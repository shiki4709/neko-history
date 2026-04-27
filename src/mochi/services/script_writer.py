"""Script generation service using Google Gemini."""

from __future__ import annotations

import json
from typing import Any

from google import genai

from mochi.config import Config
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
- Narration is ALWAYS from Mochi's first-person perspective
- Mochi is physically present in the scene as a cat
- Include real historical facts woven into the humor
- End with a genuine historical insight or emotional moment
- Each scene description must be vivid enough to generate an AI video from it
"""

SHORT_FORMAT_PROMPT = """\
Write a 60-second SHORT video script with 6-8 scenes.
Each scene is 5-10 seconds.
Start with a strong hook in the first 3 seconds.
End with a punchline or surprising historical fact.
"""

LONG_FORMAT_PROMPT = """\
Write a 10-minute LONG-FORM video script with 40-60 scenes.
Each scene is 8-15 seconds.
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
  "era": "Historical era name",
  "event": "Historical event name and year",
  "description": "YouTube/TikTok description (2-3 sentences with historical context)",
  "hashtags": ["history", "cat", ...],
  "scenes": [
    {
      "scene_number": 1,
      "description": "What visually happens in this scene",
      "narration": "Mochi's voiceover text for this scene",
      "video_prompt": "Detailed prompt for AI video generation: \
A realistic orange tabby cat [action] in [detailed historical setting]. \
Handheld camera, hyper-realistic, cinematic atmosphere. 9:16 vertical.",
      "duration_seconds": 8
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
    """Parse the JSON response from Gemini into a Script object."""
    # Strip markdown code fences if present
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
            narration=s["narration"],
            video_prompt=s["video_prompt"],
            duration_seconds=s.get("duration_seconds", 8),
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
    )


async def generate_script(
    topic: str,
    channel: Channel,
    fmt: VideoFormat,
    config: Config,
) -> Script:
    """Generate a complete video script using Google Gemini."""
    client = genai.Client(api_key=config.google.api_key)

    prompt = build_prompt(topic, channel, fmt)

    response = await client.aio.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt,
        config=genai.types.GenerateContentConfig(
            system_instruction=CHARACTER_SYSTEM_PROMPT,
            temperature=0.9,
        ),
    )

    return parse_script_response(response.text, channel, fmt)
