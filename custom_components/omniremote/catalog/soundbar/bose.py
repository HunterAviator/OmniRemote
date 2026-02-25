"""Bose Soundbar profiles."""

BOSE_SOUNDBAR_IR = DeviceProfile(
    id="bose_soundbar_ir",
    name="Bose Soundbar (IR)",
    brand="Bose",
    category="soundbar",
    model_years="2018+",
    description="Bose soundbars (Soundbar 500, 700, 900, Ultra).",
    control_methods=[ControlMethod.IR],
    logo_url=BRAND_LOGOS.get("bose", ""),
    ir_codes={
        "power": nec(0x8C, 0x0C, "power"),
        "vol_up": nec(0x8C, 0x04, "vol_up"),
        "vol_down": nec(0x8C, 0x05, "vol_down"),
        "mute": nec(0x8C, 0x06, "mute"),
        "input_tv": nec(0x8C, 0x10, "input_tv"),
        "input_hdmi": nec(0x8C, 0x11, "input_hdmi"),
        "input_optical": nec(0x8C, 0x12, "input_optical"),
        "input_aux": nec(0x8C, 0x13, "input_aux"),
        "input_bluetooth": nec(0x8C, 0x14, "input_bluetooth"),
        "input_wifi": nec(0x8C, 0x15, "input_wifi"),
        "bass_up": nec(0x8C, 0x20, "bass_up"),
        "bass_down": nec(0x8C, 0x21, "bass_down"),
        "dialog_mode": nec(0x8C, 0x22, "dialog_mode"),
    },
)
register_profile(BOSE_SOUNDBAR_IR)

BOSE_SOUNDBAR_NETWORK = DeviceProfile(
    id="bose_soundbar_network",
    name="Bose Soundbar (Network)",
    brand="Bose",
    category="soundbar",
    model_years="2018+",
    description="Bose soundbar network control via SoundTouch API.",
    control_methods=[ControlMethod.NETWORK],
    logo_url=BRAND_LOGOS.get("bose", ""),
    network_port=8090,
    network_protocol="http",
    network_commands={
        "power_on": NetworkCommand("power_on", "POST", "/key", {"key": "POWER", "state": "press"}),
        "power_off": NetworkCommand("power_off", "POST", "/key", {"key": "POWER", "state": "press"}),
        "vol_up": NetworkCommand("vol_up", "POST", "/key", {"key": "VOLUME_UP", "state": "press"}),
        "vol_down": NetworkCommand("vol_down", "POST", "/key", {"key": "VOLUME_DOWN", "state": "press"}),
        "mute": NetworkCommand("mute", "POST", "/key", {"key": "MUTE", "state": "press"}),
        "play": NetworkCommand("play", "POST", "/key", {"key": "PLAY", "state": "press"}),
        "pause": NetworkCommand("pause", "POST", "/key", {"key": "PAUSE", "state": "press"}),
        "next": NetworkCommand("next", "POST", "/key", {"key": "NEXT_TRACK", "state": "press"}),
        "previous": NetworkCommand("previous", "POST", "/key", {"key": "PREV_TRACK", "state": "press"}),
        "get_info": NetworkCommand("get_info", "GET", "/info", {}),
        "get_volume": NetworkCommand("get_volume", "GET", "/volume", {}),
        "set_volume": NetworkCommand("set_volume", "POST", "/volume", {"targetvolume": 50}),
        "get_now_playing": NetworkCommand("get_now_playing", "GET", "/now_playing", {}),
    },
)
register_profile(BOSE_SOUNDBAR_NETWORK)
