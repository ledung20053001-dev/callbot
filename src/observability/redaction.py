from collections.abc import Mapping, Sequence
from typing import Any

REDACTED = "[REDACTED]"
SENSITIVE_KEYS = frozenset(
    {
        "caller_number",
        "full_name",
        "dob",
        "provided_name",
        "provided_dob",
        "patient_id",
        "appointment_id",
        "appointment",
        "appointment_version",
        "offered_slot_ids",
        "selected_slot_id",
        "new_slot_id",
        "user_text",
        "bot_utterance",
        "last_user_text",
        "last_bot_text",
        "conversation_history",
    }
)


def redact_sensitive_data(value: Any) -> Any:
    """Recursively redact patient data before logging or debug output."""

    if isinstance(value, Mapping):
        return {
            str(key): (
                REDACTED if str(key).lower() in SENSITIVE_KEYS else redact_sensitive_data(item)
            )
            for key, item in value.items()
        }
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return [redact_sensitive_data(item) for item in value]
    return value
