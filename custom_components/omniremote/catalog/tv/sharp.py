"""Sharp TV profiles."""

# =============================================================================
# Sharp Aquos TV - IR Control
# =============================================================================
SHARP_TV_IR = DeviceProfile(
    id="sharp_tv_ir",
    name="Sharp Aquos TV (IR)",
    brand="Sharp",
    category="tv",
    model_years="2010+",
    description="Sharp Aquos LCD/LED TVs - Standard IR codes.",
    control_methods=[ControlMethod.IR],
    logo_url=BRAND_LOGOS.get("sharp", ""),
    ir_codes={
        # Power
        "power": nec(0x45, 0x40, "power"),
        "power_on": nec(0x45, 0x41, "power_on"),
        "power_off": nec(0x45, 0x42, "power_off"),
        
        # Volume
        "vol_up": nec(0x45, 0x44, "vol_up"),
        "vol_down": nec(0x45, 0x45, "vol_down"),
        "mute": nec(0x45, 0x48, "mute"),
        
        # Channels
        "ch_up": nec(0x45, 0x46, "ch_up"),
        "ch_down": nec(0x45, 0x47, "ch_down"),
        "prev_ch": nec(0x45, 0x49, "prev_ch"),
        
        # Input
        "input": nec(0x45, 0x4A, "input"),
        "hdmi1": nec(0x45, 0x5A, "hdmi1"),
        "hdmi2": nec(0x45, 0x5B, "hdmi2"),
        "hdmi3": nec(0x45, 0x5C, "hdmi3"),
        "hdmi4": nec(0x45, 0x5D, "hdmi4"),
        "av1": nec(0x45, 0x55, "av1"),
        "component1": nec(0x45, 0x57, "component1"),
        "tv": nec(0x45, 0x52, "tv"),
        
        # Navigation
        "menu": nec(0x45, 0x4B, "menu"),
        "up": nec(0x45, 0x4C, "up"),
        "down": nec(0x45, 0x4D, "down"),
        "left": nec(0x45, 0x4E, "left"),
        "right": nec(0x45, 0x4F, "right"),
        "enter": nec(0x45, 0x50, "enter"),
        "back": nec(0x45, 0x51, "back"),
        "exit": nec(0x45, 0x54, "exit"),
        
        # Smart Features
        "smart_central": nec(0x45, 0x60, "smart_central"),
        "apps": nec(0x45, 0x61, "apps"),
        "netflix": nec(0x45, 0x62, "netflix"),
        
        # Media
        "play": nec(0x45, 0x70, "play"),
        "pause": nec(0x45, 0x71, "pause"),
        "stop": nec(0x45, 0x72, "stop"),
        "rewind": nec(0x45, 0x73, "rewind"),
        "fast_forward": nec(0x45, 0x74, "fast_forward"),
        
        # Numbers
        "0": nec(0x45, 0x00, "0"),
        "1": nec(0x45, 0x01, "1"),
        "2": nec(0x45, 0x02, "2"),
        "3": nec(0x45, 0x03, "3"),
        "4": nec(0x45, 0x04, "4"),
        "5": nec(0x45, 0x05, "5"),
        "6": nec(0x45, 0x06, "6"),
        "7": nec(0x45, 0x07, "7"),
        "8": nec(0x45, 0x08, "8"),
        "9": nec(0x45, 0x09, "9"),
        
        # Picture/Sound
        "picture_mode": nec(0x45, 0x80, "picture_mode"),
        "aspect": nec(0x45, 0x81, "aspect"),
        "sound_mode": nec(0x45, 0x82, "sound_mode"),
    },
)
register_profile(SHARP_TV_IR)


# =============================================================================
# Sharp Roku TV - IR Control
# =============================================================================
SHARP_ROKU_TV = DeviceProfile(
    id="sharp_roku_tv",
    name="Sharp Roku TV",
    brand="Sharp",
    category="tv",
    model_years="2017+",
    description="Sharp Roku TVs - Uses Roku IR codes.",
    control_methods=[ControlMethod.IR, ControlMethod.NETWORK],
    logo_url=BRAND_LOGOS.get("sharp", ""),
    network_port=8060,
    network_protocol="ecp",
    ir_codes={
        # Power
        "power": nec(0xEE, 0x8D, "power"),
        
        # Volume
        "vol_up": nec(0xEE, 0x80, "vol_up"),
        "vol_down": nec(0xEE, 0x81, "vol_down"),
        "mute": nec(0xEE, 0x8C, "mute"),
        
        # Navigation
        "home": nec(0xEE, 0x8E, "home"),
        "back": nec(0xEE, 0x83, "back"),
        "up": nec(0xEE, 0x9A, "up"),
        "down": nec(0xEE, 0x9B, "down"),
        "left": nec(0xEE, 0x9C, "left"),
        "right": nec(0xEE, 0x9D, "right"),
        "enter": nec(0xEE, 0x9E, "enter"),
        
        # Media
        "play": nec(0xEE, 0x8F, "play"),
        "pause": nec(0xEE, 0x8F, "pause"),
        "rewind": nec(0xEE, 0x8B, "rewind"),
        "fast_forward": nec(0xEE, 0x8A, "fast_forward"),
        
        # Options
        "options": nec(0xEE, 0x82, "options"),
        "replay": nec(0xEE, 0x86, "replay"),
    },
)
register_profile(SHARP_ROKU_TV)
