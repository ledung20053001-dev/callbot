from collections.abc import Mapping
from typing import Any

from src.core.exceptions import PrivacyViolationError
from src.guards.identity_guard import is_identity_verified
from src.models.enums import CallActionName

PROTECTED_APPOINTMENT_ACTIONS = frozenset(
    {
        CallActionName.READ_APPOINTMENT,
        CallActionName.DISCLOSE_APPOINTMENT,
        CallActionName.CONFIRM_APPOINTMENT,
        CallActionName.CANCEL_APPOINTMENT,
        CallActionName.GET_SLOTS,
        CallActionName.OFFER_SLOTS,
        CallActionName.RESCHEDULE_APPOINTMENT,
        CallActionName.BOOK_APPOINTMENT,
    }
)


def require_action_allowed(
    state: Mapping[str, Any], action: CallActionName
) -> None:
    """Enforce the pre-verification action boundary in deterministic code."""

    if action in PROTECTED_APPOINTMENT_ACTIONS and not is_identity_verified(state):
        raise PrivacyViolationError(
            f"Action '{action.value}' requires verified identity."
        )
