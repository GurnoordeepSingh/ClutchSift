# GitHub milestones / issue backlog

Copy these into GitHub Issues after the new repository is created. The target is *quality validated by users*, not just adding AI features.

## Milestone 1: Test on real Windows / stable alpha

1. **Windows smoke test** — start Tkinter through `run_windows.bat`, scan a 20-minute 1080p gameplay MP4, preview, export 9:16. Capture CPU/RAM/time and upload permission-safe log. Acceptance: no crash, playable file and no original overwrite.
2. **CUDA ASR setup guide** — test `large-v3-turbo` on RTX 5060 8GB, compare CPU small, document peak VRAM and correct DLL versions. Acceptance: repeatable setup on Windows.
3. **NVENC validation** — ensure output bitrate/pix_fmt and `h264_nvenc` works on a real NVIDIA laptop; quality compare with x264.
4. **Safe project versioning** — new export run ID and numbered directories so repeat exports cannot replace old exports by default.
5. **Real timeline UI** — waveform + candidate thumbnails + scrub preview, keyboard shortcuts and trim handles.

## Milestone 2: Human acceptance benchmark

6. **Consent-based benchmark metadata format** — record game, duration, user labels (gold ranges), rights and demographics only where necessary. Remove identifying details.
7. **Audio vs hybrid evaluation** — measure P@5, usable clips/hour, misses, false-positives, duplicated candidates, editing minutes saved across 50+ videos.
8. **Game profiles** — GTA, Roblox etc; opt-in templates for HUD cues; no universal claims, version by game build/UI resolution.
9. **Boundary refinement** — detect context before the event and reaction afterward; compare human trims.
10. **Feedback records** — creator accept/reject/edit per candidate; enable local settings but no telemetry.

## Milestone 3: Smarter AI and publishing quality

11. **Semantic ranking benchmark** — evaluate Qwen3.5 4B vs Qwen3-VL 4B on 3–8 sampled frames per candidate; avoid hallucinated events.
12. **WhisperX alignment trial** — test karaoke timing with mixed Hindi/English and gaming slang; language-switching WER.
13. **Facecam-aware layout** — face tracking only with consent, prefer preserving game HUD and footage context.
14. **Output QA** — check black frames, loudness, letterboxing, subtitle overlap and clip end truncation.
15. **Creator metadata/editor export** — multiple human-editable titles, hooks, captions, export to Premiere XML/CapCut-friendly format.

## Milestone 4: Business validation

16. **5 observed creator sessions** — time-saved baseline, repeat-use decision, expected pricing interview.
17. **OSS release demo** — clear 60-second demo using owned gameplay, no inflated performance claims.
18. **Optional paid services** — interview 10 creators/agencies about setup and batch export; measure server cost before cloud pricing.
19. **User-controlled platform publishing** — only after reviewing API terms, explicit OAuth consent and upload confirmation, no private data scraping.

Recommended labels: `bug`, `enhancement`, `research`, `good first issue`, `privacy`, `windows`, `benchmark`, `game-profile`, `needs-consented-media`.
