"""Mochi CLI — the main entry point."""

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
from mochi.models.script import Channel, VideoFormat

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


@click.group()
@click.version_option(version=__version__)
def cli() -> None:
    """Mochi CLI — AI-powered POV history video production agent.

    A cat named Mochi time-travels through history.
    You make the videos. Mochi does the narrating.
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
    """Generate a video script for a topic.

    Example: mochi script "The Great Fire of Meireki 1657" -c japan -f short
    """
    from mochi.services.script_writer import generate_script

    config = load_config()
    ch = Channel(channel)
    vf = VideoFormat(fmt)

    with Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Writing script...", total=None)
        result = asyncio.run(generate_script(topic, ch, vf, config))

    slug = _slugify(result.title)
    out_dir = _output_dir_for(ch, vf, slug)
    script_path = out_dir / "script.json"

    script_data = {
        "title": result.title,
        "hook": result.hook,
        "channel": result.channel.value,
        "format": result.format.value,
        "era": result.era,
        "event": result.event,
        "description": result.description,
        "hashtags": list(result.hashtags),
        "scenes": [
            {
                "scene_number": s.scene_number,
                "description": s.description,
                "narration": s.narration,
                "video_prompt": s.video_prompt,
                "duration_seconds": s.duration_seconds,
            }
            for s in result.scenes
        ],
    }

    with open(script_path, "w") as f:
        json.dump(script_data, f, indent=2)

    console.print(Panel(
        f"[bold green]Script generated![/]\n\n"
        f"Title: {result.title}\n"
        f"Hook: {result.hook}\n"
        f"Scenes: {result.scene_count}\n"
        f"Duration: ~{result.total_duration}s\n"
        f"Saved: {script_path}",
        title="Mochi Script",
    ))

    # Show scene table
    table = Table(title="Scenes")
    table.add_column("#", style="bold")
    table.add_column("Narration", max_width=60)
    table.add_column("Duration")

    for s in result.scenes:
        narration_preview = s.narration[:57] + "..." if len(s.narration) > 60 else s.narration
        table.add_row(str(s.scene_number), narration_preview, f"{s.duration_seconds}s")

    console.print(table)


@cli.command()
@click.argument("script_path", type=click.Path(exists=True))
def images(script_path: str) -> None:
    """Generate scene images from a script.

    Example: mochi images output/japan/shorts/great_fire/script.json
    """
    from mochi.services.image_gen import generate_all_scene_images, generate_thumbnail
    from mochi.models.script import Script, Scene

    config = load_config()
    script_dir = Path(script_path).parent

    with open(script_path) as f:
        data = json.load(f)

    script_obj = Script(
        title=data["title"],
        hook=data["hook"],
        channel=Channel(data["channel"]),
        format=VideoFormat(data["format"]),
        era=data["era"],
        event=data["event"],
        scenes=tuple(
            Scene(**s) for s in data["scenes"]
        ),
        hashtags=tuple(data.get("hashtags", [])),
        description=data.get("description", ""),
    )

    img_dir = script_dir / "images"

    with Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task(
            f"Generating {script_obj.scene_count} scene images...", total=None
        )
        paths = asyncio.run(
            generate_all_scene_images(script_obj, img_dir, config)
        )

        progress.update(task, description="Generating thumbnail...")
        thumb_path = script_dir / "thumbnail.png"
        asyncio.run(generate_thumbnail(script_obj, thumb_path, config))

    console.print(f"[bold green]Generated {len(paths)} images + thumbnail[/]")
    console.print(f"Saved to: {img_dir}")


@cli.command()
@click.argument("script_path", type=click.Path(exists=True))
def voice(script_path: str) -> None:
    """Generate Mochi's voiceover from a script.

    Example: mochi voice output/japan/shorts/great_fire/script.json
    """
    from mochi.services.voice import generate_voice, generate_scene_voices
    from mochi.models.script import Script, Scene

    config = load_config()
    script_dir = Path(script_path).parent

    with open(script_path) as f:
        data = json.load(f)

    script_obj = Script(
        title=data["title"],
        hook=data["hook"],
        channel=Channel(data["channel"]),
        format=VideoFormat(data["format"]),
        era=data["era"],
        event=data["event"],
        scenes=tuple(Scene(**s) for s in data["scenes"]),
        hashtags=tuple(data.get("hashtags", [])),
        description=data.get("description", ""),
    )

    voice_dir = script_dir / "voice"

    with Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Generating full narration...", total=None)
        full_path = script_dir / "narration.mp3"
        asyncio.run(generate_voice(script_obj, full_path, config))

        progress.update(task, description="Generating per-scene audio...")
        asyncio.run(generate_scene_voices(script_obj, voice_dir, config))

    console.print(f"[bold green]Voice generated![/]")
    console.print(f"Full narration: {full_path}")
    console.print(f"Scene clips: {voice_dir}")


@cli.command()
@click.argument("script_path", type=click.Path(exists=True))
@click.option(
    "--engine", "-e",
    type=click.Choice(["veo", "higgsfield"]),
    default="veo",
    help="Video generation engine",
)
def clips(script_path: str, engine: str) -> None:
    """Generate video clips from scene images.

    Example: mochi clips output/japan/shorts/great_fire/script.json --engine veo
    """
    from mochi.services.video_gen import generate_all_clips
    from mochi.models.script import Scene

    config = load_config()
    script_dir = Path(script_path).parent

    with open(script_path) as f:
        data = json.load(f)

    scenes = [Scene(**s) for s in data["scenes"]]
    img_dir = script_dir / "images"
    clip_dir = script_dir / "clips"

    if engine == "higgsfield":
        console.print("[bold yellow]Higgsfield mode — manual upload required.[/]")
        console.print("Upload each scene image to Higgsfield Cinema Studio.\n")

    with Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task(
            f"Generating {len(scenes)} clips via {engine}...", total=None
        )
        paths = asyncio.run(
            generate_all_clips(scenes, img_dir, clip_dir, config, engine)
        )

    console.print(f"[bold green]Generated {len(paths)} clips[/]")
    console.print(f"Saved to: {clip_dir}")


@cli.command()
@click.argument("script_path", type=click.Path(exists=True))
def assemble(script_path: str) -> None:
    """Assemble final video from clips + voice.

    Example: mochi assemble output/japan/shorts/great_fire/script.json
    """
    from mochi.services.assembler import assemble_video
    from mochi.models.script import Script, Scene

    script_dir = Path(script_path).parent

    with open(script_path) as f:
        data = json.load(f)

    script_obj = Script(
        title=data["title"],
        hook=data["hook"],
        channel=Channel(data["channel"]),
        format=VideoFormat(data["format"]),
        era=data["era"],
        event=data["event"],
        scenes=tuple(Scene(**s) for s in data["scenes"]),
        hashtags=tuple(data.get("hashtags", [])),
        description=data.get("description", ""),
    )

    clip_dir = script_dir / "clips"
    voice_path = script_dir / "narration.mp3"
    output_path = script_dir / "final.mp4"

    clip_paths = sorted(clip_dir.glob("clip_*.mp4"))

    if not clip_paths:
        console.print("[bold red]No clips found. Run `mochi clips` first.[/]")
        return
    if not voice_path.exists():
        console.print("[bold red]No narration found. Run `mochi voice` first.[/]")
        return

    with Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Assembling final video...", total=None)
        result = assemble_video(
            script_obj,
            list(clip_paths),
            voice_path,
            output_path,
        )

    console.print(Panel(
        f"[bold green]Video assembled![/]\n\n"
        f"Title: {script_obj.title}\n"
        f"Output: {result}\n"
        f"Scenes: {len(clip_paths)} clips\n",
        title="Final Video",
    ))


@cli.command()
@click.argument("topic")
@click.option("--channel", "-c", type=click.Choice(["japan", "china"]), required=True)
@click.option("--format", "-f", "fmt", type=click.Choice(["short", "long"]), default="short")
@click.option("--engine", "-e", type=click.Choice(["veo", "higgsfield"]), default="veo")
def produce(topic: str, channel: str, fmt: str, engine: str) -> None:
    """Full pipeline: script → images → voice → clips → assemble.

    Example: mochi produce "The Great Fire of Meireki 1657" -c japan -f long -e veo
    """
    from mochi.services.script_writer import generate_script
    from mochi.services.image_gen import generate_all_scene_images, generate_thumbnail
    from mochi.services.voice import generate_voice
    from mochi.services.video_gen import generate_all_clips
    from mochi.services.assembler import assemble_video

    config = load_config()
    ch = Channel(channel)
    vf = VideoFormat(fmt)

    with Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]{task.description}"),
        console=console,
    ) as progress:
        # Step 1: Script
        task = progress.add_task("Step 1/5: Writing script...", total=None)
        script_obj = asyncio.run(generate_script(topic, ch, vf, config))

        slug = _slugify(script_obj.title)
        out_dir = _output_dir_for(ch, vf, slug)

        script_path = out_dir / "script.json"
        script_data = {
            "title": script_obj.title,
            "hook": script_obj.hook,
            "channel": script_obj.channel.value,
            "format": script_obj.format.value,
            "era": script_obj.era,
            "event": script_obj.event,
            "description": script_obj.description,
            "hashtags": list(script_obj.hashtags),
            "scenes": [
                {
                    "scene_number": s.scene_number,
                    "description": s.description,
                    "narration": s.narration,
                    "video_prompt": s.video_prompt,
                    "duration_seconds": s.duration_seconds,
                }
                for s in script_obj.scenes
            ],
        }
        with open(script_path, "w") as f:
            json.dump(script_data, f, indent=2)

        # Step 2: Images
        progress.update(task, description="Step 2/5: Generating scene images...")
        img_dir = out_dir / "images"
        asyncio.run(generate_all_scene_images(script_obj, img_dir, config))
        asyncio.run(generate_thumbnail(script_obj, out_dir / "thumbnail.png", config))

        # Step 3: Voice
        progress.update(task, description="Step 3/5: Generating Mochi's voice...")
        voice_path = out_dir / "narration.mp3"
        asyncio.run(generate_voice(script_obj, voice_path, config))

        # Step 4: Video clips
        progress.update(task, description=f"Step 4/5: Generating clips via {engine}...")
        clip_dir = out_dir / "clips"
        clip_paths = asyncio.run(
            generate_all_clips(
                list(script_obj.scenes), img_dir, clip_dir, config, engine
            )
        )

        # Step 5: Assemble
        progress.update(task, description="Step 5/5: Assembling final video...")
        final_path = out_dir / "final.mp4"
        assemble_video(script_obj, clip_paths, voice_path, final_path)

    console.print(Panel(
        f"[bold green]Production complete![/]\n\n"
        f"Title: {script_obj.title}\n"
        f"Hook: {script_obj.hook}\n"
        f"Scenes: {script_obj.scene_count}\n"
        f"Output: {final_path}\n",
        title="Mochi Production Complete",
    ))


@cli.command()
def status() -> None:
    """Show project status — config, assets, and video counts."""
    config = load_config()

    table = Table(title="Mochi Project Status")
    table.add_column("Component", style="bold")
    table.add_column("Status")

    # API keys
    table.add_row(
        "Google AI API",
        "[green]Configured[/]" if config.google.api_key else "[red]Missing[/]",
    )
    table.add_row(
        "ElevenLabs API",
        "[green]Configured[/]" if config.elevenlabs.api_key else "[red]Missing[/]",
    )
    table.add_row(
        "ElevenLabs Voice ID",
        f"[green]{config.elevenlabs.voice_id}[/]" if config.elevenlabs.voice_id else "[red]Not set[/]",
    )
    table.add_row(
        "Higgsfield API",
        "[green]Configured[/]" if config.higgsfield.api_key else "[yellow]Optional[/]",
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
                table.add_row(f"{ch}/{fmt}", f"{len(videos)} videos")
            else:
                table.add_row(f"{ch}/{fmt}", "0 videos")

    console.print(table)


def main() -> None:
    cli()


if __name__ == "__main__":
    main()
