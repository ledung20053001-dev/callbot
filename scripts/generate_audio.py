"""Generate the Day-1 synthetic Vietnamese STT fixture set.

Metadata generation is offline and deterministic. Audio generation uses Edge
TTS only as a convenient synthetic voice source; no patient data is sent. WAV
post-processing uses a bundled FFmpeg executable and the Python standard
library.

Install optional tooling locally:
    python -m pip install edge-tts imageio-ffmpeg

Usage:
    python scripts/generate_audio.py --metadata-only
    python scripts/generate_audio.py --generate-audio
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import random
import sys
import tempfile
import wave
from array import array
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SAMPLE_ROOT = ROOT / "speech" / "samples"
DEFAULT_VOICE = "vi-VN-HoaiMyNeural"
SECOND_VOICE = "vi-VN-NamMinhNeural"


def sample(
    audio_id: str,
    category: str,
    text: str,
    *,
    voice: str = DEFAULT_VOICE,
    speed: str = "normal",
    rate: str = "+0%",
    noise: str = "clean",
    sample_rate_hz: int = 16_000,
    notes: str | None = None,
) -> dict[str, Any]:
    filename = f"{audio_id}_{noise}_{speed}.wav"
    return {
        "audio_id": audio_id,
        "category": category,
        "audio_path": f"{category}/{filename}",
        "expected_transcript": text,
        "speaker_style": "tts_synthetic",
        "voice": voice,
        "speed": speed,
        "tts_rate": rate,
        "noise": noise,
        "sample_rate_hz": sample_rate_hz,
        "channel_count": 1,
        "encoding": "pcm_s16le",
        "synthetic": True,
        "contains_real_patient_data": False,
        "notes": notes,
    }


SAMPLES = [
    sample("name_001", "names", "Nguyễn Minh An"),
    sample("name_002", "names", "Trần Gia Huy", voice=SECOND_VOICE),
    sample("name_003", "names", "Lê Thu Hà"),
    sample("name_004", "names", "Phạm Quốc Minh", voice=SECOND_VOICE),
    sample("name_005", "names", "Võ Ngọc Mai"),
    sample("name_006", "names", "Bùi Thanh Long", voice=SECOND_VOICE),
    sample("name_007", "names", "Đặng Hải Yến"),
    sample(
        "name_008",
        "names",
        "Nguyễn Văn Anh",
        voice=SECOND_VOICE,
        notes="identity-critical contrast: An/Anh",
    ),
    sample("dob_001", "dob", "Ngày mười bốn tháng ba năm một nghìn chín trăm bảy mươi tám"),
    sample(
        "dob_002",
        "dob",
        "Tôi sinh ngày năm tháng mười một năm một nghìn chín trăm chín mươi hai",
        voice=SECOND_VOICE,
    ),
    sample(
        "dob_003",
        "dob",
        "Ngày sinh của tôi là ngày hai tháng bảy năm một nghìn chín trăm tám mươi lăm",
    ),
    sample("dob_004", "dob", "Tôi sinh năm một nghìn chín trăm chín mươi", voice=SECOND_VOICE),
    sample("dob_005", "dob", "Ngày hai mươi chín tháng hai năm hai nghìn", notes="leap-day case"),
    sample(
        "dob_006", "dob", "Mùng một tháng một năm hai nghìn không trăm lẻ một", voice=SECOND_VOICE
    ),
    sample(
        "dob_007", "dob", "Ngày ba mươi mốt tháng mười hai năm một nghìn chín trăm sáu mươi chín"
    ),
    sample(
        "dob_008",
        "dob",
        "Mười bốn tháng ba năm bảy tám",
        voice=SECOND_VOICE,
        notes="intentionally ambiguous two-digit year; do not infer century",
    ),
    sample("style_001", "styles", "Tôi muốn đổi lịch", speed="slow", rate="-30%"),
    sample("style_002", "styles", "Tôi muốn đổi lịch", speed="normal", voice=SECOND_VOICE),
    sample("style_003", "styles", "Tôi muốn đổi lịch", speed="fast", rate="+35%"),
    sample(
        "style_004",
        "styles",
        "À, tôi muốn, đổi lịch",
        speed="hesitant",
        rate="-15%",
        voice=SECOND_VOICE,
    ),
    sample("style_005", "styles", "Ừm, tôi muốn đổi lịch ấy", speed="filler", rate="-5%"),
    sample(
        "noise_001",
        "noise",
        "Tôi muốn xác nhận lịch khám",
        noise="light_white",
        sample_rate_hz=8_000,
        voice=SECOND_VOICE,
        notes="synthetic narrowband phone fixture",
    ),
    sample(
        "noise_002",
        "noise",
        "Tên tôi là Nguyễn Minh An",
        noise="moderate_white",
        sample_rate_hz=8_000,
        notes="synthetic narrowband phone fixture",
    ),
    sample(
        "noise_003",
        "noise",
        "Tôi sinh ngày mười bốn tháng ba năm một nghìn chín trăm bảy mươi tám",
        noise="room_echo",
        sample_rate_hz=8_000,
        voice=SECOND_VOICE,
        notes="synthetic narrowband phone fixture",
    ),
]


def write_metadata() -> None:
    SAMPLE_ROOT.mkdir(parents=True, exist_ok=True)
    for category in {item["category"] for item in SAMPLES}:
        (SAMPLE_ROOT / category).mkdir(exist_ok=True)
    output = SAMPLE_ROOT / "metadata.jsonl"
    with output.open("w", encoding="utf-8", newline="\n") as handle:
        for item in SAMPLES:
            record = dict(item)
            audio_path = SAMPLE_ROOT / item["audio_path"]
            if audio_path.exists():
                with audio_path.open("rb") as audio_handle:
                    record["sha256"] = hashlib.file_digest(audio_handle, "sha256").hexdigest()
                with wave.open(str(audio_path), "rb") as source:
                    record["duration_ms"] = round(
                        source.getnframes() * 1000 / source.getframerate()
                    )
                record["byte_size"] = audio_path.stat().st_size
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def verify_fixture_set() -> None:
    failures: list[str] = []
    for item in SAMPLES:
        audio_path = SAMPLE_ROOT / item["audio_path"]
        if not audio_path.exists():
            failures.append(f"missing: {item['audio_path']}")
            continue
        with wave.open(str(audio_path), "rb") as source:
            observed = (source.getframerate(), source.getnchannels(), source.getsampwidth())
        expected = (item["sample_rate_hz"], item["channel_count"], 2)
        if observed != expected:
            failures.append(
                f"invalid WAV {item['audio_path']}: observed={observed}, expected={expected}"
            )
    if failures:
        raise SystemExit("Fixture verification failed:\n" + "\n".join(failures))
    print(f"Verified {len(SAMPLES)} PCM WAV fixtures and their manifest paths.")


def find_optional_modules() -> tuple[Any, str]:
    local_roots = [ROOT / ".tools" / "edge_tts", ROOT / ".tools" / "audio"]
    for local_root in local_roots:
        if local_root.exists():
            sys.path.insert(0, str(local_root))
    try:
        import edge_tts  # type: ignore[import-not-found]
        import imageio_ffmpeg  # type: ignore[import-not-found]
    except ImportError as exc:
        raise SystemExit(
            "Audio dependencies missing. Install edge-tts and imageio-ffmpeg, "
            "or run with --metadata-only."
        ) from exc
    return edge_tts, imageio_ffmpeg.get_ffmpeg_exe()


def add_effect(path: Path, effect: str, seed: int) -> None:
    if effect == "clean":
        return
    with wave.open(str(path), "rb") as source:
        params = source.getparams()
        samples = array("h", source.readframes(source.getnframes()))
    # A fixed non-cryptographic PRNG makes test noise reproducible.
    rng = random.Random(seed)  # noqa: S311
    original = samples.tolist()
    peak = 420 if effect == "light_white" else 1_150
    if effect in {"light_white", "moderate_white"}:
        for index, value in enumerate(original):
            samples[index] = max(-32768, min(32767, value + rng.randint(-peak, peak)))
    elif effect == "room_echo":
        delay = max(1, int(params.framerate * 0.11))
        for index, value in enumerate(original):
            echo = int(original[index - delay] * 0.32) if index >= delay else 0
            samples[index] = max(-32768, min(32767, value + echo))
    with wave.open(str(path), "wb") as target:
        target.setparams(params)
        target.writeframes(samples.tobytes())


async def generate_one(item: dict[str, Any], edge_tts: Any, ffmpeg: str, index: int) -> None:
    destination = SAMPLE_ROOT / item["audio_path"]
    with tempfile.TemporaryDirectory(prefix="callbot_tts_") as tmp:
        mp3_path = Path(tmp) / "source.mp3"
        communicator = edge_tts.Communicate(
            item["expected_transcript"], item["voice"], rate=item["tts_rate"]
        )
        await communicator.save(str(mp3_path))
        command = [
            ffmpeg,
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-i",
            str(mp3_path),
            "-ac",
            "1",
            "-ar",
            str(item["sample_rate_hz"]),
            "-c:a",
            "pcm_s16le",
            str(destination),
        ]
        process = await asyncio.create_subprocess_exec(*command)
        return_code = await process.wait()
        if return_code != 0:
            raise RuntimeError(f"FFmpeg exited with status {return_code}")
    add_effect(destination, item["noise"], seed=20260914 + index)


async def generate_audio() -> None:
    edge_tts, ffmpeg = find_optional_modules()
    for index, item in enumerate(SAMPLES, start=1):
        print(f"[{index:02d}/{len(SAMPLES)}] {item['audio_path']}")
        await generate_one(item, edge_tts, ffmpeg, index)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--metadata-only", action="store_true")
    mode.add_argument("--generate-audio", action="store_true")
    mode.add_argument("--verify", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    write_metadata()
    if args.generate_audio:
        asyncio.run(generate_audio())
        write_metadata()
        verify_fixture_set()
    elif args.verify:
        verify_fixture_set()


if __name__ == "__main__":
    main()
