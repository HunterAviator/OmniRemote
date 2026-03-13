#!/usr/bin/env python3
"""
OmniRemote™ Standalone Web Server

© 2026 One Eye Enterprises LLC - All Rights Reserved
OmniRemote™ is a trademark of One Eye Enterprises LLC
Brand Colors: Purple #7C3AED | Blue #2563EB | Green #10B981

Features:
- Shares UI with Home Assistant integration
- Full device/room/scene management
- MQTT integration with HA sync
- IR blaster support
- Bluetooth and USB HID remote support
"""

import argparse
import json
import logging
import os
import time
import uuid
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import List, Optional, Dict, Any

import yaml
from flask import Flask, jsonify, request, send_file, Response
from flask_cors import CORS
import paho.mqtt.client as mqtt

#-------------------------------------------------------------------------------
# Configuration
#-------------------------------------------------------------------------------

VERSION = "1.5.24"
PANEL_VERSION = "1.10.50"
BRAND = {
    "name": "OmniRemote",
    "tagline": "One Remote to Rule Them All",
    "copyright": "© 2026 One Eye Enterprises LLC",
    "colors": {
        "purple": "#7C3AED",
        "blue": "#2563EB",
        "green": "#10B981",
    }
}

#-------------------------------------------------------------------------------
# Logging
#-------------------------------------------------------------------------------

def setup_logging(config: dict) -> logging.Logger:
    log_config = config.get("logging", {})
    log_file = log_config.get("file", "/var/log/omniremote/web.log")
    log_level = getattr(logging, log_config.get("level", "INFO"))
    max_size = log_config.get("max_size_mb", 10) * 1024 * 1024
    
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    
    logger = logging.getLogger("OmniRemoteWeb")
    logger.setLevel(log_level)
    logger.handlers.clear()
    
    fh = RotatingFileHandler(log_file, maxBytes=max_size, backupCount=3)
    fh.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
    
    ch = logging.StreamHandler()
    ch.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
    
    logger.addHandler(fh)
    logger.addHandler(ch)
    
    return logger

#-------------------------------------------------------------------------------
# Database - JSON file storage
#-------------------------------------------------------------------------------

class Database:
    def __init__(self, path: str, log: logging.Logger):
        self.path = Path(path)
        self.log = log
        self.data = {
            "rooms": [],
            "devices": [],
            "scenes": [],
            "blasters": [],
            "remote_profiles": [],
            "physical_remotes": [],
            "remote_bridges": [],
            "sync": None
        }
        self.load()
    
    def load(self):
        if self.path.exists():
            try:
                self.data = json.loads(self.path.read_text())
                self.log.info(f"Loaded database: {len(self.data.get('devices', []))} devices, {len(self.data.get('rooms', []))} rooms")
            except Exception as e:
                self.log.error(f"Database load failed: {e}")
    
    def save(self):
        try:
            self.data["sync"] = datetime.now().isoformat()
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.write_text(json.dumps(self.data, indent=2))
        except Exception as e:
            self.log.error(f"Database save failed: {e}")
    
    def _generate_id(self, prefix: str = "item") -> str:
        return f"{prefix}_{uuid.uuid4().hex[:8]}"
    
    # Rooms
    def get_rooms(self) -> List[dict]:
        rooms = self.data.get("rooms", [])
        # Handle both dict (from HA sync) and list (local) format
        if isinstance(rooms, dict):
            return list(rooms.values())
        return rooms
    
    def get_room(self, room_id: str) -> Optional[dict]:
        rooms = self.data.get("rooms", [])
        # Handle dict format
        if isinstance(rooms, dict):
            return rooms.get(room_id)
        return next((r for r in rooms if r.get("id") == room_id), None)
    
    def add_room(self, room: dict) -> dict:
        if "id" not in room:
            room["id"] = self._generate_id("room")
        room["created"] = datetime.now().isoformat()
        
        # Handle both dict and list storage formats
        rooms = self.data.get("rooms", [])
        if isinstance(rooms, dict):
            rooms[room["id"]] = room
        else:
            self.data.setdefault("rooms", []).append(room)
        self.save()
        self.log.info(f"Added room: {room.get('name')}")
        return room
    
    def update_room(self, room_id: str, updates: dict) -> Optional[dict]:
        room = self.get_room(room_id)
        if room:
            room.update(updates)
            room["updated"] = datetime.now().isoformat()
            # If stored as dict, update in place
            rooms = self.data.get("rooms", [])
            if isinstance(rooms, dict):
                rooms[room_id] = room
            self.save()
            return room
        return None
    
    def delete_room(self, room_id: str) -> bool:
        rooms = self.data.get("rooms", [])
        if isinstance(rooms, dict):
            if room_id in rooms:
                del rooms[room_id]
                self.save()
                return True
        else:
            for i, r in enumerate(rooms):
                if r.get("id") == room_id:
                    del rooms[i]
                    self.save()
                    return True
        return False
    
    # Devices
    def get_devices(self) -> List[dict]:
        devices = self.data.get("devices", [])
        # Handle both dict (from HA sync) and list (local) format
        if isinstance(devices, dict):
            return list(devices.values())
        return devices
    
    def get_device(self, device_id: str) -> Optional[dict]:
        devices = self.data.get("devices", [])
        # Handle dict format
        if isinstance(devices, dict):
            return devices.get(device_id)
        return next((d for d in devices if d.get("id") == device_id), None)
    
    def add_device(self, device: dict) -> dict:
        if "id" not in device:
            device["id"] = self._generate_id("dev")
        device["created"] = datetime.now().isoformat()
        
        # Handle both dict and list storage formats
        devices = self.data.get("devices", [])
        if isinstance(devices, dict):
            devices[device["id"]] = device
        else:
            self.data.setdefault("devices", []).append(device)
        self.save()
        self.log.info(f"Added device: {device.get('name')}")
        return device
    
    def update_device(self, device_id: str, updates: dict) -> Optional[dict]:
        device = self.get_device(device_id)
        if device:
            device.update(updates)
            device["updated"] = datetime.now().isoformat()
            self.save()
            return device
        return None
    
    def delete_device(self, device_id: str) -> bool:
        devices = self.data.get("devices", [])
        for i, d in enumerate(devices):
            if d.get("id") == device_id:
                del devices[i]
                self.save()
                return True
        return False
    
    # Scenes
    def get_scenes(self) -> List[dict]:
        return self.data.get("scenes", [])
    
    def get_scene(self, scene_id: str) -> Optional[dict]:
        return next((s for s in self.get_scenes() if s.get("id") == scene_id), None)
    
    def add_scene(self, scene: dict) -> dict:
        if "id" not in scene:
            scene["id"] = self._generate_id("scene")
        scene["created"] = datetime.now().isoformat()
        self.data.setdefault("scenes", []).append(scene)
        self.save()
        self.log.info(f"Added scene: {scene.get('name')}")
        return scene
    
    def update_scene(self, scene_id: str, updates: dict) -> Optional[dict]:
        scene = self.get_scene(scene_id)
        if scene:
            scene.update(updates)
            scene["updated"] = datetime.now().isoformat()
            self.save()
            return scene
        return None
    
    def delete_scene(self, scene_id: str) -> bool:
        scenes = self.data.get("scenes", [])
        for i, s in enumerate(scenes):
            if s.get("id") == scene_id:
                del scenes[i]
                self.save()
                return True
        return False
    
    # Blasters
    def get_blasters(self) -> List[dict]:
        return self.data.get("blasters", [])
    
    def add_blaster(self, blaster: dict) -> dict:
        if "id" not in blaster:
            blaster["id"] = self._generate_id("blaster")
        blaster["created"] = datetime.now().isoformat()
        self.data.setdefault("blasters", []).append(blaster)
        self.save()
        return blaster
    
    def delete_blaster(self, blaster_id: str) -> bool:
        blasters = self.data.get("blasters", [])
        for i, b in enumerate(blasters):
            if b.get("id") == blaster_id:
                del blasters[i]
                self.save()
                return True
        return False
    
    # Remote Profiles
    def get_remote_profiles(self) -> List[dict]:
        return self.data.get("remote_profiles", [])
    
    def get_remote_profile(self, profile_id: str) -> Optional[dict]:
        return next((p for p in self.get_remote_profiles() if p.get("id") == profile_id), None)
    
    def add_remote_profile(self, profile: dict) -> dict:
        if "id" not in profile:
            profile["id"] = self._generate_id("profile")
        profile["created"] = datetime.now().isoformat()
        self.data.setdefault("remote_profiles", []).append(profile)
        self.save()
        return profile
    
    def update_remote_profile(self, profile_id: str, updates: dict) -> Optional[dict]:
        profile = self.get_remote_profile(profile_id)
        if profile:
            profile.update(updates)
            profile["updated"] = datetime.now().isoformat()
            self.save()
            return profile
        return None
    
    def delete_remote_profile(self, profile_id: str) -> bool:
        profiles = self.data.get("remote_profiles", [])
        for i, p in enumerate(profiles):
            if p.get("id") == profile_id:
                del profiles[i]
                self.save()
                return True
        return False
    
    # Physical Remotes
    def get_physical_remotes(self) -> List[dict]:
        remotes = self.data.get("physical_remotes", [])
        # Handle both dict (from HA sync) and list (legacy) format
        if isinstance(remotes, dict):
            return list(remotes.values())
        return remotes
    
    # Remote Bridges
    def get_remote_bridges(self) -> List[dict]:
        bridges = self.data.get("remote_bridges", [])
        # Handle both dict and list format
        if isinstance(bridges, dict):
            return list(bridges.values())
        return bridges

#-------------------------------------------------------------------------------
# MQTT Client
#-------------------------------------------------------------------------------

class MQTTClient:
    def __init__(self, config: dict, db: Database, log: logging.Logger):
        self.cfg = config.get("mqtt", {})
        self.db = db
        self.log = log
        self.client: Optional[mqtt.Client] = None
        self.connected = False
        self.prefix = self.cfg.get("topic_prefix", "omniremote")
        self.pi_hubs: Dict[str, dict] = {}
        self._reconnect_delay = 5
    
    def connect(self):
        broker = self.cfg.get("broker", "").strip()
        port = int(self.cfg.get("port", 1883))
        
        if not broker:
            self.log.warning("MQTT broker not configured - configure in Settings")
            self.log.info(f"Current MQTT config: {self.cfg}")
            return
        
        try:
            # Try paho-mqtt 2.x style first
            try:
                from paho.mqtt.enums import CallbackAPIVersion
                self.client = mqtt.Client(
                    callback_api_version=CallbackAPIVersion.VERSION1,
                    client_id="omniremote-standalone"
                )
            except (ImportError, AttributeError):
                # Fall back to paho-mqtt 1.x
                self.client = mqtt.Client(client_id="omniremote-standalone")
            
            if self.cfg.get("username"):
                self.client.username_pw_set(self.cfg["username"], self.cfg.get("password", ""))
            
            self.client.on_connect = self._on_connect
            self.client.on_disconnect = self._on_disconnect
            self.client.on_message = self._on_message
            
            # Enable automatic reconnection
            self.client.reconnect_delay_set(min_delay=1, max_delay=60)
            
            self.client.connect(broker, port, keepalive=60)
            self.client.loop_start()
            self.log.info(f"Connecting to MQTT at {broker}:{port}")
        except Exception as e:
            self.log.error(f"MQTT connection error: {e}")
            self.log.info(f"Will retry connection in {self._reconnect_delay}s")
    
    def _on_disconnect(self, client, userdata, rc):
        self.connected = False
        if rc != 0:
            self.log.warning(f"MQTT disconnected unexpectedly (rc={rc}), will auto-reconnect")
        else:
            self.log.info("MQTT disconnected cleanly")
    
    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self.connected = True
            self.log.info("MQTT connected")
            # Subscribe to hub announcements
            client.subscribe(f"{self.prefix}/hub/+/config")
            client.subscribe(f"{self.prefix}/hub/+/status")
            client.subscribe(f"{self.prefix}/hub/+/devices")
            client.subscribe(f"{self.prefix}/physical_remote")
            # Subscribe to config sync from HA
            client.subscribe(f"{self.prefix}/config/physical_remotes")
            client.subscribe(f"{self.prefix}/config/rooms")
            client.subscribe(f"{self.prefix}/config/devices")
            # Subscribe to full database sync from HA
            client.subscribe(f"{self.prefix}/sync/database")
            
            # Request full sync from HA
            self.log.info("📤 Requesting database sync from Home Assistant")
            client.publish(f"{self.prefix}/sync/request", json.dumps({
                "hub_id": self.cfg.get("hub_id", get_hub_id()),
                "timestamp": datetime.now().isoformat()
            }))
    
    def _on_message(self, client, userdata, msg):
        try:
            topic_parts = msg.topic.split('/')
            
            # Handle full database sync from HA
            if msg.topic == f"{self.prefix}/sync/database":
                payload = json.loads(msg.payload.decode())
                self._handle_full_database_sync(payload)
                return
            
            # Handle config sync from HA
            if len(topic_parts) >= 3 and topic_parts[1] == 'config':
                config_type = topic_parts[2]
                payload = json.loads(msg.payload.decode())
                self._handle_config_sync(config_type, payload)
                return
            
            if len(topic_parts) >= 4 and topic_parts[1] == 'hub':
                hub_id = topic_parts[2]
                msg_type = topic_parts[3]
                payload = json.loads(msg.payload.decode())
                
                # Skip our own messages (we publish to this topic too)
                local_hub_id = config.get("hub_id", get_hub_id())
                if hub_id == local_hub_id or hub_id.lower() == local_hub_id.lower():
                    self.log.debug(f"Ignoring own hub message: {hub_id}")
                    return
                
                if msg_type == 'config':
                    self.pi_hubs[hub_id] = {
                        "id": hub_id,
                        "config": payload,
                        "last_seen": datetime.now().isoformat()
                    }
                    self.log.info(f"Pi Hub discovered: {hub_id}")
                elif msg_type == 'status':
                    if hub_id in self.pi_hubs:
                        self.pi_hubs[hub_id]["status"] = payload
                elif msg_type == 'devices':
                    if hub_id in self.pi_hubs:
                        self.pi_hubs[hub_id]["devices"] = payload
        except Exception as e:
            self.log.error(f"MQTT message error: {e}")
    
    def _handle_config_sync(self, config_type: str, payload: dict):
        """Handle config sync messages from HA."""
        if config_type == 'physical_remotes':
            remotes = payload.get("remotes", {})
            if remotes:
                self.log.info(f"📥 Syncing {len(remotes)} physical remotes from HA")
                if "physical_remotes" not in self.db.data:
                    self.db.data["physical_remotes"] = {}
                # Convert to dict format if needed
                if isinstance(self.db.data["physical_remotes"], list):
                    self.db.data["physical_remotes"] = {}
                for rid, rdata in remotes.items():
                    rdata["synced_from_ha"] = True
                    self.db.data["physical_remotes"][rid] = rdata
                self.db.save()
        
        elif config_type == 'rooms':
            rooms = payload.get("rooms", {})
            if rooms:
                self.log.info(f"📥 Syncing {len(rooms)} rooms from HA")
                if "rooms" not in self.db.data:
                    self.db.data["rooms"] = {}
                if isinstance(self.db.data["rooms"], list):
                    # Convert list to dict
                    self.db.data["rooms"] = {r.get("id"): r for r in self.db.data["rooms"] if r.get("id")}
                for rid, rdata in rooms.items():
                    rdata["synced_from_ha"] = True
                    self.db.data["rooms"][rid] = rdata
                self.db.save()
        
        elif config_type == 'devices':
            devices = payload.get("devices", {})
            if devices:
                self.log.info(f"📥 Syncing {len(devices)} devices from HA")
                if "devices" not in self.db.data:
                    self.db.data["devices"] = {}
                if isinstance(self.db.data["devices"], list):
                    self.db.data["devices"] = {d.get("id"): d for d in self.db.data["devices"] if d.get("id")}
                for did, ddata in devices.items():
                    ddata["synced_from_ha"] = True
                    self.db.data["devices"][did] = ddata
                self.db.save()
    
    def _handle_full_database_sync(self, payload: dict):
        """Handle full database sync from HA - HA is the source of truth."""
        timestamp = payload.get("timestamp", "")
        source = payload.get("source", "unknown")
        
        self.log.info(f"📥 Receiving full database sync from HA (source: {source})")
        
        # Sync rooms - HA data replaces local
        if "rooms" in payload:
            rooms = payload["rooms"]
            self.log.info(f"  • Syncing {len(rooms)} rooms")
            # Convert list to dict if needed
            if isinstance(rooms, list):
                rooms = {r.get("id"): r for r in rooms if r.get("id")}
            for rid, rdata in rooms.items():
                rdata["synced_from_ha"] = True
            self.db.data["rooms"] = rooms
        
        # Sync devices - HA data replaces local
        if "devices" in payload:
            devices = payload["devices"]
            self.log.info(f"  • Syncing {len(devices)} devices")
            if isinstance(devices, list):
                devices = {d.get("id"): d for d in devices if d.get("id")}
            for did, ddata in devices.items():
                ddata["synced_from_ha"] = True
            self.db.data["devices"] = devices
        
        # Sync scenes
        if "scenes" in payload:
            scenes = payload["scenes"]
            self.log.info(f"  • Syncing {len(scenes)} scenes")
            if isinstance(scenes, list):
                scenes = {s.get("id"): s for s in scenes if s.get("id")}
            for sid, sdata in scenes.items():
                sdata["synced_from_ha"] = True
            self.db.data["scenes"] = scenes
        
        # Sync physical remotes
        if "physical_remotes" in payload:
            remotes = payload["physical_remotes"]
            self.log.info(f"  • Syncing {len(remotes)} physical remotes")
            if isinstance(remotes, list):
                remotes = {r.get("id"): r for r in remotes if r.get("id")}
            for rid, rdata in remotes.items():
                rdata["synced_from_ha"] = True
            self.db.data["physical_remotes"] = remotes
        
        # Sync remote profiles
        if "remote_profiles" in payload:
            profiles = payload["remote_profiles"]
            self.log.info(f"  • Syncing {len(profiles)} remote profiles")
            if isinstance(profiles, dict):
                profiles = list(profiles.values())
            for p in profiles:
                p["synced_from_ha"] = True
            self.db.data["remote_profiles"] = profiles
        
        # Sync remote bridges
        if "remote_bridges" in payload:
            bridges = payload["remote_bridges"]
            self.log.info(f"  • Syncing {len(bridges)} remote bridges")
            if isinstance(bridges, list):
                bridges = {b.get("id"): b for b in bridges if b.get("id")}
            for bid, bdata in bridges.items():
                bdata["synced_from_ha"] = True
            self.db.data["remote_bridges"] = bridges
        
        # Track sync metadata
        self.db.data["_sync_meta"] = {
            "last_sync": datetime.now().isoformat(),
            "source": source,
            "ha_timestamp": timestamp,
            "synced_from_ha": True
        }
        
        self.db.save()
        self.log.info(f"✅ Database sync complete - HA is now the source of truth")
    
    def publish_discover(self):
        if self.client and self.connected:
            self.client.publish(f"{self.prefix}/hub/discover", "{}", retain=False)
            return True
        return False
    
    def send_ir(self, hub_id: str, code: str, protocol: str = "raw") -> bool:
        if not self.connected:
            return False
        
        payload = {"code": code, "protocol": protocol}
        self.client.publish(f"{self.prefix}/hub/{hub_id}/ir/send", json.dumps(payload))
        return True
    
    def send_command(self, device_id: str, command: str) -> bool:
        if not self.connected:
            return False
        
        payload = {
            "device_id": device_id,
            "command": command,
            "timestamp": datetime.now().isoformat()
        }
        self.client.publish(f"{self.prefix}/command", json.dumps(payload))
        return True

#-------------------------------------------------------------------------------
# IR Catalog - Built-in codes
#-------------------------------------------------------------------------------

def get_catalog():
    """Return basic catalog data. In a full implementation, this would load from files."""
    return [
        {
            "id": "samsung_tv",
            "brand": "Samsung",
            "category": "tv",
            "model": "Universal",
            "commands": {
                "power": {"protocol": "samsung", "code": "0xE0E040BF"},
                "volume_up": {"protocol": "samsung", "code": "0xE0E0E01F"},
                "volume_down": {"protocol": "samsung", "code": "0xE0E0D02F"},
                "mute": {"protocol": "samsung", "code": "0xE0E0F00F"},
                "source": {"protocol": "samsung", "code": "0xE0E0807F"},
            }
        },
        {
            "id": "lg_tv",
            "brand": "LG",
            "category": "tv",
            "model": "Universal",
            "commands": {
                "power": {"protocol": "nec", "code": "0x20DF10EF"},
                "volume_up": {"protocol": "nec", "code": "0x20DF40BF"},
                "volume_down": {"protocol": "nec", "code": "0x20DFC03F"},
                "mute": {"protocol": "nec", "code": "0x20DF906F"},
            }
        },
        {
            "id": "sony_tv",
            "brand": "Sony",
            "category": "tv",
            "model": "Universal",
            "commands": {
                "power": {"protocol": "sony", "code": "0xA90"},
                "volume_up": {"protocol": "sony", "code": "0x490"},
                "volume_down": {"protocol": "sony", "code": "0xC90"},
                "mute": {"protocol": "sony", "code": "0x290"},
            }
        }
    ]

#-------------------------------------------------------------------------------
# Flask App
#-------------------------------------------------------------------------------

app = Flask(__name__)
CORS(app)

db: Optional[Database] = None
mqtt_client: Optional[MQTTClient] = None
config: dict = {}
log: Optional[logging.Logger] = None
panel_js_path: Optional[Path] = None

#-------------------------------------------------------------------------------
# Standalone HTML Wrapper
#-------------------------------------------------------------------------------

STANDALONE_HTML = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="theme-color" content="#7C3AED">
    <title>OmniRemote™</title>
    <!-- Trademark favicon - Purple/Blue gradient with remote icon -->
    <link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Cdefs%3E%3ClinearGradient id='g' x1='0%25' y1='0%25' x2='100%25' y2='100%25'%3E%3Cstop offset='0%25' stop-color='%237C3AED'/%3E%3Cstop offset='100%25' stop-color='%232563EB'/%3E%3C/linearGradient%3E%3C/defs%3E%3Crect width='32' height='32' rx='6' fill='url(%23g)'/%3E%3Cpath d='M16 6c-3.3 0-6 2.7-6 6v8c0 3.3 2.7 6 6 6s6-2.7 6-6v-8c0-3.3-2.7-6-6-6zm-2 6a2 2 0 1 1 4 0 2 2 0 0 1-4 0zm2 12a2 2 0 1 1 0-4 2 2 0 0 1 0 4zm0-5a1.5 1.5 0 1 1 0-3 1.5 1.5 0 0 1 0 3z' fill='%2310B981'/%3E%3C/svg%3E">
    <link rel="apple-touch-icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 180 180'%3E%3Cdefs%3E%3ClinearGradient id='g' x1='0%25' y1='0%25' x2='100%25' y2='100%25'%3E%3Cstop offset='0%25' stop-color='%237C3AED'/%3E%3Cstop offset='100%25' stop-color='%232563EB'/%3E%3C/linearGradient%3E%3C/defs%3E%3Crect width='180' height='180' rx='40' fill='url(%23g)'/%3E%3Cpath d='M90 30c-22 0-40 18-40 40v40c0 22 18 40 40 40s40-18 40-40V70c0-22-18-40-40-40zm-12 40a12 12 0 1 1 24 0 12 12 0 0 1-24 0zm12 70a12 12 0 1 1 0-24 12 12 0 0 1 0 24zm0-35a8 8 0 1 1 0-16 8 8 0 0 1 0 16z' fill='%2310B981'/%3E%3C/svg%3E">
    <!-- Material Design Icons -->
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@mdi/font@7.4.47/css/materialdesignicons.min.css">
    <style>
        body {
            margin: 0;
            padding: 0;
            font-family: system-ui, -apple-system, sans-serif;
            background: #0f172a;
        }
        omniremote-panel {
            display: block;
            width: 100%;
            height: 100vh;
        }
        /* Loading state */
        .loading {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            height: 100vh;
            color: #fff;
        }
        .loading-logo {
            font-size: 32px;
            font-weight: 700;
            margin-bottom: 16px;
        }
        .loading-logo .omni { color: #7C3AED; }
        .loading-logo .remote { color: #2563EB; }
        .loading-spinner {
            width: 40px;
            height: 40px;
            border: 3px solid rgba(124, 58, 237, 0.3);
            border-top-color: #7C3AED;
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
    </style>
</head>
<body>
    <div class="loading" id="loading">
        <div class="loading-logo">
            <span class="omni">Omni</span><span class="remote">Remote</span>™
        </div>
        <div class="loading-spinner"></div>
        <p style="color: #9CA3AF; margin-top: 16px;">Loading...</p>
    </div>
    
    <omniremote-panel id="panel" style="display: none;"></omniremote-panel>
    
    <!-- ha-icon polyfill for standalone mode -->
    <script>
        // Polyfill ha-icon custom element (used by Home Assistant)
        // Uses MDI font - no shadow DOM to avoid event bubbling issues
        class HaIcon extends HTMLElement {
            connectedCallback() {
                this.render();
            }
            
            static get observedAttributes() {
                return ['icon'];
            }
            
            attributeChangedCallback() {
                if (this.isConnected) this.render();
            }
            
            render() {
                const icon = this.getAttribute('icon') || '';
                // Convert mdi:icon-name to mdi-icon-name
                const mdiClass = icon.replace('mdi:', 'mdi-');
                
                // Set inline styles to match HA icon behavior
                this.style.cssText = `
                    display: inline-flex;
                    align-items: center;
                    justify-content: center;
                    width: var(--mdc-icon-size, 24px);
                    height: var(--mdc-icon-size, 24px);
                    pointer-events: none;
                    vertical-align: middle;
                `;
                
                // Create or update the inner span
                if (!this._span) {
                    this._span = document.createElement('span');
                    this.appendChild(this._span);
                }
                this._span.className = `mdi ${mdiClass}`;
                // Inherit color from parent and use variable size
                this._span.style.cssText = `
                    font-size: var(--mdc-icon-size, 24px);
                    line-height: 1;
                    pointer-events: none;
                    color: inherit;
                `;
            }
        }
        
        // Register the custom element before panel.js loads
        if (!customElements.get('ha-icon')) {
            customElements.define('ha-icon', HaIcon);
            console.log('[OmniRemote] ha-icon polyfill registered');
        }
    </script>
    
    <script src="/panel.js"></script>
    <script>
        // Wait for panel.js to load and register the custom element
        customElements.whenDefined('omniremote-panel').then(() => {
            const panel = document.getElementById('panel');
            const loading = document.getElementById('loading');
            
            // Initialize in standalone mode
            panel.initStandalone();
            
            // Show panel, hide loading
            loading.style.display = 'none';
            panel.style.display = 'block';
            
            console.log('[OmniRemote] Standalone mode initialized');
        }).catch(err => {
            console.error('[OmniRemote] Failed to initialize:', err);
            document.getElementById('loading').innerHTML = `
                <div class="loading-logo">
                    <span class="omni">Omni</span><span class="remote">Remote</span>™
                </div>
                <p style="color: #EF4444;">Failed to load panel</p>
                <p style="color: #9CA3AF; font-size: 14px;">${err.message}</p>
            `;
        });
    </script>
</body>
</html>
'''

#-------------------------------------------------------------------------------
# Routes - Static Files
#-------------------------------------------------------------------------------

@app.route("/")
def index():
    log.info(f"Web access from {request.remote_addr}")
    return STANDALONE_HTML

@app.route("/api/panel-status")
def panel_status():
    """Check if panel.js is found."""
    if panel_js_path and panel_js_path.exists():
        return jsonify({"found": True, "path": str(panel_js_path)})
    
    # Check fallback paths
    paths = [
        Path("/opt/omniremote/panel.js"),
        Path("/etc/omniremote/panel.js"),
        Path(__file__).parent / "panel.js",
    ]
    for p in paths:
        if p.exists():
            return jsonify({"found": True, "path": str(p), "fallback": True})
    
    return jsonify({"found": False, "searched": [str(p) for p in paths]})

@app.route("/panel.js")
def serve_panel():
    """Serve the panel.js file - same as HA integration."""
    if panel_js_path and panel_js_path.exists():
        log.info(f"Serving panel.js from {panel_js_path}")
        return send_file(panel_js_path, mimetype='application/javascript')
    else:
        # Fallback: try common locations (in order of preference)
        paths = [
            Path("/opt/omniremote/panel.js"),  # Default install location
            Path("/etc/omniremote/panel.js"),
            Path(__file__).parent / "panel.js",  # Same directory as web_server.py
        ]
        for p in paths:
            if p.exists():
                log.info(f"Serving panel.js from fallback: {p}")
                return send_file(p, mimetype='application/javascript')
        
        log.error("panel.js not found in any location!")
        return "// panel.js not found - copy panel.js to /etc/omniremote/panel.js", 404

@app.route("/test")
def test_page():
    """Simple test page to verify click handling works."""
    return '''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>OmniRemote Click Test</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@mdi/font@7.4.47/css/materialdesignicons.min.css">
    <style>
        body { background: #0f172a; color: #fff; font-family: system-ui; padding: 20px; }
        .test-btn { 
            display: flex; align-items: center; gap: 10px; 
            padding: 15px 20px; margin: 10px 0; 
            background: #1a1a2e; border: 1px solid #7C3AED; border-radius: 8px;
            cursor: pointer; color: #fff; font-size: 16px;
        }
        .test-btn:hover { background: #252545; }
        .test-btn ha-icon { pointer-events: none; }
        #log { background: #111; padding: 15px; border-radius: 8px; margin-top: 20px; font-family: monospace; font-size: 12px; max-height: 300px; overflow-y: auto; }
        .log-entry { margin: 5px 0; padding: 5px; background: #1a1a2e; border-radius: 4px; }
        h1 { color: #7C3AED; }
    </style>
</head>
<body>
    <h1>OmniRemote Click Test v''' + VERSION + '''</h1>
    <p>Click the buttons below. If clicks work, you'll see log entries appear.</p>
    
    <div class="test-btn" data-nav="devices">
        <ha-icon icon="mdi:devices"></ha-icon>
        <span>Devices (data-nav)</span>
    </div>
    
    <div class="test-btn" data-nav="settings">
        <ha-icon icon="mdi:cog"></ha-icon>
        <span>Settings (data-nav)</span>
    </div>
    
    <div class="test-btn" data-action="test-action">
        <ha-icon icon="mdi:play"></ha-icon>
        <span>Test Action (data-action)</span>
    </div>
    
    <button class="test-btn" onclick="logClick('onclick button')">
        <ha-icon icon="mdi:cursor-default-click"></ha-icon>
        <span>Direct onclick</span>
    </button>
    
    <div id="log">
        <div class="log-entry">Waiting for clicks...</div>
    </div>
    
    <script>
        // ha-icon polyfill
        class HaIcon extends HTMLElement {
            connectedCallback() { this.render(); }
            static get observedAttributes() { return ['icon']; }
            attributeChangedCallback() { if (this.isConnected) this.render(); }
            render() {
                const icon = this.getAttribute('icon') || '';
                const mdiClass = icon.replace('mdi:', 'mdi-');
                this.style.cssText = 'display:inline-flex;align-items:center;justify-content:center;width:24px;height:24px;pointer-events:none;';
                if (!this._span) {
                    this._span = document.createElement('span');
                    this._span.style.cssText = 'font-size:24px;line-height:1;pointer-events:none;';
                    this.appendChild(this._span);
                }
                this._span.className = 'mdi ' + mdiClass;
            }
        }
        if (!customElements.get('ha-icon')) customElements.define('ha-icon', HaIcon);
        
        function logClick(msg) {
            const log = document.getElementById('log');
            const entry = document.createElement('div');
            entry.className = 'log-entry';
            entry.textContent = new Date().toLocaleTimeString() + ' - ' + msg;
            log.insertBefore(entry, log.firstChild);
        }
        
        // Event delegation test
        document.addEventListener('click', (e) => {
            const nav = e.target.closest('[data-nav]');
            if (nav) {
                logClick('NAV CLICK: ' + nav.dataset.nav + ' (target: ' + e.target.tagName + ')');
                return;
            }
            const action = e.target.closest('[data-action]');
            if (action) {
                logClick('ACTION CLICK: ' + action.dataset.action + ' (target: ' + e.target.tagName + ')');
                return;
            }
            logClick('Other click: ' + e.target.tagName + ' ' + e.target.className);
        });
        
        logClick('Test page loaded - ha-icon registered: ' + !!customElements.get('ha-icon'));
    </script>
</body>
</html>'''

#-------------------------------------------------------------------------------
# Routes - API Endpoints (matching HA integration)
#-------------------------------------------------------------------------------

@app.route("/api/omniremote/version")
def api_version():
    return jsonify({"version": PANEL_VERSION, "server_version": VERSION})

@app.route("/api/omniremote/rooms", methods=["GET", "POST", "PUT", "DELETE"])
def api_rooms():
    if request.method == "GET":
        return jsonify(db.get_rooms())
    
    data = request.json or {}
    action = data.get("action")
    
    if request.method == "DELETE" or action == "delete":
        room_id = data.get("id")
        success = db.delete_room(room_id)
        return jsonify({"success": success})
    
    if action == "update":
        room_id = data.get("id")
        room = db.update_room(room_id, data)
        return jsonify(room) if room else (jsonify({"error": "Room not found"}), 404)
    
    # Create new room
    room = db.add_room({
        "name": data.get("name", "New Room"),
        "icon": data.get("icon", "mdi:sofa"),
        "device_ids": data.get("device_ids", []),
        "entity_ids": data.get("entity_ids", []),
    })
    return jsonify(room), 201

@app.route("/api/omniremote/devices", methods=["GET", "POST", "PUT", "DELETE"])
def api_devices():
    if request.method == "GET":
        return jsonify(db.get_devices())
    
    data = request.json or {}
    action = data.get("action")
    
    if request.method == "DELETE" or action == "delete":
        device_id = data.get("id")
        success = db.delete_device(device_id)
        return jsonify({"success": success})
    
    if action == "update" or request.method == "PUT":
        device_id = data.get("id")
        device = db.update_device(device_id, data)
        return jsonify(device) if device else (jsonify({"error": "Device not found"}), 404)
    
    # Create new device
    device = db.add_device({
        "name": data.get("name", "New Device"),
        "category": data.get("category", "tv"),
        "brand": data.get("brand", ""),
        "room_id": data.get("room_id"),
        "commands": data.get("commands", {}),
    })
    return jsonify(device), 201

@app.route("/api/omniremote/scenes", methods=["GET", "POST", "PUT", "DELETE"])
def api_scenes():
    if request.method == "GET":
        return jsonify(db.get_scenes())
    
    data = request.json or {}
    action = data.get("action")
    
    if request.method == "DELETE" or action == "delete":
        scene_id = data.get("id") or data.get("scene_id")
        success = db.delete_scene(scene_id)
        return jsonify({"success": success})
    
    if action == "activate":
        scene_id = data.get("scene_id")
        scene = db.get_scene(scene_id)
        if scene:
            # Execute scene actions via MQTT
            for act in scene.get("actions", []):
                if mqtt_client:
                    mqtt_client.send_command(act.get("device_id"), act.get("command"))
            return jsonify({"success": True, "activated": scene_id})
        return jsonify({"error": "Scene not found"}), 404
    
    if action == "update" or request.method == "PUT":
        scene_id = data.get("id")
        scene = db.update_scene(scene_id, data)
        return jsonify(scene) if scene else (jsonify({"error": "Scene not found"}), 404)
    
    # Create new scene
    scene = db.add_scene({
        "name": data.get("name", "New Scene"),
        "icon": data.get("icon", "mdi:play"),
        "actions": data.get("actions", []),
    })
    return jsonify(scene), 201

@app.route("/api/omniremote/blasters", methods=["GET", "POST", "DELETE"])
def api_blasters():
    if request.method == "GET":
        # Return blasters + any Pi Hub bridges with IR capability
        blasters = db.get_blasters()
        pi_hub_bridges = []
        
        if mqtt_client:
            for hub_id, hub_data in mqtt_client.pi_hubs.items():
                cfg = hub_data.get("config", {})
                if cfg.get("ir_blaster", {}).get("enabled"):
                    pi_hub_bridges.append({
                        "id": f"pihub_{hub_id}",
                        "name": cfg.get("name", f"Pi Hub {hub_id[:8]}"),
                        "type": "pi_hub",
                        "hub_id": hub_id,
                        "capabilities": ["ir"],
                    })
        
        return jsonify({
            "blasters": blasters,
            "ha_blasters": [],  # HA blasters not available in standalone
            "pi_hub_bridges": pi_hub_bridges,
        })
    
    data = request.json or {}
    action = data.get("action")
    
    if action == "delete" or request.method == "DELETE":
        blaster_id = data.get("id")
        success = db.delete_blaster(blaster_id)
        return jsonify({"success": success})
    
    if action == "add":
        blaster = db.add_blaster({
            "name": data.get("name", "IR Blaster"),
            "host": data.get("host"),
            "type": data.get("type", "broadlink"),
        })
        return jsonify(blaster), 201
    
    if action == "mdns":
        # Placeholder for mDNS discovery
        return jsonify({"devices": []})
    
    if action == "send":
        # Send IR command
        blaster_id = data.get("blaster_id")
        code = data.get("code")
        protocol = data.get("protocol", "raw")
        
        if blaster_id and blaster_id.startswith("pihub_"):
            hub_id = blaster_id[6:]
            if mqtt_client:
                success = mqtt_client.send_ir(hub_id, code, protocol)
                return jsonify({"success": success})
        
        return jsonify({"success": False, "error": "Blaster not found"})
    
    return jsonify(db.get_blasters())

@app.route("/api/omniremote/catalog", methods=["GET", "POST"])
def api_catalog():
    if request.method == "GET":
        catalog = get_catalog()
        # Add name field for display
        for entry in catalog:
            if "name" not in entry:
                entry["name"] = f"{entry.get('brand', '')} {entry.get('model', '')}".strip()
        return jsonify({"devices": catalog})
    
    data = request.json or {}
    catalog_id = data.get("catalog_id")
    device_name = data.get("name", "")
    room_id = data.get("room_id")
    
    # Find catalog entry
    catalog_entry = None
    for entry in get_catalog():
        if entry["id"] == catalog_id:
            catalog_entry = entry
            break
    
    if not catalog_entry:
        return jsonify({"error": "Catalog entry not found"}), 404
    
    # Create device and add to database
    device = db.add_device({
        "name": device_name or catalog_entry.get("name", f"{catalog_entry.get('brand', '')} {catalog_entry.get('model', '')}".strip()),
        "category": catalog_entry.get("category", "other"),
        "brand": catalog_entry.get("brand", ""),
        "model": catalog_entry.get("model", ""),
        "room_id": room_id,
        "catalog_id": catalog_id,
        "commands": {},
    })
    
    # Copy commands from catalog
    converted_count = 0
    failed_count = 0
    
    # Check for 'commands' (standalone format) or 'ir_codes' (HA format)
    commands_source = catalog_entry.get("commands") or catalog_entry.get("ir_codes", {})
    
    for cmd_name, cmd_data in commands_source.items():
        try:
            if isinstance(cmd_data, dict):
                device["commands"][cmd_name] = {
                    "source": "catalog",
                    "protocol": cmd_data.get("protocol"),
                    "address": cmd_data.get("address"),
                    "command": cmd_data.get("command"),
                    "code": cmd_data.get("code"),
                    "raw": cmd_data.get("raw"),
                }
            else:
                # Simple string code
                device["commands"][cmd_name] = {
                    "source": "catalog",
                    "code": str(cmd_data),
                }
            converted_count += 1
        except Exception as e:
            log.warning(f"Failed to convert command {cmd_name}: {e}")
            failed_count += 1
    
    # Update and save
    db.update_device(device["id"], device)
    
    return jsonify({
        "device": device,
        "commands_added": converted_count,
        "commands_failed": failed_count,
        "catalog_id": catalog_id,
    })

@app.route("/api/omniremote/physical_remotes", methods=["GET", "POST"])
def api_physical_remotes():
    if request.method == "GET":
        return jsonify(db.get_physical_remotes())
    
    # POST - handle discovery actions
    data = request.json or {}
    action = data.get("action")
    
    if action == "discover_remotes":
        # Query USB devices from local evdev
        usb_devices = []
        try:
            import evdev
            for path in evdev.list_devices():
                try:
                    dev = evdev.InputDevice(path)
                    # Filter for likely remotes/keyboards
                    if any(kw in dev.name.lower() for kw in ['remote', 'keyboard', 'mouse', 'g20', 'g30', 'air']):
                        usb_devices.append({
                            "name": dev.name,
                            "path": path,
                            "phys": getattr(dev, 'phys', ''),
                            "type": "usb_keyboard",
                            "protocol": "usb",
                            "suggested_model_id": None,
                            "match_confidence": "low",
                        })
                except:
                    pass
        except ImportError:
            log.warning("evdev not available for USB discovery")
        
        # Discover Bluetooth devices (trigger a real scan)
        bluetooth_devices = []
        try:
            scan_result = bluetooth_scan_sync()
            bluetooth_devices = scan_result.get("devices", [])
        except Exception as e:
            log.warning(f"Bluetooth scan failed: {e}")
            # Fall back to cached devices
            bluetooth_devices = discover_bluetooth_devices_cached()
        
        # Query Pi Hubs via MQTT for their devices
        pi_hub_devices = []
        if mqtt_client and mqtt_client.connected:
            for hub_id, hub_data in mqtt_client.pi_hubs.items():
                devices = hub_data.get("devices", {}).get("devices", [])
                for dev in devices:
                    pi_hub_devices.append({
                        "name": dev.get("name", "Unknown"),
                        "path": dev.get("path", ""),
                        "phys": dev.get("phys", ""),
                        "type": "usb_keyboard",
                        "protocol": "usb",
                        "hub_id": hub_id,
                        "hub_name": hub_data.get("config", {}).get("name", f"Hub {hub_id[:8]}"),
                        "suggested_model_id": None,
                        "match_confidence": "low",
                    })
        
        return jsonify({
            "total": len(usb_devices) + len(pi_hub_devices) + len(bluetooth_devices),
            "usb": usb_devices,
            "pi_hub": pi_hub_devices,
            "zigbee": [],  # Not available in standalone
            "bluetooth": bluetooth_devices,
        })
    
    elif action == "add":
        # Add a new physical remote
        import uuid
        remote_id = data.get("id") or str(uuid.uuid4())[:8]
        new_remote = {
            "id": remote_id,
            "name": data.get("name", "New Remote"),
            "type": data.get("type", "usb_keyboard"),
            "protocol": data.get("protocol", "usb"),
            "mac": data.get("mac", ""),
            "path": data.get("path", ""),
            "room_id": data.get("room_id", ""),
            "model_id": data.get("model_id", ""),
            "hub_id": data.get("hub_id", ""),
            "button_mappings": data.get("button_mappings", {}),
            "enabled": True,
        }
        
        # Get existing remotes or initialize
        if "physical_remotes" not in db.data:
            db.data["physical_remotes"] = []
        
        # Check if it's a list (old format) or dict (new format)
        if isinstance(db.data["physical_remotes"], dict):
            db.data["physical_remotes"][remote_id] = new_remote
        else:
            # Remove any existing remote with same ID
            db.data["physical_remotes"] = [r for r in db.data["physical_remotes"] if r.get("id") != remote_id]
            db.data["physical_remotes"].append(new_remote)
        
        db.save()
        log.info(f"Added physical remote: {new_remote['name']} ({remote_id})")
        
        # Publish to MQTT if connected
        if mqtt_client and mqtt_client.connected:
            mqtt_client.publish(f"{mqtt_client.prefix}/config/physical_remotes", json.dumps({remote_id: new_remote}), retain=True)
        
        return jsonify({"success": True, "remote": new_remote})
    
    elif action == "update":
        remote_id = data.get("id")
        if not remote_id:
            return jsonify({"success": False, "error": "Missing remote ID"}), 400
        
        remotes = db.data.get("physical_remotes", [])
        
        if isinstance(remotes, dict):
            if remote_id in remotes:
                remotes[remote_id].update({k: v for k, v in data.items() if k != "action"})
                db.save()
                return jsonify({"success": True, "remote": remotes[remote_id]})
        else:
            for i, r in enumerate(remotes):
                if r.get("id") == remote_id:
                    for k, v in data.items():
                        if k != "action":
                            remotes[i][k] = v
                    db.save()
                    return jsonify({"success": True, "remote": remotes[i]})
        
        return jsonify({"success": False, "error": "Remote not found"}), 404
    
    elif action == "delete":
        remote_id = data.get("id")
        if not remote_id:
            return jsonify({"success": False, "error": "Missing remote ID"}), 400
        
        remotes = db.data.get("physical_remotes", [])
        
        if isinstance(remotes, dict):
            if remote_id in remotes:
                del remotes[remote_id]
                db.save()
                return jsonify({"success": True})
        else:
            original_len = len(remotes)
            db.data["physical_remotes"] = [r for r in remotes if r.get("id") != remote_id]
            if len(db.data["physical_remotes"]) < original_len:
                db.save()
                return jsonify({"success": True})
        
        return jsonify({"success": False, "error": "Remote not found"}), 404
    
    return jsonify({"error": f"Unknown action: {action}"}), 400

def discover_bluetooth_devices_cached():
    """Return cached Bluetooth devices from BlueZ (no new scan)."""
    devices = []
    
    try:
        import dbus
        from dbus.mainloop.glib import DBusGMainLoop
        
        # Set up dbus
        DBusGMainLoop(set_as_default=True)
        bus = dbus.SystemBus()
        
        # Get BlueZ manager
        manager = dbus.Interface(
            bus.get_object("org.bluez", "/"),
            "org.freedesktop.DBus.ObjectManager"
        )
        
        objects = manager.GetManagedObjects()
        
        for path, interfaces in objects.items():
            if "org.bluez.Device1" in interfaces:
                props = interfaces["org.bluez.Device1"]
                name = str(props.get("Name", "Unknown"))
                mac = str(props.get("Address", ""))
                paired = bool(props.get("Paired", False))
                connected = bool(props.get("Connected", False))
                rssi = int(props.get("RSSI", -999)) if "RSSI" in props else None
                
                # Filter for likely remotes
                name_lower = name.lower()
                is_remote = any(x in name_lower for x in [
                    'remote', 'keyboard', 'g20', 'g30', 'air', 'mouse', 
                    'hid', 'gamepad', 'controller', 'clicker'
                ])
                
                if is_remote or paired:
                    devices.append({
                        "mac": mac,
                        "name": name,
                        "paired": paired,
                        "connected": connected,
                        "rssi": rssi,
                        "type": "bluetooth_paired" if paired else "bluetooth",
                        "protocol": "bluetooth",
                        "has_hid": True,
                        "suggested_model_id": None,
                        "match_confidence": "low",
                    })
    except ImportError:
        log.warning("dbus not available for Bluetooth discovery")
    except Exception as e:
        log.error(f"Bluetooth discovery error: {e}")
    
    return devices

def bluetooth_scan_sync():
    """Synchronous Bluetooth scan (triggers actual discovery)."""
    import subprocess
    import time
    
    devices = []
    paired_macs = set()
    
    # Get currently paired devices first
    try:
        result = subprocess.run(
            ["bluetoothctl", "devices", "Paired"],
            capture_output=True, text=True, timeout=5
        )
        for line in result.stdout.strip().split('\n'):
            if line.startswith("Device "):
                parts = line.split(" ", 2)
                if len(parts) >= 2:
                    paired_macs.add(parts[1].upper())
    except Exception as e:
        log.warning(f"Failed to get paired devices: {e}")
    
    # Start scanning
    try:
        # Power on adapter
        subprocess.run(["bluetoothctl", "power", "on"], capture_output=True, timeout=5)
        
        # Start scan
        scan_proc = subprocess.Popen(
            ["bluetoothctl", "scan", "on"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        
        # Wait for devices to be discovered (shorter for discovery vs add remote scan)
        time.sleep(5)
        
        # Stop scan
        scan_proc.terminate()
        subprocess.run(["bluetoothctl", "scan", "off"], capture_output=True, timeout=5)
        
        # Get all devices
        result = subprocess.run(
            ["bluetoothctl", "devices"],
            capture_output=True, text=True, timeout=5
        )
        
        for line in result.stdout.strip().split('\n'):
            if line.startswith("Device "):
                parts = line.split(" ", 2)
                if len(parts) >= 3:
                    mac = parts[1].upper()
                    name = parts[2]
                    
                    # Filter for likely remotes
                    name_lower = name.lower()
                    is_remote = any(x in name_lower for x in [
                        'remote', 'keyboard', 'g20', 'g30', 'air', 'mouse',
                        'hid', 'gamepad', 'controller', 'clicker', 'rii'
                    ])
                    
                    if is_remote or mac in paired_macs:
                        devices.append({
                            "mac": mac,
                            "name": name,
                            "paired": mac in paired_macs,
                            "type": "bluetooth_paired" if mac in paired_macs else "bluetooth",
                            "protocol": "bluetooth",
                            "has_hid": True,
                            "suggested_model_id": None,
                            "match_confidence": "low",
                        })
        
        log.info(f"Bluetooth scan found {len(devices)} devices")
        return {"success": True, "devices": devices}
        
    except Exception as e:
        log.error(f"Bluetooth scan error: {e}")
        return {"success": False, "error": str(e), "devices": []}

@app.route("/api/omniremote/bluetooth", methods=["POST"])
def api_bluetooth():
    """Handle Bluetooth operations (scan, pair, unpair, list_paired, list_hid)."""
    data = request.json or {}
    action = data.get("action")
    
    if action == "scan":
        return bluetooth_scan()
    elif action == "pair":
        mac = data.get("mac")
        if not mac:
            return jsonify({"success": False, "error": "MAC address required"})
        return bluetooth_pair(mac)
    elif action == "unpair":
        mac = data.get("mac")
        if not mac:
            return jsonify({"success": False, "error": "MAC address required"})
        return bluetooth_unpair(mac)
    elif action == "list_paired":
        return bluetooth_list_paired()
    elif action == "list_hid":
        return list_hid_devices()
    elif action == "trust":
        mac = data.get("mac")
        if not mac:
            return jsonify({"success": False, "error": "MAC address required"})
        return bluetooth_trust(mac)
    else:
        return jsonify({"success": False, "error": f"Unknown action: {action}"})


def list_hid_devices():
    """List connected HID input devices (USB and Bluetooth remotes)."""
    try:
        from evdev import InputDevice, list_devices, ecodes
        
        devices = []
        for path in list_devices():
            try:
                dev = InputDevice(path)
                if ecodes.EV_KEY in dev.capabilities():
                    # Determine if it's likely a remote
                    name_lower = dev.name.lower()
                    is_remote = any(x in name_lower for x in [
                        'remote', 'keyboard', 'g20', 'g30', 'air', 'mouse',
                        'hid', 'gamepad', 'controller', 'clicker', 'rii',
                        'wechip', 'mele', 'vontar', 'h17', 'minix', 'firetv',
                        'usb', '2.4g', 'wireless'
                    ])
                    
                    # Check if it's a Bluetooth device (path contains bluetooth)
                    is_bluetooth = 'bluetooth' in path.lower() or 'bt' in name_lower
                    
                    devices.append({
                        "path": path,
                        "name": dev.name,
                        "phys": dev.phys,
                        "is_remote": is_remote,
                        "is_bluetooth": is_bluetooth,
                        "connected": True,
                    })
            except Exception as e:
                log.debug(f"Failed to read device {path}: {e}")
        
        log.info(f"Found {len(devices)} HID input devices")
        return jsonify({"success": True, "devices": devices})
        
    except ImportError:
        log.warning("evdev not available - cannot list HID devices")
        return jsonify({"success": False, "error": "evdev not available", "devices": []})
    except Exception as e:
        log.error(f"HID device list error: {e}")
        return jsonify({"success": False, "error": str(e), "devices": []})
def bluetooth_scan():
    """Scan for Bluetooth devices."""
    import subprocess
    import time
    import shutil
    
    devices = []
    paired_devices = {}  # mac -> name
    adapter_info = {}
    
    # Check if bluetoothctl is available
    if not shutil.which("bluetoothctl"):
        log.error("bluetoothctl not found - install bluetooth package")
        return jsonify({
            "success": False, 
            "error": "Bluetooth not installed. Run: sudo apt install bluetooth bluez",
            "devices": [],
            "adapter": None
        })
    
    # Check Bluetooth adapter status
    try:
        status_result = subprocess.run(
            ["bluetoothctl", "show"],
            capture_output=True, text=True, timeout=5
        )
        log.info(f"Bluetooth adapter status:\n{status_result.stdout}")
        
        if "No default controller" in status_result.stdout or "No default controller" in status_result.stderr:
            log.warning("No Bluetooth adapter found")
            return jsonify({
                "success": False, 
                "error": "No Bluetooth adapter found. Pi Zero 2 W has built-in Bluetooth - check if enabled in /boot/config.txt",
                "devices": [],
                "adapter": None
            })
        
        # Parse adapter info
        for line in status_result.stdout.split('\n'):
            if ':' in line:
                key, _, value = line.partition(':')
                adapter_info[key.strip()] = value.strip()
        
        # Check if powered
        if "Powered: no" in status_result.stdout:
            log.info("Bluetooth adapter not powered, turning on...")
            power_result = subprocess.run(["bluetoothctl", "power", "on"], capture_output=True, text=True, timeout=5)
            log.info(f"Power on result: {power_result.stdout} {power_result.stderr}")
            time.sleep(1)
            
            # Re-check status
            status_result = subprocess.run(["bluetoothctl", "show"], capture_output=True, text=True, timeout=5)
            if "Powered: no" in status_result.stdout:
                return jsonify({
                    "success": False,
                    "error": "Failed to power on Bluetooth adapter. Try: sudo systemctl restart bluetooth",
                    "devices": [],
                    "adapter": adapter_info
                })
                
    except Exception as e:
        log.error(f"Bluetooth status check failed: {e}")
        return jsonify({
            "success": False, 
            "error": f"Bluetooth check failed: {e}",
            "devices": [],
            "adapter": None
        })
    
    # Get currently paired devices first (we'll ALWAYS show these)
    try:
        result = subprocess.run(
            ["bluetoothctl", "devices", "Paired"],
            capture_output=True, text=True, timeout=5
        )
        for line in result.stdout.strip().split('\n'):
            if line.startswith("Device "):
                parts = line.split(" ", 2)
                if len(parts) >= 3:
                    mac = parts[1].upper()
                    name = parts[2]
                    paired_devices[mac] = name
        log.info(f"Found {len(paired_devices)} paired Bluetooth devices")
    except Exception as e:
        log.warning(f"Failed to get paired devices: {e}")
    
    # Add all paired devices first (they should always be visible)
    for mac, name in paired_devices.items():
        devices.append({
            "mac": mac,
            "name": name,
            "paired": True,
            "source": "pi_hub",
            "hub_id": config.get("hub_id", get_hub_id()),
        })
    
    # Start scanning for additional devices
    try:
        # Power on adapter
        subprocess.run(["bluetoothctl", "power", "on"], capture_output=True, timeout=5)
        
        # Enable agent for pairing
        subprocess.run(["bluetoothctl", "agent", "NoInputNoOutput"], capture_output=True, timeout=5)
        subprocess.run(["bluetoothctl", "default-agent"], capture_output=True, timeout=5)
        
        # Make discoverable (helps some devices)
        subprocess.run(["bluetoothctl", "discoverable", "on"], capture_output=True, timeout=5)
        
        log.info("Starting Bluetooth scan (8 seconds)...")
        
        # Start scan
        scan_proc = subprocess.Popen(
            ["bluetoothctl", "scan", "on"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        
        # Wait for devices to be discovered
        time.sleep(8)
        
        # Stop scan
        scan_proc.terminate()
        subprocess.run(["bluetoothctl", "scan", "off"], capture_output=True, timeout=5)
        
        # Get all discovered devices
        result = subprocess.run(
            ["bluetoothctl", "devices"],
            capture_output=True, text=True, timeout=5
        )
        
        log.info(f"bluetoothctl devices output:\n{result.stdout}")
        
        all_discovered = []
        for line in result.stdout.strip().split('\n'):
            if line.startswith("Device "):
                parts = line.split(" ", 2)
                if len(parts) >= 3:
                    mac = parts[1].upper()
                    name = parts[2]
                    
                    # Skip if already in list (from paired)
                    if mac in paired_devices:
                        continue
                    
                    # Check if likely a remote
                    name_lower = name.lower()
                    is_remote = any(x in name_lower for x in [
                        'remote', 'keyboard', 'g20', 'g30', 'air', 'mouse',
                        'hid', 'gamepad', 'controller', 'clicker', 'rii',
                        'wechip', 'mele', 'vontar', 'h17', 'minix', 'firetv',
                        'flipper', 'input', 'key', 'pad'
                    ])
                    
                    all_discovered.append({
                        "mac": mac,
                        "name": name,
                        "paired": False,
                        "likely_remote": is_remote,
                        "source": "pi_hub",
                        "hub_id": config.get("hub_id", get_hub_id()),
                    })
        
        # Add ALL discovered devices to the list (not just filtered)
        devices.extend(all_discovered)
        
        log.info(f"Bluetooth scan found {len(devices)} total devices ({len(paired_devices)} paired, {len(all_discovered)} discovered)")
        return jsonify({
            "success": True, 
            "devices": devices,
            "adapter": adapter_info,
            "scan_duration": 8
        })
        
    except Exception as e:
        log.error(f"Bluetooth scan error: {e}")
        # Still return paired devices even if scan failed
        return jsonify({
            "success": True, 
            "devices": devices, 
            "scan_error": str(e),
            "adapter": adapter_info
        })

def bluetooth_pair(mac: str):
    """Pair with a Bluetooth device."""
    import subprocess
    import time
    
    log.info(f"Attempting to pair with {mac}")
    
    try:
        # Power on adapter
        subprocess.run(["bluetoothctl", "power", "on"], capture_output=True, timeout=5)
        
        # Set up agent for no-input pairing (remotes typically don't need PIN)
        subprocess.run(["bluetoothctl", "agent", "NoInputNoOutput"], capture_output=True, timeout=5)
        subprocess.run(["bluetoothctl", "default-agent"], capture_output=True, timeout=5)
        
        # Make device trusted (allows auto-reconnect)
        trust_result = subprocess.run(
            ["bluetoothctl", "trust", mac],
            capture_output=True, text=True, timeout=10
        )
        log.debug(f"Trust result: {trust_result.stdout}")
        
        # Pair with the device
        pair_result = subprocess.run(
            ["bluetoothctl", "pair", mac],
            capture_output=True, text=True, timeout=30
        )
        
        log.info(f"Pair output: {pair_result.stdout}")
        
        if "Pairing successful" in pair_result.stdout or "already exists" in pair_result.stdout.lower():
            # Try to connect after pairing
            connect_result = subprocess.run(
                ["bluetoothctl", "connect", mac],
                capture_output=True, text=True, timeout=15
            )
            log.info(f"Connect output: {connect_result.stdout}")
            
            return jsonify({
                "success": True, 
                "message": f"Paired with {mac}",
                "connected": "Connection successful" in connect_result.stdout
            })
        elif "Failed" in pair_result.stdout or pair_result.returncode != 0:
            error = pair_result.stdout.strip() or pair_result.stderr.strip() or "Pairing failed"
            return jsonify({"success": False, "error": error})
        else:
            # Check if it's actually paired now
            check = subprocess.run(
                ["bluetoothctl", "info", mac],
                capture_output=True, text=True, timeout=5
            )
            if "Paired: yes" in check.stdout:
                return jsonify({"success": True, "message": f"Paired with {mac}"})
            return jsonify({"success": False, "error": "Pairing status unclear - please verify"})
            
    except subprocess.TimeoutExpired:
        return jsonify({"success": False, "error": "Pairing timed out. Make sure the remote is in pairing mode."})
    except Exception as e:
        log.error(f"Bluetooth pair error: {e}")
        return jsonify({"success": False, "error": str(e)})

def bluetooth_trust(mac: str):
    """Trust a Bluetooth device (allows auto-reconnect)."""
    import subprocess
    
    try:
        result = subprocess.run(
            ["bluetoothctl", "trust", mac],
            capture_output=True, text=True, timeout=10
        )
        
        if "trust succeeded" in result.stdout.lower() or result.returncode == 0:
            return jsonify({"success": True, "message": f"Trusted {mac}"})
        else:
            return jsonify({"success": False, "error": result.stdout or "Trust failed"})
            
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

def bluetooth_unpair(mac: str):
    """Remove/unpair a Bluetooth device."""
    import subprocess
    
    try:
        result = subprocess.run(
            ["bluetoothctl", "remove", mac],
            capture_output=True, text=True, timeout=10
        )
        
        if "Device has been removed" in result.stdout or result.returncode == 0:
            return jsonify({"success": True, "message": f"Removed {mac}"})
        else:
            return jsonify({"success": False, "error": result.stdout or "Remove failed"})
            
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

def bluetooth_list_paired():
    """List all paired Bluetooth devices."""
    import subprocess
    
    devices = []
    
    try:
        result = subprocess.run(
            ["bluetoothctl", "devices", "Paired"],
            capture_output=True, text=True, timeout=5
        )
        
        for line in result.stdout.strip().split('\n'):
            if line.startswith("Device "):
                parts = line.split(" ", 2)
                if len(parts) >= 3:
                    devices.append({
                        "mac": parts[1].upper(),
                        "name": parts[2],
                        "paired": True,
                        "hub_id": config.get("hub_id", get_hub_id()),
                    })
        
        return jsonify({"success": True, "devices": devices})
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e), "devices": []})

@app.route("/api/omniremote/remote_bridges", methods=["GET"])
def api_remote_bridges():
    return jsonify(db.get_remote_bridges())

@app.route("/api/omniremote/remote_profiles", methods=["GET", "POST", "PUT", "DELETE"])
def api_remote_profiles():
    if request.method == "GET":
        return jsonify(db.get_remote_profiles())
    
    data = request.json or {}
    action = data.get("action")
    
    if request.method == "DELETE" or action == "delete":
        profile_id = data.get("id")
        success = db.delete_remote_profile(profile_id)
        return jsonify({"success": success})
    
    if action == "update" or request.method == "PUT":
        profile_id = data.get("id")
        profile = db.update_remote_profile(profile_id, data)
        return jsonify(profile) if profile else (jsonify({"error": "Profile not found"}), 404)
    
    # Create new profile
    profile = db.add_remote_profile({
        "name": data.get("name", "New Remote"),
        "layout": data.get("layout", "standard"),
        "buttons": data.get("buttons", []),
        "device_id": data.get("device_id"),
    })
    return jsonify(profile), 201

@app.route("/api/omniremote/debug", methods=["GET"])
def api_debug():
    return jsonify({
        "version": VERSION,
        "panel_version": PANEL_VERSION,
        "mqtt_connected": mqtt_client.connected if mqtt_client else False,
        "pi_hubs": len(mqtt_client.pi_hubs) if mqtt_client else 0,
        "devices": len(db.get_devices()) if db else 0,
        "rooms": len(db.get_rooms()) if db else 0,
        "scenes": len(db.get_scenes()) if db else 0,
        "standalone": True,
    })

@app.route("/api/omniremote/system", methods=["GET", "POST"])
def api_system():
    """System control - reboot, restart services, safe mode."""
    import subprocess
    
    if request.method == "GET":
        # Return system status
        status = {
            "hostname": subprocess.run(["hostname"], capture_output=True, text=True).stdout.strip(),
            "uptime": subprocess.run(["uptime", "-p"], capture_output=True, text=True).stdout.strip(),
            "ip": get_local_ip(),
            "version": VERSION,
        }
        
        # Check SSH status
        try:
            ssh_result = subprocess.run(["systemctl", "is-active", "ssh"], capture_output=True, text=True)
            status["ssh_enabled"] = ssh_result.stdout.strip() == "active"
        except:
            status["ssh_enabled"] = None
        
        # Check services
        for svc in ["omniremote-web", "omniremote-bridge"]:
            try:
                result = subprocess.run(["systemctl", "is-active", svc], capture_output=True, text=True)
                status[svc.replace("-", "_")] = result.stdout.strip()
            except:
                status[svc.replace("-", "_")] = "unknown"
        
        # Bluetooth status
        status["bluetooth"] = get_bluetooth_status()
        
        # WiFi status
        status["wifi"] = get_wifi_status()
        
        return jsonify(status)
    
    # POST - execute action
    data = request.json or {}
    action = data.get("action")
    
    if action == "reboot":
        log.warning("System reboot requested via web UI")
        # Use threading to delay reboot so response can be sent
        import threading
        def do_reboot():
            time.sleep(2)
            subprocess.run(["sudo", "reboot"])
        threading.Thread(target=do_reboot, daemon=True).start()
        return jsonify({"success": True, "message": "Rebooting in 2 seconds..."})
    
    elif action == "safe_mode":
        log.warning("Safe mode reboot requested - disabling web server")
        # Create safe mode flag file
        try:
            Path("/etc/omniremote/.safe_mode").touch()
            log.info("Safe mode flag created")
        except Exception as e:
            log.error(f"Failed to create safe mode flag: {e}")
        
        # Disable web server in config
        config_path = Path("/etc/omniremote/config.yaml")
        try:
            cfg = yaml.safe_load(config_path.read_text()) if config_path.exists() else {}
            if "web_server" not in cfg:
                cfg["web_server"] = {}
            cfg["web_server"]["enabled"] = False
            config_path.write_text(yaml.dump(cfg, default_flow_style=False))
            log.info("Web server disabled in config")
        except Exception as e:
            log.error(f"Failed to update config: {e}")
        
        import threading
        def do_reboot():
            time.sleep(2)
            subprocess.run(["sudo", "reboot"])
        threading.Thread(target=do_reboot, daemon=True).start()
        return jsonify({"success": True, "message": "Rebooting into safe mode... Web server will be disabled. SSH should still work. To re-enable: sudo nano /etc/omniremote/config.yaml and set web_server.enabled: true"})
    
    elif action == "restart_services":
        log.info("Restarting OmniRemote services")
        results = {}
        for svc in ["omniremote-bridge", "omniremote-web"]:
            try:
                result = subprocess.run(["sudo", "systemctl", "restart", svc], capture_output=True, text=True, timeout=30)
                results[svc] = "restarted" if result.returncode == 0 else result.stderr.strip()
            except Exception as e:
                results[svc] = str(e)
        return jsonify({"success": True, "results": results})
    
    elif action == "enable_ssh":
        log.info("Enabling SSH")
        try:
            subprocess.run(["sudo", "systemctl", "enable", "ssh"], capture_output=True, timeout=10)
            subprocess.run(["sudo", "systemctl", "start", "ssh"], capture_output=True, timeout=10)
            return jsonify({"success": True, "message": "SSH enabled and started"})
        except Exception as e:
            return jsonify({"success": False, "error": str(e)})
    
    elif action == "disable_ssh":
        log.warning("Disabling SSH")
        try:
            subprocess.run(["sudo", "systemctl", "stop", "ssh"], capture_output=True, timeout=10)
            subprocess.run(["sudo", "systemctl", "disable", "ssh"], capture_output=True, timeout=10)
            return jsonify({"success": True, "message": "SSH disabled"})
        except Exception as e:
            return jsonify({"success": False, "error": str(e)})
    
    elif action == "exit_safe_mode":
        log.info("Exiting safe mode")
        # Remove safe mode flag
        try:
            Path("/etc/omniremote/.safe_mode").unlink(missing_ok=True)
        except:
            pass
        
        # Re-enable web server in config
        config_path = Path("/etc/omniremote/config.yaml")
        try:
            cfg = yaml.safe_load(config_path.read_text()) if config_path.exists() else {}
            if "web_server" not in cfg:
                cfg["web_server"] = {}
            cfg["web_server"]["enabled"] = True
            config_path.write_text(yaml.dump(cfg, default_flow_style=False))
            return jsonify({"success": True, "message": "Safe mode disabled. Web server will start on next boot."})
        except Exception as e:
            return jsonify({"success": False, "error": str(e)})
    
    elif action == "shutdown":
        log.warning("System shutdown requested via web UI")
        import threading
        def do_shutdown():
            time.sleep(2)
            subprocess.run(["sudo", "shutdown", "-h", "now"])
        threading.Thread(target=do_shutdown, daemon=True).start()
        return jsonify({"success": True, "message": "Shutting down in 2 seconds..."})
    
    else:
        return jsonify({"success": False, "error": f"Unknown action: {action}"})

@app.route("/api/omniremote/logs", methods=["GET"])
def api_logs():
    """Get system logs, optionally sanitized for support."""
    import subprocess
    import re
    
    sanitize = request.args.get("sanitize", "false").lower() == "true"
    lines = int(request.args.get("lines", 200))
    service = request.args.get("service", "all")  # all, web, bridge
    
    logs = []
    
    # Collect logs from different sources
    log_sources = []
    
    if service in ["all", "web"]:
        log_sources.append(("omniremote-web", ["journalctl", "-u", "omniremote-web", "-n", str(lines), "--no-pager"]))
    
    if service in ["all", "bridge"]:
        log_sources.append(("omniremote-bridge", ["journalctl", "-u", "omniremote-bridge", "-n", str(lines), "--no-pager"]))
    
    # Also include file logs if they exist
    log_file = Path("/var/log/omniremote/bridge.log")
    
    for source_name, cmd in log_sources:
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            if result.stdout:
                logs.append(f"=== {source_name} (journalctl) ===")
                logs.append(result.stdout)
        except Exception as e:
            logs.append(f"=== {source_name} ERROR: {e} ===")
    
    if log_file.exists():
        try:
            content = log_file.read_text()
            # Get last N lines
            log_lines = content.strip().split('\n')
            logs.append(f"=== File Log ({log_file}) ===")
            logs.append('\n'.join(log_lines[-lines:]))
        except Exception as e:
            logs.append(f"=== File Log ERROR: {e} ===")
    
    # Add system info
    logs.insert(0, f"=== OmniRemote Support Log ===")
    logs.insert(1, f"Version: {VERSION}")
    logs.insert(2, f"Generated: {datetime.now().isoformat()}")
    logs.insert(3, "")
    
    full_log = '\n'.join(logs)
    
    if sanitize:
        # Sanitize personal information
        full_log = sanitize_log(full_log)
    
    # Return as downloadable file or JSON
    if request.args.get("download", "false").lower() == "true":
        from flask import Response
        filename = f"omniremote-support-{'sanitized-' if sanitize else ''}{datetime.now().strftime('%Y%m%d-%H%M%S')}.log"
        return Response(
            full_log,
            mimetype="text/plain",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    
    return jsonify({"success": True, "log": full_log, "lines": len(full_log.split('\n'))})

def sanitize_log(log_text: str) -> str:
    """Remove personal/identifying information from logs for support."""
    import re
    
    sanitized = log_text
    
    # Replace IP addresses (keep localhost/127.x.x.x)
    sanitized = re.sub(r'\b(?!127\.)(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})\b', '[REDACTED_IP]', sanitized)
    
    # Replace MAC addresses
    sanitized = re.sub(r'([0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}', '[REDACTED_MAC]', sanitized)
    
    # Replace hostnames (common patterns)
    sanitized = re.sub(r'hostname["\s:=]+["\']?[\w\-\.]+["\']?', 'hostname: [REDACTED]', sanitized, flags=re.IGNORECASE)
    
    # Replace usernames in paths
    sanitized = re.sub(r'/home/[\w\-]+/', '/home/[USER]/', sanitized)
    sanitized = re.sub(r'/Users/[\w\-]+/', '/Users/[USER]/', sanitized)
    
    # Replace MQTT credentials
    sanitized = re.sub(r'(username|user)["\s:=]+["\']?[\w\-@\.]+["\']?', r'\1: [REDACTED]', sanitized, flags=re.IGNORECASE)
    sanitized = re.sub(r'(password|pass)["\s:=]+["\']?[^\s"\',}]+["\']?', r'\1: [REDACTED]', sanitized, flags=re.IGNORECASE)
    
    # Replace broker addresses (but keep port)
    sanitized = re.sub(r'(broker)["\s:=]+["\']?[\w\-\.]+["\']?', r'\1: [REDACTED]', sanitized, flags=re.IGNORECASE)
    
    # Replace hub names that might be personal
    sanitized = re.sub(r'(hub_name|name)["\s:=]+["\']?Pi Hub [^"\'}\n]+["\']?', r'\1: "Pi Hub [REDACTED]"', sanitized, flags=re.IGNORECASE)
    
    # Replace serial numbers / UUIDs (but keep hub_id format)
    sanitized = re.sub(r'\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b', '[REDACTED_UUID]', sanitized, flags=re.IGNORECASE)
    
    # Add sanitization notice
    sanitized = "=== SANITIZED FOR SUPPORT - Personal details removed ===\n\n" + sanitized
    
    return sanitized

@app.route("/api/omniremote/flipper", methods=["GET", "POST"])
def api_flipper():
    # Flipper Zero integration placeholder
    if request.method == "GET":
        return jsonify({"status": "not_connected", "files": []})
    return jsonify({"success": False, "error": "Flipper not available in standalone mode"})

@app.route("/api/omniremote/update", methods=["POST"])
def api_update():
    """Receive and apply an update pushed from Home Assistant."""
    import base64
    import tarfile
    import io
    import subprocess
    import threading
    
    data = request.json or {}
    package_b64 = data.get("package_b64")
    
    if not package_b64:
        return jsonify({"success": False, "error": "No package data received"})
    
    log.info("Receiving update package from Home Assistant...")
    
    try:
        # Decode the base64 tarball
        tar_data = base64.b64decode(package_b64)
        log.info(f"Update package size: {len(tar_data)} bytes")
        
        # Extract to a temp directory
        update_dir = Path("/tmp/omniremote-update")
        if update_dir.exists():
            import shutil
            shutil.rmtree(update_dir)
        update_dir.mkdir(parents=True)
        
        # Extract tarball
        tar_buffer = io.BytesIO(tar_data)
        with tarfile.open(fileobj=tar_buffer, mode='r:gz') as tar:
            tar.extractall(update_dir)
        
        log.info(f"Extracted update to {update_dir}")
        
        # Check for install.sh
        install_script = update_dir / "install.sh"
        if not install_script.exists():
            return jsonify({"success": False, "error": "No install.sh found in update package"})
        
        # Run install script in background and restart
        def do_update():
            time.sleep(1)
            try:
                log.info("Running install.sh --unattended...")
                result = subprocess.run(
                    ["sudo", "bash", str(install_script), "--unattended"],
                    cwd=str(update_dir),
                    capture_output=True,
                    text=True,
                    timeout=300  # 5 minutes for full install
                )
                log.info(f"Install output: {result.stdout[-2000:] if result.stdout else 'none'}")
                if result.returncode != 0:
                    log.error(f"Install error (rc={result.returncode}): {result.stderr[-500:] if result.stderr else 'none'}")
                else:
                    log.info("Update installed successfully, restarting services...")
                    # Restart services
                    subprocess.run(["sudo", "systemctl", "restart", "omniremote-bridge"], capture_output=True)
                    subprocess.run(["sudo", "systemctl", "restart", "omniremote-web"], capture_output=True)
            except Exception as e:
                log.error(f"Update failed: {e}")
        
        threading.Thread(target=do_update, daemon=True).start()
        
        return jsonify({
            "success": True, 
            "message": "Update received, installing in background. Services will restart."
        })
        
    except Exception as e:
        log.error(f"Update processing error: {e}")
        return jsonify({"success": False, "error": str(e)})

@app.route("/api/omniremote/remote_models", methods=["GET"])
def api_remote_models():
    """Return available remote models for auto button mapping."""
    models = [
        # WeChip / Generic Air Mouse
        {"id": "wechip_g20", "name": "G20/G20S Air Mouse", "manufacturer": "WeChip", "buttons": ["power", "mute", "home", "back", "menu", "up", "down", "left", "right", "ok", "vol_up", "vol_down", "ch_up", "ch_down"]},
        {"id": "wechip_g30", "name": "G30/G30S Air Mouse", "manufacturer": "WeChip", "buttons": ["power", "mute", "home", "back", "menu", "up", "down", "left", "right", "ok", "vol_up", "vol_down", "mic"]},
        {"id": "wechip_w1", "name": "W1 Air Mouse", "manufacturer": "WeChip", "buttons": ["power", "home", "back", "up", "down", "left", "right", "ok", "vol_up", "vol_down"]},
        # MX3 / Rii
        {"id": "mx3_air", "name": "MX3 Air Mouse", "manufacturer": "MX3", "buttons": ["power", "mute", "home", "back", "menu", "up", "down", "left", "right", "ok", "vol_up", "vol_down", "play", "pause"]},
        {"id": "rii_i8", "name": "Rii i8+ Mini Keyboard", "manufacturer": "Rii", "buttons": ["power", "home", "back", "up", "down", "left", "right", "ok", "vol_up", "vol_down", "mute"]},
        {"id": "rii_mx6", "name": "Rii MX6 Air Mouse", "manufacturer": "Rii", "buttons": ["power", "home", "back", "up", "down", "left", "right", "ok", "vol_up", "vol_down", "mic"]},
        # Fire TV
        {"id": "firetv_remote", "name": "Fire TV Remote", "manufacturer": "Amazon", "buttons": ["power", "home", "back", "menu", "up", "down", "left", "right", "ok", "rewind", "play_pause", "fast_forward", "vol_up", "vol_down", "mute"]},
        {"id": "firetv_voice", "name": "Fire TV Voice Remote", "manufacturer": "Amazon", "buttons": ["power", "home", "back", "menu", "up", "down", "left", "right", "ok", "rewind", "play_pause", "fast_forward", "vol_up", "vol_down", "mute", "alexa"]},
        # Roku
        {"id": "roku_simple", "name": "Roku Simple Remote", "manufacturer": "Roku", "buttons": ["power", "home", "back", "up", "down", "left", "right", "ok", "replay", "options"]},
        {"id": "roku_voice", "name": "Roku Voice Remote", "manufacturer": "Roku", "buttons": ["power", "home", "back", "up", "down", "left", "right", "ok", "replay", "options", "vol_up", "vol_down", "mute", "voice"]},
        # Apple TV
        {"id": "apple_siri", "name": "Apple TV Siri Remote", "manufacturer": "Apple", "buttons": ["power", "home", "back", "menu", "up", "down", "left", "right", "ok", "play_pause", "vol_up", "vol_down", "mute", "siri"]},
        # NVIDIA Shield
        {"id": "shield_remote", "name": "NVIDIA Shield Remote", "manufacturer": "NVIDIA", "buttons": ["power", "home", "back", "up", "down", "left", "right", "ok", "vol_up", "vol_down", "mic"]},
        # Generic
        {"id": "generic_ir", "name": "Generic IR Remote", "manufacturer": "Generic", "buttons": ["power", "vol_up", "vol_down", "ch_up", "ch_down", "mute", "up", "down", "left", "right", "ok", "menu", "back", "home"]},
        {"id": "generic_bt", "name": "Generic Bluetooth Remote", "manufacturer": "Generic", "buttons": ["power", "home", "back", "up", "down", "left", "right", "ok", "vol_up", "vol_down"]},
    ]
    return jsonify({"models": models})

@app.route("/api/omniremote/mqtt/status", methods=["GET"])
def api_mqtt_status():
    if not mqtt_client:
        return jsonify({
            "connected": False, 
            "broker": None,
            "sync_status": "disconnected"
        })
    
    # Get sync metadata from database
    sync_meta = db.data.get("_sync_meta", {})
    
    sync_status = "local_only"
    if mqtt_client.connected:
        if sync_meta.get("synced_from_ha"):
            sync_status = "synced"
        else:
            sync_status = "connected_awaiting_sync"
    
    return jsonify({
        "connected": mqtt_client.connected,
        "broker": mqtt_client.cfg.get("broker"),
        "port": mqtt_client.cfg.get("port", 1883),
        "username": mqtt_client.cfg.get("username", ""),
        "sync_status": sync_status,
        "last_sync": sync_meta.get("last_sync"),
        "sync_source": sync_meta.get("source"),
    })

@app.route("/api/omniremote/mqtt/config", methods=["POST"])
def api_mqtt_config():
    global mqtt_client, config
    data = request.json or {}
    config_path = Path("/etc/omniremote/config.yaml")
    
    try:
        existing = yaml.safe_load(config_path.read_text()) if config_path.exists() else {}
        
        if "mqtt" not in existing:
            existing["mqtt"] = {}
        
        existing["mqtt"]["broker"] = data.get("broker")
        existing["mqtt"]["port"] = int(data.get("port", 1883))
        existing["mqtt"]["username"] = data.get("username", "")
        if data.get("password"):
            existing["mqtt"]["password"] = data["password"]
        
        config_path.write_text(yaml.dump(existing, default_flow_style=False))
        log.info(f"MQTT config saved: {data.get('broker')}:{data.get('port')}")
        
        # Update global config to stay in sync
        config = existing
        
        # Reconnect MQTT with new settings
        if mqtt_client and mqtt_client.client:
            try:
                mqtt_client.client.loop_stop()
                mqtt_client.client.disconnect()
            except:
                pass
        
        # Create new MQTT client with new config
        mqtt_client = MQTTClient(existing, db, log)
        mqtt_client.connect()
        
        return jsonify({"success": True, "message": "MQTT config saved and reconnecting..."})
    except Exception as e:
        log.error(f"MQTT config save error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/omniremote/mqtt/test", methods=["POST"])
def api_mqtt_test():
    data = request.json or {}
    broker = data.get("broker", "localhost")
    port = int(data.get("port", 1883))
    username = data.get("username", "")
    password = data.get("password", "")
    
    log.info(f"Testing MQTT connection to {broker}:{port}")
    
    import socket
    
    # First test TCP connectivity
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((broker, port))
        sock.close()
        
        if result != 0:
            log.warning(f"MQTT test failed: Cannot reach {broker}:{port}")
            return jsonify({"success": False, "error": f"Cannot reach {broker}:{port}"})
    except socket.gaierror:
        log.warning(f"MQTT test failed: Cannot resolve {broker}")
        return jsonify({"success": False, "error": f"Cannot resolve hostname: {broker}"})
    except Exception as e:
        log.warning(f"MQTT test socket error: {e}")
        return jsonify({"success": False, "error": str(e)})
    
    # Now test MQTT protocol connection
    try:
        # Try new-style client creation first (paho-mqtt 2.x)
        try:
            from paho.mqtt.client import CallbackAPIVersion
            test_client = mqtt.Client(callback_api_version=CallbackAPIVersion.VERSION1, client_id="omniremote-test")
        except ImportError:
            # Fall back to old-style (paho-mqtt 1.x)
            test_client = mqtt.Client(client_id="omniremote-test")
        
        if username:
            test_client.username_pw_set(username, password)
        
        connected = [False]
        error_msg = [None]
        
        def on_connect(c, u, f, rc):
            if rc == 0:
                connected[0] = True
            else:
                codes = {1: "Bad protocol", 2: "Client ID rejected", 3: "Server unavailable", 
                         4: "Bad username/password", 5: "Not authorized"}
                error_msg[0] = codes.get(rc, f"Error code {rc}")
        
        test_client.on_connect = on_connect
        test_client.connect(broker, port)
        test_client.loop_start()
        
        # Wait up to 5 seconds for connection
        for _ in range(50):
            if connected[0] or error_msg[0]:
                break
            time.sleep(0.1)
        
        test_client.loop_stop()
        test_client.disconnect()
        
        if connected[0]:
            log.info(f"MQTT test successful: {broker}:{port}")
            return jsonify({"success": True, "message": "Connected successfully!"})
        elif error_msg[0]:
            log.warning(f"MQTT test failed: {error_msg[0]}")
            return jsonify({"success": False, "error": error_msg[0]})
        else:
            log.warning(f"MQTT test failed: Connection timeout")
            return jsonify({"success": False, "error": "Connection timeout"})
            
    except Exception as e:
        log.error(f"MQTT test exception: {e}")
        return jsonify({"success": False, "error": str(e)})

@app.route("/api/omniremote/mqtt/auto-configure", methods=["POST"])
def api_mqtt_auto_configure():
    # In standalone mode, just return current MQTT status
    if mqtt_client and mqtt_client.connected:
        return jsonify({
            "success": True,
            "broker": mqtt_client.cfg.get("broker"),
            "port": mqtt_client.cfg.get("port", 1883),
        })
    return jsonify({"success": False, "error": "MQTT not configured"})

@app.route("/api/omniremote/network", methods=["GET"])
def api_network():
    """Discover network-controllable devices (Roku, Chromecast, etc.)."""
    import socket
    import subprocess
    
    device_type = request.args.get("type", "all")
    devices = []
    
    # Roku discovery via SSDP
    if device_type in ("all", "roku"):
        try:
            roku_devices = discover_roku()
            devices.extend(roku_devices)
        except Exception as e:
            log.warning(f"Roku discovery error: {e}")
    
    # Chromecast discovery via mDNS
    if device_type in ("all", "chromecast"):
        try:
            cc_devices = discover_chromecast()
            devices.extend(cc_devices)
        except Exception as e:
            log.warning(f"Chromecast discovery error: {e}")
    
    return jsonify({"devices": devices})

def discover_roku():
    """Discover Roku devices via SSDP."""
    import socket
    
    devices = []
    
    ssdp_request = (
        'M-SEARCH * HTTP/1.1\r\n'
        'HOST: 239.255.255.250:1900\r\n'
        'MAN: "ssdp:discover"\r\n'
        'ST: roku:ecp\r\n'
        'MX: 3\r\n'
        '\r\n'
    ).encode()
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(4)
        sock.sendto(ssdp_request, ('239.255.255.250', 1900))
        
        seen_ips = set()
        while True:
            try:
                data, addr = sock.recvfrom(1024)
                ip = addr[0]
                if ip in seen_ips:
                    continue
                seen_ips.add(ip)
                
                # Parse response for device info
                response = data.decode('utf-8', errors='ignore')
                name = "Roku Device"
                model = ""
                device_id = ""
                
                # Try to get device info from Roku API
                try:
                    import urllib.request
                    url = f"http://{ip}:8060/query/device-info"
                    req = urllib.request.Request(url, method='GET')
                    req.add_header('User-Agent', 'OmniRemote/1.0')
                    with urllib.request.urlopen(req, timeout=2) as r:
                        info_xml = r.read().decode('utf-8')
                        # Parse basic info
                        import re
                        name_match = re.search(r'<friendly-device-name>([^<]+)</friendly-device-name>', info_xml)
                        model_match = re.search(r'<model-name>([^<]+)</model-name>', info_xml)
                        id_match = re.search(r'<serial-number>([^<]+)</serial-number>', info_xml)
                        if name_match:
                            name = name_match.group(1)
                        if model_match:
                            model = model_match.group(1)
                        if id_match:
                            device_id = id_match.group(1)
                except:
                    pass
                
                devices.append({
                    "type": "roku",
                    "name": name,
                    "ip": ip,
                    "port": 8060,
                    "model": model,
                    "id": device_id,
                })
            except socket.timeout:
                break
        
        sock.close()
    except Exception as e:
        log.warning(f"SSDP discovery error: {e}")
    
    return devices

def discover_chromecast():
    """Discover Chromecast devices via mDNS."""
    import socket
    
    devices = []
    
    # Simple UDP probe for _googlecast._tcp.local
    # For full mDNS, we'd need zeroconf library
    # This is a simplified version that looks for common Chromecast ports
    
    try:
        # Try to import zeroconf if available
        from zeroconf import ServiceBrowser, Zeroconf
        
        discovered = []
        
        class Listener:
            def add_service(self, zc, service_type, name):
                info = zc.get_service_info(service_type, name)
                if info:
                    ip = socket.inet_ntoa(info.addresses[0]) if info.addresses else None
                    if ip:
                        discovered.append({
                            "type": "chromecast",
                            "name": info.name.replace("._googlecast._tcp.local.", ""),
                            "ip": ip,
                            "port": info.port,
                            "model": info.properties.get(b'md', b'').decode('utf-8', errors='ignore'),
                            "id": info.properties.get(b'id', b'').decode('utf-8', errors='ignore'),
                        })
            def remove_service(self, zc, service_type, name):
                pass
            def update_service(self, zc, service_type, name):
                pass
        
        zc = Zeroconf()
        browser = ServiceBrowser(zc, "_googlecast._tcp.local.", Listener())
        time.sleep(3)
        zc.close()
        
        devices.extend(discovered)
    except ImportError:
        log.debug("zeroconf not available, skipping Chromecast discovery")
    except Exception as e:
        log.warning(f"Chromecast discovery error: {e}")
    
    return devices

@app.route("/api/omniremote/network/scan", methods=["POST"])
def api_network_scan():
    """Scan the network for controllable devices (TVs, receivers, etc.)."""
    import subprocess
    import socket
    import concurrent.futures
    
    data = request.get_json() or {}
    timeout = data.get("timeout", 20)
    
    devices = []
    
    log.info("Starting network scan for controllable devices...")
    
    # Get local network range
    local_ip = get_local_ip()
    network_prefix = '.'.join(local_ip.split('.')[:-1])
    
    def check_device(ip):
        """Check a single IP for controllable device signatures."""
        result = {"ip": ip}
        
        # Common ports for controllable devices
        port_checks = {
            8060: "roku",           # Roku ECP
            8008: "chromecast",     # Chromecast
            8443: "samsung_tv",     # Samsung SmartThings
            3000: "lg_tv",          # LG WebOS
            80: "http",             # Generic HTTP
            23: "telnet",           # Telnet (some older devices)
            10002: "onkyo",         # Onkyo eISCP
            50000: "denon",         # Denon/Marantz
        }
        
        open_ports = []
        detected_type = None
        
        for port, device_type in port_checks.items():
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(0.5)
                if sock.connect_ex((ip, port)) == 0:
                    open_ports.append(port)
                    if not detected_type:
                        detected_type = device_type
                sock.close()
            except:
                pass
        
        if not open_ports:
            return None
        
        result["open_ports"] = open_ports
        result["type"] = detected_type
        
        # Try to get hostname
        try:
            hostname = socket.gethostbyaddr(ip)[0]
            result["hostname"] = hostname
            result["name"] = hostname.split('.')[0]
        except:
            pass
        
        # Try to get MAC address from ARP table
        try:
            arp_result = subprocess.run(["arp", "-n", ip], capture_output=True, text=True, timeout=2)
            for line in arp_result.stdout.split('\n'):
                if ip in line:
                    parts = line.split()
                    for part in parts:
                        if ':' in part and len(part) == 17:
                            result["mac"] = part.upper()
                            break
        except:
            pass
        
        # Specific device detection
        if 8060 in open_ports:
            # Roku - try to get device info
            try:
                import urllib.request
                req = urllib.request.Request(f"http://{ip}:8060/query/device-info", headers={"User-Agent": "OmniRemote"})
                response = urllib.request.urlopen(req, timeout=2)
                content = response.read().decode()
                if "<device-info>" in content:
                    result["type"] = "roku"
                    # Parse name from XML
                    import re
                    name_match = re.search(r'<user-device-name>([^<]+)</user-device-name>', content)
                    if name_match:
                        result["name"] = name_match.group(1)
                    model_match = re.search(r'<model-name>([^<]+)</model-name>', content)
                    if model_match:
                        result["model"] = model_match.group(1)
            except:
                pass
        
        return result
    
    # Scan network in parallel
    with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
        futures = {executor.submit(check_device, f"{network_prefix}.{i}"): i for i in range(1, 255)}
        
        for future in concurrent.futures.as_completed(futures, timeout=timeout):
            try:
                result = future.result()
                if result:
                    devices.append(result)
            except:
                pass
    
    # Also run SSDP and mDNS discovery
    try:
        roku_devices = discover_roku()
        for rd in roku_devices:
            if not any(d["ip"] == rd["ip"] for d in devices):
                devices.append(rd)
    except:
        pass
    
    try:
        cc_devices = discover_chromecast()
        for cd in cc_devices:
            if not any(d["ip"] == cd["ip"] for d in devices):
                devices.append(cd)
    except:
        pass
    
    log.info(f"Network scan found {len(devices)} controllable devices")
    return jsonify({"success": True, "devices": devices})

@app.route("/api/omniremote/network/test", methods=["POST"])
def api_network_test():
    """Test network connectivity to a device."""
    import subprocess
    import socket
    
    data = request.get_json() or {}
    ip = data.get("ip")
    port = data.get("port")
    protocol = data.get("protocol")
    
    if not ip:
        return jsonify({"success": False, "error": "No IP address provided"})
    
    result = {"success": False, "ip": ip}
    
    # Ping test
    try:
        ping_result = subprocess.run(
            ["ping", "-c", "1", "-W", "2", ip],
            capture_output=True, text=True, timeout=5
        )
        if ping_result.returncode == 0:
            result["success"] = True
            # Parse ping time
            import re
            time_match = re.search(r'time[=<](\d+\.?\d*)', ping_result.stdout)
            if time_match:
                result["ping_ms"] = float(time_match.group(1))
    except Exception as e:
        result["error"] = f"Ping failed: {e}"
    
    # Try to get hostname
    try:
        hostname = socket.gethostbyaddr(ip)[0]
        result["hostname"] = hostname
    except:
        pass
    
    # Check common ports
    open_ports = []
    port_checks = [80, 443, 8060, 8008, 8443, 3000, 10002, 50000, 23]
    if port:
        port_checks.insert(0, int(port))
    
    for p in port_checks:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            if sock.connect_ex((ip, p)) == 0:
                open_ports.append(p)
            sock.close()
        except:
            pass
    
    if open_ports:
        result["open_ports"] = open_ports
        result["success"] = True
    
    # Try to detect device type
    if 8060 in open_ports:
        result["detected_type"] = "Roku"
    elif 8008 in open_ports:
        result["detected_type"] = "Chromecast/Google TV"
    elif 10002 in open_ports:
        result["detected_type"] = "Onkyo/Pioneer AVR"
    elif 50000 in open_ports:
        result["detected_type"] = "Denon/Marantz AVR"
    
    return jsonify(result)

@app.route("/api/omniremote/pi_hubs", methods=["GET"])
def api_pi_hubs():
    """Return list of Pi Hubs - always includes local hub in standalone mode."""
    import socket
    import subprocess
    
    hubs = []
    
    # Always include THIS Pi Hub (local)
    local_ip = get_local_ip()
    web_cfg = config.get("web_server", {})
    web_port = web_cfg.get("port", 8125)  # Default to 8125 (HTTPS)
    
    # Determine protocol - SSL is enabled by default
    ssl_cfg = web_cfg.get("ssl", {})
    ssl_enabled = ssl_cfg.get("enabled", True)
    protocol = "https" if ssl_enabled else "http"
    
    hub_id = config.get("hub_id", get_hub_id())
    hub_name = config.get("hub_name", config.get("name", "Pi Hub (Local)"))
    
    # Check if Bluetooth is available locally
    bt_available = False
    bt_status = "unknown"
    bt_powered = False
    try:
        result = subprocess.run(["bluetoothctl", "show"], capture_output=True, text=True, timeout=3)
        if "Controller" in result.stdout:
            bt_available = True
            bt_status = "available"
            if "Powered: yes" in result.stdout:
                bt_status = "powered"
                bt_powered = True
            elif "Powered: no" in result.stdout:
                bt_status = "off"
    except:
        pass
    
    local_hub = {
        "id": hub_id,
        "hub_id": hub_id,
        "name": hub_name,
        "ip": local_ip,
        "online": True,
        "status": "online",
        "has_bluetooth": bt_available,
        "bluetooth_status": bt_status,
        "bluetooth_powered": bt_powered,
        "has_usb": True,
        "has_ir": config.get("ir_blaster", {}).get("enabled", False),
        "web_ui": f"{protocol}://{local_ip}:{web_port}",
        "web_port": web_port,
        "version": VERSION,
        "capabilities": {
            "bluetooth": bt_available,
            "bluetooth_status": bt_status,
            "bluetooth_powered": bt_powered,
            "usb_hid": True,
            "ir_blaster": config.get("ir_blaster", {}).get("enabled", False),
        },
        "is_local": True,
    }
    hubs.append(local_hub)
    
    # Also include any other Pi Hubs discovered via MQTT
    # But skip any that match our local hub (by ID or IP)
    if mqtt_client:
        for remote_hub_id, hub_data in mqtt_client.pi_hubs.items():
            # Skip ourselves - check multiple ways to avoid duplicates
            if remote_hub_id == hub_id:
                continue
            if remote_hub_id.lower() == hub_id.lower():
                continue
            
            cfg = hub_data.get("config", {})
            remote_ip = cfg.get("ip", "")
            
            # Skip if same IP as local
            if remote_ip and remote_ip == local_ip:
                continue
            
            caps = cfg.get("capabilities", {})
            
            hubs.append({
                "id": remote_hub_id,
                "hub_id": remote_hub_id,
                "name": cfg.get("name", f"Pi Hub {remote_hub_id[:8]}"),
                "ip": remote_ip,
                "online": True,  # If we see it via MQTT, it's online
                "status": hub_data.get("status", {}).get("status", "online"),
                "has_bluetooth": caps.get("bluetooth", False),
                "bluetooth_status": caps.get("bluetooth_status", "unknown"),
                "bluetooth_powered": caps.get("bluetooth_powered", False),
                "has_usb": caps.get("usb_hid", True),
                "has_ir": caps.get("ir_blaster", False),
                "web_ui": cfg.get("web_ui", ""),
                "version": cfg.get("version", ""),
                "capabilities": caps,
                "is_local": False,
            })
    
    return jsonify({"hubs": hubs, "mqtt_available": mqtt_client is not None and mqtt_client.connected})

def get_local_ip():
    """Get the local IP address."""
    import socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

def get_hub_id():
    """Generate a consistent hub ID based on MAC address."""
    import uuid
    try:
        mac = uuid.getnode()
        return f"pihub_{mac:012x}"[-16:]
    except:
        return "pihub_local"

def get_bluetooth_status():
    """Get Bluetooth adapter status."""
    import subprocess
    import shutil
    
    status = {
        "available": False,
        "powered": False,
        "address": None,
        "name": None,
    }
    
    if not shutil.which("bluetoothctl"):
        return status
    
    try:
        result = subprocess.run(
            ["bluetoothctl", "show"],
            capture_output=True, text=True, timeout=5
        )
        
        if "Controller" in result.stdout:
            status["available"] = True
            status["powered"] = "Powered: yes" in result.stdout
            
            for line in result.stdout.split('\n'):
                if line.strip().startswith("Controller"):
                    parts = line.split()
                    if len(parts) >= 2:
                        status["address"] = parts[1]
                elif "Name:" in line:
                    status["name"] = line.split(":", 1)[1].strip()
    except:
        pass
    
    return status

def get_wifi_status():
    """Get WiFi connection status."""
    import subprocess
    import re
    
    status = {
        "connected": False,
        "ssid": None,
        "frequency": None,
        "band": None,
        "signal_dbm": None,
        "interface": "wlan0",
    }
    
    try:
        # Use iwconfig to get WiFi info
        result = subprocess.run(
            ["iwconfig", "wlan0"],
            capture_output=True, text=True, timeout=5
        )
        
        output = result.stdout
        
        # Parse ESSID
        essid_match = re.search(r'ESSID:"([^"]*)"', output)
        if essid_match and essid_match.group(1):
            status["ssid"] = essid_match.group(1)
            status["connected"] = True
        
        # Parse frequency
        freq_match = re.search(r'Frequency:(\d+\.?\d*)\s*(GHz|MHz)', output)
        if freq_match:
            freq = float(freq_match.group(1))
            unit = freq_match.group(2)
            if unit == "GHz":
                status["frequency"] = f"{freq} GHz"
                if freq < 3:
                    status["band"] = "2.4 GHz"
                else:
                    status["band"] = "5 GHz"
            else:
                status["frequency"] = f"{freq} MHz"
        
        # Parse signal level
        signal_match = re.search(r'Signal level[=:](-?\d+)', output)
        if signal_match:
            status["signal_dbm"] = int(signal_match.group(1))
            
    except:
        pass
    
    return status

@app.route("/api/omniremote/bluetooth/control", methods=["POST"])
def api_bluetooth_control():
    """Control Bluetooth adapter - power on/off, discoverable, etc."""
    import subprocess
    import shutil
    
    data = request.get_json() or {}
    action = data.get("action", "status")
    
    if not shutil.which("bluetoothctl"):
        return jsonify({"success": False, "error": "Bluetooth not installed"})
    
    result = {"success": False, "action": action}
    
    try:
        if action == "status":
            # Get current status
            status_result = subprocess.run(
                ["bluetoothctl", "show"],
                capture_output=True, text=True, timeout=5
            )
            result["success"] = True
            result["output"] = status_result.stdout
            
            # Parse status
            result["powered"] = "Powered: yes" in status_result.stdout
            result["discoverable"] = "Discoverable: yes" in status_result.stdout
            result["pairable"] = "Pairable: yes" in status_result.stdout
            result["available"] = "Controller" in status_result.stdout
            
            # Get controller address
            for line in status_result.stdout.split('\n'):
                if line.strip().startswith("Controller"):
                    parts = line.split()
                    if len(parts) >= 2:
                        result["address"] = parts[1]
                elif "Name:" in line:
                    result["name"] = line.split(":", 1)[1].strip()
                    
        elif action in ("power_on", "enable"):
            # Unblock with rfkill first
            subprocess.run(["rfkill", "unblock", "bluetooth"], capture_output=True, timeout=5)
            
            # Power on
            power_result = subprocess.run(
                ["bluetoothctl", "power", "on"],
                capture_output=True, text=True, timeout=5
            )
            result["success"] = "succeeded" in power_result.stdout.lower() or "yes" in power_result.stdout.lower()
            result["output"] = power_result.stdout
            
        elif action in ("power_off", "disable"):
            power_result = subprocess.run(
                ["bluetoothctl", "power", "off"],
                capture_output=True, text=True, timeout=5
            )
            result["success"] = "succeeded" in power_result.stdout.lower() or "no" in power_result.stdout.lower()
            result["output"] = power_result.stdout
            
        elif action == "discoverable_on":
            disc_result = subprocess.run(
                ["bluetoothctl", "discoverable", "on"],
                capture_output=True, text=True, timeout=5
            )
            result["success"] = "succeeded" in disc_result.stdout.lower()
            result["output"] = disc_result.stdout
            
        elif action == "discoverable_off":
            disc_result = subprocess.run(
                ["bluetoothctl", "discoverable", "off"],
                capture_output=True, text=True, timeout=5
            )
            result["success"] = "succeeded" in disc_result.stdout.lower()
            result["output"] = disc_result.stdout
            
        elif action == "restart_service":
            # Restart bluetooth service
            restart_result = subprocess.run(
                ["systemctl", "restart", "bluetooth"],
                capture_output=True, text=True, timeout=30
            )
            result["success"] = restart_result.returncode == 0
            result["output"] = restart_result.stdout + restart_result.stderr
            
            # Wait and power on
            import time
            time.sleep(2)
            subprocess.run(["bluetoothctl", "power", "on"], capture_output=True, timeout=5)
            
        else:
            result["error"] = f"Unknown action: {action}"
            
    except Exception as e:
        result["error"] = str(e)
        log.error(f"Bluetooth control error: {e}")
    
    return jsonify(result)

@app.route("/api/omniremote/wifi/control", methods=["POST"])
def api_wifi_control():
    """Get WiFi status and info (read-only for safety)."""
    import subprocess
    
    data = request.get_json() or {}
    action = data.get("action", "status")
    
    result = {"success": False, "action": action}
    
    try:
        if action == "status":
            # Get WiFi status
            result["success"] = True
            
            # Get interface info
            try:
                iw_result = subprocess.run(
                    ["iwconfig", "wlan0"],
                    capture_output=True, text=True, timeout=5
                )
                result["interface"] = "wlan0"
                result["output"] = iw_result.stdout
                
                # Parse ESSID
                for line in iw_result.stdout.split('\n'):
                    if "ESSID:" in line:
                        essid = line.split('ESSID:')[1].strip().strip('"')
                        result["ssid"] = essid
                    if "Frequency:" in line:
                        if "2.4" in line or "2.5" in line:
                            result["band"] = "2.4GHz"
                        elif "5." in line:
                            result["band"] = "5GHz"
                    if "Signal level" in line:
                        # Parse signal level
                        import re
                        match = re.search(r'Signal level[=:](-?\d+)', line)
                        if match:
                            result["signal_dbm"] = int(match.group(1))
            except:
                pass
            
            # Get IP address
            try:
                ip_result = subprocess.run(
                    ["hostname", "-I"],
                    capture_output=True, text=True, timeout=5
                )
                result["ip"] = ip_result.stdout.strip().split()[0]
            except:
                pass
                
        else:
            result["error"] = "Only 'status' action is supported for WiFi"
            
    except Exception as e:
        result["error"] = str(e)
    
    return jsonify(result)

@app.route("/api/omniremote/pi_hubs/discover", methods=["POST"])
def api_pi_hubs_discover():
    if mqtt_client:
        success = mqtt_client.publish_discover()
        return jsonify({"success": success, "message": "Discovery request sent"})
    return jsonify({"success": False, "error": "MQTT not connected"})

@app.route("/api/omniremote/pi_hubs/devices", methods=["POST"])
def api_pi_hubs_devices():
    """Return USB devices connected to this Pi Hub."""
    # This is the standalone Pi Hub, so return our own devices
    import evdev
    
    devices = []
    try:
        for path in evdev.list_devices():
            try:
                dev = evdev.InputDevice(path)
                # Filter for remotes/keyboards/mice
                name_lower = dev.name.lower()
                is_remote = any(x in name_lower for x in ['remote', 'keyboard', 'g20', 'g30', 'air', 'mouse', 'hid'])
                
                if is_remote:
                    devices.append({
                        "path": dev.path,
                        "name": dev.name,
                        "phys": getattr(dev, 'phys', ''),
                        "type": "usb_hid",
                        "hub_id": config.get("hub_id", get_hub_id()),
                        "hub_name": config.get("name", "Pi Hub"),
                    })
            except:
                pass
    except Exception as e:
        log.error(f"Error listing devices: {e}")
    
    return jsonify({
        "success": True,
        "devices": devices,
        "hub_id": config.get("hub_id", get_hub_id()),
        "hub_name": config.get("name", "Pi Hub"),
    })

@app.route("/api/omniremote/send", methods=["POST"])
def api_send():
    data = request.json or {}
    device_id = data.get("device_id")
    command = data.get("command")
    
    if mqtt_client and mqtt_client.connected:
        success = mqtt_client.send_command(device_id, command)
        return jsonify({"success": success})
    
    return jsonify({"success": False, "error": "MQTT not connected"})

#-------------------------------------------------------------------------------
# SSL Certificate Management
#-------------------------------------------------------------------------------

def setup_ssl(log, ssl_config: dict):
    """Setup SSL with self-signed certificate or provided cert."""
    import ssl
    import subprocess
    
    ssl_dir = Path("/etc/omniremote/ssl")
    cert_file = ssl_dir / "server.crt"
    key_file = ssl_dir / "server.key"
    
    # Check for custom cert paths in config
    if ssl_config.get("cert_file"):
        cert_file = Path(ssl_config["cert_file"])
    if ssl_config.get("key_file"):
        key_file = Path(ssl_config["key_file"])
    
    # Generate self-signed cert if needed
    if not cert_file.exists() or not key_file.exists():
        log.info("Generating self-signed SSL certificate...")
        try:
            ssl_dir.mkdir(parents=True, exist_ok=True)
            
            # Get hostname for certificate
            import socket
            hostname = socket.gethostname()
            
            # Generate self-signed certificate using openssl
            cmd = [
                "openssl", "req", "-x509", "-newkey", "rsa:2048",
                "-keyout", str(key_file),
                "-out", str(cert_file),
                "-days", "3650",  # 10 years
                "-nodes",  # No passphrase
                "-subj", f"/CN={hostname}/O=OmniRemote/OU=Pi Hub",
                "-addext", f"subjectAltName=DNS:{hostname},DNS:localhost,IP:127.0.0.1"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                log.error(f"Failed to generate SSL cert: {result.stderr}")
                return None
            
            # Set permissions
            key_file.chmod(0o600)
            cert_file.chmod(0o644)
            
            log.info(f"SSL certificate generated: {cert_file}")
            log.info(f"Certificate valid for: {hostname}, localhost, 127.0.0.1")
            log.info("Note: Browser will show security warning for self-signed cert")
            
        except Exception as e:
            log.error(f"SSL certificate generation failed: {e}")
            return None
    
    # Create SSL context
    try:
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(str(cert_file), str(key_file))
        
        # Modern security settings
        context.minimum_version = ssl.TLSVersion.TLSv1_2
        context.set_ciphers('ECDHE+AESGCM:DHE+AESGCM:ECDHE+CHACHA20:DHE+CHACHA20')
        
        log.info("SSL context configured successfully")
        return context
        
    except Exception as e:
        log.error(f"Failed to create SSL context: {e}")
        return None

#-------------------------------------------------------------------------------
# Main
#-------------------------------------------------------------------------------

def main():
    global db, mqtt_client, config, log, panel_js_path
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", "-c", default="/etc/omniremote/config.yaml")
    parser.add_argument("--panel", "-p", help="Path to panel.js file")
    parser.add_argument("--no-ssl", action="store_true", help="Disable SSL")
    args = parser.parse_args()
    
    cfg_path = Path(args.config)
    config = yaml.safe_load(cfg_path.read_text()) if cfg_path.exists() else {}
    
    # Panel.js location
    if args.panel:
        panel_js_path = Path(args.panel)
    else:
        panel_js_path = config.get("web_server", {}).get("panel_js")
        if panel_js_path:
            panel_js_path = Path(panel_js_path)
    
    log = setup_logging(config)
    log.info("=" * 60)
    log.info("OmniRemote™ Standalone Web Server")
    log.info("──────────")
    log.info(f"Version {VERSION} | Panel {PANEL_VERSION}")
    log.info("© 2026 One Eye Enterprises LLC")
    log.info("=" * 60)
    
    # Initialize database
    db_path = config.get("web_server", {}).get("data_file", "/etc/omniremote/database.json")
    db = Database(db_path, log)
    
    # Initialize MQTT
    mqtt_client = MQTTClient(config, db, log)
    mqtt_client.connect()
    
    # Start web server
    web = config.get("web_server", {})
    host = web.get("host", "0.0.0.0")
    port = int(web.get("port", 8125))
    
    if panel_js_path and panel_js_path.exists():
        log.info(f"Panel.js: {panel_js_path}")
    else:
        log.warning("Panel.js not found - UI may not work correctly")
        log.info("Copy panel.js to /etc/omniremote/panel.js or specify with --panel")
    
    # SSL Configuration
    ssl_config = web.get("ssl", {})
    ssl_enabled = ssl_config.get("enabled", True) and not args.no_ssl
    ssl_context = None
    
    if ssl_enabled:
        ssl_context = setup_ssl(log, ssl_config)
        if ssl_context:
            log.info(f"Starting on https://{host}:{port}")
        else:
            log.warning("SSL setup failed, falling back to HTTP")
            log.info(f"Starting on http://{host}:{port}")
    else:
        log.info(f"Starting on http://{host}:{port} (SSL disabled)")
    
    app.run(host=host, port=port, threaded=True, debug=False, ssl_context=ssl_context)

if __name__ == "__main__":
    main()
