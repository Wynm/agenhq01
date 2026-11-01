"""CLI.
  python -m autovid.main make [--topic "..."] [--out out]          -> out/<id>/video.mp4 + meta.json
  python -m autovid.main publish --meta out/<id>/meta.json [--video-url URL]
"""
import argparse
import datetime as dt
import json
import logging
import os
import shutil
import sys
from pathlib import Path

from .util import ROOT, load_config, log, write_json


def cmd_make(args):
    from . import assemble, script_gen, tts, visuals
    cfg = load_config(args.config)
    script = script_gen.generate_script(cfg, topic=args.topic or os.getenv("VIDEO_TOPIC") or None)
    vid_id = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%d-%H%M%S")
    outdir = Path(args.out) / vid_id
    work = outdir / "work"
    work.mkdir(parents=True, exist_ok=True)
    log.info("script: %s (%d scenes)", script["title"], len(script["scenes"]))
    scenes = tts.synthesize_scenes(script["scenes"], cfg["voice"], cfg.get("voice_rate", "+0%"), work)
    scenes = visuals.fetch_backgrounds(scenes, work, seed=vid_id)
    video = outdir / "video.mp4"
    duration = assemble.assemble(scenes, script["title"], cfg.get("brand", ""), cfg.get("font", "Cairo-Variable.ttf"),
                                 video, work, music_volume=float(cfg.get("music_volume") or 0))
    credits = sorted({s["bg"].get("credit") for s in scenes if s["bg"].get("credit")})
    captions = script_gen.build_captions(script, cfg)
    meta = {"id": vid_id, "title": script["title"], "topic": script.get("topic", ""), "language": cfg.get("language", "ar"),
            "voice": cfg["voice"], "duration": round(duration, 2), "description": script["description"],
            "hashtags": script["hashtags"], "captions": captions, "credits": credits,
            "script": [{"text": s["text"], "keywords": s["keywords"]} for s in scenes],
            "mock_script": not os.getenv("GEMINI_API_KEY")}
    write_json(outdir / "meta.json", meta)
    if not args.keep_work:
        shutil.rmtree(work, ignore_errors=True)
    if not args.no_history:
        script_gen.add_to_history(script, {"id": vid_id})
    log.info("DONE %s (%.1fs)", video, duration)
    gh_out = os.getenv("GITHUB_OUTPUT")
    if gh_out:
        with open(gh_out, "a") as f:
            f.write(f"video_dir={outdir}\nvideo_id={vid_id}\n")
    print(outdir)


def cmd_publish(args):
    from .publishers import ADAPTERS
    cfg = load_config(args.config)
    meta = json.loads(Path(args.meta).read_text(encoding="utf-8"))
    video_path = str(Path(args.meta).parent / "video.mp4")
    names = cfg.get("publishers") or []
    if not names:
        log.info("No publishers configured -> nothing posted (set PUBLISHERS or config.yaml publishers)")
        return
    ctx = {"video_path": video_path, "video_url": args.video_url, "meta": meta, "cfg": cfg}
    results, failed = {}, False
    for name in names:
        mod = ADAPTERS.get(name)
        if not mod:
            log.error("unknown publisher '%s' (known: %s)", name, ", ".join(ADAPTERS))
            failed = True
            continue
        missing = [k for k in getattr(mod, "REQUIRED", []) if not os.getenv(k)]
        if missing:
            log.warning("skip %s: missing secrets %s", name, ", ".join(missing))
            results[name] = {"skipped": f"missing {missing}"}
            continue
        try:
            results[name] = mod.publish(ctx)
            log.info("published via %s: %s", name, json.dumps(results[name], ensure_ascii=False)[:400])
        except Exception as e:
            failed = True
            results[name] = {"error": str(e)[:500]}
            log.error("publisher %s failed: %s", name, e)
    write_json(Path(args.meta).parent / "publish_result.json", results)
    if failed:
        sys.exit(1)


def cmd_channels(args):
    """List Postiz channels (id + platform) to fill POSTIZ_INTEGRATIONS."""
    from .publishers import postiz
    for c in postiz.list_integrations():
        print(f"{c['id']}\t{c.get('identifier')}\t{c.get('name')}\t{'disabled' if c.get('disabled') else 'ok'}")


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    p = argparse.ArgumentParser(prog="autovid")
    p.add_argument("--config", default=None)
    sub = p.add_subparsers(dest="cmd", required=True)
    m = sub.add_parser("make")
    m.add_argument("--topic")
    m.add_argument("--out", default=str(ROOT / "out"))
    m.add_argument("--keep-work", action="store_true")
    m.add_argument("--no-history", action="store_true")
    pb = sub.add_parser("publish")
    pb.add_argument("--meta", required=True)
    pb.add_argument("--video-url", default="")
    sub.add_parser("channels", help="list Postiz channels")
    args = p.parse_args()
    {"make": cmd_make, "publish": cmd_publish, "channels": cmd_channels}[args.cmd](args)


if __name__ == "__main__":
    main()
