"""Network device controllers for Roku, FireTV, Xbox, PlayStation, etc."""
from __future__ import annotations

import asyncio
import logging
import socket
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

import aiohttp

_LOGGER = logging.getLogger(__name__)


@dataclass
class NetworkDevice:
    """Base class for network-controlled devices."""
    host: str
    port: int
    name: str = ""
    device_type: str = ""
    mac: str = ""
    
    def to_dict(self) -> dict:
        return {
            "host": self.host,
            "port": self.port,
            "name": self.name,
            "device_type": self.device_type,
            "mac": self.mac,
        }


class NetworkController(ABC):
    """Abstract base class for network device controllers."""
    
    @abstractmethod
    async def connect(self) -> bool:
        """Connect to the device."""
        pass
    
    @abstractmethod
    async def send_command(self, command: str) -> bool:
        """Send a command to the device."""
        pass
    
    @abstractmethod
    async def get_state(self) -> dict[str, Any]:
        """Get the current state of the device."""
        pass


# =============================================================================
# ROKU ECP (External Control Protocol)
# =============================================================================

class RokuController(NetworkController):
    """Controller for Roku devices using ECP (External Control Protocol)."""
    
    KEYPRESS_COMMANDS = {
        "home", "rev", "fwd", "play", "select", "left", "right", "down", "up",
        "back", "instantreplay", "info", "backspace", "search", "enter",
        "volumedown", "volumeup", "volumemute", "poweroff", "poweron",
        "channelup", "channeldown", "inputtuner", "inputhdmi1", "inputhdmi2",
        "inputhdmi3", "inputhdmi4", "inputav1", "findremote",
    }
    
    def __init__(self, host: str, port: int = 8060):
        self.host = host
        self.port = port
        self.base_url = f"http://{host}:{port}"
        self._session: aiohttp.ClientSession | None = None
    
    async def connect(self) -> bool:
        """Test connection to Roku."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/query/device-info", timeout=5) as resp:
                    return resp.status == 200
        except Exception as e:
            _LOGGER.error(f"Failed to connect to Roku: {e}")
            return False
    
    async def send_command(self, command: str) -> bool:
        """Send a keypress command to Roku."""
        command = command.lower().replace("_", "").replace("-", "")
        
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/keypress/{command}"
                async with session.post(url, timeout=5) as resp:
                    return resp.status == 200
        except Exception as e:
            _LOGGER.error(f"Failed to send Roku command: {e}")
            return False
    
    async def launch_app(self, app_id: str) -> bool:
        """Launch an app by ID."""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/launch/{app_id}"
                async with session.post(url, timeout=10) as resp:
                    return resp.status == 200
        except Exception as e:
            _LOGGER.error(f"Failed to launch Roku app: {e}")
            return False
    
    async def launch_app_with_content(self, app_id: str, content_id: str = "", media_type: str = "") -> bool:
        """Launch an app with specific content (e.g., a movie or show)."""
        try:
            params = {}
            if content_id:
                params["contentId"] = content_id
            if media_type:
                params["mediaType"] = media_type
            
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/launch/{app_id}"
                async with session.post(url, params=params, timeout=10) as resp:
                    return resp.status == 200
        except Exception as e:
            _LOGGER.error(f"Failed to launch Roku app with content: {e}")
            return False
    
    async def search(self, keyword: str, search_type: str = "movie") -> bool:
        """Search for content."""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/search/browse"
                params = {"keyword": keyword, "type": search_type}
                async with session.post(url, params=params, timeout=10) as resp:
                    return resp.status == 200
        except Exception as e:
            _LOGGER.error(f"Failed to search on Roku: {e}")
            return False
    
    async def input_text(self, text: str) -> bool:
        """Send text input (types characters one by one)."""
        try:
            async with aiohttp.ClientSession() as session:
                for char in text:
                    url = f"{self.base_url}/keypress/Lit_{char}"
                    async with session.post(url, timeout=2) as resp:
                        if resp.status != 200:
                            return False
                    await asyncio.sleep(0.1)
                return True
        except Exception as e:
            _LOGGER.error(f"Failed to input text on Roku: {e}")
            return False
    
    async def get_state(self) -> dict[str, Any]:
        """Get device info and current state."""
        try:
            async with aiohttp.ClientSession() as session:
                # Device info
                async with session.get(f"{self.base_url}/query/device-info", timeout=5) as resp:
                    if resp.status != 200:
                        return {}
                    device_info = await resp.text()
                
                # Active app
                async with session.get(f"{self.base_url}/query/active-app", timeout=5) as resp:
                    active_app = await resp.text() if resp.status == 200 else ""
                
                # TV channels (if Roku TV)
                channels = []
                try:
                    async with session.get(f"{self.base_url}/query/tv-channels", timeout=5) as resp:
                        if resp.status == 200:
                            channels_data = await resp.text()
                            # Parse channels...
                except:
                    pass
                
                return {
                    "device_info": device_info,
                    "active_app": active_app,
                    "channels": channels,
                }
        except Exception as e:
            _LOGGER.error(f"Failed to get Roku state: {e}")
            return {}
    
    async def get_apps(self) -> list[dict]:
        """Get list of installed apps."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/query/apps", timeout=5) as resp:
                    if resp.status != 200:
                        return []
                    
                    from xml.etree import ElementTree
                    text = await resp.text()
                    root = ElementTree.fromstring(text)
                    
                    apps = []
                    for app in root.findall("app"):
                        apps.append({
                            "id": app.get("id"),
                            "name": app.text,
                            "type": app.get("type"),
                            "version": app.get("version"),
                        })
                    return apps
        except Exception as e:
            _LOGGER.error(f"Failed to get Roku apps: {e}")
            return []
    
    async def get_tv_channels(self) -> list[dict]:
        """Get list of TV channels (Roku TV only)."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/query/tv-channels", timeout=5) as resp:
                    if resp.status != 200:
                        return []
                    
                    from xml.etree import ElementTree
                    text = await resp.text()
                    root = ElementTree.fromstring(text)
                    
                    channels = []
                    for channel in root.findall("channel"):
                        channels.append({
                            "number": channel.findtext("number"),
                            "name": channel.findtext("name"),
                            "type": channel.findtext("type"),
                            "user_hidden": channel.findtext("user-hidden") == "true",
                        })
                    return channels
        except Exception as e:
            _LOGGER.error(f"Failed to get Roku TV channels: {e}")
            return []
    
    async def tune_channel(self, channel_number: str) -> bool:
        """Tune to a specific TV channel (Roku TV only)."""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/tv/tune"
                params = {"channel-number": channel_number}
                async with session.post(url, params=params, timeout=10) as resp:
                    return resp.status == 200
        except Exception as e:
            _LOGGER.error(f"Failed to tune Roku channel: {e}")
            return False


# =============================================================================
# AMAZON FIRE TV (ADB)
# =============================================================================

class FireTVController(NetworkController):
    """Controller for Fire TV using ADB over network."""
    
    # Common key codes
    KEYCODES = {
        "home": 3,
        "back": 4,
        "up": 19,
        "down": 20,
        "left": 21,
        "right": 22,
        "select": 23,
        "ok": 23,
        "enter": 66,
        "play_pause": 85,
        "play": 126,
        "pause": 127,
        "stop": 86,
        "rewind": 89,
        "fast_forward": 90,
        "skip_forward": 87,
        "skip_back": 88,
        "menu": 82,
        "volume_up": 24,
        "volume_down": 25,
        "mute": 164,
        "power": 26,
        "sleep": 223,
        "wakeup": 224,
    }
    
    def __init__(self, host: str, port: int = 5555):
        self.host = host
        self.port = port
        self._connected = False
    
    async def connect(self) -> bool:
        """Connect to Fire TV via ADB."""
        try:
            # Try to import adb_shell
            from adb_shell.adb_device import AdbDeviceTcp
            from adb_shell.auth.sign_pythonrsa import PythonRSASigner
            
            self._device = AdbDeviceTcp(self.host, self.port, default_transport_timeout_s=9.)
            self._device.connect()
            self._connected = True
            return True
        except ImportError:
            _LOGGER.warning("adb_shell not installed, using HTTP fallback")
            self._connected = False
            return False
        except Exception as e:
            _LOGGER.error(f"Failed to connect to Fire TV: {e}")
            self._connected = False
            return False
    
    async def send_command(self, command: str) -> bool:
        """Send a key command to Fire TV."""
        command = command.lower().replace("-", "_")
        
        if command not in self.KEYCODES:
            _LOGGER.warning(f"Unknown Fire TV command: {command}")
            return False
        
        keycode = self.KEYCODES[command]
        return await self._send_keyevent(keycode)
    
    async def _send_keyevent(self, keycode: int) -> bool:
        """Send a key event via ADB."""
        try:
            if self._connected and hasattr(self, '_device'):
                await asyncio.to_thread(
                    self._device.shell, f"input keyevent {keycode}"
                )
                return True
            return False
        except Exception as e:
            _LOGGER.error(f"Failed to send Fire TV keyevent: {e}")
            return False
    
    async def launch_app(self, package: str, activity: str = "") -> bool:
        """Launch an app by package name."""
        try:
            if not self._connected:
                return False
            
            if activity:
                cmd = f"am start -n {package}/{activity}"
            else:
                cmd = f"monkey -p {package} -c android.intent.category.LAUNCHER 1"
            
            await asyncio.to_thread(self._device.shell, cmd)
            return True
        except Exception as e:
            _LOGGER.error(f"Failed to launch Fire TV app: {e}")
            return False
    
    async def get_state(self) -> dict[str, Any]:
        """Get current state of Fire TV."""
        try:
            if not self._connected:
                return {"state": "disconnected"}
            
            # Get current app
            current_app = await asyncio.to_thread(
                self._device.shell, 
                "dumpsys window windows | grep -E 'mCurrentFocus|mFocusedApp'"
            )
            
            # Get wake state
            wake_state = await asyncio.to_thread(
                self._device.shell,
                "dumpsys power | grep 'Display Power'"
            )
            
            return {
                "state": "on" if "Display Power: state=ON" in wake_state else "standby",
                "current_app": current_app,
            }
        except Exception as e:
            _LOGGER.error(f"Failed to get Fire TV state: {e}")
            return {"state": "unknown"}
    
    async def get_installed_apps(self) -> list[str]:
        """Get list of installed apps."""
        try:
            if not self._connected:
                return []
            
            output = await asyncio.to_thread(
                self._device.shell,
                "pm list packages -3"
            )
            
            packages = []
            for line in output.split("\n"):
                if line.startswith("package:"):
                    packages.append(line.replace("package:", "").strip())
            
            return packages
        except Exception as e:
            _LOGGER.error(f"Failed to get Fire TV apps: {e}")
            return []
    
    async def input_text(self, text: str) -> bool:
        """Input text."""
        try:
            if not self._connected:
                return False
            
            # Escape special characters
            escaped = text.replace(" ", "%s").replace("'", "\\'").replace('"', '\\"')
            await asyncio.to_thread(
                self._device.shell,
                f"input text '{escaped}'"
            )
            return True
        except Exception as e:
            _LOGGER.error(f"Failed to input text on Fire TV: {e}")
            return False
    
    async def open_url(self, url: str) -> bool:
        """Open a URL in the browser."""
        try:
            if not self._connected:
                return False
            
            await asyncio.to_thread(
                self._device.shell,
                f"am start -a android.intent.action.VIEW -d '{url}'"
            )
            return True
        except Exception as e:
            _LOGGER.error(f"Failed to open URL on Fire TV: {e}")
            return False


# =============================================================================
# ONKYO/INTEGRA eISCP
# =============================================================================

class OnkyoController(NetworkController):
    """Controller for Onkyo/Integra receivers using eISCP."""
    
    # Common commands
    COMMANDS = {
        "power_on": "PWR01",
        "power_off": "PWR00",
        "power_query": "PWRQSTN",
        "mute_on": "AMT01",
        "mute_off": "AMT00",
        "mute_toggle": "AMTTG",
        "volume_up": "MVLUP",
        "volume_down": "MVLDOWN",
        "volume_query": "MVLQSTN",
        "input_bd_dvd": "SLI10",
        "input_cbl_sat": "SLI01",
        "input_game": "SLI02",
        "input_aux": "SLI03",
        "input_pc": "SLI05",
        "input_tv": "SLI12",
        "input_strm_box": "SLI11",
        "input_bluetooth": "SLI2E",
        "input_net": "SLI2B",
        "input_usb": "SLI29",
        "input_query": "SLIQSTN",
        "listening_mode_stereo": "LMD00",
        "listening_mode_direct": "LMD01",
        "listening_mode_surround": "LMD80",
        "listening_mode_query": "LMDQSTN",
    }
    
    def __init__(self, host: str, port: int = 60128):
        self.host = host
        self.port = port
    
    async def connect(self) -> bool:
        """Test connection to Onkyo receiver."""
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(self.host, self.port),
                timeout=5
            )
            writer.close()
            await writer.wait_closed()
            return True
        except Exception as e:
            _LOGGER.error(f"Failed to connect to Onkyo: {e}")
            return False
    
    def _build_eiscp_message(self, command: str) -> bytes:
        """Build an eISCP message."""
        iscp_msg = f"!1{command}\r"
        msg_length = len(iscp_msg)
        
        # eISCP header
        header = b"ISCP"
        header += (16).to_bytes(4, 'big')  # Header size
        header += msg_length.to_bytes(4, 'big')  # Data size
        header += b"\x01"  # Version
        header += b"\x00\x00\x00"  # Reserved
        
        return header + iscp_msg.encode()
    
    async def send_command(self, command: str) -> bool:
        """Send a command to the Onkyo receiver."""
        command = command.lower().replace("-", "_")
        
        if command in self.COMMANDS:
            eiscp_cmd = self.COMMANDS[command]
        else:
            eiscp_cmd = command.upper()
        
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(self.host, self.port),
                timeout=5
            )
            
            message = self._build_eiscp_message(eiscp_cmd)
            writer.write(message)
            await writer.drain()
            
            # Read response
            response = await asyncio.wait_for(reader.read(1024), timeout=2)
            
            writer.close()
            await writer.wait_closed()
            
            return True
        except Exception as e:
            _LOGGER.error(f"Failed to send Onkyo command: {e}")
            return False
    
    async def set_volume(self, level: int) -> bool:
        """Set volume level (0-80)."""
        level = max(0, min(80, level))
        return await self.send_command(f"MVL{level:02X}")
    
    async def get_state(self) -> dict[str, Any]:
        """Get current state."""
        # Query multiple states
        state = {}
        
        try:
            # Power
            await self.send_command("power_query")
            # Volume
            await self.send_command("volume_query")
            # Input
            await self.send_command("input_query")
            
            return state
        except Exception as e:
            _LOGGER.error(f"Failed to get Onkyo state: {e}")
            return {}


# =============================================================================
# SHELLY HTTP CONTROLLER
# =============================================================================

class ShellyController(NetworkController):
    """Controller for Shelly devices via HTTP."""
    
    def __init__(self, host: str, port: int = 80):
        self.host = host
        self.port = port
        self.base_url = f"http://{host}"
    
    async def connect(self) -> bool:
        """Test connection to Shelly device."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/shelly", timeout=5) as resp:
                    return resp.status == 200
        except Exception as e:
            _LOGGER.error(f"Failed to connect to Shelly: {e}")
            return False
    
    async def send_command(self, command: str) -> bool:
        """Send a command to the Shelly device."""
        endpoints = {
            "open": "/roller/0?go=open",
            "close": "/roller/0?go=close",
            "stop": "/roller/0?go=stop",
            "on": "/relay/0?turn=on",
            "off": "/relay/0?turn=off",
            "toggle": "/relay/0?turn=toggle",
        }
        
        endpoint = endpoints.get(command.lower())
        if not endpoint:
            _LOGGER.warning(f"Unknown Shelly command: {command}")
            return False
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}{endpoint}", timeout=5) as resp:
                    return resp.status == 200
        except Exception as e:
            _LOGGER.error(f"Failed to send Shelly command: {e}")
            return False
    
    async def set_position(self, position: int) -> bool:
        """Set roller position (0-100)."""
        position = max(0, min(100, position))
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/roller/0?go=to_pos&roller_pos={position}"
                async with session.get(url, timeout=5) as resp:
                    return resp.status == 200
        except Exception as e:
            _LOGGER.error(f"Failed to set Shelly position: {e}")
            return False
    
    async def get_state(self) -> dict[str, Any]:
        """Get current state."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/status", timeout=5) as resp:
                    if resp.status == 200:
                        return await resp.json()
                    return {}
        except Exception as e:
            _LOGGER.error(f"Failed to get Shelly state: {e}")
            return {}


# =============================================================================
# BENQ PROJECTOR RS232-over-IP
# =============================================================================

class BenQProjectorController(NetworkController):
    """Controller for BenQ projectors using RS232-over-IP."""
    
    COMMANDS = {
        "power_on": "*pow=on#",
        "power_off": "*pow=off#",
        "power_query": "*pow=?#",
        "source_hdmi1": "*sour=hdmi#",
        "source_hdmi2": "*sour=hdmi2#",
        "source_vga": "*sour=rgb#",
        "source_component": "*sour=ypbr#",
        "source_video": "*sour=vid#",
        "source_query": "*sour=?#",
        "mute_on": "*mute=on#",
        "mute_off": "*mute=off#",
        "blank_on": "*blank=on#",
        "blank_off": "*blank=off#",
        "vol_up": "*vol=+#",
        "vol_down": "*vol=-#",
        "lamp_hours": "*ltim=?#",
        "model": "*modelname=?#",
        "aspect_auto": "*asp=auto#",
        "aspect_4_3": "*asp=4:3#",
        "aspect_16_9": "*asp=16:9#",
        "keystone_up": "*ksd=1#",
        "keystone_down": "*ksd=0#",
        "picture_mode_bright": "*appmod=bright#",
        "picture_mode_cinema": "*appmod=cine#",
        "picture_mode_game": "*appmod=game#",
        "picture_mode_user": "*appmod=user#",
        "3d_on": "*3d=on#",
        "3d_off": "*3d=off#",
        "eco_mode_on": "*lampm=eco#",
        "eco_mode_off": "*lampm=normal#",
    }
    
    def __init__(self, host: str, port: int = 8000):
        self.host = host
        self.port = port
    
    async def connect(self) -> bool:
        """Test connection to projector."""
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(self.host, self.port),
                timeout=5
            )
            writer.close()
            await writer.wait_closed()
            return True
        except Exception as e:
            _LOGGER.error(f"Failed to connect to BenQ projector: {e}")
            return False
    
    async def send_command(self, command: str) -> bool:
        """Send a command to the projector."""
        command = command.lower().replace("-", "_")
        
        if command in self.COMMANDS:
            cmd = self.COMMANDS[command]
        else:
            cmd = f"*{command}#"
        
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(self.host, self.port),
                timeout=5
            )
            
            writer.write((cmd + "\r").encode())
            await writer.drain()
            
            # Read response
            response = await asyncio.wait_for(reader.readline(), timeout=2)
            
            writer.close()
            await writer.wait_closed()
            
            return b"*" in response  # BenQ responds with *cmd=value#
        except Exception as e:
            _LOGGER.error(f"Failed to send BenQ command: {e}")
            return False
    
    async def get_lamp_hours(self) -> int | None:
        """Get lamp hours."""
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(self.host, self.port),
                timeout=5
            )
            
            writer.write(b"*ltim=?#\r")
            await writer.drain()
            
            response = await asyncio.wait_for(reader.readline(), timeout=2)
            
            writer.close()
            await writer.wait_closed()
            
            # Parse response like "*ltim=1234#"
            if b"*ltim=" in response:
                hours_str = response.decode().split("=")[1].split("#")[0]
                return int(hours_str)
            return None
        except Exception as e:
            _LOGGER.error(f"Failed to get BenQ lamp hours: {e}")
            return None
    
    async def get_state(self) -> dict[str, Any]:
        """Get projector state."""
        state = {}
        
        try:
            # Power state
            # ... (would need to send query and parse response)
            
            # Lamp hours
            lamp_hours = await self.get_lamp_hours()
            if lamp_hours is not None:
                state["lamp_hours"] = lamp_hours
            
            return state
        except Exception as e:
            _LOGGER.error(f"Failed to get BenQ state: {e}")
            return {}


# =============================================================================
# DISCOVERY
# =============================================================================

async def discover_roku_devices(timeout: float = 5.0) -> list[NetworkDevice]:
    """Discover Roku devices on the network using SSDP."""
    devices = []
    
    ssdp_request = (
        "M-SEARCH * HTTP/1.1\r\n"
        "HOST: 239.255.255.250:1900\r\n"
        "MAN: \"ssdp:discover\"\r\n"
        "MX: 2\r\n"
        "ST: roku:ecp\r\n"
        "\r\n"
    )
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.settimeout(timeout)
        
        sock.sendto(ssdp_request.encode(), ("239.255.255.250", 1900))
        
        while True:
            try:
                data, addr = sock.recvfrom(1024)
                response = data.decode()
                
                if "roku" in response.lower():
                    # Parse location
                    for line in response.split("\r\n"):
                        if line.lower().startswith("location:"):
                            location = line.split(":", 1)[1].strip()
                            # Extract host from URL
                            host = location.split("//")[1].split(":")[0]
                            
                            devices.append(NetworkDevice(
                                host=host,
                                port=8060,
                                name="Roku",
                                device_type="roku",
                            ))
                            break
            except socket.timeout:
                break
        
        sock.close()
    except Exception as e:
        _LOGGER.error(f"Roku discovery failed: {e}")
    
    return devices


# =============================================================================
# CONTROLLER FACTORY
# =============================================================================

def get_controller(device_type: str, host: str, port: int = None) -> NetworkController | None:
    """Get the appropriate controller for a device type."""
    controllers = {
        "roku_ecp": (RokuController, 8060),
        "android_tv_adb": (FireTVController, 5555),
        "onkyo_eiscp": (OnkyoController, 60128),
        "shelly_http": (ShellyController, 80),
        "benq_rs232_over_ip": (BenQProjectorController, 8000),
    }
    
    if device_type not in controllers:
        return None
    
    controller_class, default_port = controllers[device_type]
    return controller_class(host, port or default_port)
