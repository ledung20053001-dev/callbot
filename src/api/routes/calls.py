from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from src.api.dependencies import get_session_service
from src.config import Settings, get_settings
from src.models.call import (
    DebugCallResponse,
    StartCallRequest,
    StartCallResponse,
    TurnRequest,
    TurnResponse,
)
from src.observability.redaction import redact_sensitive_data
from src.services.session_service import SessionService

router = APIRouter(prefix="/v1/calls", tags=["calls"])
SessionServiceDependency = Annotated[SessionService, Depends(get_session_service)]
SettingsDependency = Annotated[Settings, Depends(get_settings)]


@router.post("", response_model=StartCallResponse, status_code=status.HTTP_201_CREATED)
def start_call(
    request: StartCallRequest,
    service: SessionServiceDependency,
) -> StartCallResponse:
    state = service.start_call(request)
    return StartCallResponse(
        call_id=state["call_id"],
        state=state["state"],
        verified_identity=state["verified_identity"],
        reply=state.get("last_bot_text"),
    )


@router.post("/{call_id}/turn", response_model=TurnResponse)
def process_turn(
    call_id: str,
    request: TurnRequest,
    service: SessionServiceDependency,
) -> TurnResponse:
    state = service.process_turn(call_id, request.text)
    return TurnResponse(
        call_id=state["call_id"],
        state=state["state"],
        verified_identity=state["verified_identity"],
        reply=state.get("last_bot_text"),
    )


@router.get("/{call_id}/debug", response_model=DebugCallResponse, tags=["debug"])
def debug_call(
    call_id: str,
    service: SessionServiceDependency,
    settings: SettingsDependency,
) -> DebugCallResponse:
    if not settings.enable_debug_interface:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")

    state = service.get_call(call_id)
    safe_snapshot = redact_sensitive_data(state)
    return DebugCallResponse(
        call_id=state["call_id"],
        state=state["state"],
        verified_identity=state["verified_identity"],
        turn=state.get("turn", 0),
        snapshot=safe_snapshot,
    )
