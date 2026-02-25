"""TCL TV profiles (mostly Roku-based)."""

# =============================================================================
# TCL Roku TV - IR
# =============================================================================
TCL_ROKU_TV_IR = DeviceProfile(
    id="tcl_roku_tv_ir",
    name="TCL Roku TV (IR)",
    brand="TCL",
    category="tv",
    model_years="2015+",
    description="TCL Roku TVs - uses Roku IR codes.",
    control_methods=[ControlMethod.IR],
    logo_url=BRAND_LOGOS.get("tcl", ""),
    ir_codes={
        "power": nec(0xEE, 0x8D, "power"),
        "vol_up": nec(0xEE, 0x84, "vol_up"),
        "vol_down": nec(0xEE, 0x85, "vol_down"),
        "mute": nec(0xEE, 0x8C, "mute"),
        "home": nec(0xEE, 0x8E, "home"),
        "back": nec(0xEE, 0x83, "back"),
        "up": nec(0xEE, 0x9A, "up"),
        "down": nec(0xEE, 0x9B, "down"),
        "left": nec(0xEE, 0x9C, "left"),
        "right": nec(0xEE, 0x9D, "right"),
        "enter": nec(0xEE, 0x9E, "enter"),
        "ok": nec(0xEE, 0x9E, "ok"),
        "play": nec(0xEE, 0x8F, "play"),
        "pause": nec(0xEE, 0x8F, "pause"),
        "rewind": nec(0xEE, 0x8B, "rewind"),
        "fast_forward": nec(0xEE, 0x8A, "fast_forward"),
        "replay": nec(0xEE, 0x86, "replay"),
        "options": nec(0xEE, 0x82, "options"),
        "sleep": nec(0xEE, 0x92, "sleep"),
        "input": nec(0xEE, 0x90, "input"),
        "netflix": nec(0xEE, 0x96, "netflix"),
        "hulu": nec(0xEE, 0x97, "hulu"),
        "disney_plus": nec(0xEE, 0x99, "disney_plus"),
        "apple_tv": nec(0xEE, 0x9F, "apple_tv"),
    },
)
register_profile(TCL_ROKU_TV_IR)

# =============================================================================
# TCL Google TV - IR
# =============================================================================
TCL_GOOGLE_TV_IR = DeviceProfile(
    id="tcl_google_tv_ir",
    name="TCL Google TV (IR)",
    brand="TCL",
    category="tv",
    model_years="2021+",
    description="TCL Google TVs with Google TV interface.",
    control_methods=[ControlMethod.IR],
    logo_url=BRAND_LOGOS.get("tcl", ""),
    ir_codes={
        "power": nec(0x40, 0x12, "power"),
        "vol_up": nec(0x40, 0x1A, "vol_up"),
        "vol_down": nec(0x40, 0x1E, "vol_down"),
        "mute": nec(0x40, 0x10, "mute"),
        "home": nec(0x40, 0x2A, "home"),
        "back": nec(0x40, 0x23, "back"),
        "up": nec(0x40, 0x1B, "up"),
        "down": nec(0x40, 0x1F, "down"),
        "left": nec(0x40, 0x19, "left"),
        "right": nec(0x40, 0x18, "right"),
        "enter": nec(0x40, 0x1C, "enter"),
        "input": nec(0x40, 0x0F, "input"),
        "0": nec(0x40, 0x00, "0"),
        "1": nec(0x40, 0x01, "1"),
        "2": nec(0x40, 0x02, "2"),
        "3": nec(0x40, 0x03, "3"),
        "4": nec(0x40, 0x04, "4"),
        "5": nec(0x40, 0x05, "5"),
        "6": nec(0x40, 0x06, "6"),
        "7": nec(0x40, 0x07, "7"),
        "8": nec(0x40, 0x08, "8"),
        "9": nec(0x40, 0x09, "9"),
    },
)
register_profile(TCL_GOOGLE_TV_IR)
