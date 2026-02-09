"""
narration_engine.py - TTS-based Narration Audio Generator (Production-Ready)

Converts story scripts to natural-sounding narration audio.
Audio duration is the source of truth for all video timing.

PRODUCTION IMPROVEMENTS:
- Uses centralized configuration
- Better error handling
- Multiple TTS engine support
"""

import subprocess
import os
import wave
from typing import Optional
from production_config import NARRATION_MIN_DURATION, NARRATION_MAX_DURATION


class NarrationEngine:
    """
    Generates narration audio from story scripts using TTS.
    Supports espeak-ng and gTTS.
    """
    
    def __init__(self):
        self._verify_dependencies()
    
    def _verify_dependencies(self):
        """Verify required TTS tools are available."""
        
        # Check for espeak-ng or piper-tts
        try:
            subprocess.run(
                ["espeak-ng", "--version"],
                capture_output=True,
                check=True
            )
            self.tts_engine = "espeak"
            print("  [narration] Using espeak-ng for TTS")
        except (FileNotFoundError, subprocess.CalledProcessError):
            # Fallback to gtts if espeak not available
            try:
                import gtts
                self.tts_engine = "gtts"
                print("  [narration] Using gTTS for narration")
            except ImportError:
                raise RuntimeError(
                    "No TTS engine available. Install espeak-ng or gTTS:\n"
                    "  Ubuntu: sudo apt install espeak-ng\n"
                    "  Python: pip install gtts"
                )
    
    def generate_narration(self, script: str, output_path: str) -> float:
        """
        Generate narration audio from script.
        
        Parameters
        ----------
        script : str
            Full narration text
        output_path : str
            Path to save WAV file
        
        Returns
        -------
        float : Duration in seconds
        """
        
        print(f"  [narration] Generating audio ({len(script)} chars, {len(script.split())} words)...")
        
        # Pre-check expected duration based on word count
        word_count = len(script.split())
        # Average speaking rate: ~2.5 words per second for TTS
        estimated_duration = word_count / 2.5
        
        if estimated_duration < NARRATION_MIN_DURATION - 5:  # 5 second buffer
            print(f"  [narration] WARN Script likely too short ({estimated_duration:.1f}s estimated)")
            print(f"  [narration]   Recommend minimum {int(NARRATION_MIN_DURATION * 2.5)} words")
        
        if self.tts_engine == "espeak":
            duration = self._generate_espeak(script, output_path)
        else:
            duration = self._generate_gtts(script, output_path)
        
        # Validate duration
        if duration < NARRATION_MIN_DURATION:
            print(f"  [narration] WARN Duration {duration:.1f}s below minimum {NARRATION_MIN_DURATION}s")
            print(f"  [narration]   VIDEO MAY NOT QUALIFY FOR MONETIZATION")
        elif duration > NARRATION_MAX_DURATION:
            print(f"  [narration] WARN Duration {duration:.1f}s above maximum {NARRATION_MAX_DURATION}s")
            print(f"  [narration]   Consider trimming for better retention")
        else:
            print(f"  [narration] OK Duration {duration:.1f}s (optimal for monetization)")

        return duration
    
    def _generate_espeak(self, script: str, output_path: str) -> float:
        """Generate audio using espeak-ng with DRAMATICALLY improved settings."""

        # Use natural English voice with optimized dramatic settings
        subprocess.run([
            "espeak-ng",
            "-v", "en-us+f4",        # US English, female voice variant 4 (most natural)
            "-s", "155",             # Speed: 155 wpm (slower, more deliberate for suspense)
            "-p", "45",              # Pitch: 45 (lower, more dramatic)
            "-a", "180",             # Amplitude: 180 (clear but not harsh)
            "-g", "15",              # Gap between words: 15ms (more suspenseful pacing)
            "-k", "10",              # Emphasis/capitals: stronger for drama
            "-w", output_path,       # Output WAV file
            script
        ], check=True, capture_output=True)

        return self._get_wav_duration(output_path)
    
    def _generate_gtts(self, script: str, output_path: str) -> float:
        """Generate audio using Google TTS with VIRAL STORYTELLING parameters."""

        from gtts import gTTS

        # GOLDEN STANDARD: 155 WPM speaking rate with natural inflections
        # Try multiple TLDs for reliability
        temp_mp3 = output_path.replace('.wav', '_temp.mp3')

        for tld in ['com', 'co.uk', 'com.au']:
            try:
                # Use slow=False for baseline, will adjust speed with atempo
                tts = gTTS(text=script, lang='en', slow=False, tld=tld)
                tts.save(temp_mp3)
                break
            except Exception as e:
                if tld == 'com.au':  # Last attempt failed
                    raise RuntimeError(f"All gTTS attempts failed: {e}")
                continue

        # GOLDEN STANDARD AUDIO PROCESSING:
        # - Target: 155 WPM (brisk but articulate)
        # - Max 0.2s silence between sentences (remove dead air)
        # - Natural inflections via reduced compression
        subprocess.run([
            'ffmpeg', '-y',
            '-i', temp_mp3,
            '-ar', '24000',              # Higher sample rate for clarity
            '-ac', '1',                  # Mono
            '-acodec', 'pcm_s16le',      # 16-bit PCM
            # GOLDEN STANDARD FILTERS:
            # 1. silenceremove: Trim silence between sentences to max 0.2s
            # 2. loudnorm: Normalize volume for consistency
            # 3. bass/treble: Subtle warmth without over-processing
            # 4. acompressor: Very gentle (1.5:1) to preserve natural dynamics
            # 5. atempo: Speed to 155 WPM (~1.25x for viral pacing)
            '-af', (
                'silenceremove='
                'stop_periods=-1:'           # Process all silence
                'stop_duration=0.2:'         # Max 0.2s silence (Golden Standard)
                'stop_threshold=-50dB,'      # Detect silence threshold
                'loudnorm,'                  # Normalize volume
                'bass=g=0.5,'                # Subtle bass warmth
                'treble=g=-0.2,'             # Slight treble reduction
                'acompressor='               # VERY gentle compression for natural feel
                'threshold=-24dB:'           # (Simulates 35-40% stability)
                'ratio=1.5:'
                'attack=8:'
                'release=100,'
                'atempo=1.25'                # 155 WPM viral storytelling speed
            ),
            output_path
        ], check=True, capture_output=True)

        # Cleanup
        if os.path.exists(temp_mp3):
            os.remove(temp_mp3)

        return self._get_wav_duration(output_path)
    
    def _get_wav_duration(self, wav_path: str) -> float:
        """Get duration of WAV file in seconds."""
        
        try:
            with wave.open(wav_path, 'rb') as wf:
                frames = wf.getnframes()
                rate = wf.getframerate()
                duration = frames / float(rate)
                return duration
        except Exception as e:
            print(f"  [narration] WARN Error reading WAV duration: {e}")
            return 0.0
    
    def adjust_script_for_duration(self, script: str, target_duration: float) -> str:
        """
        Adjust script length to hit target duration.
        This is a fallback - prefer writing scripts to correct length initially.
        """
        
        # Rough estimate: ~150 words per minute for TTS
        # target_duration seconds -> target_words
        words_per_second = 2.5
        target_words = int(target_duration * words_per_second)
        
        words = script.split()
        current_words = len(words)
        
        if current_words > target_words * 1.1:  # 10% tolerance
            # Too long - trim
            trimmed = ' '.join(words[:target_words])
            # Try to end on complete sentence
            last_period = trimmed.rfind('.')
            if last_period > target_words * 0.8:
                trimmed = trimmed[:last_period + 1]
            
            print(f"  [narration] WARN Script trimmed: {current_words} -> {len(trimmed.split())} words")
            return trimmed
        
        return script


def create_narration_engine() -> NarrationEngine:
    """Factory function."""
    return NarrationEngine()


# Test mode
if __name__ == "__main__":
    print("=" * 70)
    print("  NARRATION ENGINE TEST")
    print("=" * 70)
    
    engine = create_narration_engine()
    
    test_script = """
    Something was terribly wrong at the research facility. Dr. Sarah Chen noticed it first.
    The readings on her monitor showed impossible values. Equipment that had functioned
    flawlessly for years suddenly displayed numbers that defied the laws of physics.
    She checked the calibration. Everything was perfect. But the anomalies continued.
    Then came the sounds. Late at night, when the building should have been completely empty,
    footsteps echoed through the sterile corridors. Security footage revealed nothing.
    Yet the sounds persisted, growing louder each night. On the seventh day, every sensor
    in the building activated simultaneously. The final log entry contained just three words.
    And then, absolute silence.
    """
    
    output = "/home/claude/test_narration.wav"
    
    duration = engine.generate_narration(test_script, output)
    
    print(f"\nOK Generated narration: {duration:.1f} seconds")
    print(f"  File: {output}")
    
    if os.path.exists(output):
        size_kb = os.path.getsize(output) / 1024
        print(f"  Size: {size_kb:.1f} KB")