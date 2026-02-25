"""Toshiba TV profiles."""

# =============================================================================
# Toshiba TV - Standard IR (NEC Protocol)
# =============================================================================
TOSHIBA_TV_IR = DeviceProfile(
    id="toshiba_tv_ir",
    name="Toshiba TV (IR)",
    brand="Toshiba",
    category="tv",
    model_years="2010+",
    description="Toshiba LCD/LED TVs - Standard NEC protocol IR codes.",
    control_methods=[ControlMethod.IR],
    logo_url=BRAND_LOGOS.get("toshiba", ""),
    ir_codes={
        # Power
        "power": nec(0x40, 0x12, "power"),
        "power_on": nec(0x40, 0x75, "power_on"),
        "power_off": nec(0x40, 0x76, "power_off"),
        
        # Volume
        "vol_up": nec(0x40, 0x1A, "vol_up"),
        "vol_down": nec(0x40, 0x1E, "vol_down"),
        "mute": nec(0x40, 0x10, "mute"),
        
        # Channels
        "ch_up": nec(0x40, 0x1B, "ch_up"),
        "ch_down": nec(0x40, 0x1F, "ch_down"),
        "prev_ch": nec(0x40, 0x18, "prev_ch"),
        
        # Input
        "input": nec(0x40, 0x0F, "input"),
        "hdmi1": nec(0x40, 0x67, "hdmi1"),
        "hdmi2": nec(0x40, 0x68, "hdmi2"),
        "hdmi3": nec(0x40, 0x69, "hdmi3"),
        "hdmi4": nec(0x40, 0x6A, "hdmi4"),
        "av1": nec(0x40, 0x63, "av1"),
        "component1": nec(0x40, 0x65, "component1"),
        "tv": nec(0x40, 0x60, "tv"),
        
        # Navigation
        "menu": nec(0x40, 0xC3, "menu"),
        "up": nec(0x40, 0x41, "up"),
        "down": nec(0x40, 0x42, "down"),
        "left": nec(0x40, 0x43, "left"),
        "right": nec(0x40, 0x44, "right"),
        "enter": nec(0x40, 0x45, "enter"),
        "back": nec(0x40, 0x46, "back"),
        "exit": nec(0x40, 0xC4, "exit"),
        
        # Info/Guide
        "info": nec(0x40, 0x47, "info"),
        "guide": nec(0x40, 0x48, "guide"),
        
        # Media
        "play": nec(0x40, 0x50, "play"),
        "pause": nec(0x40, 0x51, "pause"),
        "stop": nec(0x40, 0x52, "stop"),
        "record": nec(0x40, 0x53, "record"),
        "rewind": nec(0x40, 0x54, "rewind"),
        "fast_forward": nec(0x40, 0x55, "fast_forward"),
        
        # Numbers
        "0": nec(0x40, 0x00, "0"),
        "1": nec(0x40, 0x01, "1"),
        "2": nec(0x40, 0x02, "2"),
        "3": nec(0x40, 0x03, "3"),
        "4": nec(0x40, 0x04, "4"),
        "5": nec(0x40, 0x05, "5"),
        "6": nec(0x40, 0x06, "6"),
        "7": nec(0x40, 0x07, "7"),
        "8": nec(0x40, 0x08, "8"),
        "9": nec(0x40, 0x09, "9"),
        
        # Picture
        "picture_mode": nec(0x40, 0x80, "picture_mode"),
        "aspect": nec(0x40, 0x81, "aspect"),
        "sleep": nec(0x40, 0x17, "sleep"),
        "caption": nec(0x40, 0x71, "caption"),
    },
)
register_profile(TOSHIBA_TV_IR)


# =============================================================================
# Toshiba Fire TV Edition
# =============================================================================
TOSHIBA_FIRETV = DeviceProfile(
    id="toshiba_firetv",
    name="Toshiba Fire TV Edition",
    brand="Toshiba",
    category="tv",
    model_years="2018+",
    description="Toshiba Fire TV Edition - Uses Fire TV IR codes and ADB.",
    control_methods=[ControlMethod.IR, ControlMethod.NETWORK],
    logo_url=BRAND_LOGOS.get("toshiba", ""),
    network_port=5555,
    network_protocol="adb",
    ir_codes={
        # Power
        "power": nec(0x40, 0x12, "power"),
        
        # Volume
        "vol_up": nec(0x40, 0x1A, "vol_up"),
        "vol_down": nec(0x40, 0x1E, "vol_down"),
        "mute": nec(0x40, 0x10, "mute"),
        
        # Navigation (Fire TV codes)
        "home": nec(0xEE, 0x5A, "home"),
        "back": nec(0xEE, 0x5B, "back"),
        "up": nec(0xEE, 0x50, "up"),
        "down": nec(0xEE, 0x51, "down"),
        "left": nec(0xEE, 0x52, "left"),
        "right": nec(0xEE, 0x53, "right"),
        "enter": nec(0xEE, 0x54, "enter"),
        
        # Media
        "play_pause": nec(0xEE, 0x55, "play_pause"),
        "rewind": nec(0xEE, 0x56, "rewind"),
        "fast_forward": nec(0xEE, 0x57, "fast_forward"),
        
        # App shortcuts
        "alexa": nec(0xEE, 0x5C, "alexa"),
    },
    network_commands={
        "home": NetworkCommand("home", "ADB", "shell input keyevent KEYCODE_HOME", {}),
        "back": NetworkCommand("back", "ADB", "shell input keyevent KEYCODE_BACK", {}),
        "up": NetworkCommand("up", "ADB", "shell input keyevent KEYCODE_DPAD_UP", {}),
        "down": NetworkCommand("down", "ADB", "shell input keyevent KEYCODE_DPAD_DOWN", {}),
        "left": NetworkCommand("left", "ADB", "shell input keyevent KEYCODE_DPAD_LEFT", {}),
        "right": NetworkCommand("right", "ADB", "shell input keyevent KEYCODE_DPAD_RIGHT", {}),
        "enter": NetworkCommand("enter", "ADB", "shell input keyevent KEYCODE_ENTER", {}),
        "play_pause": NetworkCommand("play_pause", "ADB", "shell input keyevent KEYCODE_MEDIA_PLAY_PAUSE", {}),
        "launch_netflix": NetworkCommand("launch_netflix", "ADB", "shell am start -n com.netflix.ninja/.MainActivity", {}),
        "launch_prime": NetworkCommand("launch_prime", "ADB", "shell am start -n com.amazon.avod/.MainActivity", {}),
    },
    apps={
        "netflix": "com.netflix.ninja",
        "prime_video": "com.amazon.avod",
        "youtube": "com.google.android.youtube.tv",
        "hulu": "com.hulu.livingroomplus",
        "disney_plus": "com.disney.disneyplus",
    },
)
register_profile(TOSHIBA_FIRETV)
