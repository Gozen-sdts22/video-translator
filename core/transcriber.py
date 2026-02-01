"""Speech-to-text transcription using Faster-Whisper."""

from typing import Optional
from pathlib import Path


class TranscriptionError(Exception):
    """Exception raised when transcription fails."""

    pass


# Default prompt for idol-related content
DEFAULT_INITIAL_PROMPT = (
    "推しメン、握手会、センター、チェキ、総選挙、ランキング、"
    "メンバー、ファン、ライブ、コンサート、MV、楽曲"
)


def transcribe(
    audio_path: str,
    model_name: str = "large-v3",
    device: str = "cuda",
    compute_type: str = "float16",
    initial_prompt: str | None = None,
    language: str = "ja",
) -> list[dict]:
    """
    Transcribe audio to text using Faster-Whisper.

    Args:
        audio_path: Path to the audio file (WAV format recommended).
        model_name: Whisper model to use (e.g., "large-v3", "medium", "small").
        device: Device to use ("cuda" or "cpu").
        compute_type: Compute type for inference ("float16", "int8", etc.).
        initial_prompt: Initial prompt to guide transcription.
                       Helps with domain-specific terminology.
        language: Language code for transcription.

    Returns:
        List of transcription segments, each containing:
        - start: Start time in seconds
        - end: End time in seconds
        - text: Transcribed text

    Raises:
        TranscriptionError: If transcription fails.
        FileNotFoundError: If the audio file doesn't exist.
    """
    audio_path = Path(audio_path)

    if not audio_path.exists():
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    if initial_prompt is None:
        initial_prompt = DEFAULT_INITIAL_PROMPT

    try:
        from faster_whisper import WhisperModel
    except ImportError:
        raise TranscriptionError(
            "faster-whisper is not installed. "
            "Please install it with: pip install faster-whisper"
        )

    try:
        # Load the model
        model = WhisperModel(
            model_name,
            device=device,
            compute_type=compute_type,
        )

        # Transcribe the audio
        segments, info = model.transcribe(
            str(audio_path),
            language=language,
            initial_prompt=initial_prompt,
            vad_filter=True,  # Voice activity detection for better segmentation
            vad_parameters=dict(
                min_silence_duration_ms=500,
            ),
        )

        # Convert segments to list of dicts
        result = []
        for segment in segments:
            result.append(
                {
                    "start": segment.start,
                    "end": segment.end,
                    "text": segment.text.strip(),
                }
            )

        return result

    except Exception as e:
        raise TranscriptionError(f"Transcription failed: {e}") from e


def get_transcription_info(
    audio_path: str,
    model_name: str = "large-v3",
    device: str = "cuda",
    compute_type: str = "float16",
) -> dict:
    """
    Get information about the audio without full transcription.

    Args:
        audio_path: Path to the audio file.
        model_name: Whisper model to use.
        device: Device to use.
        compute_type: Compute type.

    Returns:
        Dictionary containing:
        - language: Detected language
        - language_probability: Confidence in language detection
        - duration: Duration in seconds
    """
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        raise TranscriptionError(
            "faster-whisper is not installed. "
            "Please install it with: pip install faster-whisper"
        )

    try:
        model = WhisperModel(
            model_name,
            device=device,
            compute_type=compute_type,
        )

        # Run with a short segment to get info
        _, info = model.transcribe(
            str(audio_path),
            language=None,  # Auto-detect
        )

        return {
            "language": info.language,
            "language_probability": info.language_probability,
            "duration": info.duration,
        }

    except Exception as e:
        raise TranscriptionError(f"Failed to get transcription info: {e}") from e
