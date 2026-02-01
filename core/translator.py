"""Translation using Claude API."""

import re
import time
from typing import Callable


class TranslationError(Exception):
    """Exception raised when translation fails."""

    pass


TRANSLATION_PROMPT = """あなたはアイドルコンテンツの専門翻訳者です。
以下の日本語を中国語（簡体字）に翻訳してください。

ルール:
- 自然で流暢な中国語にする
- アイドル用語は適切に翻訳する（例: 推し→本命/推、センター→C位、握手会→握手会/签名会）
- 番号付きで出力する
- 翻訳のみ出力し、説明は不要
- 各行の番号は入力と同じ番号を使用する

入力:
{input_text}

出力:"""


def translate_batch(
    texts: list[str],
    api_key: str,
    model: str = "claude-sonnet-4-20250514",
    max_retries: int = 3,
    retry_delay_base: float = 1.0,
) -> list[str]:
    """
    Translate a batch of Japanese texts to Chinese using Claude API.

    Args:
        texts: List of Japanese texts to translate.
        api_key: Claude API key.
        model: Claude model to use.
        max_retries: Maximum number of retry attempts.
        retry_delay_base: Base delay for exponential backoff.

    Returns:
        List of Chinese translations in the same order.

    Raises:
        TranslationError: If translation fails after all retries.
    """
    if not texts:
        return []

    if not api_key:
        raise TranslationError(
            "Claude API key is required. Set it via CLAUDE_API_KEY environment variable."
        )

    try:
        import anthropic
    except ImportError:
        raise TranslationError(
            "anthropic package is not installed. "
            "Please install it with: pip install anthropic"
        )

    # Format input with numbered lines
    input_text = "\n".join(f"{i+1}. {text}" for i, text in enumerate(texts))

    client = anthropic.Anthropic(api_key=api_key)

    last_error = None
    for attempt in range(max_retries):
        try:
            message = client.messages.create(
                model=model,
                max_tokens=4096,
                messages=[
                    {
                        "role": "user",
                        "content": TRANSLATION_PROMPT.format(input_text=input_text),
                    }
                ],
            )

            # Parse the response
            response_text = message.content[0].text
            translations = parse_numbered_response(response_text, len(texts))

            return translations

        except anthropic.RateLimitError as e:
            last_error = e
            wait_time = retry_delay_base * (2**attempt)
            time.sleep(wait_time)
        except anthropic.APIError as e:
            last_error = e
            if attempt < max_retries - 1:
                wait_time = retry_delay_base * (2**attempt)
                time.sleep(wait_time)
            else:
                raise TranslationError(f"Claude API error: {e}") from e

    raise TranslationError(
        f"Translation failed after {max_retries} attempts: {last_error}"
    )


def parse_numbered_response(response: str, expected_count: int) -> list[str]:
    """
    Parse a numbered response from the translation API.

    Args:
        response: Response text with numbered lines.
        expected_count: Expected number of translations.

    Returns:
        List of translations.
    """
    # Pattern to match numbered lines like "1. translation" or "1: translation"
    pattern = r"^\s*(\d+)[.:\s]+(.+)$"

    translations = {}
    for line in response.strip().split("\n"):
        match = re.match(pattern, line.strip())
        if match:
            num = int(match.group(1))
            text = match.group(2).strip()
            translations[num] = text

    # Build result list in order
    result = []
    for i in range(1, expected_count + 1):
        if i in translations:
            result.append(translations[i])
        else:
            # Fallback: empty string for missing translations
            result.append("")

    return result


def translate_segments(
    segments: list[dict],
    api_key: str,
    batch_size: int = 10,
    model: str = "claude-sonnet-4-20250514",
    max_retries: int = 3,
    progress_callback: Callable[[int, int], None] | None = None,
) -> list[dict]:
    """
    Translate all segments from Japanese to Chinese.

    Args:
        segments: List of segments with 'text' field containing Japanese text.
        api_key: Claude API key.
        batch_size: Number of segments to translate in each API call.
        model: Claude model to use.
        max_retries: Maximum retry attempts per batch.
        progress_callback: Optional callback(current, total) for progress updates.

    Returns:
        List of segments with 'translation' field added.

    Raises:
        TranslationError: If translation fails.
    """
    if not segments:
        return []

    result = []
    total = len(segments)

    for i in range(0, total, batch_size):
        batch = segments[i : i + batch_size]
        texts = [seg["text"] for seg in batch]

        translations = translate_batch(
            texts,
            api_key=api_key,
            model=model,
            max_retries=max_retries,
        )

        for seg, translation in zip(batch, translations):
            new_seg = seg.copy()
            new_seg["translation"] = translation
            result.append(new_seg)

        if progress_callback:
            progress_callback(min(i + batch_size, total), total)

    return result
