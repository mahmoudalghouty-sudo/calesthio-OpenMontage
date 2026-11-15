# Cloud Studio Foundation

Status: architecture proposal and implementation guardrails
Target: private, cloud-hosted OpenMontage studio controlled from a phone
Approval model: human approval at every creative production gate
Repository: this fork of OpenMontage; do not replace it with a second editor project

## 1. Existing system we are preserving

OpenMontage is already an agent-first production system. Claude Code is the production director/orchestrator; Python provides registered production tools and durable project checkpoints. The repository already contains:

- pipeline manifests and stage-director skills;
- image, video, TTS, stock-media, subtitle, audio, and enhancement providers;
- Remotion / HyperFrames / FFmpeg composition paths;
- checkpoint history, decision logs, budget tracking, and post-render QA;
- Backlot, a read-only living storyboard for project review.

Do not add a second agent orchestrator or replace the existing pipeline system.

## 2. Non-negotiable approval contract

The human is the producer. The system must stop at each creative gate and wait for an explicit response before advancing.

Approval gates to preserve and verify across every enabled pipeline:

1. concept / proposal;
2. script and narration direction;
3. scene plan and visual direction;
4. generated/source assets (before a draft render);
5. edit decisions;
6. final composition / QA result;
7. publish/export action.

A prior approval never authorizes a later gate. Paid generation must show provider, model, estimated cost, and sample/batch scope before execution. Never silently change a provider, model family, render runtime, or creative direction. Keep the existing append-only decision log and checkpoint history.

Important implementation note: the checkpoint protocol treats each pipeline manifest's `human_approval_default` as binding. Do not assume the global `checkpoint.policy` setting overrides a manifest. Before enabling cloud production, audit all pipeline manifests and add tests proving the gates above are enforced.

## 3. Cloud architecture (first release)

Use a small, private, CPU-first deployment. AI image/video generation remains provider-API based at first; do not rent an always-on GPU. Add a GPU worker only after a real workload justifies its cost.

- **Control / agent:** Claude Code remains the human-facing production director. It reads this repository, follows the existing pipeline manifests and skills, and asks for approval in the user's conversation.
- **Execution runtime:** a Linux container with the repository, supported Python version, Node.js version from `.node-version`, FFmpeg, and Remotion/HyperFrames dependencies. It runs the existing tools and render commands; it does not invent a second orchestration engine.
- **Review UI:** Backlot remains the read-only storyboard. Its current server is intentionally loopback-only and allows only `127.0.0.1` / `localhost` Host headers. Never expose it directly to the public internet. Cloud access requires authentication in front of it (or an equivalent reviewed auth layer), HTTPS, an explicit host allowlist, and private media access.
- **Project state:** keep checkpoints, artifacts, decision logs, and project metadata on durable storage. A container's ephemeral filesystem is not acceptable for production state.
- **Media storage:** keep large uploads, generated assets, and final MP4s in private S3-compatible object storage. Use short-lived signed URLs for browser previews/downloads; never make the bucket public.
- **Job execution:** start with one bounded worker process and one active render per project. Add a queue only when the first end-to-end cloud test proves it is needed. Make render jobs resumable and idempotent so retries cannot double-submit paid generation.
- **Secrets:** store provider keys only in the hosting platform's secret manager/environment settings. Never commit `.env`, API keys, tokens, or signed URLs.
- **Observability:** capture job ID, project ID, stage, provider/model, estimated and settled cost, duration, retries, and failure reason. Do not log secrets or raw credentials.

## 4. Deployment decision

The codebase currently has a local Backlot board, not a complete authenticated multi-user cloud SaaS. Cloud deployment must therefore be private and single-owner first.

Recommended deployment shape:
- one private application/runtime service for OpenMontage + Backlot;
- durable project volume for checkpoints and working files;
- private object storage for media and final renders;
- optional separate worker/GPU service later.

Budget decision: hard ceiling USD $10/month, with a target operating cost of $0/month during the prototype. Do not create or activate paid resources without a separate explicit approval.

Selected zero-cost-first architecture:
- **Dashboard:** Cloudflare Pages static assets (Free).
- **Control API:** Cloudflare Workers Free, limited to authentication/session checks, project metadata, approval state, and dispatching jobs. Never run FFmpeg, Python video rendering, or AI inference inside a Worker.
- **Media storage:** Cloudflare R2 Standard private bucket, staying within the 10 GB-month and request free allowances.
- **Render execution:** GitHub Actions on the repository's included monthly minutes. Actions workers run bounded CPU jobs, use FFmpeg/Remotion where supported, and upload outputs to private R2. No always-on VM and no GPU.
- **Project metadata:** versioned JSON/checkpoint files in the repository for the initial prototype; move mutable metadata to a durable store only if required and after reviewing free-tier constraints.
- **Approval:** Claude Code remains the authoritative approval interface. A stage cannot advance until the user explicitly approves that stage. The dashboard may display status, but must not silently approve.
- **Private access:** Cloudflare Access or an equivalent reviewed single-owner authentication layer in front of the dashboard and API. Verify current free eligibility and exact setup before enabling public DNS.

Important limits:
- Workers Free has a 10 ms CPU limit per invocation and is only the lightweight control plane.
- GitHub Actions Free for private repositories includes 2,000 minutes/month; monitor usage and stop jobs before the quota is exhausted.
- R2 Free includes 10 GB-month Standard storage, 1 million Class A and 10 million Class B operations, with no egress fees.
- This stack can host the control plane and run limited CPU render jobs. It cannot promise always-on rendering, heavy AI inference, or GPU video generation at $0.
- If GitHub Actions minutes, R2 usage, or any other quota would exceed the free allowance, pause and request approval; never allow automatic overage.

No paid cloud resources, subscriptions, Workers Paid plan, GPU instances, or paid generation providers are authorized by this decision.

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
- Add cost preflight and hard budget caps before enabling paid generation.
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

Complete Phase 0 against the current fork. The cloud host and budget are now selected: Cloudflare Free + GitHub Actions Free, target $0/month and hard cap $10/month. Next implement the static dashboard/control API and private R2 integration in a test-only branch; do not provision paid services or enable paid generation.
