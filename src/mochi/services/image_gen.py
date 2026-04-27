"""Image generation service using Google Imagen via Gemini."""

from __future__ import annotations

import base64
from pathlib import Path

from google import genai
from google.genai import types

from mochi.config import Config
from mochi.models.script import Script


CHARACTER_REF_DIR = Path(__file__).parent.parent.parent.parent / "assets" / "character"


def _load_character_reference() -> bytes | None:
    """Load Mochi's primary reference image if available."""
    ref_path = CHARACTER_REF_DIR / "mochi_ref_01_calm.jpg"
    if ref_path.exists():
        return ref_path.read_bytes()
    return None


async def generate_scene_image(
    video_prompt: str,
    output_path: Path,
    config: Config,
) -> Path:
    """Generate a single scene image using Imagen 3 via Gemini.

    Uses Mochi's reference image for character consistency.
    """
    client = genai.Client(api_key=config.google.api_key)

    prompt = (
        f"Generate an image: {video_prompt} "
        "The orange tabby cat should look exactly like the reference image. "
        "Hyper-realistic photography style."
    )

    contents: list[types.Part | str] = []

    ref_bytes = _load_character_reference()
    if ref_bytes is not None:
        contents.append(
            types.Part.from_bytes(data=ref_bytes, mime_type="image/jpeg")
        )
        contents.append(
            "This is the reference image of Mochi the orange tabby cat. "
            "Generate a new image keeping this exact cat appearance. "
        )

    contents.append(prompt)

    response = await client.aio.models.generate_content(
        model="gemini-2.0-flash-preview-image-generation",
        contents=contents,
        config=types.GenerateContentConfig(
            response_modalities=["image", "text"],
        ),
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)

    for part in response.candidates[0].content.parts:
        if part.inline_data is not None:
            with open(output_path, "wb") as f:
                f.write(part.inline_data.data)
            return output_path

    raise RuntimeError("No image generated in response")


async def generate_all_scene_images(
    script: Script,
    output_dir: Path,
    config: Config,
) -> list[Path]:
    """Generate images for all scenes in a script.

    Returns list of image paths.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []

    for scene in script.scenes:
        img_path = output_dir / f"scene_{scene.scene_number:03d}.png"
        await generate_scene_image(scene.video_prompt, img_path, config)
        paths.append(img_path)

    return paths


async def generate_thumbnail(
    script: Script,
    output_path: Path,
    config: Config,
) -> Path:
    """Generate a YouTube thumbnail for the video."""
    prompt = (
        f"A dramatic YouTube thumbnail: a realistic orange tabby cat with wide "
        f"golden eyes in a {script.era} {script.channel.value} historical setting. "
        f"Related to: {script.event}. "
        f"Dramatic lighting, cinematic, eye-catching, 16:9 aspect ratio. "
        f"No text overlay."
    )

    return await generate_scene_image(prompt, output_path, config)
