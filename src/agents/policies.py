from collections.abc import Callable, Mapping
from typing import Any, TypeVar

from src.guards.appointment_guard import require_action_allowed
from src.guards.output_guard import require_public_payload_safe
from src.models.enums import CallActionName

ResultT = TypeVar("ResultT")


def execute_core_action(
    state: Mapping[str, Any],
    action: CallActionName,
    operation: Callable[[], ResultT],
) -> ResultT:
    """Single execution gateway for all core scenario actions.

    Authorization is checked before the operation runs. Its result is checked
    again before it can leave the core, preventing prompt or tool behavior from
    bypassing the privacy boundary.
    """

    require_action_allowed(state, action)
    result = operation()
    require_public_payload_safe(state, result)
    return result
