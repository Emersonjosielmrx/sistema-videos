import sys
from pathlib import Path
sys.path.insert(0, str(Path("D:/historias-em-frames/bin")))
from image_generator import generate_images_for_story

story = {
    "genero": "religioso",
    "cenas": [
        {"texto": "O homem orou a Deus no pico do monte", "image_prompt": "A man praying on a mountain peak, sunset", "mood": "calm_chill"}
    ] * 6  # 6 scenes
}

try:
    generate_images_for_story(story, n_variations=2, story_id="test_quota")
except Exception as e:
    print(f"Error: {e}")
