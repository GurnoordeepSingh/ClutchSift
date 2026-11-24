# AI model research — ClutchSift (reviewed 2026-11-24)

**Design principle:** there is no universal “best clipping model.” Optimize the complete workflow on a controlled creator dataset: quality of candidate *moment selection*, latency, video quality, VRAM, language, licensing, and ease of installation. An accurate speech-to-text model is not automatically good at recognizing GTA kills.

Target reference machine: Windows laptop, RTX 5060 Laptop GPU 8 GB VRAM, 16 GB RAM. Treat all model hardware requirements as estimates until measured on that hardware. Never load all GPU models simultaneously; schedule model stages sequentially.

| Pipeline stage | Selected starting point | Why | Status |
| --- | --- | --- | --- |
| Audio spikes / reactions | FFmpeg PCM RMS + local changes | transparent and tiny dependencies | ✅ v0.1 |
| Visual activity | FFmpeg 1 FPS 64×36 frame difference | fast baseline for silent moments, not semantic | ✅ v0.2 |
| Multilingual speech | faster-whisper `small` CPU baseline; `large-v3-turbo` GPU option | good ecosystem, 99-language Whisper family | ✅ v0.2 optional |
| Word caption timing | faster-whisper `word_timestamps=True` | sufficient for pilot; no heavy aligner | ✅ v0.2 optional |
| More precise word alignment | WhisperX | specialized forced alignment, overlap caveats | ⏳ evaluate later |
| English-heavy fast ASR | NVIDIA Parakeet TDT 0.6B v3 | excellent throughput for supported languages; **not Hindi** | ⏳ benchmark later |
| Alternative multilingual ASR | Qwen3-ASR 0.6B/1.7B | supports Hindi, Japanese and many other languages; test performance/VRAM | ⏳ benchmark later |
| Local title/description from transcript | Ollama `qwen3.5:4b` | compact multimodal-capable family; basic text metadata now | ✅ v0.2 optional |
| Sparse-frame VLM observations | `qwen3.5:4b` via Ollama, three frames per candidate | grounded description, NOT demonstrated game-event detection | ✅ v0.2 opt-in |
| Calibrated semantic game-event ranking | Qwen3.5:4b / Qwen3-VL-4B comparison on labelled data | game-event precision must be proven before re-ranking | ⏳ future benchmark |
| Visual cut detection | PySceneDetect AdaptiveDetector | strong established alternative to simple frame differences | ⏳ evaluate later |
| Multi-speaker separation | pyannote Community-1 / WhisperX | valuable for interviews/co-op, not initial GTA solo clips | ⏳ later |
| Frame/person tracking | OpenCV initially; specialized detector only if validated | prevent cropping HUD and facecam; avoid unnecessary AGPL risk | ⏳ later |

### Why not load the biggest model everywhere?

1. Video can be 2–8 hours, so sending every frame through a vision-language model is costly even on a local GPU.
2. We **propose** candidates with cheap audio/visual signals, then optionally have a VLM inspect only short candidate windows and sampled frames.
3. VLM statements (“the player got a kill”) can be wrong; preserve human review and include evidence/timecodes.
4. Qwen3.5:4b's published Ollama quantized download is ~3.3–4.0 GB; adding video context/runtime buffers matters on 8 GB VRAM. Separate ASR and VLM stages.
5. A model cannot honestly guarantee a viral clip. Rank for human judged usefulness, opening clarity, build-up, payoff and false positives, not fictitious probability of virality.

### Model benchmarking plan

- Creators provide **50+ short consented recordings** across GTA, Roblox, and at least one other game, including quiet gameplay, background music, mixed Hindi/English, and facecam footage.
- 2 people label timestamps for genuinely useful moments and whether each starts early enough and ends after payoff.
- Measure **precision@5**, **recall of labeled moments**, **duplicate rate**, **clip boundary error**, **clips usable per hour**, and **editor minutes saved**. Keep an audio-only baseline.
- ASR: measure word error rate on a representative manually transcribed mix of English, Hindi, gaming slang and proper nouns.
- System: wall time per hour of footage, peak GPU memory, system RAM, disk consumption, export failures, and setup time on Windows.
- Compare vision models with same frames/prompts and report both false negatives and hallucinated game events. Keep human review.
- Document benchmarks and make a switch only when gain justifies installation cost and license terms.

### Licensing notes

- Python project core: MIT.
- FFmpeg: executable is provided separately. License depends on build/configuration; review before redistribution, especially if compiled with additional components.
- faster-whisper: inspect library and model-specific licenses if bundling weights. Downloaded models are *not* redistributed in this repo.
- The Qwen3.5-4B Hugging Face model card lists Apache-2.0; NVIDIA Parakeet TDT 0.6B v3 lists CC-BY-4.0. Verify exact quantized builds, Qwen3-ASR, WhisperX/pyannote and other dependencies individually before commercial packaging or hosting. **Code license != all model weights licenses.**
- Ultralytics YOLO package uses AGPL-3.0 or enterprise licensing options; don't casually embed it in a closed hosted product without legal review.

### Primary sources

- faster-whisper: https://github.com/SYSTRAN/faster-whisper
- WhisperX: https://github.com/m-bain/whisperX
- Qwen3.5 4B local: https://ollama.com/library/qwen3.5:4b
- Qwen3.5 model card: https://huggingface.co/Qwen/Qwen3.5-4B
- Qwen3-VL 4B: https://huggingface.co/Qwen/Qwen3-VL-4B-Instruct
- Qwen3-ASR languages: https://huggingface.co/docs/transformers/model_doc/qwen3_asr
- Parakeet TDT v3: https://huggingface.co/nvidia/parakeet-tdt-0.6b-v3
- pyannote: https://github.com/pyannote/pyannote-audio
- PySceneDetect: https://github.com/Breakthrough/PySceneDetect
- Ultralytics licenses: https://github.com/ultralytics/ultralytics
