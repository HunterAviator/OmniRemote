"""Nintendo Switch profile."""

# =============================================================================
# Nintendo Switch - HDMI-CEC Only
# =============================================================================
NINTENDO_SWITCH = DeviceProfile(
    id="nintendo_switch",
    name="Nintendo Switch",
    brand="Nintendo",
    category="game_console",
    model_years="2017+",
    description="Nintendo Switch - HDMI-CEC only (limited control). Switch does not support IR.",
    control_methods=[ControlMethod.HDMI_CEC],
    logo_url=BRAND_LOGOS.get("nintendo", ""),
    # Switch has no IR receiver - it uses HDMI-CEC for TV control only
    # The Switch itself cannot be controlled via IR/Network
    # These are CEC commands that can be sent TO the Switch
    network_commands={
        # HDMI-CEC commands (via HA HDMI-CEC integration)
        "power_on": NetworkCommand("power_on", "CEC", "on", {}),
        "power_off": NetworkCommand("power_off", "CEC", "standby", {}),
        "select": NetworkCommand("select", "CEC", "set_stream_path", {}),
    },
)
register_profile(NINTENDO_SWITCH)


# =============================================================================
# Nintendo Switch - With Dock/HDMI Adapter Workaround
# Using Smart Plug for Power Control
# =============================================================================
NINTENDO_SWITCH_DOCK = DeviceProfile(
    id="nintendo_switch_dock",
    name="Nintendo Switch (Dock Setup)",
    brand="Nintendo",
    category="game_console",
    model_years="2017+",
    description="Nintendo Switch docked setup - Uses smart plug for power control and HDMI-CEC.",
    control_methods=[ControlMethod.HDMI_CEC, ControlMethod.NETWORK],
    logo_url=BRAND_LOGOS.get("nintendo", ""),
    network_commands={
        # These would be Home Assistant services called via scenes
        "dock_power_on": NetworkCommand("dock_power_on", "HA_SERVICE", "switch.turn_on", {"entity_id": "switch.nintendo_dock"}),
        "dock_power_off": NetworkCommand("dock_power_off", "HA_SERVICE", "switch.turn_off", {"entity_id": "switch.nintendo_dock"}),
        "cec_power_on": NetworkCommand("cec_power_on", "CEC", "on", {}),
        "cec_select_input": NetworkCommand("cec_select_input", "CEC", "set_stream_path", {}),
    },
)
register_profile(NINTENDO_SWITCH_DOCK)
