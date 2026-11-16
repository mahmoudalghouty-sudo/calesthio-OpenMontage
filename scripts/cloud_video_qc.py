#!/usr/bin/env python3
"""Deterministic post-render QC for cloud MP4 output.

Technical checks only: this does not claim to judge whether a hook, story,
or shot is persuasive. Black/freeze/silence detections are warnings because
intentional creative pauses and fades can be valid.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path


def probe(path: Path) -> dict:
    raw = subprocess.check_output(
        ["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(path)],
        text=True,
    )
    return json.loads(raw)


def parse_detection_log(stderr: str) -> dict:
    black = []
    freezes = []
    silence = []
    for match in re.finditer(r"black_start:([0-9.]+) black_end:([0-9.]+) black_duration:([0-9.]+)", stderr):
        black.append({
            "start_seconds": float(match.group(1)),
            "end_seconds": float(match.group(2)),
            "duration_seconds": float(match.group(3)),
        })
    for match in re.finditer(r"freeze_start:([0-9.]+)", stderr):
        freezes.append({"start_seconds": float(match.group(1))})
    for match in re.finditer(r"silence_start:([0-9.]+)", stderr):
        silence.append({"start_seconds": float(match.group(1))})
    return {"black_intervals": black, "freeze_events": freezes, "silence_events": silence}


def run_qc(video_path: Path, expected_width: int | None = None, expected_height: int | None = None) -> dict:
    if not video_path.is_file() or video_path.stat().st_size < 1024:
        raise ValueError("Rendered video is missing or too small")
    metadata = probe(video_path)
    streams = metadata.get("streams", [])
    video = next((item for item in streams if item.get("codec_type") == "video"), None)
    audio = next((item for item in streams if item.get("codec_type") == "audio"), None)
    if not video:
        raise ValueError("Rendered file has no video stream")
    duration = float(metadata.get("format", {}).get("duration", 0))
    if duration <= 0:
        raise ValueError("Rendered file has invalid duration")
    if expected_width and int(video.get("width", 0)) != expected_width:
        raise ValueError("Rendered width does not match requested profile")
    if expected_height and int(video.get("height", 0)) != expected_height:
        raise ValueError("Rendered height does not match requested profile")

    cmd = [
        "ffmpeg", "-hide_banner", "-i", str(video_path),
        "-vf", "blackdetect=d=0.4:pix_th=0.10,freezedetect=n=-50dB:d=2",
        "-af", "silencedetect=noise=-45dB:d=1.5" if audio else "anull",
        "-f", "null", "-",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg QC failed: {result.stderr[-1200:]}")
    detections = parse_detection_log(result.stderr)
    warnings = []
    if detections["black_intervals"]:
        warnings.append("Black intervals detected; review whether they are intentional.")
    if detections["freeze_events"]:
        warnings.append("Potential frozen frames detected; review the listed timestamps.")
    if detections["silence_events"]:
        warnings.append("Audio silence intervals detected; confirm they are intentional.")
    return {
        "status": "passed_with_warnings" if warnings else "passed",
        "file": str(video_path),
        "duration_seconds": duration,
        "video": {
            "codec": video.get("codec_name"),
            "width": int(video.get("width", 0)),
            "height": int(video.get("height", 0)),
            "fps": video.get("r_frame_rate"),
        },
        "audio": {
            "present": bool(audio),
            "codec": audio.get("codec_name") if audio else None,
        },
        "detections": detections,
        "warnings": warnings,
        "scope": "technical signal checks only; creative/semantic review remains with the multimodal agent",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("video", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--width", type=int)
    parser.add_argument("--height", type=int)
    args = parser.parse_args()
    report = run_qc(args.video, args.width, args.height)
    output = args.output or args.video.with_suffix(".qc.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
