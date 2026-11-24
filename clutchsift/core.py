"""Local, dependency-light highlight detection and FFmpeg export helpers."""
from __future__ import annotations

from array import array
from dataclasses import asdict, dataclass
import json
import math
from pathlib import Path
import shutil
import statistics
import subprocess
import sys

SAMPLE_RATE = 4000
WINDOW_SECONDS = 1


class ClutchSiftError(RuntimeError):
    """Helpful error suitable for showing directly to a user."""


@dataclass(frozen=True)
class Highlight:
    start: float
    end: float
    peak_at: float
    jump_db: float
    peak_dbfs: float
    method: str = "audio"

    @property
    def duration(self) -> float:
        return self.end - self.start


def find_tool(name: str) -> str:
    executable = shutil.which(name)
    if not executable:
        raise ClutchSiftError(
            f"'{name}' is missing. Install FFmpeg and put its bin folder on PATH. "
            "See README.md for Windows setup."
        )
    return executable


def run_command(args: list[str], *, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    p = subprocess.run(args, capture_output=True, text=True, cwd=cwd, check=False)
    if p.returncode:
        message = (p.stderr or p.stdout or "Unknown FFmpeg error").strip()
        raise ClutchSiftError(message[-1800:])
    return p


def probe_media(video: Path | str) -> tuple[float, bool]:
    video = Path(video).expanduser().resolve()
    if not video.is_file():
        raise ClutchSiftError(f"Video not found: {video}")
    info = run_command([
        find_tool("ffprobe"), "-v", "error", "-show_format", "-show_streams",
        "-of", "json", str(video),
    ])
    data = json.loads(info.stdout)
    streams = data.get("streams", [])
    if not any(s.get("codec_type") == "video" for s in streams):
        raise ClutchSiftError("This file has no video track.")
    duration = float(data.get("format", {}).get("duration") or 0)
    if duration <= 0:
        durations = [float(s["duration"]) for s in streams if s.get("duration")]
        duration = max(durations, default=0)
    if duration <= 0:
        raise ClutchSiftError("Could not determine video duration.")
    return duration, any(s.get("codec_type") == "audio" for s in streams)


def sample_audio_dbfs(video: Path | str) -> list[float]:
    """Read just mono 4 kHz PCM from FFmpeg (not the full video in RAM).

    Each entry is the RMS amplitude of ~1 second of audio, measured in dBFS.
    This is an *audio heuristic*, NOT an AI model detecting kills/funny moments.
    """
    args = [
        find_tool("ffmpeg"), "-nostdin", "-hide_banner", "-loglevel", "error",
        "-i", str(Path(video).resolve()), "-map", "0:a:0", "-vn", "-ac", "1",
        "-ar", str(SAMPLE_RATE), "-f", "s16le", "pipe:1",
    ]
    proc = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    assert proc.stdout is not None
    db_values: list[float] = []
    nbytes = SAMPLE_RATE * WINDOW_SECONDS * 2
    try:
        while True:
            block = proc.stdout.read(nbytes)
            if not block:
                break
            # A partial terminal audio sample should be ignored, not interpreted.
            block = block[: len(block) - len(block) % 2]
            if not block:
                break
            samples = array("h")
            samples.frombytes(block)
            if sys.byteorder != "little":
                samples.byteswap()
            power = sum(x * x for x in samples) / len(samples)
            rms = math.sqrt(power)
            db_values.append(20 * math.log10(max(rms / 32768.0, 1e-7)))
    except BaseException:
        proc.kill()
        proc.communicate()
        raise
    finally:
        proc.stdout.close()
    error = proc.stderr.read().decode("utf-8", errors="replace") if proc.stderr else ""
    if proc.stderr:
        proc.stderr.close()
    status = proc.wait()
    if status:
        raise ClutchSiftError(f"Audio decoding failed: {error[-1500:]}")
    return db_values


def evenly_spaced_candidates(duration: float, clip_seconds: float, limit: int) -> list[Highlight]:
    """Non-audio fallback: these are NOT detected highlights."""
    output: list[Highlight] = []
    length = min(duration, clip_seconds)
    max_start = max(0.0, duration - length)
    for i in range(min(limit, max(1, math.ceil(duration / length)))):
        start = min(max_start, i * length)
        end = min(duration, start + length)
        output.append(Highlight(start, end, start + (end - start) / 2, 0, -120, "sampling"))
    return output


def rank_audio_candidates(
    levels: list[float], duration: float, clip_seconds: float = 30,
    limit: int = 5,
) -> list[Highlight]:
    """Rank loud and *locally surprising* moments; keep non-overlapping clips."""
    if duration <= 0 or clip_seconds <= 0 or limit < 1:
        raise ValueError("Duration, clip length, and candidate count must be positive.")
    if not levels:
        return evenly_spaced_candidates(duration, clip_seconds, limit)
    n = len(levels)
    baseline = statistics.median(levels)
    # Local loudness jump + actual loudness; a loud explosion may be a candidate,
    # but this score makes NO claim about whether a moment is entertaining.
    scored: list[tuple[float, int, float]] = []
    for i, value in enumerate(levels):
        local = statistics.median(levels[max(0, i - 12):min(n, i + 13)])
        jump = max(0.0, value - local)
        intensity = max(0.0, value - baseline)
        score = (jump * 2.0) + intensity
        scored.append((score, i, jump))
    scored.sort(key=lambda x: x[0], reverse=True)
    chosen: list[Highlight] = []
    clip_seconds = min(clip_seconds, duration)
    for score, index, jump in scored:
        peak = min(duration, float(index) + 0.5)
        start = max(0.0, min(duration - clip_seconds, peak - clip_seconds * 0.65))
        end = start + clip_seconds
        # Reject intervals that overlap existing clips by more than 10%.
        if any(max(0, min(end, h.end) - max(start, h.start)) > 0.1 * clip_seconds for h in chosen):
            continue
        chosen.append(Highlight(round(start, 2), round(end, 2), peak,
                                round(jump, 1), round(levels[index], 1)))
        if len(chosen) >= limit:
            break
    return sorted(chosen, key=lambda h: h.start)


def find_highlights(video: Path | str, clip_seconds: float = 30, limit: int = 5) -> tuple[float, list[Highlight]]:
    duration, audio_exists = probe_media(video)
    if not (3 <= clip_seconds <= 180):
        raise ClutchSiftError("Clip length must be between 3 and 180 seconds.")
    if not (1 <= limit <= 30):
        raise ClutchSiftError("Clip count must be between 1 and 30.")
    if audio_exists:
        levels = sample_audio_dbfs(video)
        if levels and max(levels) > -70 and max(levels) - statistics.median(levels) >= 4:
            return duration, rank_audio_candidates(levels, duration, clip_seconds, limit)
    # Silence or near-constant loudness has no useful peaks. Never pretend the
    # evenly spaced suggestions were found by an intelligent detector.
    return duration, evenly_spaced_candidates(duration, clip_seconds, limit)


def validate_segment(start: float, end: float, duration: float) -> tuple[float, float]:
    if not all(math.isfinite(v) for v in (start, end, duration)):
        raise ClutchSiftError("Start/end must be finite numbers.")
    if start < 0 or end <= start or end > duration + 0.05:
        raise ClutchSiftError(f"Invalid clip range {start:.2f}–{end:.2f} for video length {duration:.2f}s.")
    return max(0, start), min(duration, end)


def export_clip(
    video: Path | str, destination: Path | str, start: float, end: float,
    vertical: bool = True, *, duration: float | None = None,
    layout: str = "fit-blur", encoder: str = "cpu",
) -> Path:
    video = Path(video).resolve()
    destination = Path(destination).resolve()
    total, _ = probe_media(video) if duration is None else (duration, None)
    start, end = validate_segment(start, end, total)
    if destination == video:
        raise ClutchSiftError("Refusing to overwrite the original recording.")
    if layout not in ("fit-blur", "center-crop"):
        raise ClutchSiftError("Layout must be fit-blur or center-crop.")
    if encoder not in ("cpu", "nvenc"):
        raise ClutchSiftError("Encoder must be cpu or nvenc.")
    destination.parent.mkdir(parents=True, exist_ok=True)
    args = [find_tool("ffmpeg"), "-nostdin", "-hide_banner", "-loglevel", "error", "-y",
            "-ss", str(start), "-i", str(video), "-t", str(end - start)]
    if vertical:
        # Blurred 9:16 canvas + full uncropped gameplay centered over it.
        # This retains the HUD/gameplay context instead of cutting off 70% of the frame.
        if layout == "fit-blur":
            filt = (
                "[0:v:0]scale=720:1280:force_original_aspect_ratio=increase,"
                "crop=720:1280,boxblur=20:1[bg];"
                "[0:v:0]scale=720:1280:force_original_aspect_ratio=decrease[fg];"
                "[bg][fg]overlay=(W-w)/2:(H-h)/2,setsar=1,format=yuv420p[v]"
            )
        else:
            filt = ("[0:v:0]scale=720:1280:force_original_aspect_ratio=increase,"
                    "crop=720:1280,setsar=1,format=yuv420p[v]")
        args.extend(["-filter_complex", filt, "-map", "[v]"])
    else:
        args.extend(["-map", "0:v:0"])
    video_args = (["-c:v", "h264_nvenc", "-preset", "p4", "-cq", "23", "-b:v", "0"]
                  if encoder == "nvenc" else ["-c:v", "libx264", "-preset", "veryfast", "-crf", "23"])
    args.extend(["-map", "0:a:0?", *video_args,
                 "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k",
                 "-movflags", "+faststart", str(destination)])
    run_command(args)
    return destination


def write_srt(video_clip: Path | str, *, model_name: str = "base") -> Path:
    """Optional offline captions. First run downloads the transcription model."""
    try:
        from faster_whisper import WhisperModel  # type: ignore
    except ImportError as exc:
        raise ClutchSiftError(
            "Captions require an optional package. Run: pip install -r requirements-captions.txt"
        ) from exc
    clip = Path(video_clip).resolve()
    model = WhisperModel(model_name, device="cpu", compute_type="int8")
    segments, _ = model.transcribe(str(clip), beam_size=3, vad_filter=True)
    path = clip.with_suffix(".srt")
    with path.open("w", encoding="utf-8") as f:
        for i, segment in enumerate(segments, 1):
            text = segment.text.strip()
            if not text:
                continue
            f.write(f"{i}\n{_srt_time(segment.start)} --> {_srt_time(segment.end)}\n{text}\n\n")
    return path


def _srt_time(seconds: float) -> str:
    milliseconds = max(0, round(seconds * 1000))
    hours, rest = divmod(milliseconds, 3600000)
    minutes, rest = divmod(rest, 60000)
    secs, ms = divmod(rest, 1000)
    return f"{hours:02}:{minutes:02}:{secs:02},{ms:03}"


def burn_subtitles(clip: Path | str, srt: Path | str) -> Path:
    """Optional subtitle burn-in using FFmpeg's libass subtitles filter."""
    clip, srt = Path(clip).resolve(), Path(srt).resolve()
    if clip.parent != srt.parent:
        raise ClutchSiftError("SRT must be in the same directory as the clip.")
    # Avoid FFmpeg's Windows drive-colon escaping by using the SRT basename and cwd.
    if "'" in srt.name or ":" in srt.name or "\\" in srt.name:
        raise ClutchSiftError("Unsupported caption filename.")
    output = clip.with_name(clip.stem + "_captioned.mp4")
    args = [find_tool("ffmpeg"), "-nostdin", "-hide_banner", "-loglevel", "error", "-y",
            "-i", str(clip), "-vf", f"subtitles=filename='{srt.name}'",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "22",
            "-c:a", "copy", "-movflags", "+faststart", str(output)]
    run_command(args, cwd=srt.parent)
    return output


def write_manifest(video: Path, highlights: list[Highlight], folder: Path) -> Path:
    folder.mkdir(parents=True, exist_ok=True)
    manifest = folder / "highlights.json"
    manifest.write_text(json.dumps({"source": str(video), "candidates": [asdict(h) for h in highlights]},
                                   indent=2), encoding="utf-8")
    return manifest


def pretty_time(seconds: float) -> str:
    seconds = max(0, int(seconds))
    hours, remainder = divmod(seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    return f"{hours:02}:{minutes:02}:{secs:02}"
