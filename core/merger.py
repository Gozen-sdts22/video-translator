"""Merge transcription and diarization results."""


def find_best_speaker(
    trans_start: float,
    trans_end: float,
    diarization_segments: list[dict],
) -> str:
    """
    Find the speaker with the maximum overlap for a transcription segment.

    Args:
        trans_start: Start time of the transcription segment.
        trans_end: End time of the transcription segment.
        diarization_segments: List of diarization segments.

    Returns:
        Speaker ID with the maximum overlap, or "UNKNOWN" if no overlap.
    """
    best_speaker = "UNKNOWN"
    best_overlap = 0.0

    for d_seg in diarization_segments:
        # Calculate overlap
        overlap_start = max(trans_start, d_seg["start"])
        overlap_end = min(trans_end, d_seg["end"])
        overlap = max(0.0, overlap_end - overlap_start)

        if overlap > best_overlap:
            best_overlap = overlap
            best_speaker = d_seg["speaker"]

    return best_speaker


def merge_segments(
    transcription_segments: list[dict],
    diarization_segments: list[dict] | None = None,
) -> list[dict]:
    """
    Merge transcription segments with speaker diarization results.

    Args:
        transcription_segments: List of transcription segments, each containing:
            - start: Start time in seconds
            - end: End time in seconds
            - text: Transcribed text
        diarization_segments: List of diarization segments, each containing:
            - start: Start time in seconds
            - end: End time in seconds
            - speaker: Speaker ID
            If None, all segments will be assigned to "SPEAKER_00".

    Returns:
        List of merged segments with speaker information added.
    """
    if not transcription_segments:
        return []

    # If no diarization, assign all to default speaker
    if not diarization_segments:
        return [
            {
                "start": seg["start"],
                "end": seg["end"],
                "text": seg["text"],
                "speaker": "SPEAKER_00",
            }
            for seg in transcription_segments
        ]

    # Merge transcription with diarization
    merged = []
    for trans_seg in transcription_segments:
        speaker = find_best_speaker(
            trans_seg["start"],
            trans_seg["end"],
            diarization_segments,
        )

        merged.append(
            {
                "start": trans_seg["start"],
                "end": trans_seg["end"],
                "text": trans_seg["text"],
                "speaker": speaker,
            }
        )

    return merged


def consolidate_segments(
    segments: list[dict],
    max_gap: float = 0.5,
    max_duration: float = 10.0,
) -> list[dict]:
    """
    Consolidate consecutive segments from the same speaker.

    This helps create more natural subtitle segments by combining
    short consecutive utterances from the same speaker.

    Args:
        segments: List of merged segments.
        max_gap: Maximum gap in seconds between segments to consolidate.
        max_duration: Maximum duration for a consolidated segment.

    Returns:
        Consolidated list of segments.
    """
    if not segments:
        return []

    consolidated = []
    current = None

    for seg in segments:
        if current is None:
            current = seg.copy()
            continue

        # Check if we can merge with current segment
        same_speaker = seg["speaker"] == current["speaker"]
        small_gap = seg["start"] - current["end"] <= max_gap
        within_duration = seg["end"] - current["start"] <= max_duration

        if same_speaker and small_gap and within_duration:
            # Merge segments
            current["end"] = seg["end"]
            current["text"] = current["text"] + " " + seg["text"]
        else:
            # Save current and start new
            consolidated.append(current)
            current = seg.copy()

    # Don't forget the last segment
    if current is not None:
        consolidated.append(current)

    return consolidated
