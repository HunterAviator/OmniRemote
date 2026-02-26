"""
IR Protocol Encoder for Broadlink devices.

Converts protocol-based IR codes (NEC, Samsung32, Sony, RC5, RC6, etc.)
to Broadlink raw format that can be transmitted.
"""
from __future__ import annotations

import base64
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Any

_LOGGER = logging.getLogger(__name__)

# Debug log storage for GUI debugger
_debug_log: list[dict] = []
_max_debug_entries = 100


def get_debug_log() -> list[dict]:
    """Get the debug log for GUI display."""
    return list(_debug_log)


def clear_debug_log() -> None:
    """Clear the debug log."""
    _debug_log.clear()


def _log_debug(entry: dict) -> None:
    """Add entry to debug log."""
    entry["timestamp"] = datetime.now().isoformat()
    _debug_log.append(entry)
    # Keep log bounded
    while len(_debug_log) > _max_debug_entries:
        _debug_log.pop(0)


# Import IRProtocol enum values for comparison
# We need these at runtime, not just for type checking
try:
    from .catalog import IRProtocol
except ImportError:
    # Standalone testing - define a minimal enum
    class IRProtocol(Enum):
        NEC = "nec"
        NEC_EXT = "nec_extended"
        SAMSUNG32 = "samsung32"
        SONY_SIRC = "sony_sirc"
        SONY_SIRC15 = "sony_sirc15"
        SONY_SIRC20 = "sony_sirc20"
        RC5 = "rc5"
        RC6 = "rc6"
        PANASONIC = "panasonic"
        JVC = "jvc"

if TYPE_CHECKING:
    from .catalog import IRCode


def encode_ir_to_broadlink(ir_code: "IRCode") -> str | None:
    """
    Convert an IRCode to Broadlink base64 format.
    
    Returns base64-encoded Broadlink packet or None if conversion fails.
    """
    debug_entry = {
        "action": "encode_ir_to_broadlink",
        "input": {
            "name": getattr(ir_code, 'name', 'unknown'),
            "protocol": str(ir_code.protocol.value if hasattr(ir_code.protocol, 'value') else ir_code.protocol),
            "address": ir_code.address,
            "command": ir_code.command,
            "frequency": getattr(ir_code, 'frequency', 38000),
        },
        "status": "started",
    }
    
    try:
        timings = _protocol_to_timings(ir_code)
        if not timings:
            debug_entry["status"] = "error"
            debug_entry["error"] = f"Could not generate timings for protocol {ir_code.protocol}"
            _log_debug(debug_entry)
            _LOGGER.warning("Could not encode protocol %s", ir_code.protocol)
            return None
        
        debug_entry["timings"] = {
            "count": len(timings),
            "total_duration_us": sum(timings),
            "total_duration_ms": sum(timings) / 1000,
            "preview": timings[:20],
        }
        
        result = _timings_to_broadlink(timings, getattr(ir_code, 'frequency', 38000))
        
        if result:
            debug_entry["status"] = "success"
            debug_entry["output"] = {
                "broadlink_base64": result[:50] + "..." if len(result) > 50 else result,
                "broadlink_bytes": len(base64.b64decode(result)),
            }
            _LOGGER.debug(
                "Encoded %s: protocol=%s, addr=%s, cmd=%s -> %d bytes",
                getattr(ir_code, 'name', 'code'),
                ir_code.protocol,
                ir_code.address,
                ir_code.command,
                len(base64.b64decode(result))
            )
        else:
            debug_entry["status"] = "error"
            debug_entry["error"] = "Failed to convert timings to Broadlink format"
        
        _log_debug(debug_entry)
        return result
        
    except Exception as ex:
        debug_entry["status"] = "exception"
        debug_entry["error"] = str(ex)
        _log_debug(debug_entry)
        _LOGGER.error("Error encoding IR code: %s", ex)
        return None


def _timings_to_broadlink(timings: list[int], frequency: int = 38000) -> str:
    """
    Convert raw timings (microseconds) to Broadlink format.
    
    Timings are alternating mark/space durations in microseconds.
    
    IMPORTANT: Broadlink RM2/RM Mini uses a fixed time unit of approximately
    30.45µs (8192/269), NOT based on the carrier frequency!
    """
    if not timings:
        return None
    
    # Broadlink time unit is fixed at 8192/269 µs ≈ 30.45µs
    # This is independent of the carrier frequency!
    BROADLINK_TIME_UNIT = 8192.0 / 269.0  # ≈ 30.45 µs
    
    _LOGGER.debug("Converting %d timings to Broadlink format (time_unit=%.2fµs)", 
                  len(timings), BROADLINK_TIME_UNIT)
    
    # Convert timings to Broadlink units
    bl_data = []
    for timing in timings:
        # Convert microseconds to Broadlink time units
        units = round(abs(timing) / BROADLINK_TIME_UNIT)
        
        if units == 0:
            units = 1  # Minimum 1 unit
        
        if units > 255:
            # Use extended format for long durations (3 bytes: 0x00, high, low)
            bl_data.extend([0x00, (units >> 8) & 0xFF, units & 0xFF])
        else:
            bl_data.append(units)
    
    # Build Broadlink packet
    # Format: 0x26 0x00 <length_lo> <length_hi> <data...>
    # 0x26 = IR transmission marker
    # 0x00 = Repeat count (0 = send once)
    packet = [0x26, 0x00]
    
    # Add length (little-endian)
    data_len = len(bl_data)
    packet.extend([data_len & 0xFF, (data_len >> 8) & 0xFF])
    
    # Add timing data
    packet.extend(bl_data)
    
    # Pad to multiple of 16 bytes (required by Broadlink)
    while len(packet) % 16 != 0:
        packet.append(0x00)
    
    _LOGGER.debug("Broadlink packet: %d bytes total, %d bytes timing data", 
                  len(packet), data_len)
    
    return base64.b64encode(bytes(packet)).decode('ascii')


def _protocol_to_timings(ir_code: "IRCode") -> list[int] | None:
    """Convert protocol-based IR code to raw timings."""
    protocol = ir_code.protocol
    
    # Parse address and command from hex strings
    try:
        # Handle different address formats
        addr_str = ir_code.address.replace(" ", "")
        cmd_str = ir_code.command.replace(" ", "")
        
        # Take first byte(s) as needed
        if len(addr_str) >= 2:
            address = int(addr_str[:2], 16)
        else:
            address = int(addr_str, 16) if addr_str else 0
            
        if len(cmd_str) >= 2:
            command = int(cmd_str[:2], 16)
        else:
            command = int(cmd_str, 16) if cmd_str else 0
            
        # For extended address formats
        if len(addr_str) >= 4:
            address_ext = int(addr_str[:4], 16)
        else:
            address_ext = address
            
    except ValueError as ex:
        _LOGGER.error("Invalid address/command format: %s", ex)
        return None
    
    # Generate timings based on protocol
    if protocol == IRProtocol.NEC:
        return _encode_nec(address, command)
    elif protocol == IRProtocol.NEC_EXT:
        return _encode_nec_extended(address_ext, command)
    elif protocol == IRProtocol.SAMSUNG32:
        return _encode_samsung32(address, command)
    elif protocol in (IRProtocol.SONY_SIRC, IRProtocol.SONY_SIRC15, IRProtocol.SONY_SIRC20):
        bits = 12
        if protocol == IRProtocol.SONY_SIRC15:
            bits = 15
        elif protocol == IRProtocol.SONY_SIRC20:
            bits = 20
        return _encode_sony(address, command, bits)
    elif protocol == IRProtocol.RC5:
        return _encode_rc5(address, command)
    elif protocol == IRProtocol.RC6:
        return _encode_rc6(address, command)
    elif protocol == IRProtocol.PANASONIC:
        return _encode_panasonic(address_ext, int(cmd_str[:6], 16) if len(cmd_str) >= 6 else command)
    elif protocol == IRProtocol.JVC:
        return _encode_jvc(address, command)
    else:
        _LOGGER.warning("Unsupported protocol: %s", protocol)
        return None


# =============================================================================
# NEC Protocol (38kHz)
# =============================================================================
# Leader: 9000µs mark, 4500µs space
# Logical 0: 562µs mark, 562µs space
# Logical 1: 562µs mark, 1687µs space
# Format: Address (8), ~Address (8), Command (8), ~Command (8)

def _encode_nec(address: int, command: int) -> list[int]:
    """Encode NEC protocol."""
    timings = []
    
    # Leader
    timings.extend([9000, 4500])
    
    # Build data: address, ~address, command, ~command
    data = [
        address & 0xFF,
        (~address) & 0xFF,
        command & 0xFF,
        (~command) & 0xFF
    ]
    
    # Encode each bit (LSB first)
    for byte in data:
        for bit in range(8):
            timings.append(562)  # Mark
            if (byte >> bit) & 1:
                timings.append(1687)  # Space for 1
            else:
                timings.append(562)   # Space for 0
    
    # End mark
    timings.append(562)
    
    return timings


def _encode_nec_extended(address: int, command: int) -> list[int]:
    """Encode NEC Extended protocol (16-bit address)."""
    timings = []
    
    # Leader
    timings.extend([9000, 4500])
    
    # Build data: address_lo, address_hi, command, ~command
    data = [
        address & 0xFF,
        (address >> 8) & 0xFF,
        command & 0xFF,
        (~command) & 0xFF
    ]
    
    # Encode each bit (LSB first)
    for byte in data:
        for bit in range(8):
            timings.append(562)
            if (byte >> bit) & 1:
                timings.append(1687)
            else:
                timings.append(562)
    
    # End mark
    timings.append(562)
    
    return timings


# =============================================================================
# Samsung32 Protocol (38kHz)
# =============================================================================
# Leader: 4500µs mark, 4500µs space
# 
# IMPORTANT: There are TWO Samsung IR encoding variants:
# 
# Variant 1 (Space-based, traditional):
#   - Logical 0: 560µs mark, 560µs space
#   - Logical 1: 560µs mark, 1690µs space
#   - Bit determined by SPACE duration
#
# Variant 2 (Mark-based, used by many Broadlink-controlled TVs):
#   - Logical 0: 560µs mark, 560µs space  
#   - Logical 1: 1690µs mark, 560µs space
#   - Bit determined by MARK duration
#
# We use Variant 2 (mark-based) as this matches Broadlink app behavior.
# Format: Address (8), Address (8), Command (8), ~Command (8)

def _encode_samsung32(address: int, command: int, repeats: int = 1) -> list[int]:
    """Encode Samsung32 protocol (mark-based variant).
    
    This uses the mark-duration encoding that matches Broadlink app behavior.
    
    Args:
        address: Device address (typically 0x07 for Samsung TV)
        command: Command code
        repeats: Number of times to repeat the frame (default 1)
    """
    
    def encode_frame():
        """Encode a single Samsung32 frame."""
        frame = []
        
        # Leader pulse
        frame.extend([4500, 4500])
        
        # Build data: address, address (repeated), command, ~command
        data = [
            address & 0xFF,
            address & 0xFF,  # Samsung repeats address
            command & 0xFF,
            (~command) & 0xFF
        ]
        
        # Encode each bit (LSB first)
        # Mark-based encoding: long mark = 1, short mark = 0
        for byte in data:
            for bit in range(8):
                if (byte >> bit) & 1:
                    frame.append(1690)  # Long mark for 1
                else:
                    frame.append(560)   # Short mark for 0
                frame.append(560)       # Space is always short
        
        # End mark
        frame.append(560)
        
        return frame
    
    timings = []
    
    # First frame
    timings.extend(encode_frame())
    
    # Add repeats with gap if needed
    for _ in range(repeats - 1):
        # Gap between frames (about 46ms for Samsung)
        timings.append(46000)
        timings.extend(encode_frame())
    
    return timings


# =============================================================================
# Sony SIRC Protocol (40kHz)
# =============================================================================
# Leader: 2400µs mark, 600µs space
# Logical 0: 600µs mark, 600µs space
# Logical 1: 1200µs mark, 600µs space
# Format: Command (7), Address (5/8/13)

def _encode_sony(address: int, command: int, bits: int = 12) -> list[int]:
    """Encode Sony SIRC protocol."""
    timings = []
    
    # Leader
    timings.extend([2400, 600])
    
    # Command (7 bits, LSB first)
    for bit in range(7):
        if (command >> bit) & 1:
            timings.append(1200)
        else:
            timings.append(600)
        timings.append(600)
    
    # Address (5, 8, or 13 bits depending on protocol version)
    addr_bits = bits - 7
    for bit in range(addr_bits):
        if (address >> bit) & 1:
            timings.append(1200)
        else:
            timings.append(600)
        timings.append(600)
    
    return timings


# =============================================================================
# RC5 Protocol (36kHz) - Manchester encoding
# =============================================================================
# Bit time: 889µs per half-bit
# Logical 0: space-mark (889µs space, 889µs mark)
# Logical 1: mark-space (889µs mark, 889µs space)
# Format: Start (2), Toggle (1), Address (5), Command (6)

def _encode_rc5(address: int, command: int, toggle: int = 0) -> list[int]:
    """Encode RC5 protocol (Manchester encoding)."""
    timings = []
    
    # Build 14-bit data: 2 start bits (1,1), toggle, 5-bit address, 6-bit command
    # Start bits are always 1,1 for RC5
    bits = []
    bits.append(1)  # Start bit 1
    bits.append(1)  # Start bit 2
    bits.append(toggle & 1)  # Toggle bit
    
    # Address (5 bits, MSB first)
    for i in range(4, -1, -1):
        bits.append((address >> i) & 1)
    
    # Command (6 bits, MSB first)
    for i in range(5, -1, -1):
        bits.append((command >> i) & 1)
    
    # Manchester encode
    for i, bit in enumerate(bits):
        if bit == 1:
            # 1 = mark then space
            timings.append(889)
            timings.append(889)
        else:
            # 0 = space then mark
            # But we need to handle transitions between bits
            timings.append(889)
            timings.append(889)
    
    # Merge consecutive marks/spaces
    return _merge_manchester_timings(timings, bits)


def _merge_manchester_timings(timings: list[int], bits: list[int]) -> list[int]:
    """Convert Manchester bit sequence to mark/space timings."""
    result = []
    
    for i, bit in enumerate(bits):
        if bit == 1:
            # 1 = mark-space
            if i == 0 or bits[i-1] == 0:
                result.append(889)  # New mark
            else:
                result[-1] += 889   # Extend previous mark
            result.append(889)      # Space
        else:
            # 0 = space-mark
            if i == 0:
                result.append(889)  # Initial space (will be ignored in IR)
            elif bits[i-1] == 1:
                result[-1] += 889   # Extend previous space
            else:
                result.append(889)  # New space
            result.append(889)      # Mark
    
    # RC5 starts with mark, so adjust if needed
    if result and len(result) > 1:
        # Ensure we start with a mark
        return result[1:] if result[0] < 889 else result
    
    return result


# =============================================================================
# RC6 Protocol (36kHz)
# =============================================================================
# More complex than RC5, uses variable bit times

def _encode_rc6(address: int, command: int, toggle: int = 0) -> list[int]:
    """Encode RC6 protocol (Mode 0)."""
    timings = []
    
    # Leader: 2666µs mark, 889µs space
    timings.extend([2666, 889])
    
    # Start bit (1)
    timings.extend([444, 444])
    
    # Mode bits (3 bits, all 0 for mode 0)
    for _ in range(3):
        timings.extend([444, 444])
    
    # Trailer/Toggle bit (double length)
    if toggle:
        timings.extend([889, 889])
    else:
        timings.extend([889, 889])
    
    # Address (8 bits)
    for i in range(7, -1, -1):
        if (address >> i) & 1:
            timings.extend([444, 444])
        else:
            timings.extend([444, 444])
    
    # Command (8 bits)
    for i in range(7, -1, -1):
        if (command >> i) & 1:
            timings.extend([444, 444])
        else:
            timings.extend([444, 444])
    
    return timings


# =============================================================================
# Panasonic/Kaseikyo Protocol (37kHz)
# =============================================================================
# Leader: 3500µs mark, 1750µs space
# Logical 0: 432µs mark, 432µs space
# Logical 1: 432µs mark, 1296µs space

def _encode_panasonic(address: int, command: int) -> list[int]:
    """Encode Panasonic/Kaseikyo protocol."""
    timings = []
    
    # Leader
    timings.extend([3500, 1750])
    
    # OEM code (16 bits) - typically 0x4004 for Panasonic
    oem = 0x4004
    
    # Build 48-bit data
    data = [
        (oem >> 8) & 0xFF,      # OEM1
        oem & 0xFF,             # OEM2
        (address >> 8) & 0xFF,  # Device high
        address & 0xFF,         # Device low
        (command >> 16) & 0xFF, # Function high
        (command >> 8) & 0xFF,  # Function mid
        command & 0xFF,         # Function low + parity
    ]
    
    # Encode (LSB first per byte)
    for byte in data[:6]:  # First 6 bytes
        for bit in range(8):
            timings.append(432)
            if (byte >> bit) & 1:
                timings.append(1296)
            else:
                timings.append(432)
    
    # End mark
    timings.append(432)
    
    return timings


# =============================================================================
# JVC Protocol (38kHz)
# =============================================================================
# Leader: 8400µs mark, 4200µs space (first frame only)
# Logical 0: 525µs mark, 525µs space
# Logical 1: 525µs mark, 1575µs space

def _encode_jvc(address: int, command: int) -> list[int]:
    """Encode JVC protocol."""
    timings = []
    
    # Leader
    timings.extend([8400, 4200])
    
    # Address (8 bits, LSB first)
    for bit in range(8):
        timings.append(525)
        if (address >> bit) & 1:
            timings.append(1575)
        else:
            timings.append(525)
    
    # Command (8 bits, LSB first)
    for bit in range(8):
        timings.append(525)
        if (command >> bit) & 1:
            timings.append(1575)
        else:
            timings.append(525)
    
    # End mark
    timings.append(525)
    
    return timings


# =============================================================================
# Test/Debug Functions
# =============================================================================

def test_encode(protocol: str, address: int, command: int) -> dict:
    """Test encoding a protocol. Returns debug info."""
    try:
        from .catalog import IRCode
    except ImportError:
        # Standalone testing
        from dataclasses import dataclass
        @dataclass
        class IRCode:
            name: str
            protocol: Any
            address: str
            command: str
            frequency: int = 38000
    
    # Map protocol string to enum
    protocol_map = {
        "nec": IRProtocol.NEC,
        "nec_ext": IRProtocol.NEC_EXT,
        "samsung": IRProtocol.SAMSUNG32,
        "samsung32": IRProtocol.SAMSUNG32,
        "sony": IRProtocol.SONY_SIRC,
        "sony12": IRProtocol.SONY_SIRC,
        "sony15": IRProtocol.SONY_SIRC15,
        "sony20": IRProtocol.SONY_SIRC20,
        "rc5": IRProtocol.RC5,
        "rc6": IRProtocol.RC6,
        "panasonic": IRProtocol.PANASONIC,
        "jvc": IRProtocol.JVC,
    }
    
    proto_enum = protocol_map.get(protocol.lower())
    if not proto_enum:
        return {"error": f"Unknown protocol: {protocol}"}
    
    ir_code = IRCode(
        name="test",
        protocol=proto_enum,
        address=f"{address:02X} 00 00 00",
        command=f"{command:02X} 00 00 00",
    )
    
    timings = _protocol_to_timings(ir_code)
    broadlink = encode_ir_to_broadlink(ir_code)
    
    return {
        "protocol": protocol,
        "address": address,
        "command": command,
        "timings_count": len(timings) if timings else 0,
        "timings_preview": timings[:20] if timings else None,
        "broadlink_base64": broadlink,
        "broadlink_length": len(base64.b64decode(broadlink)) if broadlink else 0,
    }
