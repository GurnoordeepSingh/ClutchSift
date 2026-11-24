"""Optional faster-whisper transcription and readable subtitle writers."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from .core import ClutchSiftError, _srt_time


@lru_cache(maxsize=2)
def _load_model(model_name: str, device: str):
    try:
        from faster_whisper import WhisperModel
    except ImportError as exc:
        raise ClutchSiftError("Install transcription extras: py -3 -m pip install -r requirements-captions.txt") from exc
    if device not in ("cpu", "cuda", "auto"):
        raise ClutchSiftError("ASR device must be 'cpu', 'cuda', or 'auto'.")
    compute = "int8" if device == "cpu" else "auto"
    return WhisperModel(model_name, device=device, compute_type=compute)


def transcribe_clip(clip: Path | str, model_name: str = "small", device: str = "cpu") -> list[dict]:
    """Return word-aligned text segments and timestamps; model cached per process."""
    model = _load_model(model_name, device)
    try:
        segments, _ = model.transcribe(str(Path(clip).resolve()), vad_filter=True,
                                       word_timestamps=True, beam_size=3,
                                       condition_on_previous_text=False)
        result = []
        for s in segments:
            words = []
            for w in (s.words or []):
                if w.start is not None and w.end is not None:
                    words.append({"start": max(0., float(w.start)),
                                  "end": max(float(w.start), float(w.end)),
                                  "text": w.word.strip()})
            text = s.text.strip()
            if text:
                result.append({"start": float(s.start), "end": float(s.end),
                               "text": text, "words": words})
        return result
    except Exception as exc:
        raise ClutchSiftError("Speech recognition failed. Try CPU mode or smaller model: " + str(exc)) from exc


def save_srt(segments: list[dict], path: Path) -> Path:
    with path.open("w", encoding="utf-8") as f:
        for i, seg in enumerate((s for s in segments if s["text"].strip()), 1):
            text = seg["text"].replace("\n", " ").strip()
            f.write(f"{i}\n{_srt_time(seg['start'])} --> {_srt_time(seg['end'])}\n{text}\n\n")
    return path


def _ass_timestamp(seconds: float) -> str:
    centiseconds = max(0, round(float(seconds) * 100))
    hh, rem = divmod(centiseconds, 360000)
    mm, rem = divmod(rem, 6000)
    ss, cs = divmod(rem, 100)
    return f"{hh}:{mm:02}:{ss:02}.{cs:02}"


def _ass_escape(text: str) -> str:
    return text.replace("\\", "").replace("{", "(").replace("}", ")").replace("\n", " ")


def _groups(words: list[dict], max_words: int = 4) -> list[list[dict]]:
    """Break word timestamps into compact on-screen groups."""
    result = []
    for i in range(0, len(words), max_words):
        chunk = [w for w in words[i:i + max_words] if w["text"].strip()]
        if chunk:
            result.append(chunk)
    return result


def save_karaoke_ass(segments: list[dict], path: Path) -> Path:
    """Write word-timed ASS karaoke captions. Requires FFmpeg libass to burn in."""
    header = """[Script Info]
Title: ClutchSift word-timed captions
ScriptType: v4.00+
PlayResX: 720
PlayResY: 1280
ScaledBorderAndShadow: yes
WrapStyle: 2

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Clutch,Arial,64,&H00FFFFFF,&H0000E5FF,&H00000000,&H64000000,-1,0,0,0,100,100,0,0,1,4,1,2,46,46,185,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    events = []
    for segment in segments:
        words = segment.get("words", [])
        if not words:
            text = _ass_escape(segment["text"])
            events.append((segment["start"], segment["end"], text))
            continue
        for group in _groups(words):
            beg, end = float(group[0]["start"]), float(group[-1]["end"])
            if end <= beg:
                continue
            phrase = " ".join(
                "{\\kf" + str(max(1, round((float(w["end"]) - float(w["start"])) * 100))) + "}" +
                _ass_escape(w["text"]) for w in group)
            events.append((beg, end, phrase))
    with path.open("w", encoding="utf-8") as f:
        f.write(header)
        for start, end, content in events:
            f.write(f"Dialogue: 0,{_ass_timestamp(start)},{_ass_timestamp(end)},Clutch,,0,0,0,,{content}\n")
    return path


def write_captions(clip: Path | str, *, model_name: str = "small", device: str = "cpu",
                   style: str = "srt") -> tuple[Path, str]:
    """Create SRT for editing; optional additional styled ASS for exporting."""
    if style not in ("srt", "karaoke"):
        raise ClutchSiftError("Unknown caption style; choose srt or karaoke.")
    path = Path(clip).resolve()
    segments = transcribe_clip(path, model_name, device)
    save_srt(segments, path.with_suffix(".srt"))
    burned_path = save_karaoke_ass(segments, path.with_suffix(".ass")) if style == "karaoke" else path.with_suffix(".srt")
    transcript = " ".join(seg["text"] for seg in segments)
    return burned_path, transcript
