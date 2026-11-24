# 🎬 ClutchSift

**Local-first gaming highlight candidate finder and Shorts clipper.**  Select a recording, review likely moments, trim them, and export vertical or landscape clips. No account, watermark, cloud upload, or paid API required for core editing.

[![CI](https://img.shields.io/badge/tests-12%20passing-brightgreen)](#tests) [![Python](https://img.shields.io/badge/Python-3.11%2B-blue)](#quick-start-windows) [![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

> **Truthful capability note:** v0.2 uses **audio peaks and/or simple visual-motion changes**, not a trained GTA/Roblox kill detector. Motion, loud audio, and changes do not prove a clip is funny, exciting, or viral. This is a working prototype to validate real demand and collect permitted user feedback.

## What's included in v0.2

| Capability | Availability |
| --- | --- |
| Local MP4/MKV/MOV/WebM/AVI input, preview and manual trim | ✅ GUI and CLI |
| Audio-activity proposals with transparent labels | ✅ |
| Audio + 1 FPS visual-motion proposals, fallback to sampling | ✅ Heuristic, new |
| 9:16 full-gameplay-in-blurred-background export | ✅ |
| 9:16 center-crop and 16:9 exports | ✅ CLI |
| NVIDIA NVENC accelerated encoding (when supported) | ✅ CLI, opt-in |
| Offline Whisper transcript, editable SRT | ✅ Optional package/model |
| Word-timed karaoke-style ASS captions | ✅ Optional, new |
| SRT/ASS burn-in | ✅ With suitable FFmpeg libass build |
| Locally suggested video title/description/hashtags | ✅ Optional running Ollama, new |
| Candidate three-frame visual descriptions by local multimodal AI | ✅ Optional `--vision-review`, new; **not** event detection |
| Game-event-specific object/HUD detector, facecam tracking | 📋 Roadmap, not built |
| Performance prediction, auto-publishing, analytics integrations | 📋 Roadmap, not built |

## Quick start (Windows)

1. Install **Python 3.11 or 3.12** from https://python.org. (3.13 is fine for the stdlib core; optional GPU packages may have narrower support.)
2. Install **FFmpeg** (including `ffmpeg` and `ffprobe`) from https://ffmpeg.org/download.html or Windows PowerShell: `winget install Gyan.FFmpeg`. Open a fresh terminal after installing.
3. Download/unzip this repository, then double-click **`run_windows.bat`** in the extracted `ClutchSift` folder. Or run in PowerShell from the repository root:

   ```powershell
   py -3 -m clutchsift
   ```

4. Select a recording → Find moments → select and preview candidates → edit trim → export clips.

**No Python packages are needed for the core editor and audio+motion proposal engine.** It uses Python's standard library, native Tkinter, and your separately installed FFmpeg.

### Optional: captions

```powershell
py -3 -m pip install -r requirements-captions.txt
```

In the GUI check **Generate captions**; optional **Word-highlight karaoke captions**, then optional **Burn captions**. The first run downloads the chosen Whisper model. The GUI defaults to `small` on CPU (safe but slower). Video is not sent to a provider. On-screen karaoke word timings are approximate ASR outputs and must be checked for correctness.

For improved GPU throughput, try CLI `--asr-device cuda` only if your CUDA/CTranslate2 runtime is installed and compatible (see faster-whisper docs). The project does not bundle NVIDIA CUDA libraries.

### Optional: title/description suggestions

1. Install [Ollama](https://ollama.com/download) and run `ollama pull qwen3.5:4b` (a few GB download).
2. Start Ollama's local service.
3. In GUI check **Suggest titles/descriptions** or use CLI `--titles`. Captions dependencies are also required because title proposals use the clip transcript.

This calls **localhost only** at `127.0.0.1:11434`; it does **not** send footage to a hosted AI provider. It creates a separate JSON metadata file per clip for review; it does not post content.

## CLI examples

```powershell
# Best no-install core: use audio + visual motion; no transcription models needed
py -3 -m clutchsift "D:\Recordings\gameplay.mp4" --mode hybrid --count 5 --seconds 30 --scan-only

# Export reviewable vertical Shorts, preserving the full gameplay view
py -3 -m clutchsift "D:\Recordings\gameplay.mp4" --mode hybrid --count 5 --seconds 30

# Fill the vertical frame (cuts off sides, including possible HUD)
py -3 -m clutchsift "D:\Recordings\gameplay.mp4" --layout center-crop

# NVIDIA hardware encoder (FFmpeg must have h264_nvenc)
py -3 -m clutchsift "D:\Recordings\gameplay.mp4" --encoder nvenc

# Approximate word-level karaoke captions and burn-in
py -3 -m clutchsift "D:\Recordings\gameplay.mp4" --count 2 --captions --caption-style karaoke --burn

# Ask local Ollama's vision model to describe sparse preview frames of candidates
py -3 -m clutchsift "D:\Recordings\gameplay.mp4" --count 3 --scan-only --vision-review

# More capable, but heavier ASR model with supported CUDA setup
py -3 -m clutchsift "D:\Recordings\gameplay.mp4" --count 2 --captions --asr-model large-v3-turbo --asr-device cuda

# Optional local text metadata; speech recognition extras and Ollama required
py -3 -m clutchsift "D:\Recordings\gameplay.mp4" --count 2 --titles --ollama-model qwen3.5:4b

# Full uncropped wide output
py -3 -m clutchsift "D:\Recordings\gameplay.mp4" --landscape
```

### Pipeline

```text
Recording you own / are allowed to edit
  ├─ FFprobe validates media
  ├─ FFmpeg decodes 4 kHz mono audio → 1-second loudness changes
  ├─ FFmpeg decodes 64x36 grayscale at 1 FPS → frame-change estimates
  └─ Hybrid scoring, nonoverlap suppression → editable candidate ranges
                      ↓
               Human reviews clips
                      ↓
           FFmpeg H.264 / AAC exports
                      ↓ (optional)
         faster-whisper → SRT / ASS word captions
                      ↓ (optional)
         Ollama localhost → suggested metadata JSON / sparse-frame visual observations
```

Every candidate has a detector `method` in `highlights.json`: `audio`, `motion`, `audio+motion` or `sampling`. **Sampling is not an AI-detected highlight.** Motion responds to camera motion, so it will often surface ordinary footage; visual game event detection is future work.

### Safety and data handling

- Source video is read, never rewritten as an export. A guard prevents accidentally exporting over the original.
- Destination clips, `highlights.json`, and optional caption/metadata files are written to the chosen output folder. **Existing output files with the same names can be overwritten** by FFmpeg's `-y`; use a fresh export directory if you want to preserve earlier results.
- Core analysis is offline. Optional model download uses the internet once. Optional Ollama communicates on localhost only. No telemetry, analytics, video upload, hidden posting, or API key.
- Use only recordings you own or have the right to edit and distribute; game, music and voice rights may apply. Don't infer privacy permissions from public availability.

## Tests

```powershell
py -3 -m unittest discover -s tests -v
```

14 tests pass locally with FFmpeg, covering normal audio and hybrid selection, caption formatting, metadata validation, path safety, and actual 9:16 export. CI also runs Python tests; FFmpeg tests skip when no FFmpeg exists. **The optional heavyweight ASR/Ollama stacks and the native Windows Tkinter GUI have not yet been end-to-end tested on your machine.**

## Development and research

- [AI model decision matrix](docs/MODEL_RESEARCH.md)
- [How Shorts metrics inform the clipper](docs/SHORTS_RESEARCH.md)
- [Architecture, acceptance tests, milestones](docs/ARCHITECTURE.md)
- [Competitive inspiration and licensing notes](docs/OPEN_SOURCE_RESEARCH.md)
- [Founder business plan](BUSINESS_PLAN.md)
- [Launch checklist](LAUNCH_CHECKLIST.md)
- [GitHub milestones and issue backlog](docs/GITHUB_BACKLOG.md)
- [Contributing](CONTRIBUTING.md)

No third-party project code was copied into the repository; third-party tools are separately installed integrations. Research links credit their maintainers. Model licenses must be rechecked before bundling any weights into redistributed downloads or deploying a commercial hosted version.

## Contributing

Bug reports, authorized sample clips, performance measurements, game-specific heuristic plugins, fixes, and tests welcome. See [CONTRIBUTING.md](CONTRIBUTING.md). All highlights remain subject to human editorial judgment.

MIT License — see [LICENSE](LICENSE).
