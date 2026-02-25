#!/usr/bin/env python3
"""
OmniRemote USB/Bluetooth Bridge

This script runs on a Raspberry Pi Zero W (or similar) and:
1. Captures USB keyboard events from remotes like MX3 Air Mouse
2. Captures Bluetooth HID events from paired remotes
3. Sends button press events to Home Assistant via MQTT

Install on Pi Zero W:
    pip3 install evdev paho-mqtt

Run as service:
    sudo cp omniremote-bridge.service /etc/systemd/system/
    sudo systemctl enable omniremote-bridge
    sudo systemctl start omniremote-bridge
"""

import argparse
import asyncio
import json
import logging
import os
import socket
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

try:
    import evdev
    from evdev import InputDevice, categorize, ecodes
except ImportError:
    print("ERROR: evdev not installed. Run: pip3 install evdev")
    sys.exit(1)

try:
    import paho.mqtt.client as mqtt
except ImportError:
    print("ERROR: paho-mqtt not installed. Run: pip3 install paho-mqtt")
    sys.exit(1)

# =============================================================================
# Configuration
# =============================================================================

@dataclass
class BridgeConfig:
    """Bridge configuration."""
    bridge_id: str = ""
    bridge_name: str = "OmniRemote Bridge"
    
    # MQTT settings
    mqtt_host: str = "homeassistant.local"
    mqtt_port: int = 1883
    mqtt_username: str = ""
    mqtt_password: str = ""
    mqtt_topic_prefix: str = "omniremote/bridge"
    
    # Device settings
    device_paths: list = None  # Auto-discover if None
    grab_devices: bool = True  # Prevent events from reaching other apps
    
    # Long press detection
    long_press_ms: int = 500
    double_press_ms: int = 300
    
    # Logging
    log_level: str = "INFO"
    
    def __post_init__(self):
        if not self.bridge_id:
            self.bridge_id = socket.gethostname()
        if self.device_paths is None:
            self.device_paths = []


def load_config(config_path: str) -> BridgeConfig:
    """Load configuration from JSON file."""
    config = BridgeConfig()
    
    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            data = json.load(f)
        
        for key, value in data.items():
            if hasattr(config, key):
                setattr(config, key, value)
    
    return config


def save_config(config: BridgeConfig, config_path: str) -> None:
    """Save configuration to JSON file."""
    data = {
        "bridge_id": config.bridge_id,
        "bridge_name": config.bridge_name,
        "mqtt_host": config.mqtt_host,
        "mqtt_port": config.mqtt_port,
        "mqtt_username": config.mqtt_username,
        "mqtt_password": config.mqtt_password,
        "mqtt_topic_prefix": config.mqtt_topic_prefix,
        "device_paths": config.device_paths,
        "grab_devices": config.grab_devices,
        "long_press_ms": config.long_press_ms,
        "double_press_ms": config.double_press_ms,
        "log_level": config.log_level,
    }
    
    with open(config_path, "w") as f:
        json.dump(data, f, indent=2)


# =============================================================================
# Device Discovery
# =============================================================================

def discover_input_devices() -> list[dict]:
    """Discover available input devices."""
    devices = []
    
    for path in evdev.list_devices():
        try:
            device = InputDevice(path)
            caps = device.capabilities(verbose=True)
            
            # Check if it's a keyboard-like device
            has_keys = ("EV_KEY", ecodes.EV_KEY) in caps or ecodes.EV_KEY in device.capabilities()
            
            if has_keys:
                devices.append({
                    "path": path,
                    "name": device.name,
                    "phys": device.phys,
                    "info": device.info,
                })
            
            device.close()
        except Exception as e:
            logging.debug(f"Could not read device {path}: {e}")
    
    return devices


def find_remote_devices() -> list[str]:
    """Find devices that look like remote controls."""
    remote_keywords = [
        "air mouse", "mx3", "remote", "keyboard", "2.4g",
        "rii", "wechip", "g10", "g20", "g30", "t2", "t6",
    ]
    
    devices = discover_input_devices()
    remote_paths = []
    
    for device in devices:
        name_lower = device["name"].lower()
        if any(keyword in name_lower for keyword in remote_keywords):
            remote_paths.append(device["path"])
            logging.info(f"Found remote: {device['name']} at {device['path']}")
    
    return remote_paths


# =============================================================================
# MQTT Client
# =============================================================================

class MQTTClient:
    """MQTT client for sending events to Home Assistant."""
    
    def __init__(self, config: BridgeConfig):
        self.config = config
        self.client = mqtt.Client(client_id=f"omniremote-bridge-{config.bridge_id}")
        self.connected = False
        
        if config.mqtt_username:
            self.client.username_pw_set(config.mqtt_username, config.mqtt_password)
        
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        
        # Set up LWT (Last Will and Testament)
        status_topic = f"{config.mqtt_topic_prefix}/{config.bridge_id}/status"
        self.client.will_set(status_topic, "offline", qos=1, retain=True)
    
    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            logging.info("Connected to MQTT broker")
            self.connected = True
            
            # Publish online status
            status_topic = f"{self.config.mqtt_topic_prefix}/{self.config.bridge_id}/status"
            self.client.publish(status_topic, "online", qos=1, retain=True)
            
            # Publish discovery info
            self._publish_discovery()
        else:
            logging.error(f"MQTT connection failed with code {rc}")
    
    def _on_disconnect(self, client, userdata, rc):
        logging.warning("Disconnected from MQTT broker")
        self.connected = False
    
    def _publish_discovery(self):
        """Publish bridge discovery info."""
        discovery_topic = f"{self.config.mqtt_topic_prefix}/{self.config.bridge_id}/config"
        
        discovery_payload = {
            "bridge_id": self.config.bridge_id,
            "bridge_name": self.config.bridge_name,
            "bridge_type": "usb_bridge",
            "version": "1.0.0",
            "hostname": socket.gethostname(),
            "ip": self._get_ip(),
        }
        
        self.client.publish(
            discovery_topic, 
            json.dumps(discovery_payload), 
            qos=1, 
            retain=True
        )
    
    def _get_ip(self) -> str:
        """Get local IP address."""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "unknown"
    
    def connect(self):
        """Connect to MQTT broker."""
        try:
            self.client.connect(self.config.mqtt_host, self.config.mqtt_port, 60)
            self.client.loop_start()
        except Exception as e:
            logging.error(f"Failed to connect to MQTT: {e}")
    
    def disconnect(self):
        """Disconnect from MQTT broker."""
        status_topic = f"{self.config.mqtt_topic_prefix}/{self.config.bridge_id}/status"
        self.client.publish(status_topic, "offline", qos=1, retain=True)
        self.client.loop_stop()
        self.client.disconnect()
    
    def publish_event(self, device_name: str, button: str, press_type: str = "short"):
        """Publish a button press event."""
        if not self.connected:
            logging.warning("Not connected to MQTT, event dropped")
            return
        
        event_topic = f"{self.config.mqtt_topic_prefix}/{self.config.bridge_id}/event"
        
        event_payload = {
            "device": device_name,
            "button": button,
            "type": press_type,  # short, long, double
            "timestamp": time.time(),
        }
        
        self.client.publish(event_topic, json.dumps(event_payload), qos=1)
        logging.debug(f"Published: {button} ({press_type}) from {device_name}")


# =============================================================================
# Input Device Handler
# =============================================================================

class InputHandler:
    """Handles input events from USB/Bluetooth devices."""
    
    def __init__(self, device_path: str, mqtt_client: MQTTClient, config: BridgeConfig):
        self.device_path = device_path
        self.mqtt = mqtt_client
        self.config = config
        self.device: Optional[InputDevice] = None
        
        # Press tracking for long/double press detection
        self._press_times: dict[int, float] = {}
        self._last_release: dict[int, float] = {}
    
    async def run(self):
        """Run the input handler."""
        while True:
            try:
                await self._connect_and_read()
            except Exception as e:
                logging.error(f"Error reading {self.device_path}: {e}")
                await asyncio.sleep(5)
    
    async def _connect_and_read(self):
        """Connect to device and read events."""
        self.device = InputDevice(self.device_path)
        device_name = self.device.name
        
        logging.info(f"Connected to: {device_name}")
        
        if self.config.grab_devices:
            try:
                self.device.grab()
                logging.info(f"Grabbed exclusive access to {device_name}")
            except Exception as e:
                logging.warning(f"Could not grab device: {e}")
        
        try:
            async for event in self.device.async_read_loop():
                if event.type == ecodes.EV_KEY:
                    await self._handle_key_event(event, device_name)
        finally:
            if self.config.grab_devices:
                try:
                    self.device.ungrab()
                except Exception:
                    pass
            self.device.close()
    
    async def _handle_key_event(self, event, device_name: str):
        """Handle a key event."""
        key_code = event.code
        key_state = event.value  # 0=up, 1=down, 2=hold
        
        try:
            key_name = ecodes.KEY[key_code]
        except KeyError:
            key_name = f"KEY_{key_code}"
        
        current_time = time.time()
        
        if key_state == 1:  # Key down
            self._press_times[key_code] = current_time
            
        elif key_state == 0:  # Key up
            press_start = self._press_times.get(key_code, current_time)
            press_duration = (current_time - press_start) * 1000  # ms
            
            # Determine press type
            if press_duration >= self.config.long_press_ms:
                press_type = "long"
            else:
                # Check for double press
                last_release = self._last_release.get(key_code, 0)
                if (current_time - last_release) * 1000 < self.config.double_press_ms:
                    press_type = "double"
                else:
                    press_type = "short"
            
            self._last_release[key_code] = current_time
            
            # Publish event
            self.mqtt.publish_event(device_name, key_name, press_type)
            
            # Clean up
            if key_code in self._press_times:
                del self._press_times[key_code]


# =============================================================================
# Main
# =============================================================================

async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="OmniRemote USB/Bluetooth Bridge")
    parser.add_argument(
        "-c", "--config",
        default="/etc/omniremote-bridge/config.json",
        help="Path to configuration file"
    )
    parser.add_argument(
        "--discover",
        action="store_true",
        help="Discover available input devices and exit"
    )
    parser.add_argument(
        "--setup",
        action="store_true",
        help="Interactive setup wizard"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    # Discovery mode
    if args.discover:
        print("\nDiscovering input devices...\n")
        devices = discover_input_devices()
        
        if not devices:
            print("No input devices found!")
            return
        
        print(f"Found {len(devices)} input device(s):\n")
        for i, dev in enumerate(devices):
            print(f"  [{i}] {dev['name']}")
            print(f"      Path: {dev['path']}")
            print(f"      Phys: {dev['phys']}")
            print()
        
        print("Remote-like devices:")
        remotes = find_remote_devices()
        if remotes:
            for path in remotes:
                print(f"  - {path}")
        else:
            print("  (none auto-detected)")
        
        return
    
    # Setup wizard
    if args.setup:
        print("\n=== OmniRemote Bridge Setup ===\n")
        
        config = BridgeConfig()
        
        # MQTT settings
        config.mqtt_host = input(f"MQTT Host [{config.mqtt_host}]: ").strip() or config.mqtt_host
        port_str = input(f"MQTT Port [{config.mqtt_port}]: ").strip()
        if port_str:
            config.mqtt_port = int(port_str)
        config.mqtt_username = input("MQTT Username (blank for none): ").strip()
        if config.mqtt_username:
            config.mqtt_password = input("MQTT Password: ").strip()
        
        # Bridge settings
        config.bridge_id = input(f"Bridge ID [{config.bridge_id}]: ").strip() or config.bridge_id
        config.bridge_name = input(f"Bridge Name [{config.bridge_name}]: ").strip() or config.bridge_name
        
        # Device discovery
        print("\nDiscovering devices...")
        remotes = find_remote_devices()
        
        if remotes:
            print(f"\nFound {len(remotes)} remote-like device(s):")
            for i, path in enumerate(remotes):
                dev = InputDevice(path)
                print(f"  [{i}] {dev.name} ({path})")
                dev.close()
            
            use_all = input("\nUse all discovered remotes? [Y/n]: ").strip().lower()
            if use_all != "n":
                config.device_paths = remotes
            else:
                indices = input("Enter device indices to use (comma-separated): ").strip()
                config.device_paths = [remotes[int(i.strip())] for i in indices.split(",")]
        else:
            print("No remotes auto-discovered. You can add device paths manually to config.")
        
        # Save config
        config_dir = Path(args.config).parent
        config_dir.mkdir(parents=True, exist_ok=True)
        save_config(config, args.config)
        
        print(f"\nConfiguration saved to {args.config}")
        print("\nTo run as a service:")
        print("  sudo systemctl enable omniremote-bridge")
        print("  sudo systemctl start omniremote-bridge")
        
        return
    
    # Load configuration
    config = load_config(args.config)
    
    # Setup logging
    log_level = logging.DEBUG if args.verbose else getattr(logging, config.log_level.upper())
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # Find devices if not configured
    device_paths = config.device_paths
    if not device_paths:
        logging.info("No devices configured, auto-discovering...")
        device_paths = find_remote_devices()
        
        if not device_paths:
            logging.error("No remote devices found!")
            logging.info("Run with --discover to see available devices")
            logging.info("Run with --setup for interactive configuration")
            sys.exit(1)
    
    # Connect to MQTT
    mqtt_client = MQTTClient(config)
    mqtt_client.connect()
    
    # Wait for connection
    for _ in range(10):
        if mqtt_client.connected:
            break
        await asyncio.sleep(0.5)
    
    if not mqtt_client.connected:
        logging.error("Failed to connect to MQTT broker")
        sys.exit(1)
    
    # Start input handlers
    handlers = []
    for path in device_paths:
        handler = InputHandler(path, mqtt_client, config)
        handlers.append(asyncio.create_task(handler.run()))
    
    logging.info(f"Bridge started with {len(handlers)} device(s)")
    
    try:
        await asyncio.gather(*handlers)
    except KeyboardInterrupt:
        logging.info("Shutting down...")
    finally:
        mqtt_client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
