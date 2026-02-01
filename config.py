"""Configuration management for the subtitle generator."""

import os
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Config:
    """Configuration settings for the subtitle generator."""

    # API settings
    claude_api_key: str = field(default_factory=lambda: os.getenv("CLAUDE_API_KEY", ""))
    hf_token: str = field(default_factory=lambda: os.getenv("HF_TOKEN", ""))

    # Whisper model settings
    whisper_model: str = "large-v3"
    whisper_device: str = "cuda"
    whisper_compute_type: str = "float16"

    # Processing settings
    enable_diarization: bool = True
    translation_batch_size: int = 10
    max_speakers: int = 4

    # Output settings
    output_dir: str = "./output"
    temp_dir: str = "./temp"

    # Initial prompt for Whisper (helps with idol-related terminology)
    initial_prompt: str = (
        "推しメン、握手会、センター、チェキ、総選挙、ランキング、"
        "メンバー、ファン、ライブ、コンサート、MV、楽曲"
    )

    # Claude model
    claude_model: str = "claude-sonnet-4-20250514"

    # Retry settings
    max_retries: int = 3
    retry_delay_base: float = 1.0

    def __post_init__(self):
        """Create necessary directories after initialization."""
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.temp_dir, exist_ok=True)

    @classmethod
    def from_env(cls) -> "Config":
        """Create a Config instance from environment variables."""
        return cls(
            claude_api_key=os.getenv("CLAUDE_API_KEY", ""),
            hf_token=os.getenv("HF_TOKEN", ""),
            whisper_model=os.getenv("WHISPER_MODEL", "large-v3"),
            whisper_device=os.getenv("WHISPER_DEVICE", "cuda"),
            whisper_compute_type=os.getenv("WHISPER_COMPUTE_TYPE", "float16"),
            enable_diarization=os.getenv("ENABLE_DIARIZATION", "true").lower() == "true",
            translation_batch_size=int(os.getenv("TRANSLATION_BATCH_SIZE", "10")),
            output_dir=os.getenv("OUTPUT_DIR", "./output"),
            temp_dir=os.getenv("TEMP_DIR", "./temp"),
        )

    def validate(self) -> list[str]:
        """Validate the configuration and return a list of errors."""
        errors = []

        if not self.claude_api_key:
            errors.append("CLAUDE_API_KEY is not set")

        if self.enable_diarization and not self.hf_token:
            errors.append("HF_TOKEN is required when diarization is enabled")

        if self.whisper_device == "cuda":
            try:
                import torch
                if not torch.cuda.is_available():
                    errors.append("CUDA is not available but whisper_device is set to 'cuda'")
            except ImportError:
                errors.append("PyTorch is not installed")

        return errors
