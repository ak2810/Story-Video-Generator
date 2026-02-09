"""
video_compositor.py - Split-Screen Video Assembly (Production-Ready)

Merges marble race gameplay and story slideshow into single vertical video.
Ensures perfect synchronization and exact duration matching.

PRODUCTION IMPROVEMENTS:
- Uses centralized config (no hardcoded dimensions)
- Configurable split mode (vertical/horizontal)
- Better error handling
- Proper resource cleanup
"""

import subprocess
import os
from production_config import (
    OUTPUT_WIDTH, OUTPUT_HEIGHT, SPLIT_MODE,
    MARBLE_WIDTH, MARBLE_HEIGHT, FPS
)


class VideoCompositor:
    """
    Combines marble race gameplay and story slideshow into split-screen video.

    Layout options:
    - Vertical split: Story (top) + Marble race (bottom)
    - Horizontal split: Story (left) + Marble race (right)
    """

    def __init__(self):
        self._verify_ffmpeg()
        print(f"  [compositor] Layout: {SPLIT_MODE}")
        print(f"  [compositor] Output: {OUTPUT_WIDTH}x{OUTPUT_HEIGHT} @ {FPS}fps")
    
    def _verify_ffmpeg(self):
        """Verify ffmpeg is available."""
        try:
            subprocess.run(
                ['ffmpeg', '-version'],
                capture_output=True,
                check=True
            )
        except (FileNotFoundError, subprocess.CalledProcessError):
            raise RuntimeError("ffmpeg not found")
    
    def compose_split_screen(
        self,
        gameplay_video: str,
        slideshow_video: str,
        narration_audio: str,
        output_path: str,
        subtitle_file: str = None
    ) -> str:
        """
        Create split-screen video with synchronized audio.

        Layout (vertical split):
        ┌--------------┐
        |  Slideshow   | <- Story visuals (top half)
        ├--------------┤
        | Marble Race  | <- Game motion (bottom half)
        └--------------┘

        Parameters
        ----------
        gameplay_video : str
            Path to marble race gameplay video
        slideshow_video : str
            Path to story slideshow video
        narration_audio : str
            Path to narration WAV audio
        output_path : str
            Output video path

        Returns
        -------
        str : Path to final composed video
        """

        print(f"  [compositor] Composing split-screen ({SPLIT_MODE})...")
        
        # Verify inputs exist
        for path, name in [
            (gameplay_video, "gameplay"),
            (slideshow_video, "slideshow"),
            (narration_audio, "narration")
        ]:
            if not os.path.exists(path):
                raise RuntimeError(f"Missing {name}: {path}")
        
        # Get audio duration (source of truth)
        audio_duration = self._get_duration(narration_audio)
        
        print(f"  [compositor] Target duration: {audio_duration:.2f}s")
        
        # Ensure both videos match duration
        gameplay_trimmed = self._trim_video(gameplay_video, audio_duration)
        slideshow_trimmed = self._trim_video(slideshow_video, audio_duration)
        
        # Compose split screen
        temp_video = output_path.replace('.mp4', '_temp.mp4')
        
        self._merge_split_screen(
            slideshow_trimmed,
            gameplay_trimmed,
            temp_video
        )
        
        # Add narration audio and subtitles
        self._add_audio_and_subtitles(temp_video, narration_audio, subtitle_file, output_path)
        
        # Cleanup temp files
        for temp in [temp_video, gameplay_trimmed, slideshow_trimmed]:
            if os.path.exists(temp) and temp != gameplay_video and temp != slideshow_video:
                os.remove(temp)
        
        print(f"  [compositor] OK Final video: {output_path}")
        
        return output_path
    
    def _get_duration(self, media_path: str) -> float:
        """Get media duration in seconds."""
        
        try:
            result = subprocess.run([
                'ffprobe',
                '-v', 'error',
                '-show_entries', 'format=duration',
                '-of', 'default=noprint_wrappers=1:nokey=1',
                media_path
            ], capture_output=True, text=True, check=True)
            
            return float(result.stdout.strip())
        
        except Exception as e:
            print(f"  [compositor] WARN Duration check failed: {e}")
            return 60.0  # Fallback
    
    def _trim_video(self, video_path: str, target_duration: float) -> str:
        """Trim video to exact duration."""
        
        current_duration = self._get_duration(video_path)
        
        # If already correct duration (within 0.1s), return original
        if abs(current_duration - target_duration) < 0.1:
            return video_path
        
        output = video_path.replace('.mp4', '_trimmed.mp4')
        
        try:
            subprocess.run([
                'ffmpeg', '-y',
                '-i', video_path,
                '-t', str(target_duration),
                '-c', 'copy',
                output
            ], check=True, capture_output=True)
            
            return output
        
        except subprocess.CalledProcessError:
            print(f"  [compositor] WARN Trim failed, using original")
            return video_path
    
    def _merge_split_screen(
        self,
        top_video: str,
        bottom_video: str,
        output: str
    ):
        """
        Merge two videos into split screen.

        Vertical split:
            Top: Story slideshow
            Bottom: Marble race gameplay

        Horizontal split (if needed):
            Left: Story slideshow
            Right: Marble race gameplay
        """

        if SPLIT_MODE == "vertical":
            # Vertical stacking (top/bottom)
            half_height = OUTPUT_HEIGHT // 2

            filter_complex = (
                f"[0:v]scale={OUTPUT_WIDTH}:{half_height}:force_original_aspect_ratio=decrease,"
                f"pad={OUTPUT_WIDTH}:{half_height}:(ow-iw)/2:(oh-ih)/2[top];"
                f"[1:v]scale={OUTPUT_WIDTH}:{half_height}:force_original_aspect_ratio=decrease,"
                f"pad={OUTPUT_WIDTH}:{half_height}:(ow-iw)/2:(oh-ih)/2[bottom];"
                f"[top][bottom]vstack=inputs=2[out]"
            )
        else:
            # Horizontal stacking (side-by-side)
            half_width = OUTPUT_WIDTH // 2

            filter_complex = (
                f"[0:v]scale={half_width}:{OUTPUT_HEIGHT}:force_original_aspect_ratio=decrease,"
                f"pad={half_width}:{OUTPUT_HEIGHT}:(ow-iw)/2:(oh-ih)/2[left];"
                f"[1:v]scale={half_width}:{OUTPUT_HEIGHT}:force_original_aspect_ratio=decrease,"
                f"pad={half_width}:{OUTPUT_HEIGHT}:(ow-iw)/2:(oh-ih)/2[right];"
                f"[left][right]hstack=inputs=2[out]"
            )

        try:
            subprocess.run([
                'ffmpeg', '-y',
                '-i', top_video,
                '-i', bottom_video,
                '-filter_complex', filter_complex,
                '-map', '[out]',
                '-c:v', 'libx264',
                '-preset', 'medium',
                '-crf', '23',
                '-pix_fmt', 'yuv420p',
                '-r', str(FPS),
                output
            ], check=True, capture_output=True)

        except subprocess.CalledProcessError as e:
            stderr = e.stderr.decode('utf-8', errors='ignore') if e.stderr else 'Unknown error'
            print(f"  [compositor] X FFmpeg error: {stderr[:300]}")
            raise RuntimeError(f"Video merge failed: {stderr[:200]}")
    
    def _add_audio_and_subtitles(
        self,
        video_path: str,
        audio_path: str,
        subtitle_path: str,
        output_path: str
    ):
        """Add narration audio and TikTok-style subtitles to video."""

        try:
            # Build ffmpeg command
            cmd = ['ffmpeg', '-y', '-i', video_path, '-i', audio_path]

            # If subtitles provided, add subtitle filter
            if subtitle_path and os.path.exists(subtitle_path):
                print(f"  [compositor] Adding TikTok-style subtitles (ASS format)...")

                # Normalize path for FFmpeg (handle Windows paths)
                ass_path = subtitle_path.replace('\\', '/').replace(':', '\\:')

                # Use subtitles filter for ASS file (styling is baked into the .ass file)
                # No force_style needed - positioning and styling are in the ASS file
                subtitle_filter = f"subtitles='{ass_path}'"

                cmd.extend([
                    '-vf', subtitle_filter,
                    '-c:a', 'aac',
                    '-b:a', '128k',
                    '-shortest',
                    output_path
                ])
            else:
                # No subtitles - just add audio
                print(f"  [compositor] WARNING: No subtitle file found at: {subtitle_path}")
                cmd.extend([
                    '-c:v', 'copy',
                    '-c:a', 'aac',
                    '-b:a', '128k',
                    '-shortest',
                    output_path
                ])

            subprocess.run(cmd, check=True, capture_output=True)

        except subprocess.CalledProcessError as e:
            stderr = e.stderr.decode('utf-8', errors='ignore') if e.stderr else 'Unknown error'
            print(f"  [compositor] WARN Audio/subtitle merge failed: {stderr[:200]}")
            raise


def create_compositor() -> VideoCompositor:
    """Factory function."""
    return VideoCompositor()


# Test mode
if __name__ == "__main__":
    print("=" * 70)
    print("  VIDEO COMPOSITOR TEST")
    print("=" * 70)

    compositor = create_compositor()

    print("OK Compositor initialized")
    print(f"  Output resolution: {OUTPUT_WIDTH}x{OUTPUT_HEIGHT}")
    print(f"  Split mode: {SPLIT_MODE}")
    print(f"  FPS: {FPS}")
