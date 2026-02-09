"""
youtube_uploader.py  -  YouTube Data API v3  -  upload & done.

OAuth2 flow:
  First run  -> browser opens, you click "Allow", token saved.
  Every run after -> token.pickle is reused (auto-refreshed).

Auth files live in:
    youtube_auth/
        client_secret.json   <- you download this from Google Cloud Console
        token.pickle         <- auto-created, never touch it

Upload record is appended to youtube_uploads.json so you can
track everything that was ever posted.
"""

import os
import json
import pickle
from datetime import datetime

# Google SDK - installed via:  pip install google-api-python-client google-auth-oauthlib
from google.oauth2.credentials            import Credentials
from google_auth_oauthlib.flow            import InstalledAppFlow
from google.auth.transport.requests       import Request
from googleapiclient.discovery            import build
from googleapiclient.errors               import HttpError
from googleapiclient.http                 import MediaFileUpload

# ---------------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------------
AUTH_DIR        = "youtube_auth"                         # folder for secrets + token
CLIENT_SECRET   = os.path.join(AUTH_DIR, "client_secret.json")
TOKEN_CACHE     = os.path.join(AUTH_DIR, "token.pickle")
UPLOAD_LOG      = "youtube_uploads.json"                 # append-only history

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

# YouTube category IDs  (pick one)
CAT_ENTERTAINMENT = "24"
CAT_GAMING        = "20"
CAT_PEOPLE        = "22"

# Which category to use for our videos
DEFAULT_CATEGORY  = CAT_ENTERTAINMENT


# ---------------------------------------------------------------------------
# Auth  -  token cached forever after first browser consent
# ---------------------------------------------------------------------------
def _get_credentials():
    """Return valid Google creds.  Handles every auth state transparently."""
    os.makedirs(AUTH_DIR, exist_ok=True)

    creds = None

    # 1. try to load cached token
    if os.path.exists(TOKEN_CACHE):
        try:
            with open(TOKEN_CACHE, "rb") as fh:
                creds = pickle.load(fh)
        except Exception:
            creds = None

    # 2. if expired but has refresh_token -> refresh silently
    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
        except Exception:
            creds = None          # fall through to full flow

    # 3. if still nothing valid -> full OAuth browser flow
    if not creds or not creds.valid:
        if not os.path.exists(CLIENT_SECRET):
            print("\n" + "=" * 60)
            print("  ERROR: client_secret.json not found")
            print(f"  Expected at:  {os.path.abspath(CLIENT_SECRET)}")
            print("  See SETUP.md for how to create it.")
            print("=" * 60)
            return None

        print("  [upload] Opening browser for Google consent…")
        flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET, SCOPES)
        creds = flow.run_local_server(port=0)   # opens browser, waits for redirect

    # 4. persist (overwrite) the token
    with open(TOKEN_CACHE, "wb") as fh:
        pickle.dump(creds, fh)

    return creds


# ---------------------------------------------------------------------------
# Upload  -  the only public function main.py calls
# ---------------------------------------------------------------------------
def upload(video_path: str, metadata: dict) -> dict | None:
    """
    Parameters
    ----------
    video_path : str   path to the final .mp4
    metadata   : dict  keys: title, description, tags

    Returns
    -------
    dict  { "video_id", "url", "title", "upload_time" }
          or None if anything went wrong.
    """
    # --- auth ---
    creds = _get_credentials()
    if creds is None:
        print("  [upload] Auth failed - video NOT uploaded.")
        return None

    yt = build("youtube", "v3", credentials=creds)

    # --- sanity check ---
    if not os.path.exists(video_path):
        print(f"  [upload] File missing: {video_path}")
        return None

    title       = metadata["title"]
    description = metadata["description"]
    tags        = metadata["tags"]

    # --- API body -
    # snippet  : title, description, tags, category
    # status   : privacy, madeForKids declaration
    body = {
        "snippet": {
            "title":       title,
            "description": description,
            "tags":        tags,
            "categoryId":  DEFAULT_CATEGORY,
        },
        "status": {
            "privacyStatus":           "public",
            "selfDeclaredMadeForKids": False,
        },
    }

    # --- resumable upload  (4 MB chunks) ---
    media = MediaFileUpload(
        video_path,
        resumable=True,
        chunksize=4 * 1024 * 1024,
    )

    file_kb = os.path.getsize(video_path) // 1024
    print(f"  [upload] starting… ({file_kb} KB)")
    print(f"  [upload] title: {title}")

    try:
        request = yt.videos().insert(
            part="snippet,status",
            body=body,
            media_body=media,
        )

        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                print(f"  [upload] {int(status.progress() * 100)}%…", flush=True)

    except HttpError as e:
        print(f"  [upload] YouTube API error: {e}")
        return None
    except Exception as e:
        print(f"  [upload] unexpected error: {e}")
        return None

    # --- success ---
    video_id = response["id"]
    url      = f"https://www.youtube.com/watch?v={video_id}"

    record = {
        "video_id":    video_id,
        "url":         url,
        "title":       title,
        "upload_time": datetime.now().isoformat(),
        "local_path":  video_path,
        "file_kb":     file_kb,
    }

    print(f"  [upload] ✅  UPLOADED  ->  {url}")
    _append_record(record)
    return record


# ---------------------------------------------------------------------------
# Upload log  (append only)
# ---------------------------------------------------------------------------
def _append_record(record: dict):
    history = []
    if os.path.exists(UPLOAD_LOG):
        try:
            with open(UPLOAD_LOG, "r", encoding="utf-8") as fh:
                history = json.load(fh)
        except Exception:
            pass
    history.append(record)
    with open(UPLOAD_LOG, "w", encoding="utf-8") as fh:
        json.dump(history, fh, indent=2, ensure_ascii=False)