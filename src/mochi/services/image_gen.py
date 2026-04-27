"""Image generation via Higgsfield Nano Banana 2.

Since Higgsfield doesn't have a public API yet, this service generates
a batch instruction file with all prompts ready to paste into Higgsfield.
When the API becomes available, this will call it directly.
"""

from __future__ import annotations

import json
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from mochi.config import CHARACTER_DIR
from mochi.models.script import Script

console = Console()

NANO_BANANA_SETTINGS = {
    "model": "Nano Banana 2",
    "aspect_ratio": "9:16",
    "resolution": "2K",
    "images_per_prompt": 4,
}


def get_character_ref_path() -> Path | None:
    """Find Mochi's primary reference image."""
    for name in ["mochi_ref_01_calm.jpg", "mochi_reference_sheet.jpg"]:
        path = CHARACTER_DIR / name
        if path.exists():
            return path
    return None


def generate_image_instructions(
    script: Script,
    output_dir: Path,
) -> Path:
    """Generate a batch instruction file for Higgsfield Nano Banana 2.

    Creates a JSON file with all image prompts and settings,
    ready to use in Higgsfield's image generator.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    ref_path = get_character_ref_path()

    instructions = {
        "platform": "Higgsfield",
        "model": NANO_BANANA_SETTINGS["model"],
        "settings": NANO_BANANA_SETTINGS,
        "character_reference": str(ref_path) if ref_path else "NOT SET — upload Mochi ref image",
        "scenes": [],
    }

    for scene in script.scenes:
        instructions["scenes"].append({
            "scene_number": scene.scene_number,
            "image_prompt": scene.image_prompt,
            "output_filename": f"scene_{scene.scene_number:03d}.png",
        })

    instructions_path = output_dir / "image_instructions.json"
    with open(instructions_path, "w") as f:
        json.dump(instructions, f, indent=2)

    # Print human-readable instructions
    console.print(Panel(
        f"[bold]Higgsfield Image Generation — Nano Banana 2[/]\n\n"
        f"1. Open [link=https://higgsfield.ai]higgsfield.ai[/link]\n"
        f"2. Go to Image section → select [bold]Nano Banana 2[/bold]\n"
        f"3. Upload Mochi reference: {ref_path or 'NOT SET'}\n"
        f"4. Set aspect ratio: 9:16, resolution: 2K\n"
        f"5. Paste each prompt below and generate 4 images\n"
        f"6. Pick the best image for each scene\n"
        f"7. Save to: {output_dir}/scene_XXX.png",
        title="Image Generation Instructions",
    ))

    table = Table(title=f"Image Prompts ({script.scene_count} scenes)")
    table.add_column("#", style="bold", width=4)
    table.add_column("Prompt", max_width=80)

    for scene in script.scenes:
        table.add_row(
            str(scene.scene_number),
            scene.image_prompt[:77] + "..." if len(scene.image_prompt) > 80 else scene.image_prompt,
        )

    console.print(table)

    return instructions_path


def generate_thumbnail_instructions(
    script: Script,
    output_dir: Path,
) -> None:
    """Print thumbnail generation instructions."""
    prompt = (
        f"A dramatic close-up of a realistic orange tabby cat with wide "
        f"golden-amber eyes in a {script.era} {script.channel.value} historical "
        f"setting. Related to: {script.event}. Dramatic lighting, cinematic, "
        f"eye-catching. 16:9 aspect ratio."
    )

    console.print(Panel(
        f"[bold]Thumbnail[/]\n\n"
        f"Generate in Higgsfield with Nano Banana 2:\n"
        f"Aspect ratio: 16:9 (for YouTube thumbnail)\n\n"
        f"Prompt:\n{prompt}",
        title="Thumbnail",
    ))
