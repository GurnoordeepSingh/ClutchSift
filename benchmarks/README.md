# Laptop validation

These checks used generated video and speech, plus four invented gameplay transcripts. A Windows laptop with an RTX 5060 Laptop GPU and FFmpeg 9.0.2 produced the following results.

| Check | Observation | Scope |
| --- | --- | --- |
| Portrait export | All four exports decoded at 720×1280. The two-second trims retained the expected audio or silence. | CPU crop, CPU blurred backdrop, silent input and NVENC blurred backdrop. Clips used punctuation and Unicode in filenames. |
| Title candidates | Both local models returned four one-line titles under 60 characters. For the three warm requests per model, Qwen2.5 7B took 0.15–0.18 s and Gemma 2 9B took 0.30–0.31 s. First requests took 57.7 s and 50.4 s, respectively. | English title-only prompt. Qwen added a race to a checkpoint clip. Gemma implied the finish in a recording that ended early. Keep creator approval and evaluate the actual metadata prompt separately. |
| Speech reference | OpenAI Whisper base on four CPU threads transcribed 39 of 39 reference words correctly in 16.4 seconds of synthesized audio, using 0.50 seconds of inference per second of audio. | Clean English speech and one voice. Timestamps were ordered and in range. Accuracy against human word boundaries, faster-whisper performance and gameplay accuracy require separate measurements. |

Run from the repository root. The title benchmark expects the two model tags in the [raw results](title_results.json) on a local Ollama server. The speech benchmark requires Windows desktop speech, the openai-whisper Python package and an existing base checkpoint. Its [raw results](speech_results.json) include the reference sentences.

```powershell
python benchmarks/media_check.py --nvenc
python benchmarks/title_benchmark.py --out my-title-results.json
python benchmarks/speech_check.py --weights "$env:USERPROFILE/.cache/whisper/base.pt"
```

For the next comparison, ask the creator to mark usable events, the setup and the payoff in a 10–20 minute recording before seeing any suggestions. Scan that recording in audio and hybrid modes with five 30-second candidates each. For each mode, count distinct accepted moments, clips missing setup or payoff and minutes spent trimming. Keep model weights, recordings and transcripts local. Record aggregate scores and a separate result for quiet gameplay.
