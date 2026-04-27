"""Video production tracker — tracks progress of all videos across both channels."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path

from rich.console import Console
from rich.table import Table

from mochi.config import OUTPUT_DIR

console = Console()

TRACKER_PATH = OUTPUT_DIR / "tracker.json"


class Stage(str, Enum):
    SCRIPT = "script"
    IMAGES = "images"
    CLIPS = "clips"
    ASSEMBLED = "assembled"
    CAPTIONED = "captioned"
    PUBLISHED = "published"


STAGE_ORDER = list(Stage)

STAGE_DISPLAY = {
    Stage.SCRIPT: "Script",
    Stage.IMAGES: "Images",
    Stage.CLIPS: "Clips",
    Stage.ASSEMBLED: "Assembled",
    Stage.CAPTIONED: "Captioned",
    Stage.PUBLISHED: "Published",
}


@dataclass
class VideoEntry:
    """A single video being tracked."""

    video_id: str  # e.g., "japan/shorts/great_fire_of_meireki"
    title: str
    channel: str
    format: str
    stage: str
    created_at: str
    updated_at: str
    published_urls: dict[str, str]  # platform -> URL
    notes: str = ""

    @property
    def stage_index(self) -> int:
        try:
            return STAGE_ORDER.index(Stage(self.stage))
        except ValueError:
            return -1

    @property
    def progress_bar(self) -> str:
        total = len(STAGE_ORDER)
        done = self.stage_index + 1
        filled = "█" * done
        empty = "░" * (total - done)
        return f"{filled}{empty} {done}/{total}"


def _load_tracker() -> dict[str, list[dict]]:
    """Load tracker data from disk."""
    if TRACKER_PATH.exists():
        with open(TRACKER_PATH) as f:
            return json.load(f)
    return {"videos": []}


def _save_tracker(data: dict[str, list[dict]]) -> None:
    """Save tracker data to disk."""
    TRACKER_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(TRACKER_PATH, "w") as f:
        json.dump(data, f, indent=2)


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M")


def add_video(
    video_id: str,
    title: str,
    channel: str,
    fmt: str,
    stage: str = "script",
    notes: str = "",
) -> VideoEntry:
    """Add a new video to the tracker."""
    data = _load_tracker()
    now = _now()

    entry = {
        "video_id": video_id,
        "title": title,
        "channel": channel,
        "format": fmt,
        "stage": stage,
        "created_at": now,
        "updated_at": now,
        "published_urls": {},
        "notes": notes,
    }

    # Check for duplicates
    existing_ids = {v["video_id"] for v in data["videos"]}
    if video_id in existing_ids:
        # Update existing
        for i, v in enumerate(data["videos"]):
            if v["video_id"] == video_id:
                data["videos"][i] = entry
                break
    else:
        data["videos"].append(entry)

    _save_tracker(data)
    return VideoEntry(**entry)


def update_stage(video_id: str, stage: str, notes: str = "") -> VideoEntry | None:
    """Update the stage of a tracked video."""
    data = _load_tracker()

    for i, v in enumerate(data["videos"]):
        if v["video_id"] == video_id:
            data["videos"][i]["stage"] = stage
            data["videos"][i]["updated_at"] = _now()
            if notes:
                data["videos"][i]["notes"] = notes
            _save_tracker(data)
            return VideoEntry(**data["videos"][i])

    return None


def add_published_url(video_id: str, platform: str, url: str) -> None:
    """Record a published URL for a video."""
    data = _load_tracker()

    for i, v in enumerate(data["videos"]):
        if v["video_id"] == video_id:
            data["videos"][i]["published_urls"][platform] = url
            data["videos"][i]["updated_at"] = _now()
            if data["videos"][i]["stage"] != Stage.PUBLISHED.value:
                data["videos"][i]["stage"] = Stage.PUBLISHED.value
            _save_tracker(data)
            return

    console.print(f"[red]Video not found: {video_id}[/]")


def list_videos(
    channel: str | None = None,
    stage: str | None = None,
) -> list[VideoEntry]:
    """List tracked videos, optionally filtered."""
    data = _load_tracker()
    entries = [VideoEntry(**v) for v in data["videos"]]

    if channel:
        entries = [e for e in entries if e.channel == channel]
    if stage:
        entries = [e for e in entries if e.stage == stage]

    return entries


def print_tracker_table(
    channel: str | None = None,
    stage: str | None = None,
) -> None:
    """Print a rich table of all tracked videos."""
    entries = list_videos(channel, stage)

    if not entries:
        console.print("[yellow]No videos tracked yet.[/]")
        console.print("Start with: [bold]mochi script <topic> -c japan[/]")
        return

    table = Table(title="Mochi Video Tracker")
    table.add_column("#", style="bold", width=3)
    table.add_column("Title", max_width=35)
    table.add_column("Channel", width=8)
    table.add_column("Format", width=8)
    table.add_column("Stage", width=12)
    table.add_column("Progress", width=16)
    table.add_column("Updated", width=12)

    stage_colors = {
        "script": "blue",
        "images": "cyan",
        "clips": "yellow",
        "assembled": "green",
        "captioned": "green",
        "published": "bold green",
    }

    for i, entry in enumerate(entries, 1):
        color = stage_colors.get(entry.stage, "white")
        title_display = entry.title[:32] + "..." if len(entry.title) > 35 else entry.title

        table.add_row(
            str(i),
            title_display,
            entry.channel,
            entry.format,
            f"[{color}]{STAGE_DISPLAY.get(Stage(entry.stage), entry.stage)}[/]",
            entry.progress_bar,
            entry.updated_at,
        )

    console.print(table)

    # Summary
    total = len(entries)
    published = sum(1 for e in entries if e.stage == Stage.PUBLISHED.value)
    in_progress = total - published
    console.print(
        f"\nTotal: {total} | "
        f"Published: [green]{published}[/] | "
        f"In Progress: [yellow]{in_progress}[/]"
    )


def print_video_detail(video_id: str) -> None:
    """Print detailed info for a single video."""
    data = _load_tracker()

    for v in data["videos"]:
        if v["video_id"] == video_id:
            entry = VideoEntry(**v)
            console.print(f"\n[bold]{entry.title}[/]")
            console.print(f"  ID: {entry.video_id}")
            console.print(f"  Channel: {entry.channel}")
            console.print(f"  Format: {entry.format}")
            console.print(f"  Stage: {entry.stage}")
            console.print(f"  Progress: {entry.progress_bar}")
            console.print(f"  Created: {entry.created_at}")
            console.print(f"  Updated: {entry.updated_at}")
            if entry.notes:
                console.print(f"  Notes: {entry.notes}")
            if entry.published_urls:
                console.print("  Published:")
                for platform, url in entry.published_urls.items():
                    console.print(f"    {platform}: {url}")
            return

    console.print(f"[red]Video not found: {video_id}[/]")


def auto_detect_stage(script_dir: Path) -> str:
    """Auto-detect the current stage based on what files exist."""
    if list(script_dir.glob("final.mp4")):
        return Stage.ASSEMBLED.value
    if list((script_dir / "clips").glob("clip_*.mp4")):
        return Stage.CLIPS.value
    if list((script_dir / "images").glob("scene_*.png")):
        return Stage.IMAGES.value
    if (script_dir / "script.json").exists():
        return Stage.SCRIPT.value
    return Stage.SCRIPT.value
