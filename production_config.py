"""
production_config.py - Centralized Production Configuration

All paths, settings, and constants in one place.
No hardcoding across the codebase.
"""

import os
from pathlib import Path

# ============================================================================
# PATHS (Auto-detect project root)
# ============================================================================
PROJECT_ROOT = Path(__file__).parent.absolute()

# Output directories
OUTPUT_DIR = PROJECT_ROOT / "match_recordings"
STORY_ASSETS_DIR = PROJECT_ROOT / "story_assets"
STORY_TEMP_DIR = PROJECT_ROOT / "story_temp"

# Ensure directories exist
OUTPUT_DIR.mkdir(exist_ok=True)
STORY_ASSETS_DIR.mkdir(exist_ok=True)
STORY_TEMP_DIR.mkdir(exist_ok=True)

# Data files
THEMES_JSON_PATH = PROJECT_ROOT / "themes.json"
PLAYED_MATCHES_PATH = PROJECT_ROOT / "played_matches.json"
LLM_CACHE_PATH = PROJECT_ROOT / "llm_query_cache.json"
YOUTUBE_UPLOADS_PATH = PROJECT_ROOT / "youtube_uploads.json"

# ============================================================================
# VIDEO OUTPUT SETTINGS
# ============================================================================
# Split-screen layout: Marble race + Story slideshow
OUTPUT_WIDTH = 1080    # TikTok vertical format
OUTPUT_HEIGHT = 1920

# Split screen halves (side-by-side OR top-bottom)
SPLIT_MODE = "vertical"  # "vertical" = top/bottom, "horizontal" = side-by-side

if SPLIT_MODE == "vertical":
    # Vertical split (top/bottom)
    MARBLE_WIDTH = OUTPUT_WIDTH
    MARBLE_HEIGHT = OUTPUT_HEIGHT // 2
    STORY_WIDTH = OUTPUT_WIDTH
    STORY_HEIGHT = OUTPUT_HEIGHT // 2
else:
    # Horizontal split (side-by-side)
    MARBLE_WIDTH = OUTPUT_WIDTH // 2
    MARBLE_HEIGHT = OUTPUT_HEIGHT
    STORY_WIDTH = OUTPUT_WIDTH // 2
    STORY_HEIGHT = OUTPUT_HEIGHT

FPS = 30
VIDEO_CODEC = "mp4v"

# ============================================================================
# MARBLE RACE GAME SETTINGS
# ============================================================================
# Physics
CIRCLE_HP = 3
CIRCLE_THICKNESS_RATIO = 0.018
CIRCLE_SPACING_RATIO = 0.014
BASE_RADIUS_RATIO = 0.12
BALL_RADIUS_RATIO = 0.022
BALL_SPEED_RATIO = 0.0085
MAX_BALL_SPEED = 25.0
COLLISION_PUSHBACK = 4.0
COLLISION_COOLDOWN = 6

# Visual effects
BLOOM_ENABLED = True
BLOOM_SCALE = 3
BLOOM_ITERATIONS = 2  # Reduced from 4 to make rival icons more visible
SHAKE_INTENSITY = 0.4
SHAKE_DECAY = 0.90
TRAIL_LENGTH = 15
EXPLOSION_PARTICLES = 60
CONFETTI_COUNT = 200

# Audio
BASE_FREQUENCY = 220
PENTATONIC_SCALE = [1.0, 1.125, 1.25, 1.5, 1.667]
SAMPLE_RATE = 22050

# Colors
COLOR_PALETTE = [
    (255, 50, 50),    # Red
    (50, 120, 255),   # Blue
    (50, 255, 120),   # Green
    (255, 220, 0),    # Yellow
    (200, 50, 255),   # Purple
    (255, 140, 0),    # Orange
]

CIRCLE_COLORS = [
    (140, 70, 255), (110, 120, 255), (70, 150, 255), (20, 200, 230),
    (30, 210, 180), (50, 220, 110), (250, 200, 20), (255, 130, 30),
]

# Rounds configuration
TOTAL_ROUNDS = 5
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

# Timing
HOOK_DURATION_FRAMES = 0
ENDCARD_DURATION_FRAMES = 90
ROUND_FLASH_FRAMES = int(FPS * 0.25)

HOOK_TEXTS = [
    "Who will win?",
    "Watch till the end!",
    "Can you predict this?",
    "The finale is INSANE",
    "Comment your pick!",
]

# ============================================================================
# STORY MODE SETTINGS
# ============================================================================
# LLM (Ollama)
OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_MODEL = "llama3.1:latest"
OLLAMA_TIMEOUT = 120

# Story generation
STORY_MIN_WORDS = 130
STORY_TARGET_WORDS = 180
STORY_MAX_WORDS = 350  # Increased to allow longer resolutions
STORY_MIN_VISUAL_CONCEPTS = 4
STORY_TARGET_VISUAL_CONCEPTS = 7

# Narration (TTS)
NARRATION_MIN_DURATION = 65  # seconds (YouTube monetization minimum)
NARRATION_MAX_DURATION = 90

# Image fetching
IMAGE_MIN_COUNT = 4
IMAGE_TARGET_COUNT = 7
IMAGE_MAX_COUNT = 10
IMAGE_SEARCH_MAX_ATTEMPTS = 25
IMAGE_SEARCH_MAX_PER_CONCEPT = 4

# Human-like delays (anti-bot protection)
DELAY_BEFORE_SEARCH = (2.5, 6.5)
DELAY_BETWEEN_DOWNLOADS = (0.8, 2.2)
DELAY_AFTER_PART = (6.0, 12.0)
DELAY_JITTER = 0.2

# Image quality filters
IMAGE_MIN_WIDTH = 400
IMAGE_MIN_HEIGHT = 300
IMAGE_MIN_ASPECT = 0.5
IMAGE_MAX_ASPECT = 3.0

# ============================================================================
# UPLOAD & PUBLISHING
# ============================================================================
AUTO_UPLOAD =  False  # Set to True to enable automatic YouTube upload
AUTO_TELEGRAM = True # False  # Set to True to enable Telegram notifications

# ============================================================================
# SAFETY & MODERATION
# ============================================================================
# Image content filtering
BANNED_KEYWORDS = [
    "gore", "blood", "violence", "weapon", "gun", "knife",
    "nude", "naked", "porn", "sex", "explicit",
    "hate", "racist", "nazi", "offensive"
]

# Safe search modifiers
SAFE_SEARCH_MODIFIERS = [
    "safe for work",
    "family friendly",
    "clean",
    "appropriate"
]

# ============================================================================
# LEGACY COMPATIBILITY (for old files)
# ============================================================================
WIDTH = MARBLE_WIDTH
HEIGHT = MARBLE_HEIGHT
NUM_ROUNDS = len(ROUND_CONFIGS)
BG_COLOR = (15, 10, 40)  # Default dark blue background
HEADLESS_MODE = False
VIDEOS_PER_SESSION = 1

# Theme system (legacy)
TEAMS = [
    {"name": "RED", "color_idx": 0},
    {"name": "BLUE", "color_idx": 1},
    {"name": "GREEN", "color_idx": 2},
]

# Convert Path objects to strings for compatibility
OUTPUT_DIR = str(OUTPUT_DIR)
STORY_ASSETS_DIR = str(STORY_ASSETS_DIR)
STORY_TEMP_DIR = str(STORY_TEMP_DIR)
THEMES_JSON_PATH = str(THEMES_JSON_PATH)
