"""Run a tiny local FFmpeg edit/export smoke test using synthetic test media.

This fixture is test-only. It does not call AI generation services, download media,
or use any user footage.
"""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path


def run(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def main() -> int:
    ffmpeg = shutil.which("ffmpeg")
    ffprobe = shutil.which("ffprobe")
    if not ffmpeg or not ffprobe:
        raise SystemExit("FFmpeg and FFprobe are required for the editing smoke test.")

    with tempfile.TemporaryDirectory(prefix="openmontage-smoke-") as temp:
        root = Path(temp)
        source = root / "synthetic-source.mp4"
        edited = root / "edited-output.mp4"

        run([
            ffmpeg, "-hide_banner", "-loglevel", "error", "-y",
            "-f", "lavfi", "-i", "color=c=black:s=320x240:r=24:d=1",
            "-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=48000",
            "-shortest", "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-c:a", "aac", str(source),
        ])
        run([
            ffmpeg, "-hide_banner", "-loglevel", "error", "-y",
            "-i", str(source), "-vf", "scale=320:240",
            "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-c:a", "aac", str(edited),
        ])
        probe = run([
            ffprobe, "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", str(edited),
        ])
        if not edited.is_file() or edited.stat().st_size <= 0:
            raise SystemExit("FFmpeg did not produce a non-empty MP4.")
        try:
            duration = float(probe.stdout.strip())
        except ValueError as exc:
            raise SystemExit("FFprobe did not return a valid MP4 duration.") from exc
        if duration <= 0:
            raise SystemExit("The exported MP4 has no positive duration.")

        print(f"FFmpeg editing smoke test passed: {edited.stat().st_size} bytes, {duration:.2f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
