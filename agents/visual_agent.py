"""
visual_agent.py
Fetches background visuals matching the script's visual_keywords.

Two providers, both free:
  1. Pollinations.ai AI image generation — NO API key, no signup at all.
     Used automatically if you set nothing up. Great for zero-setup runs.
  2. Pexels stock photos — needs a free key (PEXELS_API_KEY) from
     https://www.pexels.com/api/. Real photography instead of
     AI-generated images; used automatically once the key is set.

Either way, output is a list of local JPEG paths, one per keyword.
"""
import os
from urllib.parse import quote

import requests

POLLINATIONS_URL = (
    "https://image.pollinations.ai/prompt/{prompt}"
    "?width=1080&height=1920&nologo=true&seed={seed}"
)
PEXELS_SEARCH_URL = "https://api.pexels.com/v1/search"


def _fetch_pollinations(keyword: str, out_path: str, seed: int) -> str:
    url = POLLINATIONS_URL.format(prompt=quote(keyword), seed=seed)
    resp = requests.get(url, timeout=60)
    resp.raise_for_status()
    with open(out_path, "wb") as f:
        f.write(resp.content)
    return out_path


def _fetch_pexels(keyword: str, out_path: str, api_key: str):
    headers = {"Authorization": api_key}
    params = {"query": keyword, "orientation": "portrait", "per_page": 1}
    resp = requests.get(PEXELS_SEARCH_URL, headers=headers, params=params, timeout=30)
    resp.raise_for_status()
    photos = resp.json().get("photos", [])
    if not photos:
        return None
    img_url = photos[0]["src"]["portrait"]
    img_resp = requests.get(img_url, timeout=60)
    img_resp.raise_for_status()
    with open(out_path, "wb") as f:
        f.write(img_resp.content)
    return out_path


def get_visuals(keywords: list, out_dir: str) -> list:
    """Downloads/generates one image per keyword, returns local file paths."""
    os.makedirs(out_dir, exist_ok=True)
    pexels_key = os.environ.get("PEXELS_API_KEY")
    paths = []

    for i, keyword in enumerate(keywords):
        out_path = os.path.join(out_dir, f"visual_{i:02d}.jpg")
        try:
            result = None
            if pexels_key:
                result = _fetch_pexels(keyword, out_path, pexels_key)
            if not result:
                _fetch_pollinations(keyword, out_path, seed=i)
            paths.append(out_path)
        except Exception as exc:  # noqa: BLE001 — keep the pipeline going
            print(f"[visual_agent] failed to fetch '{keyword}': {exc}")

    return paths


if __name__ == "__main__":
    import sys
    kws = sys.argv[1:] or ["sunrise over mountains", "coffee cup on desk"]
    print(get_visuals(kws, "test_visuals"))
