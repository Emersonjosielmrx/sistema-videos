# -*- coding: utf-8 -*-
import os
import sys
from pathlib import Path

# Setup project path and logger
sys.path.insert(0, str(Path(__file__).resolve().parent))
try:
    from hp_common import PROJECT_DIR, log
except ImportError:
    PROJECT_DIR = Path(__file__).resolve().parent.parent
    def log(msg, **kwargs):
        level = kwargs.get("level", "INFO")
        print(f"[{level}] {msg}")

# Environment variable check
ADVANCED_PARALLAX_ENABLED = os.environ.get("ADVANCED_PARALLAX", "0") == "1"

def get_style_for_mood(mood: str) -> str:
    """
    Maps narrative moods to parallax styles.
    """
    if not mood:
        return "zoom_in"

    mood = mood.lower()
    if any(m in mood for m in ["action", "fight", "dynamic", "epic", "battle"]):
        return "dynamic_tilt"
    elif any(m in mood for m in ["tense", "dramatic", "suspense", "fear", "dark"]):
        return "zoom_in"
    elif any(m in mood for m in ["peaceful", "sad", "calm", "melancholy", "quiet"]):
        return "zoom_out"
    elif any(m in mood for m in ["exploration", "travel", "scenic", "journey", "walk"]):
        return "pan_right"
    else:
        return "pan_left"

def build_parallax_filter(style: str, duration: float, width: int = 1080, height: int = 1920) -> str:
    """
    Returns the ffmpeg complex filter string for the desired 2.5D parallax effect.
    """
    fps = 30
    frames = int(duration * fps)

    # Scale and crop the input image so it matches exactly the desired canvas size before zooming
    base_calc = f"scale={width}:{height}:force_original_aspect_ratio=increase,crop={width}:{height}"

    if style == "zoom_in":
        # Zoom from 1 to 1.15
        zp = (
            f"zoompan=z='min(1.15, zoom+0.0015)':d={frames}:"
            f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':fps={fps}:s={width}x{height}"
        )
        return f"{base_calc},{zp}"

    elif style == "zoom_out":
        # Zoom from 1.15 to 1
        # zoompan doesn't easily start zooming out; we set starting zoom to 1.15
        zp = (
            f"zoompan=z='1.15-(on*(0.15/{frames}))':d={frames}:"
            f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':fps={fps}:s={width}x{height}"
        )
        return f"{base_calc},{zp}"

    elif style == "pan_right":
        # Zoom 1.1, slide right (shift x)
        zp = (
            f"zoompan=z='1.1':d={frames}:"
            f"x='(iw-iw/1.1)*(on/{frames})':y='ih/2-(ih/zoom/2)':fps={fps}:s={width}x{height}"
        )
        return f"{base_calc},{zp}"

    elif style == "pan_left":
        # Zoom 1.1, slide left (start max x, move to 0)
        zp = (
            f"zoompan=z='1.1':d={frames}:"
            f"x='(iw-iw/1.1)*(1 - on/{frames})':y='ih/2-(ih/zoom/2)':fps={fps}:s={width}x{height}"
        )
        return f"{base_calc},{zp}"

    elif style == "dynamic_tilt":
        # Pseudo 2.5D via split:
        # Base image split into two:
        # Background: blurred, slight zoom out
        # Foreground: cropped center, fast zoom in
        # Then overlays the foreground on the background.

        bg_zp = (
            f"zoompan=z='1.1-(on*(0.1/{frames}))':d={frames}:"
            f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':fps={fps}:s={width}x{height}"
        )
        fg_zp = (
            f"zoompan=z='min(1.5, zoom+0.003)':d={frames}:"
            f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':fps={fps}:s={width}x{height}"
        )

        filter_str = (
            f"[0:v]{base_calc},split=2[bg_base][fg_base];"
            f"[bg_base]boxblur=10:5,{bg_zp}[bg];"
            f"[fg_base]crop=iw*0.6:ih*0.6:iw*0.2:ih*0.2,{fg_zp}[fg];"
            f"[bg][fg]overlay=(W-w)/2:(H-h)/2"
        )
        return filter_str

    else:
        # Fallback is zoom_in
        return build_parallax_filter("zoom_in", duration, width, height)

def generate_parallax_command(image_path: str, out_path: str, duration: float = 3.0, style: str = "zoom_in") -> str:
    """
    Generates the complete ffmpeg command to apply the parallax effect to a single image.
    """
    filter_str = build_parallax_filter(style, duration)

    # We input a single image and let zoompan generate `duration * 30` frames.
    cmd = (
        f"ffmpeg -y -i \"{image_path}\" "
        f"-filter_complex \"{filter_str}\" "
        f"-c:v libx264 -pix_fmt yuv420p -preset veryfast -crf 23 \"{out_path}\""
    )
    return cmd

if __name__ == "__main__":
    # Smoke test just to print the commands/filters
    test_dur = 3.0
    for s in ["zoom_in", "zoom_out", "pan_right", "pan_left", "dynamic_tilt"]:
        cmd = generate_parallax_command("input.jpg", f"output_{s}.mp4", test_dur, style=s)
        print(f"--- Style: {s} ---")
        print(cmd)
        print()
