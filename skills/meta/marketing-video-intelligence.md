# Marketing Video Intelligence — Organic + Paid

Use this workflow whenever the user asks to audit, improve, compare, or produce a marketing video for organic social or paid ads. It is an analysis/editing workflow, not an instruction to buy media, scrape restricted platforms, or call paid generation APIs.

## Operating profile

- Keep `OPENMONTAGE_PROFILE=editing_only`.
- Use user-supplied footage and accessible public references only.
- Do not invoke metered transcription, image, video, voice, music, analytics, or publishing APIs.
- Do not claim that an ad performed well based on creative appearance, views, likes, or public library presence. Actual CTR, retention, CPA, ROAS, conversion and sales require authorized account analytics.
- Never bypass login, CAPTCHA, paywalls, anti-bot controls, platform access controls, or terms. If an example cannot be lawfully viewed/downloaded, ask the user to provide the video or a screen recording.
- Keep the original media immutable. Derived media and reports go into the project workspace.

## Inputs and framing

Before analysis, establish:
1. Platform and format (e.g. Instagram Reels, TikTok, YouTube Shorts, feed ad).
2. Organic or paid objective.
3. Target audience, product/service, market, and intended CTA.
4. Video source and whether the user has rights to use it.
5. Any supplied transcript, offer details, landing page, or campaign brief.

If a detail is unknown, label it unknown; do not fabricate it.

## Evidence collection

1. Read `skills/meta/video-reference-analyst.md` for reference videos and `tools/analysis/video_analyzer.py` for local analysis capabilities.
2. Run `video_analyzer` on a local file with `analysis_depth=deep` when dependencies and CPU budget allow. If transcription dependencies are unavailable or would require an unapproved external service, continue with scene/audio/visual evidence and mark narration as untranscribed.
3. Inspect source metadata with FFprobe: duration, dimensions, frame rate, codecs, audio streams.
4. Extract scene boundaries and contact sheets. For short-form marketing, inspect the opening 0–3 seconds closely and sample at each scene change plus approximately one frame per second where feasible.
5. Inspect audio loudness, clipping, silence, speech clarity, and synchronization using local FFmpeg tools.
6. Inspect captions and on-screen text for readability, safe-area placement, spelling, timing, contrast, and mobile legibility.
7. For competitor research, use public sources such as Meta Ad Library and TikTok Creative Center only where the material is accessible without bypass. Record source URL, platform, observed date, creative format, visible copy, offer and CTA. Separate observed facts from interpretation.

## Required second-by-second report

Create `projects/<project>/artifacts/marketing_video_audit.md` and structured JSON alongside it. Cover every second of the video; use finer intervals at scene changes or rapid action. Each interval must include:

- timestamp start–end;
- visible action / shot / product visibility (from inspected frames);
- spoken line and on-screen text (only if verified);
- narrative purpose: hook, context, pain point, demonstration, proof, objection handling, offer, CTA, transition, or filler;
- attention risk, with a concrete reason;
- audio/visual technical observations;
- recommended edit: keep, trim, reorder, replace, add caption, add proof, improve audio, or clarify CTA;
- evidence source and confidence (high / medium / low).

Never invent spoken words or claim to have visually inspected frames that were not opened. If analysis sampling is sparse, say so.

## Scorecard (heuristic, not performance prediction)

Score 0–100 with written evidence and confidence:
- hook and time-to-value (20);
- message clarity and audience relevance (15);
- story, pacing and retention design (15);
- product/service comprehension and demonstration (10);
- visual craft and continuity (10);
- audio and caption quality (10);
- proof, trust and objection handling (10);
- offer, CTA and platform fit (10).

For each category, explain what was observed and what would raise the score. Label the score as an editorial heuristic, not a measured retention or conversion result.

## Organic vs paid evaluation

- Organic: prioritize native storytelling, share/save value, clarity without assuming prior intent, authentic demonstration, and a natural CTA.
- Paid: prioritize immediate product/audience clarity, problem-solution demonstration, evidence, objection handling, offer, and a single clear action. Flag claims that need substantiation and avoid deceptive scarcity, fake testimonials, or unsupported guarantees.
- Do not reuse an organic edit for paid media without checking offer, disclosures, rights, claims, aspect ratio, safe areas, and CTA.

## Competitor comparison

Compare only verified accessible creatives. For each one, record source URL/date, opening hook, structure, pacing, demonstration, proof, offer, CTA, production choices, and what can be adapted ethically. Identify repeated patterns across examples, but do not infer competitor budgets, targeting, sales, or campaign results without authorized data.

## Deliverables and approval

Return:
1. executive diagnosis (three strongest points and three biggest blockers);
2. full timestamped timeline;
3. scorecard with evidence/confidence;
4. prioritized edit list (must-fix, should-fix, optional);
5. competitor pattern table when references were supplied;
6. revised edit decision list for user approval;
7. technical QA results after render.

Stop for explicit user approval before changing the creative direction, rendering a revision, or publishing/exporting. The user must approve the final export separately.
