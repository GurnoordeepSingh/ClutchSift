import unittest
from unittest.mock import patch

from clutchsift.ai_scan import VisionHighlight, assess, find_ai_highlights
from clutchsift.core import ClutchSiftError, Highlight


class SelectionTests(unittest.TestCase):
    def test_quiet_requested_window_can_displace_peak(self):
        peak = Highlight(0, 10, 5, 12, -8)
        def rate(video, clip, focus, model):
            score = 4 if clip.start == 90 else 1
            return VisionHighlight(clip.start, clip.end, clip.peak_at, 0, -20, "AI vision",
                                   score, "checkpoint" if score == 4 else "menu")
        with patch("clutchsift.ai_scan.ollama", return_value={"capabilities": ["vision"]}), \
             patch("clutchsift.ai_scan.find_hybrid_highlights", return_value=(100, [peak])), \
             patch("clutchsift.ai_scan.assess", side_effect=rate):
            _, picks = find_ai_highlights("vod.mp4", 10, 1, focus="checkpoint")
        self.assertEqual([(p.start, p.evidence) for p in picks], [(90, "checkpoint")])

    def test_invalid_score_does_not_become_a_highlight(self):
        with patch("clutchsift.ai_scan.storyboard", return_value="jpeg"), \
             patch("clutchsift.ai_scan.ollama", return_value={"message": {
                 "content": '{"score": true, "evidence": "win"}'}}):
            with self.assertRaises(ClutchSiftError):
                assess("vod.mp4", Highlight(0, 3, 1, 0, -20), "win", "local")

    def test_remote_model_rejected_before_decoding(self):
        with patch("clutchsift.ai_scan.ollama", return_value={
                "capabilities": ["vision"], "remote_model": "cloud"}):
            with self.assertRaisesRegex(ClutchSiftError, "locally installed"):
                find_ai_highlights("unread.mp4")
