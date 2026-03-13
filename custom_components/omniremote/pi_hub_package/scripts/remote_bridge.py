#!/usr/bin/env python3
"""
OmniRemote™ Pi Zero Remote Bridge v1.2.0

Monitors USB HID devices (2.4GHz dongles) and Bluetooth HID remotes,
forwarding button presses to Home Assistant via MQTT.

© 2026 One Eye Enterprises LLC
"""

import asyncio
import argparse
import json
import os
import re
import signal
import sys
import logging
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Dict, List, Optional, Set

import yaml
import paho.mqtt.client as mqtt

try:
    from evdev import InputDevice, ecodes, list_devices
    EVDEV_AVAILABLE = True
except ImportError:
    EVDEV_AVAILABLE = False

VERSION = "1.5.26"

KEY_MAP = {
    116: "power", 142: "sleep", 143: "wakeup",
    103: "up", 108: "down", 105: "left", 106: "right",
    28: "ok", 96: "ok", 352: "ok", 353: "select",
    1: "back", 158: "back", 14: "back",
    102: "home", 172: "home", 139: "menu", 127: "menu",
    358: "info", 362: "guide", 365: "guide",
    115: "volume_up", 114: "volume_down", 113: "mute",
    402: "channel_up", 403: "channel_down",
    164: "play_pause", 207: "play", 119: "pause",
    128: "stop", 166: "stop", 163: "next", 165: "previous",
    168: "rewind", 208: "fast_forward", 159: "forward", 167: "record",
    11: "num_0", 2: "num_1", 3: "num_2", 4: "num_3", 5: "num_4",
    6: "num_5", 7: "num_6", 8: "num_7", 9: "num_8", 10: "num_9",
    398: "red", 399: "green", 400: "yellow", 401: "blue",
    59: "f1", 60: "f2", 61: "f3", 62: "f4", 63: "f5", 64: "f6",
    65: "f7", 66: "f8", 67: "f9", 68: "f10", 87: "f11", 88: "f12",
    227: "source", 377: "tv", 272: "mouse_left", 273: "mouse_right",
    582: "voice", 217: "search", 171: "settings", 364: "favorites",
}


def setup_logging(config: dict) -> logging.Logger:
    cfg = config.get("logging", {})
    log_file = cfg.get("file", "/var/log/omniremote/bridge.log")
    level = getattr(logging, cfg.get("level", "INFO"))
    
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    
    logger = logging.getLogger("OmniRemoteBridge")
    logger.setLevel(level)
    logger.handlers.clear()
    
    fh = RotatingFileHandler(log_file, maxBytes=10*1024*1024, backupCount=3)
    fh.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
    ch = logging.StreamHandler()
    ch.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
    
    logger.addHandler(fh)
    logger.addHandler(ch)
    return logger


class RemoteBridge:
    def __init__(self, config: dict, log: logging.Logger):
        self.config = config
        self.log = log
        self.mqtt: Optional[mqtt.Client] = None
        self.connected = False
        self.running = False
        self.patterns = []
        self.button_count = 0
        self.start_time = datetime.now()
        self.hub_id = self._get_hub_id()
        
        for p in config.get("bridge", {}).get("device_patterns", []):
            try:
                self.patterns.append(re.compile(p, re.IGNORECASE))
            except re.error:
                pass
    
    def _get_hub_id(self) -> str:
        """Generate unique hub ID from hostname or MAC."""
        import socket
        hostname = socket.gethostname()
        # Try to get MAC address for uniqueness
        try:
            with open('/sys/class/net/wlan0/address', 'r') as f:
                mac = f.read().strip().replace(':', '')[-6:]
                return f"{hostname}_{mac}"
        except:
            return hostname
    
    def _get_ip_address(self) -> str:
        """Get the Pi's IP address."""
        import socket
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "unknown"
    
    def _get_bluetooth_status(self) -> dict:
        """Get Bluetooth adapter info."""
        import subprocess
        try:
            result = subprocess.run(['hciconfig'], capture_output=True, text=True, timeout=5)
            if 'hci0' in result.stdout and 'UP RUNNING' in result.stdout:
                return {"available": True, "adapter": "hci0", "status": "up"}
            elif 'hci0' in result.stdout:
                return {"available": True, "adapter": "hci0", "status": "down"}
            return {"available": False}
        except:
            return {"available": False}
    
    def connect_mqtt(self) -> bool:
        cfg = self.config.get("mqtt", {})
        broker = cfg.get("broker", "localhost")
        port = int(cfg.get("port", 1883))
        
        try:
            self.mqtt = mqtt.Client(client_id=cfg.get("client_id", f"omniremote-hub-{self.hub_id}"))
            if cfg.get("username"):
                self.mqtt.username_pw_set(cfg["username"], cfg.get("password", ""))
            
            self.mqtt.on_connect = self._on_connect
            self.mqtt.on_disconnect = self._on_disconnect
            self.mqtt.on_message = self._on_message
            
            # Set last will for offline status
            prefix = cfg.get("topic_prefix", "omniremote")
            self.mqtt.will_set(f"{prefix}/hub/{self.hub_id}/status", 
                               json.dumps({"status": "offline"}), retain=True)
            
            self.mqtt.connect(broker, port, keepalive=60)
            self.mqtt.loop_start()
            self.log.info(f"Connecting to MQTT at {broker}:{port}")
            return True
        except Exception as e:
            self.log.error(f"MQTT error: {e}")
            return False
    
    def _on_disconnect(self, client, userdata, rc):
        self.connected = False
        self.log.warning(f"MQTT disconnected (rc={rc})")
    
    def _on_message(self, client, userdata, msg):
        """Handle incoming MQTT messages (for HA commands)."""
        try:
            prefix = self.config.get("mqtt", {}).get("topic_prefix", "omniremote")
            
            if msg.topic == f"{prefix}/hub/{self.hub_id}/command":
                payload = json.loads(msg.payload.decode())
                self._handle_command(payload)
            
            elif msg.topic == f"{prefix}/hub/{self.hub_id}/ir/send":
                payload = json.loads(msg.payload.decode())
                self._handle_ir_send(payload)
            
            elif msg.topic == f"{prefix}/hub/discover":
                # Re-announce ourselves
                self._publish_discovery()
            
            # Config sync from HA
            elif msg.topic == f"{prefix}/config/physical_remotes":
                payload = json.loads(msg.payload.decode())
                self._sync_physical_remotes(payload)
            
            elif msg.topic == f"{prefix}/config/rooms":
                payload = json.loads(msg.payload.decode())
                self._sync_rooms(payload)
            
            elif msg.topic == f"{prefix}/config/devices":
                payload = json.loads(msg.payload.decode())
                self._sync_devices(payload)
                
        except Exception as e:
            self.log.error(f"Message handling error: {e}")
    
    def _sync_physical_remotes(self, payload: dict):
        """Sync physical remotes config from HA."""
        remotes = payload.get("remotes", {})
        if not remotes:
            return
        
        self.log.info(f"📥 Syncing {len(remotes)} physical remotes from HA")
        
        # Load current database
        db_path = Path("/etc/omniremote/database.json")
        db = {}
        if db_path.exists():
            try:
                db = json.loads(db_path.read_text())
            except:
                db = {}
        
        # Update physical remotes (merge, don't replace)
        if "physical_remotes" not in db:
            db["physical_remotes"] = {}
        
        for remote_id, remote_data in remotes.items():
            # Mark as synced from HA
            remote_data["synced_from_ha"] = True
            db["physical_remotes"][remote_id] = remote_data
        
        # Save
        db_path.parent.mkdir(parents=True, exist_ok=True)
        db_path.write_text(json.dumps(db, indent=2))
        self.log.info(f"✓ Physical remotes synced")
    
    def _sync_rooms(self, payload: dict):
        """Sync rooms config from HA."""
        rooms = payload.get("rooms", {})
        if not rooms:
            return
        
        self.log.info(f"📥 Syncing {len(rooms)} rooms from HA")
        
        db_path = Path("/etc/omniremote/database.json")
        db = {}
        if db_path.exists():
            try:
                db = json.loads(db_path.read_text())
            except:
                db = {}
        
        if "rooms" not in db:
            db["rooms"] = {}
        
        for room_id, room_data in rooms.items():
            room_data["synced_from_ha"] = True
            db["rooms"][room_id] = room_data
        
        db_path.parent.mkdir(parents=True, exist_ok=True)
        db_path.write_text(json.dumps(db, indent=2))
        self.log.info(f"✓ Rooms synced")
    
    def _sync_devices(self, payload: dict):
        """Sync devices config from HA."""
        devices = payload.get("devices", {})
        if not devices:
            return
        
        self.log.info(f"📥 Syncing {len(devices)} devices from HA")
        
        db_path = Path("/etc/omniremote/database.json")
        db = {}
        if db_path.exists():
            try:
                db = json.loads(db_path.read_text())
            except:
                db = {}
        
        if "devices" not in db:
            db["devices"] = {}
        
        for device_id, device_data in devices.items():
            device_data["synced_from_ha"] = True
            db["devices"][device_id] = device_data
        
        db_path.parent.mkdir(parents=True, exist_ok=True)
        db_path.write_text(json.dumps(db, indent=2))
        self.log.info(f"✓ Devices synced")
    
    def _handle_ir_send(self, payload: dict):
        """Handle IR send request from Home Assistant."""
        code = payload.get("code")
        protocol = payload.get("protocol", "raw")
        
        if not code:
            self.log.warning("IR send request missing code")
            return
        
        self.log.info(f"📡 Sending IR: protocol={protocol}")
        
        # Check if we have an IR blaster configured
        ir_config = self.config.get("ir_blaster", {})
        if not ir_config.get("enabled", False):
            self.log.warning("IR blaster not enabled in config")
            return
        
        try:
            # Send via pigpio or other IR library
            import base64
            
            gpio_pin = ir_config.get("gpio", 18)  # Default GPIO 18 for IR LED
            
            if protocol == "broadlink":
                # Broadlink format - decode and convert to raw timings
                ir_bytes = base64.b64decode(code)
                self._send_ir_broadlink(ir_bytes, gpio_pin)
            elif protocol == "raw":
                # Raw timing format
                timings = payload.get("timings", [])
                self._send_ir_raw(timings, gpio_pin)
            elif protocol == "nec":
                # NEC protocol
                address = payload.get("address", 0)
                command = payload.get("command", 0)
                self._send_ir_nec(address, command, gpio_pin)
            else:
                self.log.warning(f"Unknown IR protocol: {protocol}")
                
        except Exception as e:
            self.log.error(f"IR send error: {e}")
    
    def _send_ir_broadlink(self, ir_bytes: bytes, gpio_pin: int):
        """Send IR using Broadlink packet format via GPIO."""
        try:
            import pigpio
            
            # Parse Broadlink packet to get timings
            # Broadlink format: repeat, len_hi, len_lo, timings...
            if len(ir_bytes) < 4:
                return
            
            # Extract timing data (skip header)
            timings = []
            i = 4
            while i < len(ir_bytes) - 1:
                if ir_bytes[i] == 0:
                    # Extended timing
                    if i + 2 < len(ir_bytes):
                        us = (ir_bytes[i+1] << 8) | ir_bytes[i+2]
                        timings.append(us * 8.192)  # Convert to microseconds
                        i += 3
                else:
                    timings.append(ir_bytes[i] * 8.192)
                    i += 1
            
            if timings:
                self._transmit_ir(timings, gpio_pin)
                self.log.info(f"Sent {len(timings)} IR pulses")
            
        except ImportError:
            self.log.error("pigpio not available - cannot send IR")
        except Exception as e:
            self.log.error(f"Broadlink IR send error: {e}")
    
    def _send_ir_raw(self, timings: list, gpio_pin: int):
        """Send raw IR timings via GPIO."""
        if timings:
            self._transmit_ir(timings, gpio_pin)
            self.log.info(f"Sent {len(timings)} raw IR pulses")
    
    def _send_ir_nec(self, address: int, command: int, gpio_pin: int):
        """Send NEC IR code via GPIO."""
        # Generate NEC timing pattern
        # NEC: 9ms leader, 4.5ms space, then 32 bits (address, ~address, command, ~command)
        
        LEADER_MARK = 9000
        LEADER_SPACE = 4500
        BIT_MARK = 560
        ONE_SPACE = 1690
        ZERO_SPACE = 560
        
        timings = [LEADER_MARK, LEADER_SPACE]
        
        # Build 32-bit data: address (8), ~address (8), command (8), ~command (8)
        data = (address & 0xFF) | ((~address & 0xFF) << 8) | ((command & 0xFF) << 16) | ((~command & 0xFF) << 24)
        
        for i in range(32):
            timings.append(BIT_MARK)
            if (data >> i) & 1:
                timings.append(ONE_SPACE)
            else:
                timings.append(ZERO_SPACE)
        
        timings.append(BIT_MARK)  # Final mark
        
        self._transmit_ir(timings, gpio_pin)
        self.log.info(f"Sent NEC IR: addr=0x{address:02X}, cmd=0x{command:02X}")
    
    def _transmit_ir(self, timings: list, gpio_pin: int):
        """Transmit IR pulses via GPIO using pigpio."""
        try:
            import pigpio
            
            pi = pigpio.pi()
            if not pi.connected:
                self.log.error("Cannot connect to pigpio daemon")
                return
            
            # Set up GPIO for output
            pi.set_mode(gpio_pin, pigpio.OUTPUT)
            
            # Create wave
            CARRIER_FREQ = 38000  # 38kHz carrier
            
            # Build waveform
            wave = []
            for i, duration in enumerate(timings):
                if i % 2 == 0:  # Mark (IR on with carrier)
                    cycles = int(duration * CARRIER_FREQ / 1000000)
                    for _ in range(cycles):
                        wave.append(pigpio.pulse(1 << gpio_pin, 0, 13))  # On for ~13us
                        wave.append(pigpio.pulse(0, 1 << gpio_pin, 13))  # Off for ~13us
                else:  # Space (IR off)
                    wave.append(pigpio.pulse(0, 1 << gpio_pin, int(duration)))
            
            pi.wave_add_generic(wave)
            wid = pi.wave_create()
            
            if wid >= 0:
                pi.wave_send_once(wid)
                while pi.wave_tx_busy():
                    pass
                pi.wave_delete(wid)
            
            pi.stop()
            
        except ImportError:
            self.log.error("pigpio not available for IR transmission")
        except Exception as e:
            self.log.error(f"IR transmit error: {e}")
    
    def _handle_command(self, payload: dict):
        """Handle commands from Home Assistant."""
        cmd = payload.get("command")
        self.log.info(f"Received command: {cmd}")
        
        if cmd == "scan_devices":
            self._publish_devices()
        elif cmd == "enable_bluetooth":
            self._set_bluetooth(True)
        elif cmd == "disable_bluetooth":
            self._set_bluetooth(False)
        elif cmd == "restart":
            self.log.info("Restart requested")
            os.system("sudo systemctl restart omniremote-bridge")
    
    def _set_bluetooth(self, enable: bool):
        """Enable or disable Bluetooth."""
        import subprocess
        try:
            cmd = "up" if enable else "down"
            subprocess.run(['sudo', 'hciconfig', 'hci0', cmd], check=True)
            self.log.info(f"Bluetooth set to {cmd}")
            self._publish_discovery()  # Update status
        except Exception as e:
            self.log.error(f"Bluetooth control error: {e}")
    
    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self.connected = True
            self.log.info("✓ MQTT connected")
            
            prefix = self.config.get("mqtt", {}).get("topic_prefix", "omniremote")
            
            # Subscribe to commands
            client.subscribe(f"{prefix}/hub/{self.hub_id}/command")
            client.subscribe(f"{prefix}/hub/{self.hub_id}/ir/send")  # IR send commands
            client.subscribe(f"{prefix}/hub/discover")  # Discovery request
            
            # Subscribe to config sync from HA (retained messages)
            client.subscribe(f"{prefix}/config/physical_remotes")
            client.subscribe(f"{prefix}/config/rooms")
            client.subscribe(f"{prefix}/config/devices")
            
            # Publish discovery info
            self._publish_discovery()
            
            # Publish connected devices
            self._publish_devices()
    
    def _publish_discovery(self):
        """Publish auto-discovery message for Home Assistant."""
        if not self.connected:
            return
        
        prefix = self.config.get("mqtt", {}).get("topic_prefix", "omniremote")
        bridge_cfg = self.config.get("bridge", {})
        
        bt_status = self._get_bluetooth_status()
        
        discovery_payload = {
            "hub_id": self.hub_id,
            "name": self.config.get("hub_name", f"Pi Hub ({self.hub_id})"),
            "version": VERSION,
            "ip": self._get_ip_address(),
            "status": "online",
            "started": self.start_time.isoformat(),
            "capabilities": {
                "usb_hid": bridge_cfg.get("usb_hid", True),
                "bluetooth": bt_status.get("available", False),
                "bluetooth_status": bt_status.get("status", "unknown"),
                "ir_blaster": bridge_cfg.get("ir_blaster", False),
            },
            "web_ui": f"http://{self._get_ip_address()}:{self.config.get('web_server', {}).get('port', 8080)}",
            "button_count": self.button_count,
        }
        
        # Publish to discovery topic (for HA to find)
        self.mqtt.publish(f"{prefix}/hub/{self.hub_id}/config", 
                         json.dumps(discovery_payload), retain=True)
        
        # Also publish status
        self.mqtt.publish(f"{prefix}/hub/{self.hub_id}/status",
                         json.dumps({"status": "online", "version": VERSION}), retain=True)
        
        self.log.info(f"📢 Published discovery: {self.hub_id}")
    
    def _publish_devices(self):
        """Publish list of connected input devices."""
        if not self.connected:
            return
        
        prefix = self.config.get("mqtt", {}).get("topic_prefix", "omniremote")
        devices = []
        
        for dev in self.scan():
            devices.append({
                "name": dev.name,
                "path": dev.path,
                "phys": getattr(dev, 'phys', ''),
            })
        
        self.mqtt.publish(f"{prefix}/hub/{self.hub_id}/devices",
                         json.dumps({"devices": devices}), retain=True)
        self.log.info(f"Published {len(devices)} devices")
    
    def publish(self, device: str, button: str, action: str = "press"):
        if not self.connected:
            return
        
        prefix = self.config.get("mqtt", {}).get("topic_prefix", "omniremote")
        payload = {
            "hub_id": self.hub_id,
            "device": device, 
            "button": button, 
            "action": action, 
            "timestamp": datetime.now().isoformat()
        }
        
        self.button_count += 1
        self.log.info(f"🔘 {button} ({action}) from '{device}'")
        
        try:
            self.mqtt.publish(f"{prefix}/physical_remote", json.dumps(payload))
            # Update discovery with new button count periodically
            if self.button_count % 100 == 0:
                self._publish_discovery()
        except Exception as e:
            self.log.error(f"Publish error: {e}")
    
    def matches(self, name: str) -> bool:
        return not self.patterns or any(p.search(name) for p in self.patterns)
    
    def scan(self) -> List[InputDevice]:
        found = []
        for path in list_devices():
            try:
                dev = InputDevice(path)
                if ecodes.EV_KEY in dev.capabilities() and self.matches(dev.name):
                    found.append(dev)
            except:
                pass
        return found
    
    async def monitor(self, dev: InputDevice):
        self.log.info(f"📡 Monitoring: {dev.name}")
        try:
            async for ev in dev.async_read_loop():
                if not self.running:
                    break
                if ev.type == ecodes.EV_KEY and ev.value in (1, 2):
                    btn = KEY_MAP.get(ev.code, f"key_{ev.code}")
                    self.publish(dev.name, btn, "press" if ev.value == 1 else "hold")
        except:
            pass
        self.log.info(f"Stopped: {dev.name}")
    
    async def watcher(self):
        known: Set[str] = set()
        tasks: Dict[str, asyncio.Task] = {}
        
        while self.running:
            current = {d.path: d for d in self.scan()}
            
            for path, dev in current.items():
                if path not in known:
                    self.log.info(f"🔌 New: {dev.name}")
                    tasks[path] = asyncio.create_task(self.monitor(dev))
                    known.add(path)
            
            for path in known - set(current.keys()):
                self.log.info(f"🔌 Removed: {path}")
                if path in tasks:
                    tasks[path].cancel()
                    del tasks[path]
                known.discard(path)
            
            await asyncio.sleep(5)
    
    async def run(self):
        self.running = True
        
        self.log.info("=" * 50)
        self.log.info("OmniRemote™ Pi Bridge")
        self.log.info("──────────")
        self.log.info(f"Version {VERSION}")
        self.log.info("© 2026 One Eye Enterprises LLC")
        self.log.info("=" * 50)
        
        if not EVDEV_AVAILABLE:
            self.log.error("evdev not available")
            return
        
        for _ in range(10):
            if self.connect_mqtt():
                await asyncio.sleep(2)
                if self.connected:
                    break
            await asyncio.sleep(5)
        
        if not self.connected:
            self.log.error("MQTT failed after 10 attempts")
            return
        
        self.log.info("Waiting for remotes... Plug in USB dongle")
        
        try:
            await self.watcher()
        except asyncio.CancelledError:
            pass
        
        self.log.info(f"Shutdown. Buttons: {self.button_count}")
        prefix = self.config.get("mqtt", {}).get("topic_prefix", "omniremote")
        self.mqtt.publish(f"{prefix}/bridge/status", json.dumps({"status": "offline"}), retain=True)
        self.mqtt.loop_stop()
    
    def stop(self):
        self.running = False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", "-c", default="/etc/omniremote/config.yaml")
    args = parser.parse_args()
    
    cfg_path = Path(args.config)
    config = yaml.safe_load(cfg_path.read_text()) if cfg_path.exists() else {}
    
    log = setup_logging(config)
    bridge = RemoteBridge(config, log)
    
    signal.signal(signal.SIGINT, lambda s, f: bridge.stop())
    signal.signal(signal.SIGTERM, lambda s, f: bridge.stop())
    
    asyncio.run(bridge.run())


if __name__ == "__main__":
    main()
