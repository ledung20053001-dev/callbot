from typing import Literal

from pydantic import BaseModel, ConfigDict

from src.models.enums import CallStateName


class ApiModel(BaseModel):
    """Cấu hình chung cho các schema API của Callbot."""

    model_config = ConfigDict(extra="forbid")


class StartCallRequest(ApiModel):
    """Dữ liệu khởi tạo cuộc gọi.

    ``caller_number`` chỉ là metadata và không phải bằng chứng xác minh danh tính.
    """

    caller_number: str | None = None
    direction: Literal["inbound", "outbound"] = "inbound"


class StartCallResponse(ApiModel):
    call_id: str
    state: CallStateName
    verified_identity: bool
    reply: str | None = None


class TurnRequest(ApiModel):
    text: str


class TurnResponse(ApiModel):
    call_id: str
    state: CallStateName
    verified_identity: bool
    reply: str | None = None


class DebugCallResponse(ApiModel):
    """Privacy-safe snapshot intended only for local troubleshooting."""

    call_id: str
    state: CallStateName
    verified_identity: bool
    turn: int
    snapshot: dict[str, object]
