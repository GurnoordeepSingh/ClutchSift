# System design and milestones

## Bounded worker pipeline

**Input → probe → cheap proposals → human review → export → optional ASR → optional text metadata → optional QA.**

Core modules: `core.py` (probe, audio, FFmpeg), `hybrid.py` (motion and fusion), `captions.py` (faster-whisper and SRT/ASS), `metadata.py` (local Ollama text), `vision.py` (local Ollama sparse-frame observations), `app.py` (Tkinter), `cli.py` (headless runner).

**Hard constraints:** no hidden uploads, no automatic publishing, never overwrite original input, never claim heuristic detections understand gameplay, keep expensive models optional, keep pipeline testable without downloaded model weights.

## Next milestones

1. **M0 (done):** v0.1 audio candidate editor and export.
2. **M1 (done in v0.2):** hybrid visual/audio heuristic, native review UI, crop/blur layouts, optional faster-whisper word captions and Ollama grounded title suggestions, smoke tests.
3. **M2 (not yet):** persistent projects with safe export versioning; simple creator acceptance/rejection UI; candidate thumbnails, waveform, timeline preview; resumable jobs; settings.
4. **M3 (not yet):** game profiles for GTA/Roblox (HUD/kill/wasted/template signals), semantic model adapter with VLM limited to candidate frames, human-labelled benchmark suite. No viral prediction guarantees.
5. **M4 (not yet):** facecam-aware auto-reframe, title A/B drafts, editable CapCut/Premiere/DaVinci timelines, Windows packaging, quality audit (black frames, clipping, caption overlap, loudness).
6. **M5 (conditional on adoption):** YouTube publishing with clear per-action user authorization and platform API compliance, creator-owned analytics, team collaboration/cloud queue with actual revenue validation.

## Model adapter interface proposal

Each detector returns `{time_start, time_end, score, detector_name, evidence}`; standardized scores are calibrated on held-out creator videos. Enforce an honest distinction between observable audio/motion and semantic model inferences. Use non-max suppression to avoid overlapping suggestions, then boundary refinement around action onset, context, and payoff. Preserve evidence and rejected examples for model comparison.

### Definition of 'best'

Choose a pipeline only if a blind human evaluation shows higher creator-approved clips per hour and manageable runtime on 8 GB VRAM. Model leaderboards for transcription accuracy are not clipping quality leaderboards.
