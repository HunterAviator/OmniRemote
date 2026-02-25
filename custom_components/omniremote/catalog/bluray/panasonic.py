"""Panasonic Blu-ray player profiles."""

# =============================================================================
# Panasonic Blu-ray Player - IR (Kaseikyo Protocol)
# =============================================================================
PANASONIC_BLURAY_IR = DeviceProfile(
    id="panasonic_bluray_ir",
    name="Panasonic Blu-ray (IR)",
    brand="Panasonic",
    category="bluray",
    model_years="2010+",
    description="Panasonic Blu-ray players - Uses Kaseikyo (Panasonic) protocol.",
    control_methods=[ControlMethod.IR],
    logo_url=BRAND_LOGOS.get("panasonic", ""),
    ir_codes={
        # Power
        "power": panasonic(0x4004, 0x0038BC, "power"),
        "power_on": panasonic(0x4004, 0x0038BD, "power_on"),
        "power_off": panasonic(0x4004, 0x0038BE, "power_off"),
        
        # Disc
        "eject": panasonic(0x4004, 0x0038D2, "eject"),
        
        # Playback
        "play": panasonic(0x4004, 0x0038B2, "play"),
        "pause": panasonic(0x4004, 0x0038B3, "pause"),
        "stop": panasonic(0x4004, 0x0038B0, "stop"),
        "rewind": panasonic(0x4004, 0x0038B5, "rewind"),
        "fast_forward": panasonic(0x4004, 0x0038B4, "fast_forward"),
        "slow_rewind": panasonic(0x4004, 0x0038B7, "slow_rewind"),
        "slow_forward": panasonic(0x4004, 0x0038B6, "slow_forward"),
        "prev_chapter": panasonic(0x4004, 0x0038B9, "prev_chapter"),
        "next_chapter": panasonic(0x4004, 0x0038B8, "next_chapter"),
        "step_back": panasonic(0x4004, 0x0038BB, "step_back"),
        "step_forward": panasonic(0x4004, 0x0038BA, "step_forward"),
        
        # Navigation
        "home": panasonic(0x4004, 0x0038C0, "home"),
        "menu": panasonic(0x4004, 0x0038C1, "menu"),
        "top_menu": panasonic(0x4004, 0x0038C2, "top_menu"),
        "popup_menu": panasonic(0x4004, 0x0038C3, "popup_menu"),
        "up": panasonic(0x4004, 0x003852, "up"),
        "down": panasonic(0x4004, 0x003853, "down"),
        "left": panasonic(0x4004, 0x003854, "left"),
        "right": panasonic(0x4004, 0x003855, "right"),
        "ok": panasonic(0x4004, 0x003849, "ok"),
        "return": panasonic(0x4004, 0x003828, "return"),
        "exit": panasonic(0x4004, 0x00382D, "exit"),
        
        # Info/Display
        "info": panasonic(0x4004, 0x003835, "info"),
        "display": panasonic(0x4004, 0x003844, "display"),
        
        # Audio/Video
        "audio": panasonic(0x4004, 0x0038E0, "audio"),
        "subtitle": panasonic(0x4004, 0x0038E1, "subtitle"),
        "angle": panasonic(0x4004, 0x0038E2, "angle"),
        "repeat": panasonic(0x4004, 0x0038E3, "repeat"),
        "ab_repeat": panasonic(0x4004, 0x0038E4, "ab_repeat"),
        "zoom": panasonic(0x4004, 0x0038E5, "zoom"),
        "pip": panasonic(0x4004, 0x0038E6, "pip"),
        
        # Color Buttons
        "red": panasonic(0x4004, 0x0038F0, "red"),
        "green": panasonic(0x4004, 0x0038F1, "green"),
        "yellow": panasonic(0x4004, 0x0038F2, "yellow"),
        "blue": panasonic(0x4004, 0x0038F3, "blue"),
        
        # Numbers
        "0": panasonic(0x4004, 0x003800, "0"),
        "1": panasonic(0x4004, 0x003801, "1"),
        "2": panasonic(0x4004, 0x003802, "2"),
        "3": panasonic(0x4004, 0x003803, "3"),
        "4": panasonic(0x4004, 0x003804, "4"),
        "5": panasonic(0x4004, 0x003805, "5"),
        "6": panasonic(0x4004, 0x003806, "6"),
        "7": panasonic(0x4004, 0x003807, "7"),
        "8": panasonic(0x4004, 0x003808, "8"),
        "9": panasonic(0x4004, 0x003809, "9"),
    },
)
register_profile(PANASONIC_BLURAY_IR)


# =============================================================================
# Panasonic 4K UHD Blu-ray Player
# =============================================================================
PANASONIC_4K_BLURAY_IR = DeviceProfile(
    id="panasonic_4k_bluray_ir",
    name="Panasonic 4K UHD Blu-ray (IR)",
    brand="Panasonic",
    category="bluray",
    model_years="2016+",
    description="Panasonic 4K Ultra HD Blu-ray players (DP-UB820, UB9000, etc.).",
    control_methods=[ControlMethod.IR],
    logo_url=BRAND_LOGOS.get("panasonic", ""),
    ir_codes={
        # Power
        "power": panasonic(0x4004, 0x0038BC, "power"),
        
        # Disc
        "eject": panasonic(0x4004, 0x0038D2, "eject"),
        
        # Playback
        "play": panasonic(0x4004, 0x0038B2, "play"),
        "pause": panasonic(0x4004, 0x0038B3, "pause"),
        "stop": panasonic(0x4004, 0x0038B0, "stop"),
        "rewind": panasonic(0x4004, 0x0038B5, "rewind"),
        "fast_forward": panasonic(0x4004, 0x0038B4, "fast_forward"),
        "prev_chapter": panasonic(0x4004, 0x0038B9, "prev_chapter"),
        "next_chapter": panasonic(0x4004, 0x0038B8, "next_chapter"),
        
        # Navigation
        "home": panasonic(0x4004, 0x0038C0, "home"),
        "menu": panasonic(0x4004, 0x0038C1, "menu"),
        "top_menu": panasonic(0x4004, 0x0038C2, "top_menu"),
        "popup_menu": panasonic(0x4004, 0x0038C3, "popup_menu"),
        "up": panasonic(0x4004, 0x003852, "up"),
        "down": panasonic(0x4004, 0x003853, "down"),
        "left": panasonic(0x4004, 0x003854, "left"),
        "right": panasonic(0x4004, 0x003855, "right"),
        "ok": panasonic(0x4004, 0x003849, "ok"),
        "return": panasonic(0x4004, 0x003828, "return"),
        
        # Info
        "info": panasonic(0x4004, 0x003835, "info"),
        
        # Audio/Video
        "audio": panasonic(0x4004, 0x0038E0, "audio"),
        "subtitle": panasonic(0x4004, 0x0038E1, "subtitle"),
        
        # HDR Settings
        "hdr_setting": panasonic(0x4004, 0x0038F8, "hdr_setting"),
        "hdr_optimizer": panasonic(0x4004, 0x0038F9, "hdr_optimizer"),
    },
)
register_profile(PANASONIC_4K_BLURAY_IR)
