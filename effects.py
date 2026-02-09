"""
Visual effects  +  AudioLogger  -  pure NumPy / OpenCV.

AudioLogger  (replaces live SoundManager)
-----------------------------------------
During rendering every "play" call just appends
    { 'time': <seconds>, 'type': <str>, 'params': {...} }
to self.audio_log.   main.py calls  synthesise_wav(audio_log)  after the
video is written to bake all the logged events into a single WAV file,
which is then muxed into the MP4 by ffmpeg.
"""

import math
import random
import cv2
import numpy as np
from config import *


# ---------------------------------------------------------------------------
# Colour helpers
# ---------------------------------------------------------------------------
def _rgb_to_bgr(rgb):
    return (int(rgb[2]), int(rgb[1]), int(rgb[0]))


# ---------------------------------------------------------------------------
# ScreenShake
# ---------------------------------------------------------------------------
class ScreenShake:
    def __init__(self):
        self.offset_x = 0
        self.offset_y = 0
        self.trauma   = 0

    def add_trauma(self, amount):
        self.trauma = min(1.0, self.trauma + amount)

    def update(self):
        if self.trauma > 0.01:
            shake = self.trauma ** 2
            self.offset_x = (random.random()-0.5)*2 * shake * SHAKE_INTENSITY * 10
            self.offset_y = (random.random()-0.5)*2 * shake * SHAKE_INTENSITY * 10
            self.trauma  *= SHAKE_DECAY
        else:
            self.trauma   = 0
            self.offset_x = 0
            self.offset_y = 0

    def get_offset(self):
        return (int(self.offset_x), int(self.offset_y))


# ---------------------------------------------------------------------------
# ParticleSystem
# ---------------------------------------------------------------------------
class ParticleSystem:
    def __init__(self):
        self.particles      = []   # explosion sparks
        self.glow_particles = []   # trail glow dots
        self.confetti       = []

    # -- factories ------------------------------------------------------
    def add_explosion(self, pos, color, count=30, scale=1.0):
        for _ in range(min(count, EXPLOSION_PARTICLES)):
            angle = random.uniform(0, 2*math.pi)
            speed = random.uniform(2, 8) * scale
            life  = random.uniform(0.4, 0.9)
            self.particles.append({
                'pos':  list(pos),
                'vel':  [math.cos(angle)*speed, math.sin(angle)*speed],
                'color': color,
                'life': life, 'max_life': life,
                'size': random.uniform(2, 6)*scale,
            })

    def add_trail(self, pos, color, scale=1.0):
        self.glow_particles.append({
            'pos':  list(pos),
            'color': color,
            'life': 0.15, 'max_life': 0.15,
            'size': random.uniform(2, 5)*scale,
        })

    def add_confetti(self, pos, count=100):
        cols = [(255,71,87),(251,191,36),(52,211,153),
                (168,85,247),(236,72,153),(58,134,255)]
        for _ in range(min(count, CONFETTI_COUNT)):
            angle = random.uniform(-math.pi*0.25, -math.pi*0.75)
            speed = random.uniform(6, 16)
            life  = random.uniform(2.0, 4.0)
            self.confetti.append({
                'pos':  list(pos),
                'vel':  [math.cos(angle)*speed, math.sin(angle)*speed],
                'color': random.choice(cols),
                'life': life, 'max_life': life,
                'size': random.uniform(4, 9),
                'rotation': random.uniform(0, 360),
                'rotation_speed': random.uniform(-10, 10),
            })

    # -- tick -----------------------------------------------------------
    def update(self, dt=1/60):
        for p in self.particles[:]:
            p['pos'][0] += p['vel'][0]
            p['pos'][1] += p['vel'][1]
            p['vel'][1] += 0.25
            p['life']   -= dt
            if p['life'] <= 0:
                self.particles.remove(p)

        for p in self.glow_particles[:]:
            p['life'] -= dt
            if p['life'] <= 0:
                self.glow_particles.remove(p)

        for p in self.confetti[:]:
            p['pos'][0]  += p['vel'][0]
            p['pos'][1]  += p['vel'][1]
            p['vel'][1]  += 0.35
            p['vel'][0]  *= 0.99
            p['rotation']+= p['rotation_speed']
            p['life']    -= dt
            if p['life'] <= 0:
                self.confetti.remove(p)

    # -- rendering (OpenCV) ---------------------------------------------
    def draw(self, frame):
        # glow / trail dots
        for p in self.glow_particles:
            a    = max(0, min(1, p['life']/p['max_life']))
            sz   = max(1, int(p['size']*a))
            col  = _rgb_to_bgr(tuple(min(255, int(c*a*1.3)) for c in p['color']))
            cv2.circle(frame, (int(p['pos'][0]), int(p['pos'][1])), sz, col, -1)

        # explosion sparks
        for p in self.particles:
            a    = max(0, min(1, p['life']/p['max_life']))
            sz   = max(1, int(p['size']*a))
            col  = _rgb_to_bgr(tuple(min(255, int(c*a)) for c in p['color']))
            cv2.circle(frame, (int(p['pos'][0]), int(p['pos'][1])), sz, col, -1)

        # confetti rectangles (approximated as small filled circles for speed)
        for p in self.confetti:
            a = max(0, min(1, p['life']/p['max_life']))
            if a < 0.05:
                continue
            sz  = max(1, int(p['size']*a))
            col = _rgb_to_bgr(tuple(min(255, int(c*a)) for c in p['color']))
            cv2.circle(frame, (int(p['pos'][0]), int(p['pos'][1])), sz, col, -1)


# ---------------------------------------------------------------------------
# DynamicBackground  - dark grid with subtle pulse
# ---------------------------------------------------------------------------
class DynamicBackground:
    def __init__(self, width, height, color=None):
        self.width     = width
        self.height    = height
        self.time      = 0.0
        self.grid_size = 50
        self.base_color = color if color else BG_COLOR

    def update(self):
        self.time += 0.015
        if self.time > 1000:
            self.time = 0

    def draw(self, frame):
        pulse     = math.sin(self.time*0.5)*0.15 + 0.85
        r, g, b = self.base_color
        base_bgr = (int(b * pulse), 
                    int(g * pulse), 
                    int(r * pulse))
        frame[:] = base_bgr                 # fill entire frame

        # animated grid lines (very subtle)
        grid_bgr = tuple(min(255, c+8) for c in base_bgr)
        off_x = int((self.time*15) % self.grid_size)
        off_y = int((self.time*10) % self.grid_size)

        x = -self.grid_size
        while x < self.width + self.grid_size:
            cv2.line(frame, (x - off_x, 0),
                     (x - off_x, self.height), grid_bgr, 1)
            x += self.grid_size

        y = -self.grid_size
        while y < self.height + self.grid_size:
            cv2.line(frame, (0, y - off_y),
                     (self.width, y - off_y), grid_bgr, 1)
            y += self.grid_size


# ---------------------------------------------------------------------------
# BloomEffect  - offline-quality glow (BLOOM_ITERATIONS = 4)
# ---------------------------------------------------------------------------
class BloomEffect:
    """
    Downscale -> blur (multiple passes) -> upscale -> additive blend.
    Works on a BGR numpy frame in-place.
    """
    def __init__(self, width, height):
        self.w  = width
        self.h  = height
        self.bw = max(1, width  // BLOOM_SCALE)
        self.bh = max(1, height // BLOOM_SCALE)
        self.enabled = BLOOM_ENABLED

    def apply(self, frame):
        """frame: HxWx3 BGR uint8, mutated in place."""
        if not self.enabled:
            return
        # downscale
        small = cv2.resize(frame, (self.bw, self.bh), interpolation=cv2.INTER_AREA)
        # Gaussian blur - kernel size must be odd; scale with iterations
        ksize = 3 + BLOOM_ITERATIONS * 2   # e.g. 11 when iterations=4
        if ksize % 2 == 0:
            ksize += 1
        for _ in range(BLOOM_ITERATIONS):
            small = cv2.GaussianBlur(small, (ksize, ksize), 0)
        # upscale back
        bloom_up = cv2.resize(small, (self.w, self.h), interpolation=cv2.INTER_LINEAR)
        # additive blend (saturate at 255)
        cv2.add(frame, bloom_up, dst=frame)


# ---------------------------------------------------------------------------
# AudioLogger  <- NEW  - records every sound event; no playback during render
# ---------------------------------------------------------------------------
class AudioLogger:
    """
    Drop-in replacement for the old live SoundManager.

    Every method that the game calls (play_bounce, play_break, play_win)
    now just appends a lightweight dict to self.audio_log.  After the
    video frames are written, main.py calls synthesise_wav(audio_log)
    to bake the entire log into a single mono WAV.
    """

    def __init__(self):
        self.audio_log   = []       # list of event dicts
        self._scale_idx  = 0        # walks through pentatonic scale
        
        # COLD START FIX: Inject an intro swoosh at timestamp 0.0
        # This prevents the first 1-2 seconds from being silent
        self._add_intro_swoosh()

    def _add_intro_swoosh(self):
        """Generate an ascending 'start whistle' sound at the very beginning."""
        # Create a rising frequency sweep (swoosh effect)
        for i in range(3):
            freq = BASE_FREQUENCY * PENTATONIC_SCALE[i] * 1.5
            self.audio_log.append({
                'time':   0.0 + i * 0.06,  # Staggered start
                'type':   'intro',
                'freq':   freq,
                'dur':    0.15,
                'volume': 0.12,
            })

    # -- event recorders ------------------------------------------------
    def play_bounce(self, speed_ratio=1.0, current_time=0.0):
        note  = PENTATONIC_SCALE[self._scale_idx % len(PENTATONIC_SCALE)]
        freq  = BASE_FREQUENCY * note * (0.85 + speed_ratio * 0.3)
        self._scale_idx += 1
        self.audio_log.append({
            'time':   current_time,
            'type':   'bounce',
            'freq':   freq,
            'dur':    0.08,
            'volume': 0.18,
        })

    def play_break(self, pitch_index=0, current_time=0.0):
        note = PENTATONIC_SCALE[pitch_index % len(PENTATONIC_SCALE)]
        freq = BASE_FREQUENCY * note * 0.5
        self.audio_log.append({
            'time':   current_time,
            'type':   'break',
            'freq':   freq,
            'dur':    0.15,
            'volume': 0.22,
        })

    def play_win(self, current_time=0.0):
        """Ascending three-note arpeggio."""
        for i, note_idx in enumerate([0, 2, 4]):
            freq = BASE_FREQUENCY * PENTATONIC_SCALE[note_idx] * 2
            self.audio_log.append({
                'time':   current_time + i * 0.05,
                'type':   'win',
                'freq':   freq,
                'dur':    0.20,
                'volume': 0.15,
            })


# ---------------------------------------------------------------------------
# synthesise_wav  - turn an audio_log into a mono 16-bit WAV file
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# FlashEffect  -  white brightness spike between rounds
# ---------------------------------------------------------------------------
class FlashEffect:
    """
    Call trigger() to start a flash.  Call apply(frame) every frame;
    it brightens the frame by `intensity` and decays automatically.
    """
    def __init__(self):
        self.intensity = 0.0

    def trigger(self, strength=1.0):
        self.intensity = min(1.0, strength)

    def apply(self, frame):
        if self.intensity < 0.01:
            self.intensity = 0.0
            return
        white = np.full_like(frame, 255)
        cv2.addWeighted(frame, 1.0 - self.intensity,
                        white,  self.intensity, 0, dst=frame)
        self.intensity *= 0.82


# ---------------------------------------------------------------------------
# generate_background_music  -  procedural 'Thump' beat track
# ---------------------------------------------------------------------------
def generate_background_music(duration_seconds, bpm=128):
    """
    Generate a procedural drum/heartbeat rhythm using pure NumPy.
    
    Parameters
    ----------
    duration_seconds : float
    bpm             : int, beats per minute (default 128 for energetic feel)
    
    Returns
    -------
    numpy array of float64 samples (mono, normalized to [-1, 1])
    """
    n_samples = int(SAMPLE_RATE * duration_seconds)
    music     = np.zeros(n_samples, dtype=np.float64)
    
    # Calculate beat interval
    beat_interval = 60.0 / bpm  # seconds between beats
    beat_samples  = int(beat_interval * SAMPLE_RATE)
    
    # Generate kick drum hits at each beat
    num_beats = int(duration_seconds / beat_interval)
    
    for beat in range(num_beats):
        start_sample = beat * beat_samples
        if start_sample >= n_samples:
            break
            
        # KICK DRUM: Low frequency sine with exponential decay
        kick_dur     = 0.15  # 150ms kick
        kick_samples = int(kick_dur * SAMPLE_RATE)
        end_sample   = min(start_sample + kick_samples, n_samples)
        actual_len   = end_sample - start_sample
        
        t = np.linspace(0, kick_dur, actual_len, endpoint=False)
        
        # Low frequency (60 Hz) with pitch bend down
        freq = 60 * np.exp(-t * 8)  # Frequency drops rapidly
        kick = np.sin(2 * np.pi * np.cumsum(freq) / SAMPLE_RATE)
        
        # Exponential decay envelope
        envelope = np.exp(-t * 12)
        kick *= envelope * 0.25  # Volume
        
        music[start_sample:end_sample] += kick
        
        # HI-HAT: Add on every other beat for rhythm variation
        if beat % 2 == 1:
            hat_dur     = 0.08
            hat_samples = int(hat_dur * SAMPLE_RATE)
            hat_end     = min(start_sample + hat_samples, n_samples)
            hat_len     = hat_end - start_sample
            
            # White noise filtered for hi-hat sound
            noise = np.random.randn(hat_len) * 0.08
            # Quick decay
            hat_env = np.exp(-np.linspace(0, hat_dur, hat_len) * 30)
            music[start_sample:hat_end] += noise * hat_env
    
    # Add subtle bass pulse (sub-bass)
    t_all = np.linspace(0, duration_seconds, n_samples, endpoint=False)
    bass_freq = 40  # Sub-bass frequency
    bass_pulse = np.sin(2 * np.pi * bass_freq * t_all) * 0.1
    # Modulate with slower pulse
    pulse_rate = bpm / 60.0 * 2  # Pulse at 2x beat rate
    modulation = (np.sin(2 * np.pi * pulse_rate * t_all) * 0.5 + 0.5) ** 2
    music += bass_pulse * modulation
    
    return music


# ---------------------------------------------------------------------------
# synthesise_wav  -  bake audio_log -> mono 16-bit WAV with background music
# ---------------------------------------------------------------------------
def synthesise_wav(audio_log, total_duration, output_path):
    """
    Parameters
    ----------
    audio_log     : list of dicts produced by AudioLogger
    total_duration: float, seconds
    output_path   : str, path to write .wav
    """
    import wave as _wave

    n_samples = int(SAMPLE_RATE * total_duration)
    track     = np.zeros(n_samples, dtype=np.float64)

    # ===================================================================
    # 1. Generate procedural background music (MONEY PRINTER: No MP3!)
    # ===================================================================
    print("  Generating procedural background music...", flush=True)
    background_music = generate_background_music(total_duration, bpm=128)
    track += background_music  # Mix into main track

    # ===================================================================
    # 2. Add all sound effects from audio_log
    # ===================================================================
    for ev in audio_log:
        start_sample = int(ev['time'] * SAMPLE_RATE)
        dur_samples  = int(ev['dur']  * SAMPLE_RATE)
        end_sample   = min(start_sample + dur_samples, n_samples)
        if start_sample >= n_samples:
            continue

        actual_dur = (end_sample - start_sample) / SAMPLE_RATE
        t = np.linspace(0, actual_dur, end_sample - start_sample, endpoint=False)

        # sine tone
        tone = np.sin(2 * np.pi * ev['freq'] * t) * ev['volume']

        # quick fade-out envelope (last 30 % of duration)
        fade_start = int(len(tone) * 0.7)
        if fade_start < len(tone):
            fade_len  = len(tone) - fade_start
            tone[fade_start:] *= np.linspace(1.0, 0.0, fade_len)

        track[start_sample:end_sample] += tone

    # normalise to [-1, 1] if any clipping
    peak = np.max(np.abs(track))
    if peak > 1.0:
        track /= peak

    # write 16-bit mono WAV
    pcm = (track * 32767).astype(np.int16)
    with _wave.open(output_path, 'w') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(pcm.tobytes())

    return output_path