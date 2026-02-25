"""LG Blu-ray player profiles."""

# =============================================================================
# LG Blu-ray Player - Standard IR
# =============================================================================
LG_BLURAY_IR = DeviceProfile(
    id="lg_bluray_ir",
    name="LG Blu-ray Player (IR)",
    brand="LG",
    category="bluray",
    model_years="2010+",
    description="LG Blu-ray and DVD players - Standard NEC IR codes.",
    control_methods=[ControlMethod.IR],
    logo_url=BRAND_LOGOS.get("lg", ""),
    ir_codes={
        # Power
        "power": nec(0xB4, 0x40, "power"),
        "power_on": nec(0xB4, 0x41, "power_on"),
        "power_off": nec(0xB4, 0x42, "power_off"),
        
        # Disc
        "eject": nec(0xB4, 0x16, "eject"),
        
        # Playback
        "play": nec(0xB4, 0x04, "play"),
        "pause": nec(0xB4, 0x07, "pause"),
        "stop": nec(0xB4, 0x06, "stop"),
        "rewind": nec(0xB4, 0x08, "rewind"),
        "fast_forward": nec(0xB4, 0x09, "fast_forward"),
        "slow_rewind": nec(0xB4, 0x0A, "slow_rewind"),
        "slow_forward": nec(0xB4, 0x0B, "slow_forward"),
        "prev_chapter": nec(0xB4, 0x0E, "prev_chapter"),
        "next_chapter": nec(0xB4, 0x0F, "next_chapter"),
        "prev_track": nec(0xB4, 0x0C, "prev_track"),
        "next_track": nec(0xB4, 0x0D, "next_track"),
        
        # Navigation
        "home": nec(0xB4, 0xAB, "home"),
        "menu": nec(0xB4, 0x43, "menu"),
        "title_menu": nec(0xB4, 0x4F, "title_menu"),
        "popup_menu": nec(0xB4, 0x50, "popup_menu"),
        "up": nec(0xB4, 0x40, "up"),
        "down": nec(0xB4, 0x41, "down"),
        "left": nec(0xB4, 0x42, "left"),
        "right": nec(0xB4, 0x43, "right"),
        "enter": nec(0xB4, 0x44, "enter"),
        "back": nec(0xB4, 0x28, "back"),
        
        # Info/Display
        "info": nec(0xB4, 0x55, "info"),
        "display": nec(0xB4, 0x56, "display"),
        
        # Audio/Video Settings
        "audio": nec(0xB4, 0x52, "audio"),
        "subtitle": nec(0xB4, 0x53, "subtitle"),
        "angle": nec(0xB4, 0x54, "angle"),
        "repeat": nec(0xB4, 0x57, "repeat"),
        "ab_repeat": nec(0xB4, 0x58, "ab_repeat"),
        "zoom": nec(0xB4, 0x59, "zoom"),
        
        # Color Buttons
        "red": nec(0xB4, 0x60, "red"),
        "green": nec(0xB4, 0x61, "green"),
        "yellow": nec(0xB4, 0x62, "yellow"),
        "blue": nec(0xB4, 0x63, "blue"),
        
        # Numbers
        "0": nec(0xB4, 0x10, "0"),
        "1": nec(0xB4, 0x11, "1"),
        "2": nec(0xB4, 0x12, "2"),
        "3": nec(0xB4, 0x13, "3"),
        "4": nec(0xB4, 0x14, "4"),
        "5": nec(0xB4, 0x15, "5"),
        "6": nec(0xB4, 0x16, "6"),
        "7": nec(0xB4, 0x17, "7"),
        "8": nec(0xB4, 0x18, "8"),
        "9": nec(0xB4, 0x19, "9"),
    },
)
register_profile(LG_BLURAY_IR)


# =============================================================================
# LG 4K Ultra HD Blu-ray Player
# =============================================================================
LG_4K_BLURAY_IR = DeviceProfile(
    id="lg_4k_bluray_ir",
    name="LG 4K UHD Blu-ray (IR)",
    brand="LG",
    category="bluray",
    model_years="2017+",
    description="LG 4K Ultra HD Blu-ray players (UBK80, UBK90, etc.).",
    control_methods=[ControlMethod.IR],
    logo_url=BRAND_LOGOS.get("lg", ""),
    ir_codes={
        # Power
        "power": nec(0xB4, 0x40, "power"),
        
        # Disc
        "eject": nec(0xB4, 0x16, "eject"),
        
        # Playback
        "play": nec(0xB4, 0x04, "play"),
        "pause": nec(0xB4, 0x07, "pause"),
        "stop": nec(0xB4, 0x06, "stop"),
        "rewind": nec(0xB4, 0x08, "rewind"),
        "fast_forward": nec(0xB4, 0x09, "fast_forward"),
        "prev_chapter": nec(0xB4, 0x0E, "prev_chapter"),
        "next_chapter": nec(0xB4, 0x0F, "next_chapter"),
        
        # Navigation
        "home": nec(0xB4, 0xAB, "home"),
        "menu": nec(0xB4, 0x43, "menu"),
        "title_menu": nec(0xB4, 0x4F, "title_menu"),
        "popup_menu": nec(0xB4, 0x50, "popup_menu"),
        "up": nec(0xB4, 0x40, "up"),
        "down": nec(0xB4, 0x41, "down"),
        "left": nec(0xB4, 0x42, "left"),
        "right": nec(0xB4, 0x43, "right"),
        "enter": nec(0xB4, 0x44, "enter"),
        "back": nec(0xB4, 0x28, "back"),
        
        # Info
        "info": nec(0xB4, 0x55, "info"),
        
        # Audio/Subtitle
        "audio": nec(0xB4, 0x52, "audio"),
        "subtitle": nec(0xB4, 0x53, "subtitle"),
        
        # HDR Settings
        "hdr": nec(0xB4, 0x70, "hdr"),
        "dolby_vision": nec(0xB4, 0x71, "dolby_vision"),
    },
)
register_profile(LG_4K_BLURAY_IR)
