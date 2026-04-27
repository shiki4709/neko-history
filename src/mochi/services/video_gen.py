"""Video clip generation via Higgsfield Kling 3.0.

Since Higgsfield doesn't have a public API yet, this service generates
batch instruction files with all prompts and settings ready to use.
When the API becomes available, this will call it directly.

Key settings from the tutorial:
- Model: Kling 3.0
- Enhanced: OFF
- Audio: ON (Kling generates dialogue as speech)
- Duration: 10-15 seconds
- Resolution: 1080p
- Multi-shot: Custom mode, up to 5 shots per generation
"""

from __future__ import annotations

import json
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from mochi.models.script import Script

console = Console()

KLING_SETTINGS = {
    "model": "Kling 3.0",
    "enhanced": False,
    "audio": True,
    "resolution": "1080p",
    "duration_seconds": 10,
    "max_duration_seconds": 15,
}

MULTI_SHOT_MAX = 5  # Kling 3.0 supports up to 5 shots per generation


def generate_video_instructions(
    script: Script,
    image_dir: Path,
    output_dir: Path,
) -> Path:
    """Generate batch instructions for Higgsfield Kling 3.0.

    For short-form: generates individual clip instructions.
    For long-form: groups scenes into multi-shot sequences of up to 5.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    is_long = script.format.value == "long"
    instructions: dict = {
        "platform": "Higgsfield",
        "model": KLING_SETTINGS["model"],
        "settings": KLING_SETTINGS,
        "mode": "multi-shot (custom)" if is_long else "single",
    }

    if is_long:
        # Group scenes into multi-shot sequences of up to 5
        sequences = []
        for i in range(0, len(script.scenes), MULTI_SHOT_MAX):
            batch = script.scenes[i : i + MULTI_SHOT_MAX]
            sequences.append({
                "sequence_number": len(sequences) + 1,
                "start_image": f"scene_{batch[0].scene_number:03d}.png",
                "shots": [
                    {
                        "shot_number": j + 1,
                        "scene_number": scene.scene_number,
                        "video_prompt": scene.video_prompt,
                    }
                    for j, scene in enumerate(batch)
                ],
                "output_filename": f"clip_{sequences.__len__() + 1:03d}.mp4",
            })
        instructions["sequences"] = sequences
    else:
        # Individual clips for short-form
        clips = []
        for scene in script.scenes:
            clips.append({
                "scene_number": scene.scene_number,
                "start_image": f"scene_{scene.scene_number:03d}.png",
                "video_prompt": scene.video_prompt,
                "output_filename": f"clip_{scene.scene_number:03d}.mp4",
            })
        instructions["clips"] = clips

    instructions_path = output_dir / "video_instructions.json"
    with open(instructions_path, "w") as f:
        json.dump(instructions, f, indent=2)

    # Print human-readable instructions
    console.print(Panel(
        f"[bold]Higgsfield Video Generation — Kling 3.0[/]\n\n"
        f"1. Open [link=https://higgsfield.ai]higgsfield.ai[/link]\n"
        f"2. Go to Video section → select [bold]Kling 3.0[/bold]\n"
        f"3. Settings: Enhanced [bold red]OFF[/], Audio [bold green]ON[/], "
        f"1080p, 10-15 sec\n"
        f"4. Upload scene image as start frame\n"
        f"5. Paste video prompt (includes dialogue for Kling to speak)\n"
        f"{'6. For multi-shot: toggle Custom, paste each shot prompt' if is_long else ''}\n"
        f"7. Save clips to: {output_dir}/clip_XXX.mp4",
        title="Video Generation Instructions",
    ))

    if is_long:
        _print_multishot_table(script)
    else:
        _print_single_table(script)

    return instructions_path


def _print_single_table(script: Script) -> None:
    """Print a table of individual clip prompts."""
    table = Table(title=f"Video Prompts ({script.scene_count} clips)")
    table.add_column("#", style="bold", width=4)
    table.add_column("Start Image", width=20)
    table.add_column("Dialogue", max_width=40)
    table.add_column("Prompt", max_width=50)

    for scene in script.scenes:
        table.add_row(
            str(scene.scene_number),
            f"scene_{scene.scene_number:03d}.png",
            scene.dialogue[:37] + "..." if len(scene.dialogue) > 40 else scene.dialogue,
            scene.video_prompt[:47] + "..." if len(scene.video_prompt) > 50 else scene.video_prompt,
        )

    console.print(table)


def _print_multishot_table(script: Script) -> None:
    """Print multi-shot sequence groupings."""
    table = Table(title=f"Multi-Shot Sequences ({script.scene_count} scenes)")
    table.add_column("Seq", style="bold", width=4)
    table.add_column("Shots", width=8)
    table.add_column("Start Image", width=20)
    table.add_column("Scene Range")

    for i in range(0, len(script.scenes), MULTI_SHOT_MAX):
        batch = script.scenes[i : i + MULTI_SHOT_MAX]
        seq_num = (i // MULTI_SHOT_MAX) + 1
        table.add_row(
            str(seq_num),
            str(len(batch)),
            f"scene_{batch[0].scene_number:03d}.png",
            f"Scenes {batch[0].scene_number}-{batch[-1].scene_number}",
        )

    console.print(table)

    # Also print the individual shot prompts
    console.print("\n[bold]Shot-by-shot prompts:[/]\n")
    for i, scene in enumerate(script.scenes):
        seq_num = (i // MULTI_SHOT_MAX) + 1
        shot_num = (i % MULTI_SHOT_MAX) + 1
        console.print(
            f"  [bold]Seq {seq_num}, Shot {shot_num}[/] (Scene {scene.scene_number}):"
        )
        console.print(f"    {scene.video_prompt}\n")
