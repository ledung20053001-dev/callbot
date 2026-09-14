from typing import Literal, TypedDict

from src.models.enums import CallStateName


class CallState(TypedDict, total=False):
    """Trạng thái dùng chung xuyên suốt một phiên hội thoại callbot."""

    # Thông tin phiên gọi
    call_id: str
    direction: Literal["inbound", "outbound"]
    appointment_id: str | None
    caller_number: str | None
    locale: str
    mode: Literal["text", "audio"]
    turn: int
    max_turns: int

    # Hội thoại
    last_user_text: str | None
    last_bot_text: str | None
    user_text: str | None
    bot_utterance: str
    conversation_history: list[dict[str, object]]
    intent: str | None
    failed_understanding_count: int
    silence_count: int

    # Xác minh danh tính
    full_name: str | None
    dob: str | None
    verified_identity: bool
    provided_name: str | None
    provided_dob: str | None
    identity_verified: bool
    patient_id: str | None

    # Dữ liệu lịch hẹn
    appointment: dict[str, object] | None
    appointment_version: int | None
    offered_slot_ids: list[str]
    selected_slot_id: str | None

    # Xác nhận hành động
    attendance_confirmed: bool
    cancel_confirmation_count: int
    booking_confirmed: bool
    reschedule_confirmed: bool

    # Kết quả
    state: CallStateName
    ended: bool
    outcome: Literal[
        "CONFIRMED",
        "CANCELLED",
        "RESCHEDULED",
        "TRANSFERRED",
        "UNREACHABLE",
        "BOOKED",
        "SCHEDULED",
    ] | None

    cancel_reason: str | None
    transfer_reason: str | None
    error: str | None


def create_initial_call_state(call_id: str) -> CallState:
    """Tạo state tối thiểu cho một cuộc gọi mới theo yêu cầu Day 1."""

    return CallState(
        call_id=call_id,
        state=CallStateName.AWAITING_IDENTITY,
        full_name=None,
        dob=None,
        verified_identity=False,
        patient_id=None,
        last_user_text=None,
        last_bot_text=None,
    )
