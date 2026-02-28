"""Flipper Zero integration for OmniRemote.

Connects to Flipper Zero via USB Serial or Bluetooth LE for:
- Sending IR commands
- Learning IR codes
- Listing stored IR files

Flipper Zero CLI Commands:
- ir tx <protocol> <address> <command>  - Transmit IR
- ir rx                                   - Start IR receiver
- storage list /ext/infrared             - List IR files
- storage read /ext/infrared/file.ir     - Read IR file
"""

from __future__ import annotations

import asyncio
import logging
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

from .const import DEBUG

_LOGGER = logging.getLogger(__name__)

def _debug(msg: str, *args) -> None:
    """Log debug message if DEBUG is enabled."""
    if DEBUG:
        _LOGGER.info("[Flipper DEBUG] " + msg, *args)


class FlipperConnectionType(Enum):
    """Connection type for Flipper Zero."""
    USB = "usb"
    BLUETOOTH = "bluetooth"
    

class FlipperProtocol(Enum):
    """IR protocols supported by Flipper Zero."""
    # These match Flipper's internal protocol names
    SAMSUNG32 = "Samsung32"
    NEC = "NEC"
    NECEXT = "NECext"
    NEC42 = "NEC42"
    NEC42EXT = "NEC42ext"
    SONY_SIRC = "SIRC"
    SONY_SIRC15 = "SIRC15"
    SONY_SIRC20 = "SIRC20"
    RC5 = "RC5"
    RC5X = "RC5X"
    RC6 = "RC6"
    KASEIKYO = "Kaseikyo"  # Panasonic
    RCA = "RCA"
    PIONEER = "Pioneer"
    RAW = "RAW"


# Map OmniRemote protocols to Flipper protocols
PROTOCOL_MAP = {
    "samsung32": "Samsung32",
    "nec": "NEC",
    "nec_ext": "NECext",
    "sony": "SIRC",
    "rc5": "RC5",
    "rc6": "RC6",
    "panasonic": "Kaseikyo",
    "jvc": "NEC",  # JVC uses NEC-like encoding
}


@dataclass
class FlipperDevice:
    """Represents a connected Flipper Zero device."""
    id: str
    name: str
    connection_type: FlipperConnectionType
    port: str  # USB port path or BLE address
    connected: bool = False
    firmware_version: str = ""
    _connection: object = None
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "connection_type": self.connection_type.value,
            "port": self.port,
            "connected": self.connected,
            "firmware_version": self.firmware_version,
        }


class FlipperZeroManager:
    """Manages Flipper Zero connections."""
    
    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass
        self.devices: dict[str, FlipperDevice] = {}
        self._discovery_task: asyncio.Task | None = None
        self._learn_callback: Callable | None = None
        self._learn_task: asyncio.Task | None = None
    
    async def async_discover_usb(self) -> list[dict]:
        """Discover Flipper Zero devices on USB ports."""
        devices = []
        
        try:
            import serial.tools.list_ports
            
            _LOGGER.info("Scanning USB ports for Flipper Zero...")
            
            ports = await self.hass.async_add_executor_job(
                serial.tools.list_ports.comports
            )
            
            _LOGGER.debug("Found %d USB ports total", len(ports))
            
            for port in ports:
                _LOGGER.debug("USB Port: %s, VID=%s, PID=%s, Desc=%s", 
                             port.device, 
                             hex(port.vid) if port.vid else None,
                             hex(port.pid) if port.pid else None,
                             port.description)
                
                # Flipper Zero USB identifiers
                # VID: 0x0483 (STMicroelectronics)
                # PID: 0x5740 (Virtual COM Port)
                if port.vid == 0x0483 and port.pid == 0x5740:
                    device_id = f"flipper_usb_{port.device.replace('/', '_')}"
                    devices.append({
                        "id": device_id,
                        "name": f"Flipper Zero ({port.device})",
                        "connection_type": "usb",
                        "port": port.device,
                        "description": port.description or "Flipper Zero",
                    })
                    _LOGGER.info("Found Flipper Zero on USB: %s", port.device)
                    
                # Also check description for "Flipper"
                elif port.description and "flipper" in port.description.lower():
                    device_id = f"flipper_usb_{port.device.replace('/', '_')}"
                    devices.append({
                        "id": device_id,
                        "name": f"Flipper Zero ({port.device})",
                        "connection_type": "usb",
                        "port": port.device,
                        "description": port.description,
                    })
                    _LOGGER.info("Found Flipper Zero on USB (by name): %s", port.device)
            
            if not devices:
                _LOGGER.info("No Flipper Zero found on USB ports")
                    
        except ImportError:
            _LOGGER.warning("pyserial not installed, USB discovery unavailable")
        except Exception as ex:
            _LOGGER.error("Error discovering USB devices: %s", ex)
        
        return devices
    
    async def async_discover_bluetooth(self) -> list[dict]:
        """Discover Flipper Zero devices via Bluetooth."""
        devices = []
        
        _debug("Starting Flipper Zero Bluetooth discovery...")
        _LOGGER.info("[OmniRemote] Starting Flipper Zero Bluetooth discovery...")
        
        # First try using HA's Bluetooth integration (preferred on HA Yellow)
        try:
            from homeassistant.components import bluetooth
            
            _debug("Using HA Bluetooth integration for discovery...")
            
            # Get all discovered BLE devices from HA
            discovered = bluetooth.async_discovered_service_info(self.hass)
            discovered_list = list(discovered)
            
            _debug("HA Bluetooth found %d total devices", len(discovered_list))
            _LOGGER.info("[OmniRemote] HA Bluetooth found %d BLE devices", len(discovered_list))
            
            # Log all discovered device names for debugging
            for service_info in discovered_list:
                name = service_info.name or ""
                if hasattr(service_info, 'advertisement') and service_info.advertisement:
                    name = name or service_info.advertisement.local_name or ""
                
                # Log device with Flipper-like names or unknown names
                if name:
                    _LOGGER.debug("BLE device: %s (%s) RSSI=%s", 
                                 name, service_info.address, service_info.rssi)
                    
                if name.startswith("Flipper"):
                    device_id = f"flipper_ble_{service_info.address.replace(':', '_')}"
                    devices.append({
                        "id": device_id,
                        "name": name,
                        "connection_type": "bluetooth",
                        "port": service_info.address,
                        "rssi": service_info.rssi,
                    })
                    _LOGGER.info("Found Flipper Zero via HA BLE: %s (%s)", 
                                name, service_info.address)
            
            if devices:
                return devices
            
            _LOGGER.info("No Flipper found in HA discovered devices (%d total). "
                        "Make sure Flipper Bluetooth is ON and device is discoverable.", 
                        len(discovered_list))
                    
        except ImportError:
            _LOGGER.warning("HA Bluetooth integration not available")
        except Exception as ex:
            _LOGGER.warning("HA Bluetooth discovery error: %s", ex)
        
        # Fallback to direct BleakScanner
        try:
            from bleak import BleakScanner
            
            _LOGGER.info("Fallback: Scanning with BleakScanner (10 second timeout)...")
            
            discovered = await BleakScanner.discover(timeout=10.0)
            
            _LOGGER.info("BleakScanner found %d devices", len(discovered))
            
            for device in discovered:
                if device.name:
                    _LOGGER.debug("BleakScanner device: %s (%s)", device.name, device.address)
                
                # Flipper Zero advertises as "Flipper <name>"
                if device.name and device.name.startswith("Flipper"):
                    device_id = f"flipper_ble_{device.address.replace(':', '_')}"
                    devices.append({
                        "id": device_id,
                        "name": device.name,
                        "connection_type": "bluetooth",
                        "port": device.address,
                        "rssi": device.rssi if hasattr(device, 'rssi') else None,
                    })
                    _LOGGER.info("Found Flipper Zero via BleakScanner: %s (%s)", 
                                device.name, device.address)
            
            if not devices:
                _LOGGER.warning("No Flipper Zero found via Bluetooth. "
                               "Ensure on Flipper: Settings > Bluetooth > ON, "
                               "and Flipper is NOT connected to qFlipper or phone app.")
                    
        except ImportError:
            _LOGGER.error("bleak not installed - Bluetooth discovery unavailable")
        except Exception as ex:
            _LOGGER.error("BleakScanner error: %s", ex)
        
        return devices
        

    async def async_discover_all(self) -> list[dict]:
        """Discover all Flipper Zero devices."""
        usb_devices = await self.async_discover_usb()
        ble_devices = await self.async_discover_bluetooth()
        return usb_devices + ble_devices
    
    async def async_connect_usb(self, device: FlipperDevice) -> bool:
        """Connect to Flipper Zero via USB serial."""
        try:
            import serial
            import serial_asyncio
            
            _LOGGER.info("Connecting to Flipper Zero USB: %s", device.port)
            
            # Open serial connection
            # Flipper uses 115200 baud, but CDC doesn't really care
            reader, writer = await serial_asyncio.open_serial_connection(
                url=device.port,
                baudrate=115200,
            )
            
            device._connection = (reader, writer)
            
            # Clear any pending data
            await asyncio.sleep(0.1)
            
            # Send a command to verify connection
            writer.write(b"\r\n")
            await writer.drain()
            await asyncio.sleep(0.1)
            
            # Try to get device info
            writer.write(b"device_info\r\n")
            await writer.drain()
            
            # Read response with timeout
            try:
                response = await asyncio.wait_for(
                    reader.read(1024),
                    timeout=2.0
                )
                response_text = response.decode('utf-8', errors='ignore')
                
                # Parse firmware version
                if "firmware" in response_text.lower():
                    match = re.search(r'firmware[:\s]+(\S+)', response_text, re.I)
                    if match:
                        device.firmware_version = match.group(1)
                
                device.connected = True
                _LOGGER.info("Connected to Flipper Zero USB: %s (FW: %s)", 
                            device.name, device.firmware_version)
                return True
                
            except asyncio.TimeoutError:
                # Connection works but no response - still usable
                device.connected = True
                _LOGGER.info("Connected to Flipper Zero USB: %s (no version response)", 
                            device.name)
                return True
                
        except ImportError:
            _LOGGER.error("pyserial-asyncio not installed")
            return False
        except Exception as ex:
            _LOGGER.error("Failed to connect to Flipper USB %s: %s", device.port, ex)
            return False
    
    async def async_connect_bluetooth(self, device: FlipperDevice) -> bool:
        """Connect to Flipper Zero via Bluetooth LE Serial.
        
        IMPORTANT: Flipper Zero BLE Serial has specific requirements:
        1. On Flipper: Settings > Bluetooth > Enable
        2. On Flipper: Settings > Bluetooth > RPC over Bluetooth > Enable  
        3. Flipper must NOT be connected to another device
        
        USB connection is more reliable - recommend USB if available.
        """
        _debug("async_connect_bluetooth called for device: %s (%s)", device.name, device.port)
        _LOGGER.info("[OmniRemote] Connecting to Flipper Zero Bluetooth: %s at %s", device.name, device.port)
        
        try:
            from bleak import BleakClient
            from bleak.exc import BleakError
        except ImportError:
            _LOGGER.error("[OmniRemote] bleak not installed - run: pip install bleak")
            return False
        
        # Flipper's BLE Serial service UUID (Nordic UART Service compatible)
        FLIPPER_SERIAL_SERVICE = "8fe5b3d5-2e7f-4a98-2a48-7acc60fe0000"
        FLIPPER_RX_CHAR = "19ed82ae-ed21-4c9d-4145-228e62fe0000"  # Write to Flipper
        FLIPPER_TX_CHAR = "19ed82ae-ed21-4c9d-4145-228e61fe0000"  # Read from Flipper
        
        client = None
        connection_method = "unknown"
        
        # Method 1: Try to use HA's bluetooth integration with bleak-retry-connector
        try:
            from bleak_retry_connector import establish_connection
            from homeassistant.components.bluetooth import async_ble_device_from_address
            
            _debug("Trying HA Bluetooth integration...")
            _LOGGER.info("[OmniRemote] Looking up device in HA Bluetooth cache...")
            
            # NOTE: async_ble_device_from_address is NOT async despite the name
            ble_device = async_ble_device_from_address(
                self.hass, device.port, connectable=True
            )
            
            if ble_device:
                _debug("Found BLE device in HA: %s", ble_device)
                _LOGGER.info("[OmniRemote] Found device in HA cache, connecting via bleak-retry-connector...")
                
                try:
                    client = await establish_connection(
                        BleakClient,
                        ble_device,
                        device.name,
                        max_attempts=3,
                    )
                    connection_method = "bleak-retry-connector"
                    _LOGGER.info("[OmniRemote] Connected via bleak-retry-connector!")
                except Exception as retry_ex:
                    error_str = str(retry_ex)
                    _debug("bleak-retry-connector failed: %s", retry_ex)
                    
                    # Check for connection slot exhaustion
                    if "connection slot" in error_str.lower() or "out of connection" in error_str.lower():
                        _LOGGER.error("[OmniRemote] Bluetooth adapter out of connection slots!")
                        _LOGGER.error("[OmniRemote] Your HA Bluetooth adapter has reached its connection limit (typically 3-7 devices)")
                        _LOGGER.error("[OmniRemote] Solutions:")
                        _LOGGER.error("[OmniRemote]   1. Disconnect other Bluetooth devices from HA")
                        _LOGGER.error("[OmniRemote]   2. Use USB connection instead (more reliable)")
                        _LOGGER.error("[OmniRemote]   3. Add ESPHome Bluetooth Proxy: https://esphome.github.io/bluetooth-proxies/")
                        # Return False immediately - no point trying direct connection
                        return False
                    
                    _LOGGER.warning("[OmniRemote] bleak-retry-connector failed: %s", retry_ex)
                    client = None
            else:
                _debug("Device not in HA Bluetooth cache")
                _LOGGER.info("[OmniRemote] Device not found in HA Bluetooth cache")
                
        except ImportError as ie:
            _debug("bleak-retry-connector not available: %s", ie)
            _LOGGER.debug("[OmniRemote] bleak-retry-connector not available")
        except Exception as ex:
            error_str = str(ex)
            _debug("HA Bluetooth lookup error: %s", ex)
            
            # Also check here for slot errors
            if "connection slot" in error_str.lower() or "out of connection" in error_str.lower():
                _LOGGER.error("[OmniRemote] Bluetooth adapter out of connection slots!")
                _LOGGER.error("[OmniRemote] Disconnect other Bluetooth devices or use USB")
                return False
                
            _LOGGER.warning("[OmniRemote] HA Bluetooth lookup error: %s", ex)
        
        # Method 2: Direct BleakClient connection
        if client is None or not client.is_connected:
            _debug("Trying direct BleakClient connection to %s", device.port)
            _LOGGER.info("[OmniRemote] Attempting direct BLE connection to %s (20s timeout)...", device.port)
            
            try:
                client = BleakClient(device.port, timeout=20.0)
                await client.connect()
                connection_method = "direct-bleak"
                _LOGGER.info("[OmniRemote] Connected via direct BleakClient!")
            except BleakError as ble_ex:
                error_str = str(ble_ex)
                _LOGGER.error("[OmniRemote] BLE connection error: %s", error_str)
                
                # Provide specific troubleshooting based on error
                if "not found" in error_str.lower():
                    _LOGGER.error("[OmniRemote] Device not found - make sure Flipper Bluetooth is ON and not connected elsewhere")
                elif "timeout" in error_str.lower():
                    _LOGGER.error("[OmniRemote] Connection timed out - Flipper may need RPC over Bluetooth enabled")
                elif "refused" in error_str.lower() or "rejected" in error_str.lower():
                    _LOGGER.error("[OmniRemote] Connection refused - try restarting Bluetooth on Flipper")
                
                return False
            except Exception as conn_ex:
                _LOGGER.error("[OmniRemote] Connection failed: %s", conn_ex)
                _LOGGER.error("[OmniRemote] Troubleshooting:")
                _LOGGER.error("[OmniRemote]   1. Flipper: Settings > Bluetooth > ON")
                _LOGGER.error("[OmniRemote]   2. Flipper: Settings > Bluetooth > RPC over Bluetooth > ON")
                _LOGGER.error("[OmniRemote]   3. Disconnect Flipper from phone/qFlipper")
                _LOGGER.error("[OmniRemote]   4. Consider USB connection (more reliable)")
                return False
        
        # Verify connection
        if not client or not client.is_connected:
            _LOGGER.error("[OmniRemote] Failed to establish BLE connection")
            return False
        
        _debug("Connection established via %s, checking services...", connection_method)
        
        # Verify Flipper serial service is available
        try:
            services = client.services
            serial_found = False
            service_list = []
            
            for service in services:
                service_list.append(service.uuid)
                if "fe00" in service.uuid.lower() or "8fe5b3d5" in service.uuid.lower():
                    serial_found = True
            
            _debug("Available services: %s", service_list)
            
            if serial_found:
                _LOGGER.info("[OmniRemote] Found Flipper Serial service - connection ready!")
            else:
                _LOGGER.warning("[OmniRemote] Flipper Serial service not found!")
                _LOGGER.warning("[OmniRemote] Available services: %s", service_list)
                _LOGGER.warning("[OmniRemote] Enable: Flipper > Settings > Bluetooth > RPC over Bluetooth")
                # Don't fail - some operations might still work
                
        except Exception as svc_ex:
            _debug("Could not enumerate services: %s", svc_ex)
            _LOGGER.warning("[OmniRemote] Could not enumerate BLE services: %s", svc_ex)
        
        device._connection = client
        device.connected = True
        
        _LOGGER.info("[OmniRemote] ✓ Connected to Flipper Zero '%s' via %s", device.name, connection_method)
        return True
    
    async def async_connect(self, device_id: str) -> bool:
        """Connect to a Flipper Zero device."""
        device = self.devices.get(device_id)
        if not device:
            _LOGGER.error("Flipper device not found: %s", device_id)
            return False
        
        if device.connection_type == FlipperConnectionType.USB:
            return await self.async_connect_usb(device)
        elif device.connection_type == FlipperConnectionType.BLUETOOTH:
            return await self.async_connect_bluetooth(device)
        
        return False
    
    async def async_disconnect(self, device_id: str) -> None:
        """Disconnect from a Flipper Zero device."""
        device = self.devices.get(device_id)
        if not device or not device._connection:
            return
        
        try:
            if device.connection_type == FlipperConnectionType.USB:
                reader, writer = device._connection
                writer.close()
                await writer.wait_closed()
            elif device.connection_type == FlipperConnectionType.BLUETOOTH:
                await device._connection.disconnect()
            
            device._connection = None
            device.connected = False
            _LOGGER.info("Disconnected from Flipper: %s", device.name)
            
        except Exception as ex:
            _LOGGER.error("Error disconnecting from Flipper: %s", ex)
    
    async def async_send_command(self, device_id: str, command: str) -> str:
        """Send a CLI command to Flipper and return response."""
        device = self.devices.get(device_id)
        if not device or not device.connected:
            raise RuntimeError(f"Flipper not connected: {device_id}")
        
        async with device._lock:
            try:
                if device.connection_type == FlipperConnectionType.USB:
                    reader, writer = device._connection
                    
                    # Clear buffer
                    while reader._buffer:
                        reader._buffer.clear()
                    
                    # Send command
                    cmd_bytes = f"{command}\r\n".encode('utf-8')
                    writer.write(cmd_bytes)
                    await writer.drain()
                    
                    # Read response
                    await asyncio.sleep(0.1)
                    response = b""
                    try:
                        while True:
                            chunk = await asyncio.wait_for(reader.read(1024), timeout=0.5)
                            if not chunk:
                                break
                            response += chunk
                    except asyncio.TimeoutError:
                        pass
                    
                    return response.decode('utf-8', errors='ignore')
                    
                elif device.connection_type == FlipperConnectionType.BLUETOOTH:
                    # BLE Serial implementation
                    TX_CHAR_UUID = "00000002-0000-1000-8000-00805f9b34fb"
                    RX_CHAR_UUID = "00000003-0000-1000-8000-00805f9b34fb"
                    
                    client = device._connection
                    
                    # Send command
                    cmd_bytes = f"{command}\r\n".encode('utf-8')
                    await client.write_gatt_char(TX_CHAR_UUID, cmd_bytes)
                    
                    # Read response
                    await asyncio.sleep(0.2)
                    response = await client.read_gatt_char(RX_CHAR_UUID)
                    
                    return response.decode('utf-8', errors='ignore')
                    
            except Exception as ex:
                _LOGGER.error("Error sending command to Flipper: %s", ex)
                raise
    
    async def async_send_ir(
        self,
        device_id: str,
        protocol: str,
        address: str,
        command: str,
    ) -> bool:
        """Send an IR command via Flipper Zero.
        
        Args:
            device_id: Flipper device ID
            protocol: IR protocol (samsung32, nec, etc.)
            address: Device address (hex string)
            command: Command code (hex string)
        """
        # Map protocol name
        flipper_protocol = PROTOCOL_MAP.get(protocol.lower(), protocol)
        
        # Clean up address and command - remove spaces, ensure hex
        address = address.replace(" ", "").replace("0x", "")
        command = command.replace(" ", "").replace("0x", "")
        
        # Build Flipper IR TX command
        # Format: ir tx <protocol> <address> <command>
        # Address and command should be hex values without 0x prefix
        ir_command = f"ir tx {flipper_protocol} {address} {command}"
        
        _LOGGER.info("Flipper IR TX: %s", ir_command)
        
        try:
            response = await self.async_send_command(device_id, ir_command)
            _LOGGER.debug("Flipper response: %s", response)
            
            # Check for errors
            if "error" in response.lower():
                _LOGGER.error("Flipper IR TX error: %s", response)
                return False
            
            return True
            
        except Exception as ex:
            _LOGGER.error("Failed to send IR via Flipper: %s", ex)
            return False
    
    async def async_send_ir_raw(
        self,
        device_id: str,
        frequency: int,
        duty_cycle: float,
        timings: list[int],
    ) -> bool:
        """Send raw IR timings via Flipper Zero.
        
        Args:
            device_id: Flipper device ID
            frequency: Carrier frequency in Hz (e.g., 38000)
            duty_cycle: Duty cycle (0.0-1.0)
            timings: List of timing values in microseconds (mark, space, mark, space, ...)
        """
        # Flipper raw format: ir tx_raw <frequency> <duty_cycle> <timing1> <timing2> ...
        timings_str = " ".join(str(t) for t in timings)
        ir_command = f"ir tx_raw {frequency} {duty_cycle:.2f} {timings_str}"
        
        _LOGGER.info("Flipper IR TX RAW: freq=%d, timings=%d", frequency, len(timings))
        
        try:
            response = await self.async_send_command(device_id, ir_command)
            
            if "error" in response.lower():
                _LOGGER.error("Flipper IR TX RAW error: %s", response)
                return False
            
            return True
            
        except Exception as ex:
            _LOGGER.error("Failed to send raw IR via Flipper: %s", ex)
            return False
    
    async def async_start_learning(
        self,
        device_id: str,
        callback: Callable[[dict], None],
        timeout: float = 30.0,
    ) -> bool:
        """Start IR learning mode on Flipper Zero.
        
        Args:
            device_id: Flipper device ID
            callback: Function to call when a code is received
            timeout: How long to listen for codes
        """
        device = self.devices.get(device_id)
        if not device or not device.connected:
            return False
        
        self._learn_callback = callback
        
        async def learn_loop():
            try:
                # Start IR receiver
                await self.async_send_command(device_id, "ir rx")
                
                start_time = asyncio.get_event_loop().time()
                
                while asyncio.get_event_loop().time() - start_time < timeout:
                    if device.connection_type == FlipperConnectionType.USB:
                        reader, writer = device._connection
                        
                        try:
                            data = await asyncio.wait_for(reader.read(1024), timeout=1.0)
                            if data:
                                text = data.decode('utf-8', errors='ignore')
                                
                                # Parse received IR code
                                # Flipper outputs: protocol: <proto> address: <addr> command: <cmd>
                                match = re.search(
                                    r'protocol:\s*(\S+).*?address:\s*(\S+).*?command:\s*(\S+)',
                                    text, re.I | re.S
                                )
                                
                                if match and self._learn_callback:
                                    code = {
                                        "protocol": match.group(1),
                                        "address": match.group(2),
                                        "command": match.group(3),
                                        "raw": text,
                                    }
                                    self._learn_callback(code)
                                    
                        except asyncio.TimeoutError:
                            continue
                    else:
                        await asyncio.sleep(0.5)
                        
            except asyncio.CancelledError:
                pass
            except Exception as ex:
                _LOGGER.error("Learning error: %s", ex)
            finally:
                # Stop IR receiver
                try:
                    await self.async_send_command(device_id, "\x03")  # Ctrl+C
                except:
                    pass
        
        self._learn_task = asyncio.create_task(learn_loop())
        return True
    
    async def async_stop_learning(self) -> None:
        """Stop IR learning mode."""
        if self._learn_task:
            self._learn_task.cancel()
            try:
                await self._learn_task
            except asyncio.CancelledError:
                pass
            self._learn_task = None
        
        self._learn_callback = None
    
    async def async_list_ir_files(self, device_id: str) -> list[str]:
        """List IR files stored on Flipper Zero SD card."""
        try:
            response = await self.async_send_command(
                device_id, 
                "storage list /ext/infrared"
            )
            
            # Parse file listing
            files = []
            for line in response.split('\n'):
                line = line.strip()
                if line.endswith('.ir'):
                    # Extract filename
                    parts = line.split()
                    if parts:
                        files.append(parts[-1])
            
            return files
            
        except Exception as ex:
            _LOGGER.error("Failed to list IR files: %s", ex)
            return []
    
    async def async_read_ir_file(self, device_id: str, filename: str) -> str:
        """Read an IR file from Flipper Zero SD card."""
        try:
            response = await self.async_send_command(
                device_id,
                f"storage read /ext/infrared/{filename}"
            )
            return response
            
        except Exception as ex:
            _LOGGER.error("Failed to read IR file: %s", ex)
            return ""
    
    def add_device(
        self,
        device_id: str,
        name: str,
        connection_type: str,
        port: str,
    ) -> FlipperDevice:
        """Add a Flipper device to the manager."""
        conn_type = FlipperConnectionType(connection_type)
        device = FlipperDevice(
            id=device_id,
            name=name,
            connection_type=conn_type,
            port=port,
        )
        self.devices[device_id] = device
        return device
    
    def remove_device(self, device_id: str) -> None:
        """Remove a Flipper device."""
        if device_id in self.devices:
            del self.devices[device_id]
    
    def get_device(self, device_id: str) -> FlipperDevice | None:
        """Get a Flipper device by ID."""
        return self.devices.get(device_id)
    
    def list_devices(self) -> list[dict]:
        """List all Flipper devices."""
        return [d.to_dict() for d in self.devices.values()]
