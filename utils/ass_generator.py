"""ASS (Advanced SubStation Alpha) subtitle file generator."""

from pathlib import Path
from .time_utils import seconds_to_ass_time


# Speaker color definitions (ASS uses BGR format: &HBBGGRR)
SPEAKER_COLORS = {
    "SPEAKER_00": "&H00FFFFFF",  # White
    "SPEAKER_01": "&H0000FFFF",  # Yellow
    "SPEAKER_02": "&H00FF8080",  # Light blue
    "SPEAKER_03": "&H008000FF",  # Orange
    "UNKNOWN": "&H00C0C0C0",     # Gray
}

# Default style template
DEFAULT_STYLE_TEMPLATE = (
    "Style: {name},Arial,48,{color},&H000000FF,&H00000000,&H80000000,"
    "0,0,0,0,100,100,0,0,1,2,1,2,10,10,10,1"
)

ASS_HEADER = """[Script Info]
Title: Generated Subtitles
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
{styles}

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


def generate_styles(speakers: list[str]) -> str:
    """
    Generate ASS style definitions for the given speakers.

    Args:
        speakers: List of speaker IDs.

    Returns:
        Style definitions as a string.
    """
    styles = []

    for speaker in speakers:
        color = SPEAKER_COLORS.get(speaker, SPEAKER_COLORS["UNKNOWN"])
        style = DEFAULT_STYLE_TEMPLATE.format(name=speaker, color=color)
        styles.append(style)

    # Add UNKNOWN style if not already present
    if "UNKNOWN" not in speakers:
        style = DEFAULT_STYLE_TEMPLATE.format(
            name="UNKNOWN",
            color=SPEAKER_COLORS["UNKNOWN"],
        )
        styles.append(style)

    return "\n".join(styles)


def escape_ass_text(text: str) -> str:
    """
    Escape special characters for ASS format.

    Args:
        text: Raw text.

    Returns:
        Escaped text safe for ASS format.
    """
    # Replace newlines with ASS line break
    text = text.replace("\n", "\\N")
    # Escape curly braces (used for ASS tags)
    text = text.replace("{", "\\{").replace("}", "\\}")
    return text


def generate_dialogue_line(
    start: float,
    end: float,
    speaker: str,
    text_ja: str,
    text_zh: str = "",
) -> str:
    """
    Generate a single ASS dialogue line.

    Args:
        start: Start time in seconds.
        end: End time in seconds.
        speaker: Speaker ID for style selection.
        text_ja: Japanese text.
        text_zh: Chinese translation (optional).

    Returns:
        ASS dialogue line.
    """
    start_time = seconds_to_ass_time(start)
    end_time = seconds_to_ass_time(end)

    # Combine Japanese and Chinese with line break
    if text_zh:
        text = f"{escape_ass_text(text_ja)}\\N{escape_ass_text(text_zh)}"
    else:
        text = escape_ass_text(text_ja)

    return f"Dialogue: 0,{start_time},{end_time},{speaker},,0,0,0,,{text}"


def generate_ass(
    segments: list[dict],
    output_path: str,
    include_translation: bool = True,
) -> str:
    """
    Generate an ASS subtitle file from translated segments.

    Args:
        segments: List of segments, each containing:
            - start: Start time in seconds
            - end: End time in seconds
            - speaker: Speaker ID
            - text: Japanese text
            - translation: Chinese translation (optional)
        output_path: Path for the output ASS file.
        include_translation: Whether to include Chinese translation.

    Returns:
        Path to the generated ASS file.
    """
    if not segments:
        raise ValueError("No segments provided")

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Collect unique speakers
    speakers = sorted(set(seg.get("speaker", "UNKNOWN") for seg in segments))

    # Generate styles
    styles = generate_styles(speakers)

    # Generate dialogue lines
    dialogues = []
    for seg in segments:
        text_ja = seg.get("text", "")
        text_zh = seg.get("translation", "") if include_translation else ""
        speaker = seg.get("speaker", "UNKNOWN")

        dialogue = generate_dialogue_line(
            start=seg["start"],
            end=seg["end"],
            speaker=speaker,
            text_ja=text_ja,
            text_zh=text_zh,
        )
        dialogues.append(dialogue)

    # Build complete ASS content
    ass_content = ASS_HEADER.format(styles=styles) + "\n".join(dialogues) + "\n"

    # Write to file
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(ass_content)

    return str(output_path)


def generate_ass_from_model(
    segments: list,  # List of Segment objects
    output_path: str,
    include_translation: bool = True,
) -> str:
    """
    Generate an ASS subtitle file from Segment model objects.

    Args:
        segments: List of Segment dataclass objects.
        output_path: Path for the output ASS file.
        include_translation: Whether to include Chinese translation.

    Returns:
        Path to the generated ASS file.
    """
    # Convert Segment objects to dictionaries
    dict_segments = []
    for seg in segments:
        dict_segments.append(
            {
                "start": seg.start,
                "end": seg.end,
                "speaker": seg.speaker,
                "text": seg.text_ja,
                "translation": seg.text_zh,
            }
        )

    return generate_ass(dict_segments, output_path, include_translation)
