"""
organize_codebase.py - Codebase Reorganization Script

Reorganizes the StoryVideo codebase into a clean, professional structure:

FOLDER STRUCTURE:
/core/          - Core marble race game engine
/story/         - Story generation and narration
/video/         - Video processing and composition
/assets/        - Asset management (textures, trends)
/upload/        - Publishing and distribution
/config/        - Configuration files
/utils/         - Utility functions
"""

import os
import shutil
from pathlib import Path

# Project root
ROOT = Path(__file__).parent

# Define new folder structure
FOLDERS = {
    'core': [
        'game_logic.py',
        'physics.py',
        'effects.py',
        'background.py',
    ],
    'story': [
        'story_generator.py',
        'narration_engine.py',
        'story_visual_manager.py',
    ],
    'video': [
        'video_compositor.py',
        'slideshow_generator.py',
        'subtitle_generator.py',
    ],
    'assets': [
        'texture_manager.py',
        'trend_selector.py',
    ],
    'upload': [
        'youtube_uploader.py',
        'telegram_pusher.py',
        'metadata_generator.py',
    ],
    'config': [
        'production_config.py',
        'config.py',
        'themes.json',
    ],
}

# Files to keep in root
ROOT_FILES = [
    'main_story_mode.py',
    'main.py',
    'organize_codebase.py',
    'test_production_ready.py',
    'README.md',
    'requirements.txt',
]


def create_folders():
    """Create folder structure."""
    print("=" * 70)
    print("  CREATING FOLDER STRUCTURE")
    print("=" * 70)

    for folder in FOLDERS.keys():
        folder_path = ROOT / folder
        folder_path.mkdir(exist_ok=True)
        print(f"  [OK] Created: {folder}/")

        # Create __init__.py for Python packages
        init_file = folder_path / "__init__.py"
        if not init_file.exists():
            init_file.write_text("")
            print(f"  [OK] Created: {folder}/__init__.py")


def move_files():
    """Move files to their designated folders."""
    print("\n" + "=" * 70)
    print("  MOVING FILES")
    print("=" * 70)

    moved_count = 0

    for folder, files in FOLDERS.items():
        for filename in files:
            source = ROOT / filename
            destination = ROOT / folder / filename

            if source.exists():
                try:
                    shutil.move(str(source), str(destination))
                    print(f"  [OK] Moved: {filename} -> {folder}/")
                    moved_count += 1
                except Exception as e:
                    print(f"  [WARN] Failed to move {filename}: {e}")
            else:
                print(f"  [SKIP] Not found: {filename}")

    print(f"\n  Total files moved: {moved_count}")


def update_imports_in_file(file_path: Path):
    """Update import statements in a Python file."""

    try:
        content = file_path.read_text(encoding='utf-8')
        original_content = content

        # Map of old imports to new imports
        import_mappings = {
            'from game_logic import': 'from core.game_logic import',
            'from physics import': 'from core.physics import',
            'from effects import': 'from core.effects import',
            'from background import': 'from core.background import',
            'from story_generator import': 'from story.story_generator import',
            'from narration_engine import': 'from story.narration_engine import',
            'from story_visual_manager import': 'from story.story_visual_manager import',
            'from video_compositor import': 'from video.video_compositor import',
            'from slideshow_generator import': 'from video.slideshow_generator import',
            'from subtitle_generator import': 'from video.subtitle_generator import',
            'from texture_manager import': 'from assets.texture_manager import',
            'from trend_selector import': 'from assets.trend_selector import',
            'from production_config import': 'from config.production_config import',
            'from config import': 'from config.config import',
            'import youtube_uploader': 'from upload import youtube_uploader',
            'import telegram_pusher': 'from upload import telegram_pusher',
            'import metadata_generator': 'from upload import metadata_generator',
        }

        # Apply import mappings
        for old_import, new_import in import_mappings.items():
            if old_import in content:
                content = content.replace(old_import, new_import)

        # Only write if changed
        if content != original_content:
            file_path.write_text(content, encoding='utf-8')
            return True

        return False

    except Exception as e:
        print(f"  [WARN] Error updating {file_path.name}: {e}")
        return False


def update_all_imports():
    """Update imports in all Python files."""
    print("\n" + "=" * 70)
    print("  UPDATING IMPORT STATEMENTS")
    print("=" * 70)

    updated_count = 0

    # Update root files
    for filename in ROOT_FILES:
        file_path = ROOT / filename
        if file_path.exists() and file_path.suffix == '.py':
            if update_imports_in_file(file_path):
                print(f"  [OK] Updated imports: {filename}")
                updated_count += 1

    # Update files in folders
    for folder in FOLDERS.keys():
        folder_path = ROOT / folder
        for file_path in folder_path.glob('*.py'):
            if file_path.name != '__init__.py':
                if update_imports_in_file(file_path):
                    print(f"  [OK] Updated imports: {folder}/{file_path.name}")
                    updated_count += 1

    print(f"\n  Total files updated: {updated_count}")


def create_summary():
    """Create organization summary."""
    print("\n" + "=" * 70)
    print("  ORGANIZATION COMPLETE")
    print("=" * 70)

    print("\nNEW STRUCTURE:")
    print("  /core/           - Game engine (marble race)")
    print("  /story/          - Story generation & narration")
    print("  /video/          - Video processing & subtitles")
    print("  /assets/         - Textures & trending rivals")
    print("  /upload/         - YouTube & Telegram publishing")
    print("  /config/         - Configuration files")

    print("\nMAIN ENTRY POINTS:")
    print("  main_story_mode.py    - Story mode video generation")
    print("  main.py               - Standard marble race")
    print("  test_production_ready.py - System validation")

    print("\n" + "=" * 70)


def main():
    """Run complete reorganization."""
    print("=" * 70)
    print("  CODEBASE REORGANIZATION")
    print("=" * 70)
    print("\nThis will reorganize the codebase into a professional structure.")
    print("All import statements will be automatically updated.")

    response = input("\nProceed? (yes/no): ").strip().lower()

    if response != 'yes':
        print("\n  [CANCELLED] Reorganization cancelled.")
        return

    try:
        create_folders()
        move_files()
        update_all_imports()
        create_summary()

        print("\n  [SUCCESS] Codebase reorganization complete!")
        print("  You can now run: python main_story_mode.py")

    except Exception as e:
        print(f"\n  [ERROR] Reorganization failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
