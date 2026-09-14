# Vietnamese STT candidate shortlist

Reviewed: 2026-09-14. Pricing and feature availability are snapshots; verify
again before procurement.

## Shortlist

| Criterion | PhoWhisper small/medium | Deepgram Nova-3 | Google Cloud Chirp 3 |
|---|---|---|---|
| Delivery | Self-hosted, open model | Hosted API; streaming and batch | Hosted STT V2; streaming, sync, batch |
| Vietnamese | Vietnamese-specific fine-tune on 844 hours and multiple accents | `vi` is listed for Nova-3 | `vi-VN` is GA for Chirp 3 |
| Streaming | Not native; chunking/VAD must be engineered and measured | Native interim/final streaming | Native `StreamingRecognize` |
| Phone audio | Requires 16 kHz input per model example; explicitly benchmark resampled 8 kHz | API accepts configured encoding/rate; noisy/far-field positioning is promising but 8 kHz Vietnamese remains a test item | Supports several audio models, but Vietnamese-specific phone-model availability must be checked; benchmark Chirp 3 on 8 kHz |
| Confidence | Pipeline-dependent; Whisper scores are not calibrated identity confidence | Provider result metadata; validate availability/meaning for selected endpoint | Feature support varies by locale/model; do not assume word confidence for every configuration |
| Latency | Hardware/model dependent; medium/large may be too slow without GPU optimization | Low integration effort and real-time streaming | Moderate integration effort; network and region affect latency |
| Cost | No per-minute fee; GPU/ops cost | Nova-3 PAYG: $0.0048/min monolingual streaming, $0.0043/min prerecorded at review time | STT V2 standard recognition: about $0.016/min at review time; billing rules vary by mode/channel |
| Data control | Highest; team operates storage and inference | Audio leaves system under provider terms | Audio leaves system under Google Cloud terms/region configuration |
| Main risk | Production streaming, capacity planning, operational burden | Vietnamese identity accuracy is not established by vendor feature lists | Higher list price; phone-tuned model support for Vietnamese is not guaranteed |

## Evidence and caveats

- PhoWhisper publishes five model sizes (39M–1.55B parameters), Vietnamese WER
  results, and a 16 kHz Transformers example. The repository/paper does not prove
  latency or accuracy for this project's 8 kHz clinic calls.
- Deepgram lists Vietnamese `vi` for Nova-3 and documents streaming features such
  as interim results, endpointing, sample-rate and encoding controls. Marketing
  claims about noisy/far-field audio are hypotheses until measured here.
- Google documents Vietnamese `vi-VN` as GA for Chirp 3 and supports streaming,
  synchronous, and batch methods. Model/locale feature matrices must be checked
  for confidence and adaptation before an adapter promises them.

Primary sources:

- [PhoWhisper repository and published benchmark](https://github.com/VinAIResearch/PhoWhisper)
- [PhoWhisper ICLR 2024 paper](https://arxiv.org/abs/2406.02555)
- [Deepgram models and languages](https://developers.deepgram.com/docs/models-languages-overview)
- [Deepgram streaming feature overview](https://developers.deepgram.com/docs/stt-streaming-feature-overview)
- [Deepgram pricing](https://deepgram.com/pricing)
- [Google Chirp 3 documentation](https://cloud.google.com/speech-to-text/v2/docs/chirp-model)
- [Google STT V2 language matrix](https://cloud.google.com/speech-to-text/v2/docs/speech-to-text-supported-languages)
- [Google Speech-to-Text pricing](https://cloud.google.com/speech-to-text/pricing)

## Recommendation

Implement Deepgram Nova-3 first for the Day-2 streaming baseline because it has
the shortest path to real-time telephony integration and explicitly lists
Vietnamese. Implement PhoWhisper small second as the self-hosted/privacy and cost
baseline. Keep Google Chirp 3 as the third benchmark candidate, particularly if
Google Cloud is already approved infrastructure.

This is an implementation order, not a production winner. Production selection
is blocked until all candidates run on the same fixture manifest and on a later
consented, representative 8 kHz telephone set.

## Scoring rubric

Hard gates (failure excludes a candidate regardless of total score):

1. Zero silent identity mutation in the adapter/normalizer boundary.
2. Name exact-match accuracy at least 95% on the expanded identity set.
3. DOB semantic exact-match accuracy at least 98%, with ambiguous years rejected.
4. p95 final-transcript latency at most 1,500 ms for a typical call turn.
5. Meets the project's privacy, retention, residency, and license review.

Weighted score after gates:

| Metric | Weight | Measurement |
|---|---:|---|
| Vietnamese transcript accuracy | 25% | WER and CER on all fixtures |
| Identity-critical accuracy | 25% | Exact full-name and semantic DOB accuracy |
| 8 kHz/noise robustness | 15% | Score delta from clean 16 kHz to phone fixtures |
| Latency | 15% | p50/p95 time to first partial and final transcript |
| Integration/operations | 10% | Adapter effort, streaming, observability, failure handling |
| Total cost | 10% | Provider minutes or measured infra cost at expected volume |

## Day-2 benchmark protocol

- Pin provider, model version, region, SDK version, and parameters.
- Run every row in `samples/metadata.jsonl`; do not hand-pick successes.
- Record raw transcript, confidence metadata, first-partial latency, final latency,
  errors, and retries. Never overwrite the expected transcript.
- Report WER/CER plus exact name match and semantic DOB match. A low global WER
  cannot compensate for `An ↔ Anh` or `1978 ↔ 1988`.
- Repeat each streaming sample at least five times to expose latency variance.
- Hash inputs and store benchmark outputs separately from this immutable fixture set.
