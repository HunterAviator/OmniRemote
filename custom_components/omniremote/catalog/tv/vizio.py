"""Vizio TV profiles."""

# =============================================================================
# Vizio TV - Standard NEC IR
# =============================================================================
VIZIO_TV_IR = DeviceProfile(
    id="vizio_tv_ir",
    name="Vizio TV (IR)",
    brand="Vizio",
    category="tv",
    model_years="2012+",
    description="Vizio Smart TVs using NEC IR protocol.",
    control_methods=[ControlMethod.IR],
    logo_url=BRAND_LOGOS.get("vizio", ""),
    ir_codes={
        "power": nec(0x04, 0x08, "power"),
        "power_on": nec(0x04, 0x08, "power_on"),
        "power_off": nec(0x04, 0x08, "power_off"),
        "vol_up": nec(0x04, 0x02, "vol_up"),
        "vol_down": nec(0x04, 0x03, "vol_down"),
        "mute": nec(0x04, 0x09, "mute"),
        "ch_up": nec(0x04, 0x00, "ch_up"),
        "ch_down": nec(0x04, 0x01, "ch_down"),
        "input": nec(0x04, 0x0B, "input"),
        "menu": nec(0x04, 0x43, "menu"),
        "home": nec(0x04, 0xD2, "home"),
        "back": nec(0x04, 0x28, "back"),
        "exit": nec(0x04, 0x5B, "exit"),
        "info": nec(0x04, 0xAA, "info"),
        "guide": nec(0x04, 0xAB, "guide"),
        "up": nec(0x04, 0x40, "up"),
        "down": nec(0x04, 0x41, "down"),
        "left": nec(0x04, 0x07, "left"),
        "right": nec(0x04, 0x06, "right"),
        "enter": nec(0x04, 0x44, "enter"),
        "0": nec(0x04, 0x10, "0"),
        "1": nec(0x04, 0x11, "1"),
        "2": nec(0x04, 0x12, "2"),
        "3": nec(0x04, 0x13, "3"),
        "4": nec(0x04, 0x14, "4"),
        "5": nec(0x04, 0x15, "5"),
        "6": nec(0x04, 0x16, "6"),
        "7": nec(0x04, 0x17, "7"),
        "8": nec(0x04, 0x18, "8"),
        "9": nec(0x04, 0x19, "9"),
        "amazon": nec(0x04, 0xD1, "amazon"),
        "netflix": nec(0x04, 0xD0, "netflix"),
        "vudu": nec(0x04, 0xD3, "vudu"),
        "watchfree": nec(0x04, 0xD4, "watchfree"),
    },
)
register_profile(VIZIO_TV_IR)

# =============================================================================
# Vizio TV - SmartCast Network API
# =============================================================================
VIZIO_TV_SMARTCAST = DeviceProfile(
    id="vizio_tv_smartcast",
    name="Vizio SmartCast TV (Network)",
    brand="Vizio",
    category="tv",
    model_years="2016+",
    description="Vizio SmartCast TVs with REST API control.",
    control_methods=[ControlMethod.NETWORK],
    logo_url=BRAND_LOGOS.get("vizio", ""),
    network_port=7345,
    network_protocol="https",
    network_commands={
        "power_on": NetworkCommand("power_on", "PUT", "/key_command/", {"KEYLIST": [{"CODESET": 11, "CODE": 1, "ACTION": "KEYPRESS"}]}),
        "power_off": NetworkCommand("power_off", "PUT", "/key_command/", {"KEYLIST": [{"CODESET": 11, "CODE": 0, "ACTION": "KEYPRESS"}]}),
        "vol_up": NetworkCommand("vol_up", "PUT", "/key_command/", {"KEYLIST": [{"CODESET": 5, "CODE": 1, "ACTION": "KEYPRESS"}]}),
        "vol_down": NetworkCommand("vol_down", "PUT", "/key_command/", {"KEYLIST": [{"CODESET": 5, "CODE": 0, "ACTION": "KEYPRESS"}]}),
        "mute_on": NetworkCommand("mute_on", "PUT", "/key_command/", {"KEYLIST": [{"CODESET": 5, "CODE": 3, "ACTION": "KEYPRESS"}]}),
        "mute_off": NetworkCommand("mute_off", "PUT", "/key_command/", {"KEYLIST": [{"CODESET": 5, "CODE": 2, "ACTION": "KEYPRESS"}]}),
        "input_hdmi1": NetworkCommand("input_hdmi1", "PUT", "/menu_native/dynamic/tv_settings/devices/current_input", {"VALUE": "HDMI-1"}),
        "input_hdmi2": NetworkCommand("input_hdmi2", "PUT", "/menu_native/dynamic/tv_settings/devices/current_input", {"VALUE": "HDMI-2"}),
        "up": NetworkCommand("up", "PUT", "/key_command/", {"KEYLIST": [{"CODESET": 3, "CODE": 8, "ACTION": "KEYPRESS"}]}),
        "down": NetworkCommand("down", "PUT", "/key_command/", {"KEYLIST": [{"CODESET": 3, "CODE": 0, "ACTION": "KEYPRESS"}]}),
        "left": NetworkCommand("left", "PUT", "/key_command/", {"KEYLIST": [{"CODESET": 3, "CODE": 1, "ACTION": "KEYPRESS"}]}),
        "right": NetworkCommand("right", "PUT", "/key_command/", {"KEYLIST": [{"CODESET": 3, "CODE": 7, "ACTION": "KEYPRESS"}]}),
        "ok": NetworkCommand("ok", "PUT", "/key_command/", {"KEYLIST": [{"CODESET": 3, "CODE": 2, "ACTION": "KEYPRESS"}]}),
        "back": NetworkCommand("back", "PUT", "/key_command/", {"KEYLIST": [{"CODESET": 4, "CODE": 0, "ACTION": "KEYPRESS"}]}),
    },
)
register_profile(VIZIO_TV_SMARTCAST)
