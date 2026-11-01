"""Background visuals: Pexels stock video/photo (free API key) with a generated-gradient fallback."""
import os
import random

import requests
from PIL import Image, ImageDraw, ImageFilter

from .util import H, W, log

PALETTES = [((15, 32, 80), (88, 28, 135)), ((8, 47, 73), (13, 148, 136)), ((30, 27, 75), (190, 24, 93)),
            ((17, 24, 39), (37, 99, 235)), ((20, 83, 45), (6, 95, 70)), ((69, 10, 10), (234, 88, 12))]


def gradient_slide(out, seed=None):
    rnd = random.Random(seed)
    c1, c2 = rnd.choice(PALETTES)
    big_w, big_h = int(W * 1.2), int(H * 1.2)
    img = Image.new("RGB", (big_w, big_h))
    d = ImageDraw.Draw(img)
    for y in range(big_h):
        t = y / big_h
        d.line([(0, y), (big_w, y)], fill=tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3)))
    glow = Image.new("RGBA", (big_w, big_h), (0, 0, 0, 0))
    g = ImageDraw.Draw(glow)
    for _ in range(7):
        r = rnd.randint(120, 420)
        x, y = rnd.randint(0, big_w), rnd.randint(0, big_h)
        g.ellipse([x - r, y - r, x + r, y + r], fill=(255, 255, 255, rnd.randint(18, 45)))
    glow = glow.filter(ImageFilter.GaussianBlur(60))
    img = Image.alpha_composite(img.convert("RGBA"), glow).convert("RGB")
    img.save(out, quality=92)
    return {"type": "image", "path": str(out)}


def _pexels_video(query, key, min_dur, out):
    r = requests.get("https://api.pexels.com/videos/search", headers={"Authorization": key},
                     params={"query": query, "orientation": "portrait", "per_page": 15, "size": "medium"}, timeout=30)
    r.raise_for_status()
    vids = [v for v in r.json().get("videos", []) if v.get("duration", 0) >= min(min_dur, 6)]
    random.shuffle(vids)
    for v in vids:
        files = [f for f in v.get("video_files", []) if f.get("height") and f.get("width")
                 and f["height"] > f["width"] and 960 <= f["height"] <= 2160 and f.get("file_type") == "video/mp4"]
        if not files:
            continue
        f = min(files, key=lambda f: abs(f["height"] - 1920))
        with requests.get(f["link"], stream=True, timeout=120) as resp:
            resp.raise_for_status()
            with open(out, "wb") as fh:
                for chunk in resp.iter_content(1 << 20):
                    fh.write(chunk)
        return {"type": "video", "path": str(out), "credit": f"Video by {v['user']['name']} on Pexels ({v['url']})",
                "pexels_id": v["id"]}
    return None


def _pexels_photo(query, key, out):
    r = requests.get("https://api.pexels.com/v1/search", headers={"Authorization": key},
                     params={"query": query, "orientation": "portrait", "per_page": 15}, timeout=30)
    r.raise_for_status()
    photos = r.json().get("photos", [])
    if not photos:
        return None
    p = random.choice(photos)
    data = requests.get(p["src"]["large2x"], timeout=60).content
    with open(out, "wb") as fh:
        fh.write(data)
    return {"type": "image", "path": str(out), "credit": f"Photo by {p['photographer']} on Pexels ({p['url']})"}


def fetch_backgrounds(scenes, workdir, seed=None):
    key = os.getenv("PEXELS_API_KEY", "").strip()
    if not key:
        log.warning("PEXELS_API_KEY not set -> using generated gradient backgrounds")
    used = set()
    for i, s in enumerate(scenes):
        bg = None
        if key:
            for q in s.get("keywords", []) + ["technology"]:
                try:
                    bg = _pexels_video(q, key, s["duration"], workdir / f"bg_{i:02d}.mp4")
                    if bg and bg.get("pexels_id") in used:
                        bg = None
                        continue
                    if not bg:
                        bg = _pexels_photo(q, key, workdir / f"bg_{i:02d}.jpg")
                except requests.RequestException as e:
                    log.warning("Pexels error for '%s': %s", q, e)
                if bg:
                    used.add(bg.get("pexels_id"))
                    break
        s["bg"] = bg or gradient_slide(workdir / f"bg_{i:02d}.jpg", seed=f"{seed}-{i}")
    return scenes
