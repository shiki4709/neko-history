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


def generate_brainstorm_prompt(
    topic: str,
    channel: Channel,
    fmt: VideoFormat,
) -> str:
    """Generate the brainstorming prompt — Step 1 of the ChatGPT flow."""
    channel_context = {
        Channel.JAPAN: "historical Japan",
        Channel.CHINA: "historical China",
    }

    if fmt == VideoFormat.SHORT:
        format_detail = "a 60-second short-form video (6-8 scenes)"
    else:
        format_detail = "a 10-minute long-form video (40-60 scenes)"

    return f"""\
I want to create {format_detail} about: {topic}

The character is Mochi, a realistic orange tabby cat who time-travels to \
{channel_context[channel]}. Mochi has a dramatic survivor personality — \
overreacts to everything, then plays it cool. Catchphrases include \
"We are NOT fine" and "This is how I die." He occasionally gets distracted \
by food and judges historical figures like a disappointed cat.

Before we generate prompts, let's brainstorm:
1. What are the most visually dramatic moments of this event?
2. What would Mochi's emotional journey be through this event?
3. What specific historical details would make this feel authentic?
4. What's the hook — the first 3 seconds that stops the scroll?
5. What's the punchline or emotional payoff at the end?
6. What locations/scenes would look the most cinematic?

Let's discuss the concept first before generating any prompts.\
"""


def generate_prompts_prompt(
    channel: Channel,
    fmt: VideoFormat,
) -> str:
    """Generate the prompt-generation prompt — Step 2, after brainstorming."""
    if fmt == VideoFormat.SHORT:
        format_detail = "6-8 scenes (8-10 seconds each)"
    else:
        format_detail = (
            "40-60 scenes (10-15 seconds each), "
            "grouped into multi-shot sequences of 5"
        )

    return f"""\
Great, now generate the full production document with {format_detail}.

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
    """Print the two-step ChatGPT flow: brainstorm first, then generate prompts."""
    brainstorm = generate_brainstorm_prompt(topic, channel, fmt)
    prompts = generate_prompts_prompt(channel, fmt)

    console.print(Panel(
        f"[bold]ChatGPT Flow (2 steps)[/]\n\n"
        f"1. Go to [link={CHATGPT_GPT_URL}]{CHATGPT_GPT_URL}[/link]\n"
        f"2. Search for [bold]'{CHATGPT_GPT_SEARCH}'[/bold] and open it\n"
        f"   (or use any ChatGPT chat)\n\n"
        f"[bold]Step 1:[/] Paste the brainstorm prompt below.\n"
        f"  Discuss the concept — refine scenes, locations, Mochi's reactions.\n"
        f"  Go back and forth until you're happy with the plan.\n\n"
        f"[bold]Step 2:[/] When ready, paste the second prompt to generate\n"
        f"  the full production JSON with all image + video prompts.\n\n"
        f"[bold]Step 3:[/] Save the JSON and run:\n"
        f"  [bold]mochi load-script response.json -c {channel.value} -f {fmt.value}[/bold]",
        title="ChatGPT Script Generation",
    ))

    console.print(Panel(brainstorm, title="Step 1: Paste this FIRST — Brainstorm"))
    console.print(Panel(prompts, title="Step 2: Paste this AFTER brainstorming — Generate Prompts"))

    return brainstorm


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
