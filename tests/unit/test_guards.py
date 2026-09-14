import pytest

from src.core.exceptions import PrivacyViolationError
from src.guards.identity_guard import (
    is_identity_verified,
    protect_appointment_data,
    require_verified_identity,
)
from src.guards.output_guard import require_public_payload_safe


def test_caller_number_is_not_identity_proof() -> None:
    state = {"caller_number": "0900000000", "verified_identity": False}

    assert is_identity_verified(state) is False
    with pytest.raises(PrivacyViolationError):
        require_verified_identity(state)


def test_appointment_data_is_hidden_before_verification() -> None:
    state = {"verified_identity": False}
    payload = {
        "call_id": "call-1",
        "appointment_id": "appointment-1",
        "appointment": {"date": "2026-09-15"},
    }

    assert protect_appointment_data(state, payload) == {"call_id": "call-1"}


def test_appointment_data_is_available_after_verification() -> None:
    state = {"verified_identity": True}
    payload = {"appointment_id": "appointment-1"}

    assert protect_appointment_data(state, payload) == payload


def test_structured_appointment_output_is_blocked_recursively() -> None:
    payload = {"result": [{"data": {"appointment_time": "09:00"}}]}

    with pytest.raises(PrivacyViolationError):
        require_public_payload_safe({"verified_identity": False}, payload)


def test_redacted_appointment_output_is_safe() -> None:
    require_public_payload_safe(
        {"verified_identity": False},
        {"appointment_id": "[REDACTED]"},
    )
