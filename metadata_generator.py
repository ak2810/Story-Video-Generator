"""
metadata_generator.py  --  Ollama-powered YouTube + TikTok metadata.

Calls your local Ollama to produce metadata for BOTH platforms:
- YouTube: title, description, tags
- TikTok: caption, hashtags

Platform limits enforced:
    YouTube:
        title        <= 100 chars
        description  <= 5000 chars   (hashtags live inside this)
        tags         <= 500 chars total joined,  each <= 32 chars
    
    TikTok:
        caption      <= 2200 chars (includes hashtags)
        hashtags     <= 150 chars total (recommended 3-5 hashtags)
"""

import requests
import json
import re

# ---------------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------------
OLLAMA_URL     = "http://localhost:11434/api/chat"
OLLAMA_BASE    = "http://localhost:11434"
OLLAMA_TIMEOUT = 90

# Preferred models (in order of preference)
PREFERRED_MODELS = [
    "llama3.1:latest",
    "qwen3-coder:30b-a3b-q8_0",
    "qwen2.5:32b",
    "qwen2.5-coder:14b",
    "qwen2.5:14b",
    "qwen2.5-coder:7b",
    "qwen2.5:7b",
    "qwen2.5-coder:3b",
    "llama3.1:8b",
    "llama2:latest",
    "mistral:latest",
]

# Auto-selected model (will be set on first call)
_SELECTED_MODEL = None

# YouTube limits
YT_TITLE_MAX      = 100
YT_DESC_MAX       = 5000
YT_TAGS_TOTAL_MAX = 500
YT_TAG_SINGLE_MAX = 32

# TikTok limits
TT_CAPTION_MAX    = 2200
TT_HASHTAG_MAX    = 150

MAX_RETRIES    = 2


# ---------------------------------------------------------------------------
# Model Auto-Detection
# ---------------------------------------------------------------------------
def _detect_best_model():
    """Auto-detect and select the best available Ollama model."""
    global _SELECTED_MODEL
    
    if _SELECTED_MODEL:
        return _SELECTED_MODEL
    
    try:
        resp = requests.get(f"{OLLAMA_BASE}/api/tags", timeout=5)
        if resp.status_code != 200:
            return None
        
        data = resp.json()
        available_models = [m.get("name", "") for m in data.get("models", [])]
        
        if not available_models:
            print("    [metadata] No Ollama models installed")
            return None
        
        # Try to find a preferred model
        for preferred in PREFERRED_MODELS:
            for available in available_models:
                if preferred in available or available.startswith(preferred.split(':')[0]):
                    _SELECTED_MODEL = available
                    print(f"    [metadata] Using model: {_SELECTED_MODEL}")
                    return _SELECTED_MODEL
        
        # Use first available
        _SELECTED_MODEL = available_models[0]
        print(f"    [metadata] Using fallback model: {_SELECTED_MODEL}")
        return _SELECTED_MODEL
        
    except Exception as e:
        print(f"    [metadata] Model detection failed: {e}")
        return None


# ---------------------------------------------------------------------------
# Ollama  --  single call, returns text or None
# ---------------------------------------------------------------------------
def _call_ollama(system, user):
    model = _detect_best_model()
    
    if not model:
        print("    [metadata] No Ollama model available")
        return None
    
    try:
        resp = requests.post(
            OLLAMA_URL,
            json={
                "model":    model,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user",   "content": user},
                ],
                "stream":  False,
                "options": {"temperature": 0.78, "top_p": 0.92, "num_predict": 1000},
            },
            timeout=OLLAMA_TIMEOUT,
        )
        resp.raise_for_status()
        return resp.json()["message"]["content"]
    except Exception as e:
        print(f"    [ollama] error: {e}")
        return None


# ---------------------------------------------------------------------------
# Parser  --  handles JSON, markdown-fenced JSON, or key: value lines
# ---------------------------------------------------------------------------
def _parse(raw):
    text = raw.strip()

    # strip markdown fences
    if text.startswith("```"):
        text = re.sub(r"```(?:json)?\s*", "", text).strip()
        text = text.rstrip("`").strip()

    # attempt 1: find outermost { ... } and parse as JSON
    brace_s = text.find("{")
    brace_e = text.rfind("}")
    if brace_s != -1 and brace_e > brace_s:
        try:
            obj = json.loads(text[brace_s:brace_e + 1])
            if isinstance(obj, dict):
                # Normalize tags/hashtags to arrays if they're strings
                if "youtube" in obj:
                    yt = obj["youtube"]
                    if isinstance(yt.get("tags"), str):
                        yt["tags"] = [t.strip() for t in yt["tags"].split(",")]
                if "tiktok" in obj:
                    tt = obj["tiktok"]
                    if isinstance(tt.get("hashtags"), str):
                        tt["hashtags"] = [h.strip() for h in tt["hashtags"].split(",")]
                return obj
        except (json.JSONDecodeError, ValueError):
            pass

    # attempt 2: line-by-line extraction (fallback)
    # This is more complex with nested structure, so we'll skip for now
    # and rely on JSON parsing above
    return {}


# ---------------------------------------------------------------------------
# Limit enforcement for YouTube
# ---------------------------------------------------------------------------
def _cap_yt_title(raw):
    t = str(raw).strip().strip('"').strip("'")  
    if len(t) > YT_TITLE_MAX:
        t = t[:YT_TITLE_MAX]
        sp = t.rfind(" ")
        if sp > YT_TITLE_MAX - 15:
            t = t[:sp]
    return t


def _cap_yt_description(raw):
    d = str(raw).strip()
    if len(d) <= YT_DESC_MAX:
        return d
    # keep last 250 chars (hashtag block), cut the middle
    return d[: YT_DESC_MAX - 250].rstrip() + "\n\n" + d[-250:].lstrip()


def _cap_yt_tags(raw_list):
    cleaned = []
    for t in raw_list:
        t = str(t).strip().strip('"').strip("'").lstrip("#").strip()
        if len(t) < 2:
            continue
        if len(t) > YT_TAG_SINGLE_MAX:
            t = t[:YT_TAG_SINGLE_MAX]
        cleaned.append(t)

    final, running = [], 0
    for t in cleaned:
        cost = len(t) + (1 if final else 0)
        if running + cost > YT_TAGS_TOTAL_MAX:
            break
        final.append(t)
        running += cost
    return final


# ---------------------------------------------------------------------------
# Limit enforcement for TikTok
# ---------------------------------------------------------------------------
def _cap_tt_caption(raw):
    c = str(raw).strip()
    if len(c) > TT_CAPTION_MAX:
        # Cut to fit, preserving hashtags at the end if possible
        c = c[:TT_CAPTION_MAX]
        # Try to cut at last complete word
        sp = c.rfind(" ")
        if sp > TT_CAPTION_MAX - 50:
            c = c[:sp]
    return c


def _cap_tt_hashtags(raw_list):
    """Limit hashtags to fit within 150 chars total."""
    cleaned = []
    for h in raw_list:
        h = str(h).strip().strip('"').strip("'")
        if not h.startswith("#"):
            h = "#" + h
        h = h.replace(" ", "")  # TikTok hashtags can't have spaces
        if len(h) > 2:
            cleaned.append(h)
    
    # Join and limit to 150 chars
    joined = " ".join(cleaned)
    if len(joined) <= TT_HASHTAG_MAX:
        return cleaned
    
    # Trim from the end
    result = []
    current_len = 0
    for h in cleaned:
        cost = len(h) + (1 if result else 0)  # +1 for space
        if current_len + cost > TT_HASHTAG_MAX:
            break
        result.append(h)
        current_len += cost
    return result


# ---------------------------------------------------------------------------
# Fallback templates
# ---------------------------------------------------------------------------
def _hashtag_block_yt(theme, r1, r2):
    core = [
        "#shorts", "#YouTubeShorts", "#viral", "#satisfying",
        "#marblerace", "#marblerun", "#simulation", "#championship",
        "#fyp", "#foryou", "#trending", "#watch",
    ]
    extra = [
        f"#{theme.lower()}",
        f"#{r1.lower().replace(' ', '')}",
        f"#{r2.lower().replace(' ', '')}",
        f"#{r1.lower().replace(' ', '')}vs{r2.lower().replace(' ', '')}",
    ]
    return "\n".join(core + extra)


def _fallback_yt(theme, r1, r2):
    """YouTube Shorts: SEO-optimized, detailed, more hashtags"""
    title = _cap_yt_title(f"EPIC Marble Race: {r1} vs {r2} Championship Battle 🏆")

    desc = (
        f"Who do you think will win? {r1} or {r2}? Vote in the comments!\n\n"

        f"🎯 THE COMPETITION:\n"
        f"Watch {r1} and {r2} compete in the ultimate marble race championship! "
        f"Two rivals battle through spinning rotating rings and destructive obstacles. "
        f"Each round increases in difficulty with faster speeds and tighter gaps. "
        f"Only one can claim victory!\n\n"

        f"⚡ WHAT HAPPENS:\n"
        f"• Marbles race through challenging rotating ring mazes\n"
        f"• Break through walls to escape faster\n"
        f"• Each round eliminates the slower competitor\n"
        f"• Final showdown determines the ultimate champion\n\n"

        f"🔥 CALL TO ACTION:\n"
        f"👍 Like if you predicted the winner\n"
        f"💬 Comment your favorite rival\n"
        f"🔔 Subscribe for daily marble race championships\n"
        f"🔗 Share with friends who love satisfying content\n\n"

        + _hashtag_block_yt(theme, r1, r2)
    )

    base_tags = [
        "marble race", "marble run", "marbles", "satisfying videos",
        "asmr", "oddly satisfying", "simulation", "race",
        "championship", "competition", "shorts", "viral",
        "relaxing", "mesmerizing", "physics"
    ]
    tags = _cap_yt_tags(base_tags + [theme.lower(), r1.lower(), r2.lower()])

    return title, desc, tags


def _fallback_tt(theme, r1, r2):
    """TikTok: Ultra-short, punchy, engagement-focused, fewer hashtags"""
    # Ultra-short viral hook (TikTok users scroll FAST)
    caption = (
        f"POV: Your team is losing 👀\n\n"
        f"{r1} vs {r2} - who you betting on? 💰"
    )

    # Only 4-5 hashtags (TikTok algorithm prefers fewer)
    hashtags = [
        "#fyp",
        "#marblerace",
        "#satisfying",
        f"#{r1.lower().replace(' ', '')}",
        f"#{r2.lower().replace(' ', '')}"
    ]

    return _cap_tt_caption(caption), _cap_tt_hashtags(hashtags)


# ---------------------------------------------------------------------------
# MAIN ENTRY  --  generates metadata for BOTH platforms
# ---------------------------------------------------------------------------
def generate(theme_name, rival1, rival2, champion, scores, duration_secs):
    """
    Returns {
        "youtube": {
            "title": str,
            "description": str,
            "tags": [str]
        },
        "tiktok": {
            "caption": str,
            "hashtags": [str]  # includes # prefix
        }
    }
    """
    print("    [metadata] asking Ollama for YouTube + TikTok metadata…", flush=True)

    # context block
    score_line = "  |  ".join(f"{k}: {v}" for k, v in scores.items())
    context = (
        f"Theme        : {theme_name}\n"
        f"Rival 1      : {rival1}\n"
        f"Rival 2      : {rival2}\n"
        f"Champion     : {champion}\n"
        f"Final scores : {score_line}\n"
        f"Duration     : {duration_secs:.0f} seconds\n"
        f"Format       : Vertical short-form video (9:16)\n"
    )

    # system prompt for DUAL platform generation with DISTINCT strategies
    system = (
        "You are a viral short-form video growth expert specializing in YouTube Shorts AND TikTok.\n"
        "Create DIFFERENT metadata for each platform - not just reformatted, but strategically unique.\n\n"

        "═══════════════════════════════════════════════════════════════════\n"
        "YOUTUBE SHORTS STRATEGY (SEO-Optimized, Detail-Rich)\n"
        "═══════════════════════════════════════════════════════════════════\n"
        "HARD LIMITS:\n"
        "• title       : max 100 characters\n"
        "• description : max 5000 characters\n"
        "• tags        : 12-15 tags, each ≤ 32 chars, total ≤ 500 chars\n\n"

        "YOUTUBE TITLE FORMAT:\n"
        "• SEO-focused with keywords front-loaded\n"
        "• Include 'Marble Race' OR 'Marble Run' in title\n"
        "• Pattern: [Hook] + [What Happens] + [Emoji]\n"
        "• Example: \"INSANE Marble Race: Who Survives the Final Round? 🏆\"\n"
        "• Max 1-2 emojis, NO period at end\n\n"

        "YOUTUBE DESCRIPTION (Detailed & SEO-Rich):\n"
        "Line 1: Engagement hook - \"Who do you think wins? {Rival1} or {Rival2}?\"\n"
        "Line 2-4: Detailed explanation of the competition (3-4 sentences)\n"
        "Line 5: Suspense builder about the outcome\n"
        "Line 6-8: Strong CTAs (like, subscribe, comment your prediction)\n"
        "Line 9+: 15-18 hashtags separated by spaces\n\n"

        "YOUTUBE TAGS (SEO Keywords):\n"
        "Required: marble race, marble run, marbles, satisfying, asmr, simulation, shorts\n"
        "Add: viral, competition, championship, oddly satisfying, relaxing\n"
        "Total: 12-15 tags minimum\n\n"

        "═══════════════════════════════════════════════════════════════════\n"
        "TIKTOK STRATEGY (Trend-Focused, Ultra-Short, Engagement-First)\n"
        "═══════════════════════════════════════════════════════════════════\n"
        "HARD LIMITS:\n"
        "• caption    : 150-250 characters recommended (max 2200)\n"
        "• hashtags   : 4-5 hashtags max, total ≤ 150 chars\n\n"

        "TIKTOK CAPTION FORMAT:\n"
        "• Ultra-short hook (5-8 words max)\n"
        "• End with question + emoji CTA\n"
        "• NO detailed explanation (TikTok users scroll fast)\n"
        "• Casual tone, use '?' and emojis\n"
        "• Pattern: [Viral Hook] + [Question] + [Emoji]\n"
        "• Example: \"POV: Your team is losing 👀 Who you betting on? 💰\"\n\n"

        "TIKTOK HASHTAGS (Trend Discovery):\n"
        "• 4-5 hashtags ONLY (TikTok algorithm prefers fewer)\n"
        "• Mix: 2 broad viral tags + 2-3 niche specific tags\n"
        "• Broad: #fyp #foryoupage #viral #satisfying\n"
        "• Specific: #marblerace #[rival1] #[rival2]\n"
        "• NO spaces in hashtags\n\n"

        "═══════════════════════════════════════════════════════════════════\n"
        "KEY DIFFERENCES BETWEEN PLATFORMS:\n"
        "═══════════════════════════════════════════════════════════════════\n"
        "YouTube  → Longer, SEO keywords, detailed, more hashtags\n"
        "TikTok   → Shorter, trend-focused, punchy, fewer hashtags\n\n"

        "CRITICAL RULES FOR BOTH:\n"
        "✗ NO SPOILERS - Never reveal winner or final score\n"
        "✗ NO copying - YouTube and TikTok content must be DIFFERENT\n"
        "✓ Build suspense to drive watch time\n"
        "✓ Ask questions to drive engagement\n\n"

        "OUTPUT FORMAT (JSON only, no prose):\n"
        "{\n"
        '  "youtube": {\n'
        '    "title": "SEO-focused title with Marble Race keyword",\n'
        '    "description": "Detailed multi-line description with 15-18 hashtags at end",\n'
        '    "tags": ["marble race", "marble run", "satisfying", ...12-15 total]\n'
        "  },\n"
        '  "tiktok": {\n'
        '    "caption": "Ultra-short punchy hook with question emoji",\n'
        '    "hashtags": ["#fyp", "#marblerace", ...4-5 total]\n'
        "  }\n"
        "}\n"
    )

    user = "Generate YouTube + TikTok metadata for this video:\n\n" + context

    # call + retry
    parsed = None
    for attempt in range(MAX_RETRIES + 1):
        raw = _call_ollama(system, user)
        if raw is None:
            print(f"    [metadata] Ollama unreachable (attempt {attempt + 1}).")
            break
        parsed = _parse(raw)
        if "youtube" in parsed and "tiktok" in parsed:
            break
        print(f"    [metadata] parse attempt {attempt + 1} incomplete, retry…")

    # Build final metadata with limits enforced
    result = {
        "youtube": {},
        "tiktok": {}
    }

    # === YOUTUBE ===
    if parsed and "youtube" in parsed:
        yt = parsed["youtube"]
        result["youtube"]["title"] = _cap_yt_title(yt.get("title", ""))
        result["youtube"]["description"] = _cap_yt_description(yt.get("description", ""))
        raw_tags = yt.get("tags", [])
        if isinstance(raw_tags, str):
            raw_tags = [t.strip() for t in raw_tags.split(",")]
        result["youtube"]["tags"] = _cap_yt_tags(raw_tags)
    else:
        print("    [metadata] using YouTube fallback template.")
        title, desc, tags = _fallback_yt(theme_name, rival1, rival2)
        result["youtube"] = {"title": title, "description": desc, "tags": tags}

    # === TIKTOK ===
    if parsed and "tiktok" in parsed:
        tt = parsed["tiktok"]
        result["tiktok"]["caption"] = _cap_tt_caption(tt.get("caption", ""))
        raw_hashtags = tt.get("hashtags", [])
        if isinstance(raw_hashtags, str):
            raw_hashtags = [h.strip() for h in raw_hashtags.split(",")]
        result["tiktok"]["hashtags"] = _cap_tt_hashtags(raw_hashtags)
    else:
        print("    [metadata] using TikTok fallback template.")
        caption, hashtags = _fallback_tt(theme_name, rival1, rival2)
        result["tiktok"] = {"caption": caption, "hashtags": hashtags}

    # Log stats
    yt = result["youtube"]
    tt = result["tiktok"]
    
    yt_tags_ch = sum(len(t) for t in yt["tags"]) + max(len(yt["tags"]) - 1, 0)
    tt_hashtags_ch = sum(len(h) for h in tt["hashtags"]) + max(len(tt["hashtags"]) - 1, 0)
    
    print(f"    [metadata] YouTube: title {len(yt['title']):>3}/100 ch  |  "
          f"desc {len(yt['description']):>4}/5000 ch  |  "
          f"tags {len(yt['tags']):>2} items {yt_tags_ch}/500 ch")
    print(f"    [metadata] TikTok:  caption {len(tt['caption']):>4}/2200 ch  |  "
          f"hashtags {len(tt['hashtags']):>2} items {tt_hashtags_ch}/150 ch")

    return result