import os
import sys
import tempfile
import subprocess
import json
import urllib.request
import re
from pathlib import Path
from PIL import Image, ImageStat

sys.path.insert(0, str(Path(__file__).resolve().parent))
try:
    from hp_common import PROJECT_DIR, log
except ImportError:
    PROJECT_DIR = Path(__file__).resolve().parent.parent
    def log(msg, level="INFO"):
        print(f"[{level}] {msg}")

QUALITY_JUDGE = os.environ.get("QUALITY_JUDGE", "0") == "1"
QUALITY_THRESHOLD = int(os.environ.get("QUALITY_THRESHOLD", "6"))
QUALITY_USE_VISION = os.environ.get("QUALITY_USE_VISION", "0") == "1"

import gateway_cfg  # noqa: E402
OMNIROUTE_URL = gateway_cfg.url("/v1/chat/completions")
OMNIROUTE_KEY = gateway_cfg.bearer()  # secrets/omniroute.json

def extract_sample_frames(video_path, n_frames=5, start_s=0, end_s=10):
    """
    Extracts N evenly-spaced frames from the first segment of the video
    using ffmpeg subprocess. Saves to temp dir and returns list of paths.
    """
    video_path = Path(video_path)
    if not video_path.exists():
        log(f"Video not found: {video_path}", "ERROR")
        return []

    temp_dir = Path(tempfile.mkdtemp(prefix="quality_judge_"))
    extracted_paths = []

    duration = end_s - start_s
    interval = duration / max(1, (n_frames - 1)) if n_frames > 1 else 0

    for i in range(n_frames):
        timestamp = start_s + (i * interval)
        out_path = temp_dir / f"frame_{i}.jpg"

        cmd = [
            "ffmpeg",
            "-y",
            "-ss", str(timestamp),
            "-i", str(video_path),
            "-vframes", "1",
            "-q:v", "2",
            str(out_path)
        ]

        try:
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            if out_path.exists():
                extracted_paths.append(out_path)
        except subprocess.CalledProcessError:
            log(f"Failed to extract frame at {timestamp}s", "WARNING")

    return extracted_paths

def heuristic_score(frame_paths):
    """
    Analyzes frames using PIL (Pillow).
    Variables:
    - brightness: mean pixel value (0-255), ideal 80-180
    - contrast: std dev of pixels, ideal >30
    - black_ratio: % of very dark pixels (<10), bad if >50%
    Returns dict with individual scores and overall 1-10 score.
    """
    if not frame_paths:
        return {"score": 0, "details": "No frames to analyze"}

    total_brightness = 0
    total_contrast = 0
    total_black_ratio = 0

    for pt in frame_paths:
        try:
            with Image.open(pt) as img:
                img_gray = img.convert("L")
                stat = ImageStat.Stat(img_gray)

                brightness = stat.mean[0]
                contrast = stat.stddev[0]

                hist = img_gray.histogram()
                black_pixels = sum(hist[:10])
                total_pixels = img_gray.width * img_gray.height
                black_ratio = black_pixels / total_pixels

                total_brightness += brightness
                total_contrast += contrast
                total_black_ratio += black_ratio
        except Exception as e:
            log(f"Error analyzing frame {pt}: {e}", "WARNING")

    n = len(frame_paths)
    if n == 0:
        return {"score": 0, "details": "Failed to analyze any frame"}

    avg_brightness = total_brightness / n
    avg_contrast = total_contrast / n
    avg_black_ratio = total_black_ratio / n

    # Base score
    score = 10.0

    # Penalize brightness out of ideal range (80-180)
    if avg_brightness < 80:
        score -= min(3, (80 - avg_brightness) / 15)
    elif avg_brightness > 180:
        score -= min(3, (avg_brightness - 180) / 15)

    # Penalize low contrast
    if avg_contrast < 30:
        score -= min(4, (30 - avg_contrast) / 5)

    # Penalize high black proportion
    if avg_black_ratio > 0.5:
        score -= min(4, (avg_black_ratio - 0.5) * 10)

    score = max(1.0, min(10.0, score))

    return {
        "score": round(score, 1),
        "brightness": round(avg_brightness, 2),
        "contrast": round(avg_contrast, 2),
        "black_ratio": round(avg_black_ratio, 3),
        "details": f"B={avg_brightness:.1f}, C={avg_contrast:.1f}, Black={avg_black_ratio:.1%}"
    }

def call_vision_api(image_path):
    """Optionally send frame to Gemini Vision for a 1-10 quality score."""
    import base64

    try:
        with open(image_path, "rb") as f:
            img_b64 = base64.b64encode(f.read()).decode("utf-8")

        payload = {
            "model": "gemini-2.5-flash-lite", # Uses routing pipeline
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Score this image's visual quality from 1 to 10. Focus on lighting, composition, artifacts and aesthetics. Return ONLY a single integer (e.g., '7'). 1=terrible/broken image, 10=perfect/professional."
                        },
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}
                        }
                    ]
                }
            ],
            "max_tokens": 10,
            "temperature": 0.1
        }

        req = urllib.request.Request(
            OMNIROUTE_URL,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": OMNIROUTE_KEY
            }
        )

        with urllib.request.urlopen(req, timeout=10) as response:
            res_data = json.loads(response.read().decode("utf-8"))
            content = res_data["choices"][0]["message"]["content"].strip()

            match = re.search(r'\b(10|[1-9])\b', content)
            if match:
                return {"score": int(match.group(1)), "details": "Vision API Success"}
            return {"score": 5, "details": f"Vision API Unexpected response: {content}"}

    except Exception as e:
        log(f"Vision API Error: {e}", "WARNING")
        return {"score": 5, "details": f"Vision API Error: {str(e)}"}

def judge_image(image_path):
    """
    Judges a single generated image (heuristics + optional vision).
    Returns dict with final 1-10 score.
    """
    path = Path(image_path)
    res = heuristic_score([path])

    if QUALITY_USE_VISION:
        v_res = call_vision_api(path)
        final_score = (res["score"] + v_res["score"]) / 2
        res["score"] = round(final_score, 1)
        res["details"] += f" | Vision={v_res['score']}"
        res["vision_score"] = v_res["score"]

    return res

def should_retry(image_path, threshold=None):
    """
    Returns True if image quality is below the threshold.
    Respects QUALITY_JUDGE master switch.
    """
    if not QUALITY_JUDGE:
        return False

    thresh = threshold if threshold is not None else QUALITY_THRESHOLD
    info = judge_image(image_path)

    log(f"Quality check image '{Path(image_path).name}': Score {info['score']}/10 (Thresh {thresh}) - {info['details']}")
    return info["score"] < thresh

def judge_video(video_path):
    """
    Quality judge for a whole video.
    Extracts heuristic frames, checks quality, cleans up, returns pass/fail.
    """
    if not QUALITY_JUDGE:
        return {"score": 10, "details": "Judge Disabled", "pass": True}

    frames = extract_sample_frames(video_path)
    if not frames:
        return {"score": 0, "details": "Failed to extract frames", "pass": False}

    res = heuristic_score(frames)

    if QUALITY_USE_VISION and len(frames) > 0:
        # Evaluate middle frame with Vision to represent video
        mid_frame = frames[len(frames) // 2]
        v_res = call_vision_api(mid_frame)
        final_score = (res["score"] + v_res["score"]) / 2
        res["score"] = round(final_score, 1)
        res["details"] += f" | Vision={v_res['score']}"
        res["vision_score"] = v_res["score"]

    res["pass"] = res["score"] >= QUALITY_THRESHOLD

    # Clean up
    temp_dir = None
    for f in frames:
        try:
            temp_dir = f.parent
            f.unlink()
        except Exception:
            pass

    if temp_dir and temp_dir.exists():
        try:
            temp_dir.rmdir()
        except Exception:
            pass

    log(f"Video '{Path(video_path).name}' judged: {'PASS' if res['pass'] else 'FAIL'}, Score {res['score']}/10 - {res['details']}")

    return res
