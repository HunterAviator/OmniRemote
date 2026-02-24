"""Pre-built device catalog with IR codes organized by device type."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from .const import CodeType, DeviceCategory, RemoteCode


class ControlMethod(Enum):
    """How to control the device."""
    IR = "ir"
    RF = "rf"
    NETWORK = "network"
    BLUETOOTH = "bluetooth"
    HDMI_CEC = "hdmi_cec"


@dataclass
class CatalogDevice:
    """A device template from the catalog."""
    id: str
    name: str
    brand: str
    category: DeviceCategory
    control_methods: list[ControlMethod]
    ir_codes: dict[str, RemoteCode] = field(default_factory=dict)
    rf_codes: dict[str, RemoteCode] = field(default_factory=dict)
    network_config: dict[str, Any] = field(default_factory=dict)
    bluetooth_config: dict[str, Any] = field(default_factory=dict)
    apps: dict[str, str] = field(default_factory=dict)
    channels: dict[str, str] = field(default_factory=dict)
    logo_url: str = ""  # Brand logo URL
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "brand": self.brand,
            "category": self.category.value,
            "control_methods": [m.value for m in self.control_methods],
            "ir_codes": {k: v.to_dict() for k, v in self.ir_codes.items()},
            "rf_codes": {k: v.to_dict() for k, v in self.rf_codes.items()},
            "network_config": self.network_config,
            "bluetooth_config": self.bluetooth_config,
            "apps": self.apps,
            "channels": self.channels,
            "logo_url": self.logo_url,
        }


# =============================================================================
# IR CODE HELPERS
# =============================================================================

def _nec(addr: int, cmd: int, name: str = "") -> RemoteCode:
    """Create NEC protocol code."""
    return RemoteCode(name=name, code_type=CodeType.IR_PARSED, protocol="NEC",
                      address=f"{addr:02X} 00 00 00", command=f"{cmd:02X} 00 00 00")

def _samsung(addr: int, cmd: int, name: str = "") -> RemoteCode:
    """Create Samsung32 protocol code."""
    return RemoteCode(name=name, code_type=CodeType.IR_PARSED, protocol="Samsung32",
                      address=f"{addr:02X} 00 00 00", command=f"{cmd:02X} 00 00 00")

def _sony(addr: int, cmd: int, name: str = "") -> RemoteCode:
    """Create Sony SIRC protocol code."""
    return RemoteCode(name=name, code_type=CodeType.IR_PARSED, protocol="SIRC",
                      address=f"{addr:02X} 00 00 00", command=f"{cmd:02X} 00 00 00")

def _rc5(addr: int, cmd: int, name: str = "") -> RemoteCode:
    """Create RC5 protocol code (Philips)."""
    return RemoteCode(name=name, code_type=CodeType.IR_PARSED, protocol="RC5",
                      address=f"{addr:02X} 00 00 00", command=f"{cmd:02X} 00 00 00")

def _rc6(addr: int, cmd: int, name: str = "") -> RemoteCode:
    """Create RC6 protocol code."""
    return RemoteCode(name=name, code_type=CodeType.IR_PARSED, protocol="RC6",
                      address=f"{addr:02X} 00 00 00", command=f"{cmd:02X} 00 00 00")


# Brand logo URLs (using simple-icons CDN)
BRAND_LOGOS = {
    "samsung": "https://cdn.simpleicons.org/samsung",
    "lg": "https://cdn.simpleicons.org/lg",
    "sony": "https://cdn.simpleicons.org/sony",
    "vizio": "https://cdn.simpleicons.org/vizio",
    "philips": "https://cdn.simpleicons.org/philips",
    "panasonic": "https://cdn.simpleicons.org/panasonic",
    "roku": "https://cdn.simpleicons.org/roku",
    "amazon": "https://cdn.simpleicons.org/amazon",
    "apple": "https://cdn.simpleicons.org/apple",
    "nvidia": "https://cdn.simpleicons.org/nvidia",
    "denon": "https://upload.wikimedia.org/wikipedia/commons/e/e5/Denon_logo.svg",
    "yamaha": "https://cdn.simpleicons.org/yamaha",
    "onkyo": "https://upload.wikimedia.org/wikipedia/commons/6/66/Onkyo_logo.svg",
    "marantz": "https://upload.wikimedia.org/wikipedia/commons/c/c8/Marantz_logo.svg",
    "bose": "https://cdn.simpleicons.org/bose",
    "sonos": "https://cdn.simpleicons.org/sonos",
    "xbox": "https://cdn.simpleicons.org/xbox",
    "playstation": "https://cdn.simpleicons.org/playstation",
    "nintendo": "https://cdn.simpleicons.org/nintendo",
    "epson": "https://cdn.simpleicons.org/epson",
    "benq": "https://upload.wikimedia.org/wikipedia/commons/8/85/BenQ_Logo.svg",
    "optoma": "https://upload.wikimedia.org/wikipedia/commons/5/5a/Optoma_Logo.svg",
    "directv": "https://cdn.simpleicons.org/directv",
    "dish": "https://upload.wikimedia.org/wikipedia/commons/5/5e/Dish_Network_logo.svg",
    "tivo": "https://cdn.simpleicons.org/tivo",
    "google": "https://cdn.simpleicons.org/google",
}


# =============================================================================
# TELEVISIONS
# =============================================================================

TV_SAMSUNG = CatalogDevice(
    id="tv_samsung", name="Samsung TV", brand="Samsung", category=DeviceCategory.TV,
    control_methods=[ControlMethod.IR, ControlMethod.NETWORK],
    logo_url=BRAND_LOGOS["samsung"],
    ir_codes={
        "power": _samsung(0x07, 0x02), "power_on": _samsung(0x07, 0x02), "power_off": _samsung(0x07, 0x02),
        "vol_up": _samsung(0x07, 0x07), "vol_down": _samsung(0x07, 0x0B), "mute": _samsung(0x07, 0x0F),
        "ch_up": _samsung(0x07, 0x12), "ch_down": _samsung(0x07, 0x10),
        "input": _samsung(0x07, 0x01), "hdmi1": _samsung(0x07, 0x69), "hdmi2": _samsung(0x07, 0x68),
        "hdmi3": _samsung(0x07, 0x6A), "hdmi4": _samsung(0x07, 0x6B),
        "menu": _samsung(0x07, 0x1A), "home": _samsung(0x07, 0x79), "back": _samsung(0x07, 0x58),
        "up": _samsung(0x07, 0x60), "down": _samsung(0x07, 0x61), "left": _samsung(0x07, 0x65),
        "right": _samsung(0x07, 0x62), "enter": _samsung(0x07, 0x68),
        "0": _samsung(0x07, 0x11), "1": _samsung(0x07, 0x04), "2": _samsung(0x07, 0x05),
        "3": _samsung(0x07, 0x06), "4": _samsung(0x07, 0x08), "5": _samsung(0x07, 0x09),
        "6": _samsung(0x07, 0x0A), "7": _samsung(0x07, 0x0C), "8": _samsung(0x07, 0x0D), "9": _samsung(0x07, 0x0E),
    },
)

TV_LG = CatalogDevice(
    id="tv_lg", name="LG TV", brand="LG", category=DeviceCategory.TV,
    control_methods=[ControlMethod.IR, ControlMethod.NETWORK],
    logo_url=BRAND_LOGOS["lg"],
    ir_codes={
        "power": _nec(0x04, 0x08), "vol_up": _nec(0x04, 0x02), "vol_down": _nec(0x04, 0x03),
        "mute": _nec(0x04, 0x09), "ch_up": _nec(0x04, 0x00), "ch_down": _nec(0x04, 0x01),
        "input": _nec(0x04, 0x0B), "hdmi1": _nec(0x04, 0xCE), "hdmi2": _nec(0x04, 0xCC), "hdmi3": _nec(0x04, 0xE9),
        "menu": _nec(0x04, 0x43), "home": _nec(0x04, 0x7C), "back": _nec(0x04, 0x28),
        "up": _nec(0x04, 0x40), "down": _nec(0x04, 0x41), "left": _nec(0x04, 0x07),
        "right": _nec(0x04, 0x06), "enter": _nec(0x04, 0x44),
        "0": _nec(0x04, 0x10), "1": _nec(0x04, 0x11), "2": _nec(0x04, 0x12), "3": _nec(0x04, 0x13),
        "4": _nec(0x04, 0x14), "5": _nec(0x04, 0x15), "6": _nec(0x04, 0x16),
        "7": _nec(0x04, 0x17), "8": _nec(0x04, 0x18), "9": _nec(0x04, 0x19),
    },
)

TV_SONY = CatalogDevice(
    id="tv_sony", name="Sony TV", brand="Sony", category=DeviceCategory.TV,
    control_methods=[ControlMethod.IR, ControlMethod.NETWORK],
    logo_url=BRAND_LOGOS["sony"],
    ir_codes={
        "power": _sony(0x01, 0x15), "power_on": _sony(0x01, 0x2E), "power_off": _sony(0x01, 0x2F),
        "vol_up": _sony(0x01, 0x12), "vol_down": _sony(0x01, 0x13), "mute": _sony(0x01, 0x14),
        "ch_up": _sony(0x01, 0x10), "ch_down": _sony(0x01, 0x11), "input": _sony(0x01, 0x25),
        "hdmi1": _sony(0x01, 0x49), "hdmi2": _sony(0x01, 0x4A), "hdmi3": _sony(0x01, 0x4B), "hdmi4": _sony(0x01, 0x4C),
        "menu": _sony(0x01, 0x60), "home": _sony(0x01, 0x60), "back": _sony(0x01, 0x63),
        "up": _sony(0x01, 0x74), "down": _sony(0x01, 0x75), "left": _sony(0x01, 0x34), "right": _sony(0x01, 0x33),
        "enter": _sony(0x01, 0x65),
    },
)

TV_VIZIO = CatalogDevice(
    id="tv_vizio", name="Vizio TV", brand="Vizio", category=DeviceCategory.TV,
    control_methods=[ControlMethod.IR, ControlMethod.NETWORK],
    logo_url=BRAND_LOGOS["vizio"],
    ir_codes={
        "power": _nec(0x04, 0x08), "vol_up": _nec(0x04, 0x02), "vol_down": _nec(0x04, 0x03),
        "mute": _nec(0x04, 0x09), "ch_up": _nec(0x04, 0x00), "ch_down": _nec(0x04, 0x01),
        "input": _nec(0x04, 0x0B), "menu": _nec(0x04, 0x43), "home": _nec(0x04, 0xD2),
        "back": _nec(0x04, 0x28), "up": _nec(0x04, 0x40), "down": _nec(0x04, 0x41),
        "left": _nec(0x04, 0x07), "right": _nec(0x04, 0x06), "enter": _nec(0x04, 0x44),
    },
)

TV_TCL = CatalogDevice(
    id="tv_tcl", name="TCL Roku TV", brand="TCL", category=DeviceCategory.TV,
    control_methods=[ControlMethod.IR, ControlMethod.NETWORK],
    logo_url=BRAND_LOGOS["roku"],
    ir_codes={
        "power": _nec(0xAA, 0x8D), "vol_up": _nec(0xAA, 0x84), "vol_down": _nec(0xAA, 0x85),
        "mute": _nec(0xAA, 0x8C), "home": _nec(0xAA, 0x8E), "back": _nec(0xAA, 0x83),
        "up": _nec(0xAA, 0x9A), "down": _nec(0xAA, 0x9B), "left": _nec(0xAA, 0x9C),
        "right": _nec(0xAA, 0x9D), "enter": _nec(0xAA, 0x9E),
    },
)

TV_HISENSE = CatalogDevice(
    id="tv_hisense", name="Hisense TV", brand="Hisense", category=DeviceCategory.TV,
    control_methods=[ControlMethod.IR],
    ir_codes={
        "power": _nec(0x04, 0x08), "vol_up": _nec(0x04, 0x02), "vol_down": _nec(0x04, 0x03),
        "mute": _nec(0x04, 0x09), "ch_up": _nec(0x04, 0x00), "ch_down": _nec(0x04, 0x01),
        "input": _nec(0x04, 0x0B), "menu": _nec(0x04, 0x43), "home": _nec(0x04, 0x7C),
        "back": _nec(0x04, 0x28), "up": _nec(0x04, 0x40), "down": _nec(0x04, 0x41),
        "left": _nec(0x04, 0x07), "right": _nec(0x04, 0x06), "enter": _nec(0x04, 0x44),
    },
)

TV_PHILIPS = CatalogDevice(
    id="tv_philips", name="Philips TV", brand="Philips", category=DeviceCategory.TV,
    control_methods=[ControlMethod.IR],
    logo_url=BRAND_LOGOS["philips"],
    ir_codes={
        "power": _rc6(0x00, 0x0C), "vol_up": _rc6(0x00, 0x10), "vol_down": _rc6(0x00, 0x11),
        "mute": _rc6(0x00, 0x0D), "ch_up": _rc6(0x00, 0x20), "ch_down": _rc6(0x00, 0x21),
        "menu": _rc6(0x00, 0x54), "back": _rc6(0x00, 0x0A), "up": _rc6(0x00, 0x58),
        "down": _rc6(0x00, 0x59), "left": _rc6(0x00, 0x5A), "right": _rc6(0x00, 0x5B), "enter": _rc6(0x00, 0x5C),
    },
)

TV_PANASONIC = CatalogDevice(
    id="tv_panasonic", name="Panasonic TV", brand="Panasonic", category=DeviceCategory.TV,
    control_methods=[ControlMethod.IR],
    logo_url=BRAND_LOGOS["panasonic"],
    ir_codes={
        "power": _nec(0x40, 0x3D), "vol_up": _nec(0x40, 0x20), "vol_down": _nec(0x40, 0x21),
        "mute": _nec(0x40, 0x32), "ch_up": _nec(0x40, 0x34), "ch_down": _nec(0x40, 0x35),
        "input": _nec(0x40, 0xF0), "menu": _nec(0x40, 0x49), "back": _nec(0x40, 0x4B),
        "up": _nec(0x40, 0x52), "down": _nec(0x40, 0x53), "left": _nec(0x40, 0x54),
        "right": _nec(0x40, 0x55), "enter": _nec(0x40, 0x49),
    },
)

TV_SHARP = CatalogDevice(
    id="tv_sharp", name="Sharp TV", brand="Sharp", category=DeviceCategory.TV,
    control_methods=[ControlMethod.IR],
    ir_codes={
        "power": _nec(0x10, 0x16), "vol_up": _nec(0x10, 0x14), "vol_down": _nec(0x10, 0x15),
        "mute": _nec(0x10, 0x17), "ch_up": _nec(0x10, 0x1E), "ch_down": _nec(0x10, 0x1F),
        "input": _nec(0x10, 0x0F), "menu": _nec(0x10, 0x51), "back": _nec(0x10, 0x55),
        "up": _nec(0x10, 0x41), "down": _nec(0x10, 0x42), "left": _nec(0x10, 0x44),
        "right": _nec(0x10, 0x43), "enter": _nec(0x10, 0x52),
    },
)

TV_TOSHIBA = CatalogDevice(
    id="tv_toshiba", name="Toshiba TV", brand="Toshiba", category=DeviceCategory.TV,
    control_methods=[ControlMethod.IR],
    ir_codes={
        "power": _nec(0x40, 0x12), "vol_up": _nec(0x40, 0x1A), "vol_down": _nec(0x40, 0x1E),
        "mute": _nec(0x40, 0x10), "ch_up": _nec(0x40, 0x1B), "ch_down": _nec(0x40, 0x1F),
        "input": _nec(0x40, 0x0F), "menu": _nec(0x40, 0x4D), "back": _nec(0x40, 0x0E),
        "up": _nec(0x40, 0x4B), "down": _nec(0x40, 0x4C), "left": _nec(0x40, 0x49),
        "right": _nec(0x40, 0x4A), "enter": _nec(0x40, 0x4D),
    },
)


# =============================================================================
# AV RECEIVERS / SOUNDBARS
# =============================================================================

AVR_DENON = CatalogDevice(
    id="avr_denon", name="Denon AVR", brand="Denon", category=DeviceCategory.RECEIVER,
    control_methods=[ControlMethod.IR, ControlMethod.NETWORK],
    logo_url=BRAND_LOGOS["denon"],
    ir_codes={
        "power": _nec(0x02, 0x80), "power_on": _nec(0x02, 0x80), "power_off": _nec(0x02, 0x40),
        "vol_up": _nec(0x02, 0x88), "vol_down": _nec(0x02, 0x48), "mute": _nec(0x02, 0x18),
        "input_cbl_sat": _nec(0x02, 0xC0), "input_dvd": _nec(0x02, 0xA0), "input_bluray": _nec(0x02, 0xA0),
        "input_game": _nec(0x02, 0x60), "input_tv": _nec(0x02, 0x20), "input_aux": _nec(0x02, 0xE0),
        "input_media_player": _nec(0x02, 0x30), "input_cd": _nec(0x02, 0x70),
        "surround": _nec(0x02, 0x54), "menu": _nec(0x02, 0xF8),
        "up": _nec(0x02, 0x08), "down": _nec(0x02, 0x88), "left": _nec(0x02, 0xC8),
        "right": _nec(0x02, 0x48), "enter": _nec(0x02, 0x28),
    },
    network_config={"type": "denon_avr", "port": 23},
)

AVR_YAMAHA = CatalogDevice(
    id="avr_yamaha", name="Yamaha AVR", brand="Yamaha", category=DeviceCategory.RECEIVER,
    control_methods=[ControlMethod.IR, ControlMethod.NETWORK],
    logo_url=BRAND_LOGOS["yamaha"],
    ir_codes={
        "power": _nec(0x7A, 0x1F), "power_on": _nec(0x7A, 0x1E), "power_off": _nec(0x7A, 0x1F),
        "vol_up": _nec(0x7A, 0x1A), "vol_down": _nec(0x7A, 0x1B), "mute": _nec(0x7A, 0x1C),
        "input_hdmi1": _nec(0x7A, 0xE1), "input_hdmi2": _nec(0x7A, 0xE2),
        "input_hdmi3": _nec(0x7A, 0xE3), "input_hdmi4": _nec(0x7A, 0xE4),
        "input_av1": _nec(0x7A, 0xC1), "input_av2": _nec(0x7A, 0xC2), "input_tuner": _nec(0x7A, 0x28),
        "surround": _nec(0x7A, 0x07), "menu": _nec(0x7A, 0x4B),
        "up": _nec(0x7A, 0x40), "down": _nec(0x7A, 0x41), "left": _nec(0x7A, 0x42),
        "right": _nec(0x7A, 0x43), "enter": _nec(0x7A, 0x44),
    },
)

AVR_ONKYO = CatalogDevice(
    id="avr_onkyo", name="Onkyo AVR", brand="Onkyo", category=DeviceCategory.RECEIVER,
    control_methods=[ControlMethod.IR, ControlMethod.NETWORK],
    logo_url=BRAND_LOGOS["onkyo"],
    ir_codes={
        "power": _nec(0x4B, 0xB0), "power_on": _nec(0x4B, 0x30), "power_off": _nec(0x4B, 0xB0),
        "vol_up": _nec(0x4B, 0x02), "vol_down": _nec(0x4B, 0x03), "mute": _nec(0x4B, 0x05),
        "input_cbl_sat": _nec(0x4B, 0x90), "input_dvd": _nec(0x4B, 0x31), "input_game": _nec(0x4B, 0xE0),
        "input_tv": _nec(0x4B, 0xA3), "input_aux": _nec(0x4B, 0x04), "input_cd": _nec(0x4B, 0x20),
        "input_strm_box": _nec(0x4B, 0x64), "surround": _nec(0x4B, 0x91),
        "menu": _nec(0x4B, 0xD3), "up": _nec(0x4B, 0x60), "down": _nec(0x4B, 0x61),
        "left": _nec(0x4B, 0x62), "right": _nec(0x4B, 0x63), "enter": _nec(0x4B, 0x64),
    },
)

AVR_MARANTZ = CatalogDevice(
    id="avr_marantz", name="Marantz AVR", brand="Marantz", category=DeviceCategory.RECEIVER,
    control_methods=[ControlMethod.IR, ControlMethod.NETWORK],
    logo_url=BRAND_LOGOS["marantz"],
    ir_codes={
        "power": _nec(0x10, 0x1C), "power_off": _nec(0x10, 0x1D),
        "vol_up": _nec(0x10, 0x10), "vol_down": _nec(0x10, 0x11), "mute": _nec(0x10, 0x12),
        "input_cbl_sat": _nec(0x10, 0x05), "input_dvd": _nec(0x10, 0x04), "input_tv": _nec(0x10, 0x00),
        "menu": _nec(0x10, 0x08), "up": _nec(0x10, 0x52), "down": _nec(0x10, 0x53),
        "left": _nec(0x10, 0x54), "right": _nec(0x10, 0x55), "enter": _nec(0x10, 0x56),
    },
)

AVR_PIONEER = CatalogDevice(
    id="avr_pioneer", name="Pioneer AVR", brand="Pioneer", category=DeviceCategory.RECEIVER,
    control_methods=[ControlMethod.IR],
    ir_codes={
        "power": _nec(0xA5, 0x5A), "vol_up": _nec(0xA5, 0x0A), "vol_down": _nec(0xA5, 0x0B),
        "mute": _nec(0xA5, 0x4B), "input_dvd": _nec(0xA5, 0x19), "input_tv": _nec(0xA5, 0x04),
        "input_cbl_sat": _nec(0xA5, 0x06), "input_game": _nec(0xA5, 0x49),
        "surround": _nec(0xA5, 0x51), "menu": _nec(0xA5, 0x33),
    },
)

SOUNDBAR_BOSE = CatalogDevice(
    id="soundbar_bose", name="Bose Soundbar", brand="Bose", category=DeviceCategory.SOUNDBAR,
    control_methods=[ControlMethod.IR, ControlMethod.BLUETOOTH],
    logo_url=BRAND_LOGOS["bose"],
    ir_codes={
        "power": _nec(0xE0, 0x4C), "vol_up": _nec(0xE0, 0x50), "vol_down": _nec(0xE0, 0x51),
        "mute": _nec(0xE0, 0x4D), "input_tv": _nec(0xE0, 0x02), "input_bluetooth": _nec(0xE0, 0x08),
        "input_aux": _nec(0xE0, 0x09), "bass_up": _nec(0xE0, 0x54), "bass_down": _nec(0xE0, 0x55),
    },
)

SOUNDBAR_SONOS = CatalogDevice(
    id="soundbar_sonos", name="Sonos Soundbar", brand="Sonos", category=DeviceCategory.SOUNDBAR,
    control_methods=[ControlMethod.NETWORK],
    logo_url=BRAND_LOGOS["sonos"],
    network_config={"type": "sonos"},
)

SOUNDBAR_SAMSUNG = CatalogDevice(
    id="soundbar_samsung", name="Samsung Soundbar", brand="Samsung", category=DeviceCategory.SOUNDBAR,
    control_methods=[ControlMethod.IR],
    logo_url=BRAND_LOGOS["samsung"],
    ir_codes={
        "power": _samsung(0x01, 0x0C), "vol_up": _samsung(0x01, 0x07), "vol_down": _samsung(0x01, 0x0B),
        "mute": _samsung(0x01, 0x0F), "input": _samsung(0x01, 0x01), "sound_mode": _samsung(0x01, 0x53),
    },
)


# =============================================================================
# STREAMING DEVICES / MEDIA PLAYERS
# =============================================================================

STREAMER_ROKU = CatalogDevice(
    id="streamer_roku", name="Roku Streaming", brand="Roku", category=DeviceCategory.STREAMER,
    control_methods=[ControlMethod.IR, ControlMethod.NETWORK],
    logo_url=BRAND_LOGOS["roku"],
    ir_codes={
        "power": _nec(0xEE, 0x8D), "home": _nec(0xEE, 0x8E), "back": _nec(0xEE, 0x83),
        "up": _nec(0xEE, 0x9A), "down": _nec(0xEE, 0x9B), "left": _nec(0xEE, 0x9C),
        "right": _nec(0xEE, 0x9D), "enter": _nec(0xEE, 0x9E),
        "play": _nec(0xEE, 0x8F), "pause": _nec(0xEE, 0x8F), "rev": _nec(0xEE, 0x8B),
        "fwd": _nec(0xEE, 0x8A), "replay": _nec(0xEE, 0x86), "options": _nec(0xEE, 0x82),
        "netflix": _nec(0xEE, 0x96), "disney": _nec(0xEE, 0x99), "hulu": _nec(0xEE, 0x97),
    },
    network_config={"type": "roku", "port": 8060},
    apps={"Netflix": "12", "Hulu": "2285", "Disney+": "291097", "YouTube": "837", "Prime Video": "13"},
)

STREAMER_FIRETV = CatalogDevice(
    id="streamer_firetv", name="Amazon Fire TV", brand="Amazon", category=DeviceCategory.STREAMER,
    control_methods=[ControlMethod.IR, ControlMethod.NETWORK],
    logo_url=BRAND_LOGOS["amazon"],
    ir_codes={
        "power": _nec(0x40, 0x01), "home": _nec(0x40, 0x1E), "back": _nec(0x40, 0x23),
        "up": _nec(0x40, 0x1A), "down": _nec(0x40, 0x1B), "left": _nec(0x40, 0x18),
        "right": _nec(0x40, 0x19), "enter": _nec(0x40, 0x1F),
        "menu": _nec(0x40, 0x0A), "play": _nec(0x40, 0x16), "pause": _nec(0x40, 0x16),
        "rev": _nec(0x40, 0x14), "fwd": _nec(0x40, 0x15),
    },
    network_config={"type": "androidtv"},
)

STREAMER_APPLETV = CatalogDevice(
    id="streamer_appletv", name="Apple TV", brand="Apple", category=DeviceCategory.STREAMER,
    control_methods=[ControlMethod.IR, ControlMethod.NETWORK],
    logo_url=BRAND_LOGOS["apple"],
    ir_codes={
        "menu": _nec(0xEE, 0x03), "up": _nec(0xEE, 0x0A), "down": _nec(0xEE, 0x0C),
        "left": _nec(0xEE, 0x09), "right": _nec(0xEE, 0x06), "enter": _nec(0xEE, 0x5F),
        "play": _nec(0xEE, 0x5C), "pause": _nec(0xEE, 0x5C),
    },
    network_config={"type": "appletv"},
)

STREAMER_SHIELD = CatalogDevice(
    id="streamer_shield", name="NVIDIA Shield", brand="NVIDIA", category=DeviceCategory.STREAMER,
    control_methods=[ControlMethod.IR, ControlMethod.NETWORK],
    logo_url=BRAND_LOGOS["nvidia"],
    ir_codes={
        "power": _nec(0x00, 0x18), "home": _nec(0x00, 0x0D), "back": _nec(0x00, 0x11),
        "up": _nec(0x00, 0x06), "down": _nec(0x00, 0x07), "left": _nec(0x00, 0x08),
        "right": _nec(0x00, 0x09), "enter": _nec(0x00, 0x10),
        "play": _nec(0x00, 0x05), "pause": _nec(0x00, 0x05),
    },
    network_config={"type": "androidtv"},
)

STREAMER_CHROMECAST = CatalogDevice(
    id="streamer_chromecast", name="Chromecast with Google TV", brand="Google", category=DeviceCategory.STREAMER,
    control_methods=[ControlMethod.NETWORK, ControlMethod.HDMI_CEC],
    logo_url=BRAND_LOGOS["google"],
    network_config={"type": "androidtv"},
)


# =============================================================================
# GAMING CONSOLES
# =============================================================================

CONSOLE_XBOX = CatalogDevice(
    id="console_xbox", name="Xbox Series X/S", brand="Microsoft", category=DeviceCategory.GAME_CONSOLE,
    control_methods=[ControlMethod.IR, ControlMethod.NETWORK, ControlMethod.HDMI_CEC],
    logo_url=BRAND_LOGOS["xbox"],
    ir_codes={
        "power": _rc6(0x80, 0x0C), "guide": _rc6(0x80, 0x83), "menu": _rc6(0x80, 0x0D),
        "up": _rc6(0x80, 0x58), "down": _rc6(0x80, 0x59), "left": _rc6(0x80, 0x5A),
        "right": _rc6(0x80, 0x5B), "enter": _rc6(0x80, 0x5C),
        "back": _rc6(0x80, 0x83), "view": _rc6(0x80, 0x24),
        "play": _rc6(0x80, 0x2C), "pause": _rc6(0x80, 0x30), "stop": _rc6(0x80, 0x31),
        "fwd": _rc6(0x80, 0x28), "rev": _rc6(0x80, 0x29),
    },
)

CONSOLE_PS5 = CatalogDevice(
    id="console_ps5", name="PlayStation 5", brand="Sony", category=DeviceCategory.GAME_CONSOLE,
    control_methods=[ControlMethod.NETWORK, ControlMethod.HDMI_CEC, ControlMethod.BLUETOOTH],
    logo_url=BRAND_LOGOS["playstation"],
    network_config={"type": "ps5"},
)

CONSOLE_SWITCH = CatalogDevice(
    id="console_switch", name="Nintendo Switch", brand="Nintendo", category=DeviceCategory.GAME_CONSOLE,
    control_methods=[ControlMethod.HDMI_CEC],
    logo_url=BRAND_LOGOS["nintendo"],
)


# =============================================================================
# PROJECTORS
# =============================================================================

PROJ_EPSON = CatalogDevice(
    id="proj_epson", name="Epson Projector", brand="Epson", category=DeviceCategory.PROJECTOR,
    control_methods=[ControlMethod.IR, ControlMethod.NETWORK],
    logo_url=BRAND_LOGOS["epson"],
    ir_codes={
        "power": _nec(0x54, 0x00), "power_on": _nec(0x54, 0x00), "power_off": _nec(0x54, 0x04),
        "input": _nec(0x54, 0x0D), "hdmi1": _nec(0x54, 0x80), "hdmi2": _nec(0x54, 0x8F),
        "menu": _nec(0x54, 0x03), "back": _nec(0x54, 0x06),
        "up": _nec(0x54, 0x35), "down": _nec(0x54, 0x36), "left": _nec(0x54, 0x37),
        "right": _nec(0x54, 0x38), "enter": _nec(0x54, 0x16),
        "lens": _nec(0x54, 0x50), "aspect": _nec(0x54, 0x54), "blank": _nec(0x54, 0x2D),
    },
    network_config={"type": "epson_projector", "port": 3629},
)

PROJ_BENQ = CatalogDevice(
    id="proj_benq", name="BenQ Projector", brand="BenQ", category=DeviceCategory.PROJECTOR,
    control_methods=[ControlMethod.IR, ControlMethod.NETWORK],
    logo_url=BRAND_LOGOS["benq"],
    ir_codes={
        "power": _nec(0x30, 0x00), "power_on": _nec(0x30, 0x00), "power_off": _nec(0x30, 0x09),
        "input": _nec(0x30, 0x06), "hdmi1": _nec(0x30, 0x1F), "hdmi2": _nec(0x30, 0x47),
        "menu": _nec(0x30, 0x07), "back": _nec(0x30, 0x03),
        "up": _nec(0x30, 0x16), "down": _nec(0x30, 0x17), "left": _nec(0x30, 0x14),
        "right": _nec(0x30, 0x15), "enter": _nec(0x30, 0x13),
        "blank": _nec(0x30, 0x1C), "aspect": _nec(0x30, 0x59), "eco": _nec(0x30, 0x5C),
    },
    network_config={"type": "benq_projector", "port": 4352},
)

PROJ_OPTOMA = CatalogDevice(
    id="proj_optoma", name="Optoma Projector", brand="Optoma", category=DeviceCategory.PROJECTOR,
    control_methods=[ControlMethod.IR, ControlMethod.NETWORK],
    logo_url=BRAND_LOGOS["optoma"],
    ir_codes={
        "power": _nec(0x54, 0x10), "power_on": _nec(0x54, 0x10), "power_off": _nec(0x54, 0x11),
        "input": _nec(0x54, 0x01), "hdmi": _nec(0x54, 0x08), "vga": _nec(0x54, 0x0F),
        "menu": _nec(0x54, 0x03), "back": _nec(0x54, 0x06),
        "up": _nec(0x54, 0x40), "down": _nec(0x54, 0x41), "left": _nec(0x54, 0x42),
        "right": _nec(0x54, 0x43), "enter": _nec(0x54, 0x44),
        "blank": _nec(0x54, 0x05),
    },
)

PROJ_SONY = CatalogDevice(
    id="proj_sony", name="Sony Projector", brand="Sony", category=DeviceCategory.PROJECTOR,
    control_methods=[ControlMethod.IR, ControlMethod.NETWORK],
    logo_url=BRAND_LOGOS["sony"],
    ir_codes={
        "power": _sony(0xA4, 0x15), "power_on": _sony(0xA4, 0x2E), "power_off": _sony(0xA4, 0x2F),
        "input": _sony(0xA4, 0x25), "hdmi1": _sony(0xA4, 0x49), "hdmi2": _sony(0xA4, 0x4A),
        "menu": _sony(0xA4, 0x60), "back": _sony(0xA4, 0x63),
        "up": _sony(0xA4, 0x74), "down": _sony(0xA4, 0x75), "left": _sony(0xA4, 0x34),
        "right": _sony(0xA4, 0x33), "enter": _sony(0xA4, 0x65),
        "lens": _sony(0xA4, 0x1A), "picture": _sony(0xA4, 0x3F),
    },
)

PROJ_JVC = CatalogDevice(
    id="proj_jvc", name="JVC Projector", brand="JVC", category=DeviceCategory.PROJECTOR,
    control_methods=[ControlMethod.IR, ControlMethod.NETWORK],
    ir_codes={
        "power": _nec(0x50, 0x50), "power_on": _nec(0x50, 0x37), "power_off": _nec(0x50, 0x38),
        "input": _nec(0x50, 0x08), "hdmi1": _nec(0x50, 0x70), "hdmi2": _nec(0x50, 0x71),
        "menu": _nec(0x50, 0x2E), "back": _nec(0x50, 0x03),
        "up": _nec(0x50, 0x01), "down": _nec(0x50, 0x02), "left": _nec(0x50, 0x36),
        "right": _nec(0x50, 0x34), "enter": _nec(0x50, 0x2F),
        "lens": _nec(0x50, 0x30), "picture": _nec(0x50, 0x7C),
    },
)


# =============================================================================
# CABLE / SATELLITE
# =============================================================================

CABLE_DIRECTV = CatalogDevice(
    id="cable_directv", name="DirecTV", brand="DirecTV", category=DeviceCategory.CABLE,
    control_methods=[ControlMethod.IR, ControlMethod.NETWORK],
    logo_url=BRAND_LOGOS["directv"],
    ir_codes={
        "power": _nec(0x60, 0x10), "guide": _nec(0x60, 0x43), "menu": _nec(0x60, 0x82),
        "exit": _nec(0x60, 0x53), "info": _nec(0x60, 0x84),
        "ch_up": _nec(0x60, 0x20), "ch_down": _nec(0x60, 0x21),
        "up": _nec(0x60, 0x58), "down": _nec(0x60, 0x59), "left": _nec(0x60, 0x5A),
        "right": _nec(0x60, 0x5B), "enter": _nec(0x60, 0x5C),
        "play": _nec(0x60, 0x2C), "pause": _nec(0x60, 0x30), "stop": _nec(0x60, 0x31),
        "record": _nec(0x60, 0x37), "fwd": _nec(0x60, 0x28), "rev": _nec(0x60, 0x29),
        "0": _nec(0x60, 0x00), "1": _nec(0x60, 0x01), "2": _nec(0x60, 0x02), "3": _nec(0x60, 0x03),
        "4": _nec(0x60, 0x04), "5": _nec(0x60, 0x05), "6": _nec(0x60, 0x06),
        "7": _nec(0x60, 0x07), "8": _nec(0x60, 0x08), "9": _nec(0x60, 0x09),
    },
)

CABLE_DISH = CatalogDevice(
    id="cable_dish", name="Dish Network", brand="Dish", category=DeviceCategory.CABLE,
    control_methods=[ControlMethod.IR],
    logo_url=BRAND_LOGOS["dish"],
    ir_codes={
        "power": _nec(0x00, 0x00), "guide": _nec(0x00, 0x43), "menu": _nec(0x00, 0x82),
        "exit": _nec(0x00, 0x53), "info": _nec(0x00, 0x84),
        "ch_up": _nec(0x00, 0x20), "ch_down": _nec(0x00, 0x21),
        "up": _nec(0x00, 0x58), "down": _nec(0x00, 0x59), "left": _nec(0x00, 0x5A),
        "right": _nec(0x00, 0x5B), "enter": _nec(0x00, 0x5C),
        "dvr": _nec(0x00, 0x48), "play": _nec(0x00, 0x2C), "pause": _nec(0x00, 0x30),
        "record": _nec(0x00, 0x37), "fwd": _nec(0x00, 0x28), "rev": _nec(0x00, 0x29),
    },
)

CABLE_TIVO = CatalogDevice(
    id="cable_tivo", name="TiVo", brand="TiVo", category=DeviceCategory.DVR,
    control_methods=[ControlMethod.IR, ControlMethod.NETWORK],
    logo_url=BRAND_LOGOS["tivo"],
    ir_codes={
        "power": _nec(0x54, 0x10), "tivo": _nec(0x54, 0x11), "guide": _nec(0x54, 0x12),
        "live_tv": _nec(0x54, 0x13), "info": _nec(0x54, 0x14),
        "ch_up": _nec(0x54, 0x20), "ch_down": _nec(0x54, 0x21),
        "up": _nec(0x54, 0x58), "down": _nec(0x54, 0x59), "left": _nec(0x54, 0x5A),
        "right": _nec(0x54, 0x5B), "enter": _nec(0x54, 0x5C),
        "thumbs_up": _nec(0x54, 0x1A), "thumbs_down": _nec(0x54, 0x1B),
        "play": _nec(0x54, 0x2C), "pause": _nec(0x54, 0x30), "stop": _nec(0x54, 0x31),
        "record": _nec(0x54, 0x37), "fwd": _nec(0x54, 0x28), "rev": _nec(0x54, 0x29),
        "skip_back": _nec(0x54, 0x1E), "skip_fwd": _nec(0x54, 0x1F),
    },
)


# =============================================================================
# DVD / BLU-RAY PLAYERS
# =============================================================================

BLURAY_SONY = CatalogDevice(
    id="bluray_sony", name="Sony Blu-ray", brand="Sony", category=DeviceCategory.BLURAY,
    control_methods=[ControlMethod.IR],
    logo_url=BRAND_LOGOS["sony"],
    ir_codes={
        "power": _sony(0x1A, 0x15), "eject": _sony(0x1A, 0x16), "home": _sony(0x1A, 0x42),
        "up": _sony(0x1A, 0x39), "down": _sony(0x1A, 0x3A), "left": _sony(0x1A, 0x3B),
        "right": _sony(0x1A, 0x3C), "enter": _sony(0x1A, 0x3D),
        "play": _sony(0x1A, 0x32), "pause": _sony(0x1A, 0x39), "stop": _sony(0x1A, 0x38),
        "fwd": _sony(0x1A, 0x33), "rev": _sony(0x1A, 0x34),
        "prev": _sony(0x1A, 0x30), "next": _sony(0x1A, 0x31),
    },
)

BLURAY_SAMSUNG = CatalogDevice(
    id="bluray_samsung", name="Samsung Blu-ray", brand="Samsung", category=DeviceCategory.BLURAY,
    control_methods=[ControlMethod.IR],
    logo_url=BRAND_LOGOS["samsung"],
    ir_codes={
        "power": _samsung(0x32, 0x0C), "eject": _samsung(0x32, 0x1B),
        "up": _samsung(0x32, 0x60), "down": _samsung(0x32, 0x61), "left": _samsung(0x32, 0x65),
        "right": _samsung(0x32, 0x62), "enter": _samsung(0x32, 0x68),
        "play": _samsung(0x32, 0x47), "pause": _samsung(0x32, 0x4A), "stop": _samsung(0x32, 0x46),
        "fwd": _samsung(0x32, 0x48), "rev": _samsung(0x32, 0x45),
        "prev": _samsung(0x32, 0x55), "next": _samsung(0x32, 0x4F),
        "menu": _samsung(0x32, 0x79), "popup": _samsung(0x32, 0x59),
    },
)

BLURAY_LG = CatalogDevice(
    id="bluray_lg", name="LG Blu-ray", brand="LG", category=DeviceCategory.BLURAY,
    control_methods=[ControlMethod.IR],
    logo_url=BRAND_LOGOS["lg"],
    ir_codes={
        "power": _nec(0x30, 0x08), "eject": _nec(0x30, 0x16),
        "up": _nec(0x30, 0x40), "down": _nec(0x30, 0x41), "left": _nec(0x30, 0x07),
        "right": _nec(0x30, 0x06), "enter": _nec(0x30, 0x44),
        "play": _nec(0x30, 0x0B), "pause": _nec(0x30, 0x1D), "stop": _nec(0x30, 0x0D),
        "fwd": _nec(0x30, 0x0E), "rev": _nec(0x30, 0x0F),
        "home": _nec(0x30, 0xAB), "popup": _nec(0x30, 0x1A),
    },
)

BLURAY_PANASONIC = CatalogDevice(
    id="bluray_panasonic", name="Panasonic Blu-ray", brand="Panasonic", category=DeviceCategory.BLURAY,
    control_methods=[ControlMethod.IR],
    logo_url=BRAND_LOGOS["panasonic"],
    ir_codes={
        "power": _nec(0x50, 0x3D), "eject": _nec(0x50, 0x24),
        "up": _nec(0x50, 0x52), "down": _nec(0x50, 0x53), "left": _nec(0x50, 0x54),
        "right": _nec(0x50, 0x55), "enter": _nec(0x50, 0x49),
        "play": _nec(0x50, 0x04), "pause": _nec(0x50, 0x06), "stop": _nec(0x50, 0x00),
        "fwd": _nec(0x50, 0x4A), "rev": _nec(0x50, 0x4B),
        "home": _nec(0x50, 0xD0), "popup": _nec(0x50, 0x56),
    },
)


# =============================================================================
# DEVICE CATALOG INDEX
# =============================================================================

DEVICE_CATALOG: dict[str, CatalogDevice] = {
    # TVs
    "tv_samsung": TV_SAMSUNG,
    "tv_lg": TV_LG,
    "tv_sony": TV_SONY,
    "tv_vizio": TV_VIZIO,
    "tv_tcl": TV_TCL,
    "tv_hisense": TV_HISENSE,
    "tv_philips": TV_PHILIPS,
    "tv_panasonic": TV_PANASONIC,
    "tv_sharp": TV_SHARP,
    "tv_toshiba": TV_TOSHIBA,
    
    # Receivers / Soundbars
    "avr_denon": AVR_DENON,
    "avr_yamaha": AVR_YAMAHA,
    "avr_onkyo": AVR_ONKYO,
    "avr_marantz": AVR_MARANTZ,
    "avr_pioneer": AVR_PIONEER,
    "soundbar_bose": SOUNDBAR_BOSE,
    "soundbar_sonos": SOUNDBAR_SONOS,
    "soundbar_samsung": SOUNDBAR_SAMSUNG,
    
    # Streaming / Media Players
    "streamer_roku": STREAMER_ROKU,
    "streamer_firetv": STREAMER_FIRETV,
    "streamer_appletv": STREAMER_APPLETV,
    "streamer_shield": STREAMER_SHIELD,
    "streamer_chromecast": STREAMER_CHROMECAST,
    
    # Gaming
    "console_xbox": CONSOLE_XBOX,
    "console_ps5": CONSOLE_PS5,
    "console_switch": CONSOLE_SWITCH,
    
    # Projectors
    "proj_epson": PROJ_EPSON,
    "proj_benq": PROJ_BENQ,
    "proj_optoma": PROJ_OPTOMA,
    "proj_sony": PROJ_SONY,
    "proj_jvc": PROJ_JVC,
    
    # Cable / Satellite
    "cable_directv": CABLE_DIRECTV,
    "cable_dish": CABLE_DISH,
    "cable_tivo": CABLE_TIVO,
    
    # Blu-ray / DVD
    "bluray_sony": BLURAY_SONY,
    "bluray_samsung": BLURAY_SAMSUNG,
    "bluray_lg": BLURAY_LG,
    "bluray_panasonic": BLURAY_PANASONIC,
}


# Indexes for searching
CATALOG_BY_CATEGORY: dict[str, list[CatalogDevice]] = {}
CATALOG_BY_BRAND: dict[str, list[CatalogDevice]] = {}

for device in DEVICE_CATALOG.values():
    # By category
    cat = device.category.value
    if cat not in CATALOG_BY_CATEGORY:
        CATALOG_BY_CATEGORY[cat] = []
    CATALOG_BY_CATEGORY[cat].append(device)
    
    # By brand
    brand = device.brand.lower()
    if brand not in CATALOG_BY_BRAND:
        CATALOG_BY_BRAND[brand] = []
    CATALOG_BY_BRAND[brand].append(device)


def get_catalog_device(device_id: str) -> CatalogDevice | None:
    """Get a catalog device by ID."""
    return DEVICE_CATALOG.get(device_id)


def search_catalog(query: str) -> list[CatalogDevice]:
    """Search catalog by name, brand, or category."""
    query = query.lower()
    results = []
    for device in DEVICE_CATALOG.values():
        if (query in device.name.lower() or
            query in device.brand.lower() or
            query in device.category.value.lower()):
            results.append(device)
    return results


def list_catalog() -> list[dict]:
    """List all catalog devices as dicts."""
    return [d.to_dict() for d in DEVICE_CATALOG.values()]
