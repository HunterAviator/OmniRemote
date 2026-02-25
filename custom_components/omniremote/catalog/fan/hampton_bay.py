"""Hampton Bay ceiling fan profiles (RF 303MHz)."""

# Hampton Bay FAN-11T remote (common DIP switch based)
HAMPTON_BAY_FAN_RF = DeviceProfile(
    id="hampton_bay_fan_rf",
    name="Hampton Bay Ceiling Fan (RF)",
    brand="Hampton Bay",
    category="fan",
    model_years="2010+",
    description="Hampton Bay ceiling fans with RF remote (FAN-11T, FAN-53T). Uses 303.875MHz.",
    control_methods=[ControlMethod.RF],
    logo_url=BRAND_LOGOS.get("hampton_bay", ""),
    rf_codes={
        # DIP switch code 0000 (all off) - adjust based on actual DIP settings
        "light_on": RFCode("light_on", 303875000, "FAN11T", "0000_LIGHT_ON"),
        "light_off": RFCode("light_off", 303875000, "FAN11T", "0000_LIGHT_OFF"),
        "light_toggle": RFCode("light_toggle", 303875000, "FAN11T", "0000_LIGHT_TOGGLE"),
        "fan_off": RFCode("fan_off", 303875000, "FAN11T", "0000_FAN_OFF"),
        "fan_low": RFCode("fan_low", 303875000, "FAN11T", "0000_FAN_LOW"),
        "fan_med": RFCode("fan_med", 303875000, "FAN11T", "0000_FAN_MED"),
        "fan_high": RFCode("fan_high", 303875000, "FAN11T", "0000_FAN_HIGH"),
        "reverse": RFCode("reverse", 303875000, "FAN11T", "0000_FAN_REVERSE"),
    },
)
register_profile(HAMPTON_BAY_FAN_RF)
