"""Direct YouTube Data API v3 upload (backup publisher, uploads as a Short).
Env: YT_CLIENT_ID, YT_CLIENT_SECRET, YT_REFRESH_TOKEN (OAuth for YOUR channel, scope youtube.upload).
Note: videos uploaded by an unverified Google Cloud app are locked to 'private' until the app passes YouTube's audit."""
import json
import os

import requests

REQUIRED = ["YT_CLIENT_ID", "YT_CLIENT_SECRET", "YT_REFRESH_TOKEN"]


def _token():
    r = requests.post("https://oauth2.googleapis.com/token", data={
        "client_id": os.environ["YT_CLIENT_ID"], "client_secret": os.environ["YT_CLIENT_SECRET"],
        "refresh_token": os.environ["YT_REFRESH_TOKEN"], "grant_type": "refresh_token"}, timeout=30)
    r.raise_for_status()
    return r.json()["access_token"]


def publish(ctx):
    meta, cfg = ctx["meta"], ctx["cfg"]
    yt = cfg.get("youtube") or {}
    title = meta["title"]
    if "#shorts" not in title.lower():
        title = (title[:90] + " #Shorts")
    body = {"snippet": {"title": title[:100], "description": meta["captions"].get("youtube", meta["description"])[:4900],
                        "tags": [t.lstrip("#") for t in meta["hashtags"].get("youtube", [])][:15],
                        "categoryId": str(yt.get("category_id", "28")), "defaultLanguage": meta["language"]},
            "status": {"privacyStatus": yt.get("privacy", "public"), "selfDeclaredMadeForKids": False}}
    tok = _token()
    size = os.path.getsize(ctx["video_path"])
    r = requests.post("https://www.googleapis.com/upload/youtube/v3/videos",
                      params={"uploadType": "resumable", "part": "snippet,status"},
                      headers={"Authorization": f"Bearer {tok}", "Content-Type": "application/json; charset=UTF-8",
                               "X-Upload-Content-Type": "video/mp4", "X-Upload-Content-Length": str(size)},
                      data=json.dumps(body), timeout=60)
    r.raise_for_status()
    with open(ctx["video_path"], "rb") as f:
        up = requests.put(r.headers["Location"], data=f, headers={"Content-Type": "video/mp4"}, timeout=900)
    up.raise_for_status()
    vid = up.json()["id"]
    return {"video_id": vid, "url": f"https://youtube.com/shorts/{vid}"}
