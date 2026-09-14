from typing import Literal, TypedDict


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
    user_text: str | None
    bot_utterance: str
    conversation_history: list[dict]
    intent: str | None
    failed_understanding_count: int
    silence_count: int

    # Xác minh danh tính
    provided_name: str | None
    provided_dob: str | None
    identity_verified: bool
    patient_id: str | None

    # Dữ liệu lịch hẹn
    appointment: dict | None
    appointment_version: int | None
    offered_slot_ids: list[str]
    selected_slot_id: str | None

    # Xác nhận hành động
    attendance_confirmed: bool
    cancel_confirmation_count: int
    booking_confirmed: bool
    reschedule_confirmed: bool

    # Kết quả
    state: Literal[
        "AWAITING_IDENTITY",
        "AWAITING_INTENT",
        "AWAITING_CONFIRMATION",
        "OFFERING_SLOTS",
        "CLOSING",
        "ENDED",
    ]
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
