"""
subtitle_generator.py - TikTok-Style Subtitle Generator (Production-Ready)

Generates animated word-by-word subtitles with TikTok styling:
- Yellow text with black outline
- Centered positioning
- Word-by-word or phrase-by-phrase highlighting
- Smooth animations

FEATURES:
- Automatic timing calculation from word count
- Multiple subtitle styles (TikTok, viral, dramatic)
- Configurable positioning and colors
- FFmpeg SRT subtitle overlay
"""

import os
import re
from typing import List, Tuple
from production_config import OUTPUT_DIR


class SubtitleGenerator:
    """
    Generates TikTok-style subtitles for story videos.
    """

    def __init__(self):
        self.style = "tiktok"  # tiktok, viral, dramatic

    def generate_subtitles(
        self,
        script: str,
        duration: float,
        output_path: str,
        style: str = "tiktok"
    ) -> str:
        """
        Generate SRT subtitle file from script.

        Parameters
        ----------
        script : str
            Full narration script
        duration : float
            Total duration in seconds
        output_path : str
            Path to save .srt file
        style : str
            Subtitle style ("tiktok", "viral", "dramatic")

        Returns
        -------
        str
            Path to generated SRT file
        """

        self.style = style

        # Split script into words
        words = self._split_into_words(script)

        # Calculate timing for each word
        timings = self._calculate_timings(words, duration)

        # Group words into phrases (3-5 words per subtitle)
        phrases = self._group_into_phrases(words, timings)

        # Generate ASS content (better positioning control than SRT)
        ass_content = self._generate_srt(phrases)

        # Save to ASS file (using .ass extension for proper format)
        ass_path = output_path.replace('.srt', '').replace('.ass', '') + '.ass'
        with open(ass_path, 'w', encoding='utf-8') as f:
            f.write(ass_content)

        print(f"  [subtitles] Generated {len(phrases)} subtitle phrases (ASS format)")
        return ass_path

    def _split_into_words(self, script: str) -> List[str]:
        """Split script into words, preserving punctuation."""

        # Remove excessive whitespace
        script = ' '.join(script.split())

        # Split on whitespace but keep punctuation attached
        words = script.split()

        return [w.strip() for w in words if w.strip()]

    def _calculate_timings(
        self,
        words: List[str],
        total_duration: float
    ) -> List[Tuple[float, float]]:
        """
        Calculate start/end time for each word.

        Uses average speaking rate: ~2.5 words per second for TTS
        """

        words_per_second = 2.5
        avg_word_duration = 1.0 / words_per_second

        timings = []
        current_time = 0.0

        for word in words:
            # Adjust duration based on word length
            word_length = len(word)
            word_duration = avg_word_duration * (word_length / 5.0)  # 5 = average word length
            word_duration = max(0.2, min(word_duration, 1.0))  # clamp between 0.2-1.0s

            start_time = current_time
            end_time = current_time + word_duration

            timings.append((start_time, end_time))
            current_time = end_time

        # Scale to match actual duration
        if current_time > 0:
            scale_factor = total_duration / current_time
            timings = [(start * scale_factor, end * scale_factor) for start, end in timings]

        return timings

    def _group_into_phrases(
        self,
        words: List[str],
        timings: List[Tuple[float, float]]
    ) -> List[Tuple[str, float, float]]:
        """
        Group words into subtitle phrases (3-5 words each).

        Returns list of (phrase_text, start_time, end_time)
        """

        phrases = []
        current_phrase = []
        phrase_start = None

        for i, (word, (start, end)) in enumerate(zip(words, timings)):
            if phrase_start is None:
                phrase_start = start

            current_phrase.append(word)

            # End phrase conditions:
            # 1. Reached 5 words
            # 2. Punctuation at end of word
            # 3. Last word
            is_last = (i == len(words) - 1)
            has_punctuation = bool(re.search(r'[.!?,;:]$', word))
            is_long_enough = len(current_phrase) >= 3

            should_end = (
                len(current_phrase) >= 5 or
                (has_punctuation and is_long_enough) or
                is_last
            )

            if should_end:
                phrase_text = ' '.join(current_phrase)
                phrases.append((phrase_text, phrase_start, end))
                current_phrase = []
                phrase_start = None

        return phrases

    def _generate_srt(
        self,
        phrases: List[Tuple[str, float, float]]
    ) -> str:
        """
        Generate ASS subtitle file content with absolute center positioning.

        ASS Format gives us full control over positioning.
        Video dimensions: 1080x1920 (vertical)
        Center position: x=540, y=960 (absolute middle of screen)
        """

        # ASS Header with proper styling and center positioning
        ass_header = """[Script Info]
Title: TikTok Style Subtitles
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial Black,100,&H0000D7FF,&H000000FF,&H00000000,&H00000000,-1,0,0,0,100,100,0,0,1,2,1,2,10,10,980,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

        ass_lines = [ass_header.strip()]

        for i, (text, start, end) in enumerate(phrases):
            # Convert times to ASS format (H:MM:SS.cc)
            start_str = self._format_ass_time(start)
            end_str = self._format_ass_time(end)

            # ASS dialogue line with absolute center positioning
            # Using Alignment=2 (Bottom center) which is already set in Style
            ass_lines.append(
                f"Dialogue: 0,{start_str},{end_str},Default,,0,0,0,,{text}"
            )

        return '\n'.join(ass_lines)

    def _format_srt_time(self, seconds: float) -> str:
        """Convert seconds to SRT time format: HH:MM:SS,mmm"""

        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)

        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

    def _format_ass_time(self, seconds: float) -> str:
        """Convert seconds to ASS time format: H:MM:SS.cc"""

        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = seconds % 60

        return f"{hours}:{minutes:02d}:{secs:05.2f}"

    def _apply_text_style(self, text: str) -> str:
        """
        Apply text styling for different subtitle styles.

        Note: Actual visual styling is done by FFmpeg
        This just returns the text (styling applied in video_compositor)
        """

        # For now, return uppercase for emphasis (TikTok style)
        if self.style == "tiktok":
            return text.upper()
        elif self.style == "dramatic":
            return text.upper()
        else:
            return text

    def get_ffmpeg_subtitle_filter(self, ass_path: str, style: str = "tiktok") -> str:
        """
        Get FFmpeg filter for rendering subtitles with TikTok styling.

        Parameters
        ----------
        ass_path : str
            Path to ASS subtitle file
        style : str
            Subtitle style (not used - styling is in ASS file)

        Returns
        -------
        str
            FFmpeg subtitle filter string
        """

        # Normalize path for FFmpeg (use forward slashes)
        ass_path = ass_path.replace('\\', '/')

        # Use subtitles filter for ASS file (styling and positioning are baked into the .ass file)
        # Golden Standard: Center positioned at x=540, y=960 (absolute middle of 1080x1920)
        return f"subtitles='{ass_path}'"


def create_subtitle_generator() -> SubtitleGenerator:
    """Factory function."""
    return SubtitleGenerator()


# Test mode
if __name__ == "__main__":
    print("=" * 70)
    print("  SUBTITLE GENERATOR TEST")
    print("=" * 70)

    generator = create_subtitle_generator()

    test_script = """
    Something was wrong at the research facility. Dr. Sarah Chen noticed it first.
    The readings showed impossible values. Equipment that had worked perfectly
    suddenly displayed numbers that defied physics. She checked everything.
    It was all perfect. But the anomalies continued. Then came the sounds.
    Late at night, when the building should have been empty, footsteps echoed.
    Security footage revealed nothing. Yet the sounds persisted, growing louder.
    On the seventh day, every sensor activated simultaneously. The final log entry
    contained just three words. And then, absolute silence.
    """

    output_path = os.path.join(OUTPUT_DIR, "test_subtitles.srt")

    srt_path = generator.generate_subtitles(
        script=test_script,
        duration=60.0,
        output_path=output_path,
        style="tiktok"
    )

    print(f"\nOK Generated: {srt_path}")

    # Show first few lines
    with open(srt_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()[:15]
        print("\nPreview:")
        print(''.join(lines))

    print("\n" + "=" * 70)
    print("  TEST COMPLETE")
    print("=" * 70)
