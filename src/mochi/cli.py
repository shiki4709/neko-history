"""Mochi CLI — the main entry point.

Workflow (matches the YouTube tutorial exactly):
1. Script: Paste prompt into ChatGPT website → get JSON back
2. Images: Paste prompts into Higgsfield → Nano Banana 2 (9:16, 2K)
3. Clips:  Upload images to Higgsfield → Kling 3.0 (enhanced OFF, audio ON, 1080p)
4. Stitch: ffmpeg concatenates clips (audio already embedded by Kling)
5. Polish: Add top label overlay via ffmpeg (like Instagram Edits app)

No API keys required — everything is copy-paste into web UIs.
"""

from __future__ import annotations

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


@click.group()
@click.version_option(version=__version__)
def cli() -> None:
    """Mochi CLI — AI-powered POV history video production agent.

    A cat named Mochi time-travels through history.

    \b
    Workflow:
      1. mochi script       → Get prompt to paste into ChatGPT
      2. mochi load-script   → Load ChatGPT's JSON response
      3. mochi images        → Get prompts for Higgsfield (Nano Banana 2)
      4. mochi clips         → Get prompts for Higgsfield (Kling 3.0)
      5. mochi assemble      → Stitch clips + add top label (ffmpeg)

    No API keys required. Everything is copy-paste.
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
    """Generate a ChatGPT prompt for script creation.

    Prints a prompt to paste into ChatGPT. ChatGPT returns JSON
    that you feed into `mochi load-script`.

    Example: mochi script "The Great Fire of Meireki 1657" -c japan -f short
    """
    from mochi.services.script_writer import print_chatgpt_instructions

    ch = Channel(channel)
    vf = VideoFormat(fmt)

    print_chatgpt_instructions(topic, ch, vf)


@cli.command("load-script")
@click.argument("json_file", type=click.Path(exists=True))
@click.option(
    "--channel", "-c",
    type=click.Choice(["japan", "china"]),
    required=True,
)
@click.option(
    "--format", "-f", "fmt",
    type=click.Choice(["short", "long"]),
    default="short",
)
def load_script(json_file: str, channel: str, fmt: str) -> None:
    """Load a script from ChatGPT's JSON response.

    Save ChatGPT's JSON output to a file, then load it here.

    Example: mochi load-script ~/Downloads/chatgpt_response.json -c japan -f short
    """
    from mochi.services.script_writer import parse_chatgpt_response, save_script_to_disk
    from mochi.services.tracker import add_video

    ch = Channel(channel)
    vf = VideoFormat(fmt)

    with open(json_file) as f:
        raw = f.read()

    script_obj = parse_chatgpt_response(raw, ch, vf)

    slug = _slugify(script_obj.title)
    out_dir = _output_dir_for(ch, vf, slug)
    script_path = save_script_to_disk(script_obj, out_dir)

    # Auto-track
    fmt_dir = "shorts" if vf == VideoFormat.SHORT else "longform"
    video_id = f"{ch.value}/{fmt_dir}/{slug}"
    add_video(video_id, script_obj.title, ch.value, vf.value, "script")

    console.print(Panel(
        f"[bold green]Script loaded![/]\n\n"
        f"Title: {script_obj.title}\n"
        f"Hook: {script_obj.hook}\n"
        f"Top Label: {script_obj.top_label}\n"
        f"Scenes: {script_obj.scene_count}\n"
        f"Duration: ~{script_obj.total_duration}s\n"
        f"Saved: {script_path}",
        title="Mochi Script",
    ))

    table = Table(title="Scenes")
    table.add_column("#", style="bold", width=4)
    table.add_column("Dialogue", max_width=50)
    table.add_column("Duration", width=8)

    for s in script_obj.scenes:
        preview = s.dialogue[:47] + "..." if len(s.dialogue) > 50 else s.dialogue
        table.add_row(str(s.scene_number), preview, f"{s.duration_seconds}s")

    console.print(table)
    console.print(f"\nNext: [bold]mochi images {script_path}[/]")


@cli.command()
@click.argument("script_path", type=click.Path(exists=True))
def images(script_path: str) -> None:
    """Print image prompts for Higgsfield Nano Banana 2.

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
    """Print video prompts for Higgsfield Kling 3.0.

    Settings: enhanced OFF, audio ON, 1080p, 10-15 sec.
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

    Clips must be saved as clip_001.mp4, clip_002.mp4, etc.

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
    """Full pipeline: generates all prompts for ChatGPT + Higgsfield.

    Example: mochi produce "The Great Fire of Meireki 1657" -c japan -f long
    """
    from mochi.services.script_writer import print_chatgpt_instructions

    ch = Channel(channel)
    vf = VideoFormat(fmt)

    print_chatgpt_instructions(topic, ch, vf)

    console.print("\n" + "=" * 60)
    console.print(Panel(
        f"[bold]After getting ChatGPT's JSON response:[/]\n\n"
        f"1. Save the JSON to a file (e.g., response.json)\n"
        f"2. Run: [bold]mochi load-script response.json -c {channel} -f {fmt}[/bold]\n"
        f"3. Run: [bold]mochi images <script.json>[/bold]\n"
        f"4. Generate images in Higgsfield (Nano Banana 2)\n"
        f"5. Run: [bold]mochi clips <script.json>[/bold]\n"
        f"6. Generate videos in Higgsfield (Kling 3.0)\n"
        f"7. Run: [bold]mochi assemble <script.json>[/bold]",
        title="Full Workflow",
    ))


@cli.command()
@click.option("--channel", "-c", type=click.Choice(["japan", "china"]), default=None)
@click.option("--stage", "-s", type=click.Choice(["script", "images", "clips", "assembled", "captioned", "published"]), default=None)
def tracker(channel: str | None, stage: str | None) -> None:
    """Show video production tracker.

    Example: mochi tracker
    Example: mochi tracker -c japan
    Example: mochi tracker -s clips
    """
    from mochi.services.tracker import print_tracker_table

    print_tracker_table(channel, stage)


@cli.command("track-update")
@click.argument("video_id")
@click.argument("stage", type=click.Choice(["script", "images", "clips", "assembled", "captioned", "published"]))
@click.option("--notes", "-n", default="", help="Optional notes")
def track_update(video_id: str, stage: str, notes: str) -> None:
    """Update a video's stage in the tracker.

    Example: mochi track-update japan/shorts/great_fire images
    """
    from mochi.services.tracker import update_stage

    entry = update_stage(video_id, stage, notes)
    if entry:
        console.print(f"[green]Updated:[/] {entry.title} → {stage} {entry.progress_bar}")
    else:
        console.print(f"[red]Video not found: {video_id}[/]")


@cli.command("track-publish")
@click.argument("video_id")
@click.argument("platform", type=click.Choice(["youtube", "tiktok", "instagram"]))
@click.argument("url")
def track_publish(video_id: str, platform: str, url: str) -> None:
    """Record a published URL for a video.

    Example: mochi track-publish japan/shorts/great_fire youtube https://youtu.be/xxx
    """
    from mochi.services.tracker import add_published_url

    add_published_url(video_id, platform, url)
    console.print(f"[green]Recorded:[/] {platform} → {url}")


@cli.command("track-detail")
@click.argument("video_id")
def track_detail(video_id: str) -> None:
    """Show detailed info for a tracked video.

    Example: mochi track-detail japan/shorts/great_fire
    """
    from mochi.services.tracker import print_video_detail

    print_video_detail(video_id)


@cli.command()
def status() -> None:
    """Show project status — assets, tools, and tracker summary."""
    from mochi.services.tracker import list_videos

    table = Table(title="Mochi Project Status")
    table.add_column("Component", style="bold")
    table.add_column("Status")

    # Tools
    table.add_row("ffmpeg", _check_ffmpeg_status())

    # Character refs
    ref_images = list(CHARACTER_DIR.glob("*.jpg")) + list(CHARACTER_DIR.glob("*.png"))
    table.add_row("Character refs", f"[green]{len(ref_images)} images[/]")

    # Tracker summary
    all_videos = list_videos()
    if all_videos:
        published = sum(1 for v in all_videos if v.stage == "published")
        in_progress = len(all_videos) - published
        table.add_row("Videos tracked", f"{len(all_videos)} total")
        table.add_row("Published", f"[green]{published}[/]")
        table.add_row("In progress", f"[yellow]{in_progress}[/]")
    else:
        table.add_row("Videos tracked", "0")

    # Video file counts
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
    console.print("  1. mochi script     → get ChatGPT prompt")
    console.print("  2. mochi load-script → load ChatGPT JSON response")
    console.print("  3. mochi images     → get Higgsfield image prompts")
    console.print("  4. mochi clips      → get Higgsfield video prompts")
    console.print("  5. mochi assemble   → stitch clips with ffmpeg")
    console.print("  6. mochi tracker    → view production progress")
    console.print("\n[bold]Tools needed:[/]")
    console.print("  - ChatGPT (free) — chatgpt.com")
    console.print("  - Higgsfield ($15-34/mo) — higgsfield.ai")
    console.print("  - ffmpeg (free) — brew install ffmpeg")


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
