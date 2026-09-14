from copy import deepcopy
from threading import RLock

from src.agents.state import CallState
from src.core.exceptions import CallAlreadyExistsError, CallNotFoundError


class InMemorySessionRepository:
    """Thread-safe process-local session store for development and tests."""

    def __init__(self) -> None:
        self._sessions: dict[str, CallState] = {}
        self._lock = RLock()

    def create(self, state: CallState) -> CallState:
        call_id = state["call_id"]
        with self._lock:
            if call_id in self._sessions:
                raise CallAlreadyExistsError(f"Call '{call_id}' already exists.")
            self._sessions[call_id] = deepcopy(state)
            return deepcopy(state)

    def get(self, call_id: str) -> CallState:
        with self._lock:
            try:
                return deepcopy(self._sessions[call_id])
            except KeyError as exc:
                raise CallNotFoundError(f"Call '{call_id}' was not found.") from exc

    def save(self, state: CallState) -> CallState:
        call_id = state["call_id"]
        with self._lock:
            if call_id not in self._sessions:
                raise CallNotFoundError(f"Call '{call_id}' was not found.")
            self._sessions[call_id] = deepcopy(state)
            return deepcopy(state)

    def clear(self) -> None:
        with self._lock:
            self._sessions.clear()
