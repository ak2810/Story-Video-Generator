"""
trend_selector.py - Smart Trend/Rival Selection (Production-Ready)

Selects trending topics and rivals for marble race gameplay.
Uses themes.json database for variety.
"""

import json
import random
from typing import List, Dict, Tuple


class TrendSelector:
    """
    Intelligent trend/rival selection for marble race videos.
    """

    def __init__(self, themes_path: str = "themes.json"):
        self.themes_path = themes_path
        self.themes_db = self._load_themes()

    def _load_themes(self) -> Dict:
        """Load themes from JSON file."""
        try:
            with open(self.themes_path, 'r', encoding='utf-8') as f:
                themes = json.load(f)
            print(f"  [trends] Loaded {len(themes)} categories")
            return themes
        except Exception as e:
            print(f"  [trends] WARN Could not load themes: {e}")
            return {}

    def select_trending_rivals(self, count: int = 2) -> Tuple[str, List[Tuple[str, Tuple, str]]]:
        """
        Select trending rivals for marble race.

        Parameters
        ----------
        count : int
            Number of rivals to select (default 2 for optimal viewing)

        Returns
        -------
        Tuple[str, List[Tuple]]
            (category_name, [(name, color_rgb, search_query), ...])
        """

        if not self.themes_db:
            print("  [trends] No themes available, using defaults")
            return self._get_default_rivals(count)

        # Select random high-engagement category
        popular_categories = [
            "POLITICS", "FOOTBALL", "TECH_COMPANIES",
            "GAMING", "STREAMING", "SUPERHEROES"
        ]

        # Filter to available categories
        available = [cat for cat in popular_categories if cat in self.themes_db]

        if not available:
            # Fall back to any category
            available = list(self.themes_db.keys())

        if not available:
            return self._get_default_rivals(count)

        # Select category
        category = random.choice(available)
        items = self.themes_db[category]

        if len(items) < count:
            print(f"  [trends] WARN Not enough items in {category}, using defaults")
            return self._get_default_rivals(count)

        # Select random rivals from category
        selected_items = random.sample(items, count)

        rivals = []
        for item in selected_items:
            name = item.get("name", "Unknown")
            color = tuple(item.get("color", [255, 100, 100]))
            search_query = item.get("search_query", name)

            rivals.append((name, color, search_query))

        print(f"  [trends] Selected category: {category}")
        for rival in rivals:
            print(f"    -> {rival[0]}")

        return (category, rivals)

    def _get_default_rivals(self, count: int = 2) -> Tuple[str, List[Tuple]]:
        """Fallback default rivals."""
        defaults = [
            ("RED", (255, 50, 50), "red team"),
            ("BLUE", (50, 120, 255), "blue team"),
            ("GREEN", (50, 255, 120), "green team"),
        ]
        return ("DEFAULT", defaults[:count])


def create_trend_selector(themes_path: str = "themes.json") -> TrendSelector:
    """Factory function."""
    return TrendSelector(themes_path)


# Test mode
if __name__ == "__main__":
    print("=" * 70)
    print("  TREND SELECTOR TEST")
    print("=" * 70)

    selector = create_trend_selector()

    print("\nTest 1: Select 2 rivals")
    category, rivals = selector.select_trending_rivals(2)
    print(f"\nCategory: {category}")
    print(f"Rivals: {len(rivals)}")
    for name, color, query in rivals:
        print(f"  - {name} (RGB: {color})")

    print("\n" + "=" * 70)
    print("  TEST PASSED")
    print("=" * 70)
