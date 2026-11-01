"""ffmpeg assembly: per-scene segment (background + burned captions + voice) -> concat -> optional music."""
import random
import re

from PIL import Image

from .textrender import caption_png, draw_block, font
from .util import FPS, H, ROOT, W, log, media_duration, run

VENC = ["-c:v", "libx264", "-preset", "veryfast", "-crf", "21", "-pix_fmt", "yuv420p", "-r", str(FPS)]
AENC = ["-c:a", "aac", "-b:a", "160k", "-ar", "48000", "-ac", "2"]


def chunk_text(text, max_words=6):
    """Split a sentence into short caption chunks (keeps punctuation)."""
    raw = [p.strip() for p in re.split(r"(?<=[،,.!?؟:;])\s+", text) if p.strip()]
    parts = []
    for p in raw:  # glue very short pieces to the previous one so captions don't flash
        if parts and (len(p.split()) < 3 or len(parts[-1].split()) < 3) and len((parts[-1] + " " + p).split()) <= max_words + 2:
            parts[-1] += " " + p
        else:
            parts.append(p)
    chunks = []
    for p in parts:
        words = p.split()
        n = max(1, -(-len(words) // max_words))
        size = -(-len(words) // n)
        chunks += [" ".join(words[i:i + size]) for i in range(0, len(words), size)]
    return chunks


def header_png(title, brand, out, font_name, show_title, progress=None):
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    if progress is not None:  # little scene-progress dots at the bottom
        from PIL import ImageDraw
        d = ImageDraw.Draw(img)
        i, n = progress
        x0 = W / 2 - (n * 34) / 2
        for k in range(n):
            r = 11 if k == i else 7
            cx, cy = x0 + k * 34 + 17, H - 150
            d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(255, 255, 255, 235 if k <= i else 110))
    draw_block(img, brand, font(font_name, 44), 120, W - 200, fill=(255, 255, 255), stroke_w=3, box=(0, 0, 0, 110))
    if show_title:
        draw_block(img, title, font(font_name, 78), 380, W - 140, fill=(255, 221, 51), stroke_w=6, box=(0, 0, 0, 120))
    img.save(out)
    return out


def build_segment(i, scene, title, brand, font_name, workdir, n=1):
    dur = scene["duration"]
    bg = scene["bg"]
    # captions timed proportionally to text length within the scene's audio
    chunks = chunk_text(scene["text"])
    speech = dur - 0.25
    total = sum(len(c) for c in chunks)
    inputs, t = [], 0.0
    for j, c in enumerate(chunks):
        d = speech * len(c) / total
        png = caption_png(c, workdir / f"cap_{i:02d}_{j:02d}.png", font_name)
        inputs.append((png, t, t + d if j < len(chunks) - 1 else dur))
        t += d
    head = header_png(title, brand, workdir / f"head_{i:02d}.png", font_name, show_title=(i == 0), progress=(i, n))

    cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error"]
    if bg["type"] == "video":
        cmd += ["-stream_loop", "-1", "-i", bg["path"]]
        base = (f"[0:v]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},fps={FPS},setsar=1,"
                f"eq=brightness=-0.08:saturation=1.1[b0]")
    else:
        cmd += ["-loop", "1", "-framerate", str(FPS), "-i", bg["path"]]
        # gentle pan over a slightly bigger image (cheap Ken-Burns)
        bw, bh = int(W * 1.12), int(H * 1.12)
        base = (f"[0:v]scale={bw}:{bh}:force_original_aspect_ratio=increase,crop={bw}:{bh},"
                f"crop={W}:{H}:x='(iw-{W})*t/{dur:.2f}':y='(ih-{H})*(1-t/{dur:.2f})',setsar=1,"
                f"eq=brightness=-0.05[b0]")
    cmd += ["-i", scene["audio"], "-i", head]
    for png, _, _ in inputs:
        cmd += ["-i", png]
    filt = [base, "[b0][2:v]overlay=0:0[v0]"]
    last = "v0"
    for k, (_, a, b) in enumerate(inputs):
        filt.append(f"[{last}][{k + 3}:v]overlay=0:0:enable='between(t,{a:.3f},{b:.3f})'[v{k + 1}]")
        last = f"v{k + 1}"
    filt.append(f"[1:a]apad,atrim=0:{dur:.3f},asetpts=N/SR/TB[a]")
    out = workdir / f"seg_{i:02d}.mp4"
    cmd += ["-filter_complex", ";".join(filt), "-map", f"[{last}]", "-map", "[a]", "-t", f"{dur:.3f}",
            *VENC, *AENC, str(out)]
    run(cmd)
    return out


def assemble(scenes, title, brand, font_name, out_path, workdir, music_volume=0.0):
    segs = [build_segment(i, s, title, brand, font_name, workdir, len(scenes)) for i, s in enumerate(scenes)]
    lst = workdir / "concat.txt"
    lst.write_text("".join(f"file '{p.resolve()}'\n" for p in segs))
    joined = workdir / "joined.mp4"
    run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst,
         "-c", "copy", joined])
    music = sorted((ROOT / "assets" / "music").glob("*.mp3"))
    if music and music_volume > 0:
        track = random.choice(music)
        log.info("background music: %s", track.name)
        run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", joined, "-stream_loop", "-1", "-i", track,
             "-filter_complex", f"[1:a]volume={music_volume}[m];[0:a][m]amix=inputs=2:duration=first:normalize=0[a]",
             "-map", "0:v", "-map", "[a]", "-c:v", "copy", *AENC, "-movflags", "+faststart", out_path])
    else:
        run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", joined, "-c", "copy",
             "-movflags", "+faststart", out_path])
    return media_duration(out_path)
