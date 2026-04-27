"""Configuration loader for Mochi CLI."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

import yaml


PROJECT_ROOT = Path(__file__).parent.parent.parent
CONFIG_PATH = PROJECT_ROOT / "config" / "settings.yaml"
OUTPUT_DIR = PROJECT_ROOT / "output"
ASSETS_DIR = PROJECT_ROOT / "assets"
CHARACTER_DIR = ASSETS_DIR / "character"
DATA_DIR = PROJECT_ROOT / "data"


@dataclass(frozen=True)
class GoogleConfig:
    api_key: str = ""


@dataclass(frozen=True)
class ElevenLabsConfig:
    api_key: str = ""
    voice_id: str = ""
    model: str = "eleven_multilingual_v2"


@dataclass(frozen=True)
class HiggsFieldConfig:
    api_key: str = ""


@dataclass(frozen=True)
class Config:
    google: GoogleConfig = field(default_factory=GoogleConfig)
    elevenlabs: ElevenLabsConfig = field(default_factory=ElevenLabsConfig)
    higgsfield: HiggsFieldConfig = field(default_factory=HiggsFieldConfig)


def load_config() -> Config:
    """Load config from settings.yaml, with env var overrides."""
    raw: dict = {}
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH) as f:
            raw = yaml.safe_load(f) or {}

    apis = raw.get("apis", {})

    return Config(
        google=GoogleConfig(
            api_key=os.environ.get(
                "GOOGLE_AI_API_KEY",
                apis.get("google_ai_studio", {}).get("api_key", ""),
            ),
        ),
        elevenlabs=ElevenLabsConfig(
            api_key=os.environ.get(
                "ELEVENLABS_API_KEY",
                apis.get("elevenlabs", {}).get("api_key", ""),
            ),
            voice_id=apis.get("elevenlabs", {}).get("voice_id", ""),
            model=apis.get("elevenlabs", {}).get("model", "eleven_multilingual_v2"),
        ),
        higgsfield=HiggsFieldConfig(
            api_key=os.environ.get(
                "HIGGSFIELD_API_KEY",
                apis.get("higgsfield", {}).get("api_key", ""),
            ),
        ),
    )
