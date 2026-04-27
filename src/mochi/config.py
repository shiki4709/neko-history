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
class HiggsFieldConfig:
    api_key: str = ""


@dataclass(frozen=True)
class Config:
    higgsfield: HiggsFieldConfig = field(default_factory=HiggsFieldConfig)


def load_config() -> Config:
    """Load config from settings.yaml, with env var overrides."""
    raw: dict = {}
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH) as f:
            raw = yaml.safe_load(f) or {}

    apis = raw.get("apis", {})

    return Config(
        higgsfield=HiggsFieldConfig(
            api_key=os.environ.get(
                "HIGGSFIELD_API_KEY",
                apis.get("higgsfield", {}).get("api_key", ""),
            ),
        ),
    )
