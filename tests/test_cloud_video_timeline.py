from pathlib import Path

import pytest

from scripts.cloud_video_job import build_timeline


def test_build_timeline_accepts_reference_source():
    source = Path("/tmp/reference.mp4")
    cuts = build_timeline(
        [{"in_seconds": 1, "out_seconds": 4}],
        source,
        10,
        {},
    )
    assert cuts == [{
        "source": str(source),
        "in_seconds": 1.0,
        "out_seconds": 4.0,
        "speed": 1.0,
    }]


def test_build_timeline_accepts_only_manifest_stock_ids(tmp_path):
    clip = tmp_path / "stock" / "clip.mp4"
    clip.parent.mkdir()
    clip.write_bytes(b"stock")
    cuts = build_timeline(
        [{"asset_id": "archive_org_123", "in_seconds": 0, "out_seconds": 3}],
        tmp_path / "reference.mp4",
        10,
        {"archive_org_123": {"path": clip, "duration": 5}},
    )
    assert cuts[0]["source"] == str(clip)
    assert cuts[0]["out_seconds"] == 3.0


def test_build_timeline_resolves_stock_by_slot_id(tmp_path):
    clip = tmp_path / "stock" / "dog-grooming.mp4"
    clip.parent.mkdir()
    clip.write_bytes(b"stock")
    cuts = build_timeline(
        [{"source": "stock", "slot_id": "dog_grooming_broll", "in_seconds": 0, "out_seconds": 2}],
        tmp_path / "reference.mp4",
        10,
        {"slot:dog_grooming_broll": {"path": clip, "duration": 4}},
    )
    assert cuts[0]["source"] == str(clip)
    assert cuts[0]["out_seconds"] == 2.0


def test_build_timeline_rejects_missing_stock_asset():
    with pytest.raises(SystemExit, match="unavailable stock asset"):
        build_timeline(
            [{"asset_id": "not-in-manifest"}],
            Path("/tmp/reference.mp4"),
            10,
            {},
        )


def test_build_timeline_rejects_arbitrary_source_path():
    with pytest.raises(SystemExit, match="unsupported source type"):
        build_timeline(
            [{"source": "/etc/passwd", "in_seconds": 0, "out_seconds": 1}],
            Path("/tmp/reference.mp4"),
            10,
            {},
        )


@pytest.mark.parametrize(
    "segment",
    [
        {"in_seconds": -1, "out_seconds": 1},
        {"in_seconds": 2, "out_seconds": 1},
        {"in_seconds": 0, "out_seconds": 11},
        {"in_seconds": 0, "out_seconds": 1, "speed": 3},
    ],
)
def test_build_timeline_rejects_invalid_ranges_and_speeds(segment):
    with pytest.raises(SystemExit):
        build_timeline(
            [segment],
            Path("/tmp/reference.mp4"),
            10,
            {},
        )


def test_build_timeline_rejects_empty_or_oversized_timeline():
    with pytest.raises(SystemExit, match="1-100"):
        build_timeline([], Path("/tmp/reference.mp4"), 10, {})
    with pytest.raises(SystemExit, match="1-100"):
        build_timeline([{}] * 101, Path("/tmp/reference.mp4"), 10, {})
