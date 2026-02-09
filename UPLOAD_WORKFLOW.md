# Upload Workflow Documentation

## Overview

The system now handles **different upload workflows** for YouTube and TikTok:

- **YouTube**: Upload ONLY Part 1 automatically, save Part 2 metadata to file
- **TikTok**: Send BOTH videos + metadata file to P-Cloud via Telegram

---

## 🎯 Workflow Steps

### YouTube Upload (Automatic)

**Part 1:**
✅ Uploaded automatically to YouTube Shorts
✅ Uses platform-optimized metadata (SEO-focused, detailed, 15-18 hashtags)

**Part 2:**
✅ Metadata saved to text file: `part2_metadata_[session_id].txt`
✅ **NOT uploaded** (for manual upload later)
✅ File contains: Title, Description, Tags, TikTok reference

---

### TikTok Workflow (via P-Cloud + Telegram)

**Step 1: Clean P-Cloud Folder**
```
P:\avy\shorts\  [DELETE ALL FILES]
```

**Step 2: Copy Files**
```
P:\avy\shorts\
├── [part1_video].mp4        ← Part 1 video
├── [part2_video].mp4        ← Part 2 video
└── part2_metadata_[id].txt  ← Metadata file
```

**Step 3: Send Telegram Notification**
- Metadata for Video 1 (Part 1)
- Metadata for Video 2 (Part 2)
- Location of files in P-Cloud

---

## 📁 Final P-Cloud State

After each generation, `P:\avy\shorts\` contains **exactly 3 files**:

1. **Part 1 video** - Ready for TikTok upload
2. **Part 2 video** - Ready for TikTok upload
3. **Metadata file** - YouTube Part 2 upload instructions

---

## 📝 Metadata File Format

**File**: `part2_metadata_[session_id].txt`

**Contents**:
```
======================================================================
  PART 2 METADATA - YouTube Shorts
======================================================================

TITLE:
[SEO-optimized title for Part 2]

======================================================================
DESCRIPTION:
======================================================================
[Detailed multi-paragraph description with 15-18 hashtags]

======================================================================
TAGS:
======================================================================
marble race, marble run, satisfying, asmr, [etc...]

======================================================================
  TikTok Metadata (Reference)
======================================================================

CAPTION:
[Ultra-short punchy caption for Part 2]

HASHTAGS:
#fyp #marblerace #satisfying [etc...]

======================================================================
Generated: 2026-02-08 19:45:23
======================================================================
```

---

## 📲 Telegram Notification Format

**Message**:
```
🎬 NEW TIKTOK VIDEOS READY (2 PARTS)
========================================

📹 VIDEO 1 (Part 1)
────────────────────────────────────────
📝 CAPTION:
[Caption for Part 1]

🏷️ HASHTAGS:
#fyp #marblerace #satisfying #barcelona #realmadrid

========================================

📹 VIDEO 2 (Part 2)
────────────────────────────────────────
📝 CAPTION:
[Caption for Part 2]

🏷️ HASHTAGS:
#fyp #marblerace #viral #barcelona #realmadrid

========================================
📁 All files in: P:\avy\shorts
   - Part 1 video
   - Part 2 video
   - Metadata file

🎯 Upload BOTH videos to TikTok with their respective captions!
```

---

## 🔧 Configuration

### Enable Auto-Upload

**File**: `production_config.py`

```python
# Upload & Publishing
AUTO_UPLOAD = True      # Enable YouTube Part 1 auto-upload
AUTO_TELEGRAM = True    # Enable P-Cloud sync + Telegram notification
```

### P-Cloud Path

**File**: `my_credentials.py`

```python
PCLOUD_SYNC_DIR = "P:/avy/shorts"  # Your P-Cloud sync folder
```

---

## 🚀 Usage

### Generate Videos with Auto-Upload

```bash
python main_story_mode.py
```

**What happens:**
1. Generates Part 1 and Part 2 videos
2. **YouTube**:
   - ✅ Uploads Part 1 automatically
   - ✅ Saves Part 2 metadata to file
3. **TikTok**:
   - ✅ Cleans P:\avy\shorts
   - ✅ Copies Part 1, Part 2, metadata file
   - ✅ Sends Telegram notification

---

## 📊 Upload Summary

| Platform | Part 1 | Part 2 |
|----------|--------|--------|
| **YouTube** | ✅ Auto-uploaded | 📄 Metadata file only |
| **TikTok** | 📁 In P-Cloud | 📁 In P-Cloud |
| **Telegram** | 📲 Metadata sent | 📲 Metadata sent |

---

## 🎯 Manual Upload Steps

### YouTube Part 2 (Manual)

1. Open the metadata file: `part2_metadata_[session_id].txt`
2. Go to YouTube Studio → Upload
3. Select Part 2 video
4. Copy-paste:
   - **Title** from metadata file
   - **Description** from metadata file
   - **Tags** from metadata file
5. Publish

### TikTok (Manual)

1. Open P-Cloud folder: `P:\avy\shorts`
2. Open your Telegram notification
3. Upload **Part 1 video** to TikTok:
   - Use Caption from "VIDEO 1 (Part 1)"
   - Use Hashtags from "VIDEO 1 (Part 1)"
4. Upload **Part 2 video** to TikTok:
   - Use Caption from "VIDEO 2 (Part 2)"
   - Use Hashtags from "VIDEO 2 (Part 2)"

---

## 🔍 Verification

After running `main_story_mode.py`, verify:

### YouTube
- [ ] Part 1 uploaded successfully
- [ ] YouTube URL displayed in console
- [ ] Part 2 metadata file created in output directory

### P-Cloud
- [ ] Folder cleaned (old files deleted)
- [ ] Part 1 video present
- [ ] Part 2 video present
- [ ] Metadata file present
- [ ] **Total: Exactly 3 files**

### Telegram
- [ ] Notification received
- [ ] Video 1 caption and hashtags visible
- [ ] Video 2 caption and hashtags visible
- [ ] P-Cloud location shown

---

## 📁 File Locations

```
StoryVideo/
├── match_recordings/
│   ├── [session_id]_part1_final.mp4          ← Generated video
│   ├── [session_id]_part2_final.mp4          ← Generated video
│   └── part2_metadata_[session_id].txt       ← Part 2 metadata
│
└── youtube_uploads.json                       ← Upload history (Part 1 only)

P:\avy\shorts\                                 ← P-Cloud sync folder
├── [session_id]_part1_final.mp4              ← For TikTok
├── [session_id]_part2_final.mp4              ← For TikTok
└── part2_metadata_[session_id].txt           ← Backup
```

---

## 🎨 Platform-Specific Metadata

Both platforms get **different** metadata:

### YouTube (SEO-Focused)
- Title: 100 chars, includes "Marble Race"
- Description: Detailed, 3-4 paragraphs, 15-18 hashtags
- Tags: 12-15 SEO keywords

### TikTok (Viral-Focused)
- Caption: Ultra-short (150-250 chars), punchy hook
- Hashtags: 4-5 hashtags only (#fyp, #marblerace, etc.)

---

## ⚙️ Advanced Configuration

### Disable Auto-Upload

If you want to manually upload everything:

**File**: `production_config.py`
```python
AUTO_UPLOAD = False      # Disable YouTube auto-upload
AUTO_TELEGRAM = False    # Disable P-Cloud sync
```

### Change P-Cloud Folder

**File**: `my_credentials.py`
```python
PCLOUD_SYNC_DIR = "D:/YourCustomPath/videos"  # Custom path
```

---

## 🐛 Troubleshooting

### Part 1 Not Uploading

**Check**:
1. `AUTO_UPLOAD = True` in production_config.py
2. YouTube credentials configured (youtube_auth/client_secret.json)
3. Internet connection active

### Telegram Not Sending

**Check**:
1. `AUTO_TELEGRAM = True` in production_config.py
2. TELEGRAM_BOT_TOKEN configured in my_credentials.py
3. TELEGRAM_CHAT_ID configured in my_credentials.py

### P-Cloud Folder Issues

**Check**:
1. `PCLOUD_SYNC_DIR = "P:/avy/shorts"` in my_credentials.py
2. P-Cloud drive mounted and accessible
3. Write permissions on the folder

---

## ✅ Success Indicators

**Console Output**:
```
======================================================================
  PUBLISHING
======================================================================

  [YouTube] Uploading Part 1 ONLY...
  ✅ Part 1 uploaded: https://www.youtube.com/watch?v=...

  [YouTube] Part 2: Saving metadata to file (NOT uploading)...
  ✅ Part 2 metadata saved: c:\AI\StoryVideo\match_recordings\part2_metadata_....txt

  [TikTok/Telegram] Syncing videos to P-Cloud...

  [pcloud] 🗑️  Cleaning P-Cloud folder: P:/avy/shorts
  [pcloud] ✅ Cleaned 3 old file(s)

  [pcloud] 📹 Copying Part 1...
  [pcloud] ✅ Part 1 copied (15.4 MB)

  [pcloud] 📹 Copying Part 2...
  [pcloud] ✅ Part 2 copied (20.5 MB)

  [pcloud] 📄 Copying metadata file...
  [pcloud] ✅ Metadata copied

  [pcloud] 📂 Final P-Cloud folder contents: 3 files
    - part1_final.mp4
    - part2_final.mp4
    - part2_metadata.txt

  [telegram] 📲 Sending TikTok metadata for BOTH videos...
  [telegram] ✅ Metadata sent successfully!

======================================================================
  ✅ TIKTOK WORKFLOW COMPLETE
======================================================================
  P-Cloud location: P:/avy/shorts
  Files: Part 1 + Part 2 + Metadata (3 files)
  Telegram notification: Sent ✅
======================================================================
```

---

**Status**: ✅ Production-Ready
**Last Updated**: February 8, 2026
