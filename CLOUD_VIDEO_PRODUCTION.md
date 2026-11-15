# Phone-to-Cloud Video Production

This workflow is an isolated, free-tier cloud render path for the `cloud-transfer-roundtrip` branch. It does not change or merge `main`.

## What it does

1. Accepts a source-video ID from tmp0.cc.
2. Requires that the source is marked `clientEncrypted=true`.
3. Downloads and decrypts the video only inside an ephemeral GitHub-hosted runner.
4. Uses OpenMontage `VideoCompose` in `OPENMONTAGE_PROFILE=editing_only`.
5. Supports sequential cuts, optional SRT subtitle burn-in, and platform output profiles.
6. Encrypts the rendered MP4 with the same client-side Argon2id/AES-256-GCM password before sending it to tmp0.cc.
7. Returns a temporary download URL in the GitHub Actions run summary.

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
5. Set source expiry to one hour, then upload.
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

The first cloud path supports cuts, subtitle burn-in, and output formatting. It does not yet provide the planned deep second-by-second marketing analysis, competitor research, or full studio interface. Do not describe those features as complete.

## Trigger and retrieve the result

- Push the request file to branch `cloud-transfer-roundtrip`. The **Phone Video Production** workflow starts automatically.
- Claude Code should monitor the run until it finishes and read the **Summary** section.
- Open the encrypted result link from the run summary in the phone browser and enter the same password.
- Output links expire after 24 hours and allow up to three downloads.

## Synthetic test

The checked-in request used for validation has `"test_mode": true`. It creates synthetic media on the runner, renders a vertical MP4 through OpenMontage, uploads the result encrypted, downloads it again, and compares exact SHA-256 hashes. It does not require the password secret and does not use personal media.

Before switching to a real file, the synthetic production workflow must pass. The initial source-transfer proof is separate and also must pass.

## Safety and cost boundaries

- Use only standard `ubuntu-24.04` GitHub-hosted runners; no paid runner labels or GPU services.
- Keep `OPENMONTAGE_PROFILE=editing_only`. No paid APIs, generation providers, publishing integrations, or silent fallbacks.
- Source and final media must remain client-encrypted while stored on tmp0.cc.
- Real jobs must never upload media as GitHub artifacts.
- Source upload limit for this first version: 500 MB; maximum duration: 30 minutes.
- tmp0.cc is temporary storage, not a permanent library; it keeps no backups and offers no guaranteed uptime. Browser-based E2EE depends on the JavaScript served by tmp0.cc, so do not use this path for highly sensitive footage.
- If any encryption, metadata, render, or hash check fails, stop and report the exact blocker. Never ask for a real video as a workaround.
