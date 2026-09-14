# STT adapter interface specification

Status: Day-1 contract, version `1.0`  
Default language: `vi-VN`

## Scope

Business logic depends only on this adapter. Provider SDK objects, HTTP status
codes, and provider-specific confidence scales must not escape the adapter.
Version 1 handles one complete utterance per call; a future streaming contract
may add interim events without changing the final result schema.

## Input

Exactly one of `audio_url` and `audio_blob` is required (exclusive OR).

```json
{
  "audio_url": "https://storage.example.test/call/c001-turn-01.wav",
  "audio_blob": null,
  "content_type": "audio/wav",
  "language": "vi-VN",
  "sample_rate_hz": 16000,
  "channel_count": 1,
  "request_id": "req_01J..."
}
```

For an HTTP API, `audio_blob` is a binary multipart field, not base64 embedded in
JSON. Internal Python callers use `audio_bytes`.

### Validation and security

- `audio_url`: HTTPS only. Fetch server-side with an allow-list or signed-object
  policy; block loopback, link-local and private networks to prevent SSRF.
- Redirects count toward the same allow-list and timeout policy.
- Maximum payload: 10 MiB and 120 seconds for a single final utterance.
- Accepted baseline: WAV/PCM signed 16-bit, mono, 8 kHz or 16 kHz.
- Compressed formats may be enabled per adapter only after decoding limits are
  enforced. The adapter must not trust filename extensions.
- If declared rate/channels disagree with the decoded header, decoded properties
  win and the mismatch is logged.
- Audio and URLs are sensitive data: do not log blobs, signed query strings, or
  unredacted transcripts.

## Successful output

```json
{
  "text": "Tôi muốn đổi lịch",
  "is_final": true,
  "confidence": 0.94,
  "confidence_kind": "provider_utterance",
  "language": "vi-VN",
  "duration_ms": 2380,
  "latency_ms": 410,
  "provider": "example-stt",
  "provider_request_id": "upstream-123",
  "segments": [
    {
      "text": "Tôi muốn đổi lịch",
      "start_ms": 0,
      "end_ms": 2210,
      "confidence": 0.94,
      "words": [
        {"text": "đổi", "start_ms": 1020, "end_ms": 1280, "confidence": 0.71}
      ]
    }
  ]
}
```

`text` is the raw provider transcript. Normalized identity fields are produced by
a separate component and never overwrite this value.

### Confidence semantics

- `confidence` and every word/segment confidence are nullable.
- `null` means unavailable or not meaningfully comparable; it never means zero.
- `confidence_kind` identifies provenance, for example `provider_utterance`,
  `mean_word_confidence`, or `null`. Derived values must be labeled as derived.
- Thresholds are calibrated separately for each provider/model and test set.
  Never apply one provider's threshold to another provider.
- Name/DOB confirmation is required by business policy even at high confidence;
  confidence may trigger clarification but must not silently confirm identity.

## Stable errors

Adapters raise/return the following provider-independent codes:

| Code | Retryable | HTTP mapping | Meaning |
|---|---:|---:|---|
| `INVALID_REQUEST` | No | 400 | XOR or field validation failed |
| `UNSUPPORTED_AUDIO_FORMAT` | No | 415 | Container/codec/rate is unsupported |
| `AUDIO_TOO_LARGE` | No | 413 | Byte or duration limit exceeded |
| `AUDIO_FETCH_FAILED` | Sometimes | 422/502 | URL rejected, expired, or fetch failed |
| `NO_SPEECH_DETECTED` | No | 422 | No intelligible speech after decoding |
| `STT_TIMEOUT` | Yes | 504 | Adapter or provider deadline expired |
| `STT_RATE_LIMITED` | Yes | 429 | Upstream quota/rate limit reached |
| `STT_UPSTREAM_ERROR` | Yes | 502/503 | Provider unavailable or invalid response |

Error envelope:

```json
{
  "error": {
    "code": "STT_TIMEOUT",
    "message": "Speech recognition timed out.",
    "retryable": true,
    "request_id": "req_01J..."
  }
}
```

Provider response bodies and credentials are never returned to callers. Retryable
errors use bounded exponential backoff within the overall call deadline. Invalid
input and no-speech errors are not retried automatically.

## Python interface

The executable contract is in `src/services/stt_service.py`:

```python
class STTAdapter(Protocol):
    async def transcribe(self, request: STTRequest) -> STTResult:
        ...
```

## Compatibility rules

- Additive nullable fields are backward compatible.
- Renaming fields, changing confidence meaning, or changing error retryability
  requires a contract version bump.
- Provider/model version is pinned in deployment configuration and recorded in
  evaluation output.
