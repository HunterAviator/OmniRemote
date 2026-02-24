"""Constants for OmniRemote integration."""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

DOMAIN = "omniremote"
VERSION = "1.2.3"
STORAGE_VERSION = 1
STORAGE_KEY = f"{DOMAIN}.storage"

# Service names
SERVICE_IMPORT_FLIPPER = "import_flipper"
SERVICE_EXPORT_FLIPPER = "export_flipper"
SERVICE_LEARN_CODE = "learn_code"
SERVICE_SEND_CODE = "send_code"
SERVICE_RUN_SCENE = "run_scene"
SERVICE_CREATE_SCENE = "create_scene"
SERVICE_ADD_ROOM = "add_room"
SERVICE_ADD_DEVICE = "add_device"