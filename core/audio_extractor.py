"""Audio extraction from video files using FFmpeg."""

import os
import subprocess
import tempfile
from pathlib import Path


class AudioExtractionError(Exception):
    """Exception raised when audio extraction fails."""

    pass


def extract_audio(video_path: str, output_dir: str | None = None) -> str:
    """
    Extract audio from a video file using FFmpeg.

    Args:
        video_path: Path to the input video file.
        output_dir: Directory for the output audio file.
                   If None, uses a temporary directory.

    Returns:
        Path to the extracted audio file (WAV format).

    Raises:
        AudioExtractionError: If extraction fails.
        FileNotFoundError: If the video file doesn't exist.
    """
    video_path = Path(video_path)

    if not video_path.exists():
        raise FileNotFoundError(f"Video file not found: {video_path}")

    # Determine output path
    if output_dir is None:
        output_dir = tempfile.mkdtemp()
    else:
        os.makedirs(output_dir, exist_ok=True)

    audio_filename = video_path.stem + ".wav"
    audio_path = Path(output_dir) / audio_filename

    # Build FFmpeg command
    # -vn: disable video
    # -acodec pcm_s16le: 16-bit PCM format
    # -ar 16000: 16kHz sample rate (recommended for Whisper)
    # -ac 1: mono channel
    cmd = [
        "ffmpeg",
        "-i",
        str(video_path),
        "-vn",
        "-acodec",
        "pcm_s16le",
        "-ar",
        "16000",
        "-ac",
        "1",
        "-y",  # Overwrite output file if exists
        str(audio_path),
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
        )
    except subprocess.CalledProcessError as e:
        raise AudioExtractionError(
            f"FFmpeg failed with error: {e.stderr}"
        ) from e
    except FileNotFoundError:
        raise AudioExtractionError(
            "FFmpeg not found. Please install FFmpeg and add it to PATH."
        )

    # Verify output file exists
    if not audio_path.exists():
        raise AudioExtractionError(
            f"Audio extraction completed but output file not found: {audio_path}"
        )

    return str(audio_path)


def get_video_duration(video_path: str) -> float:
    """
    Get the duration of a video file in seconds.

    Args:
        video_path: Path to the video file.

    Returns:
        Duration in seconds.

    Raises:
        AudioExtractionError: If duration cannot be determined.
    """
    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        str(video_path),
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
        )
        return float(result.stdout.strip())
    except (subprocess.CalledProcessError, ValueError) as e:
        raise AudioExtractionError(
            f"Failed to get video duration: {e}"
        ) from e
