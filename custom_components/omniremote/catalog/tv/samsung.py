"""Samsung TV profiles."""

# =============================================================================
# Samsung TV - Standard IR (2015-2020, Most Models)
# =============================================================================
SAMSUNG_TV_IR_STANDARD = DeviceProfile(
    id="samsung_tv_ir_standard",
    name="Samsung TV (Standard IR)",
    brand="Samsung",
    category="tv",
    model_years="2015-2020",
    description="Standard Samsung TV IR codes. Works with most Samsung TVs.",
    control_methods=[ControlMethod.IR],
    logo_url=BRAND_LOGOS.get("samsung", ""),
    ir_codes={
        # Power
        "power": samsung(0x07, 0x02, "power"),
        "power_on": samsung(0x07, 0x02, "power_on"),
        "power_off": samsung(0x07, 0x98, "power_off"),
        
        # Volume
        "vol_up": samsung(0x07, 0x07, "vol_up"),
        "vol_down": samsung(0x07, 0x0B, "vol_down"),
        "mute": samsung(0x07, 0x0F, "mute"),
        
        # Channels
        "ch_up": samsung(0x07, 0x12, "ch_up"),
        "ch_down": samsung(0x07, 0x10, "ch_down"),
        "ch_list": samsung(0x07, 0x6B, "ch_list"),
        "prev_ch": samsung(0x07, 0x13, "prev_ch"),
        
        # Input
        "input": samsung(0x07, 0x01, "input"),
        "source": samsung(0x07, 0x01, "source"),
        "hdmi1": samsung(0x07, 0x69, "hdmi1"),
        "hdmi2": samsung(0x07, 0x68, "hdmi2"),
        "hdmi3": samsung(0x07, 0x6A, "hdmi3"),
        "hdmi4": samsung(0x07, 0x6B, "hdmi4"),
        "component1": samsung(0x07, 0x6E, "component1"),
        "av1": samsung(0x07, 0x5F, "av1"),
        "tv": samsung(0x07, 0x56, "tv"),
        
        # Navigation
        "menu": samsung(0x07, 0x1A, "menu"),
        "home": samsung(0x07, 0x79, "home"),
        "smart_hub": samsung(0x07, 0x79, "smart_hub"),
        "guide": samsung(0x07, 0x4F, "guide"),
        "info": samsung(0x07, 0x1F, "info"),
        "tools": samsung(0x07, 0x4B, "tools"),
        "back": samsung(0x07, 0x58, "back"),
        "exit": samsung(0x07, 0x2D, "exit"),
        
        # D-Pad
        "up": samsung(0x07, 0x60, "up"),
        "down": samsung(0x07, 0x61, "down"),
        "left": samsung(0x07, 0x65, "left"),
        "right": samsung(0x07, 0x62, "right"),
        "enter": samsung(0x07, 0x68, "enter"),
        "ok": samsung(0x07, 0x68, "ok"),
        
        # Color buttons
        "red": samsung(0x07, 0x6C, "red"),
        "green": samsung(0x07, 0x14, "green"),
        "yellow": samsung(0x07, 0x15, "yellow"),
        "blue": samsung(0x07, 0x16, "blue"),
        
        # Media
        "play": samsung(0x07, 0x47, "play"),
        "pause": samsung(0x07, 0x4A, "pause"),
        "stop": samsung(0x07, 0x46, "stop"),
        "record": samsung(0x07, 0x49, "record"),
        "rewind": samsung(0x07, 0x45, "rewind"),
        "fast_forward": samsung(0x07, 0x48, "fast_forward"),
        
        # Number pad
        "0": samsung(0x07, 0x11, "0"),
        "1": samsung(0x07, 0x04, "1"),
        "2": samsung(0x07, 0x05, "2"),
        "3": samsung(0x07, 0x06, "3"),
        "4": samsung(0x07, 0x08, "4"),
        "5": samsung(0x07, 0x09, "5"),
        "6": samsung(0x07, 0x0A, "6"),
        "7": samsung(0x07, 0x0C, "7"),
        "8": samsung(0x07, 0x0D, "8"),
        "9": samsung(0x07, 0x0E, "9"),
        
        # Picture
        "picture_mode": samsung(0x07, 0x50, "picture_mode"),
        "aspect": samsung(0x07, 0x4C, "aspect"),
        
        # Sound
        "sound_mode": samsung(0x07, 0x51, "sound_mode"),
        
        # Settings
        "settings": samsung(0x07, 0x1A, "settings"),
        "sleep": samsung(0x07, 0x03, "sleep"),
        "caption": samsung(0x07, 0x25, "caption"),
    },
)
register_profile(SAMSUNG_TV_IR_STANDARD)


# =============================================================================
# Samsung TV - Extended IR (2020+, QLED/Neo QLED)
# =============================================================================
SAMSUNG_TV_IR_2020 = DeviceProfile(
    id="samsung_tv_ir_2020",
    name="Samsung TV (2020+ QLED)",
    brand="Samsung",
    category="tv",
    model_years="2020+",
    description="Samsung QLED/Neo QLED TVs (2020 and later). Some codes differ from older models.",
    control_methods=[ControlMethod.IR],
    logo_url=BRAND_LOGOS.get("samsung", ""),
    ir_codes={
        # Power
        "power": samsung(0x07, 0x02, "power"),
        "power_off": samsung(0x07, 0x98, "power_off"),
        
        # Volume
        "vol_up": samsung(0x07, 0x07, "vol_up"),
        "vol_down": samsung(0x07, 0x0B, "vol_down"),
        "mute": samsung(0x07, 0x0F, "mute"),
        
        # Channels
        "ch_up": samsung(0x07, 0x12, "ch_up"),
        "ch_down": samsung(0x07, 0x10, "ch_down"),
        
        # Input
        "source": samsung(0x07, 0x01, "source"),
        "hdmi1": samsung(0x07, 0x69, "hdmi1"),
        "hdmi2": samsung(0x07, 0x68, "hdmi2"),
        "hdmi3": samsung(0x07, 0x6A, "hdmi3"),
        "hdmi4": samsung(0x07, 0x6B, "hdmi4"),
        
        # Smart Features
        "home": samsung(0x07, 0x79, "home"),
        "ambient": samsung(0x07, 0x7B, "ambient"),  # Ambient mode
        "bixby": samsung(0x07, 0x7C, "bixby"),  # Voice assistant
        
        # Navigation
        "back": samsung(0x07, 0x58, "back"),
        "up": samsung(0x07, 0x60, "up"),
        "down": samsung(0x07, 0x61, "down"),
        "left": samsung(0x07, 0x65, "left"),
        "right": samsung(0x07, 0x62, "right"),
        "enter": samsung(0x07, 0x68, "enter"),
        
        # Media
        "play": samsung(0x07, 0x47, "play"),
        "pause": samsung(0x07, 0x4A, "pause"),
        "stop": samsung(0x07, 0x46, "stop"),
        
        # Numbers
        "0": samsung(0x07, 0x11, "0"),
        "1": samsung(0x07, 0x04, "1"),
        "2": samsung(0x07, 0x05, "2"),
        "3": samsung(0x07, 0x06, "3"),
        "4": samsung(0x07, 0x08, "4"),
        "5": samsung(0x07, 0x09, "5"),
        "6": samsung(0x07, 0x0A, "6"),
        "7": samsung(0x07, 0x0C, "7"),
        "8": samsung(0x07, 0x0D, "8"),
        "9": samsung(0x07, 0x0E, "9"),
    },
)
register_profile(SAMSUNG_TV_IR_2020)


# =============================================================================
# Samsung TV - Network/SmartThings API
# =============================================================================
SAMSUNG_TV_NETWORK = DeviceProfile(
    id="samsung_tv_network",
    name="Samsung TV (Network/SmartThings)",
    brand="Samsung",
    category="tv",
    model_years="2016+",
    description="Samsung Smart TVs with network control. Requires SmartThings or WebSocket API.",
    control_methods=[ControlMethod.NETWORK],
    logo_url=BRAND_LOGOS.get("samsung", ""),
    network_port=8001,
    network_protocol="wss",
    network_commands={
        "power_off": NetworkCommand("power_off", "POST", "/api/v2/applications", {"appId": "poweroff"}),
        "vol_up": NetworkCommand("vol_up", "POST", "/api/v2/keys", {"key": "KEY_VOLUP"}),
        "vol_down": NetworkCommand("vol_down", "POST", "/api/v2/keys", {"key": "KEY_VOLDOWN"}),
        "mute": NetworkCommand("mute", "POST", "/api/v2/keys", {"key": "KEY_MUTE"}),
        "ch_up": NetworkCommand("ch_up", "POST", "/api/v2/keys", {"key": "KEY_CHUP"}),
        "ch_down": NetworkCommand("ch_down", "POST", "/api/v2/keys", {"key": "KEY_CHDOWN"}),
        "home": NetworkCommand("home", "POST", "/api/v2/keys", {"key": "KEY_HOME"}),
        "source": NetworkCommand("source", "POST", "/api/v2/keys", {"key": "KEY_SOURCE"}),
        "up": NetworkCommand("up", "POST", "/api/v2/keys", {"key": "KEY_UP"}),
        "down": NetworkCommand("down", "POST", "/api/v2/keys", {"key": "KEY_DOWN"}),
        "left": NetworkCommand("left", "POST", "/api/v2/keys", {"key": "KEY_LEFT"}),
        "right": NetworkCommand("right", "POST", "/api/v2/keys", {"key": "KEY_RIGHT"}),
        "enter": NetworkCommand("enter", "POST", "/api/v2/keys", {"key": "KEY_ENTER"}),
        "back": NetworkCommand("back", "POST", "/api/v2/keys", {"key": "KEY_RETURN"}),
    },
)
register_profile(SAMSUNG_TV_NETWORK)
