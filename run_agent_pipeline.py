"""
run_agent_pipeline.py
Orchestrates the full pipeline: pick a trending topic from your existing
tracker's output -> write a script -> narrate it -> fetch visuals ->
render the video -> upload to YouTube (unlisted, for review, by default).

Usage:
    python run_agent_pipeline.py                 # uses today's #1 trending topic
    python run_agent_pipeline.py --rank 3         # uses the 3rd-ranked trend instead
    python run_agent_pipeline.py --topic "..."    # skip the tracker, use your own topic

Setup required — see README_AGENTS.md. In short:
    export GEMINI_API_KEY="..."          # free: https://aistudio.google.com/apikey
    export PEXELS_API_KEY="..."          # optional, free: https://www.pexels.com/api/
    # client_secret.json in this folder  # free OAuth app, for YouTube upload
"""
import argparse
import csv
import glob
import os
import re
from datetime import datetime

import agent_config as cfg
from agents import script_agent, voice_agent, visual_agent, editor_agent, publish_agent


def _latest_trending_csv() -> str:
    pattern = os.path.join(cfg.TRENDING_OUTPUT_DIR, "trending_*.csv")
    files = sorted(glob.glob(pattern))
    if not files:
        raise FileNotFoundError(
            f"No trending_*.csv found in {cfg.TRENDING_OUTPUT_DIR}/ — run "
            "main.py (the trend tracker) first."
        )
    return files[-1]


def pick_topic(rank: int = 1) -> dict:
    """Reads the latest trending CSV and returns the row at `rank` (1-indexed),
    among YouTube Shorts rows, sorted by views_per_hour descending."""
    path = _latest_trending_csv()
    with open(path, newline="", encoding="utf-8") as f:
        rows = [r for r in csv.DictReader(f) if r.get("platform") == "YouTube Shorts"]
    if not rows:
        raise ValueError(f"No YouTube Shorts rows found in {path}")
    rows.sort(key=lambda r: float(r.get("views_per_hour") or 0), reverse=True)
    idx = min(max(rank, 1), len(rows)) - 1
    return rows[idx]


def _slugify(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:50]
    return slug or datetime.now().strftime("%Y%m%d-%H%M%S")


def run(topic: str = None, rank: int = 1) -> str:
    if topic:
        topic_title = topic
    else:
        row = pick_topic(rank)
        topic_title = row["title"]
        print(f"[pipeline] using trending topic: {topic_title}  "
              f"({row.get('views_per_hour')} views/hr)")

    work_dir = os.path.join(cfg.VIDEOS_OUTPUT_DIR, _slugify(topic_title))
    os.makedirs(work_dir, exist_ok=True)

    print("[pipeline] 1/5 generating script...")
    script = script_agent.generate_script(
        topic_title, niche=cfg.NICHE, target_seconds=cfg.TARGET_SECONDS
    )
    narration_text = script_agent.full_narration_text(script)

    print("[pipeline] 2/5 synthesizing narration...")
    narration_path = os.path.join(work_dir, "narration.mp3")
    word_timestamps = voice_agent.synthesize(narration_text, narration_path)

    print("[pipeline] 3/5 fetching visuals...")
    visual_paths = visual_agent.get_visuals(
        script["visual_keywords"], os.path.join(work_dir, "visuals")
    )

    print("[pipeline] 4/5 rendering video...")
    final_path = os.path.join(work_dir, "final.mp4")
    editor_agent.build_video(
        narration_path=narration_path,
        word_timestamps=word_timestamps,
        visual_paths=visual_paths,
        title_text=script["on_screen_title"],
        out_path=final_path,
        font_path=cfg.FONT_PATH,
        caption_group_size=cfg.CAPTION_GROUP_SIZE,
    )
    print(f"[pipeline] video ready: {final_path}")

    print(f"[pipeline] 5/5 uploading as {cfg.PRIVACY_STATUS}...")
    video_id = publish_agent.upload_video(
        final_path,
        title=script["title"],
        description=narration_text + "\n\n#shorts",
        tags=script["visual_keywords"],
        privacy_status=cfg.PRIVACY_STATUS,
    )

    url = f"https://youtu.be/{video_id}"
    if cfg.PRIVACY_STATUS != "public":
        print(f"[pipeline] uploaded UNLISTED for your review: {url}")
        print("[pipeline] check it in YouTube Studio and hit Publish when you're happy.")
    else:
        print(f"[pipeline] published: {url}")
    return url


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--topic", help="Skip the trend tracker, use this topic directly")
    parser.add_argument("--rank", type=int, default=1,
                         help="Use the Nth-ranked trending topic (default: 1)")
    args = parser.parse_args()
    run(topic=args.topic, rank=args.rank)
