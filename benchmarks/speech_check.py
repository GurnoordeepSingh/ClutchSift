"""Run a small, offline Whisper timing check on generated English commentary on Windows."""

import argparse
import importlib.metadata
import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import time
import wave


LINES = (
    "Wait for the jump. I landed on the roof. That was so close.",
    "My car is stuck under the bridge. Reverse slowly and then turn left.",
    "We have one checkpoint left. Grab the flag before the timer runs out.",
)


def words(text):
    return re.findall(r"[a-z0-9']+", text.lower())


def edits(reference, actual):
    row = list(range(len(actual) + 1))
    for i, left in enumerate(reference, 1):
        next_row = [i]
        for j, right in enumerate(actual, 1):
            next_row.append(min(next_row[-1] + 1, row[j] + 1, row[j - 1] + (left != right)))
        row = next_row
    return row[-1]


def make_fixtures(root):
    code = """
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Speech
$synth = New-Object System.Speech.Synthesis.SpeechSynthesizer
try {
    $lines = Get-Content -LiteralPath 'lines.json' -Raw | ConvertFrom-Json
    for ($i = 0; $i -lt $lines.Count; $i++) {
        $synth.SetOutputToWaveFile((Join-Path (Get-Location) ("line-{0}.wav" -f $i)))
        $synth.Speak($lines[$i])
        $synth.SetOutputToNull()
    }
    Write-Output $synth.Voice.Name
} finally { $synth.Dispose() }
"""
    (root / "lines.json").write_text(json.dumps(LINES), encoding="ascii")
    powershell = shutil.which("pwsh") or "powershell.exe"
    result = subprocess.run([powershell, "-NoProfile", "-NonInteractive", "-Command", code],
                            cwd=root, check=True, timeout=90, stdout=subprocess.PIPE, text=True)
    return result.stdout.strip()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--weights", type=Path, required=True, help="Existing OpenAI Whisper .pt checkpoint")
    parser.add_argument("--threads", type=int, default=4)
    args = parser.parse_args()
    if not args.weights.is_file() or args.threads < 1:
        parser.error("Supply an existing checkpoint and a positive thread count.")
    import torch
    import whisper

    torch.set_num_threads(args.threads)
    results = []
    started = time.perf_counter()
    model = whisper.load_model(str(args.weights), device="cpu")
    load_seconds = round(time.perf_counter() - started, 3)
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        voice = make_fixtures(root)
        for i, ref in enumerate(LINES):
            wav = root / f"line-{i}.wav"
            with wave.open(str(wav)) as stream:
                seconds = stream.getnframes() / stream.getframerate()
            start = time.perf_counter()
            decoded = model.transcribe(str(wav), language="en", temperature=0, fp16=False,
                                       word_timestamps=True, condition_on_previous_text=False)
            runtime = time.perf_counter() - start
            timed = [w for s in decoded["segments"] for w in s.get("words", [])]
            valid = bool(timed) and all(0 <= w["start"] <= w["end"] <= seconds + 0.05 for w in timed)
            ordered = all(a["end"] <= b["start"] + .02 for a, b in zip(timed, timed[1:]))
            actual = decoded["text"].strip()
            results.append(dict(reference=ref, transcript=actual, audio_seconds=round(seconds, 3),
                                decode_seconds=round(runtime, 3), reference_words=len(words(ref)),
                                word_edits=edits(words(ref), words(actual)), timed_tokens=len(timed),
                                timestamps_present_ordered_in_bounds=valid and ordered))
    duration = sum(r["audio_seconds"] for r in results)
    print(json.dumps(dict(checkpoint=args.weights.name, voice=voice,
                          whisper=importlib.metadata.version("openai-whisper"), torch=torch.__version__,
                          device="cpu", threads=args.threads, model_load_seconds=load_seconds,
                          reference_words=sum(r["reference_words"] for r in results),
                          word_error_rate=sum(r["word_edits"] for r in results)/sum(r["reference_words"] for r in results),
                          audio_seconds=round(duration, 3), real_time_factor=round(
                              sum(r["decode_seconds"] for r in results)/duration, 3), clips=results), indent=2))
    return 0 if all(r["timestamps_present_ordered_in_bounds"] for r in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
