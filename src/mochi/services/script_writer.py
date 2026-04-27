"""Script generation — uses the 'Time Travel Vlog' custom GPT on ChatGPT.

The workflow from the tutorial:
1. Open the "Time Travel Vlog" GPT on ChatGPT
2. Click "Put yourself in a vlog"
3. Upload Mochi's reference photo
4. Tell it the location and time period
5. It generates 5 text-to-image prompts + 5 text-to-video prompts
6. Paste them into Higgsfield
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.panel import Panel

from mochi.config import CHARACTER_DIR
from mochi.models.script import Channel, Scene, Script, VideoFormat

console = Console()

CHATGPT_GPT_URL = "https://chatgpt.com/gpts"
CHATGPT_GPT_SEARCH = "Time Travel Vlog"


def get_character_ref_path() -> Path | None:
    """Find Mochi's primary reference image."""
    for name in ["mochi_ref_01_calm.jpg", "mochi_reference_sheet.jpg"]:
        path = CHARACTER_DIR / name
        if path.exists():
            return path
    return None


def print_chatgpt_instructions(
    topic: str,
    channel: Channel,
    fmt: VideoFormat,
) -> None:
    """Print step-by-step instructions matching the tutorial exactly."""
    channel_context = {
        Channel.JAPAN: "historical Japan",
        Channel.CHINA: "historical China",
    }

    ref_path = get_character_ref_path()

    console.print(Panel(
        f"[bold]Step 1: Open the Time Travel Vlog GPT[/]\n\n"
        f"1. Go to [link={CHATGPT_GPT_URL}]{CHATGPT_GPT_URL}[/link]\n"
        f"2. Search for [bold]'{CHATGPT_GPT_SEARCH}'[/bold]\n"
        f"3. Open it and start a chat\n"
        f"4. Click [bold]'Put yourself in a vlog'[/bold]",
        title="Step 1",
    ))

    console.print(Panel(
        f"[bold]Step 2: Upload reference photo + location[/]\n\n"
        f"The GPT will ask you for:\n\n"
        f"  1. [bold]Reference photo:[/] Upload Mochi's image\n"
        f"     → {ref_path or 'Generate one first with Google AI Studio'}\n\n"
        f"  2. [bold]Location & time period:[/] Reply with:\n"
        f'     [bold]"{topic} in {channel_context[channel]}"[/]',
        title="Step 2",
    ))

    console.print(Panel(
        f"[bold]Step 3: Get your prompts[/]\n\n"
        f"The GPT will generate:\n"
        f"  • 5 text-to-image prompts (for Nano Banana 2)\n"
        f"  • 5 text-to-video prompts (for Kling 3.0)\n\n"
        f"[bold]Next:[/] Run [bold]mochi images[/] for Higgsfield instructions,\n"
        f"or go straight to Higgsfield and paste the prompts.",
        title="Step 3",
    ))

    console.print(Panel(
        f"[bold]Higgsfield Settings Reminder[/]\n\n"
        f"[bold]Images (Nano Banana 2):[/]\n"
        f"  • Upload Mochi reference photo\n"
        f"  • Aspect ratio: 9:16\n"
        f"  • Resolution: 2K\n"
        f"  • Generate 4 images per prompt, pick the best\n\n"
        f"[bold]Videos (Kling 3.0):[/]\n"
        f"  • Upload best image as start frame\n"
        f"  • Enhanced: [bold red]OFF[/]\n"
        f"  • Audio: [bold green]ON[/]\n"
        f"  • Duration: 10-15 seconds\n"
        f"  • Resolution: 1080p\n"
        f"  • Multi-shot: Custom (up to 5 shots)",
        title="Higgsfield Quick Reference",
    ))


def parse_chatgpt_response(
    raw: str,
    channel: Channel,
    fmt: VideoFormat,
) -> Script:
    """Parse JSON response from ChatGPT into a Script object.

    Use this if you ask ChatGPT to output JSON format.
    """
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("\n", 1)[1]
    if cleaned.endswith("```"):
        cleaned = cleaned.rsplit("```", 1)[0]
    cleaned = cleaned.strip()

    data: dict[str, Any] = json.loads(cleaned)

    scenes = tuple(
        Scene(
            scene_number=s["scene_number"],
            description=s["description"],
            dialogue=s.get("dialogue", ""),
            image_prompt=s.get("image_prompt", ""),
            video_prompt=s.get("video_prompt", ""),
            duration_seconds=s.get("duration_seconds", 10),
        )
        for s in data["scenes"]
    )

    return Script(
        title=data["title"],
        hook=data.get("hook", ""),
        channel=channel,
        format=fmt,
        era=data.get("era", ""),
        event=data.get("event", ""),
        scenes=scenes,
        hashtags=tuple(data.get("hashtags", [])),
        description=data.get("description", ""),
        top_label=data.get("top_label", ""),
    )


def save_script_to_disk(script: Script, output_dir: Path) -> Path:
    """Save a parsed script to disk as JSON."""
    output_dir.mkdir(parents=True, exist_ok=True)
    script_path = output_dir / "script.json"

    data = {
        "title": script.title,
        "hook": script.hook,
        "channel": script.channel.value,
        "format": script.format.value,
        "era": script.era,
        "event": script.event,
        "description": script.description,
        "top_label": script.top_label,
        "hashtags": list(script.hashtags),
        "scenes": [
            {
                "scene_number": s.scene_number,
                "description": s.description,
                "dialogue": s.dialogue,
                "image_prompt": s.image_prompt,
                "video_prompt": s.video_prompt,
                "duration_seconds": s.duration_seconds,
            }
            for s in script.scenes
        ],
    }

    with open(script_path, "w") as f:
        json.dump(data, f, indent=2)

    return script_path
