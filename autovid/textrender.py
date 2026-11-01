"""Arabic-safe text rendering with Pillow (RTL shaping via libraqm, or arabic-reshaper+bidi fallback)."""
import re
from functools import lru_cache

from PIL import Image, ImageDraw, ImageFont, features

from .util import ROOT

HAS_RAQM = features.check("raqm")
FONTS = ROOT / "assets" / "fonts"


def is_rtl(text):
    return any("\u0590" <= ch <= "\u08ff" for ch in text)


@lru_cache(maxsize=32)
def font(name, size):
    f = ImageFont.truetype(str(FONTS / name), size,
                           layout_engine=ImageFont.Layout.RAQM if HAS_RAQM else ImageFont.Layout.BASIC)
    try:
        f.set_variation_by_name("Bold")
    except Exception:
        pass
    return f


_EMOJI = re.compile("[\U0001F000-\U0001FAFF\u2600-\u27BF\uFE0F\u200d]+")


def clean(text):
    """Remove emoji (caption fonts have no emoji glyphs)."""
    return re.sub(r"\s{2,}", " ", _EMOJI.sub("", text)).strip()


def _visual(text):
    """Return (text_to_draw, kwargs) so Arabic is shaped and ordered right."""
    if not is_rtl(text):
        return text, {}
    if HAS_RAQM:
        return text, {"direction": "rtl", "language": "ar"}
    import arabic_reshaper
    from bidi.algorithm import get_display
    return get_display(arabic_reshaper.reshape(text)), {}


def text_width(text, f):
    t, kw = _visual(text)
    return f.getlength(t, **kw)


def wrap(text, f, max_w):
    words, lines, cur = text.split(), [], ""
    for w in words:
        test = (cur + " " + w).strip()
        if text_width(test, f) <= max_w or not cur:
            cur = test
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def draw_block(img, text, f, center_y, max_w, fill=(255, 255, 255), stroke=(0, 0, 0), stroke_w=6,
               box=None, line_gap=1.25):
    """Draw centered multi-line text; optional rounded background box (RGBA)."""
    d = ImageDraw.Draw(img)
    text = clean(text)
    lines = wrap(text, f, max_w)
    lh = int(f.size * line_gap * 1.25)
    total_h = lh * len(lines)
    y = int(center_y - total_h / 2)
    if box:
        widest = max(text_width(l, f) for l in lines)
        pad = 34
        W = img.width
        d.rounded_rectangle([W / 2 - widest / 2 - pad, y - pad / 1.5, W / 2 + widest / 2 + pad, y + total_h + pad / 1.5],
                            radius=36, fill=box)
    for line in lines:
        t, kw = _visual(line)
        w = f.getlength(t, **kw)
        d.text(((img.width - w) / 2, y), t, font=f, fill=fill, stroke_width=stroke_w, stroke_fill=stroke, **kw)
        y += lh
    return lines


def caption_png(text, out, font_name, W=1080, H=1920, y_ratio=0.70):
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw_block(img, text, font(font_name, 70), int(H * y_ratio), W - 160, box=(0, 0, 0, 150), stroke_w=4)
    img.save(out)
    return out
