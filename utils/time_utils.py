"""Time conversion utilities for subtitle generation."""


def seconds_to_ass_time(seconds: float) -> str:
    """
    Convert seconds to ASS time format (H:MM:SS.cc).

    Args:
        seconds: Time in seconds.

    Returns:
        Time string in ASS format (e.g., "0:01:23.45").
    """
    if seconds < 0:
        seconds = 0

    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60

    # ASS format uses centiseconds (2 decimal places)
    return f"{hours}:{minutes:02d}:{secs:05.2f}"


def ass_time_to_seconds(time_str: str) -> float:
    """
    Convert ASS time format to seconds.

    Args:
        time_str: Time string in ASS format (e.g., "0:01:23.45").

    Returns:
        Time in seconds.

    Raises:
        ValueError: If the time string is invalid.
    """
    parts = time_str.split(":")

    if len(parts) != 3:
        raise ValueError(f"Invalid ASS time format: {time_str}")

    try:
        hours = int(parts[0])
        minutes = int(parts[1])
        seconds = float(parts[2])

        return hours * 3600 + minutes * 60 + seconds
    except (ValueError, IndexError) as e:
        raise ValueError(f"Invalid ASS time format: {time_str}") from e


def format_duration(seconds: float) -> str:
    """
    Format a duration in seconds to a human-readable string.

    Args:
        seconds: Duration in seconds.

    Returns:
        Human-readable duration string (e.g., "1h 23m 45s").
    """
    if seconds < 0:
        seconds = 0

    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)

    parts = []
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0 or hours > 0:
        parts.append(f"{minutes}m")
    parts.append(f"{secs}s")

    return " ".join(parts)
