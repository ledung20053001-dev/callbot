from collections.abc import Mapping, Sequence
from typing import Any

from src.core.exceptions import PrivacyViolationError
from src.guards.identity_guard import is_identity_verified
from src.observability.redaction import REDACTED

APPOINTMENT_DETAIL_KEYS = frozenset(
    {
        "appointment",
        "appointment_id",
        "appointment_version",
        "appointment_status",
        "clinic",
        "clinic_id",
        "clinic_name",
        "scheduled_at",
        "appointment_date",
        "appointment_time",
        "confirmed_at",
        "slot",
        "slot_id",
        "slot_ids",
        "offered_slot_ids",
        "selected_slot_id",
        "new_slot_id",
    }
)


def _contains_unredacted_appointment_detail(value: Any) -> bool:
    if isinstance(value, Mapping):
        for key, item in value.items():
            normalized_key = str(key).lower()
            if normalized_key in APPOINTMENT_DETAIL_KEYS and item not in (
                None,
                "",
                REDACTED,
            ):
                return True
            if _contains_unredacted_appointment_detail(item):
                return True
        return False
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return any(_contains_unredacted_appointment_detail(item) for item in value)
    return False


def require_public_payload_safe(state: Mapping[str, Any], payload: Any) -> None:
    """Block appointment-specific structured output before verification."""

    if not is_identity_verified(state) and _contains_unredacted_appointment_detail(
        payload
    ):
        raise PrivacyViolationError(
            "Appointment details cannot be returned before identity verification."
        )
