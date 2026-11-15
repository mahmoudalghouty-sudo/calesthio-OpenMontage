#!/usr/bin/env python3
"""Render one phone-uploaded source through OpenMontage's VideoCompose tool.

This is a small, deterministic cloud-job adapter. It does not call generation
providers, publishing APIs, or paid services. The runner is ephemeral.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from lib.env_loader import load_env

load_env()

from lib.media_profiles import get_profile
from tools.video.video_compose import VideoCompose

REQUEST_PATH = ROOT / "jobs" / "requests" / "next.json"
ALLOWED_PROFILES = {
    "instagram_reels",
    "instagram_feed",
    "youtube_shorts",
    "youtube_landscape",
    "tiktok",
}


def fail(message: str) -> None:
    raise SystemExit(f"CLOUD_RENDER_ERROR: {message}")


def probe(path: Path) -> dict:
    raw = subprocess.check_output(
        ["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(path)],
        text=True,
    )
    return json.loads(raw)


def main() -> None:
    if not REQUEST_PATH.is_file():
        fail(f"request file missing: {REQUEST_PATH.relative_to(ROOT)}")
    request = json.loads(REQUEST_PATH.read_text(encoding="utf-8"))

    project_id = str(request.get("project_id", "phone-video"))
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{1,47}", project_id):
        fail("project_id must be 2-48 lowercase letters, numbers, or hyphens")

    profile_name = str(request.get("output_profile", "instagram_reels"))
    if profile_name not in ALLOWED_PROFILES:
        fail(f"unsupported output_profile: {profile_name}")
    profile = get_profile(profile_name)

    project = ROOT / "projects" / project_id
    assets = project / "assets"
    renders = project / "renders"
    artifacts = project / "artifacts"
    for folder in (assets, renders, artifacts):
        folder.mkdir(parents=True, exist_ok=True)

    configured_input = os.environ.get("CLOUD_VIDEO_INPUT")
    source = Path(configured_input) if configured_input else assets / "source.mp4"
    if not source.is_absolute():
        source = ROOT / source
    if not source.is_file():
        fail(f"source video not found: {source}")

    source_probe = probe(source)
    video_stream = next((s for s in source_probe.get("streams", []) if s.get("codec_type") == "video"), None)
    if not video_stream:
        fail("input file contains no video stream")
    duration = float(source_probe.get("format", {}).get("duration", 0))
    if duration <= 0 or duration > 1800:
        fail(f"unsupported video duration: {duration:.2f}s (allowed: 0-1800s)")

    raw_cuts = request.get("cuts") or [{"in_seconds": 0, "out_seconds": duration}]
    if not isinstance(raw_cuts, list) or not raw_cuts or len(raw_cuts) > 100:
        fail("cuts must contain 1-100 edit segments")

    cuts = []
    for index, item in enumerate(raw_cuts):
        start = float(item.get("in_seconds", 0))
        end = float(item.get("out_seconds", duration))
        speed = float(item.get("speed", 1.0))
        if start < 0 or end <= start or end > duration + 0.05:
            fail(f"cut {index + 1} is outside the source duration")
        if speed < 0.5 or speed > 2.0:
            fail(f"cut {index + 1} speed must be between 0.5 and 2.0")
        cuts.append({
            "source": str(source),
            "in_seconds": start,
            "out_seconds": min(end, duration),
            "speed": speed,
        })

    subtitle_path = None
    subtitle_text = request.get("subtitles_srt")
    if subtitle_text:
        if not isinstance(subtitle_text, str) or len(subtitle_text) > 20000:
            fail("subtitles_srt must be text no longer than 20,000 characters")
        subtitle_path = assets / "subtitles.srt"
        subtitle_path.write_text(subtitle_text, encoding="utf-8")

    style = request.get("subtitle_style") or {
        "font": "Arial",
        "font_size": 32,
        "bold": True,
        "outline_width": 3,
        "margin_v": 180,
        "alignment": 2,
    }
    allowed_style = {"font", "font_size", "bold", "primary_color", "outline_color", "outline_width", "margin_v", "alignment", "shadow"}
    if not isinstance(style, dict) or set(style) - allowed_style:
        fail("subtitle_style contains unsupported fields")

    target = {
        "width": profile.width,
        "height": profile.height,
        "fit": "cover" if profile.height > profile.width else "pad",
    }
    output = renders / "final.mp4"
    payload = {
        "operation": "compose",
        "edit_decisions": {
            "cuts": cuts,
            "metadata": {"compose_target": target},
        },
        "profile": profile_name,
        "crf": profile.crf,
        "preset": "fast",
        "output_path": str(output),
    }
    if subtitle_path:
        payload["subtitle_path"] = str(subtitle_path)
        payload["subtitle_style"] = style

    result = VideoCompose().execute(payload)
    if not result.success:
        fail(f"VideoCompose failed: {result.error}")

    output_probe = probe(output)
    final_video = next((s for s in output_probe.get("streams", []) if s.get("codec_type") == "video"), None)
    if not final_video:
        fail("render output contains no video stream")
    if (int(final_video["width"]), int(final_video["height"])) != (profile.width, profile.height):
        fail(f"unexpected output dimensions: {final_video.get('width')}x{final_video.get('height')}")
    if final_video.get("codec_name") != "h264":
        fail(f"unexpected video codec: {final_video.get('codec_name')}")
    from fractions import Fraction
    actual_fps = float(Fraction(final_video.get("r_frame_rate", "0/1")))
    if abs(actual_fps - profile.fps) > 0.1:
        fail(f"unexpected frame rate: {actual_fps:.3f} fps")
    audio_stream = next((s for s in output_probe.get("streams", []) if s.get("codec_type") == "audio"), None)
    if not audio_stream or audio_stream.get("codec_name") != "aac":
        fail("render output must contain an AAC audio stream")
    output_duration = float(output_probe["format"]["duration"])
    expected_duration = sum((c["out_seconds"] - c["in_seconds"]) / c["speed"] for c in cuts)
    if abs(output_duration - expected_duration) > 0.75:
        fail(f"unexpected render duration: {output_duration:.2f}s; expected about {expected_duration:.2f}s")
    if profile.max_duration_seconds and output_duration > profile.max_duration_seconds:
        fail(f"output exceeds {profile_name} duration limit of {profile.max_duration_seconds}s")
    max_size_mb = min(profile.max_file_size_mb or 500, 500)
    if output.stat().st_size > max_size_mb * 1024 * 1024:
        fail(f"render output exceeds the {max_size_mb:g} MB safe limit")

    report = {
        "project_id": project_id,
        "output_profile": profile_name,
        "source": {
            "duration_seconds": duration,
            "width": int(video_stream.get("width", 0)),
            "height": int(video_stream.get("height", 0)),
            "size_bytes": source.stat().st_size,
        },
        "render": {
            "duration_seconds": float(output_probe["format"]["duration"]),
            "width": int(final_video["width"]),
            "height": int(final_video["height"]),
            "codec": final_video.get("codec_name"),
            "audio_codec": audio_stream.get("codec_name"),
            "fps": actual_fps,
            "size_bytes": output.stat().st_size,
            "subtitle_burned": bool(subtitle_path),
            "cut_count": len(cuts),
        },
    }
    (artifacts / "render-report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    print(f"PASS: OpenMontage rendered {output.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
