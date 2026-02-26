"""Onkyo/Integra AVR profiles."""

# Onkyo uses NEC protocol with address 0x4B (75)
# Verified codes from IRDB and Pronto databases

ONKYO_AVR_IR = DeviceProfile(
    id="onkyo_avr_ir",
    name="Onkyo AVR (IR)",
    brand="Onkyo",
    category="receiver",
    model_years="2008+",
    description="Onkyo AV Receivers - IR control. Uses NEC protocol.",
    control_methods=[ControlMethod.IR],
    logo_url=BRAND_LOGOS.get("onkyo", ""),
    ir_codes={
        # Power
        "power": nec(0x4B, 0x04, "power"),           # Power toggle
        "power_on": nec(0x4B, 0x1E, "power_on"),     # Discrete on
        "power_off": nec(0x4B, 0x1F, "power_off"),   # Discrete off
        
        # Volume
        "vol_up": nec(0x4B, 0x02, "vol_up"),
        "vol_down": nec(0x4B, 0x03, "vol_down"),
        "mute": nec(0x4B, 0x05, "mute"),
        
        # Inputs (verified codes)
        "input_dvd": nec(0x4B, 0x0B, "input_dvd"),
        "input_cbl_sat": nec(0x4B, 0x0E, "input_cbl_sat"),
        "input_tv": nec(0x4B, 0x12, "input_tv"),
        "input_cd": nec(0x4B, 0x20, "input_cd"),
        "input_tuner": nec(0x4B, 0x08, "input_tuner"),
        "input_phono": nec(0x4B, 0x21, "input_phono"),
        "input_aux": nec(0x4B, 0x22, "input_aux"),
        "input_bd": nec(0x4B, 0x10, "input_bd"),
        "input_game": nec(0x4B, 0x0A, "input_game"),
        "input_vcr": nec(0x4B, 0x0C, "input_vcr"),
        "input_tape": nec(0x4B, 0x0D, "input_tape"),
        "input_net": nec(0x4B, 0x2B, "input_net"),
        "input_usb": nec(0x4B, 0x29, "input_usb"),
        
        # Navigation
        "menu": nec(0x4B, 0x15, "menu"),
        "up": nec(0x4B, 0x16, "up"),
        "down": nec(0x4B, 0x17, "down"),
        "left": nec(0x4B, 0x18, "left"),
        "right": nec(0x4B, 0x19, "right"),
        "enter": nec(0x4B, 0x1A, "enter"),
        "return": nec(0x4B, 0x1B, "return"),
        "display": nec(0x4B, 0x14, "display"),
        
        # Listening modes
        "stereo": nec(0x4B, 0x50, "stereo"),
        "surround": nec(0x4B, 0x51, "surround"),
        "thx": nec(0x4B, 0x52, "thx"),
        "direct": nec(0x4B, 0x53, "direct"),
        "pure_audio": nec(0x4B, 0x54, "pure_audio"),
        
        # Tone/EQ
        "bass_up": nec(0x4B, 0x30, "bass_up"),
        "bass_down": nec(0x4B, 0x31, "bass_down"),
        "treble_up": nec(0x4B, 0x32, "treble_up"),
        "treble_down": nec(0x4B, 0x33, "treble_down"),
        
        # Misc
        "sleep": nec(0x4B, 0x0F, "sleep"),
        "dimmer": nec(0x4B, 0x13, "dimmer"),
    },
)
register_profile(ONKYO_AVR_IR)

ONKYO_AVR_NETWORK = DeviceProfile(
    id="onkyo_avr_network",
    name="Onkyo AVR (eISCP Network)",
    brand="Onkyo",
    category="receiver",
    model_years="2012+",
    description="Onkyo eISCP network protocol. Port 60128.",
    control_methods=[ControlMethod.NETWORK],
    logo_url=BRAND_LOGOS.get("onkyo", ""),
    network_port=60128,
    network_protocol="eiscp",
    network_commands={
        "power_on": NetworkCommand("power_on", "RAW", "PWR01", {}),
        "power_off": NetworkCommand("power_off", "RAW", "PWR00", {}),
        "power_query": NetworkCommand("power_query", "RAW", "PWRQSTN", {}),
        "vol_up": NetworkCommand("vol_up", "RAW", "MVLUP", {}),
        "vol_down": NetworkCommand("vol_down", "RAW", "MVLDOWN", {}),
        "vol_set_50": NetworkCommand("vol_set_50", "RAW", "MVL32", {}),
        "mute_on": NetworkCommand("mute_on", "RAW", "AMT01", {}),
        "mute_off": NetworkCommand("mute_off", "RAW", "AMT00", {}),
        "input_cbl_sat": NetworkCommand("input_cbl_sat", "RAW", "SLI01", {}),
        "input_game": NetworkCommand("input_game", "RAW", "SLI02", {}),
        "input_aux": NetworkCommand("input_aux", "RAW", "SLI03", {}),
        "input_pc": NetworkCommand("input_pc", "RAW", "SLI05", {}),
        "input_bd_dvd": NetworkCommand("input_bd_dvd", "RAW", "SLI10", {}),
        "input_strm_box": NetworkCommand("input_strm_box", "RAW", "SLI11", {}),
        "input_tv": NetworkCommand("input_tv", "RAW", "SLI12", {}),
        "input_cd": NetworkCommand("input_cd", "RAW", "SLI23", {}),
        "input_phono": NetworkCommand("input_phono", "RAW", "SLI22", {}),
        "input_tuner": NetworkCommand("input_tuner", "RAW", "SLI26", {}),
        "input_usb": NetworkCommand("input_usb", "RAW", "SLI29", {}),
        "input_bluetooth": NetworkCommand("input_bluetooth", "RAW", "SLI2E", {}),
        "input_network": NetworkCommand("input_network", "RAW", "SLI2B", {}),
        "listening_mode_stereo": NetworkCommand("listening_mode_stereo", "RAW", "LMD00", {}),
        "listening_mode_direct": NetworkCommand("listening_mode_direct", "RAW", "LMD01", {}),
        "listening_mode_surround": NetworkCommand("listening_mode_surround", "RAW", "LMD02", {}),
        "listening_mode_thx": NetworkCommand("listening_mode_thx", "RAW", "LMD04", {}),
        "zone2_power_on": NetworkCommand("zone2_power_on", "RAW", "ZPW01", {}),
        "zone2_power_off": NetworkCommand("zone2_power_off", "RAW", "ZPW00", {}),
    },
)
register_profile(ONKYO_AVR_NETWORK)
