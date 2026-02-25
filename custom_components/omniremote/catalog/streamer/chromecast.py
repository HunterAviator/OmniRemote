"""Google Chromecast and Google TV profiles."""

# =============================================================================
# Chromecast with Google TV - Network/Cast
# =============================================================================
CHROMECAST_GOOGLETV = DeviceProfile(
    id="chromecast_googletv",
    name="Chromecast with Google TV",
    brand="Google",
    category="streamer",
    model_years="2020+",
    description="Chromecast with Google TV - Network control via Cast/ADB and HDMI-CEC.",
    control_methods=[ControlMethod.NETWORK, ControlMethod.HDMI_CEC],
    logo_url=BRAND_LOGOS.get("google", ""),
    network_port=8008,
    network_protocol="cast",
    ir_codes={
        # Chromecast remote uses BLE, not IR, but some universal remotes use these
        "power": nec(0x3E, 0x01, "power"),
        "vol_up": nec(0x3E, 0x02, "vol_up"),
        "vol_down": nec(0x3E, 0x03, "vol_down"),
        "mute": nec(0x3E, 0x04, "mute"),
        "input": nec(0x3E, 0x05, "input"),
    },
    network_commands={
        # Cast protocol commands
        "get_status": NetworkCommand("get_status", "CAST", "GET_STATUS", {}),
        "launch_youtube": NetworkCommand("launch_youtube", "CAST", "LAUNCH", {"appId": "YouTube"}),
        "launch_netflix": NetworkCommand("launch_netflix", "CAST", "LAUNCH", {"appId": "Netflix"}),
        "launch_disney": NetworkCommand("launch_disney", "CAST", "LAUNCH", {"appId": "Disney+"}),
        "stop": NetworkCommand("stop", "CAST", "STOP", {}),
        "pause": NetworkCommand("pause", "CAST", "PAUSE", {}),
        "play": NetworkCommand("play", "CAST", "PLAY", {}),
        
        # ADB commands (requires developer mode)
        "home": NetworkCommand("home", "ADB", "shell input keyevent KEYCODE_HOME", {}),
        "back": NetworkCommand("back", "ADB", "shell input keyevent KEYCODE_BACK", {}),
        "up": NetworkCommand("up", "ADB", "shell input keyevent KEYCODE_DPAD_UP", {}),
        "down": NetworkCommand("down", "ADB", "shell input keyevent KEYCODE_DPAD_DOWN", {}),
        "left": NetworkCommand("left", "ADB", "shell input keyevent KEYCODE_DPAD_LEFT", {}),
        "right": NetworkCommand("right", "ADB", "shell input keyevent KEYCODE_DPAD_RIGHT", {}),
        "enter": NetworkCommand("enter", "ADB", "shell input keyevent KEYCODE_ENTER", {}),
        "play_pause": NetworkCommand("play_pause", "ADB", "shell input keyevent KEYCODE_MEDIA_PLAY_PAUSE", {}),
        "google_assistant": NetworkCommand("google_assistant", "ADB", "shell input keyevent KEYCODE_SEARCH", {}),
    },
    apps={
        "youtube": "com.google.android.youtube.tv",
        "netflix": "com.netflix.ninja",
        "disney_plus": "com.disney.disneyplus",
        "prime_video": "com.amazon.amazonvideo.livingroom",
        "hbo_max": "com.wbd.stream",
        "hulu": "com.hulu.livingroomplus",
        "peacock": "com.peacocktv.peacockandroid",
        "paramount_plus": "com.cbs.ott",
        "apple_tv": "com.apple.atve.androidtv.appletv",
        "spotify": "com.spotify.tv.android",
        "plex": "com.plexapp.android",
    },
)
register_profile(CHROMECAST_GOOGLETV)


# =============================================================================
# Chromecast (Original) - Network Only
# =============================================================================
CHROMECAST_ORIGINAL = DeviceProfile(
    id="chromecast_original",
    name="Chromecast (1st-3rd Gen)",
    brand="Google",
    category="streamer",
    model_years="2013-2020",
    description="Original Chromecast dongle - Cast protocol only, no remote.",
    control_methods=[ControlMethod.NETWORK],
    logo_url=BRAND_LOGOS.get("google", ""),
    network_port=8008,
    network_protocol="cast",
    network_commands={
        "get_status": NetworkCommand("get_status", "CAST", "GET_STATUS", {}),
        "launch_youtube": NetworkCommand("launch_youtube", "CAST", "LAUNCH", {"appId": "YouTube"}),
        "launch_netflix": NetworkCommand("launch_netflix", "CAST", "LAUNCH", {"appId": "Netflix"}),
        "stop": NetworkCommand("stop", "CAST", "STOP", {}),
        "pause": NetworkCommand("pause", "CAST", "PAUSE", {}),
        "play": NetworkCommand("play", "CAST", "PLAY", {}),
        "set_volume": NetworkCommand("set_volume", "CAST", "SET_VOLUME", {"level": 0.5}),
        "mute": NetworkCommand("mute", "CAST", "SET_VOLUME", {"muted": True}),
        "unmute": NetworkCommand("unmute", "CAST", "SET_VOLUME", {"muted": False}),
    },
)
register_profile(CHROMECAST_ORIGINAL)


# =============================================================================
# Google TV (Sony, TCL, Hisense branded)
# =============================================================================
GOOGLETV_GENERIC = DeviceProfile(
    id="googletv_generic",
    name="Google TV (Built-in)",
    brand="Google",
    category="streamer",
    model_years="2020+",
    description="Google TV built into TVs (Sony Bravia, TCL, Hisense, etc.) - ADB control.",
    control_methods=[ControlMethod.NETWORK],
    logo_url=BRAND_LOGOS.get("google", ""),
    network_port=5555,
    network_protocol="adb",
    network_commands={
        "home": NetworkCommand("home", "ADB", "shell input keyevent KEYCODE_HOME", {}),
        "back": NetworkCommand("back", "ADB", "shell input keyevent KEYCODE_BACK", {}),
        "up": NetworkCommand("up", "ADB", "shell input keyevent KEYCODE_DPAD_UP", {}),
        "down": NetworkCommand("down", "ADB", "shell input keyevent KEYCODE_DPAD_DOWN", {}),
        "left": NetworkCommand("left", "ADB", "shell input keyevent KEYCODE_DPAD_LEFT", {}),
        "right": NetworkCommand("right", "ADB", "shell input keyevent KEYCODE_DPAD_RIGHT", {}),
        "enter": NetworkCommand("enter", "ADB", "shell input keyevent KEYCODE_ENTER", {}),
        "menu": NetworkCommand("menu", "ADB", "shell input keyevent KEYCODE_MENU", {}),
        "play_pause": NetworkCommand("play_pause", "ADB", "shell input keyevent KEYCODE_MEDIA_PLAY_PAUSE", {}),
        "play": NetworkCommand("play", "ADB", "shell input keyevent KEYCODE_MEDIA_PLAY", {}),
        "pause": NetworkCommand("pause", "ADB", "shell input keyevent KEYCODE_MEDIA_PAUSE", {}),
        "stop": NetworkCommand("stop", "ADB", "shell input keyevent KEYCODE_MEDIA_STOP", {}),
        "next": NetworkCommand("next", "ADB", "shell input keyevent KEYCODE_MEDIA_NEXT", {}),
        "previous": NetworkCommand("previous", "ADB", "shell input keyevent KEYCODE_MEDIA_PREVIOUS", {}),
        "rewind": NetworkCommand("rewind", "ADB", "shell input keyevent KEYCODE_MEDIA_REWIND", {}),
        "fast_forward": NetworkCommand("fast_forward", "ADB", "shell input keyevent KEYCODE_MEDIA_FAST_FORWARD", {}),
        "vol_up": NetworkCommand("vol_up", "ADB", "shell input keyevent KEYCODE_VOLUME_UP", {}),
        "vol_down": NetworkCommand("vol_down", "ADB", "shell input keyevent KEYCODE_VOLUME_DOWN", {}),
        "mute": NetworkCommand("mute", "ADB", "shell input keyevent KEYCODE_VOLUME_MUTE", {}),
        "power": NetworkCommand("power", "ADB", "shell input keyevent KEYCODE_POWER", {}),
        "google_assistant": NetworkCommand("google_assistant", "ADB", "shell input keyevent KEYCODE_ASSIST", {}),
        
        # App launches
        "launch_netflix": NetworkCommand("launch_netflix", "ADB", "shell am start -n com.netflix.ninja/.MainActivity", {}),
        "launch_youtube": NetworkCommand("launch_youtube", "ADB", "shell am start -n com.google.android.youtube.tv/com.google.android.apps.youtube.tv.activity.ShellActivity", {}),
        "launch_disney": NetworkCommand("launch_disney", "ADB", "shell am start -n com.disney.disneyplus/.MainActivity", {}),
        "launch_prime": NetworkCommand("launch_prime", "ADB", "shell am start -n com.amazon.amazonvideo.livingroom/.MainActivity", {}),
        "launch_hulu": NetworkCommand("launch_hulu", "ADB", "shell am start -n com.hulu.livingroomplus/.WKFactivity", {}),
    },
    apps={
        "youtube": "com.google.android.youtube.tv",
        "netflix": "com.netflix.ninja",
        "disney_plus": "com.disney.disneyplus",
        "prime_video": "com.amazon.amazonvideo.livingroom",
        "hbo_max": "com.wbd.stream",
        "hulu": "com.hulu.livingroomplus",
        "peacock": "com.peacocktv.peacockandroid",
        "apple_tv": "com.apple.atve.androidtv.appletv",
        "spotify": "com.spotify.tv.android",
        "plex": "com.plexapp.android",
    },
)
register_profile(GOOGLETV_GENERIC)
