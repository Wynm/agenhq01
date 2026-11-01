"""Generic webhook: POSTs the video URL + per-platform captions as JSON (n8n, Make, Zapier, custom API...).
Env: POST_WEBHOOK_URL (required), POST_WEBHOOK_TOKEN (optional, sent as 'Authorization: Bearer ...')."""
import os

import requests

REQUIRED = ["POST_WEBHOOK_URL"]


def publish(ctx):
    meta = ctx["meta"]
    headers = {"Content-Type": "application/json"}
    if os.getenv("POST_WEBHOOK_TOKEN"):
        headers["Authorization"] = "Bearer " + os.environ["POST_WEBHOOK_TOKEN"]
    payload = {
        "video_url": ctx["video_url"], "title": meta["title"], "description": meta["description"],
        "captions": meta["captions"], "hashtags": meta["hashtags"], "language": meta["language"],
        "duration": meta["duration"], "id": meta["id"],
    }
    r = requests.post(os.environ["POST_WEBHOOK_URL"], json=payload, headers=headers, timeout=60)
    r.raise_for_status()
    return {"status": r.status_code, "body": r.text[:500]}
