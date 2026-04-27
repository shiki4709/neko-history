"""Video assembly — stitch Kling 3.0 clips using ffmpeg.

Clips already contain audio (Kling generates dialogue with audio ON),
so assembly is just concatenation + optional caption overlay.
"""

from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

from mochi.models.script import Script


def _check_ffmpeg() -> None:
    """Verify ffmpeg is installed."""
    try:
        subprocess.run(
            ["ffmpeg", "-version"],
            capture_output=True,
            check=True,
        )
    except FileNotFoundError:
        raise RuntimeError(
            "ffmpeg not found. Install it: brew install ffmpeg"
        )


def stitch_clips(
    clip_paths: list[Path],
    output_path: Path,
) -> Path:
    """Concatenate video clips into a single video.

    Clips already have audio from Kling 3.0, so we just concat.
    """
    _check_ffmpeg()

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".txt", delete=False
    ) as f:
        for clip in clip_paths:
            f.write(f"file '{clip.resolve()}'\n")
        concat_file = Path(f.name)

    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            [
                "ffmpeg", "-y",
                "-f", "concat",
                "-safe", "0",
                "-i", str(concat_file),
                "-c", "copy",
                str(output_path),
            ],
            capture_output=True,
            check=True,
        )
    finally:
        concat_file.unlink(missing_ok=True)

    return output_path


def add_top_label(
    video_path: Path,
    label_text: str,
    output_path: Path,
) -> Path:
    """Add the top label overlay (e.g., 'I went to Edo to see the Great Fire').

    Mimics the Instagram Edits app style: text with background box at top center.
    """
    _check_ffmpeg()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            "ffmpeg", "-y",
            "-i", str(video_path),
            "-vf",
            f"drawtext=text='{label_text}':"
            "fontfile=/System/Library/Fonts/Helvetica.ttc:"
            "fontsize=28:fontcolor=white:"
            "box=1:boxcolor=black@0.7:boxborderw=10:"
            "x=(w-text_w)/2:y=60",
            "-c:a", "copy",
            str(output_path),
        ],
        capture_output=True,
        check=True,
    )
    return output_path


def burn_captions(
    video_path: Path,
    srt_path: Path,
    output_path: Path,
) -> Path:
    """Burn subtitle captions into the video."""
    _check_ffmpeg()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            "ffmpeg", "-y",
            "-i", str(video_path),
            "-vf", f"subtitles={srt_path}:force_style="
                   "'FontName=Arial,FontSize=24,PrimaryColour=&Hffffff&,"
                   "OutlineColour=&H000000&,Outline=2,Bold=1'",
            "-c:a", "copy",
            str(output_path),
        ],
        capture_output=True,
        check=True,
    )
    return output_path


def assemble_video(
    script: Script,
    clip_paths: list[Path],
    output_path: Path,
    add_label: bool = True,
) -> Path:
    """Full assembly: stitch clips → optional top label.

    No separate audio overlay needed — Kling 3.0 generates
    dialogue audio directly in each clip.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Step 1: Stitch all clips
    if add_label and script.top_label:
        stitched = output_path.parent / "stitched_raw.mp4"
    else:
        stitched = output_path

    stitch_clips(clip_paths, stitched)

    # Step 2: Add top label if set
    if add_label and script.top_label:
        add_top_label(stitched, script.top_label, output_path)
        stitched.unlink(missing_ok=True)

    return output_path
