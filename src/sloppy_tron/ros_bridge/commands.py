"""JSON command envelope used between the SLOP adapter and ROS nodes."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from time import time

from sloppy_tron.provider.contract import JsonObject


@dataclass(frozen=True, slots=True)
class BridgeCommand:
    """Semantic command emitted by the SLOP adapter into the ROS graph."""

    action: str
    params: JsonObject
    task_id: str
    created_at: float = field(default_factory=time)

    def to_dict(self) -> JsonObject:
        return {
            "action": self.action,
            "params": self.params,
            "taskId": self.task_id,
            "createdAt": self.created_at,
        }


def command_to_json(command: BridgeCommand) -> str:
    return json.dumps(command.to_dict(), sort_keys=True)


def command_from_json(payload: str) -> BridgeCommand:
    data = json.loads(payload)
    if not isinstance(data, dict):
        raise ValueError("bridge command must be a JSON object")

    action = data.get("action")
    params = data.get("params", {})
    task_id = data.get("taskId")
    created_at = data.get("createdAt", time())

    if not isinstance(action, str) or not action:
        raise ValueError("bridge command action must be a non-empty string")
    if not isinstance(params, dict):
        raise ValueError("bridge command params must be an object")
    if not isinstance(task_id, str) or not task_id:
        raise ValueError("bridge command taskId must be a non-empty string")
    if not isinstance(created_at, int | float):
        raise ValueError("bridge command createdAt must be numeric")

    return BridgeCommand(
        action=action,
        params=params,
        task_id=task_id,
        created_at=float(created_at),
    )
