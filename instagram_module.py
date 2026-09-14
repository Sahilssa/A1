"""
Instagram Reels trend fetcher — FRAMEWORK ONLY, not implemented.

WHY THIS ISN'T LIVE:
Instagram's official Graph API only returns data for accounts/pages you own
or manage — there is no legitimate endpoint for "what's trending across
Instagram right now." Getting that data means using a third-party scraper
(e.g. Apify's Instagram actors, RapidAPI Instagram endpoints, Bright Data).
These work, but: (1) they cost money, (2) they operate against Instagram's
Terms of Service, (3) they break whenever Instagram changes its site, more
often than YouTube's stable public API.

HOW TO PLUG A PROVIDER IN LATER:
Fill in fetch_trending_reels() below so it returns a list of dicts using
the EXACT SAME SCHEMA as youtube_module.fetch_trending_shorts(), just with
platform="Instagram Reels" and video_id/url pointing at the reel. Everything
downstream (report.py, dashboard, email) already knows how to merge and
rank both platforms together — you only need to fill in this one function.

Example shape for one row (copy this into your real implementation):

{
    "platform": "Instagram Reels",
    "video_id": "<reel shortcode>",
    "url": "https://www.instagram.com/reel/<shortcode>/",
    "title": "<caption, truncated>",
    "channel": "<@username>",
    "channel_subscribers": <follower count or None>,
    "published_at": "<ISO8601 timestamp>",
    "hours_live": <float>,
    "duration_seconds": <int>,
    "views": <int>,
    "likes": <int>,
    "comments": <int>,
    "engagement_rate_pct": <float>,
    "views_per_hour": <float>,
    "keyword_bucket": None,
}

A rough Apify integration would look like:

    from apify_client import ApifyClient
    client = ApifyClient(os.environ["APIFY_API_TOKEN"])
    run = client.actor("apify/instagram-reel-scraper").call(
        run_input={"hashtags": config.KEYWORDS, "resultsLimit": 50}
    )
    items = client.dataset(run["defaultDatasetId"]).list_items().items
    # ... map `items` fields into the schema above ...
"""

import config


def fetch_trending_reels():
    """
    Returns [] until you wire up a real provider (see module docstring).
    Kept as a live no-op (not a raised exception) so the rest of the
    pipeline runs end-to-end on YouTube data alone without crashing.
    """
    print(
        "[info] Instagram module not yet configured — skipping. "
        "See instagram_module.py for how to plug in a provider."
    )
    return []
