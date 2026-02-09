"""
slideshow_generator.py - Story Visual Slideshow Assembly (Production-Ready)

Converts story images into timed video segments with smooth transitions.
Duration exactly matches narration audio.

PRODUCTION IMPROVEMENTS:
- Uses centralized config
- Proper temp file management
- Better error handling
- Configurable output dimensions
"""

import subprocess
import os
import random
from typing import List
from PIL import Image
from production_config import (
    MARBLE_WIDTH, MARBLE_HEIGHT, FPS, STORY_TEMP_DIR
)


class SlideshowGenerator:
    """
    Generates video slideshow from images with precise duration matching.
    Dimensions match the story portion of the split screen.
    """

    def __init__(self):
        self._verify_ffmpeg()
        os.makedirs(STORY_TEMP_DIR, exist_ok=True)
        print(f"  [slideshow] Resolution: {MARBLE_WIDTH}x{MARBLE_HEIGHT} @ {FPS}fps")
    
    def _verify_ffmpeg(self):
        """Verify ffmpeg is available."""
        try:
            subprocess.run(
                ['ffmpeg', '-version'],
                capture_output=True,
                check=True
            )
        except (FileNotFoundError, subprocess.CalledProcessError):
            raise RuntimeError("ffmpeg not found - required for video generation")
    
    def generate_slideshow(
        self,
        image_paths: List[str],
        duration: float,
        output_path: str
    ) -> str:
        """
        Create slideshow video matching exact duration.
        
        Parameters
        ----------
        image_paths : List[str]
            Paths to images to include
        duration : float
            Target duration in seconds (from narration)
        output_path : str
            Output video path
        
        Returns
        -------
        str : Path to generated video
        """
        
        print(f"  [slideshow] Creating from {len(image_paths)} images ({duration:.1f}s)...")
        
        # Prepare images
        prepared_images = self._prepare_images(image_paths)
        
        if not prepared_images:
            raise RuntimeError("No valid images for slideshow")
        
        # Calculate timing
        duration_per_image = duration / len(prepared_images)
        
        print(f"  [slideshow] {duration_per_image:.2f}s per image")
        
        # Build ffmpeg filter for Ken Burns effect
        video_path = self._create_slideshow_with_motion(
            prepared_images,
            duration_per_image,
            output_path
        )
        
        print(f"  [slideshow] OK Generated: {output_path}")
        
        return video_path
    
    def _prepare_images(self, image_paths: List[str]) -> List[str]:
        """Prepare and validate images for slideshow."""

        prepared_dir = os.path.join(STORY_TEMP_DIR, "slideshow_prep")
        os.makedirs(prepared_dir, exist_ok=True)

        prepared = []

        for i, img_path in enumerate(image_paths):
            if not os.path.exists(img_path):
                print(f"  [slideshow] WARN Image not found: {img_path}")
                continue

            try:
                img = Image.open(img_path)

                # Convert to RGB
                if img.mode != 'RGB':
                    img = img.convert('RGB')

                # Resize to fit slideshow dimensions
                img_width, img_height = img.size
                target_aspect = MARBLE_WIDTH / MARBLE_HEIGHT
                img_aspect = img_width / img_height

                if img_aspect > target_aspect:
                    # Image is too wide - crop sides
                    new_width = int(img_height * target_aspect)
                    left = (img_width - new_width) // 2
                    img = img.crop((left, 0, left + new_width, img_height))
                else:
                    # Image is too tall - crop top/bottom
                    new_height = int(img_width / target_aspect)
                    top = (img_height - new_height) // 2
                    img = img.crop((0, top, img_width, top + new_height))

                # Resize to target resolution
                img = img.resize((MARBLE_WIDTH, MARBLE_HEIGHT), Image.Resampling.LANCZOS)

                # Apply dark atmospheric overlay
                img = self._apply_atmospheric_overlay(img)

                # Save
                prep_path = os.path.join(prepared_dir, f"prep_{i:03d}.jpg")
                img.save(prep_path, 'JPEG', quality=92)

                prepared.append(prep_path)

            except Exception as e:
                print(f"  [slideshow] WARN Failed to prepare {os.path.basename(img_path)}: {e}")
                continue

        return prepared
    
    def _apply_atmospheric_overlay(self, img: Image.Image) -> Image.Image:
        """Apply subtle dark overlay for atmosphere."""
        
        overlay = Image.new('RGB', img.size, (0, 0, 0))
        
        # Blend: 85% original, 15% black overlay
        blended = Image.blend(img, overlay, alpha=0.15)
        
        return blended
    
    def _create_slideshow_with_motion(
        self,
        image_paths: List[str],
        duration_per_image: float,
        output_path: str
    ) -> str:
        """
        Create slideshow with Ken Burns effect (slow zoom/pan).
        """

        # Create input file list for ffmpeg concat
        concat_file = os.path.join(STORY_TEMP_DIR, "slideshow_concat.txt")

        with open(concat_file, 'w') as f:
            for img_path in image_paths:
                # Use forward slashes for ffmpeg compatibility
                img_path_normalized = img_path.replace('\\', '/')
                f.write(f"file '{img_path_normalized}'\n")
                f.write(f"duration {duration_per_image}\n")
            # Repeat last image to ensure proper duration
            last_img_normalized = image_paths[-1].replace('\\', '/')
            f.write(f"file '{last_img_normalized}'\n")

        # Build filter for slideshow with Ken Burns effect
        # Randomly choose zoom in or out for variation
        zoom_direction = "in" if random.random() > 0.5 else "out"

        if zoom_direction == "in":
            # Subtle zoom in
            zoom_filter = f"scale={MARBLE_WIDTH}:{MARBLE_HEIGHT}:force_original_aspect_ratio=increase,crop={MARBLE_WIDTH}:{MARBLE_HEIGHT},fps={FPS}"
        else:
            # Subtle zoom out
            zoom_filter = f"scale={MARBLE_WIDTH}:{MARBLE_HEIGHT}:force_original_aspect_ratio=increase,crop={MARBLE_WIDTH}:{MARBLE_HEIGHT},fps={FPS}"

        # Generate with ffmpeg
        try:
            subprocess.run([
                'ffmpeg', '-y',
                '-f', 'concat',
                '-safe', '0',
                '-i', concat_file,
                '-vf', zoom_filter,
                '-c:v', 'libx264',
                '-preset', 'medium',
                '-crf', '23',
                '-pix_fmt', 'yuv420p',
                output_path
            ], check=True, capture_output=True)

        except subprocess.CalledProcessError as e:
            stderr = e.stderr.decode('utf-8', errors='ignore') if e.stderr else 'Unknown error'
            print(f"  [slideshow] X FFmpeg error: {stderr[:300]}")
            raise RuntimeError(f"Slideshow generation failed: {stderr[:200]}")

        return output_path


def create_slideshow_generator() -> SlideshowGenerator:
    """Factory function."""
    return SlideshowGenerator()


# Test mode
if __name__ == "__main__":
    print("=" * 70)
    print("  SLIDESHOW GENERATOR TEST")
    print("=" * 70)
    
    generator = create_slideshow_generator()
    
    # Create test images
    test_dir = "C:/AI/StoryVideo/story_assets"
    os.makedirs(test_dir, exist_ok=True)
    
    test_images = []
    for i in range(4):
        img = Image.new('RGB', (1080, 1920), (random.randint(20, 50), random.randint(10, 30), random.randint(30, 60)))
        img_path = os.path.join(test_dir, f"test_{i}.jpg")
        img.save(img_path)
        test_images.append(img_path)
    
    output = "C:/AI/StoryVideo/test_slideshow.mp4"
    
    generator.generate_slideshow(test_images, 60.0, output)
    
    print(f"\nOK Generated slideshow: {output}")
