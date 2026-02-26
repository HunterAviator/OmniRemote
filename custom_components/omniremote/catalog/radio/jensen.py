"""Jensen Radio/Stereo profiles.

Jensen makes car stereos, portable radios, and home audio systems.
Many use NEC protocol but some older models use different protocols.
"""

# NOTE: DeviceProfile, IRCode, ControlMethod, nec, nec_ext, BRAND_LOGOS, etc.
# are injected into this module's namespace by the catalog loader.
# Do not add import statements for these.

# =============================================================================
# Jensen Car Stereo - Common Models
# =============================================================================
# Many Jensen car stereos use NEC protocol with address 0x00 or 0x01
# Command codes vary by model

JENSEN_CAR_STEREO_COMMON = DeviceProfile(
    id="jensen_car_stereo",
    name="Jensen Car Stereo (Common)",
    brand="Jensen",
    category="radio",
    model_years="2015-2024",
    description="Common Jensen car stereo IR codes. Works with many JRV, CMR, and MPR series.",
    control_methods=[ControlMethod.IR],
    logo_url=BRAND_LOGOS.get("jensen", ""),
    ir_codes={
        # Power
        "power": nec(0x00, 0x12, "power"),
        "power_on": nec(0x00, 0x12, "power_on"),
        "power_off": nec(0x00, 0x12, "power_off"),
        
        # Volume
        "vol_up": nec(0x00, 0x1A, "vol_up"),
        "vol_down": nec(0x00, 0x1E, "vol_down"),
        "mute": nec(0x00, 0x0E, "mute"),
        
        # Tuner
        "tune_up": nec(0x00, 0x0A, "tune_up"),
        "tune_down": nec(0x00, 0x1B, "tune_down"),
        "seek_up": nec(0x00, 0x0A, "seek_up"),
        "seek_down": nec(0x00, 0x1B, "seek_down"),
        "band": nec(0x00, 0x0F, "band"),
        "am_fm": nec(0x00, 0x0F, "am_fm"),
        
        # Presets
        "preset_1": nec(0x00, 0x01, "preset_1"),
        "preset_2": nec(0x00, 0x02, "preset_2"),
        "preset_3": nec(0x00, 0x03, "preset_3"),
        "preset_4": nec(0x00, 0x04, "preset_4"),
        "preset_5": nec(0x00, 0x05, "preset_5"),
        "preset_6": nec(0x00, 0x06, "preset_6"),
        
        # Source
        "source": nec(0x00, 0x13, "source"),
        "mode": nec(0x00, 0x13, "mode"),
        "aux": nec(0x00, 0x19, "aux"),
        "bluetooth": nec(0x00, 0x58, "bluetooth"),
        "usb": nec(0x00, 0x14, "usb"),
        
        # Playback
        "play": nec(0x00, 0x16, "play"),
        "pause": nec(0x00, 0x16, "pause"),
        "play_pause": nec(0x00, 0x16, "play_pause"),
        "stop": nec(0x00, 0x17, "stop"),
        "next": nec(0x00, 0x0A, "next"),
        "prev": nec(0x00, 0x1B, "prev"),
        "fast_forward": nec(0x00, 0x0A, "fast_forward"),
        "rewind": nec(0x00, 0x1B, "rewind"),
        
        # Audio
        "bass_up": nec(0x00, 0x45, "bass_up"),
        "bass_down": nec(0x00, 0x46, "bass_down"),
        "treble_up": nec(0x00, 0x47, "treble_up"),
        "treble_down": nec(0x00, 0x48, "treble_down"),
        "balance_left": nec(0x00, 0x49, "balance_left"),
        "balance_right": nec(0x00, 0x4A, "balance_right"),
        "fader_front": nec(0x00, 0x4B, "fader_front"),
        "fader_rear": nec(0x00, 0x4C, "fader_rear"),
        "loudness": nec(0x00, 0x0D, "loudness"),
        
        # Display
        "display": nec(0x00, 0x1F, "display"),
        "dimmer": nec(0x00, 0x4D, "dimmer"),
        
        # Menu
        "menu": nec(0x00, 0x50, "menu"),
        "enter": nec(0x00, 0x51, "enter"),
        "back": nec(0x00, 0x52, "back"),
        "up": nec(0x00, 0x53, "up"),
        "down": nec(0x00, 0x54, "down"),
        "left": nec(0x00, 0x55, "left"),
        "right": nec(0x00, 0x56, "right"),
    },
)

# =============================================================================
# Jensen Car Stereo - Alternate Address (0x01)
# =============================================================================
JENSEN_CAR_STEREO_ALT = DeviceProfile(
    id="jensen_car_stereo_alt",
    name="Jensen Car Stereo (Alt Address)",
    brand="Jensen",
    category="radio",
    model_years="2010-2020",
    description="Alternative Jensen car stereo codes using address 0x01. Try if common codes don't work.",
    control_methods=[ControlMethod.IR],
    logo_url=BRAND_LOGOS.get("jensen", ""),
    ir_codes={
        # Power
        "power": nec(0x01, 0x12, "power"),
        
        # Volume
        "vol_up": nec(0x01, 0x1A, "vol_up"),
        "vol_down": nec(0x01, 0x1E, "vol_down"),
        "mute": nec(0x01, 0x0E, "mute"),
        
        # Tuner
        "tune_up": nec(0x01, 0x0A, "tune_up"),
        "tune_down": nec(0x01, 0x1B, "tune_down"),
        "band": nec(0x01, 0x0F, "band"),
        
        # Presets
        "preset_1": nec(0x01, 0x01, "preset_1"),
        "preset_2": nec(0x01, 0x02, "preset_2"),
        "preset_3": nec(0x01, 0x03, "preset_3"),
        "preset_4": nec(0x01, 0x04, "preset_4"),
        "preset_5": nec(0x01, 0x05, "preset_5"),
        "preset_6": nec(0x01, 0x06, "preset_6"),
        
        # Source
        "source": nec(0x01, 0x13, "source"),
        "aux": nec(0x01, 0x19, "aux"),
        
        # Playback
        "play_pause": nec(0x01, 0x16, "play_pause"),
        "stop": nec(0x01, 0x17, "stop"),
        "next": nec(0x01, 0x0A, "next"),
        "prev": nec(0x01, 0x1B, "prev"),
    },
)

# =============================================================================
# Jensen Marine/RV Stereo
# =============================================================================
JENSEN_MARINE_STEREO = DeviceProfile(
    id="jensen_marine_stereo",
    name="Jensen Marine/RV Stereo",
    brand="Jensen",
    category="radio",
    model_years="2015-2024",
    description="Jensen marine/RV stereo systems (JMS, JHD series). Weather-resistant models for boats and RVs.",
    control_methods=[ControlMethod.IR],
    logo_url=BRAND_LOGOS.get("jensen", ""),
    ir_codes={
        # Power
        "power": nec(0x04, 0x12, "power"),
        
        # Volume
        "vol_up": nec(0x04, 0x1A, "vol_up"),
        "vol_down": nec(0x04, 0x1E, "vol_down"),
        "mute": nec(0x04, 0x0E, "mute"),
        
        # Tuner
        "tune_up": nec(0x04, 0x0A, "tune_up"),
        "tune_down": nec(0x04, 0x1B, "tune_down"),
        "band": nec(0x04, 0x0F, "band"),
        
        # Source
        "source": nec(0x04, 0x13, "source"),
        "aux": nec(0x04, 0x19, "aux"),
        "bluetooth": nec(0x04, 0x58, "bluetooth"),
        "usb": nec(0x04, 0x14, "usb"),
        
        # Playback
        "play_pause": nec(0x04, 0x16, "play_pause"),
        "next": nec(0x04, 0x0A, "next"),
        "prev": nec(0x04, 0x1B, "prev"),
        
        # Presets
        "preset_1": nec(0x04, 0x01, "preset_1"),
        "preset_2": nec(0x04, 0x02, "preset_2"),
        "preset_3": nec(0x04, 0x03, "preset_3"),
        "preset_4": nec(0x04, 0x04, "preset_4"),
        "preset_5": nec(0x04, 0x05, "preset_5"),
        "preset_6": nec(0x04, 0x06, "preset_6"),
    },
)

# =============================================================================
# Jensen Portable CD/Radio Boombox
# =============================================================================
JENSEN_PORTABLE = DeviceProfile(
    id="jensen_portable",
    name="Jensen Portable CD/Radio",
    brand="Jensen",
    category="radio",
    model_years="2010-2024",
    description="Jensen portable CD players, boomboxes, and tabletop radios.",
    control_methods=[ControlMethod.IR],
    logo_url=BRAND_LOGOS.get("jensen", ""),
    ir_codes={
        # Power
        "power": nec(0x00, 0x45, "power"),
        
        # Volume
        "vol_up": nec(0x00, 0x46, "vol_up"),
        "vol_down": nec(0x00, 0x47, "vol_down"),
        "mute": nec(0x00, 0x16, "mute"),
        
        # Tuner
        "tune_up": nec(0x00, 0x40, "tune_up"),
        "tune_down": nec(0x00, 0x41, "tune_down"),
        "band": nec(0x00, 0x44, "band"),
        
        # CD/Playback
        "play": nec(0x00, 0x43, "play"),
        "pause": nec(0x00, 0x43, "pause"),
        "stop": nec(0x00, 0x42, "stop"),
        "next": nec(0x00, 0x40, "next"),
        "prev": nec(0x00, 0x41, "prev"),
        "program": nec(0x00, 0x4A, "program"),
        "repeat": nec(0x00, 0x4B, "repeat"),
        "random": nec(0x00, 0x4C, "random"),
        
        # Source
        "source": nec(0x00, 0x44, "source"),
        "cd": nec(0x00, 0x48, "cd"),
        "aux": nec(0x00, 0x49, "aux"),
    },
)

# Register all profiles
register_profile(JENSEN_CAR_STEREO_COMMON)
register_profile(JENSEN_CAR_STEREO_ALT)
register_profile(JENSEN_MARINE_STEREO)
register_profile(JENSEN_PORTABLE)
