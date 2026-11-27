<p align="center">
  <img src="assets/clutchsift-logo.png" alt="ClutchSift logo — editing corners framing a play button" width="160" height="160">
</p>

<h1 align="center">ClutchSift</h1>

**Local-first gaming highlight candidate finder and Shorts clipper.**  Select a recording, review likely moments, trim them, and export vertical or landscape clips. No account, watermark, cloud upload, or paid API required for core editing.

[CI runs](https://github.com/GurnoordeepSingh/ClutchSift/actions/workflows/test.yml) · [Python 3.11+](#quick-start-windows) · [MIT license](LICENSE)

The default scan finds changes in audio and motion. Choose **Local AI vision** to describe a visible event and let a local model rank potential clips. Review the suggestions before exporting. Accuracy on long GTA and Roblox sessions still needs creator testing.

## What you can do

| Capability | Availability |
| --- | --- |
| Local MP4/MKV/MOV/WebM/AVI input | GUI and CLI. Preview and manual trim are available in the GUI. |
| Audio-activity proposals with transparent labels | ✅ |
| Audio + 1 FPS visual-motion proposals, fallback to sampling | ✅ Heuristic, new |
| Find a requested visible event and read the evidence for each pick | GUI and CLI, optional local Qwen3-VL model |
| 9:16 full-gameplay-in-blurred-background export | ✅ |
| 9:16 center crop or original aspect ratio | GUI and CLI |
| NVIDIA NVENC encoding on supported systems | GUI and CLI, opt-in |
| Offline Whisper transcript, editable SRT | ✅ Optional package/model |
| Word-timed karaoke-style ASS captions | ✅ Optional, new |
| SRT/ASS burn-in | ✅ With suitable FFmpeg libass build |
| Locally suggested video title/description/hashtags | ✅ Optional running Ollama, new |
| Candidate three-frame visual descriptions by local multimodal AI | ✅ Optional `--vision-review`, new; **not** event detection |
| Game-event-specific object/HUD detector, facecam tracking | 📋 Roadmap, not built |
| Performance prediction, auto-publishing, analytics integrations | 📋 Roadmap, not built |

## Quick start (Windows)

### Launch the editor

1. Install Python 3.11 or 3.12 and FFmpeg (including `ffprobe`). On Windows, the FFmpeg package is available with `winget install Gyan.FFmpeg`. Open a fresh terminal after installing. [Python downloads](https://www.python.org/downloads/) · [FFmpeg downloads](https://ffmpeg.org/download.html)
2. Extract the repository and double-click **`run_windows.bat`**, or run `py -3 -m clutchsift` from the project folder.
3. Select a recording, click **Find moments**, preview and trim a suggestion, then export. The default audio and motion scan uses Python's standard library, Tkinter and FFmpeg.

### Find clips with a local vision model

Install [Ollama](https://ollama.com/download) and run `ollama pull qwen3-vl:4b` once (about 3.3 GB). Start Ollama. In the editor choose **Local AI vision**, enter an optional **AI focus** such as “a vehicle landing after a jump”, and click **Find moments**. Select a suggestion to read the model's visual evidence, then trim and export as usual.

```powershell
py -3 -m clutchsift gameplay.mp4 --mode ai --focus "a vehicle landing after a jump" --count 5 --seconds 30
```

The audio and motion scan covers the recording. The vision model compares four ordered stills per proposed window, including samples spaced across the timeline. It can miss short events and speech-only moments. Scores of 2–4 qualify for review, duplicate windows are suppressed, and the result can be empty. Scores express visual match to the request. Use `--scan-only` to save selections, scores and evidence without rendering. See the [competitor research and evaluation plan](docs/COMPETITOR_ANALYSIS.md).

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
  └─ Hybrid scoring → candidate ranges
                      ↓ (AI mode)
         Add spaced samples → review four stills per window → rank and remove overlaps
                      ↓
               Human reviews clips
                      ↓
           FFmpeg H.264 / AAC exports
                      ↓ (optional)
         faster-whisper → SRT / ASS word captions
                      ↓ (optional)
         Ollama localhost → suggested metadata JSON / sparse-frame visual observations
```

The manifest records how each clip was found. AI selections also include the original proposal method, creator request, model, match score and a short explanation. The general vision model can mistake routine movement for the requested event.

### Safety and data handling

- Source video is read, never rewritten as an export. A guard prevents accidentally exporting over the original.
- Each scan or export creates a numbered folder inside the selected output folder, such as `run-001`. Open that folder for clips, `highlights.json`, captions and metadata. Repeating the export creates another folder. A failed render leaves any previously completed video intact.
- Core analysis is offline. Optional model download uses the internet once. Optional Ollama communicates on localhost only. No telemetry, analytics, video upload, hidden posting, or API key.
- Use only recordings you own or have the right to edit and distribute; game, music and voice rights may apply. Don't infer privacy permissions from public availability.

## Tests

```powershell
py -3 -m unittest discover -s tests -v
```

CI runs the test suite and decodes generated vertical clips on Windows and Ubuntu. The Windows suite also exercises the desktop controls with generated footage. To check your own NVIDIA encoder, run `python benchmarks/media_check.py --nvenc` from the repository root.

See [laptop benchmark results](benchmarks/README.md) for model timings and their limits.

## Development and research

- [AI model decision matrix](docs/MODEL_RESEARCH.md)
- [Model choices and upstream license terms](docs/MODELS_AND_LICENSES.md)
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
