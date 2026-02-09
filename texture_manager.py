"""
texture_manager.py - Rival Icon/Logo Texture Manager (Production-Ready)

Fetches and caches rival icons/logos for marble race visualization.
Uses DuckDuckGo image search with intelligent caching.

FEATURES:
- Lazy loading (fetch only when needed)
- Persistent disk cache
- Circular mask for marble balls
- Fallback to colored circles
- Safe image validation
"""

import os
import requests
import hashlib
from typing import Optional, Tuple
from PIL import Image, ImageDraw
import numpy as np
import cv2
from production_config import STORY_ASSETS_DIR

# Singleton instance
_texture_manager_instance = None


class TextureManager:
    """
    Manages rival textures (icons/logos) for marble balls.
    """

    def __init__(self):
        self.cache_dir = os.path.join(STORY_ASSETS_DIR, "rival_textures")
        os.makedirs(self.cache_dir, exist_ok=True)

        # Check if ddgs is available
        self.ddgs_available = False
        try:
            from ddgs import DDGS
            with DDGS() as ddgs:
                list(ddgs.images("test", max_results=1))
            self.ddgs_available = True
            print("  [textures] OK ddgs available for icon fetching")
        except (ImportError, Exception):
            print("  [textures] WARN ddgs not available, using fallbacks")

    def load_texture(
        self,
        category: str,
        name: str,
        search_query: str,
        color: Tuple[int, int, int],
        ball_diameter: int
    ) -> Optional[np.ndarray]:
        """
        Load or fetch texture for a rival.

        Parameters
        ----------
        category : str
            Theme category (e.g., "FOOTBALL")
        name : str
            Rival name (e.g., "Barcelona")
        search_query : str
            Search query for finding icon (e.g., "Barcelona FC logo")
        color : Tuple[int, int, int]
            Fallback color if texture fails (RGB)
        ball_diameter : int
            Target diameter for the texture

        Returns
        -------
        Optional[np.ndarray]
            BGR image array (OpenCV format) or None for fallback
        """

        # Generate cache key
        cache_key = hashlib.md5(f"{category}_{name}_{ball_diameter}".encode()).hexdigest()
        cache_path = os.path.join(self.cache_dir, f"{cache_key}.png")

        # Check cache first
        if os.path.exists(cache_path):
            try:
                texture = cv2.imread(cache_path, cv2.IMREAD_UNCHANGED)
                if texture is not None and texture.shape[0] == ball_diameter:
                    return texture
            except Exception:
                pass

        # Not in cache - try to fetch
        if not self.ddgs_available:
            return None

        try:
            print(f"  [textures] Fetching icon: {name}")
            texture = self._fetch_and_prepare_icon(search_query, ball_diameter, color)

            if texture is not None:
                # Save to cache
                cv2.imwrite(cache_path, texture)
                print(f"  [textures] OK Cached: {name}")
                return texture

        except Exception as e:
            print(f"  [textures] Failed to fetch {name}: {e}")

        return None

    def _fetch_and_prepare_icon(
        self,
        search_query: str,
        diameter: int,
        fallback_color: Tuple[int, int, int]
    ) -> Optional[np.ndarray]:
        """
        Fetch icon from DuckDuckGo and prepare as circular texture.
        """

        from ddgs import DDGS

        try:
            with DDGS() as ddgs:
                results = list(ddgs.images(
                    query=f"{search_query} logo icon transparent",
                    max_results=5
                ))

                if not results:
                    return None

                # Try each result until we get a valid image
                for result in results:
                    try:
                        image_url = result.get('image')
                        if not image_url:
                            continue

                        # Download
                        response = requests.get(
                            image_url,
                            headers={'User-Agent': 'Mozilla/5.0'},
                            timeout=10
                        )

                        if response.status_code != 200:
                            continue

                        # Load image
                        from io import BytesIO
                        img = Image.open(BytesIO(response.content))

                        # Convert to RGBA
                        if img.mode != 'RGBA':
                            img = img.convert('RGBA')

                        # Validate size
                        if img.width < 100 or img.height < 100:
                            continue

                        # Prepare circular texture
                        texture = self._prepare_circular_texture(img, diameter, fallback_color)
                        if texture is not None:
                            return texture

                    except Exception:
                        continue

        except Exception:
            pass

        return None

    def _prepare_circular_texture(
        self,
        img: Image.Image,
        diameter: int,
        fallback_color: Tuple[int, int, int]
    ) -> Optional[np.ndarray]:
        """
        Convert image to circular texture with transparent background.
        """

        try:
            # Crop to square (center crop)
            width, height = img.size
            size = min(width, height)
            left = (width - size) // 2
            top = (height - size) // 2
            img = img.crop((left, top, left + size, top + size))

            # Resize to target diameter
            img = img.resize((diameter, diameter), Image.Resampling.LANCZOS)

            # Create circular mask
            mask = Image.new('L', (diameter, diameter), 0)
            draw = ImageDraw.Draw(mask)
            draw.ellipse((0, 0, diameter, diameter), fill=255)

            # Apply mask
            img.putalpha(mask)

            # Convert to OpenCV format (BGR + Alpha)
            img_array = np.array(img)

            # Convert RGBA to BGRA (OpenCV format)
            bgra = cv2.cvtColor(img_array, cv2.COLOR_RGBA2BGRA)

            return bgra

        except Exception:
            return None

    def overlay_texture(
        self,
        frame: np.ndarray,
        texture: np.ndarray,
        x: int,
        y: int
    ):
        """
        Overlay circular texture onto frame at position (x, y).

        Parameters
        ----------
        frame : np.ndarray
            Target frame (BGR format)
        texture : np.ndarray
            Circular texture with alpha channel (BGRA format)
        x, y : int
            Center position for the texture
        """

        if texture is None:
            return

        try:
            h, w = texture.shape[:2]
            radius = w // 2

            # Calculate overlay bounds
            y1 = max(0, y - radius)
            y2 = min(frame.shape[0], y + radius)
            x1 = max(0, x - radius)
            x2 = min(frame.shape[1], x + radius)

            # Calculate texture bounds
            ty1 = max(0, radius - y)
            ty2 = h - max(0, y + radius - frame.shape[0])
            tx1 = max(0, radius - x)
            tx2 = w - max(0, x + radius - frame.shape[1])

            # Skip if completely out of bounds
            if y1 >= y2 or x1 >= x2 or ty1 >= ty2 or tx1 >= tx2:
                return

            # Extract regions
            overlay_region = texture[ty1:ty2, tx1:tx2]
            frame_region = frame[y1:y2, x1:x2]

            # Handle alpha blending if texture has alpha channel
            if overlay_region.shape[2] == 4:
                # Extract alpha channel
                alpha = overlay_region[:, :, 3:4] / 255.0
                overlay_bgr = overlay_region[:, :, :3]

                # Alpha blending
                blended = (overlay_bgr * alpha + frame_region * (1 - alpha)).astype(np.uint8)
                frame[y1:y2, x1:x2] = blended
            else:
                # No alpha - direct overlay
                frame[y1:y2, x1:x2] = overlay_region

        except Exception as e:
            # Silently fail - fallback to colored circle
            pass


def get_texture_manager() -> TextureManager:
    """Get singleton texture manager instance."""
    global _texture_manager_instance
    if _texture_manager_instance is None:
        _texture_manager_instance = TextureManager()
    return _texture_manager_instance


# Test mode
if __name__ == "__main__":
    print("=" * 70)
    print("  TEXTURE MANAGER TEST")
    print("=" * 70)

    tm = get_texture_manager()

    # Test fetching a few icons
    test_rivals = [
        ("FOOTBALL", "Barcelona", "Barcelona FC logo", (220, 20, 60), 100),
        ("TECH_COMPANIES", "Apple", "Apple Inc logo", (100, 100, 100), 100),
        ("FAST_FOOD", "McDonald's", "McDonald's logo", (255, 199, 0), 100),
    ]

    for category, name, query, color, diameter in test_rivals:
        print(f"\nFetching: {name}")
        texture = tm.load_texture(category, name, query, color, diameter)

        if texture is not None:
            print(f"  OK Got texture: {texture.shape}")
        else:
            print(f"  WARN No texture, will use fallback color")

    print("\n" + "=" * 70)
    print("  TEST COMPLETE")
    print("=" * 70)
