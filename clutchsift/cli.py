"""Headless runner for reproducible batches and local automation."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .core import burn_subtitles, create_run_folder, export_clip, find_highlights, pretty_time, write_manifest
from .hybrid import find_hybrid_highlights


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(description="ClutchSift: local gaming clip candidates")
    parser.add_argument("video", type=Path, help="Local recording; only use footage you may edit")
    parser.add_argument("--count", type=int, default=5, help="Candidates (1–30)")
    parser.add_argument("--seconds", type=float, default=30, help="Clip length (3–180 seconds)")
    parser.add_argument("--output", type=Path, default=Path("ClutchSift_Exports"))
    parser.add_argument("--mode", choices=["audio", "hybrid"], default="hybrid",
                        help="Hybrid combines audio peaks and visual-motion changes (heuristic)")
    parser.add_argument("--landscape", action="store_true", help="Keep original landscape layout")
    parser.add_argument("--layout", choices=["fit-blur", "center-crop"], default="fit-blur",
                        help="Vertical output: fit full gameplay or crop center")
    parser.add_argument("--encoder", choices=["cpu", "nvenc"], default="cpu",
                        help="NVENC requires suitable NVIDIA GPU and FFmpeg build")
    parser.add_argument("--captions", action="store_true", help="Generate local SRT; optional faster-whisper")
    parser.add_argument("--caption-style", choices=["srt", "karaoke"], default="srt")
    parser.add_argument("--asr-model", default="small",
                        help="Whisper model name (small, medium, large-v3-turbo, etc.)")
    parser.add_argument("--asr-device", choices=["cpu", "cuda", "auto"], default="cpu")
    parser.add_argument("--burn", action="store_true", help="Burn captions into an additional MP4")
    parser.add_argument("--titles", action="store_true", help="Suggest titles using local Ollama (optional)")
    parser.add_argument("--ollama-model", default="qwen3.5:4b")
    parser.add_argument("--vision-review", action="store_true",
                        help="Describe selected sparse frames with local Ollama vision; not game-event detection")
    parser.add_argument("--scan-only", action="store_true", help="Only scan and save JSON")
    args = parser.parse_args(argv)
    if args.burn and not args.captions:
        parser.error("--burn requires --captions")
    if args.scan_only and (args.captions or args.burn or args.titles):
        parser.error("--scan-only cannot create captions, titles, or exports")
    if args.mode == "hybrid":
        duration, clips = find_hybrid_highlights(args.video, args.seconds, args.count)
    else:
        duration, clips = find_highlights(args.video, args.seconds, args.count)
    output = create_run_folder(args.output)
    print("Run folder:", output.resolve())
    manifest = write_manifest(args.video.resolve(), clips, output)
    if args.vision_review:
        from .vision import review_candidate, save_reviews
        reviews = [review_candidate(args.video, item, model=args.ollama_model) for item in clips]
        report = save_reviews(reviews, output / "vision_reviews.json")
        print("Vision observations (verify before believing):", report.resolve())
    print(f"Recording: {pretty_time(duration)} | Mode: {args.mode} | Candidates: {len(clips)}")
    for i, item in enumerate(clips, 1):
        print(f"{i:02}: {pretty_time(item.start)}–{pretty_time(item.end)} [{item.method}]")
        if args.scan_only:
            continue
        clip = output / f"clip_{i:02}.mp4"
        export_clip(args.video, clip, item.start, item.end, vertical=not args.landscape,
                    duration=duration, layout=args.layout, encoder=args.encoder)
        text = ""
        if args.captions or args.titles:
            from .captions import write_captions
            subtitle, text = write_captions(clip, model_name=args.asr_model,
                                            device=args.asr_device, style=args.caption_style)
            if args.burn:
                print("Burned subtitles:", burn_subtitles(clip, subtitle))
        if args.titles:
            from .metadata import suggest_metadata, save_metadata
            metadata = suggest_metadata(text, model=args.ollama_model)
            save_metadata(metadata, clip.with_suffix(".metadata.json"))
            print("Suggested title (review):", metadata["title"])
        print("Saved:", clip.resolve())
    print("Manifest:", manifest.resolve())


if __name__ == "__main__":
    main()
