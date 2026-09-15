"""
script_agent.py
Turns a trending topic (pulled from your existing A1 trend tracker) into
an ORIGINAL short-form video script using Google's Gemini API free tier.

Setup (free, no card required):
    1. pip install google-genai
    2. Get a key: https://aistudio.google.com/apikey
    3. export GEMINI_API_KEY="your-key"

Free tier is rate-limited (not credit-limited) — plenty for one video a
day. Model name is read from GEMINI_MODEL so you can bump it later
without touching code; check https://aistudio.google.com for the
current free-tier model list if this one is ever retired.
"""
import json
import os
import re

from google import genai
from google.genai import types

DEFAULT_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")

PROMPT_TEMPLATE = """You are a scriptwriter for a viral, faceless YouTube Shorts channel.

Topic / trending video title: "{topic}"
Niche: {niche}
Target length: {seconds} seconds spoken aloud (about {words} words)

Write an ORIGINAL short-form script inspired by why this topic is
trending right now. Do not copy any specific creator's wording, jokes,
or exact phrasing — write new commentary/facts/narrative in your own
voice. Keep sentences short and punchy; this will be read aloud by a
text-to-speech voice and needs a hook in the first line.

Return ONLY valid JSON, no markdown code fences, no extra commentary,
matching this exact shape:

{{
  "title": "short punchy YouTube title, under 60 characters",
  "hook": "first 1-2 sentences, must grab attention immediately",
  "body": ["sentence 1", "sentence 2", "sentence 3"],
  "cta": "one short closing line (e.g. follow for more, comment your take)",
  "on_screen_title": "3-6 word caption for the opening title card",
  "visual_keywords": ["concrete filmable scene 1", "scene 2", "scene 3", "scene 4", "scene 5"]
}}

"visual_keywords" must be concrete, filmable nouns/scenes (for a stock
photo/video search) that match the script content — not abstract ideas.
"""


def _extract_json(text: str) -> dict:
    text = text.strip()
    text = re.sub(r"^```(json)?", "", text).strip()
    text = re.sub(r"```$", "", text).strip()
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError(f"No JSON object found in model output:\n{text}")
    return json.loads(match.group(0))


def generate_script(topic: str, niche: str = "general / trending",
                     target_seconds: int = 45) -> dict:
    """Returns a script dict — see PROMPT_TEMPLATE for the exact shape."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "Set GEMINI_API_KEY — get a free key at https://aistudio.google.com/apikey"
        )

    client = genai.Client(api_key=api_key)
    words = int(target_seconds * 2.5)  # ~150 wpm spoken pace
    prompt = PROMPT_TEMPLATE.format(
        topic=topic, niche=niche, seconds=target_seconds, words=words
    )

    response = client.models.generate_content(
        model=DEFAULT_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(temperature=0.9, max_output_tokens=1024),
    )
    data = _extract_json(response.text)

    required = {"title", "hook", "body", "cta", "on_screen_title", "visual_keywords"}
    missing = required - data.keys()
    if missing:
        raise ValueError(f"Model output missing fields: {missing}")
    return data


def full_narration_text(script: dict) -> str:
    """Flattens the script dict into the exact text handed to the voice agent."""
    lines = [script["hook"], *script["body"], script["cta"]]
    return " ".join(line.strip() for line in lines if line.strip())


if __name__ == "__main__":
    import sys
    topic = sys.argv[1] if len(sys.argv) > 1 else "cats doing parkour"
    result = generate_script(topic)
    print(json.dumps(result, indent=2))
