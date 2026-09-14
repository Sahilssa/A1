# Daily Trend Tracker (YouTube Shorts, Instagram Reels framework)

Tracks recently-published YouTube Shorts, ranks them by **velocity**
(views per hour since publish — a better "trending" signal than raw views),
and delivers a daily HTML dashboard + CSV + optional email digest.

Instagram Reels tracking is stubbed out and ready to plug in — see
"Adding Instagram" below.

## What "accurate" means here

Be aware of what this can and can't guarantee:

- **YouTube**: uses the official Data API v3. Numbers are real and current
  as of the API call. There's no official "Shorts trending" endpoint, so
  this approximates it: pulls recently-published short-form videos
  (≤180s, YouTube's own Shorts length cap) sorted by view count, then
  re-ranks by views/hour. That's the same method serious trend-tracking
  tools use — it's a reasonable proxy, not a guarantee of matching
  YouTube's internal "Trending" tab exactly (that tab isn't public).
- **Instagram**: there is no public "what's trending on Instagram"
  endpoint from Meta. Any tool claiming to track it is using an
  unofficial scraper. This project ships the framework only — you decide
  if/when to add a scraper provider (see below).

## 1. Get a YouTube API key (free)

1. Go to https://console.cloud.google.com/
2. Create a project (or use an existing one)
3. Enable **"YouTube Data API v3"** under APIs & Services
4. Create credentials → API key
5. Free quota is 10,000 units/day. Each keyword search costs ~100 units,
   so with the default single broad keyword you can run this ~100x/day —
   more than enough for once daily.

## 2. Run it locally

```bash
pip install -r requirements.txt
export YOUTUBE_API_KEY="your-key-here"
python main.py
```

Output lands in `output/dashboard.html` (open in any browser) and
`output/trending_<date>.csv`. Historical data accumulates in
`data/history.jsonl` so you can track how a video's numbers changed
day over day.

## 3. Set up email digests (optional)

For Gmail:
1. Turn on 2-Step Verification on your Google account
2. Create an **App Password**: https://myaccount.google.com/apppasswords
3. Set these env vars (locally or as GitHub secrets — see below):
   ```
   EMAIL_HOST=smtp.gmail.com
   EMAIL_PORT=587
   EMAIL_USER=youraddress@gmail.com
   EMAIL_PASS=<the 16-char app password>
   EMAIL_TO=youraddress@gmail.com
   ```
Any other SMTP provider (Outlook, Zoho, etc.) works the same way — just
change EMAIL_HOST/PORT.

## 4. Run it automatically every day (recommended: GitHub Actions, free)

1. Push this folder to a **private** GitHub repo (private matters — your
   dashboard data will get committed back to it daily).
2. In the repo: Settings → Secrets and variables → Actions → New repository
   secret. Add `YOUTUBE_API_KEY` and, if using email, the 5 `EMAIL_*` vars
   from above.
3. Settings → Actions → General → make sure "Read and write permissions"
   is enabled for the workflow (needed so it can commit the daily dashboard
   back to the repo).
4. That's it — `.github/workflows/daily_run.yml` runs it every day at
   09:00 IST and commits the new `output/dashboard.html`. You can also
   trigger it manually from the Actions tab any time.
5. To actually *view* the dashboard from your phone/browser without
   pulling the repo: enable GitHub Pages (Settings → Pages → deploy from
   `output/` folder), or just open `output/dashboard.html` from GitHub's
   web UI (it'll show raw HTML — use https://htmlpreview.github.io/ pasted
   in front of the raw URL, or download it).

Alternative: run `python main.py` from your own machine's Task
Scheduler (Windows) or a cron job (Mac/Linux) if you don't want to use
GitHub Actions. GitHub Actions is recommended because it runs even when
your laptop is off.

## 5. Tune what it tracks

Edit `config.py`:
- `KEYWORDS` — list of niches/topics (e.g. `["cafe", "coffee", "barista"]`).
  Leave `[""]` for a broad, topic-agnostic scan.
- `REGION_CODE` — currently `"IN"`.
- `LOOKBACK_HOURS` — how "recent" a video must be to qualify (default 48h).
- `TOP_N` — how many results land in the final report (default 25).

## Adding Instagram later

Open `instagram_module.py` — it has a full docstring explaining the
options (Apify, RapidAPI, etc.), the exact data schema `fetch_trending_reels()`
needs to return, and a code sketch. Once you fill that one function in,
the dashboard, CSV, history, and email digest all automatically include
Instagram data alongside YouTube — no other file needs to change.

## Files

```
main.py                 — run this
config.py               — your settings (niches, region, etc.)
youtube_module.py       — YouTube Data API fetching + velocity ranking
instagram_module.py     — Instagram framework (not yet implemented)
report.py               — builds CSV, JSON history, HTML dashboard
emailer.py               — sends the email digest
requirements.txt
.github/workflows/daily_run.yml  — free daily automation
data/history.jsonl       — accumulates over time (created on first run)
output/                  — dashboard.html + CSVs land here
```
