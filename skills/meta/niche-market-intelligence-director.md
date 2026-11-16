# Niche Market Intelligence and Original Adaptation

This workflow is triggered when a user supplies a reference video and gives no further instructions, or says only that they want a version for the same niche.

## Default intent

Treat the supplied video as a creative and market reference, not as footage to copy. The default deliverable is an original, platform-ready adaptation informed by evidence about the niche and comparable public content.

## Autonomous workflow

1. **Inspect the reference locally**
   - Run `video_analyzer` at deep analysis depth on the supplied local file.
   - Extract transcript, scene boundaries, representative frames, on-screen text, audio characteristics, pacing, hook, narrative structure, product/problem, emotional triggers, proof, objections, and CTA.
   - Build a timestamped analysis. Distinguish observations from interpretations.

2. **Classify the niche and offer**
   - Identify the specific sub-niche (for example dog grooming, separation anxiety, walking, feeding, training, dental care, enrichment, or travel).
   - Identify the problem, proposed solution, likely buyer, awareness level, and purchase context.
   - If product identity or claims are uncertain, do not invent them. Mark uncertainty and avoid unsupported product claims.

3. **Research the market using public evidence**
   - Use a separate, explicitly enabled, read-only research capability/profile. Do not weaken the zero-cost editing-only guard or silently enable network access in an editing job.
   - Search public competitor ads and organic videos for the same problem, product category, audience, and platform. Prefer primary public sources and recent examples.
   - Record URLs, dates where available, visible engagement signals, creative patterns, repeated hooks, offers, objections, and gaps.
   - Treat views/likes/comments as observable signals, not proof of conversion or causal success. Never claim an ad is profitable or a video converted unless reliable evidence supports it.
   - If public access is blocked, return a clearly labelled limited analysis rather than fabricating competitor findings.
   - Do not claim that a separate research profile exists unless the current runtime actually exposes and permits it. Do not scrape sites against their terms or use competitor media as production assets.

4. **Explain why the reference may work**
   - Separate directly observed creative mechanics from hypotheses about audience psychology.
   - Evaluate the opening hook, first-frame clarity, time-to-value, pacing, scene changes, visual proof, emotional arc, credibility, objection handling, offer, CTA, sound, captions, and platform fit.
   - Give timestamped strengths, weaknesses, and testable hypotheses. Do not infer actual performance from creative quality alone.

5. **Create an original adaptation**
   - Preserve high-level strategic principles only: audience problem, emotional angle, narrative function, pacing pattern, proof strategy, and CTA logic.
   - Write a new hook, script, shot list, captions, and CTA. Use original wording and newly arranged or user-authorized assets.
   - Do not reproduce a competitor's exact script, shot sequence, branding, distinctive characters, or protected footage. Do not remove watermarks or imitate a living creator's distinctive style.
   - If the supplied reference is the user's own footage, it may be edited as source media subject to the user's instructions.

5a. **Prepare the cloud production request**
   - After the reference analysis and original script are complete, create a shot-level `asset_queries` list only for shots that cannot be satisfied by the supplied reference footage.
   - Use the separate `asset_acquisition` step; do not perform network acquisition in `editing_only`.
   - Build a chronological `timeline` with segments that use either `source: "reference"` or an `asset_id` returned in the verified stock manifest. Never place a URL or arbitrary path in the timeline.
   - Write original subtitle text to `subtitles_srt`. Do not put passwords, private notes, or personal details in the request file because it is committed to a public repository.
   - Set `test_mode` to false only for a real, encrypted tmp0 upload after the user has completed the browser upload. Never replace the synthetic fixture with a real file ID until the source has been uploaded client-side encrypted.
   - Commit only the request JSON and non-sensitive production instructions. Never commit source media, decrypted media, rendered media, passwords, API keys, or stock downloads.

6. **Produce and quality-check**
   - Select an available zero-cost, permitted production path. Never call paid APIs, metered generation services, GPU services, or publishing integrations under the free editing profile.
   - If the required original visuals, voice, or assets cannot be created with available free local tools, disclose the limitation and produce the best honest edit from available assets. Never pretend a generated asset exists.
   - Render a first cut, inspect it with local analysis, and review the first 3 seconds plus the full timeline for hook clarity, continuity, pacing, captions, audio, aspect ratio, and CTA.
   - Iterate when quality gates fail. Deliver the final video, a concise timestamped analysis, competitor evidence links, and a list of assumptions/limitations.

## No-questions default

When the reference clearly identifies a niche and product/problem, proceed without asking the user to explain the desired style. Use sensible defaults from the studio's saved brand/platform profile. Ask one concise question only if an essential fact cannot be inferred safely (for example, which of two visibly different products is being advertised).

## Required honesty

- A reference video is not proof of success.
- Public engagement is not proof of sales, ROAS, or profitability.
- Competitor research must include evidence links or be labelled unavailable.
- Clearly distinguish completed automated stages from recommendations, unavailable capabilities, and human-required actions.
- Never upload source media, decrypted media, final media, or private research artifacts to public GitHub artifacts or commits.
