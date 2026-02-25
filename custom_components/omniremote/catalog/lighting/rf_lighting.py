"""RF Lighting control profiles."""

# =============================================================================
# Bond Bridge - RF Fan/Light Control
# =============================================================================
BOND_BRIDGE = DeviceProfile(
    id="bond_bridge",
    name="Bond Bridge (RF Fans/Lights)",
    brand="Bond",
    category="lighting",
    model_years="2019+",
    description="Bond Bridge for controlling RF ceiling fans and lights. Uses Bond Local API.",
    control_methods=[ControlMethod.NETWORK, ControlMethod.RF],
    logo_url="",
    network_port=80,
    network_protocol="http",
    network_commands={
        # Bond Local API - device_id would be filled in
        "light_on": NetworkCommand("light_on", "PUT", "/v2/devices/{device_id}/actions/TurnLightOn", {}),
        "light_off": NetworkCommand("light_off", "PUT", "/v2/devices/{device_id}/actions/TurnLightOff", {}),
        "light_toggle": NetworkCommand("light_toggle", "PUT", "/v2/devices/{device_id}/actions/ToggleLight", {}),
        "fan_off": NetworkCommand("fan_off", "PUT", "/v2/devices/{device_id}/actions/TurnOff", {}),
        "fan_low": NetworkCommand("fan_low", "PUT", "/v2/devices/{device_id}/actions/SetSpeed", {"argument": 1}),
        "fan_med": NetworkCommand("fan_med", "PUT", "/v2/devices/{device_id}/actions/SetSpeed", {"argument": 2}),
        "fan_high": NetworkCommand("fan_high", "PUT", "/v2/devices/{device_id}/actions/SetSpeed", {"argument": 3}),
        "fan_speed_up": NetworkCommand("fan_speed_up", "PUT", "/v2/devices/{device_id}/actions/IncreaseSpeed", {}),
        "fan_speed_down": NetworkCommand("fan_speed_down", "PUT", "/v2/devices/{device_id}/actions/DecreaseSpeed", {}),
        "fan_reverse": NetworkCommand("fan_reverse", "PUT", "/v2/devices/{device_id}/actions/ToggleDirection", {}),
    },
)
register_profile(BOND_BRIDGE)


# =============================================================================
# Hampton Bay RF Fan/Light Remote (Common 315MHz)
# =============================================================================
HAMPTON_BAY_RF_LIGHT = DeviceProfile(
    id="hampton_bay_rf_light",
    name="Hampton Bay RF (315MHz)",
    brand="Hampton Bay",
    category="lighting",
    model_years="2010+",
    description="Hampton Bay ceiling fan with RF remote control (315MHz). DIP switch configured.",
    control_methods=[ControlMethod.RF],
    logo_url=BRAND_LOGOS.get("hampton_bay", ""),
    rf_codes={
        # These are common Hampton Bay codes - actual codes depend on DIP switch settings
        "light": RFCode(
            name="light",
            frequency=315000000,
            protocol="FAN-REMOTE",
            code="LEARN_FROM_REMOTE",
        ),
        "fan_off": RFCode(
            name="fan_off",
            frequency=315000000,
            protocol="FAN-REMOTE",
            code="LEARN_FROM_REMOTE",
        ),
        "fan_low": RFCode(
            name="fan_low",
            frequency=315000000,
            protocol="FAN-REMOTE",
            code="LEARN_FROM_REMOTE",
        ),
        "fan_med": RFCode(
            name="fan_med",
            frequency=315000000,
            protocol="FAN-REMOTE",
            code="LEARN_FROM_REMOTE",
        ),
        "fan_high": RFCode(
            name="fan_high",
            frequency=315000000,
            protocol="FAN-REMOTE",
            code="LEARN_FROM_REMOTE",
        ),
    },
)
register_profile(HAMPTON_BAY_RF_LIGHT)


# =============================================================================
# Hunter RF Fan/Light Remote (303MHz)
# =============================================================================
HUNTER_RF_LIGHT = DeviceProfile(
    id="hunter_rf_light",
    name="Hunter RF Fan/Light (303MHz)",
    brand="Hunter",
    category="lighting",
    model_years="2010+",
    description="Hunter ceiling fan with RF remote control (303MHz).",
    control_methods=[ControlMethod.RF],
    logo_url=BRAND_LOGOS.get("hunter", ""),
    rf_codes={
        "light": RFCode(
            name="light",
            frequency=303875000,
            protocol="FAN-REMOTE",
            code="LEARN_FROM_REMOTE",
        ),
        "fan_off": RFCode(
            name="fan_off",
            frequency=303875000,
            protocol="FAN-REMOTE",
            code="LEARN_FROM_REMOTE",
        ),
        "fan_low": RFCode(
            name="fan_low",
            frequency=303875000,
            protocol="FAN-REMOTE",
            code="LEARN_FROM_REMOTE",
        ),
        "fan_med": RFCode(
            name="fan_med",
            frequency=303875000,
            protocol="FAN-REMOTE",
            code="LEARN_FROM_REMOTE",
        ),
        "fan_high": RFCode(
            name="fan_high",
            frequency=303875000,
            protocol="FAN-REMOTE",
            code="LEARN_FROM_REMOTE",
        ),
    },
)
register_profile(HUNTER_RF_LIGHT)


# =============================================================================
# Lutron Caseta (Network) - Via Lutron Bridge
# =============================================================================
LUTRON_CASETA = DeviceProfile(
    id="lutron_caseta",
    name="Lutron Caseta (Bridge)",
    brand="Lutron",
    category="lighting",
    model_years="2014+",
    description="Lutron Caseta wireless lighting - Controlled via Lutron Smart Bridge.",
    control_methods=[ControlMethod.NETWORK],
    logo_url="https://upload.wikimedia.org/wikipedia/commons/6/6c/Lutron_logo.svg",
    network_port=8083,
    network_protocol="leap",
    network_commands={
        # LEAP protocol commands (via Lutron integration)
        "on": NetworkCommand("on", "LEAP", "zone/on", {}),
        "off": NetworkCommand("off", "LEAP", "zone/off", {}),
        "set_level": NetworkCommand("set_level", "LEAP", "zone/level", {"level": 100}),
        "dim_25": NetworkCommand("dim_25", "LEAP", "zone/level", {"level": 25}),
        "dim_50": NetworkCommand("dim_50", "LEAP", "zone/level", {"level": 50}),
        "dim_75": NetworkCommand("dim_75", "LEAP", "zone/level", {"level": 75}),
        "raise": NetworkCommand("raise", "LEAP", "zone/raise", {}),
        "lower": NetworkCommand("lower", "LEAP", "zone/lower", {}),
    },
)
register_profile(LUTRON_CASETA)


# =============================================================================
# WLED (Network) - LED Strip Controller
# =============================================================================
WLED = DeviceProfile(
    id="wled",
    name="WLED LED Controller",
    brand="WLED",
    category="lighting",
    model_years="2019+",
    description="WLED-based LED strip/pixel controller - Network/HTTP/MQTT control.",
    control_methods=[ControlMethod.NETWORK],
    logo_url="",
    network_port=80,
    network_protocol="http",
    network_commands={
        "on": NetworkCommand("on", "GET", "/win&T=1", {}),
        "off": NetworkCommand("off", "GET", "/win&T=0", {}),
        "toggle": NetworkCommand("toggle", "GET", "/win&T=2", {}),
        "brightness_25": NetworkCommand("brightness_25", "GET", "/win&A=64", {}),
        "brightness_50": NetworkCommand("brightness_50", "GET", "/win&A=128", {}),
        "brightness_75": NetworkCommand("brightness_75", "GET", "/win&A=192", {}),
        "brightness_100": NetworkCommand("brightness_100", "GET", "/win&A=255", {}),
        "color_red": NetworkCommand("color_red", "GET", "/win&R=255&G=0&B=0", {}),
        "color_green": NetworkCommand("color_green", "GET", "/win&R=0&G=255&B=0", {}),
        "color_blue": NetworkCommand("color_blue", "GET", "/win&R=0&G=0&B=255", {}),
        "color_white": NetworkCommand("color_white", "GET", "/win&R=255&G=255&B=255", {}),
        "color_warm": NetworkCommand("color_warm", "GET", "/win&R=255&G=200&B=150", {}),
        "effect_rainbow": NetworkCommand("effect_rainbow", "GET", "/win&FX=9", {}),
        "effect_scan": NetworkCommand("effect_scan", "GET", "/win&FX=28", {}),
        "effect_fire": NetworkCommand("effect_fire", "GET", "/win&FX=66", {}),
        "effect_solid": NetworkCommand("effect_solid", "GET", "/win&FX=0", {}),
        "speed_slow": NetworkCommand("speed_slow", "GET", "/win&SX=50", {}),
        "speed_medium": NetworkCommand("speed_medium", "GET", "/win&SX=128", {}),
        "speed_fast": NetworkCommand("speed_fast", "GET", "/win&SX=200", {}),
    },
)
register_profile(WLED)
