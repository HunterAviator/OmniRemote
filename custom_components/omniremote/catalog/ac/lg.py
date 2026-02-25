"""LG AC profiles."""

LG_AC_IR = DeviceProfile(
    id="lg_ac_ir",
    name="LG Air Conditioner (IR)",
    brand="LG",
    category="ac",
    model_years="2015+",
    description="LG split system and window AC units.",
    control_methods=[ControlMethod.IR],
    logo_url=BRAND_LOGOS.get("lg_ac", ""),
    ir_codes={
        "power": nec(0x88, 0x08, "power"),
        "mode_cool": nec(0x88, 0x00, "mode_cool"),
        "mode_heat": nec(0x88, 0x04, "mode_heat"),
        "mode_dry": nec(0x88, 0x02, "mode_dry"),
        "mode_fan": nec(0x88, 0x06, "mode_fan"),
        "mode_auto": nec(0x88, 0x08, "mode_auto"),
        "temp_up": nec(0x88, 0x40, "temp_up"),
        "temp_down": nec(0x88, 0x44, "temp_down"),
        "fan_low": nec(0x88, 0x09, "fan_low"),
        "fan_med": nec(0x88, 0x05, "fan_med"),
        "fan_high": nec(0x88, 0x03, "fan_high"),
        "fan_auto": nec(0x88, 0x01, "fan_auto"),
        "swing_on": nec(0x88, 0x10, "swing_on"),
        "swing_off": nec(0x88, 0x14, "swing_off"),
        "timer_on": nec(0x88, 0x20, "timer_on"),
        "timer_off": nec(0x88, 0x24, "timer_off"),
        "sleep": nec(0x88, 0x30, "sleep"),
        "jet_cool": nec(0x88, 0x50, "jet_cool"),
        "energy_saving": nec(0x88, 0x60, "energy_saving"),
    },
)
register_profile(LG_AC_IR)
