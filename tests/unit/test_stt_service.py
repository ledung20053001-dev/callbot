import pytest

from src.services.stt_service import STTRequest


def test_stt_request_accepts_exactly_one_audio_source() -> None:
    request = STTRequest(audio_bytes=b"RIFF", content_type="audio/wav")
    assert request.audio_bytes == b"RIFF"

    with pytest.raises(ValueError, match="exactly one"):
        STTRequest()
    with pytest.raises(ValueError, match="exactly one"):
        STTRequest(audio_url="https://example.test/a.wav", audio_bytes=b"RIFF")


def test_stt_request_requires_https_url() -> None:
    with pytest.raises(ValueError, match="HTTPS"):
        STTRequest(audio_url="http://example.test/a.wav")


@pytest.mark.parametrize("channels", [0, 3])
def test_stt_request_rejects_unsupported_channel_count(channels: int) -> None:
    with pytest.raises(ValueError, match="channel_count"):
        STTRequest(audio_bytes=b"RIFF", channel_count=channels)
