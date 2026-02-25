"""LG TV profiles."""

# =============================================================================
# LG TV - Standard NEC IR
# =============================================================================
LG_TV_IR_STANDARD = DeviceProfile(
    id="lg_tv_ir_standard",
    name="LG TV (Standard IR)",
    brand="LG",
    category="tv",
    model_years="2010-2020",
    description="Standard LG TV IR codes using NEC protocol.",
    control_methods=[ControlMethod.IR],
    logo_url=BRAND_LOGOS.get("lg", ""),
    ir_codes={
        # Power
        "power": nec(0x04, 0x08, "power"),
        "power_on": nec(0x04, 0xC4, "power_on"),
        "power_off": nec(0x04, 0xC5, "power_off"),
        
        # Volume
        "vol_up": nec(0x04, 0x02, "vol_up"),
        "vol_down": nec(0x04, 0x03, "vol_down"),
        "mute": nec(0x04, 0x09, "mute"),
        
        # Channels
        "ch_up": nec(0x04, 0x00, "ch_up"),
        "ch_down": nec(0x04, 0x01, "ch_down"),
        "prev_ch": nec(0x04, 0x1A, "prev_ch"),
        
        # Input
        "input": nec(0x04, 0x0B, "input"),
        "tv": nec(0x04, 0xD0, "tv"),
        "hdmi1": nec(0x04, 0xCE, "hdmi1"),
        "hdmi2": nec(0x04, 0xCC, "hdmi2"),
        "hdmi3": nec(0x04, 0xE9, "hdmi3"),
        "hdmi4": nec(0x04, 0xDA, "hdmi4"),
        "av1": nec(0x04, 0x5A, "av1"),
        "component": nec(0x04, 0xBF, "component"),
        
        # Navigation
        "menu": nec(0x04, 0x43, "menu"),
        "home": nec(0x04, 0x7C, "home"),
        "settings": nec(0x04, 0xC4, "settings"),
        "guide": nec(0x04, 0xAB, "guide"),
        "info": nec(0x04, 0xAA, "info"),
        "back": nec(0x04, 0x28, "back"),
        "exit": nec(0x04, 0x5B, "exit"),
        
        # D-Pad
        "up": nec(0x04, 0x40, "up"),
        "down": nec(0x04, 0x41, "down"),
        "left": nec(0x04, 0x07, "left"),
        "right": nec(0x04, 0x06, "right"),
        "enter": nec(0x04, 0x44, "enter"),
        "ok": nec(0x04, 0x44, "ok"),
        
        # Color buttons
        "red": nec(0x04, 0x72, "red"),
        "green": nec(0x04, 0x71, "green"),
        "yellow": nec(0x04, 0x63, "yellow"),
        "blue": nec(0x04, 0x61, "blue"),
        
        # Media
        "play": nec(0x04, 0xB0, "play"),
        "pause": nec(0x04, 0xBA, "pause"),
        "stop": nec(0x04, 0xB1, "stop"),
        "rewind": nec(0x04, 0x8F, "rewind"),
        "fast_forward": nec(0x04, 0x8E, "fast_forward"),
        "record": nec(0x04, 0xBD, "record"),
        
        # Numbers
        "0": nec(0x04, 0x10, "0"),
        "1": nec(0x04, 0x11, "1"),
        "2": nec(0x04, 0x12, "2"),
        "3": nec(0x04, 0x13, "3"),
        "4": nec(0x04, 0x14, "4"),
        "5": nec(0x04, 0x15, "5"),
        "6": nec(0x04, 0x16, "6"),
        "7": nec(0x04, 0x17, "7"),
        "8": nec(0x04, 0x18, "8"),
        "9": nec(0x04, 0x19, "9"),
        
        # Picture
        "aspect": nec(0x04, 0x79, "aspect"),
        "picture_mode": nec(0x04, 0x4D, "picture_mode"),
        "energy_saving": nec(0x04, 0x95, "energy_saving"),
        
        # Sound
        "sound_mode": nec(0x04, 0x52, "sound_mode"),
        
        # Misc
        "sleep": nec(0x04, 0x0E, "sleep"),
        "caption": nec(0x04, 0x39, "caption"),
        "favorite": nec(0x04, 0x1E, "favorite"),
    },
)
register_profile(LG_TV_IR_STANDARD)


# =============================================================================
# LG TV - WebOS Network
# =============================================================================
LG_TV_WEBOS = DeviceProfile(
    id="lg_tv_webos",
    name="LG TV (WebOS Network)",
    brand="LG",
    category="tv",
    model_years="2014+",
    description="LG WebOS Smart TVs with network control via WebSocket.",
    control_methods=[ControlMethod.NETWORK],
    logo_url=BRAND_LOGOS.get("lg", ""),
    network_port=3000,
    network_protocol="wss",
    network_commands={
        "power_off": NetworkCommand("power_off", "POST", "/system.turnOff", {}),
        "vol_up": NetworkCommand("vol_up", "POST", "/audio/volumeUp", {}),
        "vol_down": NetworkCommand("vol_down", "POST", "/audio/volumeDown", {}),
        "mute": NetworkCommand("mute", "POST", "/audio/setMute", {"mute": True}),
        "unmute": NetworkCommand("unmute", "POST", "/audio/setMute", {"mute": False}),
        "set_volume": NetworkCommand("set_volume", "POST", "/audio/setVolume", {"volume": 20}),
        "ch_up": NetworkCommand("ch_up", "POST", "/tv/channelUp", {}),
        "ch_down": NetworkCommand("ch_down", "POST", "/tv/channelDown", {}),
        "home": NetworkCommand("home", "POST", "/ssap/system.launcher/open", {"id": "com.webos.app.livetv"}),
        "up": NetworkCommand("up", "POST", "/com.webos.service.ime/sendButton", {"button": "UP"}),
        "down": NetworkCommand("down", "POST", "/com.webos.service.ime/sendButton", {"button": "DOWN"}),
        "left": NetworkCommand("left", "POST", "/com.webos.service.ime/sendButton", {"button": "LEFT"}),
        "right": NetworkCommand("right", "POST", "/com.webos.service.ime/sendButton", {"button": "RIGHT"}),
        "enter": NetworkCommand("enter", "POST", "/com.webos.service.ime/sendButton", {"button": "ENTER"}),
        "back": NetworkCommand("back", "POST", "/com.webos.service.ime/sendButton", {"button": "BACK"}),
        "play": NetworkCommand("play", "POST", "/media.controls/play", {}),
        "pause": NetworkCommand("pause", "POST", "/media.controls/pause", {}),
        "stop": NetworkCommand("stop", "POST", "/media.controls/stop", {}),
    },
)
register_profile(LG_TV_WEBOS)
