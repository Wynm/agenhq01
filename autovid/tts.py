"""Voice-over with edge-tts (free Microsoft neural voices). One mp3 per scene -> exact timing."""
import asyncio

import edge_tts

from .util import log, media_duration


async def _say(text, voice, rate, out):
    for attempt in range(3):
        try:
            await edge_tts.Communicate(text, voice, rate=rate).save(str(out))
            return
        except Exception as e:  # network hiccups
            log.warning("edge-tts failed (%s), retry %s", e, attempt + 1)
            await asyncio.sleep(3)
    raise RuntimeError("edge-tts failed 3 times")


def synthesize_scenes(scenes, voice, rate, workdir):
    """Writes scene_XX.mp3 and sets scene['audio'], scene['duration']."""
    async def go():
        for i, s in enumerate(scenes):
            out = workdir / f"voice_{i:02d}.mp3"
            await _say(s["text"], voice, rate, out)
            s["audio"] = str(out)
            s["duration"] = media_duration(out) + 0.25  # small breath between scenes
    asyncio.run(go())
    return scenes
