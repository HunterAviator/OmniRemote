"""Activities - Complex multi-device workflows with timing, app launching, and channel selection."""
from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any
import uuid

from .const import Device, RemoteCode
from .network_devices import (
    RokuController,
    FireTVController,
    OnkyoController,
    ShellyController,
    BenQProjectorController,
    get_controller,
)

_LOGGER = logging.getLogger(__name__)


class ActionType(Enum):
    """Types of actions in an activity."""
    IR_COMMAND = "ir_command"       # Send IR code
    RF_COMMAND = "rf_command"       # Send RF code
    NETWORK_COMMAND = "network_command"  # Send network command
    LAUNCH_APP = "launch_app"       # Launch an app (Roku/FireTV)
    TUNE_CHANNEL = "tune_channel"   # Tune to a channel
    SET_INPUT = "set_input"         # Set device input
    SET_VOLUME = "set_volume"       # Set volume level
    POWER_ON = "power_on"           # Power on device
    POWER_OFF = "power_off"         # Power off device
    WAIT = "wait"                   # Wait/delay
    CONDITION = "condition"         # Conditional action
    KEYPRESS_SEQUENCE = "keypress_sequence"  # Multiple key presses
    TEXT_INPUT = "text_input"       # Type text (search, etc.)
    HTTP_REQUEST = "http_request"   # Custom HTTP request
    HA_SERVICE = "ha_service"       # Call Home Assistant service


@dataclass
class ActivityAction:
    """A single action within an activity."""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    action_type: ActionType = ActionType.IR_COMMAND
    device_id: str = ""
    
    # IR/RF command
    command_name: str = ""
    repeat_count: int = 1
    
    # App launching
    app_id: str = ""
    app_name: str = ""
    content_id: str = ""  # For deep linking
    
    # Channel tuning
    channel_number: str = ""
    channel_name: str = ""
    
    # Input selection
    input_name: str = ""
    
    # Volume
    volume_level: int = 0
    volume_relative: bool = False  # True = +/-, False = absolute
    
    # Timing
    delay_before: float = 0.0  # Delay before this action
    delay_after: float = 0.5   # Delay after this action
    
    # Text input
    text: str = ""
    
    # HTTP request
    url: str = ""
    method: str = "GET"
    
    # Home Assistant service
    service: str = ""
    service_data: dict = field(default_factory=dict)
    
    # Keypress sequence
    key_sequence: list[str] = field(default_factory=list)
    key_delay: float = 0.2
    
    # Condition
    condition_entity: str = ""
    condition_state: str = ""
    condition_true_actions: list[str] = field(default_factory=list)  # Action IDs
    condition_false_actions: list[str] = field(default_factory=list)
    
    # Metadata
    description: str = ""
    enabled: bool = True
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "action_type": self.action_type.value,
            "device_id": self.device_id,
            "command_name": self.command_name,
            "repeat_count": self.repeat_count,
            "app_id": self.app_id,
            "app_name": self.app_name,
            "content_id": self.content_id,
            "channel_number": self.channel_number,
            "channel_name": self.channel_name,
            "input_name": self.input_name,
            "volume_level": self.volume_level,
            "volume_relative": self.volume_relative,
            "delay_before": self.delay_before,
            "delay_after": self.delay_after,
            "text": self.text,
            "url": self.url,
            "method": self.method,
            "service": self.service,
            "service_data": self.service_data,
            "key_sequence": self.key_sequence,
            "key_delay": self.key_delay,
            "condition_entity": self.condition_entity,
            "condition_state": self.condition_state,
            "condition_true_actions": self.condition_true_actions,
            "condition_false_actions": self.condition_false_actions,
            "description": self.description,
            "enabled": self.enabled,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "ActivityAction":
        return cls(
            id=data.get("id", str(uuid.uuid4())[:8]),
            action_type=ActionType(data.get("action_type", "ir_command")),
            device_id=data.get("device_id", ""),
            command_name=data.get("command_name", ""),
            repeat_count=data.get("repeat_count", 1),
            app_id=data.get("app_id", ""),
            app_name=data.get("app_name", ""),
            content_id=data.get("content_id", ""),
            channel_number=data.get("channel_number", ""),
            channel_name=data.get("channel_name", ""),
            input_name=data.get("input_name", ""),
            volume_level=data.get("volume_level", 0),
            volume_relative=data.get("volume_relative", False),
            delay_before=data.get("delay_before", 0.0),
            delay_after=data.get("delay_after", 0.5),
            text=data.get("text", ""),
            url=data.get("url", ""),
            method=data.get("method", "GET"),
            service=data.get("service", ""),
            service_data=data.get("service_data", {}),
            key_sequence=data.get("key_sequence", []),
            key_delay=data.get("key_delay", 0.2),
            condition_entity=data.get("condition_entity", ""),
            condition_state=data.get("condition_state", ""),
            condition_true_actions=data.get("condition_true_actions", []),
            condition_false_actions=data.get("condition_false_actions", []),
            description=data.get("description", ""),
            enabled=data.get("enabled", True),
        )


@dataclass
class Activity:
    """A complete activity/macro with multiple actions."""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str = ""
    icon: str = "mdi:play"
    room_id: str | None = None
    
    # Actions in order
    actions: list[ActivityAction] = field(default_factory=list)
    
    # Startup state tracking
    device_power_states: dict[str, bool] = field(default_factory=dict)  # device_id -> should be on
    device_inputs: dict[str, str] = field(default_factory=dict)  # device_id -> input
    
    # Reverse actions for "End Activity"
    end_actions: list[ActivityAction] = field(default_factory=list)
    
    # Metadata
    description: str = ""
    category: str = ""  # e.g., "Watch TV", "Listen to Music", "Gaming"
    estimated_duration: float = 0.0  # Estimated time to complete
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "icon": self.icon,
            "room_id": self.room_id,
            "actions": [a.to_dict() for a in self.actions],
            "device_power_states": self.device_power_states,
            "device_inputs": self.device_inputs,
            "end_actions": [a.to_dict() for a in self.end_actions],
            "description": self.description,
            "category": self.category,
            "estimated_duration": self.estimated_duration,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Activity":
        return cls(
            id=data.get("id", str(uuid.uuid4())[:8]),
            name=data.get("name", ""),
            icon=data.get("icon", "mdi:play"),
            room_id=data.get("room_id"),
            actions=[ActivityAction.from_dict(a) for a in data.get("actions", [])],
            device_power_states=data.get("device_power_states", {}),
            device_inputs=data.get("device_inputs", {}),
            end_actions=[ActivityAction.from_dict(a) for a in data.get("end_actions", [])],
            description=data.get("description", ""),
            category=data.get("category", ""),
            estimated_duration=data.get("estimated_duration", 0.0),
        )


class ActivityRunner:
    """Executes activities with proper timing and error handling."""
    
    def __init__(self, hass, database):
        """Initialize the activity runner."""
        self.hass = hass
        self.database = database
        self._running_activities: dict[str, bool] = {}
        self._network_controllers: dict[str, Any] = {}
    
    async def run_activity(self, activity: Activity) -> bool:
        """Run an activity."""
        activity_id = activity.id
        
        if activity_id in self._running_activities:
            _LOGGER.warning(f"Activity {activity.name} is already running")
            return False
        
        self._running_activities[activity_id] = True
        _LOGGER.info(f"Starting activity: {activity.name}")
        
        try:
            for action in activity.actions:
                if not action.enabled:
                    continue
                
                if activity_id not in self._running_activities:
                    _LOGGER.info(f"Activity {activity.name} was cancelled")
                    return False
                
                # Delay before
                if action.delay_before > 0:
                    await asyncio.sleep(action.delay_before)
                
                # Execute action
                success = await self._execute_action(action)
                
                if not success:
                    _LOGGER.warning(f"Action failed: {action.description or action.action_type.value}")
                
                # Delay after
                if action.delay_after > 0:
                    await asyncio.sleep(action.delay_after)
            
            _LOGGER.info(f"Activity completed: {activity.name}")
            return True
            
        except Exception as e:
            _LOGGER.error(f"Activity failed: {activity.name} - {e}")
            return False
        finally:
            self._running_activities.pop(activity_id, None)
    
    async def stop_activity(self, activity_id: str) -> None:
        """Stop a running activity."""
        if activity_id in self._running_activities:
            del self._running_activities[activity_id]
    
    async def end_activity(self, activity: Activity) -> bool:
        """Run the end/cleanup actions of an activity."""
        _LOGGER.info(f"Ending activity: {activity.name}")
        
        try:
            for action in activity.end_actions:
                if not action.enabled:
                    continue
                
                if action.delay_before > 0:
                    await asyncio.sleep(action.delay_before)
                
                await self._execute_action(action)
                
                if action.delay_after > 0:
                    await asyncio.sleep(action.delay_after)
            
            return True
        except Exception as e:
            _LOGGER.error(f"Failed to end activity: {activity.name} - {e}")
            return False
    
    async def _execute_action(self, action: ActivityAction) -> bool:
        """Execute a single action."""
        action_type = action.action_type
        
        try:
            if action_type == ActionType.IR_COMMAND:
                return await self._execute_ir_command(action)
            
            elif action_type == ActionType.RF_COMMAND:
                return await self._execute_rf_command(action)
            
            elif action_type == ActionType.NETWORK_COMMAND:
                return await self._execute_network_command(action)
            
            elif action_type == ActionType.LAUNCH_APP:
                return await self._execute_launch_app(action)
            
            elif action_type == ActionType.TUNE_CHANNEL:
                return await self._execute_tune_channel(action)
            
            elif action_type == ActionType.SET_INPUT:
                return await self._execute_set_input(action)
            
            elif action_type == ActionType.SET_VOLUME:
                return await self._execute_set_volume(action)
            
            elif action_type == ActionType.POWER_ON:
                return await self._execute_power(action, on=True)
            
            elif action_type == ActionType.POWER_OFF:
                return await self._execute_power(action, on=False)
            
            elif action_type == ActionType.WAIT:
                await asyncio.sleep(action.delay_after)
                return True
            
            elif action_type == ActionType.KEYPRESS_SEQUENCE:
                return await self._execute_keypress_sequence(action)
            
            elif action_type == ActionType.TEXT_INPUT:
                return await self._execute_text_input(action)
            
            elif action_type == ActionType.HTTP_REQUEST:
                return await self._execute_http_request(action)
            
            elif action_type == ActionType.HA_SERVICE:
                return await self._execute_ha_service(action)
            
            elif action_type == ActionType.CONDITION:
                return await self._execute_condition(action)
            
            else:
                _LOGGER.warning(f"Unknown action type: {action_type}")
                return False
                
        except Exception as e:
            _LOGGER.error(f"Action execution failed: {e}")
            return False
    
    async def _execute_ir_command(self, action: ActivityAction) -> bool:
        """Execute an IR command."""
        device = self.database.devices.get(action.device_id)
        if not device:
            _LOGGER.error(f"Device not found: {action.device_id}")
            return False
        
        code = device.commands.get(action.command_name)
        if not code:
            _LOGGER.error(f"Command not found: {action.command_name}")
            return False
        
        for _ in range(action.repeat_count):
            success = await self.database.async_send_code(code)
            if not success:
                return False
            if action.repeat_count > 1:
                await asyncio.sleep(0.1)
        
        return True
    
    async def _execute_rf_command(self, action: ActivityAction) -> bool:
        """Execute an RF command."""
        # Similar to IR but for RF codes
        return await self._execute_ir_command(action)
    
    async def _execute_network_command(self, action: ActivityAction) -> bool:
        """Execute a network command."""
        device = self.database.devices.get(action.device_id)
        if not device:
            return False
        
        controller = await self._get_network_controller(device)
        if not controller:
            return False
        
        return await controller.send_command(action.command_name)
    
    async def _execute_launch_app(self, action: ActivityAction) -> bool:
        """Launch an app on Roku/FireTV."""
        device = self.database.devices.get(action.device_id)
        if not device:
            return False
        
        controller = await self._get_network_controller(device)
        if not controller:
            # Fall back to IR navigation
            return await self._launch_app_via_ir(action, device)
        
        if isinstance(controller, RokuController):
            if action.content_id:
                return await controller.launch_app_with_content(
                    action.app_id, 
                    action.content_id
                )
            return await controller.launch_app(action.app_id)
        
        elif isinstance(controller, FireTVController):
            return await controller.launch_app(action.app_id)
        
        return False
    
    async def _launch_app_via_ir(self, action: ActivityAction, device: Device) -> bool:
        """Launch app using IR commands (home + navigation)."""
        # Go home first
        home_code = device.commands.get("home")
        if home_code:
            await self.database.async_send_code(home_code)
            await asyncio.sleep(1.5)
        
        # Navigate to app based on position (would need to be configured)
        # This is a simplified example
        return True
    
    async def _execute_tune_channel(self, action: ActivityAction) -> bool:
        """Tune to a TV channel."""
        device = self.database.devices.get(action.device_id)
        if not device:
            return False
        
        # Try network control first (Roku TV)
        controller = await self._get_network_controller(device)
        if isinstance(controller, RokuController):
            return await controller.tune_channel(action.channel_number)
        
        # Fall back to IR digit entry
        return await self._tune_channel_via_ir(action, device)
    
    async def _tune_channel_via_ir(self, action: ActivityAction, device: Device) -> bool:
        """Tune channel using IR digit codes."""
        for digit in action.channel_number:
            code = device.commands.get(digit)
            if code:
                await self.database.async_send_code(code)
                await asyncio.sleep(0.2)
        
        # Send enter/ok if device has it
        enter_code = device.commands.get("enter") or device.commands.get("ok")
        if enter_code:
            await asyncio.sleep(0.3)
            await self.database.async_send_code(enter_code)
        
        return True
    
    async def _execute_set_input(self, action: ActivityAction) -> bool:
        """Set device input."""
        device = self.database.devices.get(action.device_id)
        if not device:
            return False
        
        # Look for input command
        input_commands = [
            f"input_{action.input_name}",
            f"hdmi{action.input_name}",
            action.input_name,
            f"source_{action.input_name}",
        ]
        
        for cmd_name in input_commands:
            code = device.commands.get(cmd_name)
            if code:
                success = await self.database.async_send_code(code)
                if success:
                    device.current_input = action.input_name
                    await self.database.async_save()
                return success
        
        _LOGGER.warning(f"No input command found for: {action.input_name}")
        return False
    
    async def _execute_set_volume(self, action: ActivityAction) -> bool:
        """Set volume level."""
        device = self.database.devices.get(action.device_id)
        if not device:
            return False
        
        # Try network control for exact volume
        controller = await self._get_network_controller(device)
        if isinstance(controller, OnkyoController):
            return await controller.set_volume(action.volume_level)
        
        # Fall back to IR volume steps
        if action.volume_relative:
            cmd_name = "volume_up" if action.volume_level > 0 else "volume_down"
            steps = abs(action.volume_level)
        else:
            # Can't do absolute volume with IR easily
            _LOGGER.warning("Absolute volume not supported for IR devices")
            return False
        
        code = device.commands.get(cmd_name)
        if code:
            for _ in range(steps):
                await self.database.async_send_code(code)
                await asyncio.sleep(0.1)
            return True
        
        return False
    
    async def _execute_power(self, action: ActivityAction, on: bool) -> bool:
        """Power device on or off."""
        device = self.database.devices.get(action.device_id)
        if not device:
            return False
        
        # Skip if already in desired state
        if device.power_state == on:
            return True
        
        # Find appropriate command
        if on:
            cmd_name = device.power_on_command or "power_on" or "power"
        else:
            cmd_name = device.power_off_command or "power_off" or "power"
        
        code = device.commands.get(cmd_name)
        if not code:
            code = device.commands.get("power")
        
        if code:
            success = await self.database.async_send_code(code)
            if success:
                device.power_state = on
                await self.database.async_save()
            return success
        
        return False
    
    async def _execute_keypress_sequence(self, action: ActivityAction) -> bool:
        """Execute a sequence of key presses."""
        device = self.database.devices.get(action.device_id)
        if not device:
            return False
        
        for key in action.key_sequence:
            code = device.commands.get(key)
            if code:
                await self.database.async_send_code(code)
                await asyncio.sleep(action.key_delay)
        
        return True
    
    async def _execute_text_input(self, action: ActivityAction) -> bool:
        """Input text on a device."""
        device = self.database.devices.get(action.device_id)
        if not device:
            return False
        
        controller = await self._get_network_controller(device)
        
        if isinstance(controller, RokuController):
            return await controller.input_text(action.text)
        elif isinstance(controller, FireTVController):
            return await controller.input_text(action.text)
        
        # Fall back to IR (if device has letter commands)
        _LOGGER.warning("Text input via IR not implemented")
        return False
    
    async def _execute_http_request(self, action: ActivityAction) -> bool:
        """Execute a custom HTTP request."""
        import aiohttp
        
        try:
            async with aiohttp.ClientSession() as session:
                if action.method.upper() == "GET":
                    async with session.get(action.url, timeout=10) as resp:
                        return resp.status < 400
                elif action.method.upper() == "POST":
                    async with session.post(action.url, timeout=10) as resp:
                        return resp.status < 400
        except Exception as e:
            _LOGGER.error(f"HTTP request failed: {e}")
            return False
        
        return False
    
    async def _execute_ha_service(self, action: ActivityAction) -> bool:
        """Call a Home Assistant service."""
        try:
            domain, service = action.service.split(".", 1)
            await self.hass.services.async_call(
                domain, 
                service, 
                action.service_data,
                blocking=True
            )
            return True
        except Exception as e:
            _LOGGER.error(f"HA service call failed: {e}")
            return False
    
    async def _execute_condition(self, action: ActivityAction) -> bool:
        """Evaluate a condition and execute appropriate actions."""
        state = self.hass.states.get(action.condition_entity)
        
        if state and state.state == action.condition_state:
            action_ids = action.condition_true_actions
        else:
            action_ids = action.condition_false_actions
        
        # Execute the conditional actions
        # Note: Would need to look up actions by ID
        return True
    
    async def _get_network_controller(self, device: Device) -> Any:
        """Get or create a network controller for a device."""
        if device.id in self._network_controllers:
            return self._network_controllers[device.id]
        
        # Determine controller type based on device category and brand
        # This would need network config stored on the device
        return None


# =============================================================================
# ACTIVITY TEMPLATES
# =============================================================================

def create_watch_roku_activity(
    name: str,
    tv_device_id: str,
    roku_device_id: str | None = None,
    receiver_device_id: str | None = None,
    app_id: str = "",
    app_name: str = "",
    tv_input: str = "hdmi1",
    receiver_input: str = "strm_box",
) -> Activity:
    """Create a 'Watch Roku' activity template."""
    actions = []
    
    # Power on TV
    actions.append(ActivityAction(
        action_type=ActionType.POWER_ON,
        device_id=tv_device_id,
        description="Power on TV",
        delay_after=3.0,
    ))
    
    # Power on receiver if specified
    if receiver_device_id:
        actions.append(ActivityAction(
            action_type=ActionType.POWER_ON,
            device_id=receiver_device_id,
            description="Power on receiver",
            delay_after=2.0,
        ))
        
        # Set receiver input
        actions.append(ActivityAction(
            action_type=ActionType.SET_INPUT,
            device_id=receiver_device_id,
            input_name=receiver_input,
            description=f"Set receiver to {receiver_input}",
            delay_after=1.0,
        ))
    
    # Set TV input
    actions.append(ActivityAction(
        action_type=ActionType.SET_INPUT,
        device_id=tv_device_id,
        input_name=tv_input,
        description=f"Set TV to {tv_input}",
        delay_after=2.0,
    ))
    
    # Launch app if specified
    if app_id:
        device_id = roku_device_id or tv_device_id
        actions.append(ActivityAction(
            action_type=ActionType.LAUNCH_APP,
            device_id=device_id,
            app_id=app_id,
            app_name=app_name,
            description=f"Launch {app_name or app_id}",
            delay_after=3.0,
        ))
    
    # End actions (power off)
    end_actions = [
        ActivityAction(
            action_type=ActionType.POWER_OFF,
            device_id=tv_device_id,
            description="Power off TV",
            delay_after=0.5,
        ),
    ]
    
    if receiver_device_id:
        end_actions.append(ActivityAction(
            action_type=ActionType.POWER_OFF,
            device_id=receiver_device_id,
            description="Power off receiver",
            delay_after=0.5,
        ))
    
    return Activity(
        name=name,
        icon="mdi:roku",
        actions=actions,
        end_actions=end_actions,
        category="Watch TV",
        device_power_states={
            tv_device_id: True,
            **({"receiver_device_id": True} if receiver_device_id else {}),
        },
        device_inputs={
            tv_device_id: tv_input,
            **({"receiver_device_id": receiver_input} if receiver_device_id else {}),
        },
    )


def create_watch_projector_activity(
    name: str,
    projector_device_id: str,
    screen_device_id: str | None = None,
    source_device_id: str | None = None,
    receiver_device_id: str | None = None,
    projector_input: str = "hdmi1",
    receiver_input: str = "game",
) -> Activity:
    """Create a 'Watch Projector' activity for home theater."""
    actions = []
    
    # Lower screen if motorized
    if screen_device_id:
        actions.append(ActivityAction(
            action_type=ActionType.NETWORK_COMMAND,
            device_id=screen_device_id,
            command_name="close",  # Lower screen
            description="Lower projector screen",
            delay_after=5.0,  # Wait for screen to lower
        ))
    
    # Power on projector
    actions.append(ActivityAction(
        action_type=ActionType.POWER_ON,
        device_id=projector_device_id,
        description="Power on projector",
        delay_after=30.0,  # Projectors take time to warm up
    ))
    
    # Set projector input
    actions.append(ActivityAction(
        action_type=ActionType.SET_INPUT,
        device_id=projector_device_id,
        input_name=projector_input,
        description=f"Set projector to {projector_input}",
        delay_after=2.0,
    ))
    
    # Power on receiver
    if receiver_device_id:
        actions.append(ActivityAction(
            action_type=ActionType.POWER_ON,
            device_id=receiver_device_id,
            description="Power on receiver",
            delay_after=2.0,
        ))
        
        actions.append(ActivityAction(
            action_type=ActionType.SET_INPUT,
            device_id=receiver_device_id,
            input_name=receiver_input,
            description=f"Set receiver to {receiver_input}",
            delay_after=1.0,
        ))
    
    # Power on source device
    if source_device_id:
        actions.append(ActivityAction(
            action_type=ActionType.POWER_ON,
            device_id=source_device_id,
            description="Power on source device",
            delay_after=2.0,
        ))
    
    # End actions
    end_actions = []
    
    # Raise screen
    if screen_device_id:
        end_actions.append(ActivityAction(
            action_type=ActionType.NETWORK_COMMAND,
            device_id=screen_device_id,
            command_name="open",  # Raise screen
            description="Raise projector screen",
            delay_after=1.0,
        ))
    
    # Power off devices
    if source_device_id:
        end_actions.append(ActivityAction(
            action_type=ActionType.POWER_OFF,
            device_id=source_device_id,
            description="Power off source",
            delay_after=0.5,
        ))
    
    if receiver_device_id:
        end_actions.append(ActivityAction(
            action_type=ActionType.POWER_OFF,
            device_id=receiver_device_id,
            description="Power off receiver",
            delay_after=0.5,
        ))
    
    end_actions.append(ActivityAction(
        action_type=ActionType.POWER_OFF,
        device_id=projector_device_id,
        description="Power off projector",
        delay_after=0.5,
    ))
    
    return Activity(
        name=name,
        icon="mdi:projector",
        actions=actions,
        end_actions=end_actions,
        category="Watch Projector",
        estimated_duration=40.0,
    )


def create_gaming_activity(
    name: str,
    console_device_id: str,
    tv_device_id: str,
    receiver_device_id: str | None = None,
    console_type: str = "xbox",  # "xbox" or "playstation"
    tv_input: str = "hdmi2",
    receiver_input: str = "game",
) -> Activity:
    """Create a gaming activity."""
    actions = []
    
    # Power on TV
    actions.append(ActivityAction(
        action_type=ActionType.POWER_ON,
        device_id=tv_device_id,
        description="Power on TV",
        delay_after=3.0,
    ))
    
    # Set TV to game mode (if available)
    actions.append(ActivityAction(
        action_type=ActionType.SET_INPUT,
        device_id=tv_device_id,
        input_name=tv_input,
        description=f"Set TV to {tv_input}",
        delay_after=1.0,
    ))
    
    # Power on receiver
    if receiver_device_id:
        actions.append(ActivityAction(
            action_type=ActionType.POWER_ON,
            device_id=receiver_device_id,
            description="Power on receiver",
            delay_after=2.0,
        ))
        
        actions.append(ActivityAction(
            action_type=ActionType.SET_INPUT,
            device_id=receiver_device_id,
            input_name=receiver_input,
            description=f"Set receiver to {receiver_input}",
            delay_after=1.0,
        ))
    
    # Power on console
    actions.append(ActivityAction(
        action_type=ActionType.POWER_ON,
        device_id=console_device_id,
        description=f"Power on {console_type}",
        delay_after=5.0,
    ))
    
    return Activity(
        name=name,
        icon="mdi:controller" if console_type == "xbox" else "mdi:sony-playstation",
        actions=actions,
        category="Gaming",
    )
