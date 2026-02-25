"""PlayStation profiles."""

# PS5 primarily uses Bluetooth and HDMI-CEC, limited IR support via media remote
PS5_NETWORK = DeviceProfile(
    id="ps5_network",
    name="PlayStation 5 (Network)",
    brand="Sony",
    category="game_console",
    model_years="2020+",
    description="PS5 network control. Requires PS Remote Play or third-party integration.",
    control_methods=[ControlMethod.NETWORK, ControlMethod.HDMI_CEC, ControlMethod.BLUETOOTH],
    logo_url=BRAND_LOGOS.get("playstation", ""),
    network_port=987,
    network_protocol="ps-remote",
    network_commands={
        "power_on": NetworkCommand("power_on", "PS", "power_on", {}),
        "power_off": NetworkCommand("power_off", "PS", "standby", {}),
        "up": NetworkCommand("up", "PS", "up", {}),
        "down": NetworkCommand("down", "PS", "down", {}),
        "left": NetworkCommand("left", "PS", "left", {}),
        "right": NetworkCommand("right", "PS", "right", {}),
        "enter": NetworkCommand("enter", "PS", "enter", {}),
        "back": NetworkCommand("back", "PS", "back", {}),
        "ps_button": NetworkCommand("ps_button", "PS", "ps", {}),
        "options": NetworkCommand("options", "PS", "options", {}),
    },
)
register_profile(PS5_NETWORK)

PS4_NETWORK = DeviceProfile(
    id="ps4_network",
    name="PlayStation 4 (Network)",
    brand="Sony",
    category="game_console",
    model_years="2013-2020",
    description="PS4 network control via PS4-WAKER or similar.",
    control_methods=[ControlMethod.NETWORK, ControlMethod.HDMI_CEC],
    logo_url=BRAND_LOGOS.get("playstation", ""),
    network_port=987,
    network_protocol="ps-remote",
    network_commands={
        "power_on": NetworkCommand("power_on", "PS4", "power_on", {}),
        "power_off": NetworkCommand("power_off", "PS4", "standby", {}),
        "start_app": NetworkCommand("start_app", "PS4", "start {app_id}", {}),
    },
)
register_profile(PS4_NETWORK)
