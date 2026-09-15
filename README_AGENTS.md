# AI Agent Pipeline (Trend → Script → Voice → Video → YouTube)

Extends your existing trend tracker: instead of just a dashboard, this
turns the #1 trending topic into an original faceless Short and uploads
it — **unlisted, for you to review** — every time you run it. Everything
below is free.

```
Trend Analyst (already built)  ──▶  Scriptwriter agent (Gemini free tier)
                                          │
                                          ▼
                                    Voice agent (edge-tts, free)
                                          │
                                          ▼
                                    Visual agent (Pollinations/Pexels, free)
                                          │
                                          ▼
                                    Editor agent (MoviePy + Pillow, free)
                                          │
                                          ▼
                                    Publisher agent (YouTube Data API, free)
```

## 1. Drop these files into your A1 repo

```
A1/
├── agents/
│   ├── __init__.py
│   ├── script_agent.py
│   ├── voice_agent.py
│   ├── visual_agent.py
│   ├── editor_agent.py
│   └── publish_agent.py
├── agent_config.py
├── run_agent_pipeline.py
├── requirements_agents.txt
└── .env.example
```

These sit next to your existing `main.py`, `config.py`, `youtube_module.py`,
etc. — nothing in your current tracker needs to change.

## 2. Install the extra dependencies

```
pip install -r requirements_agents.txt
```

(`ffmpeg` must be on your system PATH — Mac: `brew install ffmpeg`,
Ubuntu/Debian: `sudo apt install ffmpeg`, Windows: download from
ffmpeg.org and add it to PATH.)

## 3. Get your free API key(s)

**Required — Gemini (writes the script):**
1. https://aistudio.google.com/apikey → Create API key. No card needed.
2. `export GEMINI_API_KEY="your-key"`

**Optional — Pexels (real stock photos instead of AI-generated ones):**
1. https://www.pexels.com/api/ → sign up → copy your key.
2. `export PEXELS_API_KEY="your-key"`
3. Skip this and the pipeline still works — it falls back to
   Pollinations.ai, which needs zero signup.

**Required for publishing — YouTube OAuth (different from your tracker's
API key, which is read-only):**
1. Same Google Cloud project as your tracker → **APIs & Services →
   Credentials → Create Credentials → OAuth client ID**.
2. If prompted, configure the OAuth consent screen first: User type
   "External", fill in the required fields, add your own Google account
   under "Test users" (you don't need to publish the consent screen for
   personal use).
3. Application type: **Desktop app**. Create it, download the JSON.
4. Save it as `client_secret.json` in the repo root. **Add it to
   `.gitignore` — never commit it.**
5. First time you run the pipeline, a browser window opens asking you to
   log in and approve upload access. After that, `token.json` is saved
   and reused automatically — no more browser prompts.

## 4. Run it

```
python main.py                 # 1. refresh today's trending data (your existing tracker)
python run_agent_pipeline.py   # 2. turn the #1 trend into a video and upload it
```

Other ways to run it:
```
python run_agent_pipeline.py --rank 3          # use the 3rd-ranked trend instead
python run_agent_pipeline.py --topic "..."     # skip the tracker, use your own topic
```

Output lands in `output/videos/<topic-slug>/`:
`narration.mp3`, `visuals/`, and `final.mp4`. The console prints an
`https://youtu.be/...` link once it's uploaded.

## 5. Review-then-publish workflow (what you asked for)

By default every upload is **unlisted** — it exists on YouTube but only
people with the link can see it, and it doesn't affect your channel
publicly. The pipeline prints the link every run:

1. Open the link (or YouTube Studio on your phone) and watch it.
2. Happy with it? Open YouTube Studio → Content → find the video →
   change visibility to **Public**.
3. Not happy? Delete it, tweak `agent_config.py` (niche, length, caption
   style), and re-run.

## 6. Going fully automatic later

Once you trust the output:
```
export AUTO_PUBLISH=true
```
Every future run then uploads straight to **public** — no review step.
You can flip this back to `false` any time.

## 7. Tuning

Edit `agent_config.py`:
- `NICHE` — steers the scriptwriter (e.g. `"personal finance for students"`)
- `TARGET_SECONDS` — spoken length target (keep under ~55s for Shorts)
- `CAPTION_GROUP_SIZE` — words per on-screen caption card (3–5 is typical)
- `FONT_PATH` — point this at a downloaded `.ttf` (e.g. a bold Google
  Font like "Anton" or "Poppins-Bold") for a punchier look; leave as
  `None` to use Pillow's built-in font with zero setup

Edit `agents/voice_agent.py` → `DEFAULT_VOICE` to change the narrator.
Run `edge-tts --list-voices` to see all free options.

## 8. Two honest caveats

- **Compute**: rendering video is heavier than the tracker's daily scan.
  GitHub Actions' free runners can technically do it, but I'd start by
  running `run_agent_pipeline.py` locally (or on a free-tier VM you
  already have) rather than wiring it into `daily_run.yml` — you can
  automate the trigger later once you've seen a few runs work.
- **YouTube policy**: YouTube has tightened rules around fully automated,
  low-effort "reused/inauthentic" content for monetization eligibility.
  Original commentary/narration (which this pipeline generates, not
  reposted clips) is the safer side of that line, but keeping a human
  glance in the loop — which unlisted-by-default already gives you — is
  good practice, not just a formality, especially while you're starting out.

## 9. Extending later

- **Different visual style**: swap `visual_agent.py`'s output for an
  avatar clip, or feed `editor_agent.py` short video clips instead of
  stills (Pexels' video search endpoint returns downloadable MP4s the
  same way its photo endpoint does).
- **Multiple videos/day**: `run_agent_pipeline.py --rank N` loops
  trivially — call it a few times with different ranks in a shell loop,
  mindful of your ~6 free YouTube upload quota/day.
- **Instagram Reels**: once `instagram_module.py` is filled in, the same
  `run_agent_pipeline.py` topic-picking logic works for it — the video
  agents don't care which platform the trend came from.
