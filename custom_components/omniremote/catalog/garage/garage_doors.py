"""Garage door opener profiles - RF/Rolling Code."""

# =============================================================================
# Chamberlain/LiftMaster - Security+ 2.0 (Rolling Code)
# Note: These use rolling codes and cannot be replayed. 
# Control via MyQ network integration instead.
# =============================================================================
CHAMBERLAIN_MYQ = DeviceProfile(
    id="chamberlain_myq",
    name="Chamberlain/LiftMaster (MyQ)",
    brand="Chamberlain",
    category="garage",
    model_years="2017+",
    description="Chamberlain/LiftMaster with MyQ - Network control via MyQ API. Rolling code RF cannot be replayed.",
    control_methods=[ControlMethod.NETWORK],
    logo_url="https://upload.wikimedia.org/wikipedia/commons/5/55/Chamberlain_Group_Logo.svg",
    network_commands={
        # MyQ API commands (would integrate with HA MyQ integration)
        "open": NetworkCommand("open", "MYQ", "open", {}),
        "close": NetworkCommand("close", "MYQ", "close", {}),
        "get_status": NetworkCommand("get_status", "MYQ", "status", {}),
        "light_on": NetworkCommand("light_on", "MYQ", "light_on", {}),
        "light_off": NetworkCommand("light_off", "MYQ", "light_off", {}),
    },
)
register_profile(CHAMBERLAIN_MYQ)


# =============================================================================
# Generic 315MHz Garage Door (Fixed Code)
# These older openers use fixed codes that CAN be replayed
# =============================================================================
GARAGE_315MHZ_GENERIC = DeviceProfile(
    id="garage_315mhz_generic",
    name="Garage Door 315MHz (Fixed Code)",
    brand="Generic",
    category="garage",
    model_years="Pre-2000",
    description="Older 315MHz garage door openers with fixed codes. Learn codes from existing remotes.",
    control_methods=[ControlMethod.RF],
    logo_url="",
    rf_codes={
        # These are placeholder codes - actual codes must be learned from your remote
        "button1": RFCode(
            name="button1",
            frequency=315000000,
            protocol="Princeton",
            code="LEARN_FROM_REMOTE",
        ),
        "button2": RFCode(
            name="button2",
            frequency=315000000,
            protocol="Princeton",
            code="LEARN_FROM_REMOTE",
        ),
    },
)
register_profile(GARAGE_315MHZ_GENERIC)


# =============================================================================
# Generic 433MHz Garage Door (Fixed Code)
# =============================================================================
GARAGE_433MHZ_GENERIC = DeviceProfile(
    id="garage_433mhz_generic",
    name="Garage Door 433MHz (Fixed Code)",
    brand="Generic",
    category="garage",
    model_years="Pre-2005",
    description="Older 433MHz garage door openers with fixed codes. Common in Europe.",
    control_methods=[ControlMethod.RF],
    logo_url="",
    rf_codes={
        "button1": RFCode(
            name="button1",
            frequency=433920000,
            protocol="Princeton",
            code="LEARN_FROM_REMOTE",
        ),
        "button2": RFCode(
            name="button2",
            frequency=433920000,
            protocol="Princeton",
            code="LEARN_FROM_REMOTE",
        ),
    },
)
register_profile(GARAGE_433MHZ_GENERIC)


# =============================================================================
# Genie Garage Door - Intellicode (Rolling Code)
# Note: Rolling codes cannot be replayed. Use wired wall button or network bridge.
# =============================================================================
GENIE_INTELLICODE = DeviceProfile(
    id="genie_intellicode",
    name="Genie Intellicode (Rolling)",
    brand="Genie",
    category="garage",
    model_years="1995+",
    description="Genie Intellicode uses rolling codes. Control via Aladdin Connect network or wired relay.",
    control_methods=[ControlMethod.NETWORK],
    logo_url="https://upload.wikimedia.org/wikipedia/commons/7/79/Genie_garage_doors_logo.svg",
    network_commands={
        # Aladdin Connect API
        "open": NetworkCommand("open", "ALADDIN", "open", {}),
        "close": NetworkCommand("close", "ALADDIN", "close", {}),
        "get_status": NetworkCommand("get_status", "ALADDIN", "status", {}),
    },
)
register_profile(GENIE_INTELLICODE)


# =============================================================================
# Shelly-Based Garage Control
# Using Shelly relay for dry contact control
# =============================================================================
GARAGE_SHELLY_RELAY = DeviceProfile(
    id="garage_shelly_relay",
    name="Garage Door (Shelly Relay)",
    brand="Shelly",
    category="garage",
    model_years="2018+",
    description="Control any garage door via Shelly 1/1PM relay wired to wall button terminals.",
    control_methods=[ControlMethod.NETWORK],
    logo_url="https://upload.wikimedia.org/wikipedia/commons/1/1b/Shelly_logo.svg",
    network_commands={
        # Shelly HTTP API
        "toggle": NetworkCommand("toggle", "GET", "/relay/0?turn=on&timer=1", {}),
        "pulse": NetworkCommand("pulse", "GET", "/relay/0?turn=on&timer=0.5", {}),
        "get_status": NetworkCommand("get_status", "GET", "/status", {}),
    },
)
register_profile(GARAGE_SHELLY_RELAY)


# =============================================================================
# Ratgdo - Local Control for Chamberlain/LiftMaster
# https://github.com/PaulWieland/ratgdo
# =============================================================================
GARAGE_RATGDO = DeviceProfile(
    id="garage_ratgdo",
    name="Garage Door (ratgdo)",
    brand="ratgdo",
    category="garage",
    model_years="2023+",
    description="Local ESP-based control for Security+ 2.0 garage doors (Chamberlain/LiftMaster). Bypasses MyQ cloud.",
    control_methods=[ControlMethod.NETWORK],
    logo_url="",
    network_commands={
        # MQTT or ESPHome API
        "open": NetworkCommand("open", "MQTT", "ratgdo/door/command", {"payload": "open"}),
        "close": NetworkCommand("close", "MQTT", "ratgdo/door/command", {"payload": "close"}),
        "stop": NetworkCommand("stop", "MQTT", "ratgdo/door/command", {"payload": "stop"}),
        "toggle": NetworkCommand("toggle", "MQTT", "ratgdo/door/command", {"payload": "toggle"}),
        "light_on": NetworkCommand("light_on", "MQTT", "ratgdo/light/command", {"payload": "on"}),
        "light_off": NetworkCommand("light_off", "MQTT", "ratgdo/light/command", {"payload": "off"}),
        "lock": NetworkCommand("lock", "MQTT", "ratgdo/lock/command", {"payload": "lock"}),
        "unlock": NetworkCommand("unlock", "MQTT", "ratgdo/lock/command", {"payload": "unlock"}),
    },
)
register_profile(GARAGE_RATGDO)
