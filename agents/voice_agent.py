"""
voice_agent.py
Turns script text into narration audio using edge-tts (Microsoft Edge's
online neural voices). Completely free, no API key, no signup.

Bonus: edge-tts reports word-level timing as it synthesizes, so we get
perfectly-synced caption timestamps for free — no separate speech-to-
text pass (e.g. Whisper) is needed to caption our own narration.

Setup:
    pip install edge-tts

To see all available free voices, run in your terminal:
    edge-tts --list-voices
"""
import edge_tts

DEFAULT_VOICE = "en-US-AndrewNeural"  # confident, natural — good for narration
# Other popular free options: "en-US-AriaNeural", "en-GB-RyanNeural",
# "en-IN-PrabhatNeural", "en-US-GuyNeural"


def synthesize(text: str, out_path: str, voice: str = DEFAULT_VOICE,
               rate: str = "+8%") -> list:
    """
    Writes narration audio to `out_path` (mp3) and returns word-level
    timestamps in seconds:
        [{"text": "word", "start": 0.32, "end": 0.55}, ...]
    """
    communicate = edge_tts.Communicate(text, voice, rate=rate)
    words = []
    audio_bytes = bytearray()

    for chunk in communicate.stream_sync():
        if chunk["type"] == "audio":
            audio_bytes.extend(chunk["data"])
        elif chunk["type"] == "WordBoundary":
            words.append({
                "text": chunk["text"],
                "start": chunk["offset"] / 10_000_000,
                "end": (chunk["offset"] + chunk["duration"]) / 10_000_000,
            })

    if not audio_bytes:
        raise RuntimeError(
            "edge-tts returned no audio — check your internet connection; "
            "it calls Microsoft's free online voice service."
        )

    with open(out_path, "wb") as f:
        f.write(audio_bytes)

    return words


if __name__ == "__main__":
    import sys
    import json
    text = sys.argv[1] if len(sys.argv) > 1 else (
        "This is a test of the free narration agent."
    )
    timestamps = synthesize(text, "test_narration.mp3")
    print(json.dumps(timestamps, indent=2))
