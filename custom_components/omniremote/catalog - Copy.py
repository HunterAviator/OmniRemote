"""Pre-built device catalog with IR, RF, Network, and Bluetooth codes."""
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
    
    # App/Channel definitions for smart devices
    apps: dict[str, str] = field(default_factory=dict)  # name -> app_id
    channels: dict[str, str] = field(default_factory=dict)  # name -> channel_id
    
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
        }


# =============================================================================
# IR CODE HELPERS
# =============================================================================

def _nec_code(address: int, command: int, name: str = "") -> RemoteCode:
    """Create an NEC protocol IR code."""
    return RemoteCode(
        name=name,
        code_type=CodeType.IR_PARSED,
        protocol="NEC",
        address=f"{address:02X} 00 00 00",
        command=f"{command:02X} 00 00 00",
    )

def _samsung_code(address: int, command: int, name: str = "") -> RemoteCode:
    """Create a Samsung protocol IR code."""
    return RemoteCode(
        name=name,
        code_type=CodeType.IR_PARSED,
        protocol="Samsung32",
        address=f"{address:02X} 00 00 00",
        command=f"{command:02X} 00 00 00",
    )

def _rc5_code(address: int, command: int, name: str = "") -> RemoteCode:
    """Create an RC5 protocol IR code."""
    return RemoteCode(
        name=name,
        code_type=CodeType.IR_PARSED,
        protocol="RC5",
        address=f"{address:02X} 00 00 00",
        command=f"{command:02X} 00 00 00",
    )

def _rc6_code(address: int, command: int, name: str = "") -> RemoteCode:
    """Create an RC6 protocol IR code."""
    return RemoteCode(
        name=name,
        code_type=CodeType.IR_PARSED,
        protocol="RC6",
        address=f"{address:02X} 00 00 00",
        command=f"{command:02X} 00 00 00",
    )

def _raw_ir_code(frequency: int, data: list[int], name: str = "") -> RemoteCode:
    """Create a raw IR code."""
    return RemoteCode(
        name=name,
        code_type=CodeType.IR_RAW,
        frequency=frequency,
        raw_data=data,
    )


# =============================================================================
# SAMSUNG TV
# =============================================================================

SAMSUNG_TV = CatalogDevice(
    id="samsung_tv",
    name="Samsung TV",
    brand="Samsung",
    category=DeviceCategory.TV,
    control_methods=[ControlMethod.IR, ControlMethod.NETWORK],
    ir_codes={
        "power": _samsung_code(0x07, 0x02, "power"),
        "power_on": _samsung_code(0x07, 0x02, "power_on"),
        "power_off": _samsung_code(0x07, 0x98, "power_off"),
        "volume_up": _samsung_code(0x07, 0x07, "volume_up"),
        "volume_down": _samsung_code(0x07, 0x0B, "volume_down"),
        "mute": _samsung_code(0x07, 0x0F, "mute"),
        "channel_up": _samsung_code(0x07, 0x12, "channel_up"),
        "channel_down": _samsung_code(0x07, 0x10, "channel_down"),
        "source": _samsung_code(0x07, 0x01, "source"),
        "hdmi1": _samsung_code(0x07, 0x52, "hdmi1"),
        "hdmi2": _samsung_code(0x07, 0x54, "hdmi2"),
        "hdmi3": _samsung_code(0x07, 0x55, "hdmi3"),
        "hdmi4": _samsung_code(0x07, 0x56, "hdmi4"),
        "component": _samsung_code(0x07, 0x42, "component"),
        "av": _samsung_code(0x07, 0x5C, "av"),
        "tv": _samsung_code(0x07, 0x44, "tv"),
        "up": _samsung_code(0x07, 0x60, "up"),
        "down": _samsung_code(0x07, 0x61, "down"),
        "left": _samsung_code(0x07, 0x65, "left"),
        "right": _samsung_code(0x07, 0x62, "right"),
        "enter": _samsung_code(0x07, 0x68, "enter"),
        "return": _samsung_code(0x07, 0x58, "return"),
        "exit": _samsung_code(0x07, 0x2D, "exit"),
        "menu": _samsung_code(0x07, 0x1A, "menu"),
        "home": _samsung_code(0x07, 0x79, "home"),
        "info": _samsung_code(0x07, 0x1F, "info"),
        "guide": _samsung_code(0x07, 0x4F, "guide"),
        "0": _samsung_code(0x07, 0x11, "0"),
        "1": _samsung_code(0x07, 0x04, "1"),
        "2": _samsung_code(0x07, 0x05, "2"),
        "3": _samsung_code(0x07, 0x06, "3"),
        "4": _samsung_code(0x07, 0x08, "4"),
        "5": _samsung_code(0x07, 0x09, "5"),
        "6": _samsung_code(0x07, 0x0A, "6"),
        "7": _samsung_code(0x07, 0x0C, "7"),
        "8": _samsung_code(0x07, 0x0D, "8"),
        "9": _samsung_code(0x07, 0x0E, "9"),
        "play": _samsung_code(0x07, 0x47, "play"),
        "pause": _samsung_code(0x07, 0x46, "pause"),
        "stop": _samsung_code(0x07, 0x45, "stop"),
        "rewind": _samsung_code(0x07, 0x48, "rewind"),
        "fast_forward": _samsung_code(0x07, 0x49, "fast_forward"),
        "red": _samsung_code(0x07, 0x36, "red"),
        "green": _samsung_code(0x07, 0x37, "green"),
        "yellow": _samsung_code(0x07, 0x38, "yellow"),
        "blue": _samsung_code(0x07, 0x39, "blue"),
    },
    network_config={
        "type": "samsung_smartthings",
        "port": 8001,
        "ws_port": 8002,
    },
)


# =============================================================================
# PHILIPS TV
# =============================================================================

PHILIPS_TV = CatalogDevice(
    id="philips_tv",
    name="Philips TV",
    brand="Philips",
    category=DeviceCategory.TV,
    control_methods=[ControlMethod.IR, ControlMethod.NETWORK],
    ir_codes={
        "power": _rc6_code(0x00, 0x0C, "power"),
        "power_on": _rc6_code(0x00, 0x0C, "power_on"),
        "power_off": _rc6_code(0x00, 0x0C, "power_off"),
        "volume_up": _rc6_code(0x00, 0x10, "volume_up"),
        "volume_down": _rc6_code(0x00, 0x11, "volume_down"),
        "mute": _rc6_code(0x00, 0x0D, "mute"),
        "channel_up": _rc6_code(0x00, 0x20, "channel_up"),
        "channel_down": _rc6_code(0x00, 0x21, "channel_down"),
        "source": _rc6_code(0x00, 0x38, "source"),
        "hdmi1": _rc6_code(0x00, 0xD5, "hdmi1"),
        "hdmi2": _rc6_code(0x00, 0xD6, "hdmi2"),
        "hdmi3": _rc6_code(0x00, 0xD7, "hdmi3"),
        "up": _rc6_code(0x00, 0x58, "up"),
        "down": _rc6_code(0x00, 0x59, "down"),
        "left": _rc6_code(0x00, 0x5A, "left"),
        "right": _rc6_code(0x00, 0x5B, "right"),
        "ok": _rc6_code(0x00, 0x5C, "ok"),
        "back": _rc6_code(0x00, 0x0A, "back"),
        "home": _rc6_code(0x00, 0x54, "home"),
        "menu": _rc6_code(0x00, 0x82, "menu"),
        "info": _rc6_code(0x00, 0x0F, "info"),
        "guide": _rc6_code(0x00, 0xCC, "guide"),
        "0": _rc6_code(0x00, 0x00, "0"),
        "1": _rc6_code(0x00, 0x01, "1"),
        "2": _rc6_code(0x00, 0x02, "2"),
        "3": _rc6_code(0x00, 0x03, "3"),
        "4": _rc6_code(0x00, 0x04, "4"),
        "5": _rc6_code(0x00, 0x05, "5"),
        "6": _rc6_code(0x00, 0x06, "6"),
        "7": _rc6_code(0x00, 0x07, "7"),
        "8": _rc6_code(0x00, 0x08, "8"),
        "9": _rc6_code(0x00, 0x09, "9"),
        "play": _rc6_code(0x00, 0x2C, "play"),
        "pause": _rc6_code(0x00, 0x30, "pause"),
        "stop": _rc6_code(0x00, 0x31, "stop"),
        "rewind": _rc6_code(0x00, 0x2B, "rewind"),
        "fast_forward": _rc6_code(0x00, 0x28, "fast_forward"),
        "ambilight": _rc6_code(0x00, 0xE4, "ambilight"),
    },
    network_config={
        "type": "philips_jointspace",
        "port": 1925,
        "api_version": 6,
    },
)


# =============================================================================
# ROKU TV / ROKU DEVICE
# =============================================================================

ROKU_CODES = {
    "power": _nec_code(0xEA, 0x8F, "power"),
    "power_on": _nec_code(0xEA, 0x8E, "power_on"),
    "power_off": _nec_code(0xEA, 0x8F, "power_off"),
    "volume_up": _nec_code(0xEA, 0x80, "volume_up"),
    "volume_down": _nec_code(0xEA, 0x81, "volume_down"),
    "mute": _nec_code(0xEA, 0x82, "mute"),
    "up": _nec_code(0xEA, 0x9A, "up"),
    "down": _nec_code(0xEA, 0x99, "down"),
    "left": _nec_code(0xEA, 0x9B, "left"),
    "right": _nec_code(0xEA, 0x98, "right"),
    "ok": _nec_code(0xEA, 0x8C, "ok"),
    "back": _nec_code(0xEA, 0x83, "back"),
    "home": _nec_code(0xEA, 0x8A, "home"),
    "star": _nec_code(0xEA, 0x97, "star"),
    "rewind": _nec_code(0xEA, 0x8B, "rewind"),
    "fast_forward": _nec_code(0xEA, 0x88, "fast_forward"),
    "play_pause": _nec_code(0xEA, 0x85, "play_pause"),
    "instant_replay": _nec_code(0xEA, 0x86, "instant_replay"),
    "input_tuner": _nec_code(0xEA, 0x96, "input_tuner"),
    "input_hdmi1": _nec_code(0xEA, 0x90, "input_hdmi1"),
    "input_hdmi2": _nec_code(0xEA, 0x91, "input_hdmi2"),
    "input_hdmi3": _nec_code(0xEA, 0x92, "input_hdmi3"),
    "input_hdmi4": _nec_code(0xEA, 0x93, "input_hdmi4"),
    "input_av": _nec_code(0xEA, 0x94, "input_av"),
    "sleep": _nec_code(0xEA, 0x9C, "sleep"),
    "channel_up": _nec_code(0xEA, 0x9E, "channel_up"),
    "channel_down": _nec_code(0xEA, 0x9D, "channel_down"),
}

ROKU_APPS = {
    "Netflix": "12",
    "YouTube": "837",
    "Amazon Prime Video": "13",
    "Disney+": "291097",
    "Hulu": "2285",
    "HBO Max": "61322",
    "Apple TV+": "551012",
    "Peacock": "593099",
    "Paramount+": "31440",
    "Spotify": "22297",
    "Plex": "13535",
    "Tubi": "41468",
    "Pluto TV": "74519",
    "The Roku Channel": "151908",
    "Vudu": "13842",
    "Sling TV": "46041",
    "fuboTV": "180424",
    "ESPN": "34376",
    "MLB.TV": "17151",
}

ROKU_TV = CatalogDevice(
    id="roku_tv",
    name="Roku TV",
    brand="Roku",
    category=DeviceCategory.TV,
    control_methods=[ControlMethod.IR, ControlMethod.NETWORK],
    ir_codes=ROKU_CODES,
    network_config={
        "type": "roku_ecp",
        "port": 8060,
    },
    apps=ROKU_APPS,
)

ROKU_DEVICE = CatalogDevice(
    id="roku_device",
    name="Roku Streaming Device",
    brand="Roku",
    category=DeviceCategory.STREAMING,
    control_methods=[ControlMethod.IR, ControlMethod.NETWORK],
    ir_codes=ROKU_CODES,
    network_config={
        "type": "roku_ecp",
        "port": 8060,
    },
    apps=ROKU_APPS,
)


# =============================================================================
# AMAZON FIRE TV
# =============================================================================

FIRETV_IR_CODES = {
    "power": _nec_code(0x40, 0x1A, "power"),
    "up": _nec_code(0x40, 0x06, "up"),
    "down": _nec_code(0x40, 0x07, "down"),
    "left": _nec_code(0x40, 0x08, "left"),
    "right": _nec_code(0x40, 0x09, "right"),
    "select": _nec_code(0x40, 0x0A, "select"),
    "back": _nec_code(0x40, 0x03, "back"),
    "home": _nec_code(0x40, 0x00, "home"),
    "menu": _nec_code(0x40, 0x02, "menu"),
    "play_pause": _nec_code(0x40, 0x0B, "play_pause"),
    "rewind": _nec_code(0x40, 0x0D, "rewind"),
    "fast_forward": _nec_code(0x40, 0x0C, "fast_forward"),
    "volume_up": _nec_code(0x40, 0x10, "volume_up"),
    "volume_down": _nec_code(0x40, 0x11, "volume_down"),
    "mute": _nec_code(0x40, 0x12, "mute"),
}

FIRETV_APPS = {
    "Netflix": "com.netflix.ninja",
    "YouTube": "com.amazon.firetv.youtube",
    "Amazon Prime Video": "com.amazon.avod",
    "Disney+": "com.disney.disneyplus",
    "Hulu": "com.hulu.plus",
    "HBO Max": "com.hbo.hbomax",
    "Apple TV": "com.apple.atve.amazon.appletv",
    "Peacock": "com.peacocktv.peacockandroid",
    "Paramount+": "com.cbs.ott",
    "Spotify": "com.spotify.tv.android",
    "Plex": "com.plexapp.android",
    "Tubi": "com.tubitv",
    "Pluto TV": "tv.pluto.android",
    "Sling TV": "com.sling",
    "ESPN": "com.espn.score_center",
    "Twitch": "tv.twitch.android.app",
    "Kodi": "org.xbmc.kodi",
    "VLC": "org.videolan.vlc",
}

AMAZON_FIRETV = CatalogDevice(
    id="amazon_firetv",
    name="Amazon Fire TV",
    brand="Amazon",
    category=DeviceCategory.STREAMING,
    control_methods=[ControlMethod.IR, ControlMethod.NETWORK, ControlMethod.BLUETOOTH],
    ir_codes=FIRETV_IR_CODES,
    network_config={
        "type": "android_tv_adb",
        "port": 5555,
    },
    bluetooth_config={
        "type": "amazon_fire_bluetooth",
    },
    apps=FIRETV_APPS,
)


# =============================================================================
# ONKYO RECEIVER
# =============================================================================

ONKYO_RECEIVER = CatalogDevice(
    id="onkyo_receiver",
    name="Onkyo AV Receiver",
    brand="Onkyo",
    category=DeviceCategory.RECEIVER,
    control_methods=[ControlMethod.IR, ControlMethod.NETWORK],
    ir_codes={
        "power": _nec_code(0x4B, 0x36, "power"),
        "power_on": _nec_code(0x4B, 0x37, "power_on"),
        "power_off": _nec_code(0x4B, 0x38, "power_off"),
        "volume_up": _nec_code(0x4B, 0x02, "volume_up"),
        "volume_down": _nec_code(0x4B, 0x03, "volume_down"),
        "mute": _nec_code(0x4B, 0x05, "mute"),
        "input_bd_dvd": _nec_code(0x4B, 0x31, "input_bd_dvd"),
        "input_cbl_sat": _nec_code(0x4B, 0x33, "input_cbl_sat"),
        "input_game": _nec_code(0x4B, 0x32, "input_game"),
        "input_aux": _nec_code(0x4B, 0x2C, "input_aux"),
        "input_tv": _nec_code(0x4B, 0x34, "input_tv"),
        "input_strm_box": _nec_code(0x4B, 0x60, "input_strm_box"),
        "input_cd": _nec_code(0x4B, 0x29, "input_cd"),
        "input_tuner": _nec_code(0x4B, 0x27, "input_tuner"),
        "input_phono": _nec_code(0x4B, 0x23, "input_phono"),
        "input_bluetooth": _nec_code(0x4B, 0x6B, "input_bluetooth"),
        "input_net": _nec_code(0x4B, 0x7D, "input_net"),
        "input_usb": _nec_code(0x4B, 0x70, "input_usb"),
        "listening_mode": _nec_code(0x4B, 0x0E, "listening_mode"),
        "surround_mode": _nec_code(0x4B, 0x0F, "surround_mode"),
        "stereo": _nec_code(0x4B, 0x4D, "stereo"),
        "dolby": _nec_code(0x4B, 0x4B, "dolby"),
        "dts": _nec_code(0x4B, 0x58, "dts"),
        "all_ch_stereo": _nec_code(0x4B, 0x4C, "all_ch_stereo"),
        "up": _nec_code(0x4B, 0x14, "up"),
        "down": _nec_code(0x4B, 0x15, "down"),
        "left": _nec_code(0x4B, 0x16, "left"),
        "right": _nec_code(0x4B, 0x17, "right"),
        "enter": _nec_code(0x4B, 0x13, "enter"),
        "return": _nec_code(0x4B, 0x10, "return"),
        "home": _nec_code(0x4B, 0x0B, "home"),
        "display": _nec_code(0x4B, 0x0D, "display"),
    },
    network_config={
        "type": "onkyo_eiscp",
        "port": 60128,
    },
)


# =============================================================================
# XBOX
# =============================================================================

XBOX = CatalogDevice(
    id="xbox",
    name="Xbox Series X/S",
    brand="Microsoft",
    category=DeviceCategory.STREAMING,
    control_methods=[ControlMethod.IR, ControlMethod.NETWORK],
    ir_codes={
        "power": _nec_code(0x80, 0x0C, "power"),
        "power_on": _nec_code(0x80, 0x0C, "power_on"),
        "power_off": _nec_code(0x80, 0x0D, "power_off"),
        "up": _nec_code(0x80, 0x14, "up"),
        "down": _nec_code(0x80, 0x15, "down"),
        "left": _nec_code(0x80, 0x16, "left"),
        "right": _nec_code(0x80, 0x17, "right"),
        "a": _nec_code(0x80, 0x18, "a"),
        "b": _nec_code(0x80, 0x19, "b"),
        "x": _nec_code(0x80, 0x1A, "x"),
        "y": _nec_code(0x80, 0x1B, "y"),
        "menu": _nec_code(0x80, 0x1C, "menu"),
        "view": _nec_code(0x80, 0x1D, "view"),
        "xbox": _nec_code(0x80, 0x1E, "xbox"),
        "play_pause": _nec_code(0x80, 0x20, "play_pause"),
        "stop": _nec_code(0x80, 0x21, "stop"),
        "rewind": _nec_code(0x80, 0x22, "rewind"),
        "fast_forward": _nec_code(0x80, 0x23, "fast_forward"),
        "skip_back": _nec_code(0x80, 0x24, "skip_back"),
        "skip_forward": _nec_code(0x80, 0x25, "skip_forward"),
    },
    network_config={
        "type": "xbox_smartglass",
        "port": 5050,
    },
    apps={
        "Netflix": "Netflix",
        "YouTube": "YouTube",
        "Amazon Prime Video": "Prime Video",
        "Disney+": "Disney+",
        "Hulu": "Hulu",
        "HBO Max": "HBO Max",
        "Spotify": "Spotify",
        "Plex": "Plex",
        "Twitch": "Twitch",
    },
)


# =============================================================================
# PLAYSTATION
# =============================================================================

PLAYSTATION = CatalogDevice(
    id="playstation",
    name="PlayStation 5",
    brand="Sony",
    category=DeviceCategory.STREAMING,
    control_methods=[ControlMethod.NETWORK, ControlMethod.BLUETOOTH, ControlMethod.HDMI_CEC],
    ir_codes={},  # PS5 doesn't have IR, but PS4 media remote does
    network_config={
        "type": "playstation_psn",
        "port": 9302,
    },
    bluetooth_config={
        "type": "playstation_bluetooth",
    },
    apps={
        "Netflix": "CUSA00127",
        "YouTube": "CUSA01015",
        "Amazon Prime Video": "CUSA00129",
        "Disney+": "CUSA17640",
        "Hulu": "CUSA00133",
        "HBO Max": "CUSA18604",
        "Spotify": "CUSA01780",
        "Plex": "CUSA01178",
        "Twitch": "CUSA04975",
        "Apple TV": "CUSA18693",
    },
)


# =============================================================================
# BENQ PROJECTOR
# =============================================================================

BENQ_PROJECTOR = CatalogDevice(
    id="benq_projector",
    name="BenQ Projector",
    brand="BenQ",
    category=DeviceCategory.PROJECTOR,
    control_methods=[ControlMethod.IR, ControlMethod.NETWORK],
    ir_codes={
        "power": _nec_code(0x00, 0x0D, "power"),
        "power_on": _nec_code(0x00, 0x1B, "power_on"),
        "power_off": _nec_code(0x00, 0x1C, "power_off"),
        "source": _nec_code(0x00, 0x0E, "source"),
        "hdmi1": _nec_code(0x00, 0x41, "hdmi1"),
        "hdmi2": _nec_code(0x00, 0x51, "hdmi2"),
        "vga": _nec_code(0x00, 0x1F, "vga"),
        "component": _nec_code(0x00, 0x20, "component"),
        "video": _nec_code(0x00, 0x21, "video"),
        "usb": _nec_code(0x00, 0x62, "usb"),
        "up": _nec_code(0x00, 0x2B, "up"),
        "down": _nec_code(0x00, 0x2C, "down"),
        "left": _nec_code(0x00, 0x2D, "left"),
        "right": _nec_code(0x00, 0x2E, "right"),
        "enter": _nec_code(0x00, 0x2F, "enter"),
        "menu": _nec_code(0x00, 0x12, "menu"),
        "back": _nec_code(0x00, 0x13, "back"),
        "auto": _nec_code(0x00, 0x08, "auto"),
        "blank": _nec_code(0x00, 0x17, "blank"),
        "freeze": _nec_code(0x00, 0x09, "freeze"),
        "eco_blank": _nec_code(0x00, 0x19, "eco_blank"),
        "aspect": _nec_code(0x00, 0x14, "aspect"),
        "zoom_in": _nec_code(0x00, 0x15, "zoom_in"),
        "zoom_out": _nec_code(0x00, 0x16, "zoom_out"),
        "lens_shift_up": _nec_code(0x00, 0x70, "lens_shift_up"),
        "lens_shift_down": _nec_code(0x00, 0x71, "lens_shift_down"),
        "lens_shift_left": _nec_code(0x00, 0x72, "lens_shift_left"),
        "lens_shift_right": _nec_code(0x00, 0x73, "lens_shift_right"),
        "keystone_up": _nec_code(0x00, 0x32, "keystone_up"),
        "keystone_down": _nec_code(0x00, 0x33, "keystone_down"),
        "picture_mode": _nec_code(0x00, 0x2A, "picture_mode"),
        "brightness_up": _nec_code(0x00, 0x35, "brightness_up"),
        "brightness_down": _nec_code(0x00, 0x36, "brightness_down"),
        "contrast_up": _nec_code(0x00, 0x37, "contrast_up"),
        "contrast_down": _nec_code(0x00, 0x38, "contrast_down"),
        "3d": _nec_code(0x00, 0x50, "3d"),
        "pattern": _nec_code(0x00, 0x10, "pattern"),
        "info": _nec_code(0x00, 0x1A, "info"),
        "lamp_mode": _nec_code(0x00, 0x74, "lamp_mode"),
    },
    network_config={
        "type": "benq_rs232_over_ip",
        "port": 8000,
        "commands": {
            "power_on": "*pow=on#",
            "power_off": "*pow=off#",
            "power_query": "*pow=?#",
            "source_hdmi1": "*sour=hdmi#",
            "source_hdmi2": "*sour=hdmi2#",
            "lamp_hours": "*ltim=?#",
            "model": "*modelname=?#",
        },
    },
)


# =============================================================================
# SHELLY SHADE CONTROLLER (for projector screens)
# =============================================================================

SHELLY_SHADE = CatalogDevice(
    id="shelly_shade",
    name="Shelly Shade Controller",
    brand="Shelly",
    category=DeviceCategory.BLIND,
    control_methods=[ControlMethod.NETWORK, ControlMethod.RF],
    ir_codes={},
    rf_codes={
        # Generic RF codes - will be learned
        "open": RemoteCode(name="open", code_type=CodeType.RF_PARSED, frequency=433920000, protocol="Princeton"),
        "close": RemoteCode(name="close", code_type=CodeType.RF_PARSED, frequency=433920000, protocol="Princeton"),
        "stop": RemoteCode(name="stop", code_type=CodeType.RF_PARSED, frequency=433920000, protocol="Princeton"),
    },
    network_config={
        "type": "shelly_http",
        "endpoints": {
            "open": "/roller/0?go=open",
            "close": "/roller/0?go=close",
            "stop": "/roller/0?go=stop",
            "position": "/roller/0?go=to_pos&roller_pos={pos}",
            "status": "/status",
        },
    },
)


# =============================================================================
# JENSEN RADIO
# =============================================================================

JENSEN_RADIO = CatalogDevice(
    id="jensen_radio",
    name="Jensen Radio",
    brand="Jensen",
    category=DeviceCategory.OTHER,
    control_methods=[ControlMethod.IR],
    ir_codes={
        "power": _nec_code(0x08, 0x00, "power"),
        "volume_up": _nec_code(0x08, 0x03, "volume_up"),
        "volume_down": _nec_code(0x08, 0x07, "volume_down"),
        "mute": _nec_code(0x08, 0x0D, "mute"),
        "source": _nec_code(0x08, 0x0A, "source"),
        "fm": _nec_code(0x08, 0x04, "fm"),
        "am": _nec_code(0x08, 0x05, "am"),
        "aux": _nec_code(0x08, 0x06, "aux"),
        "bluetooth": _nec_code(0x08, 0x0B, "bluetooth"),
        "usb": _nec_code(0x08, 0x0C, "usb"),
        "cd": _nec_code(0x08, 0x08, "cd"),
        "tune_up": _nec_code(0x08, 0x01, "tune_up"),
        "tune_down": _nec_code(0x08, 0x02, "tune_down"),
        "preset_up": _nec_code(0x08, 0x09, "preset_up"),
        "preset_down": _nec_code(0x08, 0x0E, "preset_down"),
        "play": _nec_code(0x08, 0x10, "play"),
        "pause": _nec_code(0x08, 0x11, "pause"),
        "stop": _nec_code(0x08, 0x12, "stop"),
        "skip_forward": _nec_code(0x08, 0x13, "skip_forward"),
        "skip_back": _nec_code(0x08, 0x14, "skip_back"),
        "1": _nec_code(0x08, 0x20, "1"),
        "2": _nec_code(0x08, 0x21, "2"),
        "3": _nec_code(0x08, 0x22, "3"),
        "4": _nec_code(0x08, 0x23, "4"),
        "5": _nec_code(0x08, 0x24, "5"),
        "6": _nec_code(0x08, 0x25, "6"),
        "bass_up": _nec_code(0x08, 0x30, "bass_up"),
        "bass_down": _nec_code(0x08, 0x31, "bass_down"),
        "treble_up": _nec_code(0x08, 0x32, "treble_up"),
        "treble_down": _nec_code(0x08, 0x33, "treble_down"),
        "eq": _nec_code(0x08, 0x34, "eq"),
        "clock": _nec_code(0x08, 0x40, "clock"),
        "sleep": _nec_code(0x08, 0x41, "sleep"),
        "alarm": _nec_code(0x08, 0x42, "alarm"),
    },
)


# =============================================================================
# LED LIGHT STRIP (Generic IR-controlled)
# =============================================================================

LED_STRIP = CatalogDevice(
    id="led_strip",
    name="LED Light Strip",
    brand="Generic",
    category=DeviceCategory.LIGHT,
    control_methods=[ControlMethod.IR, ControlMethod.RF],
    ir_codes={
        "power": _nec_code(0x00, 0x45, "power"),
        "on": _nec_code(0x00, 0x45, "on"),
        "off": _nec_code(0x00, 0x46, "off"),
        "brightness_up": _nec_code(0x00, 0x47, "brightness_up"),
        "brightness_down": _nec_code(0x00, 0x44, "brightness_down"),
        "red": _nec_code(0x00, 0x40, "red"),
        "green": _nec_code(0x00, 0x5E, "green"),
        "blue": _nec_code(0x00, 0x5A, "blue"),
        "white": _nec_code(0x00, 0x41, "white"),
        "orange": _nec_code(0x00, 0x4D, "orange"),
        "yellow": _nec_code(0x00, 0x49, "yellow"),
        "cyan": _nec_code(0x00, 0x56, "cyan"),
        "purple": _nec_code(0x00, 0x52, "purple"),
        "pink": _nec_code(0x00, 0x4E, "pink"),
        "flash": _nec_code(0x00, 0x57, "flash"),
        "strobe": _nec_code(0x00, 0x53, "strobe"),
        "fade": _nec_code(0x00, 0x4F, "fade"),
        "smooth": _nec_code(0x00, 0x4B, "smooth"),
        "jump3": _nec_code(0x00, 0x43, "jump3"),
        "jump7": _nec_code(0x00, 0x42, "jump7"),
        "diy1": _nec_code(0x00, 0x1E, "diy1"),
        "diy2": _nec_code(0x00, 0x1F, "diy2"),
        "diy3": _nec_code(0x00, 0x20, "diy3"),
        "diy4": _nec_code(0x00, 0x21, "diy4"),
        "diy5": _nec_code(0x00, 0x22, "diy5"),
        "diy6": _nec_code(0x00, 0x23, "diy6"),
        "red_up": _nec_code(0x00, 0x14, "red_up"),
        "red_down": _nec_code(0x00, 0x10, "red_down"),
        "green_up": _nec_code(0x00, 0x15, "green_up"),
        "green_down": _nec_code(0x00, 0x11, "green_down"),
        "blue_up": _nec_code(0x00, 0x16, "blue_up"),
        "blue_down": _nec_code(0x00, 0x12, "blue_down"),
        "quick": _nec_code(0x00, 0x17, "quick"),
        "slow": _nec_code(0x00, 0x13, "slow"),
    },
)


# =============================================================================
# LEMOISTAR FAN
# =============================================================================

LEMOISTAR_FAN = CatalogDevice(
    id="lemoistar_fan",
    name="LEMOISTAR Fan",
    brand="LEMOISTAR",
    category=DeviceCategory.FAN,
    control_methods=[ControlMethod.IR, ControlMethod.RF],
    ir_codes={
        "power": _nec_code(0x10, 0x00, "power"),
        "speed_low": _nec_code(0x10, 0x01, "speed_low"),
        "speed_medium": _nec_code(0x10, 0x02, "speed_medium"),
        "speed_high": _nec_code(0x10, 0x03, "speed_high"),
        "speed_up": _nec_code(0x10, 0x04, "speed_up"),
        "speed_down": _nec_code(0x10, 0x05, "speed_down"),
        "oscillate": _nec_code(0x10, 0x06, "oscillate"),
        "timer_1h": _nec_code(0x10, 0x10, "timer_1h"),
        "timer_2h": _nec_code(0x10, 0x11, "timer_2h"),
        "timer_4h": _nec_code(0x10, 0x12, "timer_4h"),
        "timer_8h": _nec_code(0x10, 0x13, "timer_8h"),
        "mode_normal": _nec_code(0x10, 0x20, "mode_normal"),
        "mode_natural": _nec_code(0x10, 0x21, "mode_natural"),
        "mode_sleep": _nec_code(0x10, 0x22, "mode_sleep"),
        "light": _nec_code(0x10, 0x30, "light"),
        "light_dim": _nec_code(0x10, 0x31, "light_dim"),
        "light_bright": _nec_code(0x10, 0x32, "light_bright"),
        "reverse": _nec_code(0x10, 0x40, "reverse"),
    },
    rf_codes={
        # 433MHz RF codes - common for ceiling fans
        "power": RemoteCode(name="power", code_type=CodeType.RF_PARSED, frequency=433920000, protocol="Princeton"),
        "light": RemoteCode(name="light", code_type=CodeType.RF_PARSED, frequency=433920000, protocol="Princeton"),
    },
)


# =============================================================================
# FULL CATALOG
# =============================================================================

DEVICE_CATALOG: dict[str, CatalogDevice] = {
    "samsung_tv": SAMSUNG_TV,
    "philips_tv": PHILIPS_TV,
    "roku_tv": ROKU_TV,
    "roku_device": ROKU_DEVICE,
    "amazon_firetv": AMAZON_FIRETV,
    "onkyo_receiver": ONKYO_RECEIVER,
    "xbox": XBOX,
    "playstation": PLAYSTATION,
    "benq_projector": BENQ_PROJECTOR,
    "shelly_shade": SHELLY_SHADE,
    "jensen_radio": JENSEN_RADIO,
    "led_strip": LED_STRIP,
    "lemoistar_fan": LEMOISTAR_FAN,
}

CATALOG_BY_BRAND: dict[str, list[CatalogDevice]] = {}
for device in DEVICE_CATALOG.values():
    if device.brand not in CATALOG_BY_BRAND:
        CATALOG_BY_BRAND[device.brand] = []
    CATALOG_BY_BRAND[device.brand].append(device)

CATALOG_BY_CATEGORY: dict[DeviceCategory, list[CatalogDevice]] = {}
for device in DEVICE_CATALOG.values():
    if device.category not in CATALOG_BY_CATEGORY:
        CATALOG_BY_CATEGORY[device.category] = []
    CATALOG_BY_CATEGORY[device.category].append(device)


def get_catalog_device(device_id: str) -> CatalogDevice | None:
    """Get a device from the catalog by ID."""
    return DEVICE_CATALOG.get(device_id)


def search_catalog(query: str) -> list[CatalogDevice]:
    """Search the catalog by name or brand."""
    query = query.lower()
    results = []
    for device in DEVICE_CATALOG.values():
        if query in device.name.lower() or query in device.brand.lower():
            results.append(device)
    return results


def list_catalog() -> list[dict]:
    """List all devices in the catalog."""
    return [device.to_dict() for device in DEVICE_CATALOG.values()]
