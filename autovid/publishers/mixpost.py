"""Mixpost adapter - UNTESTED STUB. Only Mixpost Pro/Enterprise have a REST API (Mixpost Lite has none).
Kept so the pipeline can switch later. Env: MIXPOST_URL (e.g. https://mixpost.example.com/mixpost),
MIXPOST_TOKEN (personal access token), MIXPOST_WORKSPACE (workspace uuid), MIXPOST_ACCOUNTS (comma ids).
Verify endpoints against your Mixpost version docs before enabling."""
import os

import requests

REQUIRED = ["MIXPOST_URL", "MIXPOST_TOKEN", "MIXPOST_WORKSPACE", "MIXPOST_ACCOUNTS"]


def publish(ctx):
    base = f"{os.environ['MIXPOST_URL'].rstrip('/')}/api/{os.environ['MIXPOST_WORKSPACE']}"
    h = {"Authorization": "Bearer " + os.environ["MIXPOST_TOKEN"], "Accept": "application/json"}
    with open(ctx["video_path"], "rb") as f:
        r = requests.post(base + "/media", headers=h, files={"file": ("video.mp4", f, "video/mp4")}, timeout=300)
    r.raise_for_status()
    media_id = r.json().get("id")
    accounts = [int(a) for a in os.environ["MIXPOST_ACCOUNTS"].split(",") if a.strip()]
    body = {"accounts": accounts, "tags": [], "date": None, "time": None, "schedule_now": True,
            "versions": [{"account_id": 0, "is_original": True,
                          "content": [{"body": ctx["meta"]["captions"].get("facebook", ctx["meta"]["description"]),
                                       "media": [media_id]}]}]}
    r = requests.post(base + "/posts", headers=h, json=body, timeout=60)
    r.raise_for_status()
    return r.json()
