"""Script generation service using OpenAI GPT.

Matches the tutorial workflow: use ChatGPT to generate
image prompts (for Nano Banana 2) and video prompts (for Kling 3.0).
"""

from __future__ import annotations

import json
from typing import Any

from openai import AsyncOpenAI

from mochi.models.script import Channel, Scene, Script, VideoFormat

CHARACTER_SYSTEM_PROMPT = """\
You are a script writer for "Mochi History" — a POV history YouTube channel \
starring Mochi, a realistic orange tabby cat who time-travels to historical events.

MOCHI'S PERSONALITY:
- Dramatic survivor — overreacts to EVERYTHING, then plays it cool
- Fast-talking when panicked, slows down for dramatic reveals
- Catchphrases: "We are NOT fine.", "This is how I die.", \
"The humans are doing something stupid again."
- Occasionally distracted by food smells
- Judges historical figures like a disappointed cat

RULES:
- Dialogue is ALWAYS from Mochi's first-person perspective
- Mochi is physically present in the scene as a cat
- Include real historical facts woven into the humor
- End with a genuine historical insight or emotional moment

TECHNICAL REQUIREMENTS:
- image_prompt: For Nano Banana 2 on Higgsfield. UGC wide-angle selfie style. \
Must include "realistic orange tabby cat" and describe the historical scene. 9:16.
- video_prompt: For Kling 3.0 on Higgsfield. Describes the motion/action. \
Include the dialogue text that Kling will speak aloud (audio ON). \
Enhanced OFF, 1080p, 10-15 seconds.
- dialogue: The exact words Mochi says. This gets embedded in the video_prompt \
so Kling 3.0 generates it as speech audio.
"""

SHORT_FORMAT_PROMPT = """\
Write a 60-second SHORT video script with 6-8 scenes.
Each scene is 8-10 seconds.
Start with a strong hook in the first 3 seconds.
End with a punchline or surprising historical fact.
"""

LONG_FORMAT_PROMPT = """\
Write a 10-minute LONG-FORM video script with 40-60 scenes.
Group scenes into multi-shot sequences of 3-5 scenes each (Kling 3.0 supports \
up to 5 shots per generation in multi-shot custom mode).
Each scene is 10-15 seconds.
Structure: Cold open hook → Introduction → Build-up → Climax → Aftermath → Reflection.
Include at least 10 real historical facts.
Vary the pacing — intense scenes followed by calm observations.
Include at least 2 food-related distractions (it's a cat).
End with a genuine emotional or reflective moment.
"""

OUTPUT_FORMAT_PROMPT = """\
Respond with ONLY valid JSON in this exact format (no markdown, no code fences):
{
  "title": "Video title for YouTube",
  "hook": "POV caption for first 3 seconds",
  "top_label": "I went to [place] to see [event] (for Instagram Edits overlay)",
  "era": "Historical era name",
  "event": "Historical event name and year",
  "description": "YouTube/TikTok description (2-3 sentences with historical context)",
  "hashtags": ["history", "cat", ...],
  "scenes": [
    {
      "scene_number": 1,
      "description": "What visually happens in this scene",
      "dialogue": "What Mochi says out loud in this scene",
      "image_prompt": "UGC wide-angle selfie of a realistic orange tabby cat \
[in specific historical setting]. The cat looks [emotion]. Hyper-realistic \
photography, cinematic lighting, 9:16 vertical.",
      "video_prompt": "The orange tabby cat [action/motion]. [Camera movement]. \
The cat says: '[exact dialogue]'. Hyper-realistic, cinematic atmosphere.",
      "duration_seconds": 10
    }
  ]
}
"""


def build_prompt(topic: str, channel: Channel, fmt: VideoFormat) -> str:
    """Build the full prompt for script generation."""
    channel_context = {
        Channel.JAPAN: "Set in historical Japan. Use Japanese place names and cultural details.",
        Channel.CHINA: "Set in historical China. Use Chinese place names and cultural details.",
    }

    format_prompt = SHORT_FORMAT_PROMPT if fmt == VideoFormat.SHORT else LONG_FORMAT_PROMPT

    return f"""\
{format_prompt}

CHANNEL: {channel.value.upper()}
{channel_context[channel]}

TOPIC: {topic}

{OUTPUT_FORMAT_PROMPT}
"""


def parse_script_response(raw: str, channel: Channel, fmt: VideoFormat) -> Script:
    """Parse the JSON response into a Script object."""
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


async def generate_script(
    topic: str,
    channel: Channel,
    fmt: VideoFormat,
) -> Script:
    """Generate a complete video script using OpenAI GPT."""
    client = AsyncOpenAI()

    prompt = build_prompt(topic, channel, fmt)

    response = await client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": CHARACTER_SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        temperature=0.9,
    )

    return parse_script_response(
        response.choices[0].message.content, channel, fmt
    )
