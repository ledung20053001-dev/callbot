from fastapi.testclient import TestClient

from src.api.dependencies import get_session_repository
from src.config import get_settings
from src.main import app
from src.observability.redaction import REDACTED

client = TestClient(app)


def setup_function() -> None:
    get_session_repository().clear()
    get_settings.cache_clear()


def test_turn_records_conversation_without_auto_verifying_identity() -> None:
    started = client.post("/v1/calls", json={}).json()

    response = client.post(
        f"/v1/calls/{started['call_id']}/turn",
        json={"text": "Tôi là Nguyễn Văn A"},
    )

    assert response.status_code == 200
    assert response.json()["state"] == "AWAITING_IDENTITY"
    assert response.json()["verified_identity"] is False
    assert response.json()["reply"]


def test_debug_endpoint_is_disabled_by_default() -> None:
    started = client.post("/v1/calls", json={}).json()

    response = client.get(f"/v1/calls/{started['call_id']}/debug")

    assert response.status_code == 404


def test_debug_endpoint_redacts_sensitive_data(monkeypatch) -> None:
    monkeypatch.setenv("ENABLE_DEBUG_INTERFACE", "true")
    get_settings.cache_clear()
    started = client.post(
        "/v1/calls",
        json={"caller_number": "0900000000"},
    ).json()
    client.post(
        f"/v1/calls/{started['call_id']}/turn",
        json={"text": "Tôi là Nguyễn Văn A"},
    )

    response = client.get(f"/v1/calls/{started['call_id']}/debug")

    assert response.status_code == 200
    snapshot = response.json()["snapshot"]
    assert snapshot["caller_number"] == REDACTED
    assert snapshot["conversation_history"] == REDACTED
    assert snapshot["last_user_text"] == REDACTED
