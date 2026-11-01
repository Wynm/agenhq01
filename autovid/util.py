import json
import logging
import os
import subprocess
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
log = logging.getLogger("autovid")
W, H, FPS = 1080, 1920, 30


def load_config(path=None):
    p = Path(path) if path else ROOT / "config.yaml"
    with open(p, encoding="utf-8") as f:
        cfg = yaml.safe_load(f) or {}
    # env overrides (handy from workflow_dispatch inputs / repo variables)
    if os.getenv("VIDEO_LANGUAGE"):
        cfg["language"] = os.environ["VIDEO_LANGUAGE"]
    if os.getenv("VIDEO_VOICE"):
        cfg["voice"] = os.environ["VIDEO_VOICE"]
    if os.getenv("PUBLISHERS") is not None and os.getenv("PUBLISHERS").strip():
        cfg["publishers"] = [x.strip() for x in os.environ["PUBLISHERS"].split(",") if x.strip()]
    return cfg


def run(cmd, **kw):
    log.debug("RUN %s", " ".join(map(str, cmd)))
    r = subprocess.run([str(c) for c in cmd], capture_output=True, text=True, **kw)
    if r.returncode != 0:
        raise RuntimeError(f"command failed ({r.returncode}): {' '.join(map(str, cmd))}\n{r.stderr[-3000:]}")
    return r.stdout


def media_duration(path) -> float:
    out = run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", path])
    return float(out.strip())


def read_json(path, default):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default


def write_json(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
