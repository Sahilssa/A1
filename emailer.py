"""
Sends the daily digest by email using plain SMTP (works with Gmail App
Passwords, Outlook, or any SMTP provider). No paid email service required.
"""

import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime, timezone


def send_digest(rows, dashboard_html_path):
    host = os.environ.get("EMAIL_HOST")
    port = os.environ.get("EMAIL_PORT")
    user = os.environ.get("EMAIL_USER")
    password = os.environ.get("EMAIL_PASS")
    to_addrs = os.environ.get("EMAIL_TO")

    missing = [n for n, v in {
        "EMAIL_HOST": host, "EMAIL_PORT": port, "EMAIL_USER": user,
        "EMAIL_PASS": password, "EMAIL_TO": to_addrs,
    }.items() if not v]
    if missing:
        print(f"[info] Email skipped — missing env vars: {', '.join(missing)}")
        return False

    top5 = sorted(rows, key=lambda r: r["views_per_hour"], reverse=True)[:5]
    lines = [f"Daily Trend Digest — {datetime.now(timezone.utc).strftime('%Y-%m-%d')}", ""]
    lines.append(f"Tracked {len(rows)} short-form videos. Top 5 by velocity (views/hour):\n")
    for i, r in enumerate(top5, 1):
        lines.append(
            f"{i}. [{r['platform']}] {r['title']}\n"
            f"   {r['views']:,} views | {r['views_per_hour']:,.0f}/hr | "
            f"{r['engagement_rate_pct']}% engagement | {r['channel']}\n"
            f"   {r['url']}\n"
        )
    lines.append("\nFull dashboard is attached as an HTML file — open it in any browser.")
    body_text = "\n".join(lines)

    msg = MIMEMultipart("mixed")
    msg["Subject"] = f"Daily Trend Digest — {datetime.now(timezone.utc).strftime('%Y-%m-%d')}"
    msg["From"] = user
    msg["To"] = to_addrs
    msg.attach(MIMEText(body_text, "plain"))

    if dashboard_html_path and os.path.exists(dashboard_html_path):
        with open(dashboard_html_path, "rb") as f:
            attachment = MIMEText(f.read().decode("utf-8"), "html")
            attachment.add_header(
                "Content-Disposition", "attachment", filename="dashboard.html"
            )
            msg.attach(attachment)

    try:
        with smtplib.SMTP(host, int(port)) as server:
            server.starttls()
            server.login(user, password)
            server.sendmail(user, to_addrs.split(","), msg.as_string())
        print("[info] Email digest sent.")
        return True
    except Exception as e:
        print(f"[warn] Email send failed: {e}")
        return False
