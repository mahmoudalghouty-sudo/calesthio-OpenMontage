# Phone-to-Cloud Video Production

This workflow is an isolated, free-tier cloud render path for the `cloud-transfer-roundtrip` branch. It does not change or merge `main`.

## What it does

1. Accepts a source-video ID from tmp0.cc.
2. Requires that the source is marked `clientEncrypted=true`.
3. Downloads and decrypts the video only inside an ephemeral GitHub-hosted runner.
4. Uses OpenMontage `VideoCompose` in `OPENMONTAGE_PROFILE=editing_only`.
5. Supports mixed reference/stock timelines, optional SRT subtitle burn-in, and platform output profiles.
6. Optionally searches and downloads a small set of supplementary stock clips in a separate `asset_acquisition` profile, with a strict no-key provider allowlist and conservative commercial-use metadata filtering.
7. Renders only in the locked-down `editing_only` profile and records stock provenance, source URLs, licence labels, and SHA-256 hashes in the render report.
8. Encrypts the rendered MP4 with the same client-side Argon2id/AES-256-GCM password before sending it to tmp0.cc.
9. Returns a temporary download URL in the GitHub Actions run summary.

Real production jobs do **not** upload source videos, decrypted videos, final videos, or reports as GitHub artifacts. The runner is ephemeral. Only synthetic test output is uploaded as a short-lived artifact.

## One-time private key setup

The repository is public, so never commit a password or media file.

1. Generate a long random password in a password manager (at least 32 random characters). Save it privately; you will need it when uploading and downloading through tmp0.cc.
2. In the GitHub repository, open **Settings → Secrets and variables → Actions → New repository secret**.
3. Name the secret exactly `TMP0_E2EE_PASSWORD` and paste the random password as its value.
4. Do not send this password to Claude Code, ChatGPT, issues, commits, request JSON, or workflow inputs.

GitHub Actions reads the secret only at runtime. It is not placed in the repository or printed in logs. Reuse this password for the source upload and the final download. If you rotate it, update the GitHub secret and use the new password for subsequent uploads.

## Uploading from an Android phone

1. Open [tmp0.cc](https://tmp0.cc) in the phone browser.
2. Select the source video.
3. Rename the video to a neutral filename such as `source.mp4` first; tmp0 stores the filename as readable metadata even when the video contents are encrypted.
4. Enable password/client-side encryption and enter the exact password stored in `TMP0_E2EE_PASSWORD`. The website and CLI use the same Argon2id + AES-256-GCM format.
5. Set source expiry to one day and, if offered, allow three downloads; this gives the cloud job time to start and leaves room for a retry.
6. Copy the file ID shown by the service. The file ID is not the password; without the password, the ciphertext cannot be decrypted.

Do not use a normal, unencrypted upload. Do not upload any personal video until the synthetic production test has passed.

## Request format

Claude Code writes only this small JSON request to `jobs/requests/next.json`, commits it to `cloud-transfer-roundtrip`, and pushes. Never commit media, passwords, keys, or private assets.

```json
{
  "project_id": "my-first-reel",
  "file_id": "THE_TMP0_FILE_ID",
  "output_profile": "instagram_reels",
  "cuts": [
    { "in_seconds": 0, "out_seconds": 12 },
    { "in_seconds": 15, "out_seconds": 28 }
  ],
  "subtitles_srt": "1\n00:00:00,000 --> 00:00:02,500\nYour opening hook\n"
}
```

- `project_id`: 2–48 lowercase letters, numbers, and hyphens.
- `file_id`: the ID from tmp0.cc.
- `output_profile`: `instagram_reels`, `instagram_feed`, `youtube_shorts`, `youtube_landscape`, or `tiktok`.
- `cuts`: optional; if omitted, the entire source is used. Each cut has `in_seconds`, `out_seconds`, and optional `speed` (0.5–2.0).
- `subtitles_srt`: optional timed captions. This text is committed to a public repository, so include only copy that is safe to be public.

The cloud path now supports optional stock acquisition in a separate allowlisted profile and mixed-media timelines in the render job. The checked-in request remains a synthetic test fixture; Claude Code must create a real per-video request with the uploaded tmp0 file ID, an original timeline, captions, and optional `asset_queries`. The cloud runner performs deterministic technical validation, timestamped black/freeze/silence detection, and stock provenance reporting. Black/freeze/silence detections are review warnings, not automatic failures, because some pauses and fades may be intentional. It does not itself run an LLM for second-by-second creative interpretation or discover competitor ads. Those intelligence stages must be performed by Claude Code using an available public read-only web research capability before it writes the request; if that capability is unavailable, it must label competitor research as not performed rather than inventing evidence. A full graphical studio interface and fully automated visual-semantic QC/repair loop are not yet implemented.

## Autonomous reference-video request fields

Claude Code should prepare the request after inspecting the uploaded reference. In addition to the required `project_id`, `file_id`, and `output_profile`, the request may include:

- `asset_queries`: up to 12 short, shot-specific search queries. Each entry is an object with `query` and optional `slot_id`. The cloud acquisition step uses no-key sources from the allowlist (`archive_org`, `loc`, `noaa`, `wikimedia`) and rejects ambiguous, NC, ND, caveated, or missing licence metadata.
- `timeline`: 1–100 ordered segments. A reference segment is `{"source":"reference","in_seconds":0,"out_seconds":5}`. A stock segment may refer to an acquired asset by ID (`{"asset_id":"<asset_id>","in_seconds":0,"out_seconds":4}`) or by its predeclared slot (`{"source":"stock","slot_id":"dog_grooming_broll","in_seconds":0,"out_seconds":4}`). Slot IDs are resolved against the stock manifest after acquisition. Only acquired manifest assets are accepted; arbitrary file paths and remote URLs are rejected.
- `subtitles_srt`: optional original captions prepared by the agent. Do not put secrets or private personal information in the public request JSON.

Stock clips are downloaded into the ephemeral runner and are not uploaded as GitHub artifacts or committed. Their provenance and checksums are included in `render-report.json`.

## Trigger and retrieve the result

- Push the request file to branch `cloud-transfer-roundtrip`. The **Phone Video Production** workflow starts automatically.
- Claude Code should monitor the run until it finishes and read the **Summary** section.
- Open the encrypted result link from the run summary in the phone browser and enter the same password.
- Output links expire after 24 hours and allow up to three downloads.

## Synthetic test

The checked-in request used for the latest validation has `"test_mode": "secret_e2ee"`. It creates synthetic media, encrypts and uploads it to tmp0.cc using the repository secret, downloads and decrypts it on the runner, renders a vertical MP4 through OpenMontage, encrypts and uploads the result, downloads it again, and compares exact SHA-256 hashes. It uses no personal media. The verified run is [43814455390](https://github.com/mahmoudalghouty-sudo/calesthio-OpenMontage/actions/runs/43814455390).

Before switching to a real file, the synthetic production workflow must pass. The initial source-transfer proof is separate and also must pass.

## Safety and cost boundaries

- Use only standard `ubuntu-24.04` GitHub-hosted runners; no paid runner labels or GPU services.
- Keep `OPENMONTAGE_PROFILE=editing_only`. No paid APIs, generation providers, publishing integrations, or silent fallbacks.
- Source and final media must remain client-encrypted while stored on tmp0.cc.
- Real jobs must never upload media as GitHub artifacts.
- Source upload limit for this first version: 500 MB; maximum duration: 30 minutes.
- tmp0.cc is temporary storage, not a permanent library; it keeps no backups and offers no guaranteed uptime. Browser-based E2EE depends on the JavaScript served by tmp0.cc, so do not use this path for highly sensitive footage.
- If any encryption, metadata, render, or hash check fails, stop and report the exact blocker. Never ask for a real video as a workaround.

## Latest verified result

Latest secret-backed synthetic end-to-end run: [GitHub Actions run 43814455390](https://github.com/mahmoudalghouty-sudo/calesthio-OpenMontage/actions/runs/43814455390) — success.

- Synthetic source uploaded to tmp0.cc with client-side encryption, then downloaded/decrypted on the runner.
- Source SHA-256 matched exactly after encrypted transfer.
- Two cuts and SRT captions were rendered by OpenMontage `VideoCompose`.
- Output verified as 1080×1920, 30 fps, H.264 video + AAC audio; duration 4.533 seconds.
- Output was uploaded encrypted, downloaded/decrypted, and its SHA-256 matched exactly.
- Only synthetic output was retained as a one-day GitHub artifact.

**Not yet tested:** the actual Android browser upload and download, and a real user video. The repository secret `TMP0_E2EE_PASSWORD` has been configured and the secret-backed CLI round-trip has passed. The remaining manual check is a browser upload from Android and download of the encrypted result before using longer or important footage.
