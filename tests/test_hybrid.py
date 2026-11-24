from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from clutchsift.captions import _ass_escape, _ass_timestamp, save_karaoke_ass, save_srt
from clutchsift.core import ClutchSiftError, export_clip, probe_media
from clutchsift.hybrid import rank_hybrid_candidates, sample_visual_motion
from clutchsift.metadata import normalize_metadata


class HybridTests(unittest.TestCase):
    def test_motion_without_audio_surfaces_candidate(self):
        motion = [.001] * 85
        motion[45] = .8
        clips = rank_hybrid_candidates([], motion, 85, clip_seconds=20, limit=2)
        self.assertTrue(any(c.start <= 45 <= c.end for c in clips))
        self.assertTrue(any(c.method == "motion" for c in clips))

    def test_static_silent_fallback_not_falsely_labeled(self):
        clips = rank_hybrid_candidates([-80] * 60, [0] * 60, 60, 15, 3)
        self.assertEqual(len(clips), 3)
        self.assertTrue(all(c.method == "sampling" for c in clips))

    def test_hybrid_uses_both(self):
        audio = [-60] * 100
        motion = [.01] * 100
        audio[15] = -3
        motion[75] = .6
        clips = rank_hybrid_candidates(audio, motion, 100, 20, 3)
        self.assertTrue(any(c.method == "audio+motion" for c in clips))
        self.assertTrue(any(c.start <= 15 <= c.end for c in clips))
        self.assertTrue(any(c.start <= 75 <= c.end for c in clips))

    def test_metadata_normalization(self):
        result = normalize_metadata({"title": "A" * 100, "description": "First line\nNext",
                                     "hashtags": ["#Gaming", "shorts!!", "AI", "extra"]})
        self.assertEqual(len(result["title"]), 70)
        self.assertEqual(result["hashtags"], ["#Gaming", "#shorts", "#AI"])
        self.assertTrue(result["human_review_required"])

    def test_caption_writers(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            segments = [{"start": .5, "end": 1.9, "text": "That was insane!",
                         "words": [{"start": .5, "end": .9, "text": "That"},
                                   {"start": .9, "end": 1.4, "text": "was"},
                                   {"start": 1.4, "end": 1.9, "text": "insane!"}]}]
            srt = save_srt(segments, folder / "out.srt")
            ass = save_karaoke_ass(segments, folder / "out.ass")
            self.assertIn("00:00:00,500", srt.read_text())
            self.assertIn("{\\kf40}That", ass.read_text())
            self.assertEqual(_ass_timestamp(61.5), "0:01:01.50")
            self.assertEqual(_ass_escape("{hello}"), "(hello)")


@unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "FFmpeg required")
class VideoIntegrationTests(unittest.TestCase):
    def test_motion_and_center_crop_export(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "source.mp4"
            dst = Path(tmp) / "portrait.mp4"
            command = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                       "-f", "lavfi", "-i", "testsrc2=s=320x180:r=10:d=4",
                       "-c:v", "libx264", "-pix_fmt", "yuv420p", str(src)]
            p = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(p.returncode, 0, p.stderr)
            frames = sample_visual_motion(src)
            self.assertGreaterEqual(len(frames), 3)
            duration, _ = probe_media(src)
            with self.assertRaises(ClutchSiftError):
                export_clip(src, src, 0, 2, duration=duration)
            export_clip(src, dst, 0, 2, layout="center-crop", duration=duration)
            p = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0",
                                "-show_entries", "stream=width,height", "-of", "csv=p=0", str(dst)],
                               capture_output=True, text=True)
            self.assertEqual(p.stdout.strip(), "720,1280")


if __name__ == "__main__":
    unittest.main()

class VisionUnitTests(unittest.TestCase):
    def test_visual_report_schema_without_network(self):
        import io
        import json
        from unittest.mock import patch
        from clutchsift.core import Highlight
        from clutchsift.vision import review_candidate
        fake_response = io.BytesIO(json.dumps({"message": {"content": json.dumps({
            "visual_summary": "A paused game screen.",
            "visible_clues": ["Health bar visible", "HUD visible"],
            "uncertainty_note": "No action is visible between the frames."})}}).encode())
        class ContextFile:
            def __enter__(self): return fake_response
            def __exit__(self, *_): return False
        h = Highlight(0, 10, 5, 0, -12, "audio")
        with patch("clutchsift.vision.extract_jpeg_frame", return_value=b"JPEG"), \
             patch("clutchsift.vision.urlopen", return_value=ContextFile()):
            report = review_candidate("dummy.mp4", h)
        self.assertEqual(report["candidate"]["method"], "audio")
        self.assertIn("Sparse snapshots", report["disclaimer"])
        self.assertEqual(len(report["visible_clues"]), 2)

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "FFmpeg required")
    def test_extract_jpeg_frame(self):
        from clutchsift.vision import extract_jpeg_frame
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "clip.mp4"
            p = subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                                "-f", "lavfi", "-i", "color=c=red:s=320x180:r=5:d=1",
                                "-c:v", "libx264", str(src)], capture_output=True, text=True)
            self.assertEqual(p.returncode, 0, p.stderr)
            jpeg = extract_jpeg_frame(src, .25)
            self.assertGreater(len(jpeg), 100)
            self.assertEqual(jpeg[:2], b"\xff\xd8")
