"""Pre-configured button profiles for known physical remotes.

This file contains button mappings for popular Zigbee, Bluetooth, and RF remotes.
When a user adds a physical remote and selects a model, these mappings are auto-applied.
"""

from dataclasses import dataclass, field
from typing import Any

# Standard button names that map to common actions
STANDARD_ACTIONS = {
    "power": {"icon": "mdi:power", "color": "#f44336"},
    "volume_up": {"icon": "mdi:volume-plus", "action_type": "volume_up"},
    "volume_down": {"icon": "mdi:volume-minus", "action_type": "volume_down"},
    "mute": {"icon": "mdi:volume-off", "action_type": "mute"},
    "play_pause": {"icon": "mdi:play-pause"},
    "next": {"icon": "mdi:skip-next"},
    "previous": {"icon": "mdi:skip-previous"},
    "up": {"icon": "mdi:chevron-up"},
    "down": {"icon": "mdi:chevron-down"},
    "left": {"icon": "mdi:chevron-left"},
    "right": {"icon": "mdi:chevron-right"},
    "ok": {"icon": "mdi:checkbox-blank-circle"},
    "back": {"icon": "mdi:arrow-left"},
    "home": {"icon": "mdi:home"},
    "menu": {"icon": "mdi:menu"},
    "brightness_up": {"icon": "mdi:brightness-6"},
    "brightness_down": {"icon": "mdi:brightness-4"},
    "on": {"icon": "mdi:power", "color": "#4caf50"},
    "off": {"icon": "mdi:power-off", "color": "#f44336"},
    "toggle": {"icon": "mdi:toggle-switch"},
    "scene_1": {"icon": "mdi:numeric-1-circle"},
    "scene_2": {"icon": "mdi:numeric-2-circle"},
    "scene_3": {"icon": "mdi:numeric-3-circle"},
    "scene_4": {"icon": "mdi:numeric-4-circle"},
}


@dataclass
class RemoteModelButton:
    """A button definition for a remote model."""
    button_id: str          # The ID reported by the remote (e.g., "on", "brightness_up")
    label: str              # Human-readable label
    icon: str = "mdi:gesture-tap-button"
    color: str | None = None
    suggested_action: str = "scene"  # scene, ir_command, ha_service, volume_up, etc.
    description: str = ""   # Help text for the user
    
    def to_dict(self) -> dict:
        return {
            "button_id": self.button_id,
            "label": self.label,
            "icon": self.icon,
            "color": self.color,
            "suggested_action": self.suggested_action,
            "description": self.description,
        }


@dataclass
class RemoteModel:
    """A known remote control model with pre-configured buttons."""
    id: str
    name: str
    manufacturer: str
    description: str = ""
    image_url: str = ""
    remote_type: str = "zigbee"  # zigbee, bluetooth, rf_433, rf_315
    zigbee_model: str = ""       # Zigbee model identifier (for auto-detection)
    buttons: list[RemoteModelButton] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "manufacturer": self.manufacturer,
            "description": self.description,
            "image_url": self.image_url,
            "remote_type": self.remote_type,
            "zigbee_model": self.zigbee_model,
            "buttons": [b.to_dict() for b in self.buttons],
        }


# ============================================================================
# IKEA Remotes
# ============================================================================

IKEA_SYMFONISK_GEN2 = RemoteModel(
    id="ikea_symfonisk_gen2",
    name="SYMFONISK Sound Remote Gen 2",
    manufacturer="IKEA",
    description="Rotary dial with play/pause and skip buttons. Works with Sonos speakers.",
    remote_type="zigbee",
    zigbee_model="SYMFONISK sound remote gen2",
    buttons=[
        RemoteModelButton("play_pause", "Play/Pause", "mdi:play-pause", description="Center button - toggle playback"),
        RemoteModelButton("volume_up", "Volume Up", "mdi:volume-plus", suggested_action="volume_up", description="Rotate clockwise"),
        RemoteModelButton("volume_down", "Volume Down", "mdi:volume-minus", suggested_action="volume_down", description="Rotate counter-clockwise"),
        RemoteModelButton("track_next", "Next Track", "mdi:skip-next", description="Double-click center or side button"),
        RemoteModelButton("track_previous", "Previous Track", "mdi:skip-previous", description="Triple-click center"),
        RemoteModelButton("dots_1_short", "Single Dot (Short)", "mdi:circle-small", description="Short press single dot"),
        RemoteModelButton("dots_1_long", "Single Dot (Long)", "mdi:circle", description="Long press single dot"),
        RemoteModelButton("dots_2_short", "Double Dot (Short)", "mdi:circle-double", description="Short press double dot"),
        RemoteModelButton("dots_2_long", "Double Dot (Long)", "mdi:circle-double", description="Long press double dot"),
    ]
)

IKEA_TRADFRI_REMOTE = RemoteModel(
    id="ikea_tradfri_remote",
    name="TRÅDFRI Remote Control",
    manufacturer="IKEA",
    description="5-button remote for TRÅDFRI lights. Round design with on/off, brightness, and arrow buttons.",
    remote_type="zigbee",
    zigbee_model="TRADFRI remote control",
    buttons=[
        RemoteModelButton("toggle", "Power Toggle", "mdi:power", "#4caf50", description="Center button"),
        RemoteModelButton("brightness_up", "Brightness Up", "mdi:brightness-6", description="Top button - increase brightness"),
        RemoteModelButton("brightness_down", "Brightness Down", "mdi:brightness-4", description="Bottom button - decrease brightness"),
        RemoteModelButton("arrow_left", "Left Arrow", "mdi:chevron-left", description="Left button - previous scene/color"),
        RemoteModelButton("arrow_right", "Right Arrow", "mdi:chevron-right", description="Right button - next scene/color"),
    ]
)

IKEA_TRADFRI_DIMMER = RemoteModel(
    id="ikea_tradfri_dimmer",
    name="TRÅDFRI Wireless Dimmer",
    manufacturer="IKEA",
    description="Rotary dimmer with on/off button. Simple two-action remote.",
    remote_type="zigbee",
    zigbee_model="TRADFRI wireless dimmer",
    buttons=[
        RemoteModelButton("on", "Turn On", "mdi:power", "#4caf50", description="Short press"),
        RemoteModelButton("off", "Turn Off", "mdi:power-off", "#f44336", description="Long press"),
        RemoteModelButton("brightness_up", "Brightness Up", "mdi:brightness-6", description="Rotate clockwise"),
        RemoteModelButton("brightness_down", "Brightness Down", "mdi:brightness-4", description="Rotate counter-clockwise"),
    ]
)

IKEA_STYRBAR = RemoteModel(
    id="ikea_styrbar",
    name="STYRBAR Remote Control",
    manufacturer="IKEA",
    description="4-button remote with on/off and brightness controls. Rectangular design.",
    remote_type="zigbee",
    zigbee_model="Remote Control N2",
    buttons=[
        RemoteModelButton("on", "Turn On", "mdi:power", "#4caf50", description="Top left button"),
        RemoteModelButton("off", "Turn Off", "mdi:power-off", "#f44336", description="Bottom left button"),
        RemoteModelButton("brightness_up", "Brightness Up", "mdi:brightness-6", description="Top right button"),
        RemoteModelButton("brightness_down", "Brightness Down", "mdi:brightness-4", description="Bottom right button"),
    ]
)

IKEA_RODRET = RemoteModel(
    id="ikea_rodret",
    name="RODRET Wireless Dimmer",
    manufacturer="IKEA",
    description="Simple 2-button dimmer remote.",
    remote_type="zigbee",
    zigbee_model="RODRET Dimmer",
    buttons=[
        RemoteModelButton("on", "On / Brightness Up", "mdi:brightness-6", "#4caf50", description="Top button"),
        RemoteModelButton("off", "Off / Brightness Down", "mdi:brightness-4", "#f44336", description="Bottom button"),
    ]
)

# ============================================================================
# Philips Hue Remotes
# ============================================================================

HUE_DIMMER_SWITCH = RemoteModel(
    id="hue_dimmer_switch",
    name="Hue Dimmer Switch",
    manufacturer="Philips",
    description="4-button remote with On, Off, and brightness controls.",
    remote_type="zigbee",
    zigbee_model="RWL021",
    buttons=[
        RemoteModelButton("on", "On", "mdi:power", "#4caf50", description="Top button - turns on lights"),
        RemoteModelButton("brightness_up", "Brightness Up", "mdi:brightness-6", description="Second button - increase brightness"),
        RemoteModelButton("brightness_down", "Brightness Down", "mdi:brightness-4", description="Third button - decrease brightness"),
        RemoteModelButton("off", "Off", "mdi:power-off", "#f44336", description="Bottom button - turns off lights"),
    ]
)

HUE_TAP_DIAL = RemoteModel(
    id="hue_tap_dial",
    name="Hue Tap Dial Switch",
    manufacturer="Philips",
    description="4 scene buttons plus rotary dial for dimming.",
    remote_type="zigbee",
    zigbee_model="RDM002",
    buttons=[
        RemoteModelButton("button_1", "Button 1", "mdi:numeric-1-circle", description="Top left - Scene 1"),
        RemoteModelButton("button_2", "Button 2", "mdi:numeric-2-circle", description="Top right - Scene 2"),
        RemoteModelButton("button_3", "Button 3", "mdi:numeric-3-circle", description="Bottom left - Scene 3"),
        RemoteModelButton("button_4", "Button 4", "mdi:numeric-4-circle", description="Bottom right - Scene 4"),
        RemoteModelButton("dial_rotate_left", "Dial Left", "mdi:rotate-left", suggested_action="volume_down", description="Rotate counter-clockwise"),
        RemoteModelButton("dial_rotate_right", "Dial Right", "mdi:rotate-right", suggested_action="volume_up", description="Rotate clockwise"),
    ]
)

# ============================================================================
# Aqara/Xiaomi Remotes
# ============================================================================

AQARA_OPPLE_6 = RemoteModel(
    id="aqara_opple_6",
    name="Aqara Opple 6-Button",
    manufacturer="Aqara",
    description="6-button wireless switch. Each button supports single, double, and long press.",
    remote_type="zigbee",
    zigbee_model="lumi.remote.b686opcn01",
    buttons=[
        RemoteModelButton("button_1_single", "Button 1", "mdi:numeric-1-box", description="Top left - single press"),
        RemoteModelButton("button_1_double", "Button 1 (2x)", "mdi:numeric-1-box-multiple", description="Top left - double press"),
        RemoteModelButton("button_1_hold", "Button 1 (Hold)", "mdi:numeric-1-box", description="Top left - long press"),
        RemoteModelButton("button_2_single", "Button 2", "mdi:numeric-2-box", description="Top right - single press"),
        RemoteModelButton("button_2_double", "Button 2 (2x)", "mdi:numeric-2-box-multiple", description="Top right - double press"),
        RemoteModelButton("button_2_hold", "Button 2 (Hold)", "mdi:numeric-2-box", description="Top right - long press"),
        RemoteModelButton("button_3_single", "Button 3", "mdi:numeric-3-box", description="Middle left - single press"),
        RemoteModelButton("button_4_single", "Button 4", "mdi:numeric-4-box", description="Middle right - single press"),
        RemoteModelButton("button_5_single", "Button 5", "mdi:numeric-5-box", description="Bottom left - single press"),
        RemoteModelButton("button_6_single", "Button 6", "mdi:numeric-6-box", description="Bottom right - single press"),
    ]
)

AQARA_MINI_SWITCH = RemoteModel(
    id="aqara_mini_switch",
    name="Aqara Mini Switch",
    manufacturer="Aqara",
    description="Single button switch with single, double, and long press actions.",
    remote_type="zigbee",
    zigbee_model="lumi.remote.b1acn01",
    buttons=[
        RemoteModelButton("single", "Single Press", "mdi:gesture-tap", description="Single tap"),
        RemoteModelButton("double", "Double Press", "mdi:gesture-double-tap", description="Double tap"),
        RemoteModelButton("hold", "Long Press", "mdi:gesture-tap-hold", description="Press and hold"),
    ]
)

AQARA_CUBE = RemoteModel(
    id="aqara_cube",
    name="Aqara Magic Cube",
    manufacturer="Aqara",
    description="6-sided cube with gesture controls: shake, flip, rotate, tap.",
    remote_type="zigbee",
    zigbee_model="lumi.sensor_cube",
    buttons=[
        RemoteModelButton("shake", "Shake", "mdi:vibrate", description="Shake the cube"),
        RemoteModelButton("flip90", "Flip 90°", "mdi:rotate-3d-variant", description="Flip cube 90 degrees"),
        RemoteModelButton("flip180", "Flip 180°", "mdi:sync", description="Flip cube 180 degrees"),
        RemoteModelButton("rotate_left", "Rotate Left", "mdi:rotate-left", suggested_action="volume_down", description="Rotate on surface counter-clockwise"),
        RemoteModelButton("rotate_right", "Rotate Right", "mdi:rotate-right", suggested_action="volume_up", description="Rotate on surface clockwise"),
        RemoteModelButton("tap", "Tap", "mdi:gesture-tap", description="Tap twice on surface"),
        RemoteModelButton("slide", "Slide", "mdi:gesture-swipe", description="Slide on surface"),
    ]
)

# ============================================================================
# Lutron Remotes
# ============================================================================

LUTRON_PICO = RemoteModel(
    id="lutron_pico",
    name="Lutron Pico Remote",
    manufacturer="Lutron",
    description="5-button remote for Caseta smart lighting. On, Off, Favorite, Up, Down.",
    remote_type="rf_433",
    buttons=[
        RemoteModelButton("on", "On", "mdi:power", "#4caf50", description="Top button - turns on at last level"),
        RemoteModelButton("favorite", "Favorite", "mdi:star", "#ffc107", description="Middle button - favorite level"),
        RemoteModelButton("off", "Off", "mdi:power-off", "#f44336", description="Bottom button - turns off"),
        RemoteModelButton("raise", "Raise", "mdi:chevron-up", description="Up arrow - raise brightness"),
        RemoteModelButton("lower", "Lower", "mdi:chevron-down", description="Down arrow - lower brightness"),
    ]
)

# ============================================================================
# Sonoff Remotes
# ============================================================================

SONOFF_SNZB_01 = RemoteModel(
    id="sonoff_snzb01",
    name="SONOFF SNZB-01",
    manufacturer="SONOFF",
    description="Zigbee wireless button with single, double, and long press.",
    remote_type="zigbee",
    zigbee_model="WB01",
    buttons=[
        RemoteModelButton("single", "Single Press", "mdi:gesture-tap", description="Single tap"),
        RemoteModelButton("double", "Double Press", "mdi:gesture-double-tap", description="Double tap"),
        RemoteModelButton("long", "Long Press", "mdi:gesture-tap-hold", description="Press and hold"),
    ]
)

# ============================================================================
# Tuya Remotes
# ============================================================================

TUYA_4_BUTTON = RemoteModel(
    id="tuya_4_button",
    name="Tuya 4-Button Scene Remote",
    manufacturer="Tuya",
    description="Generic 4-button Zigbee scene controller.",
    remote_type="zigbee",
    zigbee_model="TS0044",
    buttons=[
        RemoteModelButton("button_1", "Button 1", "mdi:numeric-1-circle", description="Top left button"),
        RemoteModelButton("button_2", "Button 2", "mdi:numeric-2-circle", description="Top right button"),
        RemoteModelButton("button_3", "Button 3", "mdi:numeric-3-circle", description="Bottom left button"),
        RemoteModelButton("button_4", "Button 4", "mdi:numeric-4-circle", description="Bottom right button"),
    ]
)

# ============================================================================
# Apple/Siri Remotes
# ============================================================================

APPLE_TV_REMOTE = RemoteModel(
    id="apple_tv_remote",
    name="Apple TV Remote (Siri)",
    manufacturer="Apple",
    description="Apple TV Siri Remote with touchpad, Siri button, and playback controls.",
    remote_type="bluetooth",
    buttons=[
        RemoteModelButton("menu", "Menu/Back", "mdi:arrow-left", description="Menu button - go back"),
        RemoteModelButton("tv_home", "TV/Home", "mdi:television", description="TV button - go to home screen"),
        RemoteModelButton("siri", "Siri", "mdi:microphone", description="Siri button - voice control"),
        RemoteModelButton("play_pause", "Play/Pause", "mdi:play-pause", description="Playback toggle"),
        RemoteModelButton("up", "Up", "mdi:chevron-up", description="Swipe/click up"),
        RemoteModelButton("down", "Down", "mdi:chevron-down", description="Swipe/click down"),
        RemoteModelButton("left", "Left", "mdi:chevron-left", description="Swipe/click left"),
        RemoteModelButton("right", "Right", "mdi:chevron-right", description="Swipe/click right"),
        RemoteModelButton("select", "Select", "mdi:checkbox-blank-circle", description="Click center"),
        RemoteModelButton("volume_up", "Volume Up", "mdi:volume-plus", suggested_action="volume_up"),
        RemoteModelButton("volume_down", "Volume Down", "mdi:volume-minus", suggested_action="volume_down"),
    ]
)

AMAZON_FIRE_REMOTE = RemoteModel(
    id="amazon_fire_remote",
    name="Fire TV Remote",
    manufacturer="Amazon",
    description="Fire TV Alexa Voice Remote with navigation and playback controls.",
    remote_type="bluetooth",
    buttons=[
        RemoteModelButton("home", "Home", "mdi:home", description="Home button"),
        RemoteModelButton("back", "Back", "mdi:arrow-left", description="Back button"),
        RemoteModelButton("menu", "Menu", "mdi:menu", description="Menu button (3 lines)"),
        RemoteModelButton("alexa", "Alexa", "mdi:microphone", "#00caff", description="Voice button"),
        RemoteModelButton("up", "Up", "mdi:chevron-up"),
        RemoteModelButton("down", "Down", "mdi:chevron-down"),
        RemoteModelButton("left", "Left", "mdi:chevron-left"),
        RemoteModelButton("right", "Right", "mdi:chevron-right"),
        RemoteModelButton("select", "Select", "mdi:checkbox-blank-circle"),
        RemoteModelButton("play_pause", "Play/Pause", "mdi:play-pause"),
        RemoteModelButton("rewind", "Rewind", "mdi:rewind"),
        RemoteModelButton("fast_forward", "Fast Forward", "mdi:fast-forward"),
        RemoteModelButton("volume_up", "Volume Up", "mdi:volume-plus", suggested_action="volume_up"),
        RemoteModelButton("volume_down", "Volume Down", "mdi:volume-minus", suggested_action="volume_down"),
        RemoteModelButton("mute", "Mute", "mdi:volume-off", suggested_action="mute"),
    ]
)

# ============================================================================
# Model Registry
# ============================================================================

REMOTE_MODELS: dict[str, RemoteModel] = {
    # IKEA
    "ikea_symfonisk_gen2": IKEA_SYMFONISK_GEN2,
    "ikea_tradfri_remote": IKEA_TRADFRI_REMOTE,
    "ikea_tradfri_dimmer": IKEA_TRADFRI_DIMMER,
    "ikea_styrbar": IKEA_STYRBAR,
    "ikea_rodret": IKEA_RODRET,
    # Philips Hue
    "hue_dimmer_switch": HUE_DIMMER_SWITCH,
    "hue_tap_dial": HUE_TAP_DIAL,
    # Aqara
    "aqara_opple_6": AQARA_OPPLE_6,
    "aqara_mini_switch": AQARA_MINI_SWITCH,
    "aqara_cube": AQARA_CUBE,
    # Lutron
    "lutron_pico": LUTRON_PICO,
    # Sonoff
    "sonoff_snzb01": SONOFF_SNZB_01,
    # Tuya
    "tuya_4_button": TUYA_4_BUTTON,
    # Apple/Amazon
    "apple_tv_remote": APPLE_TV_REMOTE,
    "amazon_fire_remote": AMAZON_FIRE_REMOTE,
}

# Group by manufacturer for UI
REMOTE_MODELS_BY_MANUFACTURER: dict[str, list[RemoteModel]] = {}
for model in REMOTE_MODELS.values():
    if model.manufacturer not in REMOTE_MODELS_BY_MANUFACTURER:
        REMOTE_MODELS_BY_MANUFACTURER[model.manufacturer] = []
    REMOTE_MODELS_BY_MANUFACTURER[model.manufacturer].append(model)


def get_model(model_id: str) -> RemoteModel | None:
    """Get a remote model by ID."""
    return REMOTE_MODELS.get(model_id)


def get_model_by_zigbee(zigbee_model: str) -> RemoteModel | None:
    """Find a remote model by its Zigbee model identifier."""
    for model in REMOTE_MODELS.values():
        if model.zigbee_model and model.zigbee_model.lower() in zigbee_model.lower():
            return model
    return None


def list_models() -> list[dict]:
    """List all available remote models."""
    return [m.to_dict() for m in REMOTE_MODELS.values()]


def list_models_grouped() -> dict[str, list[dict]]:
    """List all models grouped by manufacturer."""
    result = {}
    for manufacturer, models in REMOTE_MODELS_BY_MANUFACTURER.items():
        result[manufacturer] = [m.to_dict() for m in models]
    return result


# ============================================================================
# Bluetooth Device Name Patterns for Auto-Detection
# ============================================================================

# Maps name patterns (lowercase) to model IDs
BLUETOOTH_NAME_PATTERNS: dict[str, list[str]] = {
    # Amazon Fire TV remotes
    "amazon_fire_remote": ["fire tv", "firetv", "amazon fire", "fire stick"],
    "amazon_l5b83g": ["l5b83g", "l5b83h", "cv98lm"],
    
    # Apple remotes
    "apple_tv_remote": ["apple tv remote", "siri remote", "apple remote"],
    
    # G20 series air mouse remotes
    "g20s_pro_plus": ["g20s", "g20bts", "g20 pro", "20bts"],
    
    # Generic Android TV remotes
    "rupa_bt_remote": ["rupa", "rupa remote"],
    "dupad_story_remote": ["dupad", "dupad story"],
    
    # Common air mouse patterns
    "g20s_pro_plus": ["air mouse", "airmouse", "gyro remote", "gyroscope"],
    
    # MX3 style remotes (common rebranded)
    "g20s_pro_plus": ["mx3", "mx-3", "minix"],
    
    # Generic keyboard remotes
    "g20s_pro_plus": ["rii", "ipazzport", "wechip", "mele"],
}

# Chipset/manufacturer hints from service data
BLUETOOTH_MANUFACTURER_HINTS: dict[str, str] = {
    "amazon": "amazon_fire_remote",
    "apple": "apple_tv_remote",
    "nvidia": None,  # Shield uses WiFi, not BT remote
    "roku": None,    # Roku uses WiFi
}


def match_bluetooth_device(name: str, manufacturer: str | None = None) -> dict | None:
    """
    Match a Bluetooth device to a known remote model.
    
    Returns dict with:
        - model_id: The matched model ID
        - model: The full RemoteModel object as dict
        - confidence: "high", "medium", or "low"
        - match_reason: Why this model was matched
    """
    if not name:
        return None
    
    name_lower = name.lower().strip()
    mfr_lower = (manufacturer or "").lower()
    
    # Check exact/high confidence patterns first
    for model_id, patterns in BLUETOOTH_NAME_PATTERNS.items():
        for pattern in patterns:
            if pattern in name_lower:
                model = REMOTE_MODELS.get(model_id)
                if model:
                    return {
                        "model_id": model_id,
                        "model": model.to_dict(),
                        "confidence": "high" if len(pattern) > 4 else "medium",
                        "match_reason": f"Name contains '{pattern}'"
                    }
    
    # Check manufacturer hints
    if mfr_lower:
        for mfr_pattern, model_id in BLUETOOTH_MANUFACTURER_HINTS.items():
            if mfr_pattern in mfr_lower and model_id:
                model = REMOTE_MODELS.get(model_id)
                if model:
                    return {
                        "model_id": model_id,
                        "model": model.to_dict(),
                        "confidence": "low",
                        "match_reason": f"Manufacturer '{manufacturer}'"
                    }
    
    # Generic remote detection - suggest the most versatile model
    generic_keywords = ["remote", "keyboard", "controller", "input"]
    if any(kw in name_lower for kw in generic_keywords):
        model = REMOTE_MODELS.get("g20s_pro_plus")
        if model:
            return {
                "model_id": "g20s_pro_plus",
                "model": model.to_dict(),
                "confidence": "low",
                "match_reason": "Generic Bluetooth remote - using versatile mapping"
            }
    
    return None


def get_model_for_bluetooth(name: str, manufacturer: str | None = None, service_uuids: list[str] | None = None) -> dict | None:
    """
    Get the best matching model for a Bluetooth device.
    Also checks for HID service UUID to confirm it's likely a remote.
    """
    # First check if it has HID UUID (keyboard/mouse/remote)
    has_hid = False
    if service_uuids:
        has_hid = any("1812" in str(uuid).lower() for uuid in service_uuids)
    
    match = match_bluetooth_device(name, manufacturer)
    
    if match:
        match["has_hid_service"] = has_hid
        return match
    
    # If no match but has HID service, it's probably a remote
    if has_hid:
        model = REMOTE_MODELS.get("g20s_pro_plus")
        if model:
            return {
                "model_id": "g20s_pro_plus",
                "model": model.to_dict(),
                "confidence": "low",
                "match_reason": "Has HID service UUID - likely a remote/keyboard",
                "has_hid_service": True
            }
    
    return None

# ============================================================================
# Budget/Generic Android TV Remotes
# ============================================================================

RUPA_REMOTE = RemoteModel(
    id="rupa_bt_remote",
    name="RUPA Bluetooth Voice Remote",
    manufacturer="RUPA",
    description="Budget Bluetooth voice remote for Android TV boxes. Includes voice, navigation, and media controls.",
    remote_type="bluetooth",
    buttons=[
        RemoteModelButton("power", "Power", "mdi:power", "#f44336"),
        RemoteModelButton("voice", "Voice/Mic", "mdi:microphone", "#2196f3", description="Voice search button"),
        RemoteModelButton("home", "Home", "mdi:home"),
        RemoteModelButton("back", "Back", "mdi:arrow-left"),
        RemoteModelButton("up", "Up", "mdi:chevron-up"),
        RemoteModelButton("down", "Down", "mdi:chevron-down"),
        RemoteModelButton("left", "Left", "mdi:chevron-left"),
        RemoteModelButton("right", "Right", "mdi:chevron-right"),
        RemoteModelButton("ok", "OK/Select", "mdi:checkbox-blank-circle"),
        RemoteModelButton("menu", "Menu", "mdi:menu"),
        RemoteModelButton("volume_up", "Volume Up", "mdi:volume-plus", suggested_action="volume_up"),
        RemoteModelButton("volume_down", "Volume Down", "mdi:volume-minus", suggested_action="volume_down"),
        RemoteModelButton("mute", "Mute", "mdi:volume-off", suggested_action="mute"),
        RemoteModelButton("play_pause", "Play/Pause", "mdi:play-pause"),
    ]
)

DUPAD_STORY_REMOTE = RemoteModel(
    id="dupad_story_remote",
    name="Dupad Story Bluetooth Remote",
    manufacturer="Dupad Story",
    description="Bluetooth remote with voice control for Android TV boxes and streaming devices.",
    remote_type="bluetooth",
    buttons=[
        RemoteModelButton("power", "Power", "mdi:power", "#f44336"),
        RemoteModelButton("voice", "Voice", "mdi:microphone", "#4caf50", description="Press and hold for voice search"),
        RemoteModelButton("home", "Home", "mdi:home"),
        RemoteModelButton("back", "Back", "mdi:arrow-left"),
        RemoteModelButton("up", "Up", "mdi:chevron-up"),
        RemoteModelButton("down", "Down", "mdi:chevron-down"),
        RemoteModelButton("left", "Left", "mdi:chevron-left"),
        RemoteModelButton("right", "Right", "mdi:chevron-right"),
        RemoteModelButton("ok", "OK/Select", "mdi:checkbox-blank-circle"),
        RemoteModelButton("menu", "Menu", "mdi:menu"),
        RemoteModelButton("settings", "Settings", "mdi:cog"),
        RemoteModelButton("volume_up", "Volume Up", "mdi:volume-plus", suggested_action="volume_up"),
        RemoteModelButton("volume_down", "Volume Down", "mdi:volume-minus", suggested_action="volume_down"),
        RemoteModelButton("mute", "Mute", "mdi:volume-off", suggested_action="mute"),
        RemoteModelButton("play_pause", "Play/Pause", "mdi:play-pause"),
        RemoteModelButton("rewind", "Rewind", "mdi:rewind"),
        RemoteModelButton("fast_forward", "Fast Forward", "mdi:fast-forward"),
    ]
)

AMAZON_L5B83G_REMOTE = RemoteModel(
    id="amazon_l5b83g",
    name="Amazon Fire TV Voice Remote (L5B83G)",
    manufacturer="Amazon",
    description="Amazon Fire TV Bluetooth Voice Remote with Alexa. Universal model with quick access buttons.",
    remote_type="bluetooth",
    buttons=[
        RemoteModelButton("power", "Power", "mdi:power", "#f44336", description="Turn TV on/off"),
        RemoteModelButton("alexa", "Alexa Voice", "mdi:microphone", "#00caff", description="Press and hold for Alexa"),
        RemoteModelButton("home", "Home", "mdi:home"),
        RemoteModelButton("back", "Back", "mdi:arrow-left"),
        RemoteModelButton("menu", "Menu", "mdi:menu"),
        RemoteModelButton("up", "Up", "mdi:chevron-up"),
        RemoteModelButton("down", "Down", "mdi:chevron-down"),
        RemoteModelButton("left", "Left", "mdi:chevron-left"),
        RemoteModelButton("right", "Right", "mdi:chevron-right"),
        RemoteModelButton("select", "Select", "mdi:checkbox-blank-circle"),
        RemoteModelButton("play_pause", "Play/Pause", "mdi:play-pause"),
        RemoteModelButton("rewind", "Rewind", "mdi:rewind"),
        RemoteModelButton("fast_forward", "Fast Forward", "mdi:fast-forward"),
        RemoteModelButton("volume_up", "Volume Up", "mdi:volume-plus", suggested_action="volume_up"),
        RemoteModelButton("volume_down", "Volume Down", "mdi:volume-minus", suggested_action="volume_down"),
        RemoteModelButton("mute", "Mute", "mdi:volume-off", suggested_action="mute"),
        RemoteModelButton("app_1", "App Button 1", "mdi:apps", description="Quick launch button (configurable)"),
        RemoteModelButton("app_2", "App Button 2", "mdi:apps", description="Quick launch button (configurable)"),
        RemoteModelButton("app_3", "App Button 3", "mdi:apps", description="Quick launch button (configurable)"),
        RemoteModelButton("app_4", "App Button 4", "mdi:apps", description="Quick launch button (configurable)"),
    ]
)

G20S_PRO_PLUS_REMOTE = RemoteModel(
    id="g20s_pro_plus",
    name="G20S Pro Plus Air Mouse",
    manufacturer="Generic",
    description="20BTS Plus Wireless Bluetooth 5.0 Voice Backlit Remote with 2.4G USB dongle, gyroscope air mouse, and IR learning.",
    remote_type="bluetooth",
    buttons=[
        RemoteModelButton("power", "Power", "mdi:power", "#f44336"),
        RemoteModelButton("voice", "Voice/Mic", "mdi:microphone", "#4caf50", description="Voice search button"),
        RemoteModelButton("home", "Home", "mdi:home"),
        RemoteModelButton("back", "Back", "mdi:arrow-left"),
        RemoteModelButton("menu", "Menu", "mdi:menu"),
        RemoteModelButton("up", "Up", "mdi:chevron-up"),
        RemoteModelButton("down", "Down", "mdi:chevron-down"),
        RemoteModelButton("left", "Left", "mdi:chevron-left"),
        RemoteModelButton("right", "Right", "mdi:chevron-right"),
        RemoteModelButton("ok", "OK/Select", "mdi:checkbox-blank-circle"),
        RemoteModelButton("volume_up", "Volume Up", "mdi:volume-plus", suggested_action="volume_up"),
        RemoteModelButton("volume_down", "Volume Down", "mdi:volume-minus", suggested_action="volume_down"),
        RemoteModelButton("mute", "Mute", "mdi:volume-off", suggested_action="mute"),
        RemoteModelButton("play_pause", "Play/Pause", "mdi:play-pause"),
        RemoteModelButton("rewind", "Rewind", "mdi:rewind"),
        RemoteModelButton("fast_forward", "Fast Forward", "mdi:fast-forward"),
        RemoteModelButton("stop", "Stop", "mdi:stop"),
        RemoteModelButton("channel_up", "Channel Up", "mdi:chevron-double-up"),
        RemoteModelButton("channel_down", "Channel Down", "mdi:chevron-double-down"),
        RemoteModelButton("mouse_mode", "Mouse/Air Mode", "mdi:cursor-move", description="Toggle gyroscope air mouse"),
        RemoteModelButton("keyboard", "Keyboard", "mdi:keyboard", description="On-screen keyboard"),
        RemoteModelButton("num_0", "0", "mdi:numeric-0"),
        RemoteModelButton("num_1", "1", "mdi:numeric-1"),
        RemoteModelButton("num_2", "2", "mdi:numeric-2"),
        RemoteModelButton("num_3", "3", "mdi:numeric-3"),
        RemoteModelButton("num_4", "4", "mdi:numeric-4"),
        RemoteModelButton("num_5", "5", "mdi:numeric-5"),
        RemoteModelButton("num_6", "6", "mdi:numeric-6"),
        RemoteModelButton("num_7", "7", "mdi:numeric-7"),
        RemoteModelButton("num_8", "8", "mdi:numeric-8"),
        RemoteModelButton("num_9", "9", "mdi:numeric-9"),
        RemoteModelButton("ir_tv_power", "IR TV Power", "mdi:television", description="IR learning button for TV power"),
        RemoteModelButton("ir_input", "IR Input/Source", "mdi:import", description="IR learning button for input select"),
    ]
)

# Add new remotes to registry
REMOTE_MODELS["rupa_bt_remote"] = RUPA_REMOTE
REMOTE_MODELS["dupad_story_remote"] = DUPAD_STORY_REMOTE
REMOTE_MODELS["amazon_l5b83g"] = AMAZON_L5B83G_REMOTE
REMOTE_MODELS["g20s_pro_plus"] = G20S_PRO_PLUS_REMOTE

# Update manufacturer groupings
for model_id in ["rupa_bt_remote", "dupad_story_remote", "amazon_l5b83g", "g20s_pro_plus"]:
    model = REMOTE_MODELS[model_id]
    if model.manufacturer not in REMOTE_MODELS_BY_MANUFACTURER:
        REMOTE_MODELS_BY_MANUFACTURER[model.manufacturer] = []
    REMOTE_MODELS_BY_MANUFACTURER[model.manufacturer].append(model)
