"""
publish_agent.py
Uploads the finished video to YouTube using the free YouTube Data API
v3 upload quota (1,600 units per upload; your existing 10,000/day quota
from the trend tracker gives you roughly 6 uploads/day for free).

IMPORTANT — this needs a DIFFERENT credential type than the tracker:
    - youtube_module.py (search) uses a simple API key.
    - Uploading requires OAuth2 (the API must act as *you*, with your
      consent), which is a one-time browser sign-in, then reused
      automatically via a saved refresh token.

One-time setup (free):
    1. https://console.cloud.google.com/ -> the same project you used
       for the YouTube Data API key.
    2. APIs & Services -> Credentials -> Create Credentials ->
       OAuth client ID -> Application type: "Desktop app".
    3. Download the JSON, save it as `client_secret.json` in this
       project's root (keep it out of git — add to .gitignore).
    4. First time you run this module, a browser window opens asking
       you to log in and approve "upload videos" access. After that,
       `token.json` is saved and reused — no more browser prompts.

Default behavior (REVIEW MODE): uploads as UNLISTED so nothing goes
public without you. Open YouTube Studio on your phone/laptop, check it,
and hit "Publish" yourself. Once you're comfortable, flip
`privacy_status="public"` (or set AUTO_PUBLISH=true, see agent_config.py)
for full automation.
"""
import os

import google.oauth2.credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
CLIENT_SECRET_FILE = "client_secret.json"
TOKEN_FILE = "token.json"


def _get_credentials():
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = google.oauth2.credentials.Credentials.from_authorized_user_file(
            TOKEN_FILE, SCOPES
        )
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(CLIENT_SECRET_FILE):
                raise RuntimeError(
                    f"{CLIENT_SECRET_FILE} not found — see the setup steps "
                    "at the top of publish_agent.py"
                )
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, "w") as f:
            f.write(creds.to_json())
    return creds


def upload_video(file_path: str, title: str, description: str,
                  tags: list = None, privacy_status: str = "unlisted",
                  category_id: str = "22") -> str:
    """
    Uploads `file_path` to YouTube. Returns the video ID.
    privacy_status: "private", "unlisted", or "public".
    category_id "22" = People & Blogs; see YouTube API docs for others.
    """
    creds = _get_credentials()
    youtube = build("youtube", "v3", credentials=creds)

    body = {
        "snippet": {
            "title": title[:100],
            "description": description[:5000],
            "tags": tags or [],
            "categoryId": category_id,
        },
        "status": {
            "privacyStatus": privacy_status,
            "selfDeclaredMadeForKids": False,
        },
    }

    media = MediaFileUpload(file_path, chunksize=-1, resumable=True, mimetype="video/mp4")
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"[publish_agent] upload progress: {int(status.progress() * 100)}%")

    video_id = response["id"]
    print(f"[publish_agent] uploaded as {privacy_status}: https://youtu.be/{video_id}")
    return video_id


if __name__ == "__main__":
    import sys
    path = sys.argv[1] if len(sys.argv) > 1 else "output/videos/latest/final.mp4"
    upload_video(path, title="Test upload", description="Testing the free agent pipeline.")
