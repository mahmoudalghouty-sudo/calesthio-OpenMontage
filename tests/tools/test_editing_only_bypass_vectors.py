"""Bypass attempts against the OPENMONTAGE_PROFILE=editing_only guard.

Each test tries a route around the guard (the asset cache, Backlot event
side effects, nested/indirect tool calls, subclassing, URL spelling tricks,
profile spelling) and asserts the call is refused *before* the tool body, a
cache lookup, or any network-capable helper runs.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from lib.asset_cache import AssetCache, reset_default_asset_cache
from tools.analysis.transcript_fetcher import TranscriptFetcher
from tools.analysis.video_analyzer import VideoAnalyzer
from tools.analysis.video_downloader import VideoDownloader
from tools.base_tool import (
    BaseTool,
    Determinism,
    ResourceProfile,
    ToolResult,
    ToolRuntime,
    ToolTier,
    _is_remote_reference,
    editing_only_block_reasons,
)


# --------------------------------------------------------------------------
# Fixtures / fake tools
# --------------------------------------------------------------------------

@pytest.fixture
def editing_only(monkeypatch):
    monkeypatch.setenv("OPENMONTAGE_PROFILE", "editing_only")


@pytest.fixture
def enabled_cache(tmp_path, monkeypatch):
    monkeypatch.setenv("OPENMONTAGE_ASSET_CACHE", "1")
    monkeypatch.setenv("OPENMONTAGE_ASSET_CACHE_DIR", str(tmp_path / "cache"))
    monkeypatch.setenv("OPENMONTAGE_ASSET_CACHE_MAX_GB", "0.01")
    reset_default_asset_cache()
    yield
    reset_default_asset_cache()


class _CacheableTool(BaseTool):
    """Deterministic single-file writer, so the asset cache will admit it."""

    tier = ToolTier.CORE
    runtime = ToolRuntime.LOCAL
    determinism = Determinism.DETERMINISTIC
    idempotency_key_fields = ["source", "prompt"]
    resource_profile = ResourceProfile(network_required=False)

    def __init__(self) -> None:
        self.calls = 0

    def execute(self, inputs: dict) -> ToolResult:
        self.calls += 1
        out = Path(inputs["output_path"])
        out.write_bytes(b"artifact-bytes")
        return ToolResult(success=True, data={"output": str(out)}, artifacts=[str(out)])


class CachedGenerator(_CacheableTool):
    name = "test_cached_generator"
    tier = ToolTier.GENERATE

    def execute(self, inputs: dict) -> ToolResult:
        return super().execute(inputs)


class CachedRemoteAnalyzer(_CacheableTool):
    name = "test_cached_remote_analyzer"
    tier = ToolTier.ANALYZE
    remote_source_input_keys = ["source"]

    def execute(self, inputs: dict) -> ToolResult:
        return super().execute(inputs)


class PaidProvider(BaseTool):
    name = "test_paid_provider"
    tier = ToolTier.GENERATE
    runtime = ToolRuntime.API
    resource_profile = ResourceProfile(network_required=True)
    ran = False

    def execute(self, inputs: dict) -> ToolResult:
        PaidProvider.ran = True
        return ToolResult(success=True)


class LocalSelector(BaseTool):
    """A permitted local tool that delegates to another tool's execute()."""

    name = "test_local_selector"
    tier = ToolTier.CORE
    runtime = ToolRuntime.LOCAL
    resource_profile = ResourceProfile(network_required=False)

    def __init__(self, delegate: BaseTool) -> None:
        self.delegate = delegate

    def execute(self, inputs: dict) -> ToolResult:
        return self.delegate.execute(inputs)


class RenamedAnalyzer(VideoAnalyzer):
    """Subclass with a new name: name-based checks alone would miss it."""

    name = "my_reference_analyzer"


class OverridingAnalyzer(VideoAnalyzer):
    """Subclass that overrides execute() and calls super()."""

    name = "overriding_analyzer"

    def execute(self, inputs: dict) -> ToolResult:
        return super().execute(inputs)


REMOTE_SOURCES = [
    "https://www.youtube.com/watch?v=abc123",
    "HTTPS://WWW.YOUTUBE.COM/watch?v=abc123",
    "   https://example.com/clip.mp4  ",
    "http://example.com/clip.mp4",
    "www.youtube.com/watch?v=abc123",
    "//cdn.example.com/clip.mp4",
    "ftp://example.com/clip.mp4",
    "rtmp://live.example.com/stream",
    "s3://bucket/clip.mp4",
]

LOCAL_SOURCES = [
    "/workspace/input.mp4",
    "relative/https_clip.mp4",
    "clips/www_backup.mp4",
    "C://clips/input.mp4",
    "C:\\clips\\input.mp4",
    "file:///workspace/input.mp4",
]


# --------------------------------------------------------------------------
# URL classification
# --------------------------------------------------------------------------

@pytest.mark.parametrize("source", REMOTE_SOURCES)
def test_remote_reference_detection(source):
    assert _is_remote_reference(source)


@pytest.mark.parametrize("source", LOCAL_SOURCES)
def test_local_paths_are_not_remote(source):
    assert not _is_remote_reference(source)


def test_nested_containers_are_inspected():
    assert _is_remote_reference(["/a.mp4", "https://x.test/b.mp4"])
    assert _is_remote_reference({"primary": "https://x.test/b.mp4"})
    assert not _is_remote_reference(["/a.mp4", "/b.mp4"])
    assert not _is_remote_reference(None)


def test_block_reasons_is_pure_and_matches_guard():
    reasons = editing_only_block_reasons(VideoAnalyzer(), {"source": "https://x.test/a.mp4"})
    assert reasons == ["remote_video_source(source)"]
    assert editing_only_block_reasons(VideoAnalyzer(), {"source": "/a.mp4"}) == []


# --------------------------------------------------------------------------
# Real video_analyzer: refused before any downloader / transcript fetch
# --------------------------------------------------------------------------

@pytest.mark.parametrize("source", REMOTE_SOURCES)
@pytest.mark.parametrize("tool_cls", [VideoAnalyzer, RenamedAnalyzer, OverridingAnalyzer])
def test_real_analyzer_remote_source_never_reaches_network(editing_only, tmp_path, tool_cls, source):
    with patch.object(VideoDownloader, "execute") as download, \
         patch.object(TranscriptFetcher, "execute") as fetch, \
         patch("tools.analysis.video_analyzer.VideoAnalyzer._detect_platform") as detect:
        with pytest.raises(PermissionError, match="remote_video_source"):
            tool_cls().execute({"source": source, "output_dir": str(tmp_path)})

    download.assert_not_called()
    fetch.assert_not_called()
    detect.assert_not_called()  # the tool body never started
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("profile", ["editing_only", "EDITING_ONLY", " editing-only ", "Editing Only"])
def test_profile_spelling_variants_are_enforced(monkeypatch, profile):
    monkeypatch.setenv("OPENMONTAGE_PROFILE", profile)
    with pytest.raises(PermissionError, match="remote_video_source"):
        VideoAnalyzer().execute({"source": "https://x.test/a.mp4"})


@pytest.mark.parametrize("tool_cls", [VideoDownloader, TranscriptFetcher])
def test_network_helpers_are_blocked_when_called_directly(editing_only, tool_cls):
    with pytest.raises(PermissionError, match="network_required"):
        tool_cls().execute({"url": "https://x.test/a.mp4", "url_or_video_id": "abc"})


# --------------------------------------------------------------------------
# Indirect invocation
# --------------------------------------------------------------------------

def test_local_tool_cannot_launder_a_blocked_provider(editing_only):
    PaidProvider.ran = False
    with pytest.raises(PermissionError, match="test_paid_provider"):
        LocalSelector(PaidProvider()).execute({})
    assert PaidProvider.ran is False


def test_local_tool_cannot_launder_a_remote_video_source(editing_only):
    with patch.object(VideoDownloader, "execute") as download:
        with pytest.raises(PermissionError, match="remote_video_source"):
            LocalSelector(VideoAnalyzer()).execute({"source": "https://x.test/a.mp4"})
    download.assert_not_called()


# --------------------------------------------------------------------------
# Asset cache: a warm cache entry must not be served under editing_only
# --------------------------------------------------------------------------

@pytest.mark.parametrize(
    "tool_cls, inputs",
    [
        (CachedGenerator, {"source": "/local.mp4", "prompt": "p"}),
        (CachedRemoteAnalyzer, {"source": "https://x.test/a.mp4", "prompt": "p"}),
    ],
)
def test_warm_cache_cannot_bypass_guard(enabled_cache, tmp_path, monkeypatch, tool_cls, inputs):
    tool = tool_cls()

    # 1. Populate the cache with the profile OFF.
    monkeypatch.delenv("OPENMONTAGE_PROFILE", raising=False)
    first = tool.execute({**inputs, "output_path": str(tmp_path / "warm.bin")})
    assert first.success and not first.from_cache
    again = tool.execute({**inputs, "output_path": str(tmp_path / "hit.bin")})
    assert again.from_cache, "precondition: the cache must actually be warm"
    calls_before = tool.calls

    # 2. Same call with the profile ON: refused before any cache lookup.
    monkeypatch.setenv("OPENMONTAGE_PROFILE", "editing_only")
    target = tmp_path / "bypass.bin"
    with patch.object(AssetCache, "try_restore") as restore, \
         patch.object(AssetCache, "store") as store:
        with pytest.raises(PermissionError):
            tool.execute({**inputs, "output_path": str(target)})
    restore.assert_not_called()
    store.assert_not_called()
    assert not target.exists()
    assert tool.calls == calls_before


# --------------------------------------------------------------------------
# Side effects: no Backlot events for a refused call
# --------------------------------------------------------------------------

def test_refused_call_emits_no_backlot_events(editing_only, tmp_path):
    project = tmp_path / "projects" / "demo"
    project.mkdir(parents=True)
    with patch("lib.events.emit_event") as emit:
        with pytest.raises(PermissionError):
            VideoAnalyzer().execute({
                "source": "https://x.test/a.mp4",
                "project_dir": str(project),
                "output_dir": str(project / "analysis"),
            })
    emit.assert_not_called()
    assert not (project / "events.jsonl").exists()
    assert not (project / "analysis").exists()


# --------------------------------------------------------------------------
# Wrapper order is part of the contract
# --------------------------------------------------------------------------

@pytest.mark.parametrize("tool_cls", [VideoAnalyzer, CachedGenerator, OverridingAnalyzer])
def test_wrapper_order_guard_then_cache_then_instrumentation(tool_cls):
    guard = tool_cls.__dict__["execute"]
    assert getattr(guard, "_editing_only_guarded", False)
    cache = guard.__wrapped__
    assert getattr(cache, "_asset_cached", False)
    assert not getattr(cache, "_editing_only_guarded", False)
    instrument = cache.__wrapped__
    assert getattr(instrument, "_backlot_instrumented", False)
    assert not getattr(instrument, "_asset_cached", False)
