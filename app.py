#!/usr/bin/env python3
"""
Video Subtitle Generator - CLI Application

Generates Japanese subtitles from video files and translates them to Chinese.
Output is in ASS format compatible with Aegisub.
"""

import argparse
import sys
from pathlib import Path

from config import Config
from core.pipeline import process_video, PipelineError


def print_progress(message: str, ratio: float):
    """Print progress to stdout."""
    bar_width = 40
    filled = int(bar_width * ratio)
    bar = "=" * filled + "-" * (bar_width - filled)
    percentage = int(ratio * 100)
    print(f"\r[{bar}] {percentage:3d}% {message}", end="", flush=True)
    if ratio >= 1.0:
        print()  # New line when complete


def main():
    parser = argparse.ArgumentParser(
        description="Generate Japanese-Chinese subtitles from video files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s video.mp4
  %(prog)s video.mp4 -o subtitles/
  %(prog)s video.mp4 --no-diarization
  %(prog)s video.mp4 --model medium --device cpu

Environment variables:
  CLAUDE_API_KEY  Claude API key (required)
  HF_TOKEN        HuggingFace token (required for speaker diarization)
        """,
    )

    parser.add_argument(
        "video",
        help="Path to the input video file",
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        default="./output",
        help="Output directory for subtitle file (default: ./output)",
    )
    parser.add_argument(
        "--no-diarization",
        action="store_true",
        help="Disable speaker diarization",
    )
    parser.add_argument(
        "--model",
        default="large-v3",
        choices=["tiny", "base", "small", "medium", "large-v2", "large-v3"],
        help="Whisper model to use (default: large-v3)",
    )
    parser.add_argument(
        "--device",
        default="cuda",
        choices=["cuda", "cpu"],
        help="Device for inference (default: cuda)",
    )
    parser.add_argument(
        "--compute-type",
        default="float16",
        choices=["float16", "float32", "int8"],
        help="Compute type for Whisper (default: float16)",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=10,
        help="Translation batch size (default: 10)",
    )
    parser.add_argument(
        "--max-speakers",
        type=int,
        default=4,
        help="Maximum number of speakers to detect (default: 4)",
    )
    parser.add_argument(
        "--prompt",
        default=None,
        help="Initial prompt for Whisper (helps with domain-specific terms)",
    )
    parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="Suppress progress output",
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Validate configuration and exit",
    )

    args = parser.parse_args()

    # Build configuration
    config = Config.from_env()
    config.output_dir = args.output_dir
    config.whisper_model = args.model
    config.whisper_device = args.device
    config.whisper_compute_type = args.compute_type
    config.enable_diarization = not args.no_diarization
    config.translation_batch_size = args.batch_size
    config.max_speakers = args.max_speakers

    if args.prompt:
        config.initial_prompt = args.prompt

    # Validate configuration
    errors = config.validate()
    if errors:
        print("Configuration errors:", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        if args.validate:
            sys.exit(1)
        else:
            print("\nContinuing anyway...", file=sys.stderr)

    if args.validate:
        print("Configuration is valid.")
        sys.exit(0)

    # Check video file
    video_path = Path(args.video)
    if not video_path.exists():
        print(f"Error: Video file not found: {video_path}", file=sys.stderr)
        sys.exit(1)

    # Process video
    print(f"Processing: {video_path}")
    print(f"Output directory: {config.output_dir}")
    print(f"Speaker diarization: {'enabled' if config.enable_diarization else 'disabled'}")
    print()

    try:
        progress_callback = None if args.quiet else print_progress
        output_path = process_video(
            str(video_path),
            config,
            progress_callback=progress_callback,
        )
        print(f"\nSubtitle file generated: {output_path}")
    except PipelineError as e:
        print(f"\nError: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nInterrupted by user", file=sys.stderr)
        sys.exit(130)


if __name__ == "__main__":
    main()
