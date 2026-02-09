"""
game_logic.py  -  Gauntlet round-based state machine.

VIDEO ARC
---------
  HOOK        – slow-mo arena reveal + hook text (2 s)
  ROUND 1-6   – each round: PLAYING -> WINNER_PAUSE -> FLASH -> next
  ENDCARD     – "CHAMPION" screen with final scoreboard (3 s)

The Game object owns everything.  main.py just calls
  game.update()  /  game.draw(frame)  and checks game.is_done().
"""

import math
import random
import cv2
import numpy as np
from config import *
from physics import Circle, Ball
from effects import (
    ParticleSystem, ScreenShake, DynamicBackground,
    BloomEffect, AudioLogger, FlashEffect,
)

# ---------------------------------------------------------------------------
# OpenCV helpers
# ---------------------------------------------------------------------------
FONT = cv2.FONT_HERSHEY_SIMPLEX


def _tsz(text, scale, thick=2):
    (w, h), base = cv2.getTextSize(text, FONT, scale, thick)
    return w, h + base


def _bgr(rgb):
    return (int(rgb[2]), int(rgb[1]), int(rgb[0]))


# ---------------------------------------------------------------------------
# Phase enum  (plain ints - no enum dependency)
# ---------------------------------------------------------------------------
PHASE_HOOK         = 0
PHASE_PLAYING      = 1
PHASE_WINNER_PAUSE = 2   # celebration hold after a round winner
PHASE_FLASH        = 3   # white flash transition
PHASE_ENDCARD      = 4
PHASE_DONE         = 5


# ===========================================================================
# Game
# ===========================================================================
class Game:
    def __init__(self, width, height, seed, theme_name=None, rivals=None, bg_color=None):
        """
        Parameters
        ----------
        width, height : int
        seed         : int
        theme_name   : str, optional (e.g., "FOOTBALL", "POLITICS")
        rivals       : list of tuples, optional
                       [(name1, color1, texture1), (name2, color2, texture2)]
        bg_color     : tuple, optional (R, G, B) - if None, generates random
        """
        self.width  = width
        self.height = height
        self.center = (width // 2, height // 2)
        random.seed(seed)
        self.seed   = seed

        # --- THEME SYSTEM ---
        self.theme_name = theme_name
        self.rivals     = rivals  # List of (name, color_rgb, texture_filename)
        
        # --- BACKGROUND COLOR (randomized per-run or passed in) ---
        if bg_color is None:
            # Generate random RGB values (Keep them low/dark: 5-50)
            rand_bg = (
                random.randint(5, 25),    # R: Very Low (Red adds Purple tones)
                random.randint(5, 20),    # G: Ultra Low (Keeps it from looking muddy)
                random.randint(30, 60)    # B: High (Guarantees Blue/Midnight tint)
            )
        else:
            rand_bg = bg_color

        # --- sub-systems ---
        self.sound      = AudioLogger()
        self.particles  = ParticleSystem()
        self.shake      = ScreenShake()
        self.background = DynamicBackground(width, height, color=rand_bg)
        self.bloom      = BloomEffect(width, height)
        self.flash      = FlashEffect()

        # --- global frame counter (never resets) ---
        self.frame_count = 0

        # --- phase / round bookkeeping ---
        self.phase            = PHASE_HOOK
        self.phase_frame      = 0          # frames spent in current phase
        self.current_round    = 0          # 0-based index into ROUND_CONFIGS
        self.round_frame      = 0          # frames since this round started playing
        self.round_winner     = None       # name of the winner of current round

        # --- persistent scoreboard (dynamic based on rivals or default)
        if rivals:
            # Use rival names for scoreboard
            self.scores = {rival[0]: 0 for rival in rivals}
        else:
            # Default scoreboard
            self.scores = {"RED": 0, "BLUE": 0, "GREEN": 0}

        # --- live round objects (rebuilt each round)
        self.circles = []
        self.balls   = []

        # --- hook text
        self.hook_text = random.choice(HOOK_TEXTS)

        # --- sizes
        self.circle_thickness = int(height * CIRCLE_THICKNESS_RATIO)
        self.circle_spacing   = int(height * CIRCLE_SPACING_RATIO)
        self.base_radius      = int(height * BASE_RADIUS_RATIO)
        self.ball_radius      = int(height * BALL_RADIUS_RATIO)

        # pre-spawn round 1 objects so the hook phase can show the arena
        self._spawn_round(0)

    # ================================================================
    # PUBLIC QUERY
    # ================================================================
    def is_done(self):
        return self.phase == PHASE_DONE

    # ================================================================
    # ROUND SPAWNING
    # ================================================================
    def _spawn_round(self, round_idx):
        """Create circles + balls for the given round config."""
        cfg = ROUND_CONFIGS[round_idx]
        
        # 1. Generate the random color
        new_bg_color = (
            random.randint(5, 25),    # R: Very Low (Red adds Purple tones)
            random.randint(5, 20),    # G: Ultra Low (Keeps it from looking muddy)
            random.randint(30, 60)    # B: High (Guarantees Blue/Midnight tint)
        )

        # -----------------------------------------------------------
        # THIS WAS MISSING: You must actually apply the color!
        # -----------------------------------------------------------
        if hasattr(self, 'background'):
            self.background.base_color = new_bg_color
        # -----------------------------------------------------------

        # --- circles ---
        self.circles = []
        n = cfg["num_circles"]
        for i in range(n):
            radius = self.base_radius + (n - i) * (self.circle_thickness + self.circle_spacing)
            self.circles.append(Circle(
                radius,
                gap_angle      = random.uniform(0, 360),
                color          = CIRCLE_COLORS[i % len(CIRCLE_COLORS)],
                thickness      = self.circle_thickness,
                rotation_speed = cfg["rotation_speed"],
                gap_size       = cfg["gap_size"],
            ))

        # --- balls (with theme support) ---
        self.balls = []
        nb = cfg["num_balls"]
        
        if self.rivals and len(self.rivals) >= nb:
            # THEME MODE: Use rivals from theme database
            for i in range(nb):
                rival_name, rival_color, rival_search = self.rivals[i]
                
                angle  = (i * 2 * math.pi / nb) + random.uniform(-0.2, 0.2)
                offset = 55
                x = self.center[0] + math.cos(angle) * offset
                y = self.center[1] + math.sin(angle) * offset
                
                self.balls.append(Ball(
                    x, y, 
                    rival_color,        # RGB color
                    rival_name,         # Team name
                    self.ball_radius,
                    self.height * BALL_SPEED_RATIO,
                    theme=self.theme_name,
                    rival_name=rival_name,
                    search_query=rival_search
                ))
        else:
            # LEGACY MODE
            for i in range(nb):
                team = TEAMS[i]
                col  = COLOR_PALETTE[team["color_idx"]]
                
                angle  = (i * 2 * math.pi / nb) + random.uniform(-0.2, 0.2)
                offset = 55
                x = self.center[0] + math.cos(angle) * offset
                y = self.center[1] + math.sin(angle) * offset
                
                self.balls.append(Ball(
                    x, y, col, team["name"],
                    self.ball_radius,
                    self.height * BALL_SPEED_RATIO
                ))

        self.round_winner = None
        self.round_frame  = 0
        
    # ================================================================
    # UPDATE  - call once per frame
    # ================================================================
    def update(self):
        self.frame_count += 1
        self.phase_frame += 1
        self.background.update()
        self.shake.update()
        t = self.frame_count / FPS          # seconds (for audio timestamps)

        if   self.phase == PHASE_HOOK:         self._update_hook(t)
        elif self.phase == PHASE_PLAYING:      self._update_playing(t)
        elif self.phase == PHASE_WINNER_PAUSE: self._update_winner_pause(t)
        elif self.phase == PHASE_FLASH:        self._update_flash(t)
        elif self.phase == PHASE_ENDCARD:      self._update_endcard(t)

        self.particles.update()

    # ---- HOOK phase (arena reveal) ------------------------------------
    def _update_hook(self, t):
        # circles rotate gently, no collision logic
        for c in self.circles:
            c.update()
        # balls drift slowly from center (visual only - no collisions)
        for b in self.balls:
            b.pos[0] += b.vel[0] * 0.15
            b.pos[1] += b.vel[1] * 0.15
            b.trail.append(list(b.pos))
            if len(b.trail) > TRAIL_LENGTH:
                b.trail.pop(0)

        if self.phase_frame >= HOOK_DURATION_FRAMES:
            self._enter_phase(PHASE_PLAYING)
            # re-spawn so balls start from clean positions
            self._spawn_round(self.current_round)

    # ---- PLAYING phase (live round) -----------------------------------
    def _update_playing(self, t):
        self.round_frame += 1
        cfg = ROUND_CONFIGS[self.current_round]

        # update circles
        for c in self.circles:
            if c.alive:
                c.update()

        # update balls + collisions
        for ball in self.balls:
            ball.move()
            if not ball.escaped:
                self._process_collisions(ball, t)

        # --- check for winner: first ball to escape all destroyed circles ---
        for ball in self.balls:
            if ball.escaped:
                continue
            dx   = ball.pos[0] - self.center[0]
            dy   = ball.pos[1] - self.center[1]
            dist = math.hypot(dx, dy)
            n    = cfg["num_circles"]
            max_r = self.base_radius + n * (self.circle_thickness + self.circle_spacing)
            if dist > max_r + 100 and all(not c.alive for c in self.circles):
                ball.escaped    = True
                self.round_winner = ball.team_name
                self.scores[ball.team_name] += 1
                self.sound.play_win(current_time=t)
                self.particles.add_confetti(self.center, CONFETTI_COUNT)
                self.shake.add_trauma(0.4)
                break

        # --- SUDDEN DEATH: round only ends when a winner is found ---
        # No timeout - rounds continue until a ball escapes!
        if self.round_winner:
            # winner found -> go to pause
            self._enter_phase(PHASE_WINNER_PAUSE)

    # ---- WINNER_PAUSE (celebration hold) -----------------------------
    def _update_winner_pause(self, t):
        cfg = ROUND_CONFIGS[self.current_round]
        pause_frames = int(cfg["pause_after"] * FPS)

        # keep dropping confetti during celebration
        if self.phase_frame % 3 == 0:
            self.particles.add_confetti(
                (random.randint(100, self.width - 100), 0), 5)

        if self.phase_frame >= max(pause_frames, int(FPS * 0.5)):  # minimum 0.5s pause
            # advance to next round or end
            if self.current_round < NUM_ROUNDS - 1:
                self._enter_phase(PHASE_FLASH)
                self.flash.trigger(0.95)
            else:
                # finale just ended -> end-card
                self._enter_phase(PHASE_ENDCARD)

    # ---- FLASH (transition between rounds) ---------------------------
    def _update_flash(self, t):
        if self.phase_frame >= ROUND_FLASH_FRAMES:
            self.current_round += 1
            self._spawn_round(self.current_round)
            self._enter_phase(PHASE_PLAYING)

    # ---- ENDCARD ------------------------------------------------------
    def _update_endcard(self, t):
        # gentle particle rain
        if self.phase_frame % 2 == 0:
            self.particles.add_confetti(
                (random.randint(50, self.width - 50), 0), 4)

        if self.phase_frame >= ENDCARD_DURATION_FRAMES:
            self.phase = PHASE_DONE

    # ================================================================
    # PHASE TRANSITION helper
    # ================================================================
    def _enter_phase(self, new_phase):
        self.phase       = new_phase
        self.phase_frame = 0

    # ================================================================
    # COLLISION
    # ================================================================
    def _process_collisions(self, ball, t):
        for i in range(len(self.circles) - 1, -1, -1):
            circle = self.circles[i]
            if not circle.alive or ball.is_on_cooldown(i):
                continue
            result = circle.check_collision(ball.pos, ball.radius,
                                            self.center, self.frame_count)
            if result == 'gap':
                broke = circle.take_damage()
                self.sound.play_break(i, current_time=t)
                burst = EXPLOSION_PARTICLES if broke else EXPLOSION_PARTICLES // 2
                col   = circle.base_color if broke else circle.color
                self.particles.add_explosion(ball.pos, col, burst, 1.0)
                self.shake.add_trauma(0.10 if broke else 0.05)
                ball.bounce_count.pop(i, None)
                ball.reset_speed()
                return True
            elif result == 'bounce':
                nx, ny = circle.get_bounce_normal(ball.pos, self.center)
                ball.bounce(nx, ny)
                ball.pos[0] += nx * COLLISION_PUSHBACK
                ball.pos[1] += ny * COLLISION_PUSHBACK
                ball.record_bounce(i)
                self.sound.play_bounce(ball.get_speed_ratio(), current_time=t)
                self.shake.add_trauma(0.04 * ball.get_speed_ratio())
                return True
        return False

    # ================================================================
    # DRAW  - call once per frame; mutates the BGR frame in-place
    # ================================================================
    def draw(self, frame):
        # background
        self.background.draw(frame)

        if self.phase == PHASE_ENDCARD:
            self._draw_endcard(frame)
        else:
            self._draw_arena(frame)
            self._draw_scoreboard(frame)

            if self.phase == PHASE_HOOK:
                self._draw_hook_overlay(frame)

            if self.phase in (PHASE_PLAYING, PHASE_WINNER_PAUSE):
                self._draw_round_label(frame)

            if self.phase == PHASE_WINNER_PAUSE and self.round_winner:
                self._draw_winner_banner(frame)

        # particles always on top
        self.particles.draw(frame)

        # bloom
        self.bloom.apply(frame)

        # flash overlay (on top of everything including bloom)
        self.flash.apply(frame)

    # ================================================================
    # DRAW HELPERS
    # ================================================================

    # ---- arena (circles + balls) --------------------------------------
    def _draw_arena(self, frame):
        # centre dot
        cv2.circle(frame, self.center, max(1, int(self.height * 0.008)),
                   (60, 40, 40), -1)
        # rings outermost-first
        for c in reversed(self.circles):
            c.draw(frame, self.center)
        # balls
        for b in self.balls:
            b.draw(frame, self.particles)

    # ---- scoreboard (top strip) ---------------------------------------
    def _draw_scoreboard(self, frame):
        """Dynamic scoreboard showing active teams from theme or default."""
        strip_h = int(self.height * 0.065)
        # dark semi-transparent bar
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (self.width, strip_h), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.75, frame, 0.25, 0, dst=frame)

        # Get active teams from current balls (supports both theme and legacy mode)
        active_teams = []
        for ball in self.balls:
            active_teams.append({
                'name': ball.team_name,
                'color': ball.base_color,  # RGB color
            })

        n   = len(active_teams)
        if n == 0:
            return
        
        seg = self.width // n           # width per team column

        for i, team in enumerate(active_teams):
            col_bgr = _bgr(team['color'])
            x_center = seg * i + seg // 2
            score    = self.scores.get(team['name'], 0)

            # team name (auto-scale for long names)
            name_txt = team['name']
            scale = 0.75 if len(name_txt) <= 10 else 0.55
            nw, nh   = _tsz(name_txt, scale, 2)
            cv2.putText(frame, name_txt,
                        (x_center - nw // 2, int(strip_h * 0.42)),
                        FONT, scale, col_bgr, 2, cv2.LINE_AA)

            # score (big)
            s_txt = str(score)
            sw, sh = _tsz(s_txt, 1.5, 3)
            cv2.putText(frame, s_txt,
                        (x_center - sw // 2, int(strip_h * 0.88)),
                        FONT, 1.5, (255, 255, 255), 3, cv2.LINE_AA)

            # vertical divider (not after the last)
            if i < n - 1:
                cv2.line(frame,
                         (seg * (i + 1), 4),
                         (seg * (i + 1), strip_h - 4),
                         (80, 80, 80), 1)

    # ---- hook overlay (intro text) ------------------------------------
    def _draw_hook_overlay(self, frame):
        # fade-in over first half of hook
        alpha = min(1.0, self.phase_frame / max(1, HOOK_DURATION_FRAMES * 0.4))

        txt   = self.hook_text
        scale = 1.3
        thick = 3
        w, h  = _tsz(txt, scale, thick)
        cx    = self.width  // 2
        ty    = int(self.height * 0.50)    # dead center vertically

        # pill background
        pad  = 22
        over = frame.copy()
        cv2.rectangle(over,
                      (cx - w // 2 - pad, ty - h - pad),
                      (cx + w // 2 + pad, ty + pad + 4),
                      (0, 0, 0), -1)
        cv2.addWeighted(over, alpha * 0.78, frame, 1.0 - alpha * 0.78, 0, dst=frame)

        col = (int(255 * alpha), int(255 * alpha), int(255 * alpha))
        cv2.putText(frame, txt, (cx - w // 2, ty),
                    FONT, scale, col, thick, cv2.LINE_AA)

    # ---- round label ("Round N" / "FINALE") ---------------------------
    def _draw_round_label(self, frame):
        is_finale = (self.current_round == NUM_ROUNDS - 1)

        if is_finale:
            txt   = "FINALE"
            scale = 1.8
            thick = 4
            col   = (0, 100, 255)    # BGR orange-red
        else:
            txt   = f"Round {self.current_round + 1}"
            scale = 1.0
            thick = 2
            col   = (200, 200, 200)

        w, h = _tsz(txt, scale, thick)
        # bottom-left corner (safe from scoreboard)
        x = 18
        y = self.height - 30
        cv2.putText(frame, txt, (x, y), FONT, scale, col, thick, cv2.LINE_AA)

    # ---- winner banner (center of screen during pause) ---------------
    def _draw_winner_banner(self, frame):
        # pulsing glow
        pulse = abs(math.sin(self.frame_count * 0.12)) * 0.25 + 0.75

        # Find the winner's color from active balls
        team_col = COLOR_PALETTE[0]   # default red
        for ball in self.balls:
            if ball.team_name == self.round_winner:
                team_col = ball.base_color
                break

        # shadow
        txt   = f"{self.round_winner} WINS!"
        scale = 2.2
        thick = 5
        w, h  = _tsz(txt, scale, thick)
        cx    = self.width  // 2
        cy    = self.height // 2 + 40

        cv2.putText(frame, txt, (cx - w // 2 + 3, cy + 3),
                    FONT, scale, (0, 0, 0), thick + 2, cv2.LINE_AA)
        # main text
        col = _bgr(tuple(min(255, int(c * pulse)) for c in team_col))
        cv2.putText(frame, txt, (cx - w // 2, cy),
                    FONT, scale, col, thick, cv2.LINE_AA)

    # ---- end-card (champion screen) -----------------------------------
    def _draw_endcard(self, frame):
        # darken everything
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (self.width, self.height),
                      (10, 8, 8), -1)
        cv2.addWeighted(overlay, 0.82, frame, 0.18, 0, dst=frame)

        cx = self.width  // 2
        cy = self.height // 2

        # --- "CHAMPION" title ---
        pulse = abs(math.sin(self.frame_count * 0.1)) * 30
        title = "CHAMPION"
        tw, th = _tsz(title, 2.8, 6)
        col = (int(60 + pulse), int(180 + pulse), int(255))   # BGR cyan-ish
        cv2.putText(frame, title, (cx - tw // 2, cy - 80),
                    FONT, 2.8, col, 6, cv2.LINE_AA)

        # --- find overall winner ---
        winner_name  = max(self.scores, key=self.scores.get)
        winner_score = self.scores[winner_name]
        
        # Find winner's color from active balls
        team_col = COLOR_PALETTE[0]  # default
        for ball in self.balls:
            if ball.team_name == winner_name:
                team_col = ball.base_color
                break

        # big winner name
        w, h = _tsz(winner_name, 3.0, 7)
        cv2.putText(frame, winner_name, (cx - w // 2, cy + 20),
                    FONT, 3.0, _bgr(team_col), 7, cv2.LINE_AA)

        num_balls = ROUND_CONFIGS[-1]["num_balls"]
        if self.rivals:
            # Theme Mode: Get names from the current rivals list
            display_names = [r[0] for r in self.rivals[:num_balls]]
        else:
            # Legacy Mode: Get names from default TEAMS
            display_names = [t["name"] for t in TEAMS[:num_balls]]

        tally = "  |  ".join(f"{name} {self.scores.get(name, 0)}"
                             for name in display_names)
                             
        tw2, _ = _tsz(tally, 0.9, 2)
        cv2.putText(frame, tally, (cx - tw2 // 2, cy + 90),
                    FONT, 0.9, (180, 180, 180), 2, cv2.LINE_AA)