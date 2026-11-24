"""Transparent multi-signal highlight candidate ranking.

The detector is a *heuristic*: it does not recognize kills, jokes, or virality.
Motion and audio peaks provide explainable candidate evidence for manual review.
"""
from __future__ import annotations

from pathlib import Path
import math
import statistics
import subprocess

from .core import (ClutchSiftError, Highlight, evenly_spaced_candidates,
                   find_tool, probe_media, sample_audio_dbfs)

FRAME_WIDTH, FRAME_HEIGHT = 64, 36


def sample_visual_motion(video: Path | str, fps: int = 1) -> list[float]:
    """Decode downscaled 8-bit greyscale video at 1 FPS and measure frame changes.

    Each output corresponds to approximately one second. A scene cut or camera
    motion can raise this score; neither guarantees an interesting game event.
    Video bytes are streamed, so the whole recording is never loaded into RAM.
    """
    if fps != 1:
        raise ValueError("Only 1 FPS is supported for alignment with audio bins.")
    cmd = [find_tool("ffmpeg"), "-nostdin", "-hide_banner", "-loglevel", "error",
           "-i", str(Path(video).resolve()), "-map", "0:v:0", "-an",
           "-vf", f"fps={fps},scale={FRAME_WIDTH}:{FRAME_HEIGHT}:flags=fast_bilinear,format=gray",
           "-f", "rawvideo", "pipe:1"]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    assert proc.stdout is not None
    frame_bytes = FRAME_WIDTH * FRAME_HEIGHT
    previous: bytes | None = None
    output: list[float] = []
    try:
        while True:
            data = proc.stdout.read(frame_bytes)
            if not data:
                break
            if len(data) != frame_bytes:
                break
            if previous is None:
                output.append(0.0)
            else:
                difference = sum(abs(a - b) for a, b in zip(previous, data))
                output.append(difference / (frame_bytes * 255.0))
            previous = data
    except BaseException:
        proc.kill()
        proc.communicate()
        raise
    finally:
        proc.stdout.close()
    error = proc.stderr.read().decode(errors="replace") if proc.stderr else ""
    if proc.stderr:
        proc.stderr.close()
    if proc.wait() != 0:
        raise ClutchSiftError("Video motion sampling failed: " + error[-1500:])
    return output


def _nonoverlap_candidates(scores: list[tuple[float, int, float, float]],
                           duration: float, clip_seconds: float, limit: int,
                           levels: list[float], method: str) -> list[Highlight]:
    clip_seconds = min(duration, clip_seconds)
    results: list[Highlight] = []
    for score, index, jump, motion in sorted(scores, reverse=True):
        if score < 0.03:
            break
        peak = min(duration, index + 0.5)
        start = max(0.0, min(duration - clip_seconds, peak - clip_seconds * 0.65))
        end = start + clip_seconds
        if any(max(0, min(end, r.end) - max(start, r.start)) > clip_seconds * .1
               for r in results):
            continue
        db = levels[index] if index < len(levels) else -120.0
        results.append(Highlight(round(start, 2), round(end, 2), round(peak, 2),
                                 round(jump, 1), round(db, 1), method))
        if len(results) >= limit:
            break
    return sorted(results, key=lambda x: x.start)


def rank_hybrid_candidates(levels: list[float], visual_motion: list[float],
                           duration: float, clip_seconds: float = 30,
                           limit: int = 5) -> list[Highlight]:
    """Combine surprise in sound level with significant motion/scene transitions.

    Motion scores are automatically adapted to each recording. A fully silent
    scene can still surface in visual-only mode; constant/noisy footage falls
    back to explicitly labelled sampled ranges.
    """
    if not (duration > 0 and 3 <= clip_seconds <= 180 and 1 <= limit <= 30):
        raise ValueError("Invalid duration, clip length, or clip count.")
    if not levels and not visual_motion:
        return evenly_spaced_candidates(duration, clip_seconds, limit)
    n = max(len(levels), len(visual_motion))
    base = statistics.median(levels) if levels else -120.0
    motion_median = statistics.median(visual_motion) if visual_motion else 0.0
    sorted_motion = sorted(visual_motion)
    motion_p90 = sorted_motion[int(.9 * (len(sorted_motion) - 1))] if sorted_motion else 0.0
    motion_scale = max(.02, motion_p90 - motion_median)
    has_audio = bool(levels) and max(levels) - base >= 4
    has_motion = bool(visual_motion) and max(visual_motion) - motion_median > .02
    if not has_audio and not has_motion:
        return evenly_spaced_candidates(duration, clip_seconds, limit)
    scored = []
    for i in range(n):
        loudness = levels[i] if i < len(levels) else base
        local = statistics.median(levels[max(0, i - 12):min(len(levels), i + 13)]) if i < len(levels) else base
        jump = max(0.0, loudness - local)
        audio_score = min(1.0, jump / 18.0 + max(0., loudness - base) / 36.0) if has_audio else 0.0
        motion = visual_motion[i] if i < len(visual_motion) else 0.0
        visual_score = min(1., max(0.0, motion - motion_median) / motion_scale) if has_motion else 0.0
        if has_audio and has_motion:
            combined = .65 * audio_score + .35 * visual_score
        elif has_audio:
            combined = audio_score
        else:
            combined = visual_score
        scored.append((combined, i, jump, visual_score))
    method = "audio+motion" if has_audio and has_motion else ("audio" if has_audio else "motion")
    return _nonoverlap_candidates(scored, duration, clip_seconds, limit, levels, method) or \
           evenly_spaced_candidates(duration, clip_seconds, limit)


def find_hybrid_highlights(video: Path | str, clip_seconds: float = 30,
                           limit: int = 5) -> tuple[float, list[Highlight]]:
    if not (3 <= clip_seconds <= 180 and 1 <= limit <= 30):
        raise ClutchSiftError("Clip length must be 3–180s and count must be 1–30.")
    duration, audio = probe_media(video)
    levels = sample_audio_dbfs(video) if audio else []
    motion = sample_visual_motion(video)
    return duration, rank_hybrid_candidates(levels, motion, duration, clip_seconds, limit)
