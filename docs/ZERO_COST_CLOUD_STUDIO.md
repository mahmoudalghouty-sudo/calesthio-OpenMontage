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

## Explicit non-goals

- No video-generation models or avatar generation.
- No always-on cloud VM.
- No GPU worker.
- No paid hosting, paid storage, paid APIs, or automatic publishing.
