"""
telegram_pusher.py - P-Cloud Sync + TikTok Metadata Notification (IMPROVED)

Changes from original:
- Moved API keys to secrets.py for security
- Added better error handling
- Added progress indication for file sync
- Improved logging
- Made P-Cloud path configurable
"""

import requests
import os
import shutil
import glob
import sys

# ---------------------------------------------------------------------------
# SECURE CONFIGURATION - Load from secrets.py
# ---------------------------------------------------------------------------
try:
    from my_credentials import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, PCLOUD_SYNC_DIR
except ImportError:
    print("\n" + "=" * 60)
    print("  ERROR: secrets.py not found!")
    print("=" * 60)
    print("  1. Copy secrets.py.example to secrets.py")
    print("  2. Fill in your Telegram bot token and chat ID")
    print("  3. Run again")
    print("=" * 60)
    sys.exit(1)

# Validate configuration
if not TELEGRAM_BOT_TOKEN or TELEGRAM_BOT_TOKEN == "your_bot_token_here":
    print("ERROR: TELEGRAM_BOT_TOKEN not configured in secrets.py")
    sys.exit(1)

if not TELEGRAM_CHAT_ID or TELEGRAM_CHAT_ID == "your_chat_id_here":
    print("ERROR: TELEGRAM_CHAT_ID not configured in secrets.py")
    sys.exit(1)


# ---------------------------------------------------------------------------
# P-CLOUD SYNC - Copy original video to cloud drive
# ---------------------------------------------------------------------------
def sync_to_pcloud(video_path):
    """
    Sync the original video file to P-Cloud drive.
    
    Process:
    1. Delete all existing files in P-Cloud directory
    2. Copy the new video to P-Cloud directory
    
    Parameters
    ----------
    video_path : str  (full path to the final video)
    
    Returns
    -------
    bool : True if successful, False otherwise
    """
    # Skip if P-Cloud is not configured
    if not PCLOUD_SYNC_DIR or PCLOUD_SYNC_DIR == "None":
        print("  [pcloud] [WARN]️  P-Cloud sync disabled (PCLOUD_SYNC_DIR not set)")
        return True  # Not an error, just skipped
    
    if not os.path.exists(video_path):
        print(f"  [pcloud] ❌ Error: Video file not found: {video_path}")
        return False
    
    # Create P-Cloud directory if it doesn't exist
    try:
        os.makedirs(PCLOUD_SYNC_DIR, exist_ok=True)
        print(f"  [pcloud] [OK] P-Cloud directory ready: {PCLOUD_SYNC_DIR}")
    except Exception as e:
        print(f"  [pcloud] ❌ Error: Cannot create P-Cloud directory: {e}")
        return False
    
    try:
        # 1. DELETE ALL FILES in P-Cloud directory (cleanup old videos)
        print(f"  [pcloud] 🗑️  Cleaning P-Cloud directory...")
        deleted_count = 0
        for file in glob.glob(os.path.join(PCLOUD_SYNC_DIR, "*")):
            try:
                if os.path.isfile(file):
                    os.remove(file)
                    deleted_count += 1
            except Exception as e:
                print(f"  [pcloud] [WARN]️  Could not delete {os.path.basename(file)}: {e}")
        
        if deleted_count > 0:
            print(f"  [pcloud] [OK] Deleted {deleted_count} old file(s)")
        
        # 2. COPY NEW VIDEO (original quality, no compression)
        video_filename = os.path.basename(video_path)
        pcloud_path = os.path.join(PCLOUD_SYNC_DIR, video_filename)
        
        file_size_mb = os.path.getsize(video_path) / (1024 * 1024)
        print(f"  [pcloud] ☁️  Syncing: {video_filename} ({file_size_mb:.1f} MB)")
        
        # Copy with progress indication
        shutil.copy2(video_path, pcloud_path)  # copy2 preserves metadata
        
        # Verify copy
        if os.path.exists(pcloud_path):
            copied_size_mb = os.path.getsize(pcloud_path) / (1024 * 1024)
            print(f"  [pcloud] ✅ Synced successfully ({copied_size_mb:.1f} MB)")
            print(f"  [pcloud] 📍 Location: {pcloud_path}")
            return True
        else:
            print(f"  [pcloud] ❌ Verification failed: File not found after copy")
            return False
        
    except Exception as e:
        print(f"  [pcloud] ❌ Sync failed: {e}")
        return False


# ---------------------------------------------------------------------------
# TELEGRAM TIKTOK NOTIFICATION - Send TikTok metadata only
# ---------------------------------------------------------------------------
def send_tiktok_notification(metadata):
    """
    Send a text notification to Telegram with TikTok metadata.
    
    The user will use this info to manually post the video to TikTok.
    
    Parameters
    ----------
    metadata : dict  { "youtube": {...}, "tiktok": {"caption": str, "hashtags": [str]} }
    
    Returns
    -------
    bool : True if sent successfully, False otherwise
    """
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    
    # Extract TikTok metadata
    tiktok = metadata.get("tiktok", {})
    caption = tiktok.get("caption", "No caption")
    hashtags = tiktok.get("hashtags", [])
    
    # Build message text
    message = "🎬 NEW TIKTOK VIDEO READY\n"
    message += "=" * 40 + "\n\n"
    
    message += "📝 CAPTION:\n"
    message += f"{caption}\n\n"
    
    message += "🏷️ HASHTAGS:\n"
    message += f"{' '.join(hashtags)}\n\n"
    
    message += "=" * 40 + "\n"
    
    if PCLOUD_SYNC_DIR and PCLOUD_SYNC_DIR != "None":
        message += f"📁 Video location: {PCLOUD_SYNC_DIR}\n"
    else:
        message += "📁 Check your output directory for the video\n"
    
    message += "🎯 Upload to TikTok with the caption and hashtags above!"
    
    # Telegram message length limit: 4096 characters
    if len(message) > 4096:
        message = message[:4093] + "..."
    
    try:
        print("  [telegram] 📲 Sending TikTok metadata...")
        
        data = {
            'chat_id': TELEGRAM_CHAT_ID,
            'text': message
        }
        
        response = requests.post(url, data=data, timeout=10)
        
        if response.status_code == 200:
            print("  [telegram] ✅ Metadata sent successfully!")
            return True
        else:
            print(f"  [telegram] ❌ Error: HTTP {response.status_code}")
            print(f"  [telegram] Response: {response.text[:200]}")
            return False
            
    except requests.exceptions.Timeout:
        print("  [telegram] ❌ Request timeout (check your internet connection)")
        return False
    except requests.exceptions.RequestException as e:
        print(f"  [telegram] ❌ Connection error: {e}")
        return False
    except Exception as e:
        print(f"  [telegram] ❌ Unexpected error: {e}")
        return False


# ---------------------------------------------------------------------------
# NEW: SYNC BOTH VIDEOS + METADATA - Called from main_story_mode.py
# ---------------------------------------------------------------------------
def sync_videos_and_notify(part1_path, part2_path, metadata_file, metadata_part1, metadata_part2):
    """
    Complete TikTok workflow:
    1. Clean P-Cloud folder (P:\avy\shorts)
    2. Copy Part 1 video to P-Cloud
    3. Copy Part 2 video to P-Cloud
    4. Copy metadata file to P-Cloud
    5. Send Telegram notification with metadata for BOTH videos

    Parameters
    ----------
    part1_path : str
        Path to Part 1 video
    part2_path : str
        Path to Part 2 video
    metadata_file : str
        Path to metadata text file
    metadata_part1 : dict
        { "youtube": {...}, "tiktok": {...} } for Part 1
    metadata_part2 : dict
        { "youtube": {...}, "tiktok": {...} } for Part 2

    Returns
    -------
    bool : True if all operations succeeded
    """
    print("\n" + "=" * 70)
    print("  TIKTOK: P-CLOUD SYNC + TELEGRAM NOTIFICATION")
    print("=" * 70)

    # Validate P-Cloud is configured
    if not PCLOUD_SYNC_DIR or PCLOUD_SYNC_DIR == "None":
        print("  [pcloud] ❌ P-Cloud sync disabled (PCLOUD_SYNC_DIR not set)")
        return False

    try:
        # === STEP 1: CLEAN P-CLOUD FOLDER ===
        print(f"\n  [pcloud] 🗑️  Cleaning P-Cloud folder: {PCLOUD_SYNC_DIR}")
        os.makedirs(PCLOUD_SYNC_DIR, exist_ok=True)

        deleted_count = 0
        for file in glob.glob(os.path.join(PCLOUD_SYNC_DIR, "*")):
            try:
                if os.path.isfile(file):
                    os.remove(file)
                    deleted_count += 1
            except Exception as e:
                print(f"  [pcloud] ⚠️  Could not delete {os.path.basename(file)}: {e}")

        print(f"  [pcloud] ✅ Cleaned {deleted_count} old file(s)")

        # === STEP 2: COPY PART 1 VIDEO ===
        print(f"\n  [pcloud] 📹 Copying Part 1...")
        part1_name = os.path.basename(part1_path)
        part1_dest = os.path.join(PCLOUD_SYNC_DIR, part1_name)
        shutil.copy2(part1_path, part1_dest)

        if os.path.exists(part1_dest):
            size_mb = os.path.getsize(part1_dest) / (1024 * 1024)
            print(f"  [pcloud] ✅ Part 1 copied ({size_mb:.1f} MB)")
        else:
            print(f"  [pcloud] ❌ Part 1 copy failed")
            return False

        # === STEP 3: COPY PART 2 VIDEO ===
        print(f"\n  [pcloud] 📹 Copying Part 2...")
        part2_name = os.path.basename(part2_path)
        part2_dest = os.path.join(PCLOUD_SYNC_DIR, part2_name)
        shutil.copy2(part2_path, part2_dest)

        if os.path.exists(part2_dest):
            size_mb = os.path.getsize(part2_dest) / (1024 * 1024)
            print(f"  [pcloud] ✅ Part 2 copied ({size_mb:.1f} MB)")
        else:
            print(f"  [pcloud] ❌ Part 2 copy failed")
            return False

        # === STEP 4: COPY METADATA FILE ===
        print(f"\n  [pcloud] 📄 Copying metadata file...")
        metadata_name = os.path.basename(metadata_file)
        metadata_dest = os.path.join(PCLOUD_SYNC_DIR, metadata_name)
        shutil.copy2(metadata_file, metadata_dest)

        if os.path.exists(metadata_dest):
            print(f"  [pcloud] ✅ Metadata copied")
        else:
            print(f"  [pcloud] ❌ Metadata copy failed")
            return False

        # === VERIFY FINAL STATE ===
        final_files = glob.glob(os.path.join(PCLOUD_SYNC_DIR, "*"))
        print(f"\n  [pcloud] 📂 Final P-Cloud folder contents: {len(final_files)} files")
        for file in final_files:
            print(f"    - {os.path.basename(file)}")

        if len(final_files) != 3:
            print(f"  [pcloud] ⚠️  Expected 3 files, found {len(final_files)}")

        # === STEP 5: SEND TELEGRAM NOTIFICATION ===
        print(f"\n  [telegram] 📲 Sending TikTok metadata for BOTH videos...")
        notify_ok = send_tiktok_notification_dual(metadata_part1, metadata_part2)

        # === SUMMARY ===
        print("\n" + "=" * 70)
        print("  ✅ TIKTOK WORKFLOW COMPLETE")
        print("=" * 70)
        print(f"  P-Cloud location: {PCLOUD_SYNC_DIR}")
        print(f"  Files: Part 1 + Part 2 + Metadata ({len(final_files)} files)")
        print(f"  Telegram notification: {'Sent ✅' if notify_ok else 'Failed ❌'}")
        print("=" * 70)

        return notify_ok

    except Exception as e:
        print(f"\n  [pcloud] ❌ Workflow failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def send_tiktok_notification_dual(metadata_part1, metadata_part2):
    """
    Send Telegram notification with TikTok metadata for BOTH videos.

    Parameters
    ----------
    metadata_part1 : dict
        { "tiktok": {"caption": str, "hashtags": [str]} } for Part 1
    metadata_part2 : dict
        { "tiktok": {"caption": str, "hashtags": [str]} } for Part 2

    Returns
    -------
    bool : True if sent successfully
    """
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

    # Extract TikTok metadata
    tt1 = metadata_part1.get("tiktok", {})
    tt2 = metadata_part2.get("tiktok", {})

    # Build message
    message = "🎬 NEW TIKTOK VIDEOS READY (2 PARTS)\n"
    message += "=" * 40 + "\n\n"

    message += "📹 VIDEO 1 (Part 1)\n"
    message += "─" * 40 + "\n"
    message += "📝 CAPTION:\n"
    message += f"{tt1.get('caption', 'No caption')}\n\n"
    message += "🏷️ HASHTAGS:\n"
    message += f"{' '.join(tt1.get('hashtags', []))}\n\n"

    message += "=" * 40 + "\n\n"

    message += "📹 VIDEO 2 (Part 2)\n"
    message += "─" * 40 + "\n"
    message += "📝 CAPTION:\n"
    message += f"{tt2.get('caption', 'No caption')}\n\n"
    message += "🏷️ HASHTAGS:\n"
    message += f"{' '.join(tt2.get('hashtags', []))}\n\n"

    message += "=" * 40 + "\n"

    if PCLOUD_SYNC_DIR and PCLOUD_SYNC_DIR != "None":
        message += f"📁 All files in: {PCLOUD_SYNC_DIR}\n"
        message += "   - Part 1 video\n"
        message += "   - Part 2 video\n"
        message += "   - Metadata file\n\n"

    message += "🎯 Upload BOTH videos to TikTok with their respective captions!"

    # Telegram limit: 4096 chars
    if len(message) > 4096:
        message = message[:4093] + "..."

    try:
        data = {
            'chat_id': TELEGRAM_CHAT_ID,
            'text': message
        }

        response = requests.post(url, data=data, timeout=10)

        if response.status_code == 200:
            print("  [telegram] ✅ Metadata sent successfully!")
            return True
        else:
            print(f"  [telegram] ❌ Error: HTTP {response.status_code}")
            return False

    except Exception as e:
        print(f"  [telegram] ❌ Error: {e}")
        return False


# ---------------------------------------------------------------------------
# OLD FUNCTION - Keep for backward compatibility
# ---------------------------------------------------------------------------
def sync_and_notify(video_path, metadata):
    """
    DEPRECATED: Use sync_videos_and_notify instead.

    Old workflow for single video sync.
    """
    print("\n  [WARN] Using deprecated sync_and_notify - use sync_videos_and_notify instead")

    sync_ok = sync_to_pcloud(video_path)
    notify_ok = send_tiktok_notification(metadata)

    return sync_ok and notify_ok


# ---------------------------------------------------------------------------
# TEST - Run this file directly to test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("  TELEGRAM PUSHER TEST MODE")
    print("=" * 70)
    
    # Test data
    test_metadata = {
        "youtube": {
            "title": "Test Video - Epic Marble Race",
            "description": "Test description",
            "tags": ["test", "marble race", "shorts"]
        },
        "tiktok": {
            "caption": "Who wins? Test A or Test B? 🏆\n\nWatch these rivals battle through spinning rings!",
            "hashtags": ["#test", "#marblerace", "#satisfying"]
        }
    }
    
    # Create a dummy test file
    test_video_path = "test_video.mp4"
    if not os.path.exists(test_video_path):
        print(f"\n  Creating dummy test file: {test_video_path}")
        with open(test_video_path, "wb") as f:
            f.write(b"test video content")
    
    # Run test
    result = sync_and_notify(test_video_path, test_metadata)
    
    # Cleanup
    if os.path.exists(test_video_path):
        os.remove(test_video_path)
    
    print(f"\n  Test result: {'✅ PASSED' if result else '❌ FAILED'}")