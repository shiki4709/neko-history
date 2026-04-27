"""Video clip generation — Higgsfield for production, Veo for free/testing."""

from __future__ import annotations

import asyncio
from pathlib import Path

from google import genai
from google.genai import types

from mochi.config import Config
from mochi.models.script import Scene


async def generate_clip_veo(
    scene: Scene,
    scene_image_path: Path,
    output_path: Path,
    config: Config,
) -> Path:
    """Generate a video clip from a scene image using Google Veo 3.1.

    This is the free tier option (2-5 clips/day).
    Uses image-to-video: uploads the scene image as the first frame.
    """
    client = genai.Client(api_key=config.google.api_key)

    image_bytes = scene_image_path.read_bytes()

    response = await client.aio.models.generate_videos(
        model="veo-3.1",
        prompt=scene.video_prompt,
        image=types.Image.from_bytes(data=image_bytes, mime_type="image/png"),
        config=types.GenerateVideosConfig(
            aspect_ratio="9:16",
            number_of_videos=1,
        ),
    )

    # Poll until video is ready
    while not response.done:
        await asyncio.sleep(5)
        response = await response.refresh()

    output_path.parent.mkdir(parents=True, exist_ok=True)

    video = response.generated_videos[0]
    with open(output_path, "wb") as f:
        f.write(video.video.video_bytes)

    return output_path


async def generate_all_clips(
    scenes: list[Scene],
    image_dir: Path,
    output_dir: Path,
    config: Config,
    engine: str = "veo",
) -> list[Path]:
    """Generate video clips for all scenes.

    Args:
        scenes: List of scenes to generate clips for.
        image_dir: Directory containing scene images (scene_001.png, etc.).
        output_dir: Directory to write video clips to.
        config: App configuration.
        engine: "veo" (free) or "higgsfield" (paid, better quality).

    Returns:
        List of paths to generated video clips.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []

    for scene in scenes:
        img_path = image_dir / f"scene_{scene.scene_number:03d}.png"
        clip_path = output_dir / f"clip_{scene.scene_number:03d}.mp4"

        if not img_path.exists():
            raise FileNotFoundError(
                f"Scene image not found: {img_path}. Run `mochi images` first."
            )

        if engine == "veo":
            await generate_clip_veo(scene, img_path, clip_path, config)
        elif engine == "higgsfield":
            # Higgsfield doesn't have a public Python API yet.
            # For now, print instructions for manual generation.
            print(
                f"[Higgsfield] Upload {img_path} to Higgsfield Cinema Studio.\n"
                f"  Prompt: {scene.video_prompt}\n"
                f"  Save output to: {clip_path}\n"
            )
        else:
            raise ValueError(f"Unknown engine: {engine}")

        paths.append(clip_path)

    return paths
