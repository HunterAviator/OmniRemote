"""Parser for Flipper Zero .ir and .sub files."""
from __future__ import annotations

import base64
import logging
import re
import struct
from pathlib import Path
from typing import Any

from .const import CodeType, RemoteCode, Device, DeviceCategory

_LOGGER = logging.getLogger(__name__)


class FlipperParser:
    """Parse Flipper Zero IR and SubGHz files."""

    def __init__(self) -> None:
        """Initialize the parser."""
        self.devices: dict[str, Device] = {}

    def parse_directory(self, dir_path: str) -> dict[str, Device]:
        """Parse all Flipper files in a directory."""
        path = Path(dir_path)
        
        if not path.exists():
            _LOGGER.error("Directory not found: %s", dir_path)
            return {}
        
        # Parse .ir files
        for ir_file in path.rglob("*.ir"):
            self._parse_ir_file(ir_file)
        
        # Parse .sub files
        for sub_file in path.rglob("*.sub"):
            self._parse_sub_file(sub_file)
        
        return self.devices

    def parse_file(self, file_path: str) -> Device | None:
        """Parse a single Flipper file."""
        path = Path(file_path)
        
        if not path.exists():
            _LOGGER.error("File not found: %s", file_path)
            return None
        
        if path.suffix.lower() == ".ir":
            return self._parse_ir_file(path)
        elif path.suffix.lower() == ".sub":
            return self._parse_sub_file(path)
        else:
            _LOGGER.warning("Unknown file type: %s", path.suffix)
            return None

    def _parse_ir_file(self, file_path: Path) -> Device | None:
        """Parse a Flipper .ir file."""
        _LOGGER.info("Parsing IR file: %s", file_path)
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as ex:
            _LOGGER.error("Error reading file: %s", ex)
            return None
        
        # Create device from filename
        device_name = file_path.stem.replace("_", " ").title()
        
        # Try to determine category from path
        category = self._guess_category_from_path(file_path)
        
        device = Device(
            name=device_name,
            category=category,
            brand=self._extract_brand(file_path),
        )
        
        # Parse all buttons/signals
        signals = self._parse_ir_content(content)
        
        for signal in signals:
            code = RemoteCode(
                name=signal["name"],
                source="flipper",
            )
            
            if signal["type"] == "parsed":
                code.code_type = CodeType.IR_PARSED
                code.protocol = signal.get("protocol")
                code.address = signal.get("address")
                code.command = signal.get("command")
            else:  # raw
                code.code_type = CodeType.IR_RAW
                code.frequency = signal.get("frequency", 38000)
                code.duty_cycle = signal.get("duty_cycle", 0.33)
                code.raw_data = signal.get("data", [])
            
            # Convert to Broadlink format
            code.broadlink_code = self._convert_to_broadlink(code)
            
            device.commands[signal["name"]] = code
        
        # Store device
        self.devices[device.id] = device
        _LOGGER.info("Parsed %d commands from %s", len(device.commands), device_name)
        
        return device

    def _parse_ir_content(self, content: str) -> list[dict[str, Any]]:
        """Parse IR file content into signals."""
        signals = []
        current_signal: dict[str, Any] = {}
        
        for line in content.split('\n'):
            line = line.strip()
            
            # Skip empty lines and comments (unless it's a separator)
            if not line:
                continue
            if line.startswith('#'):
                # Comment lines can separate signals
                if current_signal and "name" in current_signal:
                    signals.append(current_signal)
                    current_signal = {}
                continue
            
            # Skip header lines
            if line.startswith("Filetype:") or line.startswith("Version:"):
                continue
            
            # Parse key: value
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip().lower()
                value = value.strip()
                
                if key == "name":
                    # New signal starts
                    if current_signal and "name" in current_signal:
                        signals.append(current_signal)
                    current_signal = {"name": value}
                elif key == "type":
                    current_signal["type"] = value.lower()
                elif key == "protocol":
                    current_signal["protocol"] = value
                elif key == "address":
                    current_signal["address"] = value
                elif key == "command":
                    current_signal["command"] = value
                elif key == "frequency":
                    current_signal["frequency"] = int(value)
                elif key == "duty_cycle":
                    current_signal["duty_cycle"] = float(value)
                elif key == "data":
                    # Parse space-separated integers
                    current_signal["data"] = [int(x) for x in value.split()]
        
        # Don't forget the last signal
        if current_signal and "name" in current_signal:
            signals.append(current_signal)
        
        return signals

    def _parse_sub_file(self, file_path: Path) -> Device | None:
        """Parse a Flipper .sub file."""
        _LOGGER.info("Parsing SubGHz file: %s", file_path)
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as ex:
            _LOGGER.error("Error reading file: %s", ex)
            return None
        
        # Create device from filename
        device_name = file_path.stem.replace("_", " ").title()
        
        device = Device(
            name=device_name,
            category=self._guess_category_from_path(file_path),
            brand=self._extract_brand(file_path),
        )
        
        # Parse SubGHz content
        signal = self._parse_sub_content(content)
        
        if signal:
            code = RemoteCode(
                name=file_path.stem,
                source="flipper",
            )
            
            if signal.get("protocol", "").upper() == "RAW":
                code.code_type = CodeType.RF_RAW
                code.raw_data = signal.get("raw_data", [])
            else:
                code.code_type = CodeType.RF_PARSED
                code.protocol = signal.get("protocol")
                code.rf_bit = signal.get("bit")
                code.rf_key = signal.get("key")
                code.rf_te = signal.get("te")
            
            code.rf_frequency = signal.get("frequency")
            code.rf_preset = signal.get("preset")
            
            device.commands[file_path.stem] = code
        
        self.devices[device.id] = device
        return device

    def _parse_sub_content(self, content: str) -> dict[str, Any]:
        """Parse SubGHz file content."""
        signal: dict[str, Any] = {}
        raw_data: list[int] = []
        
        for line in content.split('\n'):
            line = line.strip()
            
            if not line or line.startswith('#'):
                continue
            
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip()
                value = value.strip()
                
                if key == "Frequency":
                    signal["frequency"] = int(value)
                elif key == "Preset":
                    signal["preset"] = value
                elif key == "Protocol":
                    signal["protocol"] = value
                elif key == "Bit":
                    signal["bit"] = int(value)
                elif key == "Key":
                    signal["key"] = value
                elif key == "TE":
                    signal["te"] = int(value)
                elif key == "RAW_Data":
                    # Parse space-separated integers
                    raw_data.extend([int(x) for x in value.split()])
        
        if raw_data:
            signal["raw_data"] = raw_data
        
        return signal

    def _convert_to_broadlink(self, code: RemoteCode) -> str | None:
        """Convert a code to Broadlink format (base64)."""
        if code.code_type == CodeType.IR_RAW and code.raw_data:
            return self._flipper_raw_to_broadlink(
                code.raw_data, 
                code.frequency
            )
        elif code.code_type == CodeType.IR_PARSED:
            # For parsed protocols, we'd need protocol-specific encoding
            # For now, return None - would need to implement each protocol
            return None
        
        return None

    def _flipper_raw_to_broadlink(
        self, 
        timings: list[int], 
        frequency: int = 38000
    ) -> str:
        """
        Convert Flipper raw timings to Broadlink format.
        
        Flipper format: alternating pulse/space durations in microseconds
        Broadlink format: 0x26 (IR) + length + frequency code + pulse/space pairs
        """
        if not timings:
            return None
        
        # Broadlink uses a time unit based on the carrier frequency
        # Time unit = 1 / (frequency * 2) seconds = 500000 / frequency microseconds
        time_unit = 500000 / frequency if frequency > 0 else 13.158
        
        # Convert timings to Broadlink units
        bl_data = []
        for timing in timings:
            # Convert microseconds to Broadlink time units
            units = int(abs(timing) / time_unit)
            if units > 255:
                # Use extended format for long durations
                bl_data.extend([0x00, (units >> 8) & 0xFF, units & 0xFF])
            else:
                bl_data.append(units)
        
        # Build Broadlink packet
        # Format: 0x26 0x00 <length_lo> <length_hi> <data...> 0x0D 0x05
        packet = [0x26, 0x00]  # IR marker
        
        # Add length (little-endian)
        data_len = len(bl_data)
        packet.extend([data_len & 0xFF, (data_len >> 8) & 0xFF])
        
        # Add timing data
        packet.extend(bl_data)
        
        # Pad to multiple of 16 bytes (required by Broadlink)
        while len(packet) % 16 != 0:
            packet.append(0x00)
        
        return base64.b64encode(bytes(packet)).decode('ascii')

    def _guess_category_from_path(self, file_path: Path) -> DeviceCategory:
        """Guess device category from file path."""
        path_lower = str(file_path).lower()
        
        if "tv" in path_lower:
            return DeviceCategory.TV
        elif "receiver" in path_lower or "avr" in path_lower or "amp" in path_lower:
            return DeviceCategory.RECEIVER
        elif "soundbar" in path_lower:
            return DeviceCategory.SOUNDBAR
        elif any(x in path_lower for x in ["roku", "firetv", "apple_tv", "chromecast", "streaming"]):
            return DeviceCategory.STREAMING
        elif "cable" in path_lower or "stb" in path_lower or "box" in path_lower:
            return DeviceCategory.CABLE_BOX
        elif "ac" in path_lower or "air_cond" in path_lower or "hvac" in path_lower:
            return DeviceCategory.AC
        elif "fan" in path_lower:
            return DeviceCategory.FAN
        elif "projector" in path_lower:
            return DeviceCategory.PROJECTOR
        elif "gate" in path_lower:
            return DeviceCategory.GATE
        elif "garage" in path_lower:
            return DeviceCategory.GARAGE
        elif "light" in path_lower or "lamp" in path_lower:
            return DeviceCategory.LIGHT
        
        return DeviceCategory.OTHER

    def _extract_brand(self, file_path: Path) -> str:
        """Extract brand from file path."""
        # Try to get brand from parent directory
        parts = file_path.parts
        
        # Common structure: Brand/Model.ir
        if len(parts) >= 2:
            potential_brand = parts[-2]
            # Filter out category directories
            if potential_brand.lower() not in [
                "infrared", "subghz", "ir", "rf", "tvs", "receivers",
                "streaming", "ac", "fans", "lights", "gates"
            ]:
                return potential_brand.replace("_", " ").title()
        
        return ""


def generate_flipper_ir(device: Device) -> str:
    """Generate a Flipper .ir file from a device."""
    lines = [
        "Filetype: IR signals file",
        "Version: 1",
    ]
    
    for cmd_name, code in device.commands.items():
        lines.append("#")
        lines.append(f"name: {cmd_name}")
        
        if code.code_type == CodeType.IR_PARSED and code.protocol:
            lines.append("type: parsed")
            lines.append(f"protocol: {code.protocol}")
            if code.address:
                lines.append(f"address: {code.address}")
            if code.command:
                lines.append(f"command: {code.command}")
        elif code.raw_data:
            lines.append("type: raw")
            lines.append(f"frequency: {code.frequency}")
            lines.append(f"duty_cycle: {code.duty_cycle:.6f}")
            lines.append(f"data: {' '.join(str(x) for x in code.raw_data)}")
    
    return '\n'.join(lines)


def generate_flipper_sub(code: RemoteCode, filename: str) -> str:
    """Generate a Flipper .sub file from a code."""
    lines = []
    
    if code.code_type == CodeType.RF_RAW:
        lines.extend([
            "Filetype: Flipper SubGhz RAW File",
            "Version: 1",
            f"Frequency: {code.rf_frequency or 433920000}",
            f"Preset: {code.rf_preset or 'FuriHalSubGhzPresetOok650Async'}",
            "Protocol: RAW",
        ])
        
        if code.raw_data:
            # Split into chunks of 512 values per line
            for i in range(0, len(code.raw_data), 512):
                chunk = code.raw_data[i:i+512]
                lines.append(f"RAW_Data: {' '.join(str(x) for x in chunk)}")
    else:
        lines.extend([
            "Filetype: Flipper SubGhz Key File",
            "Version: 1",
            f"Frequency: {code.rf_frequency or 433920000}",
            f"Preset: {code.rf_preset or 'FuriHalSubGhzPresetOok650Async'}",
            f"Protocol: {code.protocol or 'Princeton'}",
        ])
        
        if code.rf_bit:
            lines.append(f"Bit: {code.rf_bit}")
        if code.rf_key:
            lines.append(f"Key: {code.rf_key}")
        if code.rf_te:
            lines.append(f"TE: {code.rf_te}")
    
    return '\n'.join(lines)
