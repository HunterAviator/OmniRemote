"""
OmniRemote Device Catalog

Comprehensive catalog of IR/RF/Network codes for common devices.
Organized by device type with multiple profiles per brand.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any
import importlib
import logging
import os
from pathlib import Path

_LOGGER = logging.getLogger(__name__)


class ControlMethod(Enum):
    """How to control the device."""
    IR = "ir"
    RF = "rf"
    NETWORK = "network"
    BLUETOOTH = "bluetooth"
    HDMI_CEC = "hdmi_cec"
    RS232 = "rs232"


class IRProtocol(Enum):
    """IR protocol types."""
    NEC = "NEC"
    NEC_EXT = "NECext"
    SAMSUNG32 = "Samsung32"
    SONY_SIRC = "SIRC"
    SONY_SIRC15 = "SIRC15"
    SONY_SIRC20 = "SIRC20"
    RC5 = "RC5"
    RC6 = "RC6"
    PANASONIC = "Kaseikyo"
    JVC = "JVC"
    SHARP = "Sharp"
    DENON = "Denon"
    RAW = "RAW"


@dataclass
class IRCode:
    """IR code definition."""
    name: str
    protocol: IRProtocol
    address: str  # Hex address
    command: str  # Hex command
    frequency: int = 38000
    duty_cycle: float = 0.33
    repeat: int = 1
    
    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "protocol": self.protocol.value,
            "address": self.address,
            "command": self.command,
            "frequency": self.frequency,
            "duty_cycle": self.duty_cycle,
            "repeat": self.repeat,
        }


@dataclass
class RFCode:
    """RF code definition."""
    name: str
    frequency: int  # Hz (315000000, 433920000, etc.)
    protocol: str  # Protocol name
    code: str  # Code data
    
    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "frequency": self.frequency,
            "protocol": self.protocol,
            "code": self.code,
        }


@dataclass
class NetworkCommand:
    """Network/REST command definition."""
    name: str
    method: str  # GET, POST, PUT, RAW, ADB, PYATV, etc.
    endpoint: str  # URL path or command
    payload: dict[str, Any] = field(default_factory=dict)
    headers: dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "method": self.method,
            "endpoint": self.endpoint,
            "payload": self.payload,
            "headers": self.headers,
        }


@dataclass
class DeviceProfile:
    """
    A device profile with codes for a specific model/version.
    """
    id: str
    name: str
    brand: str
    category: str
    model_years: str = ""
    description: str = ""
    control_methods: list[ControlMethod] = field(default_factory=list)
    ir_codes: dict[str, IRCode] = field(default_factory=dict)
    rf_codes: dict[str, RFCode] = field(default_factory=dict)
    network_commands: dict[str, NetworkCommand] = field(default_factory=dict)
    network_port: int = 0
    network_protocol: str = ""
    logo_url: str = ""
    apps: dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        # Combine all commands for easy UI access
        commands = {}
        for k, v in self.ir_codes.items():
            commands[k] = {"type": "ir", **v.to_dict()}
        for k, v in self.rf_codes.items():
            commands[k] = {"type": "rf", **v.to_dict()}
        for k, v in self.network_commands.items():
            commands[k] = {"type": "network", **v.to_dict()}
        
        return {
            "id": self.id,
            "name": self.name,
            "brand": self.brand,
            "category": self.category,
            "model_years": self.model_years,
            "description": self.description,
            "control_methods": [m.value for m in self.control_methods],
            "commands": commands,  # Combined commands for UI
            "ir_codes": {k: v.to_dict() for k, v in self.ir_codes.items()},
            "rf_codes": {k: v.to_dict() for k, v in self.rf_codes.items()},
            "network_commands": {k: v.to_dict() for k, v in self.network_commands.items()},
            "network_port": self.network_port,
            "network_protocol": self.network_protocol,
            "logo_url": self.logo_url,
            "apps": self.apps,
        }


# =============================================================================
# IR Code Helpers
# =============================================================================

def nec(addr: int, cmd: int, name: str = "") -> IRCode:
    """Create NEC protocol IR code."""
    return IRCode(
        name=name,
        protocol=IRProtocol.NEC,
        address=f"{addr:02X} 00 00 00",
        command=f"{cmd:02X} 00 00 00",
    )

def nec_ext(addr: int, cmd: int, name: str = "") -> IRCode:
    """Create NEC extended protocol IR code."""
    return IRCode(
        name=name,
        protocol=IRProtocol.NEC_EXT,
        address=f"{addr:04X}",
        command=f"{cmd:02X} 00 00 00",
    )

def samsung(addr: int, cmd: int, name: str = "") -> IRCode:
    """Create Samsung32 protocol IR code."""
    return IRCode(
        name=name,
        protocol=IRProtocol.SAMSUNG32,
        address=f"{addr:02X} 00 00 00",
        command=f"{cmd:02X} 00 00 00",
    )

def sony(addr: int, cmd: int, name: str = "", bits: int = 12) -> IRCode:
    """Create Sony SIRC protocol IR code."""
    proto = IRProtocol.SONY_SIRC
    if bits == 15:
        proto = IRProtocol.SONY_SIRC15
    elif bits == 20:
        proto = IRProtocol.SONY_SIRC20
    return IRCode(
        name=name,
        protocol=proto,
        address=f"{addr:02X} 00 00 00",
        command=f"{cmd:02X} 00 00 00",
    )

def rc5(addr: int, cmd: int, name: str = "") -> IRCode:
    """Create RC5 protocol IR code (Philips)."""
    return IRCode(
        name=name,
        protocol=IRProtocol.RC5,
        address=f"{addr:02X} 00 00 00",
        command=f"{cmd:02X} 00 00 00",
    )

def rc6(addr: int, cmd: int, name: str = "") -> IRCode:
    """Create RC6 protocol IR code."""
    return IRCode(
        name=name,
        protocol=IRProtocol.RC6,
        address=f"{addr:02X} 00 00 00",
        command=f"{cmd:02X} 00 00 00",
    )

def panasonic(addr: int, cmd: int, name: str = "") -> IRCode:
    """Create Panasonic/Kaseikyo protocol IR code."""
    return IRCode(
        name=name,
        protocol=IRProtocol.PANASONIC,
        address=f"{addr:04X}",
        command=f"{cmd:06X}",
    )

def jvc(addr: int, cmd: int, name: str = "") -> IRCode:
    """Create JVC protocol IR code."""
    return IRCode(
        name=name,
        protocol=IRProtocol.JVC,
        address=f"{addr:02X} 00 00 00",
        command=f"{cmd:02X} 00 00 00",
    )


# =============================================================================
# Brand Logos
# =============================================================================

BRAND_LOGOS = {
    "samsung": "https://cdn.simpleicons.org/samsung",
    "lg": "https://cdn.simpleicons.org/lg",
    "sony": "https://cdn.simpleicons.org/sony",
    "vizio": "https://cdn.simpleicons.org/vizio",
    "philips": "https://cdn.simpleicons.org/philips",
    "panasonic": "https://cdn.simpleicons.org/panasonic",
    "tcl": "https://upload.wikimedia.org/wikipedia/commons/4/49/TCL_Logo.svg",
    "hisense": "https://upload.wikimedia.org/wikipedia/commons/8/8e/Hisense_logo.svg",
    "sharp": "https://cdn.simpleicons.org/sharp",
    "toshiba": "https://upload.wikimedia.org/wikipedia/commons/0/01/Toshiba_logo.svg",
    "roku": "https://cdn.simpleicons.org/roku",
    "amazon": "https://cdn.simpleicons.org/amazon",
    "apple": "https://cdn.simpleicons.org/apple",
    "nvidia": "https://cdn.simpleicons.org/nvidia",
    "google": "https://cdn.simpleicons.org/google",
    "denon": "https://upload.wikimedia.org/wikipedia/commons/e/e5/Denon_logo.svg",
    "yamaha": "https://cdn.simpleicons.org/yamaha",
    "onkyo": "https://upload.wikimedia.org/wikipedia/commons/6/66/Onkyo_logo.svg",
    "marantz": "https://upload.wikimedia.org/wikipedia/commons/c/c8/Marantz_logo.svg",
    "pioneer": "https://upload.wikimedia.org/wikipedia/commons/8/89/Pioneer_logo.svg",
    "bose": "https://cdn.simpleicons.org/bose",
    "sonos": "https://cdn.simpleicons.org/sonos",
    "xbox": "https://cdn.simpleicons.org/xbox",
    "playstation": "https://cdn.simpleicons.org/playstation",
    "nintendo": "https://cdn.simpleicons.org/nintendo",
    "epson": "https://cdn.simpleicons.org/epson",
    "benq": "https://upload.wikimedia.org/wikipedia/commons/8/85/BenQ_Logo.svg",
    "optoma": "https://upload.wikimedia.org/wikipedia/commons/5/5a/Optoma_Logo.svg",
    "jvc": "https://upload.wikimedia.org/wikipedia/commons/9/9c/JVC_logo.svg",
    "directv": "https://cdn.simpleicons.org/directv",
    "tivo": "https://cdn.simpleicons.org/tivo",
    "hunter": "https://upload.wikimedia.org/wikipedia/commons/9/95/Hunter_Fan_Company_logo.svg",
    "hampton_bay": "https://upload.wikimedia.org/wikipedia/commons/d/d3/Hampton_Bay_Logo.svg",
    "daikin": "https://upload.wikimedia.org/wikipedia/commons/a/a3/Daikin_logo.svg",
    "lg_ac": "https://cdn.simpleicons.org/lg",
    "jensen": "https://upload.wikimedia.org/wikipedia/commons/1/1b/Jensen_logo.svg",
}


# =============================================================================
# Catalog Registry
# =============================================================================

_CATALOG: dict[str, DeviceProfile] = {}
_CATALOG_BY_CATEGORY: dict[str, list[DeviceProfile]] = {}
_CATALOG_BY_BRAND: dict[str, list[DeviceProfile]] = {}


def register_profile(profile: DeviceProfile) -> None:
    """Register a device profile in the catalog."""
    _CATALOG[profile.id] = profile
    
    if profile.category not in _CATALOG_BY_CATEGORY:
        _CATALOG_BY_CATEGORY[profile.category] = []
    _CATALOG_BY_CATEGORY[profile.category].append(profile)
    
    brand_lower = profile.brand.lower()
    if brand_lower not in _CATALOG_BY_BRAND:
        _CATALOG_BY_BRAND[brand_lower] = []
    _CATALOG_BY_BRAND[brand_lower].append(profile)


def get_profile(profile_id: str) -> DeviceProfile | None:
    """Get a profile by ID."""
    return _CATALOG.get(profile_id)


def get_profiles_by_category(category: str) -> list[DeviceProfile]:
    """Get all profiles for a category."""
    return _CATALOG_BY_CATEGORY.get(category, [])


def get_profiles_by_brand(brand: str) -> list[DeviceProfile]:
    """Get all profiles for a brand."""
    return _CATALOG_BY_BRAND.get(brand.lower(), [])


def search_catalog(query: str) -> list[DeviceProfile]:
    """Search catalog by name, brand, or category."""
    query = query.lower()
    results = []
    for profile in _CATALOG.values():
        if (query in profile.name.lower() or
            query in profile.brand.lower() or
            query in profile.category.lower() or
            query in profile.description.lower()):
            results.append(profile)
    return results


def list_all_profiles() -> list[dict]:
    """List all profiles as dicts."""
    return [p.to_dict() for p in _CATALOG.values()]


def get_categories() -> list[str]:
    """Get all available categories."""
    return list(_CATALOG_BY_CATEGORY.keys())


def get_brands() -> list[str]:
    """Get all available brands."""
    return list(_CATALOG_BY_BRAND.keys())


# =============================================================================
# Auto-load device modules using exec() for reliability
# =============================================================================

def _load_device_modules():
    """Load all device modules to register profiles."""
    catalog_dir = Path(__file__).parent
    
    # Track loaded count
    loaded = 0
    failed = 0
    
    for category_dir in sorted(catalog_dir.iterdir()):
        if not category_dir.is_dir() or category_dir.name.startswith('_'):
            continue
            
        for device_file in sorted(category_dir.glob('*.py')):
            if device_file.name.startswith('_'):
                continue
                
            try:
                # Read and execute the module code directly
                code = device_file.read_text()
                
                # Create a module-like namespace with access to our functions
                namespace = {
                    'DeviceProfile': DeviceProfile,
                    'ControlMethod': ControlMethod,
                    'IRCode': IRCode,
                    'RFCode': RFCode,
                    'NetworkCommand': NetworkCommand,
                    'IRProtocol': IRProtocol,
                    'nec': nec,
                    'nec_ext': nec_ext,
                    'samsung': samsung,
                    'sony': sony,
                    'rc5': rc5,
                    'rc6': rc6,
                    'panasonic': panasonic,
                    'jvc': jvc,
                    'BRAND_LOGOS': BRAND_LOGOS,
                    'register_profile': register_profile,
                    '__name__': f'catalog.{category_dir.name}.{device_file.stem}',
                }
                
                exec(code, namespace)
                loaded += 1
                
            except Exception as e:
                _LOGGER.warning("Failed to load %s/%s: %s", category_dir.name, device_file.name, e)
                failed += 1
    
    _LOGGER.debug("Catalog loaded: %d profiles from %d modules (%d failed)", 
                  len(_CATALOG), loaded, failed)


# Load on import
_load_device_modules()


# =============================================================================
# Legacy Compatibility Exports
# =============================================================================
# These aliases maintain backward compatibility with code that imports from
# the old single-file catalog.py

DEVICE_CATALOG = _CATALOG
CATALOG_BY_CATEGORY = _CATALOG_BY_CATEGORY
CATALOG_BY_BRAND = _CATALOG_BY_BRAND


def get_catalog_device(device_id: str) -> DeviceProfile | None:
    """Legacy alias for get_profile."""
    return get_profile(device_id)


def list_catalog() -> list[dict]:
    """Legacy alias for list_all_profiles."""
    return list_all_profiles()
