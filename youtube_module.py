"""
YouTube Shorts trend fetcher.

Uses the official YouTube Data API v3 (search.list + videos.list).
Needs an API key with "YouTube Data API v3" enabled in Google Cloud Console.
Free quota: 10,000 units/day. Each search.list call costs 100 units, so
keep KEYWORDS short or you'll burn quota fast (100 units * N keywords per run).

WHAT COUNTS AS "TRENDING" HERE:
YouTube has no public "trending Shorts" endpoint. This script approximates
it the way any serious tracker would: pull recently-published short-form
videos (<=180s, YouTube's official Shorts length cap), sorted by view count,
then rank by VELOCITY (views per hour since publish) rather than raw views —
a 2-day-old video with 500K views is "hotter" than a week-old video with 2M.
"""

import os
import re
import requests
from datetime import datetime, timezone, timedelta

import config

API_URL = "https://www.googleapis.com/youtube/v3"


class YouTubeAPIError(Exception):
    pass


def _get_api_key():
    key = os.environ.get("YOUTUBE_API_KEY")
    if not key:
        raise YouTubeAPIError(
            "YOUTUBE_API_KEY environment variable is not set. "
            "See README.md for how to get one."
        )
    return key


def _iso8601_duration_to_seconds(duration: str) -> int:
    """Convert ISO 8601 duration (e.g. 'PT1M32S') to seconds."""
    match = re.match(
        r"P(?:(\d+)D)?T(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", duration
    )
    if not match:
        return 0
    days, hours, minutes, seconds = (int(g) if g else 0 for g in match.groups())
    return days * 86400 + hours * 3600 + minutes * 60 + seconds


def _search_candidates(api_key, keyword, published_after):
    params = {
        "key": api_key,
        "part": "id",
        "type": "video",
        "order": "viewCount",
        "videoDuration": "short",  # API bucket: <4 min. We filter tighter later.
        "publishedAfter": published_after,
        "regionCode": config.REGION_CODE,
        "maxResults": config.RESULTS_PER_KEYWORD,
        "safeSearch": "moderate",
    }
    if keyword:
        params["q"] = keyword

    resp = requests.get(f"{API_URL}/search", params=params, timeout=30)
    if resp.status_code != 200:
        raise YouTubeAPIError(f"search.list failed: {resp.status_code} {resp.text}")
    items = resp.json().get("items", [])
    return [item["id"]["videoId"] for item in items if item.get("id", {}).get("videoId")]


def _fetch_video_details(api_key, video_ids):
    if not video_ids:
        return []
    results = []
    # videos.list allows up to 50 ids per call
    for i in range(0, len(video_ids), 50):
        batch = video_ids[i:i + 50]
        params = {
            "key": api_key,
            "part": "snippet,statistics,contentDetails",
            "id": ",".join(batch),
        }
        resp = requests.get(f"{API_URL}/videos", params=params, timeout=30)
        if resp.status_code != 200:
            raise YouTubeAPIError(f"videos.list failed: {resp.status_code} {resp.text}")
        results.extend(resp.json().get("items", []))
    return results


def _fetch_channel_subs(api_key, channel_ids):
    """Returns {channel_id: subscriber_count}."""
    subs = {}
    channel_ids = list(set(channel_ids))
    for i in range(0, len(channel_ids), 50):
        batch = channel_ids[i:i + 50]
        params = {
            "key": api_key,
            "part": "statistics",
            "id": ",".join(batch),
        }
        resp = requests.get(f"{API_URL}/channels", params=params, timeout=30)
        if resp.status_code != 200:
            continue
        for item in resp.json().get("items", []):
            stats = item.get("statistics", {})
            subs[item["id"]] = int(stats.get("subscriberCount", 0)) if not stats.get("hiddenSubscriberCount") else None
    return subs


def fetch_trending_shorts():
    """
    Returns a list of dicts, one per trending Short, sorted by velocity desc.
    Each dict has a consistent schema so it can sit alongside Instagram data
    in the same dashboard/report later.
    """
    api_key = _get_api_key()
    now = datetime.now(timezone.utc)
    published_after = (now - timedelta(hours=config.LOOKBACK_HOURS)).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )

    all_ids = set()
    for kw in config.KEYWORDS:
        try:
            ids = _search_candidates(api_key, kw, published_after)
            all_ids.update(ids)
        except YouTubeAPIError as e:
            print(f"[warn] search failed for keyword '{kw}': {e}")

    if not all_ids:
        return []

    details = _fetch_video_details(api_key, list(all_ids))

    # Filter to true Shorts by duration, drop anything missing stats
    shorts = []
    for item in details:
        duration_s = _iso8601_duration_to_seconds(
            item.get("contentDetails", {}).get("duration", "PT0S")
        )
        if duration_s == 0 or duration_s > config.MAX_SHORT_DURATION_SECONDS:
            continue
        stats = item.get("statistics", {})
        if "viewCount" not in stats:
            continue
        shorts.append(item)

    channel_ids = [s["snippet"]["channelId"] for s in shorts]
    sub_counts = _fetch_channel_subs(api_key, channel_ids)

    rows = []
    for s in shorts:
        snippet = s["snippet"]
        stats = s["statistics"]
        published_at = datetime.strptime(
            snippet["publishedAt"], "%Y-%m-%dT%H:%M:%SZ"
        ).replace(tzinfo=timezone.utc)
        hours_live = max((now - published_at).total_seconds() / 3600, 0.5)

        views = int(stats.get("viewCount", 0))
        likes = int(stats.get("likeCount", 0)) if "likeCount" in stats else 0
        comments = int(stats.get("commentCount", 0)) if "commentCount" in stats else 0

        velocity = round(views / hours_live, 1)
        engagement_rate = round(((likes + comments) / views) * 100, 3) if views else 0.0

        rows.append({
            "platform": "YouTube Shorts",
            "video_id": s["id"],
            "url": f"https://www.youtube.com/shorts/{s['id']}",
            "title": snippet.get("title", "")[:120],
            "channel": snippet.get("channelTitle", ""),
            "channel_subscribers": sub_counts.get(snippet["channelId"]),
            "published_at": snippet["publishedAt"],
            "hours_live": round(hours_live, 1),
            "duration_seconds": _iso8601_duration_to_seconds(
                s.get("contentDetails", {}).get("duration", "PT0S")
            ),
            "views": views,
            "likes": likes,
            "comments": comments,
            "engagement_rate_pct": engagement_rate,
            "views_per_hour": velocity,
            "keyword_bucket": None,  # filled in by caller if useful
        })

    rows.sort(key=lambda r: r["views_per_hour"], reverse=True)
    return rows[: config.TOP_N]
