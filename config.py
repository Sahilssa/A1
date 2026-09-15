"""
Configuration for the trend tracker.
Edit KEYWORDS and REGION to match what you actually want to track.
Nothing here is a secret — API keys/passwords go in environment variables
(see README.md), never in this file.
"""

# ---- YouTube settings -------------------------------------------------

# Country to bias/region-restrict results (ISO 3166-1 alpha-2).
REGION_CODE = "IN"

# Keywords/niches to search for. IMPORTANT: YouTube's search API only
# returns solid results with a real keyword — an empty/broad "no filter"
# mode is unreliable (confirmed: it returns ~0 results in practice), so
# always keep at least a few real terms here. Mix broad + niche terms.
KEYWORDS = [
    "viral shorts",
    "trending video",
    "cafe",
    "coffee shop",
    "restaurant reels",
]

# How far back to look for "recently published" candidates (hours).
LOOKBACK_HOURS = 48

# Max results to pull per keyword search (YouTube API max is 50/page).
RESULTS_PER_KEYWORD = 25

# Shorts are currently defined as <= 180 seconds (3 minutes) by YouTube.
MAX_SHORT_DURATION_SECONDS = 180

# How many videos to keep in the final ranked report.
TOP_N = 25

# ---- Output settings ----------------------------------------------------

DATA_DIR = "data"          # historical JSON snapshots land here
OUTPUT_DIR = "output"      # daily CSV + HTML dashboard land here

# ---- Email settings (values pulled from env vars at runtime) -----------
# Required env vars if you want email digests:
#   EMAIL_HOST      e.g. smtp.gmail.com
#   EMAIL_PORT      e.g. 587
#   EMAIL_USER      your sending address
#   EMAIL_PASS      app password (NOT your normal password)
#   EMAIL_TO        comma-separated recipient list
SEND_EMAIL = True
