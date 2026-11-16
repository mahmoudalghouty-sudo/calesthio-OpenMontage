#!/usr/bin/env python3
"""Acquire a small, licence-screened stock-footage set for one cloud render.

Runs only in OPENMONTAGE_PROFILE=asset_acquisition. Media remains in the
ephemeral GitHub runner workspace and is never committed or uploaded as an
artifact. The resulting manifest records provenance and SHA-256 hashes.
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.video.direct_clip_search import ASSET_ACQUISITION_ALLOWED_SOURCES, DirectClipSearch

REQUEST_PATH = ROOT / "jobs" / "requests" / "next.json"


def fail(message: str) -> None:
    raise SystemExit(f"CLOUD_ASSET_ERROR: {message}")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def probe(path: Path) -> dict:
    raw = subprocess.check_output(
        ["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(path)],
        text=True,
    )
    return json.loads(raw)


def main() -> None:
    if os.environ.get("OPENMONTAGE_PROFILE", "").strip().lower() != "asset_acquisition":
        fail("must run with OPENMONTAGE_PROFILE=asset_acquisition")
    request = json.loads(REQUEST_PATH.read_text(encoding="utf-8"))
    project_id = str(request.get("project_id", "phone-video"))
    project = (ROOT / "projects" / project_id).resolve()
    assets_dir = (project / "assets" / "stock").resolve()
    artifacts_dir = (project / "artifacts").resolve()
    assets_dir.mkdir(parents=True, exist_ok=True)
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    queries = request.get("asset_queries") or []
    if not isinstance(queries, list) or len(queries) > 12:
        fail("asset_queries must be a list containing at most 12 entries")
    if not queries:
        manifest = {
            "version": 1,
            "project_id": project_id,
            "commercial_safe_only": True,
            "assets": [],
            "summary": {"queries": 0, "downloaded": 0, "note": "No supplementary stock footage requested."},
        }
        (artifacts_dir / "stock-assets.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        print(json.dumps(manifest, indent=2))
        return

    normalised = []
    for index, item in enumerate(queries):
        if not isinstance(item, dict) or not isinstance(item.get("query"), str) or not item["query"].strip():
            fail(f"asset_queries[{index}] requires a non-empty query")
        normalised.append({
            "query": item["query"].strip()[:160],
            "slot_id": str(item.get("slot_id", f"slot_{index + 1:02d}"))[:64],
            "kind": "video",
        })

    requested_sources = request.get("asset_sources") or sorted(ASSET_ACQUISITION_ALLOWED_SOURCES)
    if not isinstance(requested_sources, list) or set(requested_sources) - ASSET_ACQUISITION_ALLOWED_SOURCES:
        fail("asset_sources contains a provider outside the no-key allowlist")

    result = DirectClipSearch().execute({
        "output_dir": str(assets_dir),
        "queries": normalised,
        "sources": requested_sources,
        "clips_per_query": 2,
        "commercial_safe_only": True,
        "extract_thumbnails": True,
        "timeout_seconds": 480,
    })
    if not result.success:
        fail(result.error or "stock search failed")
    data = result.data or {}
    assets = []
    for item in data.get("clips", []):
        candidate_path = Path(item["path"]).resolve()
        if assets_dir not in candidate_path.parents:
            fail(f"stock asset escaped the acquisition directory: {candidate_path}")
        if not candidate_path.is_file() or candidate_path.stat().st_size < 1024:
            continue
        media = probe(candidate_path)
        video = next((stream for stream in media.get("streams", []) if stream.get("codec_type") == "video"), None)
        if not video:
            candidate_path.unlink(missing_ok=True)
            continue
        license_text = str(item.get("license", ""))
        if not license_text or not item.get("source_url"):
            candidate_path.unlink(missing_ok=True)
            continue
        assets.append({
            "asset_id": str(item["clip_id"]),
            "slot_id": str(item.get("slot_id", "")),
            "query": str(item.get("query", "")),
            "path": str(candidate_path),
            "source": str(item.get("source", "")),
            "source_url": str(item.get("source_url", "")),
            "creator": str(item.get("creator", "")),
            "license": license_text,
            "sha256": sha256(candidate_path),
            "size_bytes": candidate_path.stat().st_size,
            "duration_seconds": float(media.get("format", {}).get("duration", 0)),
            "width": int(video.get("width", 0)),
            "height": int(video.get("height", 0)),
            "thumbnail": str(item.get("thumbnail", "")),
        })

    manifest = {
        "version": 1,
        "project_id": project_id,
        "commercial_safe_only": True,
        "sources": data.get("resolved_sources", []),
        "summary": {
            "queries": data.get("queries_run", 0),
            "downloaded": len(assets),
            "license_rejected": data.get("license_rejected", 0),
            "errors": data.get("errors", []),
        },
        "assets": assets,
    }
    output = artifacts_dir / "stock-assets.json"
    output.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(manifest, indent=2))
    print(f"PASS: acquired {len(assets)} licence-screened stock clips (ephemeral workspace only).")


if __name__ == "__main__":
    main()
