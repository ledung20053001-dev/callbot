"""Provider-neutral speech-to-text contract.

Business services depend on :class:`STTAdapter`, not on a provider SDK.  The
wire-level contract and error semantics are documented in
``speech/docs/stt_adapter_spec.md``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Protocol, runtime_checkable


class STTErrorCode(StrEnum):
    INVALID_REQUEST = "INVALID_REQUEST"
    UNSUPPORTED_AUDIO_FORMAT = "UNSUPPORTED_AUDIO_FORMAT"
    AUDIO_FETCH_FAILED = "AUDIO_FETCH_FAILED"
    AUDIO_TOO_LARGE = "AUDIO_TOO_LARGE"
    NO_SPEECH_DETECTED = "NO_SPEECH_DETECTED"
    STT_TIMEOUT = "STT_TIMEOUT"
    STT_RATE_LIMITED = "STT_RATE_LIMITED"
    STT_UPSTREAM_ERROR = "STT_UPSTREAM_ERROR"


class STTError(Exception):
    """Stable adapter exception; provider details belong in logs, not callers."""

    def __init__(
        self,
        code: STTErrorCode,
        message: str,
        *,
        retryable: bool,
        provider: str | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.retryable = retryable
        self.provider = provider


@dataclass(frozen=True, slots=True)
class STTRequest:
    """Exactly one audio source must be supplied."""

    audio_url: str | None = None
    audio_bytes: bytes | None = None
    content_type: str | None = None
    language: str = "vi-VN"
    sample_rate_hz: int | None = None
    channel_count: int | None = None
    request_id: str | None = None

    def __post_init__(self) -> None:
        if (self.audio_url is None) == (self.audio_bytes is None):
            raise ValueError("exactly one of audio_url or audio_bytes is required")
        if self.audio_url is not None and not self.audio_url.startswith("https://"):
            raise ValueError("audio_url must use HTTPS")
        if self.audio_bytes is not None and not self.audio_bytes:
            raise ValueError("audio_bytes must not be empty")
        if self.sample_rate_hz is not None and self.sample_rate_hz <= 0:
            raise ValueError("sample_rate_hz must be positive")
        if self.channel_count is not None and self.channel_count not in (1, 2):
            raise ValueError("channel_count must be 1 or 2")


@dataclass(frozen=True, slots=True)
class STTWord:
    text: str
    start_ms: int | None = None
    end_ms: int | None = None
    confidence: float | None = None


@dataclass(frozen=True, slots=True)
class STTSegment:
    text: str
    start_ms: int
    end_ms: int
    confidence: float | None = None
    words: tuple[STTWord, ...] = ()


@dataclass(frozen=True, slots=True)
class STTResult:
    """Raw provider transcript. Identity normalization is a separate step."""

    text: str
    is_final: bool
    language: str
    latency_ms: int
    provider: str
    confidence: float | None = None
    confidence_kind: str | None = None
    duration_ms: int | None = None
    segments: tuple[STTSegment, ...] = field(default_factory=tuple)
    provider_request_id: str | None = None


@runtime_checkable
class STTAdapter(Protocol):
    async def transcribe(self, request: STTRequest) -> STTResult:
        """Transcribe one final utterance or raise :class:`STTError`."""
        ...
