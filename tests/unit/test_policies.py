import pytest

from src.agents.policies import execute_core_action
from src.core.exceptions import PrivacyViolationError
from src.models.enums import CallActionName


@pytest.mark.parametrize(
    "action",
    [
        CallActionName.READ_APPOINTMENT,
        CallActionName.DISCLOSE_APPOINTMENT,
        CallActionName.CONFIRM_APPOINTMENT,
        CallActionName.CANCEL_APPOINTMENT,
        CallActionName.GET_SLOTS,
        CallActionName.OFFER_SLOTS,
        CallActionName.RESCHEDULE_APPOINTMENT,
        CallActionName.BOOK_APPOINTMENT,
    ],
)
def test_all_appointment_actions_are_blocked_before_verification(
    action: CallActionName,
) -> None:
    operation_called = False

    def operation() -> dict[str, str]:
        nonlocal operation_called
        operation_called = True
        return {"status": "should-not-run"}

    with pytest.raises(PrivacyViolationError):
        execute_core_action(
            {"verified_identity": False},
            action,
            operation,
        )

    assert operation_called is False


@pytest.mark.parametrize(
    "state",
    [
        {"caller_number": "0900000000"},
        {"caller_number": "0900000000", "verified_identity": False},
        {"identity_verified": True},
        {"verified_identity": 1},
    ],
)
def test_metadata_and_legacy_flags_cannot_bypass_guard(state: dict[str, object]) -> None:
    with pytest.raises(PrivacyViolationError):
        execute_core_action(
            state,
            CallActionName.READ_APPOINTMENT,
            lambda: {"appointment_id": "appointment-1"},
        )


def test_non_appointment_safety_action_is_allowed_before_verification() -> None:
    result = execute_core_action(
        {"verified_identity": False},
        CallActionName.TRANSFER_TO_STAFF,
        lambda: {"outcome": "TRANSFERRED"},
    )

    assert result == {"outcome": "TRANSFERRED"}


def test_verified_identity_allows_appointment_action() -> None:
    result = execute_core_action(
        {"verified_identity": True},
        CallActionName.READ_APPOINTMENT,
        lambda: {"appointment_id": "appointment-1"},
    )

    assert result == {"appointment_id": "appointment-1"}


def test_output_guard_blocks_nested_appointment_detail() -> None:
    with pytest.raises(PrivacyViolationError):
        execute_core_action(
            {"verified_identity": False},
            CallActionName.COLLECT_IDENTITY,
            lambda: {"data": {"result": {"clinic_name": "Clinic A"}}},
        )
