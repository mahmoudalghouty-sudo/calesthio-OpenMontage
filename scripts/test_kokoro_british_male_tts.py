#!/usr/bin/env python3
"""Generate and validate local Kokoro British-male TTS audition WAVs.

Run after installing the optional local TTS dependencies and downloading/caching
Kokoro assets. This script never calls a hosted inference API.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

VOICES = ("bm_george", "bm_fable", "bm_daniel", "bm_lewis")
SAMPLE_RATE = 24_000
DEFAULT_TEXT = (
    "Your pet deserves more than an ordinary routine. "
    "Discover a smarter, simpler way to make every day better. "
    "Shop today and give your best friend the care they deserve."
)


def to_numpy(audio):
    if hasattr(audio, "detach"):
        audio = audio.detach().cpu().numpy()
    import numpy as np
    return np.asarray(audio, dtype=np.float32).reshape(-1)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default="output/tts_audition")
    parser.add_argument("--text", default=DEFAULT_TEXT)
    parser.add_argument("--rate", type=float, default=1.0)
    parser.add_argument("--offline", action="store_true",
                        help="Require cached assets; disable Hugging Face network access.")
    args = parser.parse_args()

    if args.offline:
        os.environ["HF_HUB_OFFLINE"] = "1"
        os.environ["TRANSFORMERS_OFFLINE"] = "1"

    try:
        import numpy as np
        import soundfile as sf
        from kokoro import KPipeline
    except Exception as exc:
        print(f"Missing TTS dependency: {exc}", file=sys.stderr)
        return 2

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()

    try:
        pipeline = KPipeline(lang_code="b")
    except Exception as exc:
        print(f"Could not load Kokoro British-English pipeline: {exc}", file=sys.stderr)
        return 3

    results = []
    for voice in VOICES:
        voice_started = time.perf_counter()
        chunks = []
        try:
            for _graphemes, _phonemes, audio in pipeline(
                args.text, voice=voice, speed=args.rate
            ):
                chunk = to_numpy(audio)
                if chunk.size:
                    chunks.append(chunk)

            if not chunks:
                raise RuntimeError("Kokoro returned no audio chunks")

            samples = np.concatenate(chunks)
            if not np.isfinite(samples).all():
                raise RuntimeError("Audio contains NaN or infinite samples")
            peak = float(np.max(np.abs(samples)))
            if peak <= 1e-6:
                raise RuntimeError("Audio is silent or near-silent")

            path = output_dir / f"{voice}_rate_{args.rate:.2f}.wav"
            sf.write(str(path), samples, SAMPLE_RATE, subtype="PCM_16")
            info = sf.info(str(path))
            if info.frames <= 0 or info.samplerate != SAMPLE_RATE:
                raise RuntimeError("WAV validation failed")

            results.append({
                "voice": voice,
                "language": "British English",
                "lang_code": "b",
                "rate": args.rate,
                "file": str(path),
                "sample_rate": info.samplerate,
                "duration_seconds": round(info.duration, 3),
                "peak_amplitude": round(peak, 6),
                "generation_seconds": round(time.perf_counter() - voice_started, 3),
                "status": "passed",
            })
            print(f"PASS {voice}: {path} ({info.duration:.2f}s)")
        except Exception as exc:
            results.append({
                "voice": voice,
                "language": "British English",
                "rate": args.rate,
                "status": "failed",
                "error": str(exc),
            })
            print(f"FAIL {voice}: {exc}", file=sys.stderr)

    report = {
        "engine": "Kokoro-82M",
        "language": "British English",
        "lang_code": "b",
        "voice_gender": "male",
        "rate": args.rate,
        "offline_mode": bool(args.offline),
        "total_seconds": round(time.perf_counter() - started, 3),
        "results": results,
    }
    report_path = output_dir / "tts_audition_report.json"
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    passed = sum(item["status"] == "passed" for item in results)
    print(f"\n{passed}/{len(VOICES)} voice samples passed. Report: {report_path}")
    return 0 if passed == len(VOICES) else 1


if __name__ == "__main__":
    raise SystemExit(main())
