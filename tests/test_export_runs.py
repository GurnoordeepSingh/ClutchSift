import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import patch

from clutchsift.core import (
    ClutchSiftError, create_run_folder, evenly_spaced_candidates,
    export_clip, validate_segment,
)


class ExportRunTests(unittest.TestCase):
    def test_concurrent_runs_leave_previous_files_alone(self):
        with tempfile.TemporaryDirectory() as tmp:
            parent = Path(tmp)
            original = create_run_folder(parent) / "clip_01.mp4"
            original.write_bytes(b"previous export")
            with ThreadPoolExecutor(max_workers=4) as pool:
                runs = list(pool.map(create_run_folder, [parent] * 6))
            self.assertEqual(len(set(runs)), 6)
            self.assertNotIn(original.parent, runs)
            self.assertEqual(original.read_bytes(), b"previous export")

    def test_failure_keeps_last_good_render(self):
        with tempfile.TemporaryDirectory() as tmp:
            original = Path(tmp) / "source.mp4"
            original.touch()
            target = Path(tmp) / "clip.mp4"
            target.write_bytes(b"good render")

            def fail(args):
                Path(args[-1]).write_bytes(b"partial")
                raise ClutchSiftError("encode interrupted")

            with patch("clutchsift.core.find_tool", return_value="ffmpeg"), \
                 patch("clutchsift.core.run_command", side_effect=fail), \
                 self.assertRaises(ClutchSiftError):
                export_clip(original, target, 0, 1, duration=2)
            self.assertEqual(target.read_bytes(), b"good render")
            self.assertCountEqual(Path(tmp).iterdir(), [original, target])

    def test_sampled_windows_cover_the_recording(self):
        clips = evenly_spaced_candidates(3600, 30, 3)
        self.assertEqual([c.peak_at for c in clips], [15, 1800, 3585])
        self.assertEqual(evenly_spaced_candidates(120, 30, 1)[0].peak_at, 60)

    def test_end_tolerance_cannot_create_empty_range(self):
        with self.assertRaises(ClutchSiftError):
            validate_segment(10.01, 10.02, 10)
