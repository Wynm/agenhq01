"""Writes the video script with Gemini (free tier). Falls back to a built-in sample when no key."""
import datetime as dt
import hashlib
import json
import os
import random
import re
import time

import requests

from .util import ROOT, log, read_json, write_json

HISTORY = ROOT / "data" / "history.json"

PROMPT = """You are the scriptwriter of a short-video channel called "{brand}" ({website}).
Write ONE original vertical short video (TikTok / Reels / YouTube Shorts) about: {topic}
Language of everything the viewer reads or hears: {language}. Style: {style}
Spoken length: {min_s}-{max_s} seconds (about {min_w}-{max_w} words in total).

Rules:
- Start with a strong hook sentence (question or surprising fact) in the first 3 seconds.
- Be accurate and genuinely useful. No fake promises, no "get rich quick", no medical/financial advice,
  no clickbait lies, no copyrighted characters. Money-making ideas must be legit (freelancing, selling skills, content...).
- 5 to 8 scenes. Each scene = 1 or 2 short spoken sentences.
- For each scene give 2-3 ENGLISH stock-footage search keywords (concrete visuals, e.g. "smartphone screen", "person typing laptop").
- End with a short call to action (follow for more tips).
- Do NOT repeat any of these already published titles/ideas: {avoid}

Return ONLY valid JSON with this exact shape:
{{
  "topic": "short topic label",
  "title": "catchy title max 70 chars, in {language}",
  "scenes": [{{"text": "spoken sentence(s)", "keywords": ["kw1", "kw2"]}}],
  "description": "2-3 sentence description in {language}",
  "hashtags": {{"youtube": ["#..."], "tiktok": ["#..."], "instagram": ["#..."], "facebook": ["#..."], "x": ["#..."]}}
}}"""

SAMPLES = [
    {
        "topic": "حيل الهاتف",
        "title": "3 حيل فالهاتف ديالك ما كنتيش عارفها 📱",
        "scenes": [
            {"text": "واش كتعرف بلي التيليفون ديالك فيه خصائص مخبية كتسهل عليك الحياة؟", "keywords": ["smartphone closeup", "phone hand"]},
            {"text": "الحيلة الأولى: ضغط مطول على زر المسافة فالكلافيي، وغادي تحرك المؤشر بسهولة.", "keywords": ["typing on phone", "keyboard smartphone"]},
            {"text": "الحيلة الثانية: فعل وضع توفير البطارية ملي توصل عشرين فالمية، باش تطول ليك ساعات زايدة.", "keywords": ["phone battery", "charging phone"]},
            {"text": "الحيلة الثالثة: صور الشاشة بثلاثة صوابع فبزاف ديال الهواتف، بلا ما تقلب على الأزرار.", "keywords": ["screenshot phone", "touch screen"]},
            {"text": "جرب هاد الحيل دابا، وتابعنا باش توصلك نصائح تقنية جديدة كل نهار.", "keywords": ["happy person phone", "technology"]},
        ],
        "description": "ثلاث حيل بسيطة كتخلي استعمالك للهاتف أسرع وأذكى. تابع AgenHQ لنصائح تقنية يومية.",
        "hashtags": {"youtube": ["#shorts", "#tech", "#حيل_الهاتف"], "tiktok": ["#tech", "#حيل", "#fyp"],
                      "instagram": ["#tech", "#نصائح_تقنية", "#reels"], "facebook": ["#تقنية"], "x": ["#تقنية"]},
    },
    {
        "topic": "أدوات ذكاء اصطناعي",
        "title": "أداة ذكاء اصطناعي مجانية غادي توفر ليك ساعات 🤖",
        "scenes": [
            {"text": "شنو هو الذكاء الاصطناعي اللي يقدر يلخص ليك فيديو طويل ف دقيقة وحدة؟", "keywords": ["artificial intelligence", "robot"]},
            {"text": "كاين أدوات مجانية كتعطيها الرابط، وكترجع ليك أهم الأفكار مكتوبة.", "keywords": ["laptop screen", "person working laptop"]},
            {"text": "استعملها فالقراية، فالخدمة، ولا باش تفهم شي موضوع جديد بسرعة.", "keywords": ["student studying", "office work"]},
            {"text": "ولكن ديما راجع المعلومات المهمة، حيت الذكاء الاصطناعي حتى هو كيغلط.", "keywords": ["thinking person", "checking notes"]},
            {"text": "بغيتي نوريك أدوات أخرى؟ تابع الصفحة وكتب لينا فالتعليقات.", "keywords": ["technology future", "smartphone social media"]},
        ],
        "description": "كيفاش تستعمل أدوات الذكاء الاصطناعي المجانية باش تلخص الفيديوهات والمقالات وتربح الوقت.",
        "hashtags": {"youtube": ["#shorts", "#ai", "#ذكاء_اصطناعي"], "tiktok": ["#ai", "#ذكاء_اصطناعي", "#fyp"],
                      "instagram": ["#ai", "#تقنية", "#reels"], "facebook": ["#ذكاء_اصطناعي"], "x": ["#AI"]},
    },
]


def _norm(s: str) -> str:
    return re.sub(r"[^\w]+", "", s.lower())


def _fingerprint(script) -> str:
    return hashlib.sha1(_norm(script["title"] + " ".join(s["text"] for s in script["scenes"][:2])).encode()).hexdigest()[:16]


def load_history():
    return read_json(HISTORY, [])


def is_duplicate(script, history) -> bool:
    fp = _fingerprint(script)
    t = _norm(script["title"])
    return any(h.get("fingerprint") == fp or _norm(h.get("title", "")) == t for h in history)


def add_to_history(script, extra=None):
    hist = load_history()
    item = {"date": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "title": script["title"],
            "topic": script.get("topic", ""), "fingerprint": _fingerprint(script)}
    item.update(extra or {})
    hist.append(item)
    write_json(HISTORY, hist)


def _validate(d):
    assert isinstance(d.get("title"), str) and d["title"].strip()
    assert isinstance(d.get("scenes"), list) and 3 <= len(d["scenes"]) <= 12
    for s in d["scenes"]:
        assert isinstance(s.get("text"), str) and s["text"].strip()
        s["keywords"] = [k for k in s.get("keywords", []) if isinstance(k, str)][:3] or ["technology"]
    d.setdefault("description", d["title"])
    d.setdefault("hashtags", {})
    d.setdefault("topic", "")
    return d


def _gemini(prompt, model, key):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    body = {"contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 1.0, "responseMimeType": "application/json"}}
    for attempt in range(4):
        r = requests.post(url, params={"key": key}, json=body, timeout=120)
        if r.status_code in (429, 500, 503):
            wait = 15 * (attempt + 1)
            log.warning("Gemini %s, retrying in %ss", r.status_code, wait)
            time.sleep(wait)
            continue
        r.raise_for_status()
        text = r.json()["candidates"][0]["content"]["parts"][0]["text"]
        text = re.sub(r"^```(json)?|```$", "", text.strip(), flags=re.M).strip()
        return json.loads(text)
    raise RuntimeError("Gemini kept failing (rate limit?)")


def generate_script(cfg, topic=None):
    history = load_history()
    topic = topic or random.choice(cfg.get("topics") or ["technology tips"])
    key = os.getenv("GEMINI_API_KEY", "").strip()
    if not key:
        log.warning("GEMINI_API_KEY not set -> using a built-in sample script (mock mode)")
        fresh = [s for s in SAMPLES if not is_duplicate(s, history)] or SAMPLES
        return _validate(json.loads(json.dumps(random.choice(fresh))))
    avoid = "; ".join(h["title"] for h in history[-60:]) or "(none yet)"
    min_s, max_s = cfg.get("min_seconds", 30), cfg.get("max_seconds", 60)
    prompt = PROMPT.format(brand=cfg.get("brand", ""), website=cfg.get("website", ""), topic=topic,
                           language=cfg.get("language", "ar"), style=cfg.get("style", ""),
                           min_s=min_s, max_s=max_s, min_w=int(min_s * 2.2), max_w=int(max_s * 2.3), avoid=avoid)
    model = cfg.get("gemini_model", "gemini-2.5-flash")
    last = None
    for _ in range(3):
        try:
            d = _validate(_gemini(prompt, model, key))
        except (AssertionError, json.JSONDecodeError, KeyError) as e:
            last = e
            log.warning("bad script from Gemini (%s), retrying", e)
            continue
        if is_duplicate(d, history):
            log.warning("duplicate idea '%s', retrying", d["title"])
            prompt += f"\nAlso avoid: {d['title']}"
            continue
        return d
    raise RuntimeError(f"Could not get a valid, non-duplicate script: {last}")


def build_captions(script, cfg):
    """Per-platform post text (caption + hashtags)."""
    desc = script.get("description", "").strip()
    site = cfg.get("website", "")
    tags = script.get("hashtags", {})
    default = next(iter(tags.values()), []) if tags else []
    out = {}
    for p in cfg.get("platforms", ["youtube", "tiktok", "instagram", "facebook", "x"]):
        ht = " ".join(tags.get(p) or default)
        if p == "x":
            text = f"{script['title']}\n{ht}".strip()[:270]
        elif p == "youtube":
            text = f"{desc}\n\n{site}\n{ht}".strip()
        else:
            text = f"{script['title']}\n\n{desc}\n\n{ht}".strip()
        out[p] = text
    return out
