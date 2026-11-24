# Research: existing open-source video tools

We studied project descriptions and upstream docs to identify features worth recreating through our own code or through compatible dependencies. **Do not copy code verbatim or combine incompatible licenses.** Repository features change; revisit before implementing integrations.

| Repo | Useful ideas to benchmark, not copy blindly |
| --- | --- |
| https://github.com/artbyjazi/autoclip | local/offline clip pipeline, speaker-focused reframing, manual review |
| https://github.com/iyansr/gaming-clip | game/facecam layouts, captions, thumbnail handling |
| https://github.com/kleZ799/clipmint | ranking and metadata packaging, anti-hallucination checks |
| https://github.com/m-bain/whisperX | forced speech alignment, optional diarization |
| https://github.com/SYSTRAN/faster-whisper | optimized Whisper inference, word timestamps |
| https://github.com/Breakthrough/PySceneDetect | scene-change detectors and benchmarking |
| https://github.com/WyattBlue/auto-editor | silence-based timeline edits, remove dead space responsibly |
| https://github.com/MakeMyClip/editor | editor-friendly timelines and other editor exports |
| https://github.com/alokbaraii/streamclipper | game HUD clues, exports, permission-conscious workflows |
| https://github.com/mehbul/chopify | reusable project workspace, transcript editing, local-first UI |

### Competitive insight

**Local/offline/free is not uniquely differentiating.** Several existing projects already offer it. ClutchSift should differentiate by measurable **gaming-specific precision**, crisp clip boundaries, and user-guided game profiles. For example: GTA wanted level/WASTED screens, Roblox death cues, in-game HUD templates, and voice reactions. Each game profile must be tested on *permitted* gameplay clips and varied resolutions/UI scales.

### Code policy

- This v0.2 repo contains only newly implemented Python code built on the existing v0.1 project; competitor source files were not inserted.
- Cite upstream documentation when integrating dependencies.
- Audit dependencies, licenses, and video/audio rights before a commercial hosted launch.
