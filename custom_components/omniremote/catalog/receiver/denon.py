"""Denon AVR profiles - IR and Network control."""

# =============================================================================
# Denon AVR - IR Control
# =============================================================================
DENON_AVR_IR = DeviceProfile(
    id="denon_avr_ir",
    name="Denon AVR (IR)",
    brand="Denon",
    category="receiver",
    model_years="2010+",
    description="Denon AV Receivers - IR control. Works with most Denon models.",
    control_methods=[ControlMethod.IR],
    logo_url=BRAND_LOGOS.get("denon", ""),
    ir_codes={
        # Power
        "power": nec(0x02, 0x00, "power"),
        "power_on": nec(0x02, 0x80, "power_on"),
        "power_off": nec(0x02, 0x40, "power_off"),
        
        # Volume
        "vol_up": nec(0x02, 0x40, "vol_up"),
        "vol_down": nec(0x02, 0xC0, "vol_down"),
        "mute": nec(0x02, 0x01, "mute"),
        
        # Input Sources
        "input_cbl_sat": nec(0x02, 0x84, "input_cbl_sat"),
        "input_dvd": nec(0x02, 0x04, "input_dvd"),
        "input_bluray": nec(0x02, 0x05, "input_bluray"),
        "input_game": nec(0x02, 0x86, "input_game"),
        "input_media_player": nec(0x02, 0x87, "input_media_player"),
        "input_tv_audio": nec(0x02, 0x88, "input_tv_audio"),
        "input_aux1": nec(0x02, 0x89, "input_aux1"),
        "input_aux2": nec(0x02, 0x8A, "input_aux2"),
        "input_cd": nec(0x02, 0x8B, "input_cd"),
        "input_tuner": nec(0x02, 0x8C, "input_tuner"),
        "input_phono": nec(0x02, 0x8D, "input_phono"),
        "input_bluetooth": nec(0x02, 0xBE, "input_bluetooth"),
        "input_usb": nec(0x02, 0xBF, "input_usb"),
        "input_network": nec(0x02, 0xC1, "input_network"),
        
        # Surround Modes
        "surround_auto": nec(0x02, 0x4A, "surround_auto"),
        "surround_stereo": nec(0x02, 0x4B, "surround_stereo"),
        "surround_movie": nec(0x02, 0x4C, "surround_movie"),
        "surround_music": nec(0x02, 0x4D, "surround_music"),
        "surround_game": nec(0x02, 0x4E, "surround_game"),
        "surround_direct": nec(0x02, 0x4F, "surround_direct"),
        "surround_pure_direct": nec(0x02, 0x50, "surround_pure_direct"),
        "surround_dolby": nec(0x02, 0x51, "surround_dolby"),
        "surround_dts": nec(0x02, 0x52, "surround_dts"),
        "surround_neural": nec(0x02, 0x53, "surround_neural"),
        
        # Navigation
        "menu": nec(0x02, 0x11, "menu"),
        "up": nec(0x02, 0x13, "up"),
        "down": nec(0x02, 0x14, "down"),
        "left": nec(0x02, 0x15, "left"),
        "right": nec(0x02, 0x16, "right"),
        "enter": nec(0x02, 0x17, "enter"),
        "back": nec(0x02, 0x18, "back"),
        "info": nec(0x02, 0x19, "info"),
        "options": nec(0x02, 0x1A, "options"),
        "home": nec(0x02, 0x1B, "home"),
        
        # Audio Settings
        "bass_up": nec(0x02, 0x21, "bass_up"),
        "bass_down": nec(0x02, 0x22, "bass_down"),
        "treble_up": nec(0x02, 0x23, "treble_up"),
        "treble_down": nec(0x02, 0x24, "treble_down"),
        "dialog_up": nec(0x02, 0x25, "dialog_up"),
        "dialog_down": nec(0x02, 0x26, "dialog_down"),
        "subwoofer_up": nec(0x02, 0x27, "subwoofer_up"),
        "subwoofer_down": nec(0x02, 0x28, "subwoofer_down"),
        
        # Zone 2
        "zone2_power": nec(0x02, 0x60, "zone2_power"),
        "zone2_vol_up": nec(0x02, 0x61, "zone2_vol_up"),
        "zone2_vol_down": nec(0x02, 0x62, "zone2_vol_down"),
        "zone2_mute": nec(0x02, 0x63, "zone2_mute"),
        
        # Quick Select
        "quick1": nec(0x02, 0x70, "quick1"),
        "quick2": nec(0x02, 0x71, "quick2"),
        "quick3": nec(0x02, 0x72, "quick3"),
        "quick4": nec(0x02, 0x73, "quick4"),
    },
)
register_profile(DENON_AVR_IR)


# =============================================================================
# Denon AVR - Network/Telnet Control
# =============================================================================
DENON_AVR_NETWORK = DeviceProfile(
    id="denon_avr_network",
    name="Denon AVR (Network)",
    brand="Denon",
    category="receiver",
    model_years="2012+",
    description="Denon AV Receivers - Network control via Telnet/HTTP. More reliable than IR.",
    control_methods=[ControlMethod.NETWORK],
    logo_url=BRAND_LOGOS.get("denon", ""),
    network_port=23,
    network_protocol="telnet",
    network_commands={
        # Power
        "power_on": NetworkCommand("power_on", "RAW", "PWON\r", {}),
        "power_off": NetworkCommand("power_off", "RAW", "PWSTANDBY\r", {}),
        "power_status": NetworkCommand("power_status", "RAW", "PW?\r", {}),
        
        # Volume (00-98, or UP/DOWN)
        "vol_up": NetworkCommand("vol_up", "RAW", "MVUP\r", {}),
        "vol_down": NetworkCommand("vol_down", "RAW", "MVDOWN\r", {}),
        "vol_set_50": NetworkCommand("vol_set_50", "RAW", "MV50\r", {}),
        "vol_set_60": NetworkCommand("vol_set_60", "RAW", "MV60\r", {}),
        "vol_set_70": NetworkCommand("vol_set_70", "RAW", "MV70\r", {}),
        "vol_status": NetworkCommand("vol_status", "RAW", "MV?\r", {}),
        "mute_on": NetworkCommand("mute_on", "RAW", "MUON\r", {}),
        "mute_off": NetworkCommand("mute_off", "RAW", "MUOFF\r", {}),
        "mute_status": NetworkCommand("mute_status", "RAW", "MU?\r", {}),
        
        # Input Sources
        "input_cbl_sat": NetworkCommand("input_cbl_sat", "RAW", "SISAT/CBL\r", {}),
        "input_dvd": NetworkCommand("input_dvd", "RAW", "SIDVD\r", {}),
        "input_bluray": NetworkCommand("input_bluray", "RAW", "SIBD\r", {}),
        "input_game": NetworkCommand("input_game", "RAW", "SIGAME\r", {}),
        "input_media_player": NetworkCommand("input_media_player", "RAW", "SIMPLAY\r", {}),
        "input_tv_audio": NetworkCommand("input_tv_audio", "RAW", "SITV\r", {}),
        "input_aux1": NetworkCommand("input_aux1", "RAW", "SIAUX1\r", {}),
        "input_aux2": NetworkCommand("input_aux2", "RAW", "SIAUX2\r", {}),
        "input_cd": NetworkCommand("input_cd", "RAW", "SICD\r", {}),
        "input_tuner": NetworkCommand("input_tuner", "RAW", "SITUNER\r", {}),
        "input_phono": NetworkCommand("input_phono", "RAW", "SIPHONO\r", {}),
        "input_bluetooth": NetworkCommand("input_bluetooth", "RAW", "SIBT\r", {}),
        "input_usb": NetworkCommand("input_usb", "RAW", "SIUSB\r", {}),
        "input_network": NetworkCommand("input_network", "RAW", "SINET\r", {}),
        "input_status": NetworkCommand("input_status", "RAW", "SI?\r", {}),
        
        # Surround Modes
        "surround_auto": NetworkCommand("surround_auto", "RAW", "MSAUTO\r", {}),
        "surround_stereo": NetworkCommand("surround_stereo", "RAW", "MSSTEREO\r", {}),
        "surround_movie": NetworkCommand("surround_movie", "RAW", "MSMOVIE\r", {}),
        "surround_music": NetworkCommand("surround_music", "RAW", "MSMUSIC\r", {}),
        "surround_game": NetworkCommand("surround_game", "RAW", "MSGAME\r", {}),
        "surround_direct": NetworkCommand("surround_direct", "RAW", "MSDIRECT\r", {}),
        "surround_pure_direct": NetworkCommand("surround_pure_direct", "RAW", "MSPURE DIRECT\r", {}),
        "surround_dolby_surround": NetworkCommand("surround_dolby_surround", "RAW", "MSDOLBY SURROUND\r", {}),
        "surround_dts_surround": NetworkCommand("surround_dts_surround", "RAW", "MSDTS SURROUND\r", {}),
        "surround_neural_x": NetworkCommand("surround_neural_x", "RAW", "MSNEURAL:X\r", {}),
        "surround_status": NetworkCommand("surround_status", "RAW", "MS?\r", {}),
        
        # Zone 2
        "zone2_power_on": NetworkCommand("zone2_power_on", "RAW", "Z2ON\r", {}),
        "zone2_power_off": NetworkCommand("zone2_power_off", "RAW", "Z2OFF\r", {}),
        "zone2_vol_up": NetworkCommand("zone2_vol_up", "RAW", "Z2UP\r", {}),
        "zone2_vol_down": NetworkCommand("zone2_vol_down", "RAW", "Z2DOWN\r", {}),
        "zone2_input_cbl": NetworkCommand("zone2_input_cbl", "RAW", "Z2SAT/CBL\r", {}),
        
        # Zone 3
        "zone3_power_on": NetworkCommand("zone3_power_on", "RAW", "Z3ON\r", {}),
        "zone3_power_off": NetworkCommand("zone3_power_off", "RAW", "Z3OFF\r", {}),
        
        # Audio Settings
        "dialog_up": NetworkCommand("dialog_up", "RAW", "PSDEH UP\r", {}),
        "dialog_down": NetworkCommand("dialog_down", "RAW", "PSDEH DOWN\r", {}),
        "subwoofer_up": NetworkCommand("subwoofer_up", "RAW", "PSSWR UP\r", {}),
        "subwoofer_down": NetworkCommand("subwoofer_down", "RAW", "PSSWR DOWN\r", {}),
        
        # Eco Mode
        "eco_on": NetworkCommand("eco_on", "RAW", "ECOON\r", {}),
        "eco_auto": NetworkCommand("eco_auto", "RAW", "ECOAUTO\r", {}),
        "eco_off": NetworkCommand("eco_off", "RAW", "ECOOFF\r", {}),
    },
)
register_profile(DENON_AVR_NETWORK)


# =============================================================================
# Denon AVR - HTTP/REST API (newer models)
# =============================================================================
DENON_AVR_HTTP = DeviceProfile(
    id="denon_avr_http",
    name="Denon AVR (HTTP API)",
    brand="Denon",
    category="receiver",
    model_years="2016+",
    description="Denon AV Receivers - HTTP REST API for newer models.",
    control_methods=[ControlMethod.NETWORK],
    logo_url=BRAND_LOGOS.get("denon", ""),
    network_port=8080,
    network_protocol="http",
    network_commands={
        "power_on": NetworkCommand("power_on", "GET", "/goform/formiPhoneAppPower.xml?1+PowerOn", {}),
        "power_off": NetworkCommand("power_off", "GET", "/goform/formiPhoneAppPower.xml?1+PowerStandby", {}),
        "vol_up": NetworkCommand("vol_up", "GET", "/goform/formiPhoneAppVolume.xml?1+Up", {}),
        "vol_down": NetworkCommand("vol_down", "GET", "/goform/formiPhoneAppVolume.xml?1+Down", {}),
        "mute_on": NetworkCommand("mute_on", "GET", "/goform/formiPhoneAppMute.xml?1+MuteOn", {}),
        "mute_off": NetworkCommand("mute_off", "GET", "/goform/formiPhoneAppMute.xml?1+MuteOff", {}),
        "input_dvd": NetworkCommand("input_dvd", "GET", "/goform/formiPhoneAppDirect.xml?SIDVD", {}),
        "input_bluray": NetworkCommand("input_bluray", "GET", "/goform/formiPhoneAppDirect.xml?SIBD", {}),
        "input_cbl_sat": NetworkCommand("input_cbl_sat", "GET", "/goform/formiPhoneAppDirect.xml?SISAT/CBL", {}),
        "input_game": NetworkCommand("input_game", "GET", "/goform/formiPhoneAppDirect.xml?SIGAME", {}),
        "input_tv": NetworkCommand("input_tv", "GET", "/goform/formiPhoneAppDirect.xml?SITV", {}),
        "get_status": NetworkCommand("get_status", "GET", "/goform/formMainZone_MainZoneXml.xml", {}),
    },
)
register_profile(DENON_AVR_HTTP)
