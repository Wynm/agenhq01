"""Pluggable publishers. Each adapter: publish(ctx) -> dict. ctx keys: video_path, video_url, meta, cfg.

Only post to YOUR OWN accounts. No fake engagement, no mass-account spam.
"""
from . import mixpost, postiz, webhook, youtube

ADAPTERS = {"postiz": postiz, "webhook": webhook, "youtube": youtube, "mixpost": mixpost}
