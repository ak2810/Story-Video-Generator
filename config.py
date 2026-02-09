"""
config.py  -  Viral Ball Simulator  -  GAUNTLET VIDEO FACTORY

One video = Hook intro -> 6 escalating rounds -> Finale end-card.
Running RED vs BLUE scoreboard persists the whole video.
Target duration: 44-59 s (organic, no fixed timer).
"""

import json
import os
import random

# ---------------------------------------------------------------------------
# ASSET SYSTEM
# ---------------------------------------------------------------------------
import os as _os
ASSETS_DIR = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "assets")
USE_TEXTURES = True    # Set to False to use colored circles only

# ---------------------------------------------------------------------------
# THEME DATABASE  -  Loaded from external JSON file
# ---------------------------------------------------------------------------
THEMES_JSON_PATH = "themes.json"

def load_themes():
    """
    Load theme database from themes.json.
    
    Returns
    -------
    dict : {
        "POLITICS": [
            {"name": "Donald Trump", "search_query": "...", "color": [255, 0, 0]},
            ...
        ],
        ...
    }
    """
    if not os.path.exists(THEMES_JSON_PATH):
        print(f"  [config] WARNING: {THEMES_JSON_PATH} not found!")
        print(f"  [config] Using empty theme database.")
        return {}
    
    try:
        with open(THEMES_JSON_PATH, 'r', encoding='utf-8') as f:
            themes = json.load(f)
        
        print(f"  [config] Loaded {len(themes)} categories from {THEMES_JSON_PATH}")
        for cat, items in themes.items():
            print(f"    - {cat}: {len(items)} items")
        
        return themes
    
    except Exception as e:
        print(f"  [config] ERROR loading {THEMES_JSON_PATH}: {e}")
        return {}

# Load themes at startup
THEME_DATABASES = load_themes()

# Legacy TEAMS array for backward compatibility (fallback mode)
TEAMS = [
    {"name": "RED",   "color_idx": 0},
    {"name": "BLUE",  "color_idx": 1},
    {"name": "GREEN", "color_idx": 2},
]

# ---------------------------------------------------------------------------
# RENDER
# ---------------------------------------------------------------------------
WIDTH  = 720
HEIGHT = 1280
FPS    = 60

# Background color - NOW RANDOMIZED PER RUN (see main_automated.py)
# This is just the default for backwards compatibility
BG_COLOR = (
    random.randint(5, 50),   # R: Keep low for dark background
    random.randint(5, 50),   # G: Keep low for dark background
    random.randint(10, 60)   # B: Keep low for dark background
)

HEADLESS_MODE = False

# ---------------------------------------------------------------------------
# FACTORY
# ---------------------------------------------------------------------------
VIDEOS_PER_SESSION = 1
OUTPUT_DIR         = "C:/AI/StoryVideo/match_recordings"
VIDEO_CODEC        = "mp4v"


# ---------------------------------------------------------------------------
# TOURNAMENT SETTINGS (First to win the most out of 5 rounds)
# ---------------------------------------------------------------------------
TOTAL_ROUNDS = 5  # "Best of 5" format


# ---------------------------------------------------------------------------
# GAUNTLET TIMING - ZERO-WAIT FIX (Maximize retention)
# ---------------------------------------------------------------------------
HOOK_DURATION_FRAMES    = 0                # Video starts INSTANTLY with action
ENDCARD_DURATION_FRAMES = 90               # 1.5s end-card (reduced from 3s)
ROUND_FLASH_FRAMES      = int(FPS * 0.25)  # white flash between rounds

# ---------------------------------------------------------------------------
# AUTOMATED ROUND GENERATOR - SUDDEN DEATH MODE (No ties!)
# ---------------------------------------------------------------------------
ROUND_CONFIGS = []

for i in range(TOTAL_ROUNDS):
    ROUND_CONFIGS.append({
        "num_circles": 5 + i,           
        "gap_size": 75 - (i * 5),       
        "rotation_speed": 0.6 + (i * 0.1), 
        "num_balls": 2,                          
        "max_duration": 60,                      
        "pause_after": 0.7                       
    })
    
NUM_ROUNDS = len(ROUND_CONFIGS)

# ---------------------------------------------------------------------------
# PHYSICS
# ---------------------------------------------------------------------------
CIRCLE_HP              = 3
CIRCLE_THICKNESS_RATIO = 0.018
CIRCLE_SPACING_RATIO   = 0.014
BASE_RADIUS_RATIO      = 0.12
BALL_RADIUS_RATIO      = 0.022
BALL_SPEED_RATIO       = 0.0085
MAX_BALL_SPEED         = 25.0
COLLISION_PUSHBACK     = 4.0
COLLISION_COOLDOWN     = 6

# ---------------------------------------------------------------------------
# VISUAL
# ---------------------------------------------------------------------------
BLOOM_ENABLED        = True
BLOOM_SCALE          = 3
BLOOM_ITERATIONS     = 4
SHAKE_INTENSITY      = 0.4
SHAKE_DECAY          = 0.90
TRAIL_LENGTH         = 15
EXPLOSION_PARTICLES  = 60
CONFETTI_COUNT       = 200

# ---------------------------------------------------------------------------
# AUDIO
# ---------------------------------------------------------------------------
BASE_FREQUENCY   = 220
PENTATONIC_SCALE = [1.0, 1.125, 1.25, 1.5, 1.667]
SAMPLE_RATE      = 22050

# ---------------------------------------------------------------------------
# COLOURS
# ---------------------------------------------------------------------------
COLOR_PALETTE = [
    (255, 50, 50),    # 0 Red
    (50, 120, 255),   # 1 Blue
    (50, 255, 120),   # 2 Green
    (255, 220, 0),    # 3 Yellow
    (200, 50, 255),   # 4 Purple
    (255, 140, 0),    # 5 Orange
]

CIRCLE_COLORS = [
    (140, 70, 255), (110, 120, 255), (70, 150, 255), (20, 200, 230),
    (30, 210, 180), (50, 220, 110),  (250, 200, 20), (255, 130, 30),
]

HOOK_TEXTS = [
    "Who will win?",
    "Watch till the end!",
    "Can you predict this?",
    "The finale is INSANE",
    "Comment your pick!",
]