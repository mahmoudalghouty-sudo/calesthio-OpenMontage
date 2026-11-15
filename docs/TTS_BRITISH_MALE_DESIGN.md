# British Male Advertising TTS — Design and Validation Plan

Status: approved design; runtime validation pending
Profile: English only / British English / male voice / persuasive advertising delivery
Budget: USD 0.00; local inference only; no paid API, hosted inference, or subscription

## 1. Decision

Use Kokoro-82M as the first local engine to validate. Its published voice catalogue includes four British male voice IDs:

- `bm_george`
- `bm_fable`
- `bm_daniel`
- `bm_lewis`

The language pipeline must be British English (`lang_code='b'`). The voice ID must be selected from the British male list only. Do not silently fall back to American English or a female voice.

Piper remains a possible lightweight fallback only after a separate British male voice and its model-specific licence have been verified. It is not enabled by this design.

## 2. Important capability boundary

Kokoro provides voice identity and synthesis controls, but this design does not assume a dedicated emotion slider or a guaranteed "sales" emotion mode. The persuasive advertising character is created through:
- the approved script and natural spoken phrasing;
- punctuation and sentence/chunk boundaries;
- a controlled speaking-rate comparison;
- voice audition and human selection;
- optional post-processing for loudness and dynamics.

Do not claim that the model understands or guarantees emotional intent. Do not distort the voice with aggressive compression or pitch changes.

## 3. User workflow

1. Claude Code receives the approved English script and target video duration.
2. It checks the script for UK spelling and phrasing, while preserving the user's intended meaning.
3. It proposes narration pacing and emphasis marks for approval.
4. It generates audition files locally for the four British male voices, using the same text and settings.
5. The user listens and chooses the voice. No voice is marked approved automatically.
6. The selected voice is tested at speaking-rate values 0.95, 1.00, and 1.05 (where supported by the installed Kokoro version).
7. After approval, the tool renders the full narration to WAV, stores metadata (engine/version, voice ID, language, rate, script hash, sample rate, duration), and passes the WAV to the existing FFmpeg edit pipeline.
8. The edit pipeline aligns narration with the video, then pauses for human review before export.

## 4. Initial audition script

Use the same short, original script for all voice comparisons:

"Your pet deserves more than an ordinary routine. Discover a smarter, simpler way to make every day better. Shop today and give your best friend the care they deserve."

The script is only a test fixture. Do not treat its claims as product facts for any real advertisement.

## 5. Technical implementation boundary

- Engine: local Kokoro-82M inference library.
- Language: British English pipeline (`b` / `en-GB`, according to the installed API).
- Allowed voice IDs: `bm_george`, `bm_fable`, `bm_daniel`, `bm_lewis`.
- Output master: lossless WAV; preserve the model's native sample rate until the audio mastering stage.
- Integration: call the TTS adapter as an OpenMontage local tool; use FFmpeg only for audio mastering, timing, and muxing.
- Runtime: CPU-first. GPU is not required or provisioned. Measure real-time factor, peak RAM, and first-run model load time on the actual host.
- Network: model/voice assets may need one-time download during setup; synthesis itself must run offline after assets are present. Never download arbitrary voice files during a production run.
- Secrets: none. No API key is needed.
- Budget guard: reject any provider/runtime that is paid, metered, hosted, or requires an account.
- Failure behavior: stop with a clear error if the model, voice file, or required phonemizer is unavailable. Never switch accent, gender, provider, or paid fallback automatically.

## 6. Validation matrix

Run this only in the actual OpenMontage execution environment after dependencies and model assets are installed.

### Functional checks
- [ ] Kokoro imports and model loads on CPU.
- [ ] Each of the four British male voice IDs synthesizes the exact same audition script.
- [ ] Each output is a non-empty, decodable WAV with finite samples and valid duration.
- [ ] The reported voice ID and language are stored in metadata.
- [ ] A missing/invalid voice ID fails closed; no American/female fallback.
- [ ] A second run succeeds with network access disabled after model assets are cached.
- [ ] FFmpeg can read the WAV and mux a short test video without changing the original source file.

### Quality review (human listening required)
Score each sample from 1–5 for:
- British accent consistency;
- naturalness and pronunciation;
- persuasive energy without sounding robotic or exaggerated;
- clarity and intelligibility;
- pacing and pauses;
- suitability for a paid social advertisement.

Choose the winner by listening, not by voice-name assumptions or automated scores alone.

### Performance checks
Record:
- CPU model and available RAM;
- model cold-start time;
- generation time and audio duration (real-time factor);
- peak resident memory;
- output sample rate and duration.

Do not approve deployment if the host repeatedly runs out of memory, if generation is slower than the workflow can tolerate, or if the output quality is not acceptable.

## 7. Acceptance criteria

The TTS adapter is not "ready" until:
1. all functional checks pass on the actual target host;
2. the four audition WAVs have been generated and listened to;
3. the user has explicitly selected one voice;
4. CPU/RAM/time measurements are recorded;
5. offline synthesis is verified;
6. FFmpeg integration and a human-approved narration-to-video review pass.

Until then, status must remain **designed, not runtime-tested**.

## 8. References

- Kokoro model card and Apache-2.0 model licence: https://huggingface.co/hexgrad/Kokoro-82M
- Kokoro inference library: https://github.com/hexgrad/kokoro
- British male voice catalogue: https://huggingface.co/hexgrad/Kokoro-82M/blob/main/VOICES.md
