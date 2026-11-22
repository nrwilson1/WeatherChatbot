"""Configuration module for Weather Chatbot.

Loads and validates required environment variables and secrets from .env.
"""

from dataclasses import dataclass
import os
from typing import Optional
from dotenv import load_dotenv


@dataclass
class Config:
    """Application configuration holder for validated API keys."""
    xai_api_key: str
    openweather_api_key: str

    @property
    def XAI_API_KEY(self) -> str:
        return self.xai_api_key

    @property
    def OPENWEATHER_API_KEY(self) -> str:
        return self.openweather_api_key

    def __getitem__(self, item: str) -> str:
        key = item.lower()
        if key in ("xai_api_key", "xai"):
            return self.xai_api_key
        elif key in ("openweather_api_key", "openweather", "ow_api_key"):
            return self.openweather_api_key
        raise KeyError(f"Unknown configuration key: {item}")

    def get(self, item: str, default: Optional[str] = None) -> Optional[str]:
        try:
            return self[item]
        except KeyError:
            return default


def load_config(env_path: Optional[str] = None) -> Config:
    """Loads environment variables and validates that required API keys are present.

    Args:
        env_path: Optional path to .env file.

    Returns:
        Config: Populated configuration dataclass.

    Raises:
        ValueError: If any required environment variable is missing or empty.
    """
    if env_path:
        load_dotenv(dotenv_path=env_path)
    else:
        load_dotenv()

    xai_key = os.getenv("XAI_API_KEY", "").strip()
    ow_key = os.getenv("OPENWEATHER_API_KEY", "").strip()

    missing = []
    if not xai_key:
        missing.append("XAI_API_KEY")
    if not ow_key:
        missing.append("OPENWEATHER_API_KEY")

    if missing:
        missing_str = ", ".join(missing)
        raise ValueError(
            f"Missing required environment variable(s): {missing_str}. "
            "Please ensure they are defined in your .env file or environment."
        )

    return Config(xai_api_key=xai_key, openweather_api_key=ow_key)
