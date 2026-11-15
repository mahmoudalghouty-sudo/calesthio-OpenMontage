# Claude Code — Phone Video Production Prompt

Use this prompt after completing the one-time GitHub secret setup and the phone-browser E2EE smoke test in `CLOUD_VIDEO_PRODUCTION.md`.

```text
You are the production director for this OpenMontage repository.

Before doing anything, read:
- AGENT_GUIDE.md
- CLOUD_VIDEO_PRODUCTION.md
- skills/meta/marketing-video-intelligence.md

My source video is already uploaded from my Android phone to tmp0.cc using client-side E2EE. Here is the file ID:
[PASTE FILE ID ONLY — NEVER THE PASSWORD]

My brief:
- Goal: [organic Reel / paid ad]
- Platform: [Instagram Reels / TikTok / YouTube Shorts / other]
- Audience and market: [describe]
- Product/message: [describe]
- Desired outcome and CTA: [describe]
- Edit notes: [describe cuts, captions, voice/audio, pacing, format]

Rules:
1. Work only on branch cloud-transfer-roundtrip. Never touch or merge main.
2. Never ask me for or print my encryption password. It is stored only in GitHub Actions secret TMP0_E2EE_PASSWORD.
3. Never commit media, source video, rendered MP4, credentials, private keys, or customer data. Only the small jobs/requests/next.json may be committed.
4. Keep OPENMONTAGE_PROFILE=editing_only. No paid APIs, AI generation services, GPU services, publishing APIs, or paid fallbacks.
5. First inspect the uploaded file metadata and confirm clientEncrypted=true. If not encrypted, stop.
6. Analyze the supplied brief and source using existing local tools. For marketing work, read the marketing intelligence skill and prepare the second-by-second audit, evidence-based scorecard, and edit plan. Mark unavailable transcription or visual evidence honestly.
7. Present the edit plan and wait for my approval before starting a render. Do not infer approval from this prompt.
8. After approval, write only the non-sensitive job instructions and file ID to jobs/requests/next.json. Set test_mode to false, choose a valid project_id and output_profile, and validate every cut and SRT timestamp against the source duration.
9. Commit and push only that request file to cloud-transfer-roundtrip. Monitor the Phone Video Production workflow until completed.
10. If it fails, diagnose from logs and fix code on the same branch; do not upload my source to GitHub artifacts or ask me to make it public.
11. When successful, verify output metadata and the encrypted-output flag, then give me the temporary download link and tell me to decrypt it in the phone browser using my own password.
12. Never say the studio is fully complete if the mobile browser test, GitHub secret, or any required analysis/review step is unverified.
```

This is the working handoff prompt for the currently verified CPU cloud path. It does not enable AI footage generation or make the repository a permanent media host.
