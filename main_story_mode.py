"""
main_story_mode.py - Story Mode Orchestrator (Production-Ready)

Fully autonomous two-part narrative video generation.
Integrates: story generation -> narration -> visuals -> gameplay -> composition -> publishing

PRODUCTION IMPROVEMENTS:
- Centralized configuration (no hardcoded paths)
- Proper error handling and logging
- Image safety validation
- Correct split-screen layout
- Clean architecture
"""

import os
import sys
import time
import random
from datetime import datetime
from pathlib import Path

# Use production config
from production_config import (
    OUTPUT_DIR, FPS, MARBLE_WIDTH, MARBLE_HEIGHT,
    OUTPUT_WIDTH, OUTPUT_HEIGHT, SPLIT_MODE,
    AUTO_UPLOAD, AUTO_TELEGRAM
)

# Import core infrastructure
from game_logic import Game
from effects import synthesise_wav
import cv2
import numpy as np

# Import story mode components
from story_generator import create_story_generator
from narration_engine import create_narration_engine
from story_visual_manager import create_visual_manager
from slideshow_generator import create_slideshow_generator
from video_compositor import create_compositor
from trend_selector import create_trend_selector
from subtitle_generator import create_subtitle_generator

# Import upload infrastructure if available
try:
    import metadata_generator
    import youtube_uploader
    _UPLOAD_AVAILABLE =  True
except ImportError:
    _UPLOAD_AVAILABLE = False
    print("  [story] Upload modules not available")

try:
    import telegram_pusher
    _TELEGRAM_AVAILABLE = True
except ImportError:
    _TELEGRAM_AVAILABLE = False


class StoryModeFactory:
    """
    Autonomous story mode video factory (Production-Ready).

    Generates two-part narrative videos with:
    - LLM-generated suspenseful stories (Ollama)
    - Natural TTS narration (espeak-ng or gTTS)
    - Atmospheric visual slideshow (DuckDuckGo + safety filters)
    - Synchronized marble race gameplay
    - Split-screen composition (marble race + story)
    - Optional automated publishing
    """

    def __init__(self):
        os.makedirs(OUTPUT_DIR, exist_ok=True)

        print("=" * 70)
        print("  STORY MODE FACTORY - Production-Ready")
        print("=" * 70)
        print(f"  Split-screen: {SPLIT_MODE} ({OUTPUT_WIDTH}x{OUTPUT_HEIGHT})")
        print(f"  Marble race: {MARBLE_WIDTH}x{MARBLE_HEIGHT}")
        print(f"  Story area: {MARBLE_WIDTH}x{MARBLE_HEIGHT}")
        print("=" * 70)

        # Initialize components with error handling
        try:
            self.story_gen = create_story_generator()
        except Exception as e:
            print(f"  [story] X Story generator failed: {e}")
            raise

        try:
            self.narration = create_narration_engine()
        except Exception as e:
            print(f"  [story] X Narration engine failed: {e}")
            raise

        try:
            self.visuals = create_visual_manager()
        except Exception as e:
            print(f"  [story] X Visual manager failed: {e}")
            raise

        try:
            self.slideshow = create_slideshow_generator()
        except Exception as e:
            print(f"  [story] X Slideshow generator failed: {e}")
            raise

        try:
            self.compositor = create_compositor()
        except Exception as e:
            print(f"  [story] X Compositor failed: {e}")
            raise

        try:
            self.trend_selector = create_trend_selector()
        except Exception as e:
            print(f"  [story] X Trend selector failed: {e}")
            raise

        try:
            self.subtitles = create_subtitle_generator()
        except Exception as e:
            print(f"  [story] X Subtitle generator failed: {e}")
            raise

        print(f"  Output directory: {OUTPUT_DIR}")
        print(f"  Auto-upload: {AUTO_UPLOAD and _UPLOAD_AVAILABLE}")
        print(f"  Telegram notify: {AUTO_TELEGRAM and _TELEGRAM_AVAILABLE}")
        print("=" * 70)
    
    def generate_story_video_pair(self):
        """Generate complete two-part story video series."""
        
        session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        print(f"\n{'=' * 70}")
        print(f"  SESSION: {session_id}")
        print(f"{'=' * 70}")
        
        try:
            # Step 1: Generate story
            story = self.story_gen.generate_two_part_story()
            
            # Step 2: Generate both parts
            part1_video = self._generate_story_part(
                story_data=story['part1'],
                part_number=1,
                session_id=session_id,
                topic=story['topic']
            )
            
            part2_video = self._generate_story_part(
                story_data=story['part2'],
                part_number=2,
                session_id=session_id,
                topic=story['topic']
            )
            
            # Step 3: Publish both parts
            # Run publishing if EITHER YouTube upload OR Telegram sync is enabled
            if (AUTO_UPLOAD and _UPLOAD_AVAILABLE) or (AUTO_TELEGRAM and _TELEGRAM_AVAILABLE):
                self._publish_video_pair(
                    part1_video,
                    part2_video,
                    story['topic'],
                    session_id
                )
            
            print(f"\n{'=' * 70}")
            print(f"  OK SESSION COMPLETE: {session_id}")
            print(f"{'=' * 70}")
            print(f"  Part 1: {part1_video}")
            print(f"  Part 2: {part2_video}")
            print(f"{'=' * 70}\n")
        
        except KeyboardInterrupt:
            print("\n  [story] Interrupted by user")
            raise
        
        except Exception as e:
            print(f"\n  [story] X Session failed: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    def _generate_story_part(
        self,
        story_data: dict,
        part_number: int,
        session_id: str,
        topic: str
    ) -> str:
        """Generate a single story part video."""
        
        print(f"\n{'-' * 70}")
        print(f"  PART {part_number} - {topic}")
        print(f"{'-' * 70}")
        
        script = story_data['script']
        visual_concepts = story_data['visual_concepts']
        
        part_id = f"{session_id}_part{part_number}"
        
        # Paths
        narration_path = os.path.join(OUTPUT_DIR, f"{part_id}_narration.wav")
        subtitle_path = os.path.join(OUTPUT_DIR, f"{part_id}_subtitles.ass")  # ASS format
        gameplay_path = os.path.join(OUTPUT_DIR, f"{part_id}_gameplay.mp4")
        slideshow_path = os.path.join(OUTPUT_DIR, f"{part_id}_slideshow.mp4")
        final_path = os.path.join(OUTPUT_DIR, f"{part_id}_final.mp4")
        
        # Step 1: Generate narration (source of truth for timing)
        print(f"\n[1/6] Generating narration...")
        narration_duration = self.narration.generate_narration(script, narration_path)

        # === PADDING LOGIC: Ensure minimum 61 seconds ===
        MIN_DURATION = 61.0
        video_duration = narration_duration

        if narration_duration < MIN_DURATION:
            padding_needed = MIN_DURATION - narration_duration
            video_duration = MIN_DURATION
            print(f"  [padding] Narration is {narration_duration:.1f}s, padding to {MIN_DURATION:.1f}s (+{padding_needed:.1f}s)")
            print(f"  [padding] Adding silence to audio and extending marble race...")

            # Add silence to the end of the narration audio
            self._pad_audio_with_silence(narration_path, padding_needed)
            print(f"  [padding] Audio padded with {padding_needed:.1f}s of silence")

        # Step 2: Generate TikTok-style subtitles
        print(f"\n[2/6] Generating TikTok-style subtitles...")
        self.subtitles.generate_subtitles(
            script=script,
            duration=narration_duration,  # Subtitles match narration, not padding
            output_path=subtitle_path,
            style="tiktok"
        )

        # Step 3: Fetch story images
        print(f"\n[3/6] Fetching story imagery...")
        image_paths = self.visuals.fetch_story_images(visual_concepts, part_id)

        # Step 4: Render gameplay (use padded duration)
        print(f"\n[4/6] Rendering gameplay ({video_duration:.1f}s)...")
        self._render_gameplay(video_duration, gameplay_path)

        # Step 5: Create slideshow (use padded duration, will hold last image)
        print(f"\n[5/6] Creating slideshow...")
        self.slideshow.generate_slideshow(image_paths, video_duration, slideshow_path)

        # Step 6: Compose final video with subtitles
        print(f"\n[6/6] Composing final video with TikTok subtitles...")
        self.compositor.compose_split_screen(
            gameplay_path,
            slideshow_path,
            narration_path,
            final_path,
            subtitle_file=subtitle_path
        )
        
        # Cleanup intermediate files
        for temp_file in [narration_path, subtitle_path, gameplay_path, slideshow_path]:
            if os.path.exists(temp_file):
                os.remove(temp_file)
        
        # Validate final video
        if not os.path.exists(final_path):
            raise RuntimeError(f"Final video not created: {final_path}")
        
        file_size_mb = os.path.getsize(final_path) / (1024 * 1024)
        print(f"\n  OK Part {part_number} complete: {file_size_mb:.1f} MB")
        
        return final_path
    
    def _pad_audio_with_silence(self, audio_path: str, silence_duration: float):
        """
        Add silence to the end of an audio file using FFmpeg.

        Parameters
        ----------
        audio_path : str
            Path to the audio file to pad (will be overwritten)
        silence_duration : float
            Duration of silence to add in seconds
        """
        import subprocess

        # Create temp file for padded audio
        temp_output = audio_path + ".temp.wav"

        # Use FFmpeg to add silence:
        # 1. Read original audio
        # 2. Generate silence with anullsrc
        # 3. Concatenate them
        cmd = [
            'ffmpeg', '-y',
            '-i', audio_path,
            '-f', 'lavfi',
            '-t', str(silence_duration),
            '-i', 'anullsrc=channel_layout=mono:sample_rate=24000',
            '-filter_complex', '[0:a][1:a]concat=n=2:v=0:a=1',
            '-ar', '24000',
            '-ac', '1',
            temp_output
        ]

        try:
            subprocess.run(cmd, check=True, capture_output=True)

            # Replace original with padded version
            os.replace(temp_output, audio_path)

        except subprocess.CalledProcessError as e:
            print(f"  [padding] ERROR padding audio: {e.stderr.decode()}")
            # Clean up temp file if it exists
            if os.path.exists(temp_output):
                os.remove(temp_output)
            raise

    def _render_gameplay(self, target_duration: float, output_path: str):
        """
        Render marble race gameplay with TRENDING RIVALS.
        Uses trend selector to get actual rivals instead of generic colors.
        """

        seed = random.randint(100000, 999999)

        # Random background color (dark atmospheric)
        bg_color = (
            random.randint(5, 25),    # R: Low
            random.randint(5, 20),    # G: Very low
            random.randint(30, 60)    # B: Higher (blue tint)
        )

        # SELECT TRENDING RIVALS
        theme_name, rivals = self.trend_selector.select_trending_rivals(count=2)

        # Create game instance with TRENDING RIVALS
        game = Game(
            MARBLE_WIDTH,
            MARBLE_HEIGHT,
            seed,
            theme_name=theme_name,
            rivals=rivals,
            bg_color=bg_color
        )

        # Calculate target frames
        target_frames = int(target_duration * FPS)

        # Setup video writer
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        writer = cv2.VideoWriter(
            output_path,
            fourcc,
            FPS,
            (MARBLE_WIDTH, MARBLE_HEIGHT)
        )

        if not writer.isOpened():
            raise RuntimeError(f"Failed to open video writer: {output_path}")

        frame_count = 0

        print(f"    Rendering marble race: {target_duration:.1f}s ({target_frames} frames)")

        while frame_count < target_frames:
            # Render frame
            frame = np.zeros((MARBLE_HEIGHT, MARBLE_WIDTH, 3), dtype=np.uint8)

            if not game.is_done():
                game.update()
                game.draw(frame)
            else:
                # Game ended early - keep rendering last state with animation
                game.background.update()
                game.background.draw(frame)
                game.particles.update()
                game.particles.draw(frame)

            writer.write(frame)
            frame_count += 1

            # Progress indicator
            if frame_count % (FPS * 5) == 0:
                progress = (frame_count / target_frames) * 100
                print(f"    Progress: {progress:.0f}%", end='\r')

        writer.release()
        print(f"    Progress: 100% OK")
    
    def _publish_video_pair(
        self,
        part1_path: str,
        part2_path: str,
        topic: str,
        session_id: str
    ):
        """
        Publish workflow:
        - YouTube: Upload ONLY Part 1 automatically
        - Part 2: Save metadata to file, DON'T upload
        - TikTok: Send both videos + metadata file to P-Cloud via Telegram
        """

        print(f"\n{'=' * 70}")
        print(f"  PUBLISHING")
        print(f"{'=' * 70}")

        # Generate metadata for both parts
        metadata_part1 = self._generate_metadata(topic, 1)
        metadata_part2 = self._generate_metadata(topic, 2)

        # === YOUTUBE: Upload ONLY Part 1 (if enabled) ===
        if AUTO_UPLOAD and _UPLOAD_AVAILABLE:
            print(f"\n  [YouTube] Uploading Part 1 ONLY...")
            result1 = youtube_uploader.upload(part1_path, metadata_part1.get("youtube", {}))
            if result1:
                print(f"  ✅ Part 1 uploaded: {result1['url']}")
        else:
            print(f"\n  [YouTube] Upload disabled (AUTO_UPLOAD={AUTO_UPLOAD}, Available={_UPLOAD_AVAILABLE})")

        # === PART 2: Save metadata to file (DON'T upload) ===
        print(f"\n  [YouTube] Part 2: Saving metadata to file (NOT uploading)...")
        metadata_file = self._save_metadata_to_file(metadata_part2, session_id)
        print(f"  ✅ Part 2 metadata saved: {metadata_file}")

        # === TIKTOK: Send both videos + metadata to P-Cloud via Telegram ===
        if AUTO_TELEGRAM and _TELEGRAM_AVAILABLE:
            print(f"\n  [TikTok/Telegram] Syncing videos to P-Cloud...")
            telegram_pusher.sync_videos_and_notify(
                part1_path=part1_path,
                part2_path=part2_path,
                metadata_file=metadata_file,
                metadata_part1=metadata_part1,
                metadata_part2=metadata_part2
            )

    def _save_metadata_to_file(self, metadata: dict, session_id: str) -> str:
        """Save Part 2 metadata to a text file for manual upload."""

        metadata_filename = f"part2_metadata_{session_id}.txt"
        metadata_path = os.path.join(OUTPUT_DIR, metadata_filename)

        yt = metadata.get("youtube", {})
        tt = metadata.get("tiktok", {})

        content = "=" * 70 + "\n"
        content += "  PART 2 METADATA - YouTube Shorts\n"
        content += "=" * 70 + "\n\n"

        content += "TITLE:\n"
        content += f"{yt.get('title', 'N/A')}\n\n"

        content += "=" * 70 + "\n"
        content += "DESCRIPTION:\n"
        content += "=" * 70 + "\n"
        content += f"{yt.get('description', 'N/A')}\n\n"

        content += "=" * 70 + "\n"
        content += "TAGS:\n"
        content += "=" * 70 + "\n"
        tags = yt.get('tags', [])
        content += ", ".join(tags) + "\n\n"

        content += "=" * 70 + "\n"
        content += "  TikTok Metadata (Reference)\n"
        content += "=" * 70 + "\n\n"

        content += "CAPTION:\n"
        content += f"{tt.get('caption', 'N/A')}\n\n"

        content += "HASHTAGS:\n"
        content += " ".join(tt.get('hashtags', [])) + "\n\n"

        content += "=" * 70 + "\n"
        content += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        content += "=" * 70 + "\n"

        with open(metadata_path, 'w', encoding='utf-8') as f:
            f.write(content)

        return metadata_path
    
    def _generate_metadata(self, topic: str, part_number: int) -> dict:
        """Generate optimized metadata for story video."""
        
        # Capitalize topic
        topic_title = " ".join(word.capitalize() for word in topic.split())
        
        if part_number == 1:
            youtube_title = f"The {topic_title} Mystery - Part 1 🔍"
            youtube_desc = f"""Something strange happened. But the truth is more unsettling than anyone expected.

This is Part 1 of a 2-part mystery. Watch until the end to discover what really happened.

WARN️ Part 2 reveals everything.

#mystery #scary #storytelling #unexplained #creepy #horror #shorts #fyp"""
            
            tiktok_caption = f"""The {topic_title} Mystery - Part 1 WARN️

Something happened that nobody can explain. Part 2 reveals the truth.

Watch Part 2 to find out what really happened 👀"""
        
        else:
            youtube_title = f"The {topic_title} Mystery - Part 2 (The Truth) 😱"
            youtube_desc = f"""The truth about the {topic} is finally revealed.

If you haven't watched Part 1, go watch it now. This is the resolution you've been waiting for.

#mystery #scary #storytelling #unexplained #creepy #horror #shorts #fyp #revealed"""
            
            tiktok_caption = f"""The {topic_title} Mystery - Part 2 (REVEALED) 😱

The truth is more disturbing than anyone expected.

Make sure you watched Part 1 first! 👀"""
        
        return {
            "youtube": {
                "title": youtube_title[:100],
                "description": youtube_desc[:5000],
                "tags": [
                    "mystery", "scary", "horror", "storytelling",
                    "unexplained", "creepy", "shorts", "viral",
                    topic.replace(" ", "")
                ]
            },
            "tiktok": {
                "caption": tiktok_caption,
                "hashtags": [
                    "#mystery", "#scary", "#horror",
                    "#storytelling", "#viral", "#fyp"
                ]
            }
        }


def main():
    """Entry point for story mode."""
    
    factory = StoryModeFactory()
    
    try:
        factory.generate_story_video_pair()
    
    except KeyboardInterrupt:
        print("\n\n  [story] Stopped by user")
        sys.exit(0)
    
    except Exception as e:
        print(f"\n\n  [story] X Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
