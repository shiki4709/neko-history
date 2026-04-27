"""Data models for video scripts and scenes."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class Channel(str, Enum):
    JAPAN = "japan"
    CHINA = "china"


class VideoFormat(str, Enum):
    SHORT = "short"  # 60-90 sec
    LONG = "long"  # 8-15 min


@dataclass(frozen=True)
class Scene:
    """A single scene in a video — maps to one AI-generated clip."""

    scene_number: int
    description: str  # What happens in this scene (for narration context)
    narration: str  # Mochi's voiceover for this scene
    video_prompt: str  # Prompt for Higgsfield/video gen
    duration_seconds: int = 8  # Target clip length


@dataclass(frozen=True)
class Script:
    """A complete video script with all scenes and metadata."""

    title: str
    hook: str  # First 3 seconds — the caption/text overlay
    channel: Channel
    format: VideoFormat
    era: str  # e.g., "Edo", "Tang Dynasty"
    event: str  # e.g., "Great Fire of Meireki (1657)"
    scenes: tuple[Scene, ...] = field(default_factory=tuple)
    hashtags: tuple[str, ...] = field(default_factory=tuple)
    description: str = ""  # YouTube/TikTok description

    @property
    def total_duration(self) -> int:
        return sum(s.duration_seconds for s in self.scenes)

    @property
    def full_narration(self) -> str:
        return "\n\n".join(s.narration for s in self.scenes)

    @property
    def scene_count(self) -> int:
        return len(self.scenes)


@dataclass(frozen=True)
class VideoAssets:
    """Paths to all generated assets for a video."""

    script_path: Path
    voice_path: Path | None = None
    clip_paths: tuple[Path, ...] = field(default_factory=tuple)
    final_video_path: Path | None = None
    thumbnail_path: Path | None = None
