"""
Physics and collision handling - pure NumPy / OpenCV rendering.
Updated to work with the new lazy-loading texture system.
"""
import math
import random
import cv2
import numpy as np
from config import *


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _rgb_to_bgr(rgb):
    """(R,G,B) -> (B,G,R) for OpenCV."""
    return (int(rgb[2]), int(rgb[1]), int(rgb[0]))


# ---------------------------------------------------------------------------
# Circle - rotating ring with a gap and an HP bar
# ---------------------------------------------------------------------------
class Circle:
    def __init__(self, radius, gap_angle, color, thickness,
                 rotation_speed=None, gap_size=None):
        self.radius        = radius
        self.gap_angle     = gap_angle
        self.gap_size      = gap_size if gap_size else 55
        self.base_color    = color          # RGB tuple
        self.color         = color
        self.thickness     = thickness
        self.rotation      = 0.0
        self.rotation_speed= rotation_speed if rotation_speed else 0.8
        self.alive         = True
        self.max_hp        = CIRCLE_HP
        self.hp            = CIRCLE_HP
        self.last_collision_frame = -999

    # -- state ----------------------------------------------------------
    def update(self):
        self.rotation += self.rotation_speed
        if self.rotation >= 360:
            self.rotation -= 360

    def take_damage(self):
        self.hp -= 1
        if self.hp <= 0:
            self.alive = False
            return True          # circle destroyed
        fade = self.hp / self.max_hp
        self.color = tuple(int(c * fade) for c in self.base_color)
        return False

    # -- geometry -------------------------------------------------------
    @staticmethod
    def _norm(angle):
        """Clamp angle into [0, 360)."""
        return angle % 360

    def is_in_gap(self, ball_angle):
        ball_angle = self._norm(ball_angle)
        gap_start  = self._norm(self.gap_angle + self.rotation)
        gap_end    = self._norm(gap_start + self.gap_size)
        if gap_start < gap_end:
            return gap_start <= ball_angle <= gap_end
        return ball_angle >= gap_start or ball_angle <= gap_end

    # -- collision ------------------------------------------------------
    def check_collision(self, ball_pos, ball_radius, center, frame_count):
        """Returns 'gap', 'bounce', or None."""
        if frame_count - self.last_collision_frame < 3:
            return None

        dx   = ball_pos[0] - center[0]
        dy   = ball_pos[1] - center[1]
        dist = math.hypot(dx, dy)

        inner = self.radius - self.thickness
        outer = self.radius
        margin = ball_radius * 1.2

        at_inner = inner - margin < dist < inner + margin
        at_outer = outer - margin < dist < outer + margin

        if at_inner or at_outer:
            ball_angle = self._norm(math.degrees(math.atan2(dy, dx)))
            if self.is_in_gap(ball_angle):
                return 'gap'
            self.last_collision_frame = frame_count
            return 'bounce'
        return None

    def get_bounce_normal(self, ball_pos, center):
        dx   = ball_pos[0] - center[0]
        dy   = ball_pos[1] - center[1]
        dist = math.hypot(dx, dy)
        return (dx / dist, dy / dist) if dist > 0 else (0, -1)

    # -- rendering (OpenCV) ---------------------------------------------
    def draw(self, frame, center):
        """Draw the ring onto a BGR numpy array *frame*."""
        if not self.alive:
            return

        color_bgr = _rgb_to_bgr(self.color)
        NUM_SEG   = 120
        seg_angle = 2 * math.pi / NUM_SEG

        cx, cy = center

        for i in range(NUM_SEG):
            a1 = i * seg_angle
            a2 = (i + 1) * seg_angle
            mid_deg = self._norm(math.degrees((a1 + a2) * 0.5))
            if self.is_in_gap(mid_deg):
                continue

            # four corners of the arc segment (inner/outer × start/end)
            cos1, sin1 = math.cos(a1), math.sin(a1)
            cos2, sin2 = math.cos(a2), math.sin(a2)
            r_out = self.radius
            r_in  = self.radius - self.thickness

            pts = np.array([
                [cx + r_in  * cos1, cy + r_in  * sin1],
                [cx + r_out * cos1, cy + r_out * sin1],
                [cx + r_out * cos2, cy + r_out * sin2],
                [cx + r_in  * cos2, cy + r_in  * sin2],
            ], dtype=np.int32)

            cv2.fillPoly(frame, [pts], color_bgr)


# ---------------------------------------------------------------------------
# Ball - bouncing dot with trail, speed-boost, and escape detection
# ---------------------------------------------------------------------------
class Ball:
    def __init__(self, x, y, color, team_name, radius, speed, fixed_angle=None, 
                 theme=None, rival_name=None, search_query=None):
        """
        Parameters
        ----------
        theme        : str (e.g., "POLITICS")
        rival_name   : str (e.g., "Donald Trump")  
        search_query : str (e.g., "Donald Trump face portrait")
        """
        self.pos       = [float(x), float(y)]
        self.base_color= color          # RGB
        self.color     = color
        self.team_name = team_name
        self.radius    = radius
        self.base_speed= speed

        # NEW LAZY LOADING TEXTURE SUPPORT
        self.theme         = theme              # e.g., "POLITICS"
        self.rival_name    = rival_name or team_name  # Use rival_name if provided, else team_name
        self.search_query  = search_query       # e.g., "Donald Trump face portrait"
        self.texture       = None               # Will be loaded on first draw
        self.texture_loaded= False              # Flag to avoid repeated load attempts

        angle = fixed_angle if fixed_angle is not None else random.uniform(0, 2*math.pi)
        self.vel = [math.cos(angle)*speed, math.sin(angle)*speed]

        self.trail             = []
        self.max_trail_length  = TRAIL_LENGTH
        self.bounce_count      = {}
        self.speed_boosted     = False
        self.escaped           = False
        self.speed_multiplier  = 1.0
        self.last_bounce_circle= -1
        self.bounce_cooldown   = 0
        self.collision_cooldowns = {}

    # -- movement -------------------------------------------------------
    def move(self):
        if self.speed_multiplier != 1.0:
            spd = math.hypot(*self.vel)
            if spd > 0:
                tgt = self.base_speed * self.speed_multiplier
                s   = tgt / spd
                self.vel[0] *= s
                self.vel[1] *= s

        self.pos[0] += self.vel[0]
        self.pos[1] += self.vel[1]

        spd = math.hypot(*self.vel)
        if spd > MAX_BALL_SPEED:
            s = MAX_BALL_SPEED / spd
            self.vel[0] *= s
            self.vel[1] *= s

        self.trail.append(list(self.pos))
        if len(self.trail) > self.max_trail_length:
            self.trail.pop(0)

        if self.bounce_cooldown > 0:
            self.bounce_cooldown -= 1
        for k in list(self.collision_cooldowns):
            self.collision_cooldowns[k] -= 1
            if self.collision_cooldowns[k] <= 0:
                del self.collision_cooldowns[k]

    def is_on_cooldown(self, circle_index):
        return self.collision_cooldowns.get(circle_index, 0) > 0

    # -- bounce / boost -------------------------------------------------
    def bounce(self, nx, ny):
        dot = self.vel[0]*nx + self.vel[1]*ny
        self.vel[0] -= 2*dot*nx
        self.vel[1] -= 2*dot*ny
        # tiny random jitter to break perfect loops
        noise = random.uniform(-0.05, 0.05)
        c, s  = math.cos(noise), math.sin(noise)
        vx, vy = self.vel
        self.vel[0] = vx*c - vy*s
        self.vel[1] = vx*s + vy*c

    def record_bounce(self, circle_index):
        self.bounce_count[circle_index] = self.bounce_count.get(circle_index, 0) + 1
        if self.bounce_count[circle_index] >= 5 and not self.speed_boosted:
            self.apply_speed_boost()
        self.last_bounce_circle = circle_index
        self.bounce_cooldown    = 5
        self.collision_cooldowns[circle_index] = COLLISION_COOLDOWN

    def apply_speed_boost(self):
        self.speed_boosted = True
        spd = math.hypot(*self.vel)
        if spd > 0:
            f = self.base_speed * 1.4 / spd
            self.vel[0] *= f
            self.vel[1] *= f
        self.color = (255, 220, 80)

    def reset_speed(self):
        if self.speed_boosted:
            self.speed_boosted = False
            spd = math.hypot(*self.vel)
            if spd > 0:
                f = self.base_speed / spd
                self.vel[0] *= f
                self.vel[1] *= f
            self.color = self.base_color

    def get_speed_ratio(self):
        spd = math.hypot(*self.vel)
        return min(2.0, spd / self.base_speed) if self.base_speed > 0 else 1.0

    # -- rendering (OpenCV) ---------------------------------------------
    def draw(self, frame, particle_system):
        """Draw ball + trail with NEON GLOW using layer blending, with optional texture overlay."""
        
        # 1. DRAW THE TRAIL with transparent neon glow effect
        trail_col = self.color if not self.speed_boosted else (255, 255, 150)
        
        # Create a separate overlay for the trail (this is the key to transparency)
        overlay = frame.copy()
        
        for i, pos in enumerate(self.trail):
            # Calculate fade (alpha) - newer trail segments are brighter
            alpha = (i + 1) / max(len(self.trail), 1)
            # Make the trail slightly smaller as it fades
            sz = max(1, int(self.radius * alpha * 0.8))
            
            # Convert color to BGR for OpenCV
            c_bgr = _rgb_to_bgr(trail_col)
            
            # Draw on the OVERLAY, not directly on the frame
            cv2.circle(overlay, (int(pos[0]), int(pos[1])), sz, c_bgr, -1)
            
            # Add glow particles for extra visual juice
            if i % 2 == 0:  # Optimize particle count
                particle_system.add_trail(pos, trail_col, 0.5)

        # NEON GLOW FIX: Blend the trail overlay onto the main frame at 40% opacity
        # This creates the transparent glass/neon light effect instead of solid paint
        cv2.addWeighted(overlay, 0.4, frame, 0.6, 0, frame)

        # ===================================================================
        # 2. LAZY TEXTURE LOADING: Load texture on first draw
        # ===================================================================
        if self.theme and self.rival_name and self.search_query and not self.texture_loaded:
            try:
                from texture_manager import get_texture_manager
                tm = get_texture_manager()
                diameter = int(self.radius * 2)

                # NEW SIGNATURE: pass name, search_query, and color for fallback
                self.texture = tm.load_texture(
                    category=self.theme,
                    name=self.rival_name,
                    search_query=self.search_query,
                    color=self.base_color,
                    ball_diameter=diameter
                )
            except (ImportError, Exception):
                # Fall back to colored circle if texture loading fails
                self.texture = None
            self.texture_loaded = True
        
        # ===================================================================
        # 3. DRAW THE MAIN BALL (Texture or Colored Circle)
        # ===================================================================
        if self.texture is not None:
            # TEXTURE MODE: Overlay circular image
            try:
                from texture_manager import get_texture_manager
                tm = get_texture_manager()
            except (ImportError, Exception):
                # Fall back to colored circle mode
                self.texture = None
            tm.overlay_texture(frame, self.texture, int(self.pos[0]), int(self.pos[1]))
        else:
            # FALLBACK MODE: Standard colored circle
            cv2.circle(frame,
                    (int(self.pos[0]), int(self.pos[1])),
                    int(self.radius),
                    _rgb_to_bgr(self.color),
                    -1)
                    
            # 4. DRAW HIGHLIGHT (Shiny white dot for 3D effect) - only for colored circles
            offset = int(self.radius * 0.3)
            cv2.circle(frame,
                    (int(self.pos[0] - offset), int(self.pos[1] - offset)),
                    int(self.radius * 0.3),
                    (255, 255, 255),
                    -1)