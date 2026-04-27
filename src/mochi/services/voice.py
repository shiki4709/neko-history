"""Voice generation service using ElevenLabs."""

from __future__ import annotations

from pathlib import Path

from elevenlabs import AsyncElevenLabs

from mochi.config import Config
from mochi.models.script import Script


async def generate_voice(
    script: Script,
    output_path: Path,
    config: Config,
) -> Path:
    """Generate Mochi's voiceover from the full narration script.

    Returns the path to the generated .mp3 file.
    """
    client = AsyncElevenLabs(api_key=config.elevenlabs.api_key)

    narration = script.full_narration

    audio_generator = await client.text_to_speech.convert(
        text=narration,
        voice_id=config.elevenlabs.voice_id,
        model_id=config.elevenlabs.model,
        output_format="mp3_44100_128",
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "wb") as f:
        async for chunk in audio_generator:
            f.write(chunk)

    return output_path


async def generate_scene_voices(
    script: Script,
    output_dir: Path,
    config: Config,
) -> list[Path]:
    """Generate individual voice clips per scene for easier editing.

    Returns a list of paths to the generated .mp3 files.
    """
    client = AsyncElevenLabs(api_key=config.elevenlabs.api_key)
    output_dir.mkdir(parents=True, exist_ok=True)

    paths: list[Path] = []

    for scene in script.scenes:
        scene_path = output_dir / f"scene_{scene.scene_number:03d}.mp3"

        audio_generator = await client.text_to_speech.convert(
            text=scene.narration,
            voice_id=config.elevenlabs.voice_id,
            model_id=config.elevenlabs.model,
            output_format="mp3_44100_128",
        )

        with open(scene_path, "wb") as f:
            async for chunk in audio_generator:
                f.write(chunk)

        paths.append(scene_path)

    return paths
