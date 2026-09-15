"""
agent_config.py
Central settings for the video-generation agent pipeline. Secrets
(API keys) always come from environment variables — never hardcode
them here. See .env.example for the full list of what to set.
"""
import os

# --- Pipeline behavior -----------------------------------------------------
NICHE = "general / trending"     # passed to the scriptwriter agent
TARGET_SECONDS = 45               # spoken length target (Shorts cap is ~60s)
CAPTION_GROUP_SIZE = 4            # words per on-screen caption card
FONT_PATH = None                  # e.g. "assets/fonts/Poppins-Bold.ttf" for a
                                   # custom look; None = Pillow's bundled font

# --- Publishing --------------------------------------------------------
# Start here: every run uploads as UNLISTED, so nothing goes public without
# you checking it in YouTube Studio first. Once you trust the output, set
# the AUTO_PUBLISH env var to "true" (or flip PRIVACY_STATUS below) to make
# it fully hands-off.
AUTO_PUBLISH = os.environ.get("AUTO_PUBLISH", "false").lower() == "true"
PRIVACY_STATUS = "public" if AUTO_PUBLISH else "unlisted"

# --- Paths -------------------------------------------------------------
# TRENDING_OUTPUT_DIR must match config.OUTPUT_DIR in the existing tracker
# (main.py / report.py) — that's where trending_<date>.csv lands.
TRENDING_OUTPUT_DIR = "output"
VIDEOS_OUTPUT_DIR = os.path.join("output", "videos")
