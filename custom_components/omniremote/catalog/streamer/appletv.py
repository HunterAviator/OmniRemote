"""Apple TV profiles."""

APPLETV_IR = DeviceProfile(
    id="appletv_ir",
    name="Apple TV (IR)",
    brand="Apple",
    category="streamer",
    model_years="2015+",
    description="Apple TV IR control (works with Apple TV 4K and HD).",
    control_methods=[ControlMethod.IR],
    logo_url=BRAND_LOGOS.get("apple", ""),
    ir_codes={
        "menu": nec(0x87, 0x03, "menu"),
        "up": nec(0x87, 0x0A, "up"),
        "down": nec(0x87, 0x0C, "down"),
        "left": nec(0x87, 0x09, "left"),
        "right": nec(0x87, 0x06, "right"),
        "select": nec(0x87, 0x05, "select"),
        "play": nec(0x87, 0x04, "play"),
        "pause": nec(0x87, 0x04, "pause"),
    },
)
register_profile(APPLETV_IR)

APPLETV_NETWORK = DeviceProfile(
    id="appletv_network",
    name="Apple TV (PyATV Network)",
    brand="Apple",
    category="streamer",
    model_years="2017+",
    description="Apple TV network control via pyatv library. Supports media control and app launching.",
    control_methods=[ControlMethod.NETWORK],
    logo_url=BRAND_LOGOS.get("apple", ""),
    network_port=49152,
    network_protocol="mrp",
    network_commands={
        # Navigation
        "home": NetworkCommand("home", "PYATV", "home", {}),
        "menu": NetworkCommand("menu", "PYATV", "menu", {}),
        "top_menu": NetworkCommand("top_menu", "PYATV", "top_menu", {}),
        "up": NetworkCommand("up", "PYATV", "up", {}),
        "down": NetworkCommand("down", "PYATV", "down", {}),
        "left": NetworkCommand("left", "PYATV", "left", {}),
        "right": NetworkCommand("right", "PYATV", "right", {}),
        "select": NetworkCommand("select", "PYATV", "select", {}),
        
        # Playback
        "play": NetworkCommand("play", "PYATV", "play", {}),
        "pause": NetworkCommand("pause", "PYATV", "pause", {}),
        "play_pause": NetworkCommand("play_pause", "PYATV", "play_pause", {}),
        "stop": NetworkCommand("stop", "PYATV", "stop", {}),
        "skip_forward": NetworkCommand("skip_forward", "PYATV", "skip_forward", {}),
        "skip_backward": NetworkCommand("skip_backward", "PYATV", "skip_backward", {}),
        "next": NetworkCommand("next", "PYATV", "next", {}),
        "previous": NetworkCommand("previous", "PYATV", "previous", {}),
        
        # Volume
        "vol_up": NetworkCommand("vol_up", "PYATV", "volume_up", {}),
        "vol_down": NetworkCommand("vol_down", "PYATV", "volume_down", {}),
        
        # Power
        "turn_on": NetworkCommand("turn_on", "PYATV", "turn_on", {}),
        "turn_off": NetworkCommand("turn_off", "PYATV", "turn_off", {}),
        
        # App launching (by bundle ID)
        "launch_netflix": NetworkCommand("launch_netflix", "PYATV", "launch_app com.netflix.Netflix", {}),
        "launch_youtube": NetworkCommand("launch_youtube", "PYATV", "launch_app com.google.ios.youtube", {}),
        "launch_disney": NetworkCommand("launch_disney", "PYATV", "launch_app com.disney.disneyplus", {}),
        "launch_hbo": NetworkCommand("launch_hbo", "PYATV", "launch_app com.hbo.hbonow", {}),
        "launch_prime": NetworkCommand("launch_prime", "PYATV", "launch_app com.amazon.aiv.AIVApp", {}),
        "launch_plex": NetworkCommand("launch_plex", "PYATV", "launch_app com.plexapp.plex", {}),
    },
    apps={
        "netflix": "com.netflix.Netflix",
        "youtube": "com.google.ios.youtube",
        "disney_plus": "com.disney.disneyplus",
        "hbo_max": "com.hbo.hbonow",
        "prime_video": "com.amazon.aiv.AIVApp",
        "plex": "com.plexapp.plex",
        "apple_music": "com.apple.TVMusic",
        "apple_tv_plus": "com.apple.TVWatchList",
        "hulu": "com.hulu.plus",
        "spotify": "com.spotify.client",
    },
)
register_profile(APPLETV_NETWORK)
