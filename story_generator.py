"""
story_generator.py - Two-Part Story Generator (Production-Ready)

PRODUCTION IMPROVEMENTS:
- Uses centralized configuration
- Better error handling
- Configurable word counts and durations
- Enhanced validation
"""

import requests
import json
import time
import random
import subprocess
import re
from typing import Dict, List, Optional
from production_config import (
    OLLAMA_BASE_URL, OLLAMA_MODEL, OLLAMA_TIMEOUT,
    STORY_MIN_WORDS, STORY_TARGET_WORDS, STORY_MAX_WORDS,
    STORY_MIN_VISUAL_CONCEPTS, STORY_TARGET_VISUAL_CONCEPTS
)


class StoryGenerator:
    """
    Generates two-part mystery/suspense narratives using Ollama LLM.
    """
    
    # ULTRA-VIRAL story topics (MAXIMUM first 10-second retention)
    # Each topic designed to hook viewers IMMEDIATELY
    STORY_TOPICS = [
        # Original & Refined
        "phone call that predicted a life-changing event",
        "hospital patient who woke up speaking a dead language",
        "photograph that revealed tomorrow's news headline",
        "text message from someone who died decades ago",
        "security footage that proves time travel is real",
        "last words that nobody was meant to hear",
        "town where everyone vanished at exactly 3:33 AM",
        "child who remembered dying in a past life",
        "recording that should have been deleted forever",
        "person who appeared in photos taken 100 years apart",
        "mirror that reflected your future instead of your image",
        "experiment that opened a portal to another dimension",
        "astronaut who returned changed in unexplainable ways",
        "video call from an impossible location",
        "final transmission before a research station went dark",

        # Glitch & Time
        "train that arrived 30 years late without explanation",
        "man who lived the same Tuesday for six months",
        "elevator that took someone to a non-existent floor",
        "plane that landed with zero fuel remaining",
        "letter delivered 50 years after being mailed",
        "watch that counts backwards when you enter the room",
        "tunnel where travelers lose three hours of memory",
        "reflection that blinked when the person didn’t",
        "rain that only falls on one specific house",
        "city street that disappears and reappears randomly",
        "clock that stops whenever danger is near",
        "library book that updates itself with future events",

        # Tech & Digital
        "AI that invented its own secret language",
        "unlisted number that calls every year on the same date",
        "hard drive hidden inside a sealed ancient wall",
        "bitcoin wallet that activates years after the owner's death",
        "wifi network that appears only at 3 AM",
        "phone photo from a device that was never sold",
        "text message predicting lottery numbers",
        "game console that recorded a conversation in an empty room",
        "website that knew the user's name before typing it",
        "chatbot that starts responding before a question is asked",
        "smart home that locks itself against unknown intruders",
        "VR headset that traps the user in a parallel timeline",
        "email from your future self warning of disaster",

        # True Crime & Eerie
        "twins separated at birth who lived identical lives",
        "burglar who accidentally saved the homeowner's life",
        "diary discovered inside the walls of a new house",
        "911 call from a house that burned down years ago",
        "prisoner who escaped using only dental floss",
        "detective who realized he was investigating himself",
        "stranger who paid for a coffee and left a warning note",
        "voice on the baby monitor that wasn't the parents",
        "anonymous letters revealing hidden family secrets",
        "photographer capturing someone who shouldn’t exist",
        "museum exhibit that moves slightly every night",
        "case files that predict crimes before they happen",

        # Nature & Space
        "sound from the deep ocean that shouldn't exist",
        "star that vanished while astronomers were observing",
        "island that appears on maps but not in reality",
        "patient whose heart stopped for four hours",
        "forest where no birds or insects make a sound",
        "radio station that buzzes continuously for decades",
        "archaeologist who found a modern watch in an ancient tomb",
        "lighthouse keeper who disappeared without a trace",
        "pilot who reported a UFO before vanishing",
        "doll that moves slightly whenever no one is watching",
        "meteor that repeats its path exactly every year",
        "lake that reflects a different sky than the one above",
        "volcano that erupts only when no one is nearby",
        "cave that echoes voices from another time",
        "desert where shadows move independently of objects",

        # New Additions — Eerie & Sci-Fi
        "painting that changes when you aren't looking",
        "phone app that predicts events before they happen",
        "hotel room that never existed on any map",
        "bus route that only appears during storms",
        "journal entries that write themselves overnight",
        "coin that returns to your pocket no matter what",
        "city lights that blink in Morse code messages",
        "music box that plays songs from the future",
        "shadow that moves against the light source",
        "old radio broadcasting a message from a deceased person",
        "park bench that teleports people to another city",
        "keys that unlock doors that shouldn't exist",
        "mirror that shows alternate versions of yourself",
        "phone vibration from a call that hasn't been made",
        "street sign pointing to places that never existed",
        "notes that appear in books, predicting your day",
        "window that shows events from hours in the future",
        "staircase that leads to a room you never entered",
        "old letters arriving daily from someone in the past",
        "train tracks that vanish when approached",
        "fountain that reflects scenes from other planets",
        "watch that syncs with alternate realities",
        "dog that remembers events before they happen",
        "phone contact that calls itself back automatically",
        "room that rearranges itself overnight",
        "library that contains books from the future",
        "newspaper with headlines from the next week",
        "elevator that drops you into the wrong time",
        "photograph that absorbs people into it",
        "car that drives itself to unknown destinations",
        "house where objects slowly disappear and reappear",
        "statue that whispers secrets when no one is near",
        "map that redraws itself based on events to come"
    ]

    
    def __init__(self):
        self.model_ready = False
        self._ensure_model_available()
    
    def _ensure_model_available(self):
        """Verify model is available, pull if necessary."""
        print(f"  [story] Checking for {OLLAMA_MODEL}...")

        try:
            response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=10)

            if response.status_code != 200:
                raise RuntimeError("Ollama not responding")

            available_models = [m["name"] for m in response.json().get("models", [])]

            if OLLAMA_MODEL in available_models:
                print(f"  [story] OK Model available: {OLLAMA_MODEL}")
                self.model_ready = True
                return

            # Model missing - pull it
            print(f"  [story] ⬇ Pulling {OLLAMA_MODEL}...")
            print(f"  [story]   This may take several minutes...")

            result = subprocess.run(
                ["ollama", "pull", OLLAMA_MODEL],
                capture_output=True,
                text=True,
                timeout=1800
            )

            if result.returncode == 0:
                print(f"  [story] OK Model ready")
                self.model_ready = True
            else:
                raise RuntimeError(f"Pull failed: {result.stderr}")

        except Exception as e:
            raise RuntimeError(f"Model setup failed: {e}")
    
    def generate_two_part_story(self) -> Dict:
        """
        Generate complete two-part story with guaranteed visual concepts.
        
        Returns
        -------
        dict : {
            "topic": str,
            "part1": {"script": str, "visual_concepts": [str, ...]},
            "part2": {"script": str, "visual_concepts": [str, ...]}
        }
        """
        if not self.model_ready:
            raise RuntimeError("Story model not available")
        
        topic = random.choice(self.STORY_TOPICS)
        print(f"\n  [story] Generating two-part narrative: {topic}")
        
        # Generate Part 1
        part1 = self._generate_part(topic, part_number=1)
        time.sleep(2)
        
        # Generate Part 2 with Part 1 context
        part2 = self._generate_part(topic, part_number=2, previous_script=part1["script"])
        
        return {
            "topic": topic,
            "part1": part1,
            "part2": part2
        }
    
    def _generate_part(self, topic: str, part_number: int, previous_script: Optional[str] = None) -> Dict:
        """Generate single story part with STRICT validation."""
        
        system_prompt = self._build_system_prompt(part_number)
        user_prompt = self._build_user_prompt(topic, part_number, previous_script)
        
        print(f"  [story] Generating Part {part_number}...")
        
        max_retries = 3
        for attempt in range(max_retries):
            print(f"  [story] Attempt {attempt + 1}/{max_retries}...")
            
            try:
                # Call LLM
                response = self._call_ollama(system_prompt, user_prompt)
                
                if not response:
                    print(f"  [story] X Empty response")
                    continue
                
                # Parse JSON (strict)
                parsed = self._parse_json_strict(response)
                
                if not parsed:
                    print(f"  [story] X JSON parsing failed completely")
                    continue
                
                # Validate (strict)
                valid, reason = self._validate_strict(parsed, part_number)
                
                if not valid:
                    print(f"  [story] X Validation failed: {reason}")
                    continue
                
                # Success
                word_count = len(parsed['script'].split())
                concepts_count = len(parsed['visual_concepts'])
                print(f"  [story] OK Part {part_number} generated successfully")
                print(f"  [story]   Words: {word_count}, Visual concepts: {concepts_count}")
                return parsed
                
            except Exception as e:
                print(f"  [story] X Error: {e}")
                if attempt < max_retries - 1:
                    time.sleep(3)
        
        # All retries exhausted - FAIL CLEARLY
        raise RuntimeError(f"Part {part_number} generation failed after {max_retries} attempts")
    
    def _build_system_prompt(self, part_number: int) -> str:
        """Build system prompt with explicit JSON requirements."""

        if part_number == 1:
            return """You write VIRAL mystery scripts for TikTok/YouTube Shorts.

CRITICAL RULES:
1. First sentence MUST grab attention in 3 seconds (use numbers, shocking facts, or impossible situations)
2. Script MINIMUM 180 words total
3. End on cliffhanger that demands Part 2

HOOK EXAMPLES (first sentence):
- "It happened at exactly 3:33 AM when every phone in town rang at once."
- "The last person to see her alive swears she was never there."
- "Security cameras captured something that shouldn't exist."

Return ONLY JSON:
{
  "script": "your 180+ word script with POWERFUL first sentence hook",
  "visual_concepts": ["dark forest", "abandoned building", "flickering light", "empty corridor", "ominous shadow", "warning sign"]
}

Visual concepts: 5-7 short searches (2-3 words each).
Return JSON ONLY."""

        else:
            return """You write viral mystery scripts.

CRITICAL: Script MUST be MINIMUM 180 words. Count every word.

Continue from Part 1, reveal mystery, satisfying resolution. No gore.

Return ONLY JSON:
{
  "script": "your 180+ word resolution here",
  "visual_concepts": ["evidence photo", "investigation scene", "revelation", "discovery", "aftermath", "truth revealed"]
}

Visual concepts: 5-7 short searches (2-3 words each).
Return JSON ONLY."""
    
    def _build_user_prompt(self, topic: str, part_number: int, previous_script: Optional[str]) -> str:
        """Build user prompt with concrete examples."""

        if part_number == 1:
            return f"""Topic: {topic}

Write MINIMUM 180 words. Hook start, build tension, cliffhanger end.

JSON only:
{{
  "script": "your 180+ word script",
  "visual_concepts": ["dark forest", "abandoned place", "flickering light", "empty hall", "shadow", "eerie sign"]
}}"""

        else:
            context = f"\n\nPart 1:\n{previous_script[:200]}...\n\n" if previous_script else ""

            return f"""{context}Topic: {topic}

Write MINIMUM 180 words. Resolve mystery, reveal truth.

JSON only:
{{
  "script": "your 180+ word resolution",
  "visual_concepts": ["evidence", "investigation", "revelation", "discovery", "aftermath", "truth"]
}}"""
    
    def _call_ollama(self, system_prompt: str, user_prompt: str) -> Optional[str]:
        """Call Ollama API with timeout."""
        
        try:
            response = requests.post(
                f"{OLLAMA_BASE_URL}/api/chat",
                json={
                    "model": OLLAMA_MODEL,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    "stream": False,
                    "options": {
                        "temperature": 0.8,
                        "top_p": 0.9,
                        "num_predict": 2000  # INCREASED from 1500 to allow longer outputs
                    }
                },
                timeout=OLLAMA_TIMEOUT
            )
            
            if response.status_code == 200:
                content = response.json()["message"]["content"]
                print(f"  [story] Response: {len(content)} chars")
                return content
            else:
                print(f"  [story] API error: {response.status_code}")
                return None
        
        except Exception as e:
            print(f"  [story] Request error: {e}")
            return None
    
    def _parse_json_strict(self, raw_response: str) -> Optional[Dict]:
        """
        STRICT JSON parsing with control character handling.
        
        Returns None if parsing fails (no silent recovery).
        """
        
        text = raw_response.strip()
        
        # Remove markdown fences if present
        if "```" in text:
            # Extract content between ```json and ``` or just between ```
            pattern = r'```(?:json)?\s*(.*?)```'
            match = re.search(pattern, text, re.DOTALL)
            if match:
                text = match.group(1).strip()
        
        # Find JSON object
        start = text.find("{")
        end = text.rfind("}") + 1
        
        if start == -1 or end <= start:
            print(f"  [story] No JSON object found in response")
            return None
        
        json_str = text[start:end]
        
        # CRITICAL FIX: Remove/escape control characters
        json_str = json_str.replace('\r', '')
        json_str = json_str.replace('\x00', '')
        
        # Fix unescaped newlines within quoted strings
        def fix_string_value(match):
            """Fix control characters within a JSON string value."""
            quote = match.group(1)
            content = match.group(2)
            
            # Escape newlines and tabs if not already escaped
            content = re.sub(r'(?<!\\)\n', r'\\n', content)
            content = re.sub(r'(?<!\\)\t', r'\\t', content)
            
            return f'{quote}{content}{quote}'
        
        # Match quoted strings: "..." (with escaped quotes allowed inside)
        string_pattern = r'(")((\\.|[^"\\])*?)(")'
        json_str = re.sub(string_pattern, fix_string_value, json_str)
        
        # Try to parse
        try:
            data = json.loads(json_str)
            
            # Extract and clean
            script = data.get("script", "").strip()
            concepts = data.get("visual_concepts", [])
            
            # Clean script (unescape if needed)
            script = script.replace('\\n', '\n').replace('\\t', ' ')
            
            # Clean concepts
            if isinstance(concepts, str):
                concepts = [c.strip() for c in concepts.split(',')]
            
            concepts = [c.strip(' "\'\n\t') for c in concepts if c and c.strip()]
            
            return {
                "script": script,
                "visual_concepts": concepts
            }
        
        except json.JSONDecodeError as e:
            print(f"  [story] JSON parse error: {e}")
            
            # Try manual extraction as last resort
            script = self._extract_script_manual(json_str)
            concepts = self._extract_concepts_manual(json_str)
            
            if script and concepts:
                print(f"  [story] Manual extraction succeeded")
                return {
                    "script": script,
                    "visual_concepts": concepts
                }
            
            return None
    
    def _extract_script_manual(self, text: str) -> Optional[str]:
        """Manual script extraction using regex."""
        
        # Match "script": "..." with escaped quotes handling
        pattern = r'"script"\s*:\s*"((\\.|[^"\\])*)"'
        match = re.search(pattern, text, re.DOTALL)
        
        if match:
            script = match.group(1)
            # Unescape
            script = script.replace('\\n', '\n').replace('\\t', ' ').replace('\\"', '"')
            return script.strip()
        
        return None
    
    def _extract_concepts_manual(self, text: str) -> List[str]:
        """Manual visual_concepts extraction using regex."""
        
        # Match "visual_concepts": [...]
        pattern = r'"visual_concepts"\s*:\s*\[(.*?)\]'
        match = re.search(pattern, text, re.DOTALL)
        
        if match:
            array_content = match.group(1)
            # Extract quoted strings
            concepts = re.findall(r'"([^"]+)"', array_content)
            return [c.strip() for c in concepts if c.strip()]
        
        return []
    
    def _validate_strict(self, parsed: Dict, part_number: int) -> tuple[bool, str]:
        """
        STRICT validation with clear failure reasons.
        
        HOTFIX: Relaxed minimum from 150 to 130 words
        
        Returns
        -------
        (valid: bool, reason: str)
        """
        
        script = parsed.get("script", "")
        concepts = parsed.get("visual_concepts", [])
        
        # Must have script
        if not script:
            return False, "No script found"
        
        # Word count
        words = script.split()
        word_count = len(words)

        if word_count < STORY_MIN_WORDS:
            return False, f"Script too short: {word_count} words (need {STORY_TARGET_WORDS}+ ideally)"

        if word_count > STORY_MAX_WORDS:
            return False, f"Script too long: {word_count} words (target {STORY_TARGET_WORDS})"

        # CRITICAL: Must have visual concepts
        if not concepts:
            return False, "No visual concepts found"

        if len(concepts) < STORY_MIN_VISUAL_CONCEPTS:
            return False, f"Insufficient visual concepts: {len(concepts)} (need {STORY_TARGET_VISUAL_CONCEPTS})"
        
        # Quality checks
        sentences = [s.strip() for s in script.replace('!', '.').replace('?', '.').split('.') if s.strip()]
        
        if len(sentences) < 5:
            return False, f"Too few sentences: {len(sentences)} (need 5+)"
        
        # All checks passed
        return True, "valid"


def create_story_generator() -> StoryGenerator:
    """Factory function."""
    return StoryGenerator()


# Test mode
if __name__ == "__main__":
    print("=" * 70)
    print("  STORY GENERATOR TEST")
    print("=" * 70)
    
    generator = create_story_generator()
    
    try:
        story = generator.generate_two_part_story()
        
        print("\n" + "=" * 70)
        print("  GENERATED STORY")
        print("=" * 70)
        print(f"\nTopic: {story['topic']}")
        
        for part_num in [1, 2]:
            part_key = f"part{part_num}"
            part = story[part_key]
            
            print(f"\n{'=' * 70}")
            print(f"  PART {part_num}")
            print('=' * 70)
            print(f"Script: {len(part['script'])} chars, {len(part['script'].split())} words")
            print(f"Visual concepts: {len(part['visual_concepts'])}")
            print("\nConcepts:")
            for i, concept in enumerate(part['visual_concepts'], 1):
                print(f"  {i}. {concept}")
            print("\nScript preview:")
            print(part['script'][:300] + "..." if len(part['script']) > 300 else part['script'])
        
        print("\n" + "=" * 70)
        print("  OK TEST PASSED")
        print("=" * 70)
        
    except Exception as e:
        print(f"\nX TEST FAILED: {e}")
        import traceback
        traceback.print_exc()