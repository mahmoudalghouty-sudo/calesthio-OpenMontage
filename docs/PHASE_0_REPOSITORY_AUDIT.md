# Phase 0 Repository Audit

Audit date: 2026-11-15
Audited ref: `cloud-studio-foundation`
Scope: zero-dollar editing/review studio; no AI video generation.

## Confirmed existing capabilities

| Area | Existing repository evidence | Audit finding |
|---|---|---|
| Agent orchestration | `AGENT_GUIDE.md`, pipeline manifests, director skills | Claude Code is already the intended director. Do not add a second orchestrator. |
| Approval checkpoints | `lib/checkpoint.py`, `skills/meta/checkpoint-protocol.md`, 13 shipped manifests | The branch sets every checkpointed stage to require human approval and adds a catalog contract test. |
| FFmpeg editing | `tools/video/video_compose.py`, `tools/video/video_stitch.py`, `tools/audio/audio_mixer.py` | Existing tools cover cuts, composition, audio mixing, subtitles, overlays, encoding, and stitching. |
| Remotion | `remotion-composer/` | Existing React composition project and scene components; Node dependencies are managed separately in that directory. |
| HyperFrames | `tools/video/hyperframes_compose.py` | Existing HTML/CSS/GSAP render path; requires Node.js 22+ and FFmpeg. |
| Source-footage inspection | `lib/source_media_review.py` | Existing standardized review helper probes technical media details and samples representative frames. |
| Video analysis | `tools/analysis/video_analyzer.py` | Existing analyzer supports transcript-only, standard, and deep modes; uses FFmpeg/scene detection/keyframes and optional local transcription. |
| Scene and frame analysis | `tools/analysis/scene_detect.py`, `tools/analysis/frame_sampler.py` | Existing local tools identify scene boundaries and extract timestamped frames. |
| Audio inspection | `tools/analysis/audio_probe.py`, `tools/analysis/audio_energy.py` | Existing FFprobe/FFmpeg tools inspect media streams and audio energy. |
| Speech transcription | `tools/analysis/transcriber.py` | Word timestamps are supported through faster-whisper; this dependency is optional and may be too heavy for a small free runner. |
| Review UI | `backlot/` | Backlot is read-only and intentionally loopback-only. It must not be exposed publicly as-is. |
| CI | `.github/workflows/ci.yml` | CI installs FFmpeg and runs lint plus the test suite. No workflow run was present during this audit. |

## Missing or unverified capabilities

1. There is no verified cloud rendering service with guaranteed capacity at $0/month.
2. There is no root Dockerfile or docker-compose deployment in the audited tree.
3. Root `requirements.txt` does not install all optional deep-analysis packages (yt-dlp, youtube-transcript-api, scenedetect, faster-whisper); they must remain opt-in and resource-checked.
4. `video_understand` depends on Transformers/Torch and is marked local-GPU/experimental. Do not make it a required dependency for the zero-cost CPU path.
5. There is no dedicated, verified competitor-intelligence collector for Meta Ad Library and TikTok Creative Center. Initial research must use public links/materials supplied by the user and record provenance; do not promise scraping or private metrics.
6. The existing video-analysis artifact is scene-oriented. A genuinely detailed second-by-second editorial report needs a new report schema/agent workflow that combines timestamped frames, transcript words, scene boundaries, and audio measurements. A timestamped table alone is not proof of actual retention or conversion.
7. Root CI has not yet demonstrated a successful run for this branch. The PR is still a draft and must not be merged based on static inspection alone.

## Zero-dollar safety finding

The repository's original `config.yaml` used `budget.mode: warn` and `budget.total_usd: 10.00`, which did not match the user's strict $0 requirement.

This branch now sets:
- `budget.mode: cap`
- `budget.total_usd: 0.00`
- `budget.reserve_pct: 0.00`
- `budget.single_action_approval_usd: 0.00`

A regression test was added at `tests/contracts/test_zero_cost_studio_budget.py` to assert the zero-cap configuration and that a positive-cost reservation is rejected by `CostTracker`.

Important limitation: this guard protects operations that correctly pass through `CostTracker` with an accurate positive estimate. It is not yet a universal execution firewall around every provider tool. Until that audit and enforcement are complete, do not run any provider/API-generation tools. The studio's initial editing path must use only local FFmpeg/Remotion operations and user-supplied media.

## Recommended implementation sequence

1. Finish Phase 0 by tracing every provider/API execution path and proving no paid provider can be invoked from the editing-only profile.
2. Add a no-generation, no-network editing profile and contract tests.
3. Add a small manual CI smoke workflow that creates a synthetic color-bar clip, edits/mixes it with FFmpeg, and verifies the MP4 with FFprobe. Do not upload user media in this test.
4. Build the second-by-second analysis report using existing local analyzers, with optional transcription clearly marked.
5. Add competitor research intake for user-supplied public references and evidence-linked notes; no scraping bypasses.
6. Only after the smoke workflow passes, decide whether a static mobile control panel is useful. Do not create cloud accounts, buckets, Workers, or external storage before explicit approval.

## Validation status

- Repository tree and key source files inspected through GitHub.
- All 13 shipped pipeline manifests had previously been audited for human approval gates.
- Zero-cost configuration and regression test committed to the feature branch.
- GitHub Actions workflow runs: none found during this audit.
- Python test suite: not executed in this environment.
- Cloud resources: none created.
- Paid services, API keys, and payment methods: none added.
