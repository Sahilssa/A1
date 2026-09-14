"""
Turns a list of trend rows (see youtube_module schema) into:
  - a dated CSV file
  - an appended JSON history file (so you can track a video's rise over days)
  - a self-contained HTML dashboard
"""

import csv
import json
import os
from datetime import datetime, timezone

import config


def _timestamp():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def save_csv(rows):
    os.makedirs(config.OUTPUT_DIR, exist_ok=True)
    path = os.path.join(config.OUTPUT_DIR, f"trending_{_timestamp()}.csv")
    if not rows:
        return path
    fieldnames = list(rows[0].keys())
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    return path


def append_history(rows):
    os.makedirs(config.DATA_DIR, exist_ok=True)
    path = os.path.join(config.DATA_DIR, "history.jsonl")
    with open(path, "a", encoding="utf-8") as f:
        for row in rows:
            record = dict(row)
            record["snapshot_date"] = _timestamp()
            f.write(json.dumps(record) + "\n")
    return path


def _fmt(n):
    if n is None:
        return "—"
    if isinstance(n, float):
        return f"{n:,.1f}"
    return f"{n:,}"


def build_html_dashboard(rows, output_path=None):
    os.makedirs(config.OUTPUT_DIR, exist_ok=True)
    output_path = output_path or os.path.join(config.OUTPUT_DIR, "dashboard.html")

    yt_rows = [r for r in rows if r["platform"] == "YouTube Shorts"]
    ig_rows = [r for r in rows if r["platform"] == "Instagram Reels"]

    def table_rows(items):
        out = []
        for r in items:
            out.append(f"""
            <tr>
              <td class="rank">{items.index(r) + 1}</td>
              <td class="title"><a href="{r['url']}" target="_blank">{r['title']}</a>
                  <div class="channel">{r['channel']}</div></td>
              <td>{_fmt(r['views'])}</td>
              <td>{_fmt(r['views_per_hour'])}/hr</td>
              <td>{_fmt(r['likes'])}</td>
              <td>{_fmt(r['comments'])}</td>
              <td>{r['engagement_rate_pct']}%</td>
              <td>{_fmt(r['hours_live'])}h</td>
              <td>{_fmt(r['channel_subscribers'])}</td>
            </tr>""")
        return "".join(out)

    yt_table = table_rows(yt_rows)
    ig_section = ""
    if ig_rows:
        ig_section = f"""
        <h2>Instagram Reels</h2>
        <table>
          <thead><tr><th>#</th><th>Reel</th><th>Views</th><th>Velocity</th><th>Likes</th>
          <th>Comments</th><th>Eng. Rate</th><th>Age</th><th>Followers</th></tr></thead>
          <tbody>{table_rows(ig_rows)}</tbody>
        </table>
        """
    else:
        ig_section = """
        <h2>Instagram Reels</h2>
        <p class="empty-note">Not configured yet — see instagram_module.py to plug in a data source.</p>
        """

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Daily Trend Report — {_timestamp()}</title>
<style>
  :root {{
    --bg: #0f1115;
    --card: #171a21;
    --border: #2a2e38;
    --text: #e8eaed;
    --muted: #8b909c;
    --accent: #ff4d67;
    --accent2: #4d7fff;
  }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0; padding: 40px 24px;
    background: var(--bg); color: var(--text);
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  }}
  .wrap {{ max-width: 1080px; margin: 0 auto; }}
  h1 {{ font-size: 28px; margin-bottom: 4px; }}
  .subtitle {{ color: var(--muted); margin-bottom: 32px; font-size: 14px; }}
  h2 {{ font-size: 18px; margin: 40px 0 16px; border-left: 3px solid var(--accent); padding-left: 10px; }}
  table {{ width: 100%; border-collapse: collapse; background: var(--card);
           border: 1px solid var(--border); border-radius: 8px; overflow: hidden; }}
  th, td {{ padding: 10px 12px; text-align: left; font-size: 13px; border-bottom: 1px solid var(--border); }}
  th {{ color: var(--muted); font-weight: 600; text-transform: uppercase; font-size: 11px; letter-spacing: 0.04em; }}
  tr:last-child td {{ border-bottom: none; }}
  tr:hover td {{ background: #1d212b; }}
  .rank {{ color: var(--muted); font-weight: 700; width: 24px; }}
  .title a {{ color: var(--text); text-decoration: none; font-weight: 600; }}
  .title a:hover {{ color: var(--accent2); }}
  .channel {{ color: var(--muted); font-size: 12px; margin-top: 2px; }}
  .empty-note {{ color: var(--muted); font-size: 14px; }}
  .stat-row {{ display: flex; gap: 16px; margin-bottom: 8px; flex-wrap: wrap; }}
  .stat {{ background: var(--card); border: 1px solid var(--border); border-radius: 8px;
           padding: 14px 18px; min-width: 140px; }}
  .stat .num {{ font-size: 22px; font-weight: 700; }}
  .stat .label {{ color: var(--muted); font-size: 12px; margin-top: 2px; }}
</style>
</head>
<body>
<div class="wrap">
  <h1>Daily Trend Report</h1>
  <div class="subtitle">Generated {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')} · Ranked by views/hour (velocity), not raw views</div>

  <div class="stat-row">
    <div class="stat"><div class="num">{len(yt_rows)}</div><div class="label">YouTube Shorts tracked</div></div>
    <div class="stat"><div class="num">{_fmt(max((r['views_per_hour'] for r in yt_rows), default=0))}</div><div class="label">Top velocity (views/hr)</div></div>
    <div class="stat"><div class="num">{len(ig_rows)}</div><div class="label">Instagram Reels tracked</div></div>
  </div>

  <h2>YouTube Shorts — Top {len(yt_rows)}</h2>
  <table>
    <thead><tr><th>#</th><th>Short</th><th>Views</th><th>Velocity</th><th>Likes</th>
    <th>Comments</th><th>Eng. Rate</th><th>Age</th><th>Subscribers</th></tr></thead>
    <tbody>{yt_table}</tbody>
  </table>

  {ig_section}
</div>
</body>
</html>"""

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    return output_path
