from fastapi.testclient import TestClient

from src.api.dependencies import get_session_repository
from src.main import app

client = TestClient(app)


def setup_function() -> None:
    get_session_repository().clear()


def test_start_call_awaits_identity_even_when_phone_is_provided() -> None:
    response = client.post(
        "/v1/calls",
        json={"direction": "inbound", "caller_number": "0900000000"},
    )

    assert response.status_code == 201
    assert response.json()["state"] == "AWAITING_IDENTITY"
    assert response.json()["verified_identity"] is False
