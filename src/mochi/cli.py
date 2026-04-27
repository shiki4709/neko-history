"""Mochi CLI — the main entry point.

Workflow (matches the YouTube tutorial):
1. Script: GPT-4o generates image prompts + video prompts with dialogue
2. Images: Paste prompts into Higgsfield → Nano Banana 2 (9:16, 2K)
3. Clips:  Upload images to Higgsfield → Kling 3.0 (enhanced OFF, audio ON, 1080p)
4. Stitch: ffmpeg concatenates clips (audio already embedded by Kling)
5. Polish: Add top label overlay via ffmpeg (like Instagram Edits app)
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from mochi import __version__
from mochi.config import load_config, OUTPUT_DIR, CHARACTER_DIR
from mochi.models.script import Channel, Scene, Script, VideoFormat

console = Console()


def _output_dir_for(channel: Channel, fmt: VideoFormat, title_slug: str) -> Path:
    """Create and return the output directory for a video."""
    fmt_dir = "shorts" if fmt == VideoFormat.SHORT else "longform"
    path = OUTPUT_DIR / channel.value / fmt_dir / title_slug
    path.mkdir(parents=True, exist_ok=True)
    return path


def _slugify(text: str) -> str:
    """Convert a title to a filesystem-safe slug."""
    return (
        text.lower()
        .replace(" ", "_")
        .replace(":", "")
        .replace("'", "")
        .replace('"', "")
        .replace(".", "")
    )[:60]


def _load_script(script_path: str) -> tuple[Script, Path]:
    """Load a script from JSON file."""
    path = Path(script_path)
    with open(path) as f:
        data = json.load(f)

    script_obj = Script(
        title=data["title"],
        hook=data["hook"],
        channel=Channel(data["channel"]),
        format=VideoFormat(data["format"]),
        era=data["era"],
        event=data["event"],
        scenes=tuple(
            Scene(
                scene_number=s["scene_number"],
                description=s["description"],
                dialogue=s["dialogue"],
                image_prompt=s["image_prompt"],
                video_prompt=s["video_prompt"],
                duration_seconds=s.get("duration_seconds", 10),
            )
            for s in data["scenes"]
        ),
        hashtags=tuple(data.get("hashtags", [])),
        description=data.get("description", ""),
        top_label=data.get("top_label", ""),
    )
    return script_obj, path.parent


def _save_script(script: Script, out_dir: Path) -> Path:
    """Save a script to JSON."""
    script_path = out_dir / "script.json"
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


@click.group()
@click.version_option(version=__version__)
def cli() -> None:
    """Mochi CLI — AI-powered POV history video production agent.

    A cat named Mochi time-travels through history.

    \b
    Workflow:
      1. mochi script  → Generate script with image + video prompts
      2. mochi images   → Get prompts to paste into Higgsfield (Nano Banana 2)
      3. mochi clips    → Get prompts to paste into Higgsfield (Kling 3.0)
      4. mochi assemble → Stitch clips + add top label (ffmpeg)

    Or run everything:
      mochi produce "topic" -c japan -f long
    """
    pass


@cli.command()
@click.argument("topic")
@click.option(
    "--channel", "-c",
    type=click.Choice(["japan", "china"]),
    required=True,
    help="Which channel: japan or china",
)
@click.option(
    "--format", "-f", "fmt",
    type=click.Choice(["short", "long"]),
    default="short",
    help="Video format: short (60s) or long (10min)",
)
def script(topic: str, channel: str, fmt: str) -> None:
    """Generate a video script with image + video prompts.

    Example: mochi script "The Great Fire of Meireki 1657" -c japan -f short
    """
    from mochi.services.script_writer import generate_script

    ch = Channel(channel)
    vf = VideoFormat(fmt)

    with Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]{task.description}"),
        console=console,
    ) as progress:
        progress.add_task("Writing script via GPT-4o...", total=None)
        result = asyncio.run(generate_script(topic, ch, vf))

    slug = _slugify(result.title)
    out_dir = _output_dir_for(ch, vf, slug)
    script_path = _save_script(result, out_dir)

    console.print(Panel(
        f"[bold green]Script generated![/]\n\n"
        f"Title: {result.title}\n"
        f"Hook: {result.hook}\n"
        f"Top Label: {result.top_label}\n"
        f"Scenes: {result.scene_count}\n"
        f"Duration: ~{result.total_duration}s\n"
        f"Saved: {script_path}",
        title="Mochi Script",
    ))

    table = Table(title="Scenes")
    table.add_column("#", style="bold", width=4)
    table.add_column("Dialogue", max_width=50)
    table.add_column("Duration", width=8)

    for s in result.scenes:
        dialogue_preview = s.dialogue[:47] + "..." if len(s.dialogue) > 50 else s.dialogue
        table.add_row(str(s.scene_number), dialogue_preview, f"{s.duration_seconds}s")

    console.print(table)
    console.print(f"\nNext: [bold]mochi images {script_path}[/]")


@cli.command()
@click.argument("script_path", type=click.Path(exists=True))
def images(script_path: str) -> None:
    """Generate image prompts for Higgsfield Nano Banana 2.

    Prints all prompts and settings — paste them into Higgsfield.

    Example: mochi images output/japan/shorts/great_fire/script.json
    """
    from mochi.services.image_gen import (
        generate_image_instructions,
        generate_thumbnail_instructions,
    )

    script_obj, script_dir = _load_script(script_path)
    img_dir = script_dir / "images"

    generate_image_instructions(script_obj, img_dir)
    generate_thumbnail_instructions(script_obj, script_dir)

    console.print(f"\nNext: [bold]mochi clips {script_path}[/]")


@cli.command()
@click.argument("script_path", type=click.Path(exists=True))
def clips(script_path: str) -> None:
    """Generate video prompts for Higgsfield Kling 3.0.

    Prints all prompts with settings (enhanced OFF, audio ON, 1080p).
    For long-form: groups into multi-shot sequences of 5.

    Example: mochi clips output/japan/shorts/great_fire/script.json
    """
    from mochi.services.video_gen import generate_video_instructions

    script_obj, script_dir = _load_script(script_path)
    img_dir = script_dir / "images"
    clip_dir = script_dir / "clips"

    generate_video_instructions(script_obj, img_dir, clip_dir)

    console.print(f"\nNext: [bold]mochi assemble {script_path}[/]")


@cli.command()
@click.argument("script_path", type=click.Path(exists=True))
@click.option("--no-label", is_flag=True, help="Skip top label overlay")
def assemble(script_path: str, no_label: bool) -> None:
    """Stitch downloaded clips into final video with ffmpeg.

    Clips must be saved in the clips/ directory as clip_001.mp4, etc.
    Audio is already embedded (Kling 3.0 generates it).

    Example: mochi assemble output/japan/shorts/great_fire/script.json
    """
    from mochi.services.assembler import assemble_video

    script_obj, script_dir = _load_script(script_path)
    clip_dir = script_dir / "clips"
    output_path = script_dir / "final.mp4"

    clip_paths = sorted(clip_dir.glob("clip_*.mp4"))

    if not clip_paths:
        console.print(
            f"[bold red]No clips found in {clip_dir}[/]\n"
            f"Download your Kling 3.0 clips and save them as:\n"
            f"  {clip_dir}/clip_001.mp4\n"
            f"  {clip_dir}/clip_002.mp4\n"
            f"  ..."
        )
        return

    with Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]{task.description}"),
        console=console,
    ) as progress:
        progress.add_task("Assembling final video...", total=None)
        result = assemble_video(
            script_obj,
            list(clip_paths),
            output_path,
            add_label=not no_label,
        )

    console.print(Panel(
        f"[bold green]Video assembled![/]\n\n"
        f"Title: {script_obj.title}\n"
        f"Top Label: {script_obj.top_label}\n"
        f"Clips: {len(clip_paths)}\n"
        f"Output: {result}",
        title="Final Video",
    ))


@cli.command()
@click.argument("topic")
@click.option("--channel", "-c", type=click.Choice(["japan", "china"]), required=True)
@click.option("--format", "-f", "fmt", type=click.Choice(["short", "long"]), default="short")
def produce(topic: str, channel: str, fmt: str) -> None:
    """Full pipeline: generate script + all prompts for Higgsfield.

    Generates everything you need, then waits for you to create
    images and clips in Higgsfield before assembling.

    Example: mochi produce "The Great Fire of Meireki 1657" -c japan -f long
    """
    from mochi.services.script_writer import generate_script
    from mochi.services.image_gen import (
        generate_image_instructions,
        generate_thumbnail_instructions,
    )
    from mochi.services.video_gen import generate_video_instructions

    ch = Channel(channel)
    vf = VideoFormat(fmt)

    with Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]{task.description}"),
        console=console,
    ) as progress:
        progress.add_task("Writing script via GPT-4o...", total=None)
        script_obj = asyncio.run(generate_script(topic, ch, vf))

    slug = _slugify(script_obj.title)
    out_dir = _output_dir_for(ch, vf, slug)
    script_path = _save_script(script_obj, out_dir)

    console.print(Panel(
        f"[bold green]Script generated![/]\n\n"
        f"Title: {script_obj.title}\n"
        f"Hook: {script_obj.hook}\n"
        f"Top Label: {script_obj.top_label}\n"
        f"Scenes: {script_obj.scene_count}\n"
        f"Duration: ~{script_obj.total_duration}s",
        title="Step 1/4: Script",
    ))

    # Step 2: Image instructions
    console.print("\n" + "=" * 60 + "\n")
    img_dir = out_dir / "images"
    generate_image_instructions(script_obj, img_dir)
    generate_thumbnail_instructions(script_obj, out_dir)

    # Step 3: Video instructions
    console.print("\n" + "=" * 60 + "\n")
    clip_dir = out_dir / "clips"
    generate_video_instructions(script_obj, img_dir, clip_dir)

    # Step 4: Assembly instructions
    console.print("\n" + "=" * 60 + "\n")
    console.print(Panel(
        f"[bold]After generating images and clips in Higgsfield:[/]\n\n"
        f"1. Save images to: {img_dir}/scene_XXX.png\n"
        f"2. Save clips to: {clip_dir}/clip_XXX.mp4\n"
        f"3. Run: [bold]mochi assemble {script_path}[/]\n\n"
        f"This will stitch all clips + add the top label overlay.",
        title="Step 4/4: Assembly",
    ))


@cli.command()
def status() -> None:
    """Show project status — config, assets, and video counts."""
    config = load_config()

    table = Table(title="Mochi Project Status")
    table.add_column("Component", style="bold")
    table.add_column("Status")

    # API / tools
    table.add_row(
        "Higgsfield API",
        "[green]Configured[/]" if config.higgsfield.api_key else "[yellow]Manual mode[/]",
    )
    table.add_row(
        "OPENAI_API_KEY",
        "[green]Set[/]" if __import__("os").environ.get("OPENAI_API_KEY") else "[red]Missing[/]",
    )
    table.add_row(
        "ffmpeg",
        _check_ffmpeg_status(),
    )

    # Character refs
    ref_images = list(CHARACTER_DIR.glob("*.jpg")) + list(CHARACTER_DIR.glob("*.png"))
    table.add_row("Character refs", f"[green]{len(ref_images)} images[/]")

    # Video counts
    for ch in ["japan", "china"]:
        for fmt in ["shorts", "longform"]:
            video_dir = OUTPUT_DIR / ch / fmt
            if video_dir.exists():
                videos = list(video_dir.glob("*/final.mp4"))
                scripts = list(video_dir.glob("*/script.json"))
                table.add_row(
                    f"{ch}/{fmt}",
                    f"{len(videos)} videos, {len(scripts)} scripts",
                )
            else:
                table.add_row(f"{ch}/{fmt}", "0 videos")

    console.print(table)

    console.print("\n[bold]Workflow:[/]")
    console.print("  1. mochi script → 2. mochi images → 3. mochi clips → 4. mochi assemble")
    console.print("\n[bold]Tools needed:[/]")
    console.print("  - Higgsfield account ($15-34/mo) — higgsfield.ai")
    console.print("  - OpenAI API key — platform.openai.com")
    console.print("  - ffmpeg — brew install ffmpeg")


def _check_ffmpeg_status() -> str:
    """Check if ffmpeg is installed."""
    import subprocess
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
        return "[green]Installed[/]"
    except FileNotFoundError:
        return "[red]Not installed (brew install ffmpeg)[/]"


def main() -> None:
    cli()


if __name__ == "__main__":
    main()
