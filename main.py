"""
Entry point. Run this daily (via cron, GitHub Actions, or manually):

    python main.py

Requires YOUTUBE_API_KEY env var at minimum. Email vars optional (see
emailer.py / README.md).
"""

import sys
import config
from youtube_module import fetch_trending_shorts, YouTubeAPIError
from instagram_module import fetch_trending_reels
import report
from emailer import send_digest


def main():
    print("[info] Fetching YouTube Shorts...")
    try:
        yt_rows = fetch_trending_shorts()
    except YouTubeAPIError as e:
        print(f"[error] {e}")
        sys.exit(1)
    print(f"[info] Got {len(yt_rows)} YouTube Shorts.")

    print("[info] Fetching Instagram Reels (if configured)...")
    ig_rows = fetch_trending_reels()
    print(f"[info] Got {len(ig_rows)} Instagram Reels.")

    all_rows = yt_rows + ig_rows
    if not all_rows:
        print("[warn] No data collected. Check your API key/quota and try again.")
        sys.exit(0)

    csv_path = report.save_csv(all_rows)
    print(f"[info] CSV saved: {csv_path}")

    history_path = report.append_history(all_rows)
    print(f"[info] History updated: {history_path}")

    dashboard_path = report.build_html_dashboard(all_rows)
    print(f"[info] Dashboard saved: {dashboard_path}")

    if config.SEND_EMAIL:
        send_digest(all_rows, dashboard_path)


if __name__ == "__main__":
    main()
