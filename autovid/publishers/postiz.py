"""Postiz (https://postiz.com, open-source social scheduler) public API adapter - PRIMARY publisher.

Env:
  POSTIZ_API_KEY       (required) Postiz -> Settings -> Public API -> copy key
  POSTIZ_API_URL       (optional) default https://api.postiz.com/public/v1 (cloud).
                       Self-hosted: https://YOUR-DOMAIN/api/public/v1
  POSTIZ_INTEGRATIONS  (optional) comma-separated channel ids to post to. Default: all enabled channels.
  POSTIZ_POST_TYPE     (optional) now | draft | schedule  (default: now). 'draft' = review in Postiz before it goes out.
  POSTIZ_TIKTOK_METHOD (optional) DIRECT_POST | UPLOAD (default DIRECT_POST; UPLOAD = goes to TikTok inbox)
Docs: https://docs.postiz.com/public-api
"""
import datetime as dt
import os
import time

import requests

REQUIRED = ["POSTIZ_API_KEY"]

# Postiz identifier -> our caption key
CAPTION_KEY = {"x": "x", "youtube": "youtube", "tiktok": "tiktok", "instagram": "instagram",
               "instagram-standalone": "instagram", "facebook": "facebook", "threads": "instagram"}
VIDEO_OK = {"youtube", "tiktok", "instagram", "instagram-standalone", "facebook", "x", "threads", "linkedin",
            "linkedin-page", "telegram", "bluesky", "mastodon", "pinterest", "vk"}


def _base():
    return (os.getenv("POSTIZ_API_URL") or "https://api.postiz.com/public/v1").rstrip("/")


def _h():
    return {"Authorization": os.environ["POSTIZ_API_KEY"]}


def _req(method, path, **kw):
    for attempt in range(4):
        r = requests.request(method, _base() + path, headers=_h(), timeout=300, **kw)
        if r.status_code >= 500 or r.status_code == 429:
            time.sleep(10 * (attempt + 1))
            continue
        if r.status_code >= 400:
            raise RuntimeError(f"Postiz {method} {path} -> {r.status_code}: {r.text[:500]}")
        return r.json() if r.text else {}
    raise RuntimeError(f"Postiz {method} {path} kept failing ({r.status_code}: {r.text[:300]})")


def list_integrations():
    return _req("GET", "/integrations")


def upload(video_path):
    with open(video_path, "rb") as f:
        return _req("POST", "/upload", files={"file": ("video.mp4", f, "video/mp4")})


def settings_for(identifier, meta, cfg):
    title = meta["title"][:100]
    tags = [t.lstrip("#") for t in meta["hashtags"].get("youtube", [])][:10]
    if identifier == "youtube":
        return {"__type": "youtube", "title": title if len(title) >= 2 else title + " .",
                "type": (cfg.get("youtube") or {}).get("privacy", "public"), "selfDeclaredMadeForKids": "no",
                "tags": [{"value": t, "label": t} for t in tags]}
    if identifier == "tiktok":
        return {"__type": "tiktok", "title": title[:90], "privacy_level": "PUBLIC_TO_EVERYONE", "duet": True,
                "stitch": True, "comment": True, "autoAddMusic": "no", "brand_content_toggle": False,
                "brand_organic_toggle": False, "video_made_with_ai": True,
                "content_posting_method": (os.getenv("POSTIZ_TIKTOK_METHOD") or "DIRECT_POST")}
    if identifier in ("instagram", "instagram-standalone"):
        return {"__type": identifier, "post_type": "post", "is_trial_reel": False, "collaborators": []}
    if identifier == "x":
        return {"__type": "x", "who_can_reply_post": "everyone", "community": "", "made_with_ai": True}
    if identifier in ("linkedin", "linkedin-page"):
        return {"__type": identifier, "post_as_images_carousel": False}
    return {"__type": identifier}


def publish(ctx):
    meta, cfg = ctx["meta"], ctx["cfg"]
    wanted = [x.strip() for x in os.getenv("POSTIZ_INTEGRATIONS", "").split(",") if x.strip()]
    channels = [c for c in list_integrations() if not c.get("disabled")]
    if wanted:
        channels = [c for c in channels if c["id"] in wanted]
    channels = [c for c in channels if c.get("identifier") in VIDEO_OK]
    if not channels:
        raise RuntimeError("No usable Postiz channels (connect accounts in Postiz, or check POSTIZ_INTEGRATIONS)")
    media = upload(ctx["video_path"])
    image = [{"id": media["id"], "path": media["path"], "thumbnailTimestamp": 1500}]
    posts = []
    for c in channels:
        ident = c["identifier"]
        text = meta["captions"].get(CAPTION_KEY.get(ident, "facebook")) or meta["description"]
        if ident == "x":
            text = text[:270]
        posts.append({"integration": {"id": c["id"]}, "value": [{"content": text, "image": image}],
                      "settings": settings_for(ident, meta, cfg)})
    body = {"type": (os.getenv("POSTIZ_POST_TYPE") or "now"),
            "date": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z"),
            "shortLink": False, "tags": [], "posts": posts}
    res = _req("POST", "/posts", json=body)
    return {"channels": [f"{c['identifier']}:{c.get('name')}" for c in channels], "response": res}
