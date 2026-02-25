"""Hunter ceiling fan profiles."""

HUNTER_FAN_RF = DeviceProfile(
    id="hunter_fan_rf",
    name="Hunter Ceiling Fan (RF)",
    brand="Hunter",
    category="fan",
    model_years="2015+",
    description="Hunter ceiling fans with SimpleConnect RF remote (303MHz).",
    control_methods=[ControlMethod.RF],
    logo_url=BRAND_LOGOS.get("hunter", ""),
    rf_codes={
        "light_on": RFCode("light_on", 303000000, "Hunter", "LIGHT_ON"),
        "light_off": RFCode("light_off", 303000000, "Hunter", "LIGHT_OFF"),
        "light_dim_up": RFCode("light_dim_up", 303000000, "Hunter", "LIGHT_DIM_UP"),
        "light_dim_down": RFCode("light_dim_down", 303000000, "Hunter", "LIGHT_DIM_DOWN"),
        "fan_off": RFCode("fan_off", 303000000, "Hunter", "FAN_OFF"),
        "fan_low": RFCode("fan_low", 303000000, "Hunter", "FAN_LOW"),
        "fan_med": RFCode("fan_med", 303000000, "Hunter", "FAN_MED"),
        "fan_high": RFCode("fan_high", 303000000, "Hunter", "FAN_HIGH"),
        "reverse": RFCode("reverse", 303000000, "Hunter", "FAN_REVERSE"),
        "breeze": RFCode("breeze", 303000000, "Hunter", "FAN_BREEZE"),
    },
)
register_profile(HUNTER_FAN_RF)

# Hunter with IR remote
HUNTER_FAN_IR = DeviceProfile(
    id="hunter_fan_ir",
    name="Hunter Ceiling Fan (IR)",
    brand="Hunter",
    category="fan",
    model_years="2010+",
    description="Hunter ceiling fans with IR remote.",
    control_methods=[ControlMethod.IR],
    logo_url=BRAND_LOGOS.get("hunter", ""),
    ir_codes={
        "light_on": nec(0x50, 0x01, "light_on"),
        "light_off": nec(0x50, 0x02, "light_off"),
        "fan_off": nec(0x50, 0x10, "fan_off"),
        "fan_low": nec(0x50, 0x11, "fan_low"),
        "fan_med": nec(0x50, 0x12, "fan_med"),
        "fan_high": nec(0x50, 0x13, "fan_high"),
        "reverse": nec(0x50, 0x20, "reverse"),
    },
)
register_profile(HUNTER_FAN_IR)
