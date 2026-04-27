"""Video assembly service — stitches clips + voice using ffmpeg."""

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
    """Concatenate video clips into a single video using ffmpeg."""
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


def overlay_audio(
    video_path: Path,
    audio_path: Path,
    output_path: Path,
) -> Path:
    """Overlay narration audio onto the stitched video."""
    _check_ffmpeg()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            "ffmpeg", "-y",
            "-i", str(video_path),
            "-i", str(audio_path),
            "-c:v", "copy",
            "-c:a", "aac",
            "-map", "0:v:0",
            "-map", "1:a:0",
            "-shortest",
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
    """Burn subtitle captions into the video for Shorts/Reels."""
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
    voice_path: Path,
    output_path: Path,
    burn_subs: bool = False,
    srt_path: Path | None = None,
) -> Path:
    """Full assembly pipeline: stitch clips → overlay voice → optional captions.

    Returns path to the final video.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Step 1: Stitch clips
    stitched = output_path.parent / "stitched_raw.mp4"
    stitch_clips(clip_paths, stitched)

    # Step 2: Overlay narration
    with_audio = output_path.parent / "with_audio.mp4"
    overlay_audio(stitched, voice_path, with_audio)

    # Step 3: Burn captions (optional, mainly for Shorts)
    if burn_subs and srt_path is not None and srt_path.exists():
        burn_captions(with_audio, srt_path, output_path)
    else:
        with_audio.rename(output_path)

    # Cleanup intermediate files
    stitched.unlink(missing_ok=True)
    if (output_path.parent / "with_audio.mp4").exists():
        (output_path.parent / "with_audio.mp4").unlink(missing_ok=True)

    return output_path
