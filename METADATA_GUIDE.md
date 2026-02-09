# Platform-Specific Metadata Generation

## Overview

The metadata generator now creates **strategically different** content for YouTube Shorts and TikTok, not just reformatted versions.

---

## 🎯 Platform Strategies

### YouTube Shorts Strategy
**Goal**: SEO optimization, detailed information, longer engagement

| Element | Limit | Strategy |
|---------|-------|----------|
| **Title** | 100 chars | SEO-focused, keyword front-loaded, includes "Marble Race" |
| **Description** | 5000 chars | Multi-paragraph, detailed explanation, strong CTAs, 15-18 hashtags |
| **Tags** | 12-15 tags | SEO keywords: marble race, satisfying, asmr, simulation, etc. |

**YouTube Title Format**:
```
[Hook] + [What Happens] + [Emoji]
Example: "EPIC Marble Race: Barcelona vs Real Madrid Championship Battle 🏆"
```

**YouTube Description Structure**:
1. Engagement hook line
2. 3-4 sentence detailed competition explanation
3. Bullet points of what happens
4. Multiple CTAs (like, subscribe, comment, share)
5. 15-18 hashtags at end

---

### TikTok Strategy
**Goal**: Viral discovery, ultra-short, scroll-stopping, engagement-first

| Element | Limit | Strategy |
|---------|-------|----------|
| **Caption** | 150-250 chars | Ultra-short hook, punchy question, lots of emojis |
| **Hashtags** | 4-5 hashtags | Mix broad viral + niche specific, NO spaces |

**TikTok Caption Format**:
```
[Ultra-Short Viral Hook] + [Question] + [Emoji]
Example: "POV: Your team is losing 👀\n\nBarcelona vs Real Madrid - who you betting on? 💰"
```

**TikTok Hashtag Strategy**:
- 2 broad viral tags: `#fyp` `#viral` `#satisfying`
- 2-3 specific tags: `#marblerace` `#barcelona` `#realmadrid`
- Total: 4-5 hashtags max (TikTok algorithm prefers fewer)

---

## 📊 Platform Limits Enforced

### YouTube Shorts
✅ Title: Max 100 characters
✅ Description: Max 5000 characters
✅ Tags: 12-15 tags, each ≤ 32 chars, total ≤ 500 chars

### TikTok
✅ Caption: 150-250 chars recommended (max 2200)
✅ Hashtags: 4-5 hashtags, total ≤ 150 chars

---

## 🔧 How It Works

### Generation Process

1. **LLM Generation** (Primary):
   - Calls Ollama with platform-specific instructions
   - Generates unique content for each platform
   - Parses JSON response with YouTube + TikTok data

2. **Fallback Templates** (If LLM fails):
   - Uses proven, high-quality templates
   - Different templates for each platform
   - Always respects limits

3. **Limit Enforcement**:
   - Automatically caps all content to platform limits
   - Trims intelligently at word boundaries
   - Preserves hashtags when trimming

---

## 📝 Example Output

### YouTube Shorts Example

**Title** (64 chars):
```
EPIC Marble Race: Barcelona vs Real Madrid Championship Battle 🏆
```

**Description** (919 chars):
```
Who do you think will win? Barcelona or Real Madrid? Vote in the comments!

🎯 THE COMPETITION:
Watch Barcelona and Real Madrid compete in the ultimate marble race championship!
Two rivals battle through spinning rotating rings and destructive obstacles.
Each round increases in difficulty with faster speeds and tighter gaps.
Only one can claim victory!

⚡ WHAT HAPPENS:
• Marbles race through challenging rotating ring mazes
• Break through walls to escape faster
• Each round eliminates the slower competitor
• Final showdown determines the ultimate champion

🔥 CALL TO ACTION:
👍 Like if you predicted the winner
💬 Comment your favorite rival
🔔 Subscribe for daily marble race championships
🔗 Share with friends who love satisfying content

#shorts #YouTubeShorts #viral #satisfying #marblerace #marblerun
#simulation #championship #fyp #foryou #trending #watch
#football #barcelona #realmadrid #barcelonavsrealmadrid
```

**Tags** (18):
```
marble race, marble run, marbles, satisfying videos, asmr, oddly satisfying,
simulation, race, championship, competition, shorts, viral, relaxing,
mesmerizing, physics, football, barcelona, real madrid
```

---

### TikTok Example

**Caption** (76 chars):
```
POV: Your team is losing 👀

Barcelona vs Real Madrid - who you betting on? 💰
```

**Hashtags** (5):
```
#fyp #marblerace #satisfying #barcelona #realmadrid
```

---

## 🎯 Key Differences

| Aspect | YouTube Shorts | TikTok |
|--------|---------------|--------|
| **Length** | Longer (detailed) | Shorter (punchy) |
| **Tone** | SEO-focused, informative | Casual, trend-focused |
| **Hashtags** | 15-18 hashtags | 4-5 hashtags |
| **Description** | Multi-paragraph explanation | Single short hook |
| **Emojis** | 1-2 emojis | Multiple emojis |
| **Goal** | Search discovery + watch time | FYP viral discovery |

---

## 🚀 Usage

### From Your Code

```python
from metadata_generator import generate

# Generate metadata for both platforms
metadata = generate(
    theme_name="FOOTBALL",
    rival1="Barcelona",
    rival2="Real Madrid",
    champion="Barcelona",
    scores={"Barcelona": 3, "Real Madrid": 2},
    duration_secs=75.5
)

# Access YouTube metadata
yt_title = metadata["youtube"]["title"]
yt_description = metadata["youtube"]["description"]
yt_tags = metadata["youtube"]["tags"]

# Access TikTok metadata
tt_caption = metadata["tiktok"]["caption"]
tt_hashtags = metadata["tiktok"]["hashtags"]
```

### Test Generation

```bash
python test_metadata.py
```

---

## ✅ Validation

All limits are automatically validated:

```
YouTube Title <= 100 chars: [OK] (64/100)
YouTube Description <= 5000 chars: [OK] (919/5000)
YouTube Tags 10-18 items: [OK] (18 tags)
TikTok Caption <= 2200 chars: [OK] (76/2200)
TikTok Hashtags 3-5 items: [OK] (5 hashtags)
```

---

## 📁 Files

- `metadata_generator.py` - Main generation logic
- `youtube_uploader.py` - YouTube API integration
- `telegram_pusher.py` - TikTok notification via Telegram
- `test_metadata.py` - Validation test

---

## 🔑 Critical Rules

✗ **NO SPOILERS** - Never reveal winner or final score on either platform
✗ **NO COPYING** - YouTube and TikTok content must be strategically different
✓ **Build suspense** - Make viewers watch to the end
✓ **Ask questions** - Drive engagement and comments

---

**Status**: ✅ Production-Ready
**Last Updated**: February 8, 2026
