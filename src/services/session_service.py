from uuid import uuid4

from src.agents.state import CallState, create_initial_call_state
from src.guards.appointment_guard import require_action_allowed
from src.models.call import StartCallRequest
from src.models.enums import CallActionName
from src.repositories.session_repository import InMemorySessionRepository

IDENTITY_PROMPT = "Vui lòng cho biết họ tên đầy đủ và ngày sinh của anh/chị."


class SessionService:
    """Lifecycle operations for a conversation session."""

    def __init__(self, repository: InMemorySessionRepository) -> None:
        self._repository = repository

    def start_call(self, request: StartCallRequest) -> CallState:
        call_id = str(uuid4())
        state = create_initial_call_state(call_id)
        state["direction"] = request.direction
        state["caller_number"] = request.caller_number
        state["turn"] = 0
        state["conversation_history"] = [
            {"role": "assistant", "text": IDENTITY_PROMPT}
        ]
        state["last_bot_text"] = IDENTITY_PROMPT
        return self._repository.create(state)

    def process_turn(self, call_id: str, text: str) -> CallState:
        state = self._repository.get(call_id)
        require_action_allowed(state, CallActionName.COLLECT_IDENTITY)
        history = list(state.get("conversation_history", []))
        history.extend(
            [
                {"role": "user", "text": text},
                {"role": "assistant", "text": IDENTITY_PROMPT},
            ]
        )
        state["last_user_text"] = text
        state["last_bot_text"] = IDENTITY_PROMPT
        state["conversation_history"] = history
        state["turn"] = state.get("turn", 0) + 1
        return self._repository.save(state)

    def get_call(self, call_id: str) -> CallState:
        return self._repository.get(call_id)

    def authorize_action(self, call_id: str, action: CallActionName) -> CallState:
        """Authorize a scenario action before any tool or service executes it."""

        state = self._repository.get(call_id)
        require_action_allowed(state, action)
        return state
