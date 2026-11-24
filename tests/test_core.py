"""Run with: python -m unittest discover -s tests -v"""
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from clutchsift.core import (
    ClutchSiftError, _srt_time, evenly_spaced_candidates, export_clip,
    find_highlights, pretty_time, probe_media, rank_audio_candidates,
    validate_segment, write_manifest,
)


class CoreUnitTests(unittest.TestCase):
    def test_timestamp_formats(self):
        self.assertEqual(pretty_time(3661), "01:01:01")
        self.assertEqual(_srt_time(61.234), "00:01:01,234")

    def test_audio_peak_detection(self):
        levels = [-46.0] * 100
        levels[20] = -10
        levels[72] = -6
        items = rank_audio_candidates(levels, 100, clip_seconds=20, limit=2)
        self.assertEqual(len(items), 2)
        self.assertTrue(any(x.start <= 20 <= x.end for x in items))
        self.assertTrue(any(x.start <= 72 <= x.end for x in items))
        self.assertLessEqual(items[0].end, items[1].start)
        self.assertTrue(all(x.method == "audio" for x in items))

    def test_no_audio_fallback_labeled(self):
        clips = evenly_spaced_candidates(20, 8, 3)
        self.assertEqual(len(clips), 3)
        self.assertTrue(all(c.method == "sampling" for c in clips))

    def test_invalid_segment(self):
        for begin, end in [(0, 0), (5, 2), (-3, 5), (0, 11)]:
            with self.assertRaises(ClutchSiftError):
                validate_segment(begin, end, 10)
        self.assertEqual(validate_segment(1, 5, 10), (1, 5))

    def test_manifest(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            clip = evenly_spaced_candidates(10, 5, 1)[0]
            path = write_manifest(Path("demo.mp4"), [clip], folder)
            self.assertIn('"method": "sampling"', path.read_text())


@unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "Needs FFmpeg")
class FFmpegIntegrationTests(unittest.TestCase):
    def test_probe_and_portrait_export(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            source = folder / "source.mp4"
            dest = folder / "portrait.mp4"
            creation = subprocess.run([
                "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
                "-f", "lavfi", "-i", "color=c=blue:s=320x180:r=12",
                "-f", "lavfi", "-i", "sine=frequency=500:sample_rate=44100",
                "-t", "4", "-c:v", "libx264", "-pix_fmt", "yuv420p",
                "-c:a", "aac", str(source),
            ], capture_output=True, text=True)
            self.assertEqual(creation.returncode, 0, creation.stderr)
            duration, audio = probe_media(source)
            self.assertTrue(audio)
            self.assertAlmostEqual(duration, 4, delta=0.2)
            total, candidates = find_highlights(source, clip_seconds=3, limit=1)
            self.assertTrue(candidates)
            export_clip(source, dest, candidates[0].start, candidates[0].end,
                        vertical=True, duration=total)
            self.assertTrue(dest.exists() and dest.stat().st_size > 1000)
            info = subprocess.run([
                "ffprobe", "-v", "error", "-select_streams", "v:0",
                "-show_entries", "stream=width,height", "-of", "csv=p=0", str(dest),
            ], capture_output=True, text=True)
            self.assertEqual(info.stdout.strip(), "720,1280")


if __name__ == "__main__":
    unittest.main()
