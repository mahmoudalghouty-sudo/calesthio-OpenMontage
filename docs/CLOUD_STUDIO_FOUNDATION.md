# Cloud Studio Foundation

Status: architecture proposal and implementation guardrails
Target: private, cloud-hosted OpenMontage studio controlled from a phone
Approval model: autonomous creative/editing decisions inside the approved $0 scope; explicit approval for paid, publishing, or irreversible external actions
Repository: this fork of OpenMontage; do not replace it with a second editor project

## 1. Existing system we are preserving

OpenMontage is already an agent-first production system. Claude Code is the production director/orchestrator; Python provides registered production tools and durable project checkpoints. The repository already contains:

- pipeline manifests and stage-director skills;
- image, video, TTS, stock-media, subtitle, audio, and enhancement providers;
- Remotion / HyperFrames / FFmpeg composition paths;
- checkpoint history, decision logs, budget tracking, and post-render QA;
- Backlot, a read-only living storyboard for project review.

Do not add a second agent orchestrator or replace the existing pipeline system.

## 2. Autonomy and approval contract

For this user's reference-video workflow, Claude Code is the production director and should autonomously complete routine research, script, shot planning, edit decisions, rendering, and technical QA inside the approved zero-cost scope. Read `studio_profile.yaml` before starting and use the reference-analysis override in `skills/meta/video-reference-analyst.md`.

Do not stop for approval at every creative stage or ask the user to select among routine variants. Record meaningful decisions in the append-only decision log and explain them in the delivery report.

Explicit user approval remains mandatory before:
1. any paid service, paid API, GPU, storage, or runner overage;
2. publishing or scheduling content to a public social account;
3. changing account/security settings or adding a payment method;
4. using media with unclear or restricted rights;
5. irreversible deletion or an action outside the configured project scope.

The $0 budget cap is hard. Paid generation is disabled and out of scope. Never silently change a provider, model family, or render runtime to a paid option. Keep the existing append-only decision log and checkpoint history.

Important implementation note: the checkpoint protocol treats each pipeline manifest's `human_approval_default` as binding. The reference-video override must be respected by the agent; do not assume a global checkpoint setting overrides pipeline manifests. Any pipeline invoked for this workflow must be configured or orchestrated so routine creative checkpoints do not contradict the user's autonomous-production instruction.

## 3. Cloud architecture (first release)

Use a small, private, CPU-first deployment. AI image/video generation is out of scope for this studio. Do not configure provider APIs or rent a GPU for video generation.

- **Control / agent:** Claude Code remains the human-facing production director. It reads this repository, follows the existing pipeline manifests and skills, and asks for approval in the user's conversation.
- **Execution runtime:** a Linux container with the repository, supported Python version, Node.js version from `.node-version`, FFmpeg, and Remotion/HyperFrames dependencies. It runs the existing tools and render commands; it does not invent a second orchestration engine.
- **Review UI:** Backlot remains the read-only storyboard. Its current server is intentionally loopback-only and allows only `127.0.0.1` / `localhost` Host headers. Never expose it directly to the public internet. Cloud access requires authentication in front of it (or an equivalent reviewed auth layer), HTTPS, an explicit host allowlist, and private media access.
- **Project state:** keep checkpoints, artifacts, decision logs, and project metadata on durable storage. A container's ephemeral filesystem is not acceptable for production state.
- **Media storage:** keep large uploads, generated assets, and final MP4s in private S3-compatible object storage. Use short-lived signed URLs for browser previews/downloads; never make the bucket public.
- **Job execution:** start with one bounded worker process and one active render per project. Add a queue only when the first end-to-end cloud test proves it is needed. Make render jobs resumable and idempotent so retries cannot double-submit paid generation.
- **Secrets:** store provider keys only in the hosting platform's secret manager/environment settings. Never commit `.env`, API keys, tokens, or signed URLs.
- **Observability:** capture job ID, project ID, stage, provider/model, estimated and settled cost, duration, retries, and failure reason. Do not log secrets or raw credentials.

## 4. Deployment decision — strict $0/month architecture

The user has explicitly set a hard maximum of USD $0/month and prohibited paid activation without approval. Treat this as a hard budget cap, not a target with overages allowed.

### Approved zero-cost architecture (design only; no accounts/services provisioned)

- **Static control panel:** Cloudflare Pages Free. Host only the phone-friendly studio dashboard/static frontend. Pages Free currently permits 500 builds/month, 20,000 files/site, and 25 MiB per asset. Keep all media out of Pages assets.
- **Small control/API layer:** Cloudflare Workers Free, only for lightweight authenticated project metadata and signed upload/download coordination. Current Free limits include 100,000 requests/day and 10 ms CPU time per invocation. This is not a video-rendering runtime.
- **Metadata database:** Cloudflare D1 Free for project state, approvals, stage status, and small audit metadata. Keep large files out of D1. Confirm current D1 free limits at account setup.
- **Media object storage:** Cloudflare R2 Standard Free allowance: 10 GB-month storage, 1 million Class A operations/month, 10 million Class B operations/month, and no egress charge. Enforce an application-level storage quota below 10 GB (recommended 8 GB) and refuse uploads when near quota. R2 is usage-billed beyond the allowance, so do not enable it unless the dashboard can monitor usage and the account can enforce/alert on limits. No public bucket.
- **Source of truth / code:** existing GitHub repository and pull requests. Keep video binaries and generated assets out of Git.
- **Build/test automation:** GitHub Actions only for small lint/contract tests and deployment of static assets. GitHub Free includes limited private-repo compute/storage; never assume unlimited free minutes. Do not run FFmpeg or AI generation in Actions by default.
- **Agent / orchestration:** Claude Code remains the director and calls the existing OpenMontage tools where available. It is not an always-on free cloud daemon; the user starts a production session and approves each gate.
- **Rendering:** No guaranteed always-on cloud renderer is available under the $0 cap. First release supports project planning, approvals, asset management, and review UI in the cloud. Actual FFmpeg/Remotion rendering must run on a user-controlled computer/device or on a temporary free compute allowance only after verifying its limits. Do not claim fully cloud-rendered production until a free render worker is proven.
- **AI media providers:** disabled by default. Use only local/free-tier models or explicitly approved providers with a confirmed $0 price. Never call a metered endpoint on the assumption it is free.
- **Authentication:** use Cloudflare Access only if the chosen account's current free allowance covers the intended single-user setup; otherwise implement a reviewed single-owner authentication layer using Workers/D1. Do not publish Backlot or media unauthenticated.
- **No paid fallback:** no automatic upgrade, no card-backed overage, no paid GPU, no Render paid service, no Modal, no paid database, and no paid custom domain.

### Cost guardrails

1. The deployment must remain on free plans and must not activate paid plans.
2. Set provider/account spending limits to $0 where supported; disable automatic paid upgrades and usage overages.
3. If a service requires a payment method or cannot guarantee a hard $0 cap, pause and ask the user before connecting it.
4. Display an estimated cost before every AI generation, upload, or render operation. If the cost is unknown, block the operation.
5. Keep R2 usage under 8 GB and monitor operations; stop uploads before exceeding free allowances.
6. Never store user videos permanently by default. Offer cleanup/export and retention controls.
7. No paid service, account, bucket, domain, worker, GPU, or deployment has been created by this plan.

### Free-tier limitations (must be explicit in the UI)

- Cloudflare Workers Free's 10 ms CPU limit is for lightweight API requests, not video encoding or AI inference.
- R2's free tier is capped; usage beyond included amounts can be billed.
- GitHub Actions private-repository minutes/storage are limited.
- Static hosting does not provide a persistent Python process, durable FFmpeg worker, or unlimited storage.
- Free AI endpoints may have queues, rate limits, model changes, or no commercial-use rights.

## 5. Implementation phases and acceptance criteria

### Phase 0 — repository and capability audit
- Verify Python, Node, FFmpeg, Remotion/HyperFrames versions and existing CI.
- Audit every pipeline manifest for approval gates.
- Run registry discovery and contract tests.
- Identify which tools can run in a CPU container and which require external API keys or GPU.

Acceptance: a capability matrix and a passing baseline test report; no production secrets required.

### Phase 1 — approval and security hardening
- Add a cloud approval profile that gates all creative stages.
- Add tests for gate enforcement and approval-per-stage behavior.
- Add authenticated access for Backlot before any public hostname is enabled.
- Preserve Backlot's read-only behavior; do not add unauthenticated write routes.

Acceptance: unauthenticated requests are rejected; approved users can view a project; no project/media path traversal; each creative gate blocks the next stage until approved.

### Phase 2 — containerized execution
- Add a reproducible Linux Docker image for the existing runtime.
- Include health checks and a safe, non-root runtime user.
- Keep API providers opt-in and support a no-paid-keys smoke test.
- Add a small test render using generated/local placeholder assets.

Acceptance: clean container build, health check passes, test render exports a valid MP4, and restart does not lose project state.

### Phase 3 — durable cloud media
- Add private object-storage adapter for uploads, previews, and final renders.
- Keep project JSON/checkpoints durable and versioned.
- Add signed preview/download URLs and expiry.

Acceptance: source media and final MP4 survive container restart; URLs expire; bucket remains private.

### Phase 4 — private deployment and phone review
- Deploy the application behind authenticated HTTPS.
- Connect Backlot to the durable project workspace.
- Verify the user can review the storyboard and final video from a mobile browser.
- Keep production approval in Claude Code until an authenticated approval UI is separately tested.

Acceptance: private mobile access works; no unauthenticated access to projects, assets, or renders.

### Phase 5 — production reliability
- Add a durable queue only if needed, retry/backoff rules, job cancellation, and idempotency.
- Keep paid generation disabled. Preserve the hard zero-dollar budget guard for any future separately approved operation.
- Add backups and a documented restore test.

Acceptance: interrupted jobs can resume without duplicate paid submissions; restore test succeeds.

## 6. Safety and cost rules

- No cloud resource creation or paid service activation without the user's explicit approval.
- No paid generation call without a visible cost estimate and explicit approval.
- No public Backlot endpoint without authentication and HTTPS.
- No secrets in Git.
- No GPU by default.
- No automatic publishing. Export is a separate human-approved gate.
- If a provider's cost cannot be estimated, stop and ask before calling it.

## 7. Immediate next step

Complete Phase 0 against the current fork. The selected target is strict $0/month. Next complete the repository capability audit and run a no-paid-API render smoke test. Do not provision Cloudflare resources, create an R2 bucket, attach a payment method, or enable paid generation without separate explicit approval.
