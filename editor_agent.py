"""
editor_agent.py
Assembles the final vertical (1080x1920) MP4 from:
  - narration audio (mp3)
  - word-level timestamps (from voice_agent)
  - a list of background image paths (from visual_agent)
  - an opening title card

Free stack: Pillow (text rendering) + MoviePy 2.x + ffmpeg (already on
your system or installed via `pip install moviepy`).

No ImageMagick dependency — captions are rendered as PNGs with Pillow,
then composited as image clips, which is more portable across
Windows/Mac/Linux than MoviePy's default TextClip backend.
"""
import os
from PIL import Image, ImageDraw, ImageFont
from moviepy import (
    ImageClip,
    AudioFileClip,
    CompositeVideoClip,
)

VIDEO_SIZE = (1080, 1920)  # w, h — vertical, Shorts/Reels/TikTok
FPS = 30


def _load_font(font_path, size):
    if font_path and os.path.exists(font_path):
        return ImageFont.truetype(font_path, size)
    # Pillow ships a scalable default font — works with zero setup.
    return ImageFont.load_default(size=size)


def _wrap_text(draw, text, font, max_width):
    words = text.split()
    lines, current = [], ""
    for word in words:
        trial = f"{current} {word}".strip()
        if draw.textlength(trial, font=font) <= max_width:
            current = trial
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def render_caption_png(text, font_path=None, font_size=88, max_width=940,
                        fill="white", stroke_fill="black", stroke_width=6):
    """Renders one caption card (transparent PNG) sized to fit its text."""
    font = _load_font(font_path, font_size)
    scratch = Image.new("RGBA", (10, 10))
    draw = ImageDraw.Draw(scratch)
    lines = _wrap_text(draw, text.upper(), font, max_width)

    line_height = font_size + 18
    height = line_height * len(lines) + 40
    img = Image.new("RGBA", (max_width + 80, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    y = 20
    for line in lines:
        w = draw.textlength(line, font=font)
        x = (img.width - w) / 2
        draw.text((x, y), line, font=font, fill=fill,
                   stroke_width=stroke_width, stroke_fill=stroke_fill)
        y += line_height
    return img


def _cover_resize(img: Image.Image, size):
    """Resize + center-crop an image to exactly fill `size` (no letterboxing)."""
    target_w, target_h = size
    src_w, src_h = img.size
    scale = max(target_w / src_w, target_h / src_h)
    new_w, new_h = int(src_w * scale + 0.5), int(src_h * scale + 0.5)
    img = img.resize((new_w, new_h), Image.LANCZOS)
    left = (new_w - target_w) / 2
    top = (new_h - target_h) / 2
    return img.crop((left, top, left + target_w, top + target_h))


def _group_words(word_timestamps, group_size=4):
    """Groups word-level timestamps into short multi-word caption cards."""
    groups = []
    for i in range(0, len(word_timestamps), group_size):
        chunk = word_timestamps[i:i + group_size]
        groups.append({
            "text": " ".join(w["text"] for w in chunk),
            "start": chunk[0]["start"],
            "end": chunk[-1]["end"],
        })
    return groups


def build_video(narration_path, word_timestamps, visual_paths, title_text,
                 out_path, font_path=None, caption_group_size=4,
                 video_size=VIDEO_SIZE, fps=FPS, tmp_dir="tmp_editor"):
    """
    Renders the final MP4 to `out_path`. Returns out_path.
    """
    os.makedirs(tmp_dir, exist_ok=True)
    audio = AudioFileClip(narration_path)
    total_duration = audio.duration

    if not visual_paths:
        raise ValueError("visual_agent returned no usable background images")

    # --- background layer: sequence of cover-cropped, slowly zooming stills
    per_visual = total_duration / len(visual_paths)
    bg_clips = []
    for i, path in enumerate(visual_paths):
        img = Image.open(path).convert("RGB")
        img = _cover_resize(img, video_size)
        prepped_path = os.path.join(tmp_dir, f"bg_{i:02d}.jpg")
        img.save(prepped_path, quality=90)

        clip = (
            ImageClip(prepped_path)
            .with_duration(per_visual)
            .with_start(i * per_visual)
            .resized(lambda t, i=i: 1 + 0.05 * (t / max(per_visual, 0.01)))
            .with_position("center")
        )
        bg_clips.append(clip)

    # --- caption layer: word-grouped cards synced to narration
    caption_clips = []
    for group in _group_words(word_timestamps, caption_group_size):
        png = render_caption_png(group["text"], font_path=font_path)
        png_path = os.path.join(tmp_dir, f"cap_{group['start']:.2f}.png")
        png.save(png_path)
        dur = max(group["end"] - group["start"], 0.05)
        clip = (
            ImageClip(png_path)
            .with_duration(dur)
            .with_start(group["start"])
            .with_position(("center", int(video_size[1] * 0.72)))
        )
        caption_clips.append(clip)

    # --- title card: shown for the first ~2.5s over the background
    title_png = render_caption_png(title_text, font_path=font_path,
                                    font_size=100, fill="#FFD400")
    title_path = os.path.join(tmp_dir, "title.png")
    title_png.save(title_path)
    title_clip = (
        ImageClip(title_path)
        .with_duration(min(2.5, total_duration))
        .with_start(0)
        .with_position(("center", int(video_size[1] * 0.10)))
    )

    final = CompositeVideoClip(
        bg_clips + [title_clip] + caption_clips, size=video_size
    ).with_duration(total_duration).with_audio(audio)

    final.write_videofile(
        out_path, fps=fps, codec="libx264", audio_codec="aac",
        preset="medium", threads=4, logger=None,
    )
    return out_path
