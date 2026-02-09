"""
narration_engine.py - Viral Audio Generator (Edge TTS Upgrade)

Replaces robotic gTTS/espeak with Neural storytelling voices.
Includes built-in audio engineering (Bass Boost + Compression).
"""

import os
import asyncio
import subprocess
import wave
import edge_tts
from typing import Optional
from production_config import NARRATION_MIN_DURATION, NARRATION_MAX_DURATION

# ============================================================================
# VIRAL AUDIO CONFIGURATION
# ============================================================================
# "en-US-ChristopherNeural": Deep, calm, storytelling (Best for retention)
# "en-US-GuyNeural": Energetic, news-anchor style
VOICE = "en-US-ChristopherNeural"

# Speed: +10% is the industry standard for Shorts/TikTok to keep attention
RATE = "+10%"  
# ============================================================================

class NarrationEngine:
    """
    Generates professional-grade narration using Microsoft Edge's Neural TTS.
    Compatible drop-in replacement for the old gTTS engine.
    """
    
    def __init__(self):
        print(f"  [Narration] Initialized Viral Engine (Voice: {VOICE})")
        self._verify_ffmpeg()

    def _verify_ffmpeg(self):
        """Ensure FFmpeg is installed for audio mastering."""
        try:
            subprocess.run(["ffmpeg", "-version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except FileNotFoundError:
            print("  [ERROR] FFmpeg not found! Audio mastering will fail.")

    async def _generate_raw_async(self, text: str, output_path: str):
        """
        Internal async wrapper to talk to the Edge TTS API.
        """
        communicate = edge_tts.Communicate(text, VOICE, rate=RATE)
        await communicate.save(output_path)

    def _apply_audio_mastering(self, input_path: str, output_path: str):
        """
        Applies 'Movie Trailer' style mastering using FFmpeg:
        1. Bass Boost (g=2) for resonance.
        2. Treble Boost (g=1) for clarity on phones.
        3. Compression (compand) to even out volume levels.
        4. Silence Removal (0.2s max) to keep pacing tight.
        """
        # Complex filter chain for "Viral" sound
        # - silenceremove: Trims silence > 0.2s
        # - bass/treble: EQ
        # - compand: Compression
        filter_complex = (
            "silenceremove=stop_periods=-1:stop_duration=0.2:stop_threshold=-50dB,"
            "bass=g=2,treble=g=1,"
            "compand=0.3|0.3:1|1:-90/-60|-60/-40|-40/-30|-20/-20:6:0:-90:0.2"
        )
        
        cmd = [
            'ffmpeg', '-y',
            '-i', input_path,
            '-af', filter_complex,
            '-ar', '44100',       # Standard 44.1kHz
            '-ac', '1',           # Mono is fine for voice
            output_path           # FFmpeg detects .wav extension automatically
        ]
        
        # Run FFmpeg silently
        try:
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"FFmpeg mastering failed: {e}")

    def _get_wav_duration(self, wav_path: str) -> float:
        """Helper to get exact duration of the final WAV file."""
        try:
            with wave.open(wav_path, 'rb') as wf:
                frames = wf.getnframes()
                rate = wf.getframerate()
                return frames / float(rate)
        except Exception as e:
            print(f"  [Narration WARN] Could not read duration: {e}")
            return 0.0

    def generate_narration(self, script: str, output_path: str) -> float:
        """
        Main entry point called by main_story_mode.py.
        Returns duration in seconds.
        """
        print(f"  [TTS] Generating viral audio ({len(script.split())} words)...")
        
        # Intermediate file for raw MP3
        temp_raw = output_path.replace(".wav", "_raw.mp3")
        
        try:
            # STEP 1: Generate Raw Audio (Async run in Sync context)
            asyncio.run(self._generate_raw_async(script, temp_raw))
            
            # STEP 2: Apply Mastering & Convert to WAV
            # Ensure output_path ends in .wav
            if not output_path.endswith('.wav'):
                output_path = output_path.rsplit('.', 1)[0] + '.wav'
                
            self._apply_audio_mastering(temp_raw, output_path)
            
            # STEP 3: Cleanup & Measure
            if os.path.exists(temp_raw):
                os.remove(temp_raw)
                
            duration = self._get_wav_duration(output_path)
            
            # Duration Validation (Restored from your old code)
            if duration < NARRATION_MIN_DURATION:
                print(f"  [Narration] WARN: Duration {duration:.1f}s is BELOW minimum {NARRATION_MIN_DURATION}s")
                print("  [Narration]       Video may not qualify for monetization.")
            elif duration > NARRATION_MAX_DURATION:
                print(f"  [Narration] WARN: Duration {duration:.1f}s is ABOVE maximum {NARRATION_MAX_DURATION}s")
                print("  [Narration]       Consider trimming script.")
            else:
                print(f"  [Narration] OK: Duration {duration:.1f}s (Optimal)")
            
            return duration

        except Exception as e:
            print(f"  [TTS ERROR] Generation failed: {e}")
            return 0.0

    def adjust_script_for_duration(self, script: str, target_duration: float) -> str:
        """
        [COMPATIBILITY METHOD]
        Restored so main_story_mode.py doesn't crash.
        """
        # Adjusted for +10% speed (roughly 2.6 words per second)
        words_per_second = 2.6 
        target_words = int(target_duration * words_per_second)
        
        words = script.split()
        current_words = len(words)
        
        if current_words > target_words * 1.1:
            trimmed = ' '.join(words[:target_words])
            # Try to end on a sentence
            last_period = trimmed.rfind('.')
            if last_period > target_words * 0.8:
                trimmed = trimmed[:last_period + 1]
                
            print(f"  [Narration] Trimmed script: {current_words} -> {len(trimmed.split())} words")
            return trimmed
            
        return script

def create_narration_engine() -> NarrationEngine:
    """Factory function used by main_story_mode.py"""
    return NarrationEngine()

# ============================================================================
# TEST BLOCK
# ============================================================================
if __name__ == "__main__":
    print("Testing Viral Audio Engine...")
    engine = create_narration_engine()
    test_text = "This is the new viral voice engine. Notice the deep bass, the clear treble, and the natural flow. This is how you win on YouTube Shorts."
    
    # Run test
    output_file = "test_viral.wav"
    dur = engine.generate_narration(test_text, output_file)
    
    if os.path.exists(output_file):
        print(f"Test complete. Created {output_file} ({dur:.2f}s)")