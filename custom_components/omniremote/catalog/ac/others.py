"""Mitsubishi and Fujitsu AC profiles."""

# =============================================================================
# Mitsubishi Electric AC - IR Control
# =============================================================================
MITSUBISHI_AC_IR = DeviceProfile(
    id="mitsubishi_ac_ir",
    name="Mitsubishi Electric AC (IR)",
    brand="Mitsubishi",
    category="ac",
    model_years="2010+",
    description="Mitsubishi Electric mini-split AC units - IR control.",
    control_methods=[ControlMethod.IR],
    logo_url="https://upload.wikimedia.org/wikipedia/commons/0/08/Mitsubishi_Electric_Logo.svg",
    ir_codes={
        # Power
        "power": nec(0xE3, 0x00, "power"),
        "power_on": nec(0xE3, 0x01, "power_on"),
        "power_off": nec(0xE3, 0x02, "power_off"),
        
        # Mode
        "mode_cool": nec(0xE3, 0x10, "mode_cool"),
        "mode_heat": nec(0xE3, 0x11, "mode_heat"),
        "mode_dry": nec(0xE3, 0x12, "mode_dry"),
        "mode_fan": nec(0xE3, 0x13, "mode_fan"),
        "mode_auto": nec(0xE3, 0x14, "mode_auto"),
        
        # Temperature (°C)
        "temp_up": nec(0xE3, 0x20, "temp_up"),
        "temp_down": nec(0xE3, 0x21, "temp_down"),
        "temp_18": nec(0xE3, 0x30, "temp_18"),
        "temp_19": nec(0xE3, 0x31, "temp_19"),
        "temp_20": nec(0xE3, 0x32, "temp_20"),
        "temp_21": nec(0xE3, 0x33, "temp_21"),
        "temp_22": nec(0xE3, 0x34, "temp_22"),
        "temp_23": nec(0xE3, 0x35, "temp_23"),
        "temp_24": nec(0xE3, 0x36, "temp_24"),
        "temp_25": nec(0xE3, 0x37, "temp_25"),
        "temp_26": nec(0xE3, 0x38, "temp_26"),
        "temp_27": nec(0xE3, 0x39, "temp_27"),
        "temp_28": nec(0xE3, 0x3A, "temp_28"),
        
        # Fan Speed
        "fan_auto": nec(0xE3, 0x40, "fan_auto"),
        "fan_low": nec(0xE3, 0x41, "fan_low"),
        "fan_med": nec(0xE3, 0x42, "fan_med"),
        "fan_high": nec(0xE3, 0x43, "fan_high"),
        "fan_quiet": nec(0xE3, 0x44, "fan_quiet"),
        "fan_powerful": nec(0xE3, 0x45, "fan_powerful"),
        
        # Swing
        "swing_off": nec(0xE3, 0x50, "swing_off"),
        "swing_vertical": nec(0xE3, 0x51, "swing_vertical"),
        "swing_horizontal": nec(0xE3, 0x52, "swing_horizontal"),
        "swing_both": nec(0xE3, 0x53, "swing_both"),
        
        # Features
        "timer": nec(0xE3, 0x60, "timer"),
        "sleep": nec(0xE3, 0x61, "sleep"),
        "eco": nec(0xE3, 0x62, "eco"),
        "isave": nec(0xE3, 0x63, "isave"),
        "clean": nec(0xE3, 0x64, "clean"),
    },
)
register_profile(MITSUBISHI_AC_IR)


# =============================================================================
# Fujitsu AC - IR Control
# =============================================================================
FUJITSU_AC_IR = DeviceProfile(
    id="fujitsu_ac_ir",
    name="Fujitsu AC (IR)",
    brand="Fujitsu",
    category="ac",
    model_years="2010+",
    description="Fujitsu General mini-split AC units - IR control.",
    control_methods=[ControlMethod.IR],
    logo_url="https://upload.wikimedia.org/wikipedia/commons/5/5a/Fujitsu_Logo.svg",
    ir_codes={
        # Power
        "power": nec(0x14, 0x63, "power"),
        "power_on": nec(0x14, 0x64, "power_on"),
        "power_off": nec(0x14, 0x65, "power_off"),
        
        # Mode
        "mode_cool": nec(0x14, 0x70, "mode_cool"),
        "mode_heat": nec(0x14, 0x71, "mode_heat"),
        "mode_dry": nec(0x14, 0x72, "mode_dry"),
        "mode_fan": nec(0x14, 0x73, "mode_fan"),
        "mode_auto": nec(0x14, 0x74, "mode_auto"),
        
        # Temperature
        "temp_up": nec(0x14, 0x80, "temp_up"),
        "temp_down": nec(0x14, 0x81, "temp_down"),
        "temp_18": nec(0x14, 0x90, "temp_18"),
        "temp_20": nec(0x14, 0x92, "temp_20"),
        "temp_22": nec(0x14, 0x94, "temp_22"),
        "temp_24": nec(0x14, 0x96, "temp_24"),
        "temp_26": nec(0x14, 0x98, "temp_26"),
        "temp_28": nec(0x14, 0x9A, "temp_28"),
        
        # Fan Speed
        "fan_auto": nec(0x14, 0xA0, "fan_auto"),
        "fan_low": nec(0x14, 0xA1, "fan_low"),
        "fan_med": nec(0x14, 0xA2, "fan_med"),
        "fan_high": nec(0x14, 0xA3, "fan_high"),
        "fan_quiet": nec(0x14, 0xA4, "fan_quiet"),
        
        # Swing
        "swing_off": nec(0x14, 0xB0, "swing_off"),
        "swing_on": nec(0x14, 0xB1, "swing_on"),
        
        # Features
        "timer": nec(0x14, 0xC0, "timer"),
        "economy": nec(0x14, 0xC1, "economy"),
        "powerful": nec(0x14, 0xC2, "powerful"),
    },
)
register_profile(FUJITSU_AC_IR)


# =============================================================================
# Carrier AC - IR Control
# =============================================================================
CARRIER_AC_IR = DeviceProfile(
    id="carrier_ac_ir",
    name="Carrier AC (IR)",
    brand="Carrier",
    category="ac",
    model_years="2010+",
    description="Carrier air conditioners - IR control.",
    control_methods=[ControlMethod.IR],
    logo_url="https://upload.wikimedia.org/wikipedia/commons/a/ae/Carrier_logo.svg",
    ir_codes={
        # Power
        "power": nec(0x60, 0x00, "power"),
        "power_on": nec(0x60, 0x01, "power_on"),
        "power_off": nec(0x60, 0x02, "power_off"),
        
        # Mode
        "mode_cool": nec(0x60, 0x10, "mode_cool"),
        "mode_heat": nec(0x60, 0x11, "mode_heat"),
        "mode_dry": nec(0x60, 0x12, "mode_dry"),
        "mode_fan": nec(0x60, 0x13, "mode_fan"),
        "mode_auto": nec(0x60, 0x14, "mode_auto"),
        
        # Temperature
        "temp_up": nec(0x60, 0x20, "temp_up"),
        "temp_down": nec(0x60, 0x21, "temp_down"),
        
        # Fan Speed
        "fan_auto": nec(0x60, 0x30, "fan_auto"),
        "fan_low": nec(0x60, 0x31, "fan_low"),
        "fan_med": nec(0x60, 0x32, "fan_med"),
        "fan_high": nec(0x60, 0x33, "fan_high"),
        
        # Swing
        "swing": nec(0x60, 0x40, "swing"),
        
        # Features
        "timer": nec(0x60, 0x50, "timer"),
        "sleep": nec(0x60, 0x51, "sleep"),
        "turbo": nec(0x60, 0x52, "turbo"),
    },
)
register_profile(CARRIER_AC_IR)
