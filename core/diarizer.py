"""Speaker diarization using pyannote-audio."""

from pathlib import Path


class DiarizationError(Exception):
    """Exception raised when speaker diarization fails."""

    pass


def diarize(
    audio_path: str,
    hf_token: str,
    min_speakers: int | None = None,
    max_speakers: int | None = 4,
) -> list[dict]:
    """
    Perform speaker diarization on an audio file.

    Args:
        audio_path: Path to the audio file.
        hf_token: HuggingFace token for accessing pyannote models.
        min_speakers: Minimum number of speakers (optional).
        max_speakers: Maximum number of speakers (default: 4).

    Returns:
        List of speaker segments, each containing:
        - start: Start time in seconds
        - end: End time in seconds
        - speaker: Speaker ID (e.g., "SPEAKER_00")

    Raises:
        DiarizationError: If diarization fails.
        FileNotFoundError: If the audio file doesn't exist.
    """
    audio_path = Path(audio_path)

    if not audio_path.exists():
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    if not hf_token:
        raise DiarizationError(
            "HuggingFace token is required for speaker diarization. "
            "Set it via HF_TOKEN environment variable."
        )

    try:
        from pyannote.audio import Pipeline
        import torch
    except ImportError:
        raise DiarizationError(
            "pyannote.audio is not installed. "
            "Please install it with: pip install pyannote.audio"
        )

    try:
        # Load the diarization pipeline
        pipeline = Pipeline.from_pretrained(
            "pyannote/speaker-diarization-3.1",
            use_auth_token=hf_token,
        )

        # Move to GPU if available
        if torch.cuda.is_available():
            pipeline.to(torch.device("cuda"))

        # Run diarization with speaker count constraints
        diarization_params = {}
        if min_speakers is not None:
            diarization_params["min_speakers"] = min_speakers
        if max_speakers is not None:
            diarization_params["max_speakers"] = max_speakers

        diarization = pipeline(str(audio_path), **diarization_params)

        # Convert to list of segments
        result = []
        for turn, _, speaker in diarization.itertracks(yield_label=True):
            result.append(
                {
                    "start": turn.start,
                    "end": turn.end,
                    "speaker": speaker,
                }
            )

        # Sort by start time
        result.sort(key=lambda x: x["start"])

        return result

    except Exception as e:
        raise DiarizationError(f"Speaker diarization failed: {e}") from e


def get_speaker_stats(segments: list[dict]) -> dict:
    """
    Calculate statistics about speakers from diarization results.

    Args:
        segments: List of diarization segments.

    Returns:
        Dictionary with speaker statistics:
        - speakers: List of unique speaker IDs
        - total_duration: Total duration of speech
        - speaker_durations: Duration per speaker
    """
    speakers = set()
    speaker_durations: dict[str, float] = {}

    for segment in segments:
        speaker = segment["speaker"]
        duration = segment["end"] - segment["start"]

        speakers.add(speaker)
        speaker_durations[speaker] = speaker_durations.get(speaker, 0) + duration

    return {
        "speakers": sorted(list(speakers)),
        "total_duration": sum(speaker_durations.values()),
        "speaker_durations": speaker_durations,
    }
