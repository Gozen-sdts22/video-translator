"""Main processing pipeline for video to subtitle conversion."""

import os
from pathlib import Path
from typing import Callable
from concurrent.futures import ThreadPoolExecutor

from config import Config
from .audio_extractor import extract_audio
from .transcriber import transcribe
from .diarizer import diarize
from .merger import merge_segments, consolidate_segments
from .translator import translate_segments
from utils.ass_generator import generate_ass


class PipelineError(Exception):
    """Exception raised when the pipeline fails."""

    pass


def process_video(
    video_path: str,
    config: Config,
    progress_callback: Callable[[str, float], None] | None = None,
) -> str:
    """
    Process a video file and generate subtitles.

    This is the main pipeline that:
    1. Extracts audio from video
    2. Transcribes speech to text
    3. Identifies speakers (optional)
    4. Merges transcription with speaker info
    5. Translates to Chinese
    6. Generates ASS subtitle file

    Args:
        video_path: Path to the input video file.
        config: Configuration object.
        progress_callback: Optional callback for progress updates.
                          Called with (status_message, progress_ratio).

    Returns:
        Path to the generated ASS subtitle file.

    Raises:
        PipelineError: If any step in the pipeline fails.
        FileNotFoundError: If the video file doesn't exist.
    """
    video_path = Path(video_path)

    if not video_path.exists():
        raise FileNotFoundError(f"Video file not found: {video_path}")

    def report_progress(message: str, ratio: float):
        if progress_callback:
            progress_callback(message, ratio)

    try:
        # Step 1: Extract audio
        report_progress("音声抽出中...", 0.05)
        audio_path = extract_audio(str(video_path), config.temp_dir)
        report_progress("音声抽出完了", 0.10)

        # Step 2 & 3: Transcription and Diarization (can run in parallel)
        transcription_segments = None
        diarization_segments = None

        if config.enable_diarization:
            report_progress("文字起こしと話者識別中...", 0.15)

            # Run transcription and diarization in parallel
            with ThreadPoolExecutor(max_workers=2) as executor:
                transcribe_future = executor.submit(
                    transcribe,
                    audio_path,
                    model_name=config.whisper_model,
                    device=config.whisper_device,
                    compute_type=config.whisper_compute_type,
                    initial_prompt=config.initial_prompt,
                )

                diarize_future = executor.submit(
                    diarize,
                    audio_path,
                    hf_token=config.hf_token,
                    max_speakers=config.max_speakers,
                )

                transcription_segments = transcribe_future.result()
                report_progress("文字起こし完了", 0.40)

                diarization_segments = diarize_future.result()
                report_progress("話者識別完了", 0.50)
        else:
            # Only transcription
            report_progress("文字起こし中...", 0.15)
            transcription_segments = transcribe(
                audio_path,
                model_name=config.whisper_model,
                device=config.whisper_device,
                compute_type=config.whisper_compute_type,
                initial_prompt=config.initial_prompt,
            )
            report_progress("文字起こし完了", 0.50)

        # Step 4: Merge transcription with speaker info
        report_progress("セグメント統合中...", 0.55)
        merged_segments = merge_segments(transcription_segments, diarization_segments)

        # Optionally consolidate short segments
        merged_segments = consolidate_segments(merged_segments)
        report_progress("セグメント統合完了", 0.60)

        # Step 5: Translate to Chinese
        report_progress("翻訳中...", 0.65)

        def translation_progress(current: int, total: int):
            # Map translation progress to 0.65-0.90 range
            ratio = 0.65 + (current / total) * 0.25
            report_progress(f"翻訳中... ({current}/{total})", ratio)

        translated_segments = translate_segments(
            merged_segments,
            api_key=config.claude_api_key,
            batch_size=config.translation_batch_size,
            model=config.claude_model,
            max_retries=config.max_retries,
            progress_callback=translation_progress,
        )
        report_progress("翻訳完了", 0.90)

        # Step 6: Generate ASS file
        report_progress("字幕ファイル生成中...", 0.92)

        output_filename = video_path.stem + ".ass"
        output_path = Path(config.output_dir) / output_filename

        ass_path = generate_ass(translated_segments, str(output_path))
        report_progress("完了", 1.0)

        # Clean up temporary audio file
        try:
            os.remove(audio_path)
        except OSError:
            pass  # Ignore cleanup errors

        return ass_path

    except Exception as e:
        raise PipelineError(f"Pipeline failed: {e}") from e


def process_video_simple(
    video_path: str,
    claude_api_key: str,
    hf_token: str = "",
    enable_diarization: bool = True,
    output_dir: str = "./output",
) -> str:
    """
    Simplified interface for video processing with minimal configuration.

    Args:
        video_path: Path to the input video file.
        claude_api_key: Claude API key for translation.
        hf_token: HuggingFace token for diarization (optional).
        enable_diarization: Whether to enable speaker diarization.
        output_dir: Output directory for the subtitle file.

    Returns:
        Path to the generated ASS subtitle file.
    """
    config = Config(
        claude_api_key=claude_api_key,
        hf_token=hf_token,
        enable_diarization=enable_diarization and bool(hf_token),
        output_dir=output_dir,
    )

    return process_video(video_path, config)
