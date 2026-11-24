"""Exercise editor callbacks using a hidden window and generated media."""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from clutchsift.core import burn_subtitles


@unittest.skipUnless(os.name == "nt" and shutil.which("ffmpeg") and shutil.which("ffprobe"),
                     "Windows desktop and FFmpeg required")
class DesktopTests(unittest.TestCase):
    def test_open_scan_trim_export_and_caption(self):
        from clutchsift.app import ClutchSiftApp
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            source = folder / "Player's [round] & replay.mp4"
            subprocess.run(["ffmpeg", "-loglevel", "error", "-f", "lavfi", "-i",
                            "color=red:s=160x90:r=8:d=4", "-c:v", "libx264", str(source)],
                           check=True)
            app = ClutchSiftApp()
            app.root.withdraw()
            self.addCleanup(app.root.destroy)
            def run_sync(worker, success, note):
                success(worker())
            with patch.object(app, "_run_background", side_effect=run_sync), \
                 patch("clutchsift.app.filedialog.askopenfilename", return_value=str(source)), \
                 patch("clutchsift.app.filedialog.askdirectory", return_value=str(folder)), \
                 patch("clutchsift.app.messagebox.showinfo"):
                app.choose_video()
                app.analyze()
                app.tree.selection_set("0")
                app.start_edit.set("1")
                app.end_edit.set("3")
                app.apply_edit()
                app.layout.set("center-crop")
                app.export()
            clip = folder / "run-001" / "clip_01.mp4"
            caption = folder / "Player's [round] & replay.srt"
            caption.write_text("1\n00:00:00,000 --> 00:00:01,500\nCheckpoint\n", encoding="utf-8")
            output = burn_subtitles(clip, caption)
            self.assertGreater(output.stat().st_size, 1000)
            self.assertEqual(app.highlights[0].duration, 2)
