"""FFmpeg-based watermarking implementation.

This replaces the previous MoviePy-based approach with a single ffmpeg
subprocess call. It probes the video height (via ffprobe) to compute a
logo scale based on the actual video size and runs ffmpeg with a
filter_complex that resizes/crops the video to 1080x1920 and overlays
the scaled logo at the requested corner with padding.

Requirements: `ffmpeg` and `ffprobe` must be available on PATH.
"""
from __future__ import annotations

from pathlib import Path
import shutil
import subprocess
import os
import shlex
from typing import Optional


def _which(cmd: str) -> Optional[str]:
    return shutil.which(cmd)


def _ffprobe_height(path: str) -> int:
    """Return the video height (int) using ffprobe, raise RuntimeError if it fails."""
    ffprobe = _which("ffprobe")
    if not ffprobe:
        raise RuntimeError("ffprobe binary not found; please install ffmpeg package.")
    cmd = [ffprobe, "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=height", "-of", "csv=p=0", path]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"ffprobe failed: {res.stderr.strip()}")
    try:
        return int(res.stdout.strip())
    except Exception as e:
        raise RuntimeError(f"Failed to parse ffprobe output: {res.stdout!r}") from e


def get_output_filepath(input_filepath: str, output_dir: Optional[str] = None) -> str:
    base = Path(input_filepath)
    name = base.stem
    ext = base.suffix or ".mp4"
    from datetime import datetime

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_name = f"{name}_{timestamp}_marked{ext}"
    if output_dir:
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        return str(Path(output_dir) / out_name)
    return str(base.with_name(out_name))


def add_watermark(video_filepath: str, logo_filepath: str, output_dir: Optional[str] = None, position: str = "bottom-right", scale: float = 0.2) -> str:
    """Add watermark using ffmpeg and return the output filepath.

    - `scale` is relative to video height (e.g. 0.2 means logo height = 20% of video height).
    - `position` one of top-left, top-right, bottom-left, bottom-right, full.
    """
    ffmpeg = _which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError("ffmpeg binary not found; please install ffmpeg.")

    # Ensure output dir exists
    out_path = get_output_filepath(video_filepath, output_dir)

    # Probe video height to compute logo scale
    try:
        v_height = _ffprobe_height(video_filepath)
    except Exception:
        # fallback to target height
        v_height = 1920

    logo_h = max(1, int(v_height * float(scale)))

    # Build overlay position expression
    padding_x = 15
    padding_y = 55  # leave extra space for controls at bottom
    if position == "top-left":
        overlay = f"{padding_x}:{padding_y}"
    elif position == "top-right":
        overlay = f"main_w-overlay_w-{padding_x}:{padding_y}"
    elif position == "bottom-left":
        overlay = f"{padding_x}:main_h-overlay_h-{padding_y}"
    elif position == "full":
        # full screen: scale logo to video dimensions and overlay at 0,0
        overlay = "0:0"
    else:  # bottom-right
        overlay = f"main_w-overlay_w-{padding_x}:main_h-overlay_h-{padding_y}"

    # filter_complex: scale/crop video to 1080x1920, scale logo, overlay
    # First, scale video to cover target area then center-crop
    filter_parts = []
    # scale to cover 1080x1920
    filter_parts.append("[0:v]scale='if(gt(iw/ih,1080/1920),-1,1080)':'if(gt(iw/ih,1080/1920),1920,-1)',crop=1080:1920,setsar=1[v]")
    # scale logo height
    if position == "full":
        # scale logo to full video
        filter_parts.append(f"[1:v]scale=1080:1920[logo]")
    else:
        filter_parts.append(f"[1:v]scale=-1:{logo_h}[logo]")
    filter_parts.append(f"[v][logo]overlay={overlay}[outv]")

    filter_complex = ";".join(filter_parts)

    cmd = [
        ffmpeg,
        "-y",
        "-i",
        str(video_filepath),
        "-i",
        str(logo_filepath),
        "-filter_complex",
        filter_complex,
        "-map",
        "[outv]",
        "-map",
        "0:a?",
        "-c:v",
        "libx264",
        "-preset",
        "veryfast",
        "-crf",
        "23",
        "-c:a",
        "copy",
        str(out_path),
    ]

    try:
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as e:
        # include stderr for diagnostics
        err = e.stderr.decode(errors='ignore') if e.stderr else str(e)
        raise RuntimeError(f"ffmpeg failed: {err}") from e

    return out_path