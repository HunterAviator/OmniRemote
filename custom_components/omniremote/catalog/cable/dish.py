"""Dish Network receiver profiles."""

# =============================================================================
# Dish Network - Standard IR (Hopper/Joey)
# =============================================================================
DISH_HOPPER_IR = DeviceProfile(
    id="dish_hopper_ir",
    name="Dish Hopper/Joey (IR)",
    brand="Dish Network",
    category="cable",
    model_years="2012+",
    description="Dish Network Hopper and Joey receivers - Standard IR control.",
    control_methods=[ControlMethod.IR],
    logo_url="https://upload.wikimedia.org/wikipedia/commons/d/da/Dish_Network_Logo.svg",
    ir_codes={
        # Power
        "power": nec(0x00, 0x00, "power"),
        "power_on": nec(0x00, 0x64, "power_on"),
        "power_off": nec(0x00, 0x65, "power_off"),
        
        # Volume (TV control mode)
        "vol_up": nec(0x00, 0x10, "vol_up"),
        "vol_down": nec(0x00, 0x11, "vol_down"),
        "mute": nec(0x00, 0x0D, "mute"),
        
        # Channels
        "ch_up": nec(0x00, 0x20, "ch_up"),
        "ch_down": nec(0x00, 0x21, "ch_down"),
        "prev_ch": nec(0x00, 0x1B, "prev_ch"),
        
        # Navigation
        "guide": nec(0x00, 0x4F, "guide"),
        "menu": nec(0x00, 0x0B, "menu"),
        "info": nec(0x00, 0x17, "info"),
        "up": nec(0x00, 0x58, "up"),
        "down": nec(0x00, 0x59, "down"),
        "left": nec(0x00, 0x5A, "left"),
        "right": nec(0x00, 0x5B, "right"),
        "select": nec(0x00, 0x5C, "select"),
        "cancel": nec(0x00, 0x1D, "cancel"),
        "back": nec(0x00, 0x1E, "back"),
        
        # DVR Controls
        "dvr": nec(0x00, 0x6D, "dvr"),
        "record": nec(0x00, 0x38, "record"),
        "play": nec(0x00, 0x32, "play"),
        "pause": nec(0x00, 0x33, "pause"),
        "stop": nec(0x00, 0x31, "stop"),
        "rewind": nec(0x00, 0x35, "rewind"),
        "fast_forward": nec(0x00, 0x34, "fast_forward"),
        "skip_back": nec(0x00, 0x36, "skip_back"),
        "skip_forward": nec(0x00, 0x37, "skip_forward"),
        "slow": nec(0x00, 0x39, "slow"),
        
        # Number Pad
        "0": nec(0x00, 0x00, "0"),
        "1": nec(0x00, 0x01, "1"),
        "2": nec(0x00, 0x02, "2"),
        "3": nec(0x00, 0x03, "3"),
        "4": nec(0x00, 0x04, "4"),
        "5": nec(0x00, 0x05, "5"),
        "6": nec(0x00, 0x06, "6"),
        "7": nec(0x00, 0x07, "7"),
        "8": nec(0x00, 0x08, "8"),
        "9": nec(0x00, 0x09, "9"),
        "star": nec(0x00, 0x0A, "star"),
        "pound": nec(0x00, 0x0C, "pound"),
        
        # Color Buttons
        "red": nec(0x00, 0x41, "red"),
        "green": nec(0x00, 0x42, "green"),
        "yellow": nec(0x00, 0x43, "yellow"),
        "blue": nec(0x00, 0x44, "blue"),
        
        # Special
        "dish": nec(0x00, 0x52, "dish"),  # Home/Dish button
        "pip": nec(0x00, 0x48, "pip"),
        "swap": nec(0x00, 0x47, "swap"),
        "recall": nec(0x00, 0x1A, "recall"),
        "page_up": nec(0x00, 0x45, "page_up"),
        "page_down": nec(0x00, 0x46, "page_down"),
        "format": nec(0x00, 0x53, "format"),
        "sys_info": nec(0x00, 0x54, "sys_info"),
    },
)
register_profile(DISH_HOPPER_IR)


# =============================================================================
# Dish Network - Wally (Portable)
# =============================================================================
DISH_WALLY_IR = DeviceProfile(
    id="dish_wally_ir",
    name="Dish Wally (IR)",
    brand="Dish Network",
    category="cable",
    model_years="2016+",
    description="Dish Wally portable receiver - IR control.",
    control_methods=[ControlMethod.IR],
    logo_url="https://upload.wikimedia.org/wikipedia/commons/d/da/Dish_Network_Logo.svg",
    ir_codes={
        # Uses same codes as Hopper with some variations
        "power": nec(0x00, 0x00, "power"),
        "vol_up": nec(0x00, 0x10, "vol_up"),
        "vol_down": nec(0x00, 0x11, "vol_down"),
        "mute": nec(0x00, 0x0D, "mute"),
        "ch_up": nec(0x00, 0x20, "ch_up"),
        "ch_down": nec(0x00, 0x21, "ch_down"),
        "guide": nec(0x00, 0x4F, "guide"),
        "menu": nec(0x00, 0x0B, "menu"),
        "info": nec(0x00, 0x17, "info"),
        "up": nec(0x00, 0x58, "up"),
        "down": nec(0x00, 0x59, "down"),
        "left": nec(0x00, 0x5A, "left"),
        "right": nec(0x00, 0x5B, "right"),
        "select": nec(0x00, 0x5C, "select"),
        "back": nec(0x00, 0x1E, "back"),
        "record": nec(0x00, 0x38, "record"),
        "play": nec(0x00, 0x32, "play"),
        "pause": nec(0x00, 0x33, "pause"),
        "stop": nec(0x00, 0x31, "stop"),
        "rewind": nec(0x00, 0x35, "rewind"),
        "fast_forward": nec(0x00, 0x34, "fast_forward"),
        "0": nec(0x00, 0x00, "0"),
        "1": nec(0x00, 0x01, "1"),
        "2": nec(0x00, 0x02, "2"),
        "3": nec(0x00, 0x03, "3"),
        "4": nec(0x00, 0x04, "4"),
        "5": nec(0x00, 0x05, "5"),
        "6": nec(0x00, 0x06, "6"),
        "7": nec(0x00, 0x07, "7"),
        "8": nec(0x00, 0x08, "8"),
        "9": nec(0x00, 0x09, "9"),
    },
)
register_profile(DISH_WALLY_IR)
