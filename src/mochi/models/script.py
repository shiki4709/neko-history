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
    """A single scene in a video — maps to one Higgsfield generation."""

    scene_number: int
    description: str  # What happens visually
    dialogue: str  # What Mochi says (Kling generates this as audio)
    image_prompt: str  # Prompt for Nano Banana 2 (text-to-image)
    video_prompt: str  # Prompt for Kling 3.0 (image-to-video, includes dialogue)
    duration_seconds: int = 10


@dataclass(frozen=True)
class MultiShot:
    """A multi-shot sequence — up to 5 shots in one Kling 3.0 generation."""

    shots: tuple[Scene, ...] = field(default_factory=tuple)

    @property
    def total_duration(self) -> int:
        return sum(s.duration_seconds for s in self.shots)


@dataclass(frozen=True)
class Script:
    """A complete video script with all scenes and metadata."""

    title: str
    hook: str  # Caption overlay for first 3 seconds
    channel: Channel
    format: VideoFormat
    era: str
    event: str
    scenes: tuple[Scene, ...] = field(default_factory=tuple)
    hashtags: tuple[str, ...] = field(default_factory=tuple)
    description: str = ""
    top_label: str = ""  # "I went to Edo to see the Great Fire" (Instagram Edits style)

    @property
    def total_duration(self) -> int:
        return sum(s.duration_seconds for s in self.scenes)

    @property
    def full_dialogue(self) -> str:
        return "\n\n".join(s.dialogue for s in self.scenes)

    @property
    def scene_count(self) -> int:
        return len(self.scenes)


@dataclass(frozen=True)
class VideoAssets:
    """Paths to all generated assets for a video."""

    script_path: Path
    image_paths: tuple[Path, ...] = field(default_factory=tuple)
    clip_paths: tuple[Path, ...] = field(default_factory=tuple)
    final_video_path: Path | None = None
    thumbnail_path: Path | None = None
