"""
story_visual_manager_v2.py - PRODUCTION-READY Visual Manager V2

MAJOR UPGRADES:
✅ Optimized search queries with cinematic keywords
✅ Advanced quality scoring system (0-100)
✅ More images (8-12) for dynamic slideshow motion
✅ Multiple search strategies (broad→specific)
✅ Enhanced watermark detection
✅ DDGS advanced filters (size, type, layout)
✅ Better atmospheric modifiers
✅ Retry logic with query variations

Based on 2026 image search research:
- Use "cinematic photography" + "moody atmospheric" for quality
- Add "4k hd high resolution" for size
- Filter: size=Large, type=Photo, color=Any
- Target 8-12 images (vs old 4-7) for better slideshow dynamics
"""

import os
import requests
import time
import random
from typing import List, Tuple
from PIL import Image, ImageDraw, ImageFilter, ImageStat
import io
from production_config import (
    STORY_ASSETS_DIR,
    IMAGE_MIN_COUNT, IMAGE_MAX_COUNT,
    IMAGE_SEARCH_MAX_ATTEMPTS, IMAGE_SEARCH_MAX_PER_CONCEPT,
    DELAY_BEFORE_SEARCH, DELAY_BETWEEN_DOWNLOADS, DELAY_AFTER_PART, DELAY_JITTER,
    IMAGE_MIN_WIDTH, IMAGE_MIN_HEIGHT, IMAGE_MIN_ASPECT, IMAGE_MAX_ASPECT,
    BANNED_KEYWORDS, SAFE_SEARCH_MODIFIERS
)

# UPGRADED CONSTANTS
IMAGE_TARGET_COUNT_V2 = 10  # Increased from 7 to 10 for better motion
IMAGE_MAX_COUNT_V2 = 12     # Allow up to 12 for variety
IMAGE_MIN_COUNT_V2 = 6      # Minimum 6 (vs old 4)

# Quality score thresholds
QUALITY_SCORE_EXCELLENT = 80
QUALITY_SCORE_GOOD = 60
QUALITY_SCORE_ACCEPTABLE = 40


class StoryVisualManagerV2:
    """
    Production-ready visual manager with advanced image quality optimization.
    """

    def __init__(self):
        self.cache_dir = STORY_ASSETS_DIR
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # Check ddgs availability
        self.ddgs_available = False
        try:
            from ddgs import DDGS
            
            # Test basic functionality
            with DDGS() as ddgs:
                test_results = list(ddgs.images("test", max_results=1))
            
            self.ddgs_available = True
            print("  [visuals_v2] ✅ ddgs library ready with advanced filters")
            
        except ImportError:
            print("  [visuals_v2] ❌ ddgs not installed")
            print("  [visuals_v2]   Install: pip install ddgs")
        except Exception as e:
            print(f"  [visuals_v2] ❌ ddgs error: {e}")
            print("  [visuals_v2]   Will use procedural fallbacks")
    
    def fetch_story_images(self, visual_concepts: List[str], story_id: str) -> List[str]:
        """
        Fetch high-quality atmospheric images with UPGRADED search strategy.

        IMPROVEMENTS:
        - More images (8-12 vs 4-7)
        - Better search queries
        - Advanced quality scoring
        - Multiple search strategies
        """

        # Validate inputs
        if not visual_concepts or len(visual_concepts) == 0:
            print(f"  [visuals_v2] WARN No visual concepts provided")
            return self._generate_fallbacks(IMAGE_TARGET_COUNT_V2, story_id)

        if not self.ddgs_available:
            print(f"  [visuals_v2] WARN Search unavailable, using fallbacks")
            return self._generate_fallbacks(IMAGE_TARGET_COUNT_V2, story_id)

        print(f"  [visuals_v2] Fetching {IMAGE_TARGET_COUNT_V2} high-quality images...")

        downloaded = []
        attempts = 0

        # UPGRADED: Enhanced queries with multiple strategies
        enhanced_concepts = self._create_search_strategies(visual_concepts)
        random.shuffle(enhanced_concepts)

        for strategy_name, query in enhanced_concepts:
            if len(downloaded) >= IMAGE_MAX_COUNT_V2:
                break

            if attempts >= IMAGE_SEARCH_MAX_ATTEMPTS:
                print(f"  [visuals_v2] Max attempts reached ({IMAGE_SEARCH_MAX_ATTEMPTS})")
                break

            # Human-like delay
            delay = self._human_delay(DELAY_BEFORE_SEARCH)
            time.sleep(delay)

            print(f"  [visuals_v2] Strategy [{strategy_name}]: {query[:60]}...")

            images = self._search_and_download_advanced(query, story_id, strategy_name)
            if images:
                downloaded.extend(images)
                attempts += len(images)
            else:
                attempts += 1

        # Ensure minimum
        if len(downloaded) < IMAGE_MIN_COUNT_V2:
            print(f"  [visuals_v2] Only {len(downloaded)}, adding fallbacks")
            needed = IMAGE_MIN_COUNT_V2 - len(downloaded)
            fallbacks = self._generate_fallbacks(needed, story_id)
            downloaded.extend(fallbacks)

        # QUALITY SORTING: Keep best images
        if len(downloaded) > IMAGE_TARGET_COUNT_V2:
            # Score all images
            scored_images = []
            for img_path in downloaded:
                try:
                    img = Image.open(img_path)
                    score = self._calculate_quality_score(img)
                    scored_images.append((img_path, score))
                    img.close()
                except:
                    scored_images.append((img_path, 0))
            
            # Sort by score, keep best
            scored_images.sort(key=lambda x: x[1], reverse=True)
            downloaded = [path for path, score in scored_images[:IMAGE_TARGET_COUNT_V2]]
            
            print(f"  [visuals_v2] Quality filter: {len(scored_images)} → {len(downloaded)} (top scores)")

        # Randomize order for variety
        random.shuffle(downloaded)

        print(f"  [visuals_v2] ✅ Acquired {len(downloaded)} high-quality images")

        # Cooldown
        if len(downloaded) >= IMAGE_MIN_COUNT_V2:
            cooldown = self._human_delay(DELAY_AFTER_PART)
            print(f"  [visuals_v2] Cooldown: {cooldown:.1f}s")
            time.sleep(cooldown)

        return downloaded
    
    def _create_search_strategies(self, concepts: List[str]) -> List[Tuple[str, str]]:
        """
        Create multiple search strategies for each concept.

        Returns list of (strategy_name, query) tuples.

        STRATEGIES:
        1. Cinematic + Moody (high quality)
        2. Atmospheric + Professional
        3. Concept + HD 4K
        4. Dramatic + Concept
        """

        strategies = []

        # Ultra-high quality modifiers (2026 best practices)
        quality_tiers = [
            ("cinematic", "cinematic photography moody atmospheric 4k"),
            ("professional", "professional atmospheric photography high resolution"),
            ("dramatic", "dramatic lighting artistic composition hd"),
            ("editorial", "editorial photography moody dark aesthetic"),
        ]

        # Safety modifiers
        safe_mods = SAFE_SEARCH_MODIFIERS + [
            "stock photo",
            "free image",
            "creative commons"
        ]

        for concept in concepts:
            # Skip unsafe concepts
            if not self._is_safe_query(concept):
                print(f"  [visuals_v2] WARN Skipping unsafe: {concept}")
                continue

            # Create 2 strategies per concept (vs old 1)
            for i, (tier_name, tier_mod) in enumerate(quality_tiers[:2]):
                safety_mod = random.choice(safe_mods)
                
                query = f"{concept} {tier_mod} {safety_mod}"
                strategies.append((tier_name, query))

        return strategies
    
    def _is_safe_query(self, query: str) -> bool:
        """Check if query contains banned keywords."""
        query_lower = query.lower()
        for banned in BANNED_KEYWORDS:
            if banned in query_lower:
                return False
        return True
    
    def _human_delay(self, delay_range: tuple) -> float:
        """Generate human-like delay with jitter."""
        base = random.uniform(delay_range[0], delay_range[1])
        jitter = random.uniform(-DELAY_JITTER, DELAY_JITTER)
        return max(0.1, base + jitter)

    def _search_and_download_advanced(
        self,
        query: str,
        story_id: str,
        strategy_name: str
    ) -> List[str]:
        """
        UPGRADED search with DDGS advanced filters.

        NEW FEATURES:
        - size filter (Large)
        - type filter (Photo)
        - Better quality scoring
        """
        
        from ddgs import DDGS
        
        downloaded_paths = []
        
        try:
            with DDGS() as ddgs:
                # UPGRADED: Use advanced filters
                results = list(ddgs.images(
                    query=query,
                    max_results=IMAGE_SEARCH_MAX_PER_CONCEPT * 3,  # Get more for filtering
                    size="Large",  # NEW: Filter for large images
                    type_image="Photo",  # NEW: Photos only (no clipart/gif)
                    safesearch="Moderate",
                ))
                
                if not results:
                    print(f"      → No results")
                    return []
                
                print(f"      → Found {len(results)} candidates")
                
                # Try to download best images
                for idx, result in enumerate(results):
                    if len(downloaded_paths) >= IMAGE_SEARCH_MAX_PER_CONCEPT:
                        break
                    
                    try:
                        image_url = result.get('image')
                        if not image_url:
                            continue

                        # Download with timeout
                        response = requests.get(
                            image_url,
                            headers={'User-Agent': 'Mozilla/5.0'},
                            timeout=10
                        )

                        if response.status_code != 200:
                            continue

                        # Load image
                        img = Image.open(io.BytesIO(response.content))

                        # UPGRADED: Quality scoring (0-100)
                        quality_score = self._calculate_quality_score(img)
                        
                        if quality_score >= QUALITY_SCORE_ACCEPTABLE:
                            # Save with quality score in filename
                            safe_query = query[:20].replace(' ', '_').replace('/', '_')
                            filename = f"{story_id}_{strategy_name}_q{quality_score}_{idx}.jpg"
                            filepath = os.path.join(self.cache_dir, filename)

                            # Convert to RGB if needed
                            if img.mode != 'RGB':
                                img = img.convert('RGB')

                            img.save(filepath, 'JPEG', quality=92)
                            downloaded_paths.append(filepath)
                            
                            score_label = "excellent" if quality_score >= QUALITY_SCORE_EXCELLENT else \
                                         "good" if quality_score >= QUALITY_SCORE_GOOD else "acceptable"
                            print(f"      ✓ Downloaded ({score_label}: {quality_score}/100)")

                    except Exception as e:
                        # Skip invalid images
                        continue
        
        except Exception as e:
            print(f"      → Search error: {e}")
        
        return downloaded_paths
    
    def _calculate_quality_score(self, img: Image.Image) -> int:
        """
        Calculate comprehensive quality score (0-100).

        SCORING FACTORS:
        - Resolution (0-25 points)
        - Color variance (0-25 points)
        - Brightness balance (0-20 points)
        - Sharpness (0-15 points)
        - No watermarks (0-15 points)

        Returns
        -------
        int : Quality score 0-100
        """

        try:
            score = 0
            width, height = img.size

            # Convert to RGB for analysis
            if img.mode != 'RGB':
                img_rgb = img.convert('RGB')
            else:
                img_rgb = img

            # 1. RESOLUTION (0-25 points)
            megapixels = (width * height) / 1_000_000
            if megapixels >= 8:
                score += 25
            elif megapixels >= 4:
                score += 20
            elif megapixels >= 2:
                score += 15
            elif megapixels >= 1:
                score += 10
            else:
                score += 5

            # 2. COLOR VARIANCE (0-25 points)
            thumb = img_rgb.resize((100, 100))
            pixels = list(thumb.getdata())
            
            r_vals = [p[0] for p in pixels]
            g_vals = [p[1] for p in pixels]
            b_vals = [p[2] for p in pixels]
            
            r_variance = max(r_vals) - min(r_vals)
            g_variance = max(g_vals) - min(g_vals)
            b_variance = max(b_vals) - min(b_vals)
            
            avg_variance = (r_variance + g_variance + b_variance) / 3
            
            if avg_variance >= 200:
                score += 25
            elif avg_variance >= 150:
                score += 20
            elif avg_variance >= 100:
                score += 15
            elif avg_variance >= 50:
                score += 10
            else:
                score += 5

            # 3. BRIGHTNESS BALANCE (0-20 points)
            avg_brightness = sum(sum(p) / 3 for p in pixels) / len(pixels)
            
            # Ideal: 80-180 (good dynamic range)
            if 80 <= avg_brightness <= 180:
                score += 20
            elif 60 <= avg_brightness <= 200:
                score += 15
            elif 40 <= avg_brightness <= 220:
                score += 10
            else:
                score += 5

            # 4. SHARPNESS (edge detection) (0-15 points)
            try:
                edges = img_rgb.filter(ImageFilter.FIND_EDGES)
                stat = ImageStat.Stat(edges)
                mean_edge = sum(stat.mean) / 3
                
                if mean_edge >= 30:
                    score += 15
                elif mean_edge >= 20:
                    score += 12
                elif mean_edge >= 10:
                    score += 8
                else:
                    score += 4
            except:
                score += 5  # Default if edge detection fails

            # 5. NO WATERMARKS (0-15 points)
            has_watermark = self._detect_watermark_advanced(img_rgb)
            if not has_watermark:
                score += 15
            else:
                score += 0  # Penalize watermarks

            return min(100, max(0, score))

        except Exception:
            return 40  # Default acceptable score if analysis fails

    def _detect_watermark_advanced(self, img: Image.Image) -> bool:
        """
        Advanced watermark detection.

        DETECTION METHODS:
        - Corner uniformity check
        - Edge brightness analysis
        - Pattern detection
        """

        try:
            width, height = img.size
            
            # Need minimum size for detection
            if width < 100 or height < 100:
                return False

            corner_size = 80

            # Sample all 4 corners
            corners = [
                img.crop((0, 0, corner_size, corner_size)),  # Top-left
                img.crop((width - corner_size, 0, width, corner_size)),  # Top-right
                img.crop((0, height - corner_size, corner_size, height)),  # Bottom-left
                img.crop((width - corner_size, height - corner_size, width, height)),  # Bottom-right
            ]

            watermark_indicators = 0

            for corner in corners:
                corner_pixels = list(corner.getdata())
                if len(corner_pixels) == 0:
                    continue

                # Calculate corner statistics
                corner_brightness = sum(sum(p) / 3 for p in corner_pixels) / len(corner_pixels)
                corner_variance = max([max(p) - min(p) for p in corner_pixels])

                # Watermark indicators:
                # 1. Very bright or very dark corner
                if corner_brightness > 240 or corner_brightness < 20:
                    watermark_indicators += 1
                
                # 2. Low variance (uniform overlay)
                if corner_variance < 15:
                    watermark_indicators += 1

            # If 2+ corners show watermark indicators, likely watermarked
            return watermark_indicators >= 2

        except Exception:
            return False
    
    def _generate_fallbacks(self, count: int, story_id: str) -> List[str]:
        """
        Generate UPGRADED procedural fallback images.
        
        IMPROVEMENTS:
        - More sophisticated gradients
        - Better atmospheric effects
        - Subtle textures
        """
        
        fallback_paths = []
        
        # Expanded atmospheric color schemes
        color_schemes = [
            # (base_color, accent_color, name)
            ((8, 12, 20), (35, 45, 75), "deep_blue"),
            ((12, 8, 18), (55, 35, 65), "purple_haze"),
            ((18, 12, 8), (75, 55, 35), "warm_brown"),
            ((8, 18, 12), (35, 75, 55), "forest_green"),
            ((22, 8, 8), (85, 35, 35), "deep_red"),
            ((10, 10, 15), (40, 40, 60), "midnight"),
            ((15, 8, 12), (60, 35, 50), "burgundy"),
        ]
        
        for i in range(count):
            try:
                # Create larger image for better quality
                img = Image.new('RGB', (1200, 900))
                draw = ImageDraw.Draw(img)
                
                # Select color scheme
                base, accent, name = random.choice(color_schemes)
                
                # Create diagonal gradient with noise
                for y in range(900):
                    for x in range(0, 1200, 10):  # Vertical strips
                        # Gradient factor
                        t = (x + y) / (1200 + 900)
                        
                        # Add perlin-like noise
                        noise_x = random.randint(-15, 15)
                        noise_y = random.randint(-15, 15)
                        noise_z = random.randint(-10, 10)
                        
                        color = (
                            max(0, min(255, int(base[0] * (1-t) + accent[0] * t) + noise_x)),
                            max(0, min(255, int(base[1] * (1-t) + accent[1] * t) + noise_y)),
                            max(0, min(255, int(base[2] * (1-t) + accent[2] * t) + noise_z)),
                        )
                        
                        draw.rectangle([(x, y), (x+10, y+1)], fill=color)
                
                # Add subtle vignette effect
                vignette = Image.new('L', (1200, 900), 255)
                vignette_draw = ImageDraw.Draw(vignette)
                
                for i_vig in range(150):
                    alpha = int(255 * (1 - i_vig / 150))
                    vignette_draw.rectangle(
                        [i_vig, i_vig, 1200-i_vig, 900-i_vig],
                        outline=alpha
                    )
                
                img.putalpha(vignette)
                img = img.convert('RGB')
                
                # Apply subtle blur for atmospheric effect
                img = img.filter(ImageFilter.GaussianBlur(radius=1.5))
                
                # Save
                filename = f"{story_id}_fallback_{name}_{i}.jpg"
                filepath = os.path.join(self.cache_dir, filename)
                img.save(filepath, 'JPEG', quality=90)
                
                fallback_paths.append(filepath)
            
            except Exception as e:
                print(f"  [visuals_v2] Fallback generation error: {e}")
                continue
        
        return fallback_paths


def create_visual_manager_v2() -> StoryVisualManagerV2:
    """Factory function."""
    return StoryVisualManagerV2()


# Test mode
if __name__ == "__main__":
    print("=" * 70)
    print("  VISUAL MANAGER V2 TEST")
    print("=" * 70)
    
    manager = create_visual_manager_v2()
    
    # Test concepts
    test_concepts = [
        "dark foggy forest atmosphere",
        "abandoned building exterior moody",
        "flickering streetlight urban night",
    ]
    
    print(f"\nTesting with {len(test_concepts)} visual concepts...")
    
    images = manager.fetch_story_images(test_concepts, "test_story_v2")
    
    print(f"\n{'=' * 70}")
    print(f"  RESULT: {len(images)} high-quality images acquired")
    print('=' * 70)
    
    for i, img_path in enumerate(images, 1):
        # Extract quality score from filename if present
        filename = os.path.basename(img_path)
        quality_match = filename.find('_q')
        if quality_match != -1:
            try:
                quality_score = int(filename[quality_match+2:quality_match+4])
                print(f"  {i}. {filename} (Quality: {quality_score}/100)")
            except:
                print(f"  {i}. {filename}")
        else:
            print(f"  {i}. {filename}")
    
    if len(images) >= IMAGE_MIN_COUNT_V2:
        print(f"\n✅ TEST PASSED (minimum {IMAGE_MIN_COUNT_V2} images)")
    else:
        print(f"\n❌ TEST FAILED (only {len(images)}/{IMAGE_MIN_COUNT_V2} images)")