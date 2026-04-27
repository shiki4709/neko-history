"""Script generation — prints prompts for ChatGPT website.

The tutorial uses a custom GPT called "Time Travel Vlog" on ChatGPT.
This service generates the prompt to paste into ChatGPT,
then parses the response you paste back.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.panel import Panel

from mochi.models.script import Channel, Scene, Script, VideoFormat

console = Console()

CHATGPT_GPT_URL = "https://chatgpt.com/gpts"
CHATGPT_GPT_SEARCH = "Time Travel Vlog"


def generate_chatgpt_prompt(
    topic: str,
    channel: Channel,
    fmt: VideoFormat,
) -> str:
    """Generate the prompt to paste into ChatGPT."""
    channel_context = {
        Channel.JAPAN: "historical Japan",
        Channel.CHINA: "historical China",
    }

    if fmt == VideoFormat.SHORT:
        format_detail = "a 60-second short-form video with 6-8 scenes (8-10 seconds each)"
    else:
        format_detail = (
            "a 10-minute long-form video with 40-60 scenes (10-15 seconds each). "
            "Group into multi-shot sequences of 5 scenes each"
        )

    return f"""\
Create {format_detail} about: {topic}

The character is Mochi, a realistic orange tabby cat who time-travels to \
{channel_context[channel]}. Mochi has a dramatic survivor personality — \
overreacts to everything, then plays it cool. Catchphrases include \
"We are NOT fine" and "This is how I die."

For each scene, generate:
1. A text-to-image prompt for Nano Banana 2 (UGC wide-angle selfie style, \
realistic orange tabby cat in the historical setting, 9:16)
2. A text-to-video prompt for Kling 3.0 (with dialogue that Kling will speak \
aloud, describe motion and camera movement)

Output as JSON with this format:
{{
  "title": "...",
  "hook": "POV caption for first 3 seconds",
  "top_label": "I went to [place] to see [event]",
  "era": "...",
  "event": "...",
  "description": "YouTube description",
  "hashtags": [...],
  "scenes": [
    {{
      "scene_number": 1,
      "description": "What happens visually",
      "dialogue": "What Mochi says",
      "image_prompt": "Nano Banana 2 prompt...",
      "video_prompt": "Kling 3.0 prompt with dialogue...",
      "duration_seconds": 10
    }}
  ]
}}
"""


def print_chatgpt_instructions(
    topic: str,
    channel: Channel,
    fmt: VideoFormat,
) -> str:
    """Print instructions for using ChatGPT and return the prompt."""
    prompt = generate_chatgpt_prompt(topic, channel, fmt)

    console.print(Panel(
        f"[bold]Step 1: Generate Script in ChatGPT[/]\n\n"
        f"1. Go to [link={CHATGPT_GPT_URL}]{CHATGPT_GPT_URL}[/link]\n"
        f"2. Search for [bold]'{CHATGPT_GPT_SEARCH}'[/bold] and open it\n"
        f"   (or use any ChatGPT chat)\n"
        f"3. Paste the prompt below\n"
        f"4. Copy the JSON response\n"
        f"5. Run: [bold]mochi save-script <paste>[/bold]\n"
        f"   or save the JSON to a file and run:\n"
        f"   [bold]mochi load-script path/to/response.json -c {channel.value} -f {fmt.value}[/bold]",
        title="ChatGPT Script Generation",
    ))

    console.print(Panel(prompt, title="Copy this prompt into ChatGPT"))

    return prompt


def parse_chatgpt_response(
    raw: str,
    channel: Channel,
    fmt: VideoFormat,
) -> Script:
    """Parse JSON response from ChatGPT into a Script object."""
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
            dialogue=s["dialogue"],
            image_prompt=s["image_prompt"],
            video_prompt=s["video_prompt"],
            duration_seconds=s.get("duration_seconds", 10),
        )
        for s in data["scenes"]
    )

    return Script(
        title=data["title"],
        hook=data["hook"],
        channel=channel,
        format=fmt,
        era=data["era"],
        event=data["event"],
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
