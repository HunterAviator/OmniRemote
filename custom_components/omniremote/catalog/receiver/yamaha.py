"""Yamaha AVR profiles - IR and Network control."""

# =============================================================================
# Yamaha AVR - IR Control
# =============================================================================
YAMAHA_AVR_IR = DeviceProfile(
    id="yamaha_avr_ir",
    name="Yamaha AVR (IR)",
    brand="Yamaha",
    category="receiver",
    model_years="2010+",
    description="Yamaha AV Receivers - IR control.",
    control_methods=[ControlMethod.IR],
    logo_url=BRAND_LOGOS.get("yamaha", ""),
    ir_codes={
        # Power
        "power": nec(0x7A, 0x1D, "power"),
        "power_on": nec(0x7A, 0x1D, "power_on"),
        "power_off": nec(0x7A, 0x1E, "power_off"),
        
        # Volume
        "vol_up": nec(0x7A, 0x1A, "vol_up"),
        "vol_down": nec(0x7A, 0x1B, "vol_down"),
        "mute": nec(0x7A, 0x1C, "mute"),
        
        # Input Sources
        "input_hdmi1": nec(0x7A, 0xE1, "input_hdmi1"),
        "input_hdmi2": nec(0x7A, 0xE2, "input_hdmi2"),
        "input_hdmi3": nec(0x7A, 0xE3, "input_hdmi3"),
        "input_hdmi4": nec(0x7A, 0xE4, "input_hdmi4"),
        "input_hdmi5": nec(0x7A, 0xE5, "input_hdmi5"),
        "input_av1": nec(0x7A, 0xA1, "input_av1"),
        "input_av2": nec(0x7A, 0xA2, "input_av2"),
        "input_av3": nec(0x7A, 0xA3, "input_av3"),
        "input_audio1": nec(0x7A, 0xB1, "input_audio1"),
        "input_audio2": nec(0x7A, 0xB2, "input_audio2"),
        "input_tuner": nec(0x7A, 0x15, "input_tuner"),
        "input_phono": nec(0x7A, 0x14, "input_phono"),
        "input_cd": nec(0x7A, 0x16, "input_cd"),
        "input_usb": nec(0x7A, 0xC0, "input_usb"),
        "input_bluetooth": nec(0x7A, 0xC1, "input_bluetooth"),
        "input_network": nec(0x7A, 0xC2, "input_network"),
        "input_airplay": nec(0x7A, 0xC3, "input_airplay"),
        
        # Surround
        "surround_straight": nec(0x7A, 0x50, "surround_straight"),
        "surround_stereo": nec(0x7A, 0x51, "surround_stereo"),
        "surround_surround": nec(0x7A, 0x52, "surround_surround"),
        "surround_sci_fi": nec(0x7A, 0x53, "surround_sci_fi"),
        "surround_adventure": nec(0x7A, 0x54, "surround_adventure"),
        "surround_drama": nec(0x7A, 0x55, "surround_drama"),
        "surround_music_video": nec(0x7A, 0x56, "surround_music_video"),
        "surround_sports": nec(0x7A, 0x57, "surround_sports"),
        "pure_direct": nec(0x7A, 0x59, "pure_direct"),
        
        # Navigation
        "menu": nec(0x7A, 0x41, "menu"),
        "up": nec(0x7A, 0x40, "up"),
        "down": nec(0x7A, 0x41, "down"),
        "left": nec(0x7A, 0x42, "left"),
        "right": nec(0x7A, 0x43, "right"),
        "enter": nec(0x7A, 0x44, "enter"),
        "return": nec(0x7A, 0x45, "return"),
        "info": nec(0x7A, 0x46, "info"),
        "option": nec(0x7A, 0x47, "option"),
        
        # Scene
        "scene1": nec(0x7A, 0x61, "scene1"),
        "scene2": nec(0x7A, 0x62, "scene2"),
        "scene3": nec(0x7A, 0x63, "scene3"),
        "scene4": nec(0x7A, 0x64, "scene4"),
        
        # Zone 2
        "zone2_power": nec(0x7A, 0x80, "zone2_power"),
        "zone2_vol_up": nec(0x7A, 0x81, "zone2_vol_up"),
        "zone2_vol_down": nec(0x7A, 0x82, "zone2_vol_down"),
    },
)
register_profile(YAMAHA_AVR_IR)


# =============================================================================
# Yamaha AVR - MusicCast/YXC Network API
# =============================================================================
YAMAHA_AVR_NETWORK = DeviceProfile(
    id="yamaha_avr_network",
    name="Yamaha AVR (MusicCast Network)",
    brand="Yamaha",
    category="receiver",
    model_years="2015+",
    description="Yamaha MusicCast receivers with YXC network API.",
    control_methods=[ControlMethod.NETWORK],
    logo_url=BRAND_LOGOS.get("yamaha", ""),
    network_port=80,
    network_protocol="http",
    network_commands={
        # Power
        "power_on": NetworkCommand("power_on", "GET", "/YamahaExtendedControl/v1/main/setPower?power=on", {}),
        "power_off": NetworkCommand("power_off", "GET", "/YamahaExtendedControl/v1/main/setPower?power=standby", {}),
        "power_toggle": NetworkCommand("power_toggle", "GET", "/YamahaExtendedControl/v1/main/setPower?power=toggle", {}),
        "get_status": NetworkCommand("get_status", "GET", "/YamahaExtendedControl/v1/main/getStatus", {}),
        
        # Volume
        "vol_up": NetworkCommand("vol_up", "GET", "/YamahaExtendedControl/v1/main/setVolume?volume=up", {}),
        "vol_down": NetworkCommand("vol_down", "GET", "/YamahaExtendedControl/v1/main/setVolume?volume=down", {}),
        "vol_set_50": NetworkCommand("vol_set_50", "GET", "/YamahaExtendedControl/v1/main/setVolume?volume=50", {}),
        "mute_on": NetworkCommand("mute_on", "GET", "/YamahaExtendedControl/v1/main/setMute?enable=true", {}),
        "mute_off": NetworkCommand("mute_off", "GET", "/YamahaExtendedControl/v1/main/setMute?enable=false", {}),
        
        # Inputs
        "input_hdmi1": NetworkCommand("input_hdmi1", "GET", "/YamahaExtendedControl/v1/main/setInput?input=hdmi1", {}),
        "input_hdmi2": NetworkCommand("input_hdmi2", "GET", "/YamahaExtendedControl/v1/main/setInput?input=hdmi2", {}),
        "input_hdmi3": NetworkCommand("input_hdmi3", "GET", "/YamahaExtendedControl/v1/main/setInput?input=hdmi3", {}),
        "input_hdmi4": NetworkCommand("input_hdmi4", "GET", "/YamahaExtendedControl/v1/main/setInput?input=hdmi4", {}),
        "input_av1": NetworkCommand("input_av1", "GET", "/YamahaExtendedControl/v1/main/setInput?input=av1", {}),
        "input_av2": NetworkCommand("input_av2", "GET", "/YamahaExtendedControl/v1/main/setInput?input=av2", {}),
        "input_tuner": NetworkCommand("input_tuner", "GET", "/YamahaExtendedControl/v1/main/setInput?input=tuner", {}),
        "input_usb": NetworkCommand("input_usb", "GET", "/YamahaExtendedControl/v1/main/setInput?input=usb", {}),
        "input_bluetooth": NetworkCommand("input_bluetooth", "GET", "/YamahaExtendedControl/v1/main/setInput?input=bluetooth", {}),
        "input_airplay": NetworkCommand("input_airplay", "GET", "/YamahaExtendedControl/v1/main/setInput?input=airplay", {}),
        "input_spotify": NetworkCommand("input_spotify", "GET", "/YamahaExtendedControl/v1/main/setInput?input=spotify", {}),
        "input_server": NetworkCommand("input_server", "GET", "/YamahaExtendedControl/v1/main/setInput?input=server", {}),
        "input_net_radio": NetworkCommand("input_net_radio", "GET", "/YamahaExtendedControl/v1/main/setInput?input=net_radio", {}),
        
        # Sound Programs
        "sound_straight": NetworkCommand("sound_straight", "GET", "/YamahaExtendedControl/v1/main/setSoundProgram?program=straight", {}),
        "sound_stereo": NetworkCommand("sound_stereo", "GET", "/YamahaExtendedControl/v1/main/setSoundProgram?program=stereo", {}),
        "sound_surround": NetworkCommand("sound_surround", "GET", "/YamahaExtendedControl/v1/main/setSoundProgram?program=surr_decoder", {}),
        "sound_movie": NetworkCommand("sound_movie", "GET", "/YamahaExtendedControl/v1/main/setSoundProgram?program=movie", {}),
        "sound_music": NetworkCommand("sound_music", "GET", "/YamahaExtendedControl/v1/main/setSoundProgram?program=music", {}),
        
        # Zone 2
        "zone2_power_on": NetworkCommand("zone2_power_on", "GET", "/YamahaExtendedControl/v1/zone2/setPower?power=on", {}),
        "zone2_power_off": NetworkCommand("zone2_power_off", "GET", "/YamahaExtendedControl/v1/zone2/setPower?power=standby", {}),
        "zone2_vol_up": NetworkCommand("zone2_vol_up", "GET", "/YamahaExtendedControl/v1/zone2/setVolume?volume=up", {}),
        "zone2_vol_down": NetworkCommand("zone2_vol_down", "GET", "/YamahaExtendedControl/v1/zone2/setVolume?volume=down", {}),
        
        # Device Info
        "get_device_info": NetworkCommand("get_device_info", "GET", "/YamahaExtendedControl/v1/system/getDeviceInfo", {}),
        "get_features": NetworkCommand("get_features", "GET", "/YamahaExtendedControl/v1/system/getFeatures", {}),
    },
)
register_profile(YAMAHA_AVR_NETWORK)
