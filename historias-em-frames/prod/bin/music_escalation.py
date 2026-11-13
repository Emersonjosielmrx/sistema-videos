# -*- coding: utf-8 -*-
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
try:
    from hp_common import PROJECT_DIR, log
except ImportError:
    PROJECT_DIR = Path(__file__).resolve().parent.parent
    def log(msg, level="info"):
        print(f"[{level.upper()}] {msg}")

MUSIC_ESCALATION = os.environ.get("MUSIC_ESCALATION", "1") == "1"

INTENSITY_MAP = {
    "tense_dramatic": 0.85,
    "action": 0.95,
    "sad_emotional": 0.7,
    "romantic_sexy": 0.5,
    "funny_lighthearted": 0.4,
    "calm_chill": 0.3,
    "neutral_chill": 0.4,
}

def analyze_narrative_arc(cenas):
    if not cenas: return []
    total = len(cenas)
    intensities = []
    
    for i, cena in enumerate(cenas):
        mood = cena.get("mood", "neutral_chill")
        base_int = INTENSITY_MAP.get(mood, 0.4)
        
        # Last 25% boost
        if i >= total * 0.75:
            if mood in ["tense_dramatic", "action"]:
                base_int += 0.2
                
        # First 10% boost for hook
        if i <= total * 0.1:
            base_int += 0.1
            
        # Penultimate scene = peak
        if total > 1 and i == total - 2:
            if mood in ["tense_dramatic", "action"]:
                base_int = 1.0
            else:
                base_int += 0.2
                
        # Last scene = resolution
        if i == total - 1:
            base_int *= 0.6
            
        base_int = max(0.0, min(1.0, base_int))
        intensities.append(base_int)
        
    return intensities

def get_volume_envelope(cenas, base_volume=0.15, max_volume=0.35):
    intensities = analyze_narrative_arc(cenas)
    volumes = []
    for intensity in intensities:
        v = base_volume + (max_volume - base_volume) * intensity
        volumes.append(round(v, 3))
    return volumes

def build_volume_filter(volumes, scene_durations):
    if not volumes or not scene_durations: return ""
    filters = []
    current_time = 0.0
    for v, dur in zip(volumes, scene_durations):
        start = current_time
        end = round(current_time + dur, 3)
        filters.append(f"volume=enable='between(t,{start},{end})':volume={v}")
        current_time = end
    return ",".join(filters)

def suggest_track_switch(cenas, current_mood_blocks):
    if not cenas: return []
    intensities = analyze_narrative_arc(cenas)
    suggestions = []
    for i in range(len(cenas)):
        current_int = intensities[i]
        prev_int = intensities[i-1] if i > 0 else current_int
        diff = current_int - prev_int
        
        if diff >= 0.2:
            action = "intensify"
        elif diff <= -0.15:
            action = "calm"
        else:
            action = "maintain"
            
        suggestions.append({"scene_idx": i, "action": action})
    return suggestions

def get_escalation_metadata(cenas):
    if not cenas:
        return {"peak_scene_idx": 0, "resolution_scene_idx": 0, "overall_intensity_profile": "flat"}
        
    intensities = analyze_narrative_arc(cenas)
    peak_idx = intensities.index(max(intensities))
    res_idx = len(cenas) - 1
    
    max_int = max(intensities)
    min_int = min(intensities)
    
    if max_int - min_int < 0.2:
        profile = "flat"
    elif peak_idx >= len(cenas) * 0.7:
        profile = "building"
    else:
        profile = "rollercoaster"
        
    return {
        "peak_scene_idx": peak_idx,
        "resolution_scene_idx": res_idx,
        "overall_intensity_profile": profile
    }
