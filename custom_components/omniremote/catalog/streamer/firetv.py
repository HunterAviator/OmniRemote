"""Amazon Fire TV profiles."""

FIRETV_IR = DeviceProfile(
    id="firetv_ir",
    name="Fire TV (IR)",
    brand="Amazon",
    category="streamer",
    model_years="2017+",
    description="Amazon Fire TV - IR control.",
    control_methods=[ControlMethod.IR],
    logo_url=BRAND_LOGOS.get("amazon", ""),
    ir_codes={
        "power": nec(0x40, 0x16, "power"),
        "home": nec(0x40, 0x0D, "home"),
        "back": nec(0x40, 0x23, "back"),
        "menu": nec(0x40, 0x05, "menu"),
        "up": nec(0x40, 0x1B, "up"),
        "down": nec(0x40, 0x1F, "down"),
        "left": nec(0x40, 0x19, "left"),
        "right": nec(0x40, 0x18, "right"),
        "ok": nec(0x40, 0x1C, "ok"),
        "play": nec(0x40, 0x21, "play"),
        "pause": nec(0x40, 0x20, "pause"),
        "rewind": nec(0x40, 0x22, "rewind"),
        "fast_forward": nec(0x40, 0x1D, "fast_forward"),
        "vol_up": nec(0x40, 0x1A, "vol_up"),
        "vol_down": nec(0x40, 0x1E, "vol_down"),
        "mute": nec(0x40, 0x17, "mute"),
    },
)
register_profile(FIRETV_IR)

FIRETV_ADB = DeviceProfile(
    id="firetv_adb",
    name="Fire TV (ADB Network)",
    brand="Amazon",
    category="streamer",
    model_years="2017+",
    description="Fire TV Android Debug Bridge control. Requires ADB debugging enabled.",
    control_methods=[ControlMethod.NETWORK],
    logo_url=BRAND_LOGOS.get("amazon", ""),
    network_port=5555,
    network_protocol="adb",
    network_commands={
        # Navigation
        "home": NetworkCommand("home", "ADB", "input keyevent 3", {}),
        "back": NetworkCommand("back", "ADB", "input keyevent 4", {}),
        "up": NetworkCommand("up", "ADB", "input keyevent 19", {}),
        "down": NetworkCommand("down", "ADB", "input keyevent 20", {}),
        "left": NetworkCommand("left", "ADB", "input keyevent 21", {}),
        "right": NetworkCommand("right", "ADB", "input keyevent 22", {}),
        "select": NetworkCommand("select", "ADB", "input keyevent 23", {}),
        "menu": NetworkCommand("menu", "ADB", "input keyevent 1", {}),
        
        # Playback
        "play": NetworkCommand("play", "ADB", "input keyevent 126", {}),
        "pause": NetworkCommand("pause", "ADB", "input keyevent 127", {}),
        "play_pause": NetworkCommand("play_pause", "ADB", "input keyevent 85", {}),
        "stop": NetworkCommand("stop", "ADB", "input keyevent 86", {}),
        "rewind": NetworkCommand("rewind", "ADB", "input keyevent 89", {}),
        "fast_forward": NetworkCommand("fast_forward", "ADB", "input keyevent 90", {}),
        
        # Volume
        "vol_up": NetworkCommand("vol_up", "ADB", "input keyevent 24", {}),
        "vol_down": NetworkCommand("vol_down", "ADB", "input keyevent 25", {}),
        "mute": NetworkCommand("mute", "ADB", "input keyevent 164", {}),
        
        # Power
        "sleep": NetworkCommand("sleep", "ADB", "input keyevent 223", {}),
        "wake": NetworkCommand("wake", "ADB", "input keyevent 224", {}),
        "power": NetworkCommand("power", "ADB", "input keyevent 26", {}),
        
        # App launching
        "launch_netflix": NetworkCommand("launch_netflix", "ADB", 
            "am start -n com.netflix.ninja/.MainActivity", {}),
        "launch_youtube": NetworkCommand("launch_youtube", "ADB",
            "am start -n com.amazon.firetv.youtube/.MainActivity", {}),
        "launch_prime": NetworkCommand("launch_prime", "ADB",
            "am start -n com.amazon.avod/.MainActivity", {}),
        "launch_disney": NetworkCommand("launch_disney", "ADB",
            "am start -n com.disney.disneyplus/.MainActivity", {}),
        "launch_hulu": NetworkCommand("launch_hulu", "ADB",
            "am start -n com.hulu.livingroomplus/.MainActivity", {}),
        "launch_plex": NetworkCommand("launch_plex", "ADB",
            "am start -n com.plexapp.android/.MainActivity", {}),
    },
    apps={
        "netflix": "com.netflix.ninja",
        "youtube": "com.amazon.firetv.youtube",
        "prime_video": "com.amazon.avod",
        "disney_plus": "com.disney.disneyplus",
        "hulu": "com.hulu.livingroomplus",
        "hbo_max": "com.hbo.hbonow",
        "plex": "com.plexapp.android",
        "spotify": "com.spotify.tv.android",
        "apple_tv": "com.apple.atve.amazon.appletv",
    },
)
register_profile(FIRETV_ADB)
