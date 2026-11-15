# Zero-Cost Cloud Video Studio

## Decision

Target recurring infrastructure spend: **$0/month**. Do not create or upgrade any paid service, attach a payment method, enable overages, or invoke paid media APIs without separate explicit approval.

This studio is an **editing, assembly, review, and export workflow** for user-supplied footage, images, and audio. It does not generate video footage, avatars, music, or paid AI assets.

## Selected zero-cost-first architecture

1. **Source of truth — existing private GitHub repository**
   - Keep source code, project manifests, approval decisions, edit instructions, and workflow definitions in Git.
   - Never commit source videos, audio masters, rendered MP4s, credentials, or signed URLs.

2. **Mobile control surface — static web interface**
   - Build a lightweight, mobile-first project/review interface and host it on GitHub Pages if the repository/account configuration permits.
   - Pages serves the interface only; it is not a video-processing server and must not contain secrets.
   - Keep the current Backlot server bound to localhost until a proper authenticated cloud design is implemented. Do not expose it directly.

3. **On-demand editing worker — GitHub Actions**
   - Use a manually dispatched workflow with a standard GitHub-hosted runner to run existing Python/Node/FFmpeg/Remotion tasks.
   - One job at a time; no always-on server, GPU, queue, or background polling.
   - Use only the included quota. For GitHub Free private repositories, the published allowance is 2,000 Actions minutes/month and 500 MB artifact storage; stop when the quota is exhausted. Do not enable paid overages.
   - Keep artifacts small and short-lived. This is suitable for short, occasional renders, not a guaranteed high-volume editing farm.

4. **Media storage — defer external bucket setup**
   - First prototype with small test media and workflow artifacts.
   - Cloudflare R2 Standard has a published free allowance of 10 GB-month storage, 1 million Class A operations, 10 million Class B operations, and free egress. However, it is usage-metered beyond those allowances. Do not create a bucket until the user separately approves the account setup and we verify billing safeguards and payment-method requirements.
   - Never use Infrequent Access storage. Never enable paid tiers or automatic overages.
   - If no safe zero-charge storage setup is available, keep media transfer manual and use short-lived workflow artifacts within their limits.

5. **Editing engine**
   - FFmpeg for cuts, trims, scaling, audio mixing, subtitles, and final MP4 encoding.
   - Existing Remotion/HyperFrames components only where the repo audit confirms they are needed.
   - No AI video generation. No paid TTS or voice API. Narration is supplied as an audio file by the user or produced with an explicitly approved free/local method.

## Human approval gates

Require explicit user approval before:
- accepting a creative brief and locking the script;
- locking the scene/edit plan;
- starting a render job;
- accepting the rendered preview;
- exporting the final deliverable.

A previous approval never authorizes the next gate. No automatic publishing.

## Hard cost controls

- Monthly target and hard intended cap: **$0**.
- No billing account upgrades, paid plans, paid API calls, GPU instances, or paid storage classes.
- Disable or avoid metered features where possible; do not add a payment method merely to unlock a free tier.
- Before each Actions render, show expected duration/quota use and stop if uncertain.
- Do not promise uninterrupted cloud processing: free quotas, artifact limits, and provider policies can change.
- If the free quota is exhausted, pause until it resets or ask the user before proposing any paid alternative.

## Known limitations

- GitHub Actions runners are temporary; the workflow must explicitly download inputs and upload outputs.
- Private-repository Actions minutes and artifact storage are limited. The workflow should fail closed rather than incur overages.
- A static Pages site is not a secure media backend. Any authenticated upload/review API requires a separate security design.
- R2's free allowance is not a blanket guarantee against charges if usage exceeds the included limits.
- A phone browser can review outputs, but large source uploads may be slow or unreliable on mobile networks.

## Implementation order

1. Audit the repository's actual FFmpeg/Remotion capabilities, dependency versions, tests, and current Backlot routes.
2. Build a no-secret, no-media, mobile-first control/review prototype.
3. Add a manual GitHub Actions smoke-test workflow using generated color bars and a short silent sample, then verify an MP4 export.
4. Add approval gates and fail-closed quota/cost checks.
5. Evaluate private media transfer/storage. Only then request separate approval for any external account or bucket setup.
6. Run one user-supplied short video end-to-end after explicit approval of the test plan.


## Creative intelligence and competitor-analysis team

The studio must analyze both **paid advertisements and organic videos**, at a professional, timestamp-by-timestamp level. This is analysis of existing footage and public competitor examples, not AI video generation.

### Research inputs (free-first)

- Accept competitor video URLs, screenshots, ad-library links, and user-uploaded reference files.
- Use public discovery sources such as Meta Ad Library and TikTok Creative Center where content is publicly accessible.
- Respect each platform's terms, access controls, robots restrictions, and rate limits. Do not bypass login, paywalls, CAPTCHAs, geographic restrictions, or anti-bot protections.
- If a platform does not provide a lawful downloadable asset or accessible transcript, ask the user to provide the video file or capture; do not promise automatic extraction.
- Store source URL, platform, observed date, format, and research notes so that findings are traceable. Do not infer competitor spend, conversion rate, or sales from a creative alone.

### Analysis roles

1. **Competitor Research Analyst** — collect and categorize paid and organic examples, hooks, offers, formats, calls to action, and recurring creative patterns.
2. **Hook Analyst** — assess the opening frame, first spoken line, first visual change, curiosity, clarity, and time-to-value.
3. **Story & Retention Analyst** — map problem, tension, demonstration, proof, payoff, and CTA; identify slow or confusing sections.
4. **Visual Editor Analyst** — inspect shot changes, framing, legibility, product visibility, continuity, pacing, and aspect-ratio suitability.
5. **Audio Analyst** — inspect speech clarity, loudness consistency, clipping, noise, music/effects balance, and synchronization.
6. **Conversion & Platform Strategist** — assess audience fit, offer clarity, trust, objections, CTA, and platform-native conventions.
7. **Final QA Reviewer** — compare the edited cut against the approved brief and issue a prioritized fix list.

Claude Code orchestrates these roles and tools. They are bounded specialist workflows, not separate always-running paid agents.

### Required second-by-second report

For every supplied or accessible reference video, produce a timeline table with:

- start/end timestamp (to the nearest practical frame or 0.1 second where source precision allows);
- visible action and shot description;
- spoken words / on-screen text (only when available or reliably transcribed);
- purpose of the moment (hook, context, problem, demo, proof, objection handling, CTA, etc.);
- attention/retention risk and why;
- audio/visual technical observations;
- recommended edit, replacement, trim, or caption change.

Also produce an overall scorecard (0–100) with written evidence for:
- hook strength (0–3 seconds and opening sequence);
- message clarity;
- audience relevance;
- story structure and pacing;
- visual quality and product comprehension;
- voice/audio quality;
- proof and credibility;
- offer and CTA strength;
- platform fit.

Scores are editorial heuristics, not measured performance predictions. Never present them as actual retention, sales, ROAS, or conversion data. Label confidence and evidence gaps.

### Analysis pipeline (no paid AI required)

- Use FFprobe/FFmpeg for duration, frame rate, resolution, audio stream inspection, loudness checks, scene-change candidates, thumbnails, and timestamped frame extraction.
- Use local/open-source speech recognition only when it can run within the available free compute allowance; otherwise accept a user-provided transcript or mark speech as untranscribed. Do not silently call a paid transcription API.
- Use deterministic checks for technical QA and a structured human/Claude review for creative judgment.
- Generate contact sheets and timestamped review clips so the user can verify observations.
- Keep original media immutable; all cuts and derived files go into a separate project workspace.

### Approval workflow for competitor research and editing

1. User approves the target audience, product/category, platform, and competitor set.
2. Researcher presents sourced examples and evidence; user approves the references to analyze.
3. Analysts deliver the second-by-second report and prioritized recommendations.
4. User approves the creative direction and edit plan.
5. Editor creates a first cut from user-provided assets.
6. Analysts review the first cut and produce a timestamped correction list.
7. User approves each revision round and the final export.

### Important limitations

- Public ad libraries and creative-center pages do not expose every ad, every organic post, or private performance metrics.
- A public creative can be studied for structure and execution, but its actual business performance cannot be known without authorized analytics.
- Second-by-second semantic analysis may require a transcript or visual inspection; fully automated understanding cannot be guaranteed under a $0 compute budget.
- If the free runner cannot process the full source, split the job into smaller segments or ask the user to provide a lower-resolution review copy. Never trigger paid compute automatically.

## Explicit non-goals

- No video-generation models or avatar generation.
- No always-on cloud VM.
- No GPU worker.
- No paid hosting, paid storage, paid APIs, or automatic publishing.
