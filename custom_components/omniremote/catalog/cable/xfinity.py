"""Xfinity/Comcast cable box profiles."""

# =============================================================================
# Xfinity X1 DVR - IR Control
# =============================================================================
XFINITY_X1_IR = DeviceProfile(
    id="xfinity_x1_ir",
    name="Xfinity X1 DVR (IR)",
    brand="Xfinity",
    category="cable",
    model_years="2012+",
    description="Xfinity X1 cable box/DVR - Standard IR codes.",
    control_methods=[ControlMethod.IR],
    logo_url="https://upload.wikimedia.org/wikipedia/commons/6/66/Xfinity_logo.svg",
    ir_codes={
        # Power
        "power": nec(0x1E, 0x10, "power"),
        "power_on": nec(0x1E, 0x6C, "power_on"),
        "power_off": nec(0x1E, 0x6D, "power_off"),
        
        # Channels
        "ch_up": nec(0x1E, 0x20, "ch_up"),
        "ch_down": nec(0x1E, 0x21, "ch_down"),
        "prev_ch": nec(0x1E, 0x22, "prev_ch"),
        
        # Navigation
        "guide": nec(0x1E, 0x2A, "guide"),
        "menu": nec(0x1E, 0x2B, "menu"),
        "info": nec(0x1E, 0x2C, "info"),
        "xfinity": nec(0x1E, 0x2D, "xfinity"),  # Xfinity home button
        "up": nec(0x1E, 0x58, "up"),
        "down": nec(0x1E, 0x59, "down"),
        "left": nec(0x1E, 0x5A, "left"),
        "right": nec(0x1E, 0x5B, "right"),
        "ok": nec(0x1E, 0x5C, "ok"),
        "back": nec(0x1E, 0x24, "back"),
        "exit": nec(0x1E, 0x25, "exit"),
        "last": nec(0x1E, 0x26, "last"),
        
        # DVR Controls
        "dvr": nec(0x1E, 0x4D, "dvr"),
        "record": nec(0x1E, 0x37, "record"),
        "play": nec(0x1E, 0x30, "play"),
        "pause": nec(0x1E, 0x31, "pause"),
        "stop": nec(0x1E, 0x32, "stop"),
        "rewind": nec(0x1E, 0x34, "rewind"),
        "fast_forward": nec(0x1E, 0x35, "fast_forward"),
        "replay": nec(0x1E, 0x36, "replay"),  # 7-second replay
        "advance": nec(0x1E, 0x38, "advance"),  # 30-second skip
        
        # Number Pad
        "0": nec(0x1E, 0x00, "0"),
        "1": nec(0x1E, 0x01, "1"),
        "2": nec(0x1E, 0x02, "2"),
        "3": nec(0x1E, 0x03, "3"),
        "4": nec(0x1E, 0x04, "4"),
        "5": nec(0x1E, 0x05, "5"),
        "6": nec(0x1E, 0x06, "6"),
        "7": nec(0x1E, 0x07, "7"),
        "8": nec(0x1E, 0x08, "8"),
        "9": nec(0x1E, 0x09, "9"),
        
        # Color/Letter Buttons
        "a": nec(0x1E, 0x40, "a"),  # Red/A
        "b": nec(0x1E, 0x41, "b"),  # Green/B
        "c": nec(0x1E, 0x42, "c"),  # Yellow/C
        "d": nec(0x1E, 0x43, "d"),  # Blue/D
        
        # Special
        "on_demand": nec(0x1E, 0x4A, "on_demand"),
        "page_up": nec(0x1E, 0x45, "page_up"),
        "page_down": nec(0x1E, 0x46, "page_down"),
        "pip": nec(0x1E, 0x47, "pip"),
        "swap": nec(0x1E, 0x48, "swap"),
        "live": nec(0x1E, 0x49, "live"),
        "favorites": nec(0x1E, 0x4B, "favorites"),
        "day_minus": nec(0x1E, 0x4C, "day_minus"),
        "day_plus": nec(0x1E, 0x4E, "day_plus"),
    },
)
register_profile(XFINITY_X1_IR)


# =============================================================================
# Xfinity Flex - Streaming Box
# =============================================================================
XFINITY_FLEX = DeviceProfile(
    id="xfinity_flex",
    name="Xfinity Flex",
    brand="Xfinity",
    category="streamer",
    model_years="2019+",
    description="Xfinity Flex streaming box - IR and Voice control.",
    control_methods=[ControlMethod.IR],
    logo_url="https://upload.wikimedia.org/wikipedia/commons/6/66/Xfinity_logo.svg",
    ir_codes={
        # Power
        "power": nec(0x1E, 0x10, "power"),
        
        # Navigation
        "home": nec(0x1E, 0x2D, "home"),
        "guide": nec(0x1E, 0x2A, "guide"),
        "info": nec(0x1E, 0x2C, "info"),
        "up": nec(0x1E, 0x58, "up"),
        "down": nec(0x1E, 0x59, "down"),
        "left": nec(0x1E, 0x5A, "left"),
        "right": nec(0x1E, 0x5B, "right"),
        "ok": nec(0x1E, 0x5C, "ok"),
        "back": nec(0x1E, 0x24, "back"),
        
        # Media
        "play": nec(0x1E, 0x30, "play"),
        "pause": nec(0x1E, 0x31, "pause"),
        "rewind": nec(0x1E, 0x34, "rewind"),
        "fast_forward": nec(0x1E, 0x35, "fast_forward"),
        
        # Voice
        "voice": nec(0x1E, 0x60, "voice"),
    },
)
register_profile(XFINITY_FLEX)


# =============================================================================
# Motorola/Arris DCX3600 - Common Xfinity Box
# =============================================================================
MOTOROLA_DCX3600_IR = DeviceProfile(
    id="motorola_dcx3600_ir",
    name="Motorola DCX3600-M (IR)",
    brand="Motorola",
    category="cable",
    model_years="2014+",
    description="Motorola/Arris DCX3600-M cable box - Common Xfinity equipment.",
    control_methods=[ControlMethod.IR],
    logo_url="https://upload.wikimedia.org/wikipedia/commons/4/47/Motorola_logo.svg",
    ir_codes={
        # Power
        "power": nec(0x14, 0x10, "power"),
        
        # Channels
        "ch_up": nec(0x14, 0x20, "ch_up"),
        "ch_down": nec(0x14, 0x21, "ch_down"),
        
        # Navigation
        "guide": nec(0x14, 0x2A, "guide"),
        "menu": nec(0x14, 0x2B, "menu"),
        "info": nec(0x14, 0x2C, "info"),
        "up": nec(0x14, 0x58, "up"),
        "down": nec(0x14, 0x59, "down"),
        "left": nec(0x14, 0x5A, "left"),
        "right": nec(0x14, 0x5B, "right"),
        "select": nec(0x14, 0x5C, "select"),
        "exit": nec(0x14, 0x25, "exit"),
        
        # DVR
        "record": nec(0x14, 0x37, "record"),
        "play": nec(0x14, 0x30, "play"),
        "pause": nec(0x14, 0x31, "pause"),
        "stop": nec(0x14, 0x32, "stop"),
        "rewind": nec(0x14, 0x34, "rewind"),
        "fast_forward": nec(0x14, 0x35, "fast_forward"),
        
        # Numbers
        "0": nec(0x14, 0x00, "0"),
        "1": nec(0x14, 0x01, "1"),
        "2": nec(0x14, 0x02, "2"),
        "3": nec(0x14, 0x03, "3"),
        "4": nec(0x14, 0x04, "4"),
        "5": nec(0x14, 0x05, "5"),
        "6": nec(0x14, 0x06, "6"),
        "7": nec(0x14, 0x07, "7"),
        "8": nec(0x14, 0x08, "8"),
        "9": nec(0x14, 0x09, "9"),
    },
)
register_profile(MOTOROLA_DCX3600_IR)
