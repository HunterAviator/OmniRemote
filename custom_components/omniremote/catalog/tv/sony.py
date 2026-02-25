"""Sony TV profiles."""

# =============================================================================
# Sony TV - SIRC 12-bit (Older Models)
# =============================================================================
SONY_TV_SIRC12 = DeviceProfile(
    id="sony_tv_sirc12",
    name="Sony TV (SIRC 12-bit)",
    brand="Sony",
    category="tv",
    model_years="2005-2015",
    description="Older Sony TVs using 12-bit SIRC protocol.",
    control_methods=[ControlMethod.IR],
    logo_url=BRAND_LOGOS.get("sony", ""),
    ir_codes={
        # Power
        "power": sony(0x01, 0x15, "power", 12),
        "power_on": sony(0x01, 0x2E, "power_on", 12),
        "power_off": sony(0x01, 0x2F, "power_off", 12),
        
        # Volume
        "vol_up": sony(0x01, 0x12, "vol_up", 12),
        "vol_down": sony(0x01, 0x13, "vol_down", 12),
        "mute": sony(0x01, 0x14, "mute", 12),
        
        # Channels
        "ch_up": sony(0x01, 0x10, "ch_up", 12),
        "ch_down": sony(0x01, 0x11, "ch_down", 12),
        "prev_ch": sony(0x01, 0x13, "prev_ch", 12),
        
        # Input
        "input": sony(0x01, 0x25, "input", 12),
        "tv": sony(0x01, 0x25, "tv", 12),
        "hdmi1": sony(0x01, 0x49, "hdmi1", 12),
        "hdmi2": sony(0x01, 0x4A, "hdmi2", 12),
        "hdmi3": sony(0x01, 0x4B, "hdmi3", 12),
        "hdmi4": sony(0x01, 0x4C, "hdmi4", 12),
        "video1": sony(0x01, 0x22, "video1", 12),
        "video2": sony(0x01, 0x23, "video2", 12),
        "component1": sony(0x01, 0x24, "component1", 12),
        
        # Navigation
        "menu": sony(0x01, 0x60, "menu", 12),
        "home": sony(0x01, 0x60, "home", 12),
        "guide": sony(0x01, 0x5A, "guide", 12),
        "back": sony(0x01, 0x63, "back", 12),
        "exit": sony(0x01, 0x63, "exit", 12),
        
        # D-Pad
        "up": sony(0x01, 0x74, "up", 12),
        "down": sony(0x01, 0x75, "down", 12),
        "left": sony(0x01, 0x34, "left", 12),
        "right": sony(0x01, 0x33, "right", 12),
        "enter": sony(0x01, 0x65, "enter", 12),
        "ok": sony(0x01, 0x65, "ok", 12),
        
        # Numbers
        "0": sony(0x01, 0x09, "0", 12),
        "1": sony(0x01, 0x00, "1", 12),
        "2": sony(0x01, 0x01, "2", 12),
        "3": sony(0x01, 0x02, "3", 12),
        "4": sony(0x01, 0x03, "4", 12),
        "5": sony(0x01, 0x04, "5", 12),
        "6": sony(0x01, 0x05, "6", 12),
        "7": sony(0x01, 0x06, "7", 12),
        "8": sony(0x01, 0x07, "8", 12),
        "9": sony(0x01, 0x08, "9", 12),
        
        # Picture
        "picture_mode": sony(0x01, 0x36, "picture_mode", 12),
        "wide": sony(0x01, 0x3E, "wide", 12),
        
        # Media
        "play": sony(0x01, 0x58, "play", 12),
        "pause": sony(0x01, 0x59, "pause", 12),
        "stop": sony(0x01, 0x18, "stop", 12),
        
        # Misc
        "sleep": sony(0x01, 0x36, "sleep", 12),
        "display": sony(0x01, 0x3A, "display", 12),
    },
)
register_profile(SONY_TV_SIRC12)


# =============================================================================
# Sony TV - SIRC 15-bit (Bravia 2015+)
# =============================================================================
SONY_TV_BRAVIA = DeviceProfile(
    id="sony_tv_bravia",
    name="Sony Bravia TV",
    brand="Sony",
    category="tv",
    model_years="2015+",
    description="Sony Bravia Smart TVs using 15-bit SIRC protocol.",
    control_methods=[ControlMethod.IR, ControlMethod.NETWORK],
    logo_url=BRAND_LOGOS.get("sony", ""),
    ir_codes={
        # Power
        "power": sony(0x01, 0x15, "power", 15),
        "power_on": sony(0x01, 0x2E, "power_on", 15),
        "power_off": sony(0x01, 0x2F, "power_off", 15),
        
        # Volume
        "vol_up": sony(0x01, 0x12, "vol_up", 15),
        "vol_down": sony(0x01, 0x13, "vol_down", 15),
        "mute": sony(0x01, 0x14, "mute", 15),
        
        # Channels
        "ch_up": sony(0x01, 0x10, "ch_up", 15),
        "ch_down": sony(0x01, 0x11, "ch_down", 15),
        
        # Input
        "input": sony(0x01, 0x25, "input", 15),
        "hdmi1": sony(0x01, 0x49, "hdmi1", 15),
        "hdmi2": sony(0x01, 0x4A, "hdmi2", 15),
        "hdmi3": sony(0x01, 0x4B, "hdmi3", 15),
        "hdmi4": sony(0x01, 0x4C, "hdmi4", 15),
        
        # Smart Features
        "home": sony(0x01, 0x60, "home", 15),
        "netflix": sony(0x01, 0x6E, "netflix", 15),
        "google_play": sony(0x01, 0xA4, "google_play", 15),
        "youtube": sony(0x01, 0xA5, "youtube", 15),
        
        # Navigation
        "back": sony(0x01, 0x63, "back", 15),
        "up": sony(0x01, 0x74, "up", 15),
        "down": sony(0x01, 0x75, "down", 15),
        "left": sony(0x01, 0x34, "left", 15),
        "right": sony(0x01, 0x33, "right", 15),
        "enter": sony(0x01, 0x65, "enter", 15),
        
        # Action buttons
        "action_menu": sony(0x01, 0x6B, "action_menu", 15),
        "help": sony(0x01, 0x6D, "help", 15),
        
        # Numbers
        "0": sony(0x01, 0x09, "0", 15),
        "1": sony(0x01, 0x00, "1", 15),
        "2": sony(0x01, 0x01, "2", 15),
        "3": sony(0x01, 0x02, "3", 15),
        "4": sony(0x01, 0x03, "4", 15),
        "5": sony(0x01, 0x04, "5", 15),
        "6": sony(0x01, 0x05, "6", 15),
        "7": sony(0x01, 0x06, "7", 15),
        "8": sony(0x01, 0x07, "8", 15),
        "9": sony(0x01, 0x08, "9", 15),
        
        # Media
        "play": sony(0x01, 0x58, "play", 15),
        "pause": sony(0x01, 0x59, "pause", 15),
        "stop": sony(0x01, 0x18, "stop", 15),
        "rewind": sony(0x01, 0x1B, "rewind", 15),
        "fast_forward": sony(0x01, 0x1A, "fast_forward", 15),
    },
    network_port=80,
    network_protocol="http",
    network_commands={
        "power_off": NetworkCommand("power_off", "POST", "/sony/system", {"method": "setPowerStatus", "params": [{"status": False}]}),
        "vol_up": NetworkCommand("vol_up", "POST", "/sony/audio", {"method": "setAudioVolume", "params": [{"target": "speaker", "volume": "+1"}]}),
        "vol_down": NetworkCommand("vol_down", "POST", "/sony/audio", {"method": "setAudioVolume", "params": [{"target": "speaker", "volume": "-1"}]}),
        "mute": NetworkCommand("mute", "POST", "/sony/audio", {"method": "setAudioMute", "params": [{"status": True}]}),
        "get_volume": NetworkCommand("get_volume", "POST", "/sony/audio", {"method": "getVolumeInformation", "params": []}),
    },
)
register_profile(SONY_TV_BRAVIA)
