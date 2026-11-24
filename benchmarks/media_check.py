"""Exercise ClutchSift's real export API using generated media in a private temporary folder."""

import argparse
import json
from pathlib import Path
import shutil
import statistics
import subprocess
import sys
import tempfile
import time


def command(*args):
    result = subprocess.run(list(map(str, args)), capture_output=True, timeout=120)
    if result.returncode:
        raise RuntimeError(result.stderr.decode(errors="replace")[-2000:])
    return result.stdout


def ffmpeg(*args):
    return command("ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error", *args)


def sample(path, second):
    return ffmpeg("-ss", second, "-i", path, "-frames:v", "1", "-vf", "scale=24:24,format=gray",
                  "-f", "rawvideo", "-pix_fmt", "gray", "pipe:1")


def verify(path, expect_audio):
    info = json.loads(command("ffprobe", "-v", "error", "-show_streams", "-show_format",
                              "-of", "json", path))
    video, = [s for s in info["streams"] if s["codec_type"] == "video"]
    audio = [s["codec_name"] for s in info["streams"] if s["codec_type"] == "audio"]
    duration = float(info["format"]["duration"])
    if (video["width"], video["height"], video["sample_aspect_ratio"], video["codec_name"],
            video["pix_fmt"]) != (720, 1280, "1:1", "h264", "yuv420p"):
        raise ValueError("Unexpected export geometry, codec, or pixel format")
    if abs(duration - 2) > .075 or audio != (["aac"] if expect_audio else []):
        raise ValueError("Unexpected trim duration or audio stream")
    early, late = sample(path, .01), sample(path, 1.90)
    if any(len(frame) != 576 or statistics.mean(frame) < 30 for frame in (early, late)):
        raise ValueError("Trim included black frames from outside selected interval")
    ffmpeg("-xerror", "-i", path, "-f", "null", "-")
    return dict(width=video["width"], height=video["height"], audio=audio,
                duration_seconds=duration, full_decode="pass"), early


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--nvenc", action="store_true", help="Require a successful real hardware export")
    args = parser.parse_args()
    repo = args.repo.resolve()
    if not (repo / "clutchsift" / "core.py").is_file():
        parser.error("--repo must point to the ClutchSift source folder")
    if not all(shutil.which(name) for name in ("ffmpeg", "ffprobe")):
        parser.error("Install ffmpeg and ffprobe on PATH")
    sys.path.insert(0, str(repo))
    from clutchsift.core import export_clip

    report = {}
    with tempfile.TemporaryDirectory(prefix="Clutch Sift [QA] ") as temp:
        root = Path(temp)
        source = root / "-it's [Roblox] & replay #1 日本語.mp4"
        silent = root / "silent.mp4"
        ffmpeg("-f", "lavfi", "-i", "testsrc2=size=480x270:rate=24:duration=4",
               "-f", "lavfi", "-i", "sine=frequency=440:duration=4",
               "-vf", "drawbox=c=black:t=fill:enable='lt(t,1)+gte(t,3)'",
               "-c:v", "libx264", "-c:a", "aac", source)
        ffmpeg("-i", source, "-map", "0:v", "-c", "copy", silent)
        first_frames = {}
        cases = [("center-crop", "cpu", source), ("fit-blur", "cpu", source),
                 ("center-crop", "cpu", silent)]
        if args.nvenc:
            cases.append(("fit-blur", "nvenc", source))
        for i, (layout, encoder, video) in enumerate(cases):
            target = root / f"-it's [portrait] & {i}.mp4"
            started = time.perf_counter()
            export_clip(video, target, 1, 3, vertical=True, layout=layout, encoder=encoder)
            elapsed = time.perf_counter() - started
            properties, frame = verify(target, video == source)
            properties.update(layout=layout, encoder=encoder, export_seconds=round(elapsed, 3))
            report[f"case_{i + 1}"] = properties
            if video == source and encoder == "cpu":
                first_frames[layout] = frame
        difference = statistics.mean(abs(a - b) for a, b in
                                     zip(first_frames["center-crop"], first_frames["fit-blur"]))
        if difference < 2:
            raise ValueError("Two vertical layouts produced visually indistinguishable frames")
    report["mean_gray_difference_between_layouts"] = round(difference, 3)
    report["ffmpeg_version"] = command("ffmpeg", "-version").decode().splitlines()[0]
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
