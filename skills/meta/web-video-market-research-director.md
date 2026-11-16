# Web Video Market Research Director — No Reference Required

## Purpose

This is the default discovery workflow when the user wants a marketing video, product ad, competitor analysis, or niche research but has **not** supplied a reference video. The agent must discover public internet examples itself. A user-uploaded video is optional and must never be requested merely to make research possible.

## Inputs

Use, in order:
1. The current user brief (product, category, problem, offer, audience, objective).
2. The active project/studio profile and any explicit brand/product context already available.
3. The default market and platform settings in `studio_profile.yaml`.

If the product/category is genuinely unknown and cannot be inferred from the active project, ask one concise essential question. Do not ask for a reference video.

## Research scope

Research both paid and organic creative:
- Meta Ad Library for publicly searchable Facebook/Instagram ads.
- TikTok Creative Center for publicly exposed creative examples and trend information.
- Public YouTube videos and Shorts.
- Public Instagram and Facebook video pages/posts when accessible without login or access-control bypass.
- Other reputable public sources only when they add directly relevant evidence.

Search several intent angles, not just the exact product name:
- product/category name and common synonyms;
- customer problem and pain-point phrases;
- use cases and demonstrations;
- competitor/alternative product terms;
- audience-specific language in the target market;
- organic-content and paid-ad variants.

Prioritize target-market relevance (default UK), recency where visible, relevance to the same customer problem, and diversity of creative approaches. Record search date and query terms.

## Access and evidence rules

- Use only a research/search/browser capability actually available in the current Claude Code runtime. Discover available tools first; do not assume a browser, search API, downloader, or platform connector exists.
- Do not bypass login, paywalls, CAPTCHAs, geographic restrictions, robots restrictions, anti-bot controls, rate limits, or platform terms.
- Do not scrape private content or use undocumented endpoints to evade restrictions.
- Do not download competitor videos for production reuse. Competitor media is research material only.
- Record for every result: title/description where visible, platform, creator/advertiser where visible, source URL, observed/publication date where available, format, visible engagement indicators, and access level.
- Classify access level as one of: `video_inspected`, `audio_or_transcript_only`, `thumbnail_and_metadata_only`, or `listing_only`.
- Never claim to have watched a video unless actual frames/video were inspected. Never claim second-by-second analysis unless the actual media was available and sampled.
- If only metadata is available, analyze positioning/copy/offer at metadata level and clearly mark visual/audio analysis unavailable.
- Public engagement counts are descriptive signals only. Never infer sales, conversion rate, ROAS, ad spend, profitability, or causal success from views/likes/comments.
- Keep direct observations, editorial judgments, and hypotheses in separate fields.

## Video inspection and second-by-second analysis

For each video that is genuinely accessible:
1. Obtain it through an allowed public viewing/download path, respecting platform terms.
2. Inspect metadata, duration, dimensions, frame rate, and audio streams.
3. Use local FFmpeg/FFprobe and available local analysis tools for scene boundaries, frame sampling/contact sheets, audio loudness, silence, and speech/transcript extraction where free dependencies allow.
4. Inspect the opening 0–3 seconds closely and sample the remaining timeline at scene changes and approximately once per second where compute allows.
5. Build a timeline with timestamp, visible action, verified spoken words/on-screen text, narrative role, hook/retention function, edit observations, risks, recommendation, confidence, and evidence.
6. If only sparse frames can be inspected, disclose sampling density and do not imply frame-by-frame coverage.

Score creative quality as an editorial heuristic, not a performance prediction. Evaluate hook, clarity, audience relevance, story/pacing, demonstration, proof, trust, audio/captions, offer, CTA, and platform fit. Give evidence and confidence for every score.

## Synthesis

After collecting a useful sample:
- Group examples by hook type, problem framing, demonstration style, proof, offer, objections, CTA, visual format, pacing, and organic/paid purpose.
- Identify repeated patterns and underused angles.
- Explain what can be learned strategically without copying protected expression.
- Distinguish patterns supported by multiple examples from one-off observations.
- State sample size, date window, source coverage, and any access gaps. If few sources were accessible, call the result a limited scan, not a comprehensive market study.

## Original production handoff

Create an original creative brief:
- target audience and customer problem;
- one selected strategic angle and why;
- original hook and script;
- shot-by-shot plan and timing;
- captions and CTA;
- evidence supporting the strategy;
- claims requiring substantiation;
- asset queries for visuals not otherwise available.

Never copy competitor scripts, footage, logos, watermarks, distinctive characters, or shot-for-shot sequences. Use only user-authorized or properly licensed production assets. Competitor media must not be placed in the render timeline.

Use the existing pipeline and zero-cost safeguards. Research must remain isolated from `editing_only`; asset downloads must use the separate allowlisted `asset_acquisition` profile and explicit commercial-safe license checks. Do not weaken network restrictions or invoke paid APIs, GPU, paid TTS, or metered services.

## Deliverables

Return:
1. Research summary with search date and query coverage.
2. Source table with direct links and access-level labels.
3. Competitor creative-pattern comparison (paid vs organic).
4. Timestamped analysis for each video actually inspected.
5. Editorial scorecards with evidence/confidence and explicit caveat that scores are not sales predictions.
6. Original concept, script, shot plan, captions, CTA, and production decisions.
7. Final video and technical QC report if the available production path succeeds.
8. Explicit list of unavailable sources, inaccessible media, and remaining limitations.

## Autonomy

Choose the strongest original direction autonomously within the user's approved zero-cost creative profile. Do not stop for routine choices. Ask only for an essential missing product/offer fact or a material rights/safety ambiguity. Never ask the user to send a reference video as a prerequisite.
