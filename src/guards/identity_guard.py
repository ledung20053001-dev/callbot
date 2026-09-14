from collections.abc import Mapping
from typing import Any

from src.core.exceptions import PrivacyViolationError

PROTECTED_STATE_FIELDS = frozenset(
    {
        "appointment",
        "appointment_id",
        "appointment_version",
        "offered_slot_ids",
        "selected_slot_id",
    }
)


def is_identity_verified(state: Mapping[str, Any]) -> bool:
    """Return only the explicit identity result; phone metadata is ignored."""

    return state.get("verified_identity") is True


def require_verified_identity(state: Mapping[str, Any]) -> None:
    """Block access to appointment data until name and DOB are verified."""

    if not is_identity_verified(state):
        raise PrivacyViolationError(
            "Appointment information cannot be disclosed before identity verification."
        )


def protect_appointment_data(
    state: Mapping[str, Any], payload: Mapping[str, Any]
) -> dict[str, Any]:
    """Remove protected appointment fields unless identity is verified."""

    if is_identity_verified(state):
        return dict(payload)
    return {key: value for key, value in payload.items() if key not in PROTECTED_STATE_FIELDS}
