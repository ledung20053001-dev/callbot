from pathlib import Path

from fastapi.testclient import TestClient

from src.main import app

client = TestClient(app)
UI_DIRECTORY = Path(__file__).parents[2] / "src" / "ui"


def test_internal_ui_is_served() -> None:
    response = client.get("/internal/")

    assert response.status_code == 200
    assert response.encoding == "utf-8"
    assert "Conversation transcript" in response.text
    assert "verified-value" in response.text
    assert "transcript" in response.text
    assert response.text.index("conversation-column") < response.text.index("state-column")
    assert response.headers["cache-control"].startswith("no-store")
    assert "LOADING UI · V6" in response.text
    assert 'id="start-button" class="plain-button" type="submit" disabled' in response.text


def test_internal_ui_ignores_stale_browser_etag() -> None:
    first_response = client.get("/internal/")
    stale_etag = first_response.headers.get("etag", '"stale-ui"')

    response = client.get("/internal/", headers={"If-None-Match": stale_etag})

    assert response.status_code == 200
    assert "Conversation transcript" in response.text


def test_forms_never_fall_back_to_query_string_submission() -> None:
    html = (UI_DIRECTORY / "index.html").read_text(encoding="utf-8")

    assert html.count('onsubmit="return false;"') == 2
    assert 'method="get"' not in html.lower()


def test_ui_calls_only_public_bot_conversation_endpoints() -> None:
    script = (UI_DIRECTORY / "app.js").read_text(encoding="utf-8")

    assert 'callBotApi("/v1/calls"' in script
    assert "/v1/calls/${encodeURIComponent(session.callId)}/turn" in script
    assert "/debug" not in script
    assert "clinic-mock" not in script.lower()
    assert "/appointments" not in script


def test_transcript_normalizes_unicode_and_punctuation_before_rendering() -> None:
    script = (UI_DIRECTORY / "app.js").read_text(encoding="utf-8")

    assert "normalizeTranscriptText(text)" in script
    assert "content.textContent = normalizedText" in script

    utility = (UI_DIRECTORY / "text-utils.js").read_text(encoding="utf-8")
    assert '.normalize("NFC")' in utility
    assert "\\\\+([,.;:!?…])" in utility


def test_ui_uses_classic_scripts_for_broad_browser_compatibility() -> None:
    html = (UI_DIRECTORY / "index.html").read_text(encoding="utf-8")

    assert 'type="module"' not in html
    assert "text-utils.mjs" not in html
    assert html.index("text-utils.js?v=6") < html.index("app.js?v=6")


def test_start_call_returns_initial_bot_reply() -> None:
    response = client.post("/v1/calls", json={})

    assert response.status_code == 201
    assert response.json()["reply"]
    assert response.json()["verified_identity"] is False
