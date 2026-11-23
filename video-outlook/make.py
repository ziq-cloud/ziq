import math, os, random, subprocess, sys, wave
from functools import lru_cache
from multiprocessing import Pool

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
W, H, FPS = 1080, 1920, 30
GOLD = (245, 197, 66)
GOLD2 = (255, 225, 120)
RED = (255, 59, 78)
GREEN = (25, 211, 138)
AMBER = (255, 170, 40)
TEAL = (38, 166, 154)
WHITE = (242, 243, 248)
GREY = (150, 156, 172)
FONTDIR = "/usr/share/fonts/opentype/inter/"


@lru_cache(None)
def font(w, s):
    return ImageFont.truetype(FONTDIR + f"Inter-{w}.otf", s)


def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def eo(x):  # ease out cubic
    x = clamp(x)
    return 1 - (1 - x) ** 3


def eob(x):  # ease out back
    x = clamp(x)
    c1 = 1.70158
    c3 = c1 + 1
    return 1 + c3 * (x - 1) ** 3 + c1 * (x - 1) ** 2


def ap(t, s, d=0.5):
    return eo((t - s) / d)


# ---------------------------------------------------------------- sprites
@lru_cache(4096)
def sprite(text, w, s, color, glow=0, gcol=None):
    f = font(w, s)
    l, tp, r, b = f.getbbox(text)
    pad = glow * 3 + 4
    sw, sh = r - l + 2 * pad, b - tp + 2 * pad
    im = Image.new("RGBA", (sw, sh), (0, 0, 0, 0))
    if glow:
        g = Image.new("RGBA", (sw, sh), (0, 0, 0, 0))
        ImageDraw.Draw(g).text((pad - l, pad - tp), text, font=f, fill=(gcol or color) + (255,))
        g = g.filter(ImageFilter.GaussianBlur(glow))
        im = Image.alpha_composite(im, g)
        im = Image.alpha_composite(im, g)
    ImageDraw.Draw(im).text((pad - l, pad - tp), text, font=f, fill=color + (255,))
    return im, pad


def comp(base, im, x, y, alpha=1.0):
    if alpha <= 0.003:
        return
    x, y = int(round(x)), int(round(y))
    if alpha < 0.997:
        im = im.copy()
        a = im.getchannel("A").point(lambda v: int(v * alpha))
        im.putalpha(a)
    sx0, sy0 = max(0, -x), max(0, -y)
    sx1, sy1 = min(im.width, W - x), min(im.height, H - y)
    if sx1 <= sx0 or sy1 <= sy0:
        return
    if (sx0, sy0, sx1, sy1) != (0, 0, im.width, im.height):
        im = im.crop((sx0, sy0, sx1, sy1))
    base.paste(im, (x + sx0, y + sy0), im)


def text(base, s, x, y, w="Bold", size=40, color=WHITE, anchor="l", alpha=1.0, glow=0, gcol=None, scale=1.0):
    im, pad = sprite(s, w, size, color, glow, gcol)
    vw, vh = im.width - 2 * pad, im.height - 2 * pad
    cy = y + vh / 2
    if abs(scale - 1.0) > 1e-3 and scale > 0.01:
        im = im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))), Image.BILINEAR)
        pad = pad * scale
    sw = im.width - 2 * pad
    if anchor == "l":
        px = x - pad
    elif anchor == "c":
        px = x - im.width / 2
    else:
        px = x - sw - pad
    py = cy - im.height / 2
    comp(base, im, px, py, alpha)
    return vw


def text_w(s, w, size):
    l, t, r, b = font(w, size).getbbox(s)
    return r - l


def wrap(s, w, size, maxw):
    words, lines, cur = s.split(), [], ""
    for wd in words:
        trial = (cur + " " + wd).strip()
        if text_w(trial, w, size) <= maxw or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = wd
    if cur:
        lines.append(cur)
    return lines


def para(base, s, x, y, maxw, w="SemiBold", size=40, color=WHITE, lh=1.32, alpha=1.0, anchor="l"):
    lines = wrap(s, w, size, maxw)
    for i, ln in enumerate(lines):
        text(base, ln, x, y + i * size * lh, w, size, color, anchor, alpha)
    return len(lines) * size * lh


def rgba(c, a):
    return tuple(c[:3]) + (int(255 * clamp(a)),)


# ---------------------------------------------------------------- assets
CHART_DIR = os.path.join(HERE, "charts")
USE_LIVE = os.environ.get("ZIQ_CHARTS", "live") == "live" and os.path.exists(os.path.join(CHART_DIR, "map.json"))


def load_chart(name):
    if USE_LIVE:
        return Image.open(os.path.join(CHART_DIR, name + ".png")).convert("RGB")
    im = Image.open(os.path.join(HERE, name + ".png")).convert("RGB").resize((2000, 921), Image.LANCZOS)
    return im.crop((130, 0, 1875, 892))  # plot + price axis


CH = {k: load_chart(k) for k in ("m5", "m15", "m30", "h1", "h4")}
# M5 price mapping in crop coords (axis: 3813.70 @ y49, 3506.35 @ y803)
if USE_LIVE:
    import json as _json
    _MAP = _json.load(open(os.path.join(CHART_DIR, "map.json")))
    M5_Y = lambda p: _MAP["m5"]["a"] - _MAP["m5"]["b"] * p
else:
    M5_Y = lambda p: 49 + (3813.70 - p) / ((3813.70 - 3506.35) / 754)


def rounded_mask(w, h, r):
    m = Image.new("L", (w, h), 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, w - 1, h - 1), r, fill=255)
    return m


@lru_cache(64)
def chart_panel(key, w):
    c = CH[key]
    h = int(c.height * w / c.width)
    im = c.resize((w, h), Image.LANCZOS).convert("RGBA")
    im.putalpha(rounded_mask(w, h, 22))
    return im


def panel_frame(base, x, y, w, h, col=GOLD, alpha=1.0, width=3):
    d = ImageDraw.Draw(base, "RGBA")
    d.rounded_rectangle((x, y, x + w, y + h), 22, outline=rgba(col, 0.85 * alpha), width=width)


# ---------------------------------------------------------------- background
def make_bg():
    y = np.linspace(0, 1, H)[:, None]
    x = np.linspace(0, 1, W)[None, :]
    r = np.sqrt((x - 0.5) ** 2 * 1.4 + (y - 0.32) ** 2)
    glow = np.clip(1 - r * 1.6, 0, 1) ** 2
    base = np.zeros((H, W, 3))
    base[..., 0] = 7 + 38 * glow
    base[..., 1] = 8 + 28 * glow
    base[..., 2] = 14 + 10 * glow
    vign = np.clip(1 - (np.sqrt((x - 0.5) ** 2 + (y - 0.5) ** 2) - 0.35) * 1.2, 0.45, 1)
    base *= vign[..., None]
    return Image.fromarray(base.astype(np.uint8)).convert("RGB")


BG = make_bg()
rng = random.Random(7)
PARTS = [(rng.uniform(0, W), rng.uniform(0, H), rng.uniform(15, 70), rng.uniform(1.5, 4.5), rng.uniform(0, 6.28)) for _ in range(70)]


def background(T, tint=None):
    im = BG.copy()
    d = ImageDraw.Draw(im, "RGBA")
    off = (T * 40) % 90
    for gx in range(0, W + 90, 90):
        d.line((gx, 0, gx, H), fill=(255, 255, 255, 9))
    for i in range(-1, H // 90 + 2):
        gy = i * 90 + off
        d.line((0, gy, W, gy), fill=(255, 255, 255, 9))
    for (px, py, sp, sz, ph) in PARTS:
        yy = (py - sp * T) % H
        xx = px + 14 * math.sin(T * 0.7 + ph)
        a = 0.25 + 0.35 * (0.5 + 0.5 * math.sin(T * 2 + ph))
        d.ellipse((xx - sz, yy - sz, xx + sz, yy + sz), fill=rgba(GOLD, a))
    return im


# synthetic descending candles for intro
def make_candles():
    r = random.Random(3)
    p, out = 4700.0, []
    n = 46
    for i in range(n):
        drift = -26 if i > 10 else 6
        o = p
        c = o + drift + r.uniform(-45, 40)
        hi = max(o, c) + r.uniform(5, 35)
        lo = min(o, c) - r.uniform(5, 35)
        out.append((o, hi, lo, c))
        p = c
    return out


CANDLES = make_candles()


def draw_candles(base, t, alpha):
    d = ImageDraw.Draw(base, "RGBA")
    pmax = max(c[1] for c in CANDLES)
    pmin = min(c[2] for c in CANDLES)
    y0, y1 = 300, 1650
    Y = lambda p: y0 + (pmax - p) / (pmax - pmin) * (y1 - y0)
    n = len(CANDLES)
    cw = W / n
    shown = int(n * clamp(t / 2.2))
    for i in range(shown):
        o, hi, lo, c = CANDLES[i]
        col = GREEN if c >= o else RED
        cx = i * cw + cw / 2
        d.line((cx, Y(hi), cx, Y(lo)), fill=rgba(col, 0.28 * alpha), width=3)
        d.rectangle((cx - cw * 0.32, Y(max(o, c)), cx + cw * 0.32, Y(min(o, c)) + 1), fill=rgba(col, 0.28 * alpha))


# ---------------------------------------------------------------- icons
def tri(d, cx, cy, s, col, down=True, a=1.0):
    if down:
        pts = [(cx - s, cy - s * 0.7), (cx + s, cy - s * 0.7), (cx, cy + s * 0.8)]
    else:
        pts = [(cx - s, cy + s * 0.7), (cx + s, cy + s * 0.7), (cx, cy - s * 0.8)]
    d.polygon(pts, fill=rgba(col, a))


def warn_icon(base, cx, cy, s, a=1.0):
    d = ImageDraw.Draw(base, "RGBA")
    d.polygon([(cx, cy - s), (cx + s * 1.1, cy + s * 0.85), (cx - s * 1.1, cy + s * 0.85)], fill=rgba(AMBER, a))
    text(base, "!", cx, cy - s * 0.45, "Black", int(s * 1.05), (20, 14, 0), "c", a)


def check_box(base, x, y, s, prog, col=GREEN, a=1.0):
    d = ImageDraw.Draw(base, "RGBA")
    d.rounded_rectangle((x, y, x + s, y + s), 10, outline=rgba(col, a), width=4, fill=rgba(col, 0.18 * a * prog))
    if prog > 0:
        p1, p2, p3 = (x + s * 0.22, y + s * 0.52), (x + s * 0.43, y + s * 0.74), (x + s * 0.8, y + s * 0.28)
        k = clamp(prog * 2)
        mid = (p1[0] + (p2[0] - p1[0]) * k, p1[1] + (p2[1] - p1[1]) * k)
        d.line([p1, mid], fill=rgba(col, a), width=7)
        if prog > 0.5:
            k2 = clamp((prog - 0.5) * 2)
            end = (p2[0] + (p3[0] - p2[0]) * k2, p2[1] + (p3[1] - p2[1]) * k2)
            d.line([p2, end], fill=rgba(col, a), width=7)


def pill(base, x, y, label, col, size=34, a=1.0, txtcol=(10, 10, 14), anchor="l", padx=26, pady=14, w="ExtraBold"):
    tw = text_w(label, w, size)
    bw, bh = tw + 2 * padx, size + 2 * pady
    if anchor == "c":
        x -= bw / 2
    d = ImageDraw.Draw(base, "RGBA")
    d.rounded_rectangle((x, y, x + bw, y + bh), bh // 2, fill=rgba(col, a))
    text(base, label, x + padx, y + pady + size * 0.03, w, size, txtcol, "l", a)
    return bw, bh


def flash(base, t, start=0.0, dur=0.22, col=(255, 240, 200), peak=0.55):
    k = (t - start) / dur
    if 0 <= k <= 1:
        base.paste(col, (0, 0, W, H), Image.new("L", (W, H), int(255 * peak * (1 - k))))


# ---------------------------------------------------------------- chrome
TOTAL = None  # set later


CHROME_RIGHT = "XAUUSD  •  23.11.2026"


def chrome(base, T, alpha=1.0):
    d = ImageDraw.Draw(base, "RGBA")
    d.rectangle((0, 0, W, 104), fill=(5, 6, 10, int(200 * alpha)))
    d.line((0, 104, W, 104), fill=rgba(GOLD, 0.5 * alpha), width=2)
    text(base, "ZIQFX", 48, 34, "Black", 40, GOLD, alpha=alpha)
    text(base, CHROME_RIGHT, W - 48, 40, "SemiBold", 30, GREY, "r", alpha)
    # live dot
    pulse = 0.5 + 0.5 * math.sin(T * 5)
    d.ellipse((200, 46, 218, 64), fill=rgba(RED, alpha * (0.5 + 0.5 * pulse)))
    text(base, "OUTLOOK", 228, 44, "Bold", 24, WHITE, alpha=alpha * 0.85)
    # progress
    p = clamp(T / TOTAL)
    d.rectangle((0, H - 8, W, H), fill=(255, 255, 255, int(25 * alpha)))
    d.rectangle((0, H - 8, W * p, H), fill=rgba(GOLD, alpha))


def kicker(base, t, label, col=GOLD, y=150, a=1.0):
    k = ap(t, 0.05, 0.45)
    d = ImageDraw.Draw(base, "RGBA")
    d.rectangle((60, y + 4, 60 + 10, y + 46), fill=rgba(col, k * a))
    text(base, label, 86 - 30 * (1 - k), y + 8, "ExtraBold", 36, col, alpha=k * a)


# ---------------------------------------------------------------- scenes
def sc_intro(base, t, D):
    out = 1 - clamp((t - (D - 0.3)) / 0.3)
    draw_candles(base, t, out)
    k = clamp((t - 0.15) / 0.55)
    s = 1.0 + 0.7 * (1 - eob(k))
    text(base, "ZIQFX", W / 2, 640 - 0, "Black", 230, GOLD, "c", k * out, glow=22, gcol=(255, 170, 0), scale=s)
    d = ImageDraw.Draw(base, "RGBA")
    lw = 760 * ap(t, 0.8, 0.6)
    d.rectangle((W / 2 - lw / 2, 880, W / 2 + lw / 2, 886), fill=rgba(GOLD, out))
    a2 = ap(t, 1.0, 0.5)
    text(base, "XAUUSD", W / 2, 930 + 40 * (1 - a2), "Black", 130, WHITE, "c", a2 * out)
    a3 = ap(t, 1.35, 0.5)
    text(base, "MARKET  OUTLOOK", W / 2, 1100 + 40 * (1 - a3), "ExtraBold", 72, GOLD, "c", a3 * out, glow=10, gcol=(200, 120, 0))
    a4 = ap(t, 1.8, 0.5)
    pill(base, W / 2, 1250, "ISNIN  •  23 NOVEMBER 2026", RED, 40, a4 * out, WHITE, "c")
    a5 = ap(t, 2.3, 0.5)
    text(base, "GOLD (XAU) vs US DOLLAR", W / 2, 1380, "SemiBold", 34, GREY, "c", a5 * out)
    flash(base, t, 0.15, 0.35, peak=0.7)


def sc_greet(base, t, D):
    out = 1 - clamp((t - (D - 0.3)) / 0.3)
    a1 = ap(t, 0.1)
    text(base, "Assalamualaikum", W / 2, 640 + 40 * (1 - a1), "ExtraBold", 92, WHITE, "c", a1 * out)
    a2 = ap(t, 0.5)
    text(base, "& good morning,", W / 2, 780 + 40 * (1 - a2), "SemiBold", 70, GREY, "c", a2 * out)
    k = clamp((t - 1.0) / 0.4)
    sh = 0
    if 1.0 < t < 1.5:
        sh = math.sin(t * 90) * 14 * (1.5 - t) * 2
    text(base, "FIGHTERS!", W / 2 + sh, 990, "Black", 190, GOLD, "c", k * out, glow=24, gcol=(255, 150, 0), scale=1 + 0.6 * (1 - eob(k)))
    a4 = ap(t, 1.8)
    pill(base, W / 2, 1260, "MINGGU BAHARU  •  OUTLOOK GOLD", (40, 42, 56), 34, a4 * out, GOLD, "c")
    flash(base, t, 1.0, 0.25, col=(255, 200, 80), peak=0.45)


def sc_context(base, t, D):
    out = 1 - clamp((t - (D - 0.3)) / 0.3)
    kicker(base, t, "MARKET CONTEXT", a=out)
    a = ap(t, 0.2, 0.6)
    text(base, "TEKANAN JUALAN", 60, 220 + 30 * (1 - a), "Black", 92, RED, alpha=a * out, glow=12, gcol=(180, 0, 20))
    text(base, "MASIH KUAT", 60, 330 + 30 * (1 - a), "Black", 92, WHITE, alpha=a * out)
    # Ken Burns on H4
    c = CH["h4"]
    z = 1.0 + 0.35 * eo(t / D)
    cw, chh = c.width / z, c.height / z
    cx0 = (c.width - cw) * 0.95
    cy0 = (c.height - chh) * 0.85
    crop = c.crop((int(cx0), int(cy0), int(cx0 + cw), int(cy0 + chh))).resize((960, 491), Image.BILINEAR).convert("RGBA")
    crop.putalpha(rounded_mask(960, 491, 22))
    pa = ap(t, 0.5, 0.6)
    comp(base, crop, 60, 500 + 50 * (1 - pa), pa * out)
    panel_frame(base, 60, 500 + 50 * (1 - pa), 960, 491, RED, pa * out)
    pill(base, 84, 520 + 50 * (1 - pa), "H4", GOLD, 30, pa * out)
    b = ap(t, 1.4, 0.6)
    para(base, "Gold memulakan minggu baharu dalam keadaan tekanan jualan yang masih kuat selepas kejatuhan besar minggu lalu.",
         60, 1060 + 30 * (1 - b), 960, "SemiBold", 44, WHITE, alpha=b * out)
    c2 = ap(t, 3.2, 0.6)
    d = ImageDraw.Draw(base, "RGBA")
    d.rounded_rectangle((60, 1380, 1020, 1640), 26, fill=(255, 255, 255, int(14 * c2 * out)), outline=rgba(TEAL, c2 * out), width=3)
    text(base, "LAST PRICE", 100, 1420, "Bold", 34, GREY, alpha=c2 * out)
    val = 3700 - (3700 - 3537.26) * eo((t - 3.2) / 1.4)
    text(base, f"{val:,.2f}", 100, 1480, "Black", 110, (90, 230, 210), alpha=c2 * out, glow=10, gcol=(0, 140, 130))
    tri(d, 930, 1510, 46, RED, True, c2 * out)


def sc_mtf(base, t, D):
    out = 1 - clamp((t - (D - 0.3)) / 0.3)
    kicker(base, t, "STRUKTUR MULTI-TIMEFRAME", a=out)
    items = [("h4", "H4", "BEARISH", RED), ("h1", "H1", "BEARISH", RED),
             ("m30", "M30", "PEMULIHAN KECIL", AMBER), ("m15", "M15", "PEMULIHAN KECIL", AMBER)]
    tw = 468
    for i, (k, lbl, tag, col) in enumerate(items):
        a = ap(t, 0.3 + i * 0.35, 0.5)
        x = 60 + (i % 2) * (tw + 24)
        y = 240 + (i // 2) * 340 + 40 * (1 - a)
        im = chart_panel(k, tw)
        comp(base, im, x, y, a * out)
        panel_frame(base, x, y, tw, im.height, col, a * out)
        pill(base, x + 14, y + 14, lbl, GOLD, 26, a * out, padx=16, pady=8)
        d = ImageDraw.Draw(base, "RGBA")
        bw = text_w(tag, "ExtraBold", 26) + 30
        d.rounded_rectangle((x + tw - bw - 14, y + im.height - 60, x + tw - 14, y + im.height - 14), 12, fill=rgba(col, a * out))
        text(base, tag, x + tw - bw / 2 - 14, y + im.height - 50, "ExtraBold", 26, (12, 10, 10), "c", a * out)
    a = ap(t, 2.0, 0.6)
    d = ImageDraw.Draw(base, "RGBA")
    y0 = 960
    d.rounded_rectangle((60, y0, 1020, y0 + 250), 26, fill=(255, 59, 78, int(28 * a * out)), outline=rgba(RED, a * out), width=3)
    text(base, "H4 + H1", 100, y0 + 36, "Black", 58, RED, alpha=a * out)
    para(base, "Trend utama masih BEARISH. Tekanan jualan dominan.", 100, y0 + 120, 880, "SemiBold", 40, WHITE, alpha=a * out)
    a = ap(t, 2.8, 0.6)
    y1 = 1240
    d.rounded_rectangle((60, y1, 1020, y1 + 250), 26, fill=(255, 170, 40, int(24 * a * out)), outline=rgba(AMBER, a * out), width=3)
    text(base, "M30 + M15", 100, y1 + 36, "Black", 58, AMBER, alpha=a * out)
    para(base, "Harga cuba buat pemulihan kecil berhampiran 3537.", 100, y1 + 120, 880, "SemiBold", 40, WHITE, alpha=a * out)
    a = ap(t, 4.0, 0.6)
    para(base, "Kenaikan ini masih BELUM CUKUP untuk sahkan reversal. Fokus pada reaksi harga di support & resistance dulu.",
         W / 2, 1540, 920, "Bold", 38, GOLD2, alpha=a * out, anchor="c")


def sc_bias(base, t, D):
    out = 1 - clamp((t - (D - 0.3)) / 0.3)
    kicker(base, t, "MARKET BIAS", a=out)
    rows = [("BIAS UTAMA", "STRONG BEARISH", RED, "down"),
            ("INTRADAY", "BEARISH → NEUTRAL", AMBER, None),
            ("FOCUS", "SELL ON RALLY", GOLD, "target"),
            ("LAST PRICE", None, TEAL, None)]
    shake = 0
    for i, (lab, val, col, ic) in enumerate(rows):
        st = 0.3 + i * 0.6
        k = clamp((t - st) / 0.4)
        if k <= 0:
            continue
        if st < t < st + 0.3:
            shake = math.sin(t * 100) * 8 * (st + 0.3 - t) / 0.3
        x = 60 + (1 - eob(k)) * (-1100 if i % 2 == 0 else 1100)
        y = 260 + i * 370
        d = ImageDraw.Draw(base, "RGBA")
        d.rounded_rectangle((x, y, x + 960, y + 320), 30, fill=(14, 15, 22, int(235 * out)), outline=rgba(col, out), width=4)
        d.rectangle((x, y + 30, x + 12, y + 290), fill=rgba(col, out))
        text(base, lab, x + 60, y + 48, "Bold", 38, GREY, alpha=out)
        if val:
            size = 96 if len(val) < 15 else 80
            text(base, val, x + 60 + shake, y + 140, "Black", size, col, alpha=out, glow=12, gcol=tuple(int(c * 0.6) for c in col))
        else:
            v = 3400 + 137.26 * eo((t - st) / 1.2)
            text(base, f"{v:,.2f}", x + 60, y + 130, "Black", 120, (90, 230, 210), alpha=out, glow=12, gcol=(0, 140, 130))
        if ic == "down":
            tri(d, x + 880, y + 80, 34, RED, True, out)
    flash(base, t, 0.3, 0.2, peak=0.35, col=(255, 80, 90))


def zone_bullets(base, t, start, bullets, col, y, step=0.75, size=44):
    d = ImageDraw.Draw(base, "RGBA")
    for i, b in enumerate(bullets):
        a = ap(t, start + i * step, 0.45)
        xo = 40 * (1 - a)
        d.ellipse((70 + xo, y + 2, 118 + xo, y + 50), fill=rgba(col, a))
        text(base, str(i + 1), 94 + xo, y + 12, "Black", 28, (10, 10, 14), "c", a)
        h = para(base, b, 144 + xo, y + 2, 870, "SemiBold", size, WHITE, 1.25, a)
        y += max(h, 56) + 22
    return y


def targets(base, t, start, tg, col, y, a_out=1.0, label="TARGET"):
    a = ap(t, start, 0.5)
    d = ImageDraw.Draw(base, "RGBA")
    text(base, label, 70, y, "ExtraBold", 32, col, alpha=a * a_out)
    y += 54
    cw, gap = 250, 70
    x = 70
    for i, v in enumerate(tg):
        k = ap(t, start + 0.15 + i * 0.25, 0.4)
        aa = k * a_out
        d.rounded_rectangle((x, y, x + cw, y + 104), 22, fill=rgba(col, 0.16 * aa), outline=rgba(col, aa), width=4)
        text(base, f"TP{i + 1}", x + 22, y + 14, "Bold", 22, GREY, alpha=aa)
        text(base, str(v), x + cw / 2 + 14, y + 36, "Black", 56, WHITE, "c", aa)
        if i < len(tg) - 1:
            ka = ap(t, start + 0.3 + i * 0.25, 0.3) * a_out
            text(base, "→", x + cw + gap / 2, y + 30, "Black", 50, col, "c", ka)
        x += cw + gap
    return y + 104


def chart_zone(base, t, lo, hi, col, label, y0=420, extra=None):
    out = 1.0
    w = 960
    im = chart_panel("m5", w)
    sc = w / CH["m5"].width
    a = ap(t, 0.2, 0.5)
    comp(base, im, 60, y0 + 30 * (1 - a), a)
    yy = y0 + 30 * (1 - a)
    d = ImageDraw.Draw(base, "RGBA")
    k = ap(t, 0.7, 0.7)
    plotw = (1745 - 130) * sc
    ya, yb = yy + M5_Y(hi) * sc, yy + M5_Y(lo) * sc
    if yb - ya < 10:
        ya, yb = ya - 5, yb + 5
    xr = 60 + plotw
    xl = xr - plotw * k
    pulse = 0.5 + 0.5 * math.sin(t * 6)
    d.rectangle((xl, ya, xr, yb), fill=rgba(col, (0.25 + 0.15 * pulse) * k), outline=rgba(col, k), width=3)
    if k > 0.3:
        text(base, label, xl + 20, ya - 44 if ya - 44 > yy + 90 else yb + 8, "ExtraBold", 30, col, alpha=k)
    if extra:
        for (p, c2, lb) in extra:
            ky = yy + M5_Y(p) * sc
            for xx in range(60, int(xr), 26):
                d.line((xx, ky, xx + 14, ky), fill=rgba(c2, k), width=3)
            text(base, lb, 84, ky + 6, "Bold", 24, c2, alpha=k)
    panel_frame(base, 60, yy, w, im.height, col, a)
    pill(base, 84, yy + 18, "M5", GOLD, 26, a, padx=16, pady=8)
    return yy + im.height


def make_zone_scene(num, kind, rng_, lo, hi, col, sec, down, bullets, tg, warn=None, sec2=None):
    def sc(base, t, D):
        out = 1 - clamp((t - (D - 0.3)) / 0.3)
        a = ap(t, 0.0, 0.4)
        pill(base, 60, 140, f"ZONE {num}", col, 36, a, (10, 10, 14) if col != RED else WHITE)
        text(base, kind, 290, 150, "ExtraBold", 40, col, alpha=a)
        k = clamp(t / 0.5)
        text(base, rng_, 60, 225, "Black", 128, WHITE, alpha=k, glow=14, gcol=tuple(int(c * 0.7) for c in col), scale=1 + 0.3 * (1 - eob(k)))
        bottom = chart_zone(base, t, lo, hi, col, rng_, 400)
        y = bottom + 40
        sa = ap(t, 1.2, 0.4)
        d = ImageDraw.Draw(base, "RGBA")
        tri(d, 96, y + 26, 22, col, down, sa)
        text(base, sec, 136, y + 4, "Black", 46, col, alpha=sa)
        y = zone_bullets(base, t, 1.6, bullets, col, y + 84)
        tstart = 1.6 + len(bullets) * 0.75 + 0.3
        y = targets(base, t, tstart, tg, col, y + 10)
        if warn:
            wa = ap(t, tstart + 1.4, 0.5)
            yy = y + 30
            lines = wrap(warn, "SemiBold", 32, 800)
            hh = len(lines) * 42 + 40
            d.rounded_rectangle((60, yy, 1020, yy + hh), 22, fill=(255, 170, 40, int(30 * wa)), outline=rgba(AMBER, wa), width=3)
            warn_icon(base, 112, yy + hh / 2, 30, wa)
            para(base, warn, 170, yy + 20, 800, "SemiBold", 32, WHITE, 1.3, wa)
        if out < 1:
            base.paste((7, 8, 14), (0, 0, W, H), Image.new("L", (W, H), int(255 * (1 - out))))
        flash(base, t, 0.0, 0.2, col=col, peak=0.35)
    return sc


def sc_main(base, t, D):
    out = 1 - clamp((t - (D - 0.3)) / 0.3)
    kicker(base, t, "MAIN MARKET SCENARIO", a=out)
    a = ap(t, 0.3)
    text(base, "Selagi harga di bawah", W / 2, 300 + 30 * (1 - a), "Bold", 54, GREY, "c", a * out)
    k = clamp((t - 0.7) / 0.45)
    text(base, "3570–3590", W / 2, 400, "Black", 150, WHITE, "c", k * out, glow=16, gcol=(180, 0, 30), scale=1 + 0.4 * (1 - eob(k)))
    a = ap(t, 1.3)
    text(base, "keutamaan masih kepada", W / 2, 620 + 30 * (1 - a), "Bold", 54, GREY, "c", a * out)
    k = clamp((t - 1.8) / 0.45)
    sh = math.sin(t * 100) * 10 * clamp((2.2 - t) / 0.4) if 1.8 < t < 2.2 else 0
    text(base, "SELL ON RALLY", W / 2 + sh, 730, "Black", 128, RED, "c", k * out, glow=22, gcol=(220, 0, 30), scale=1 + 0.5 * (1 - eob(k)))
    flash(base, t, 1.8, 0.25, col=(255, 60, 80), peak=0.4)
    a = ap(t, 2.8, 0.6)
    d = ImageDraw.Draw(base, "RGBA")
    d.rounded_rectangle((60, 1000, 1020, 1560), 28, fill=(255, 255, 255, int(12 * a * out)), outline=rgba(GOLD, 0.6 * a * out), width=3)
    para(base, "Struktur H4 dan H1 menunjukkan tekanan bearish yang dominan.", 110, 1050, 860, "Bold", 44, WHITE, 1.3, a * out)
    a2 = ap(t, 3.8, 0.6)
    para(base, "Kenaikan kecil pada timeframe rendah = PULLBACK, selagi belum berlaku perubahan struktur yang jelas.",
         110, 1250, 860, "SemiBold", 42, GOLD2, 1.3, a2 * out)


def sc_two(base, t, D):
    out = 1 - clamp((t - (D - 0.3)) / 0.3)
    kicker(base, t, "DUA SENARIO UTAMA", a=out)
    cards = [(1, "SELL ON RALLY", RED, True, ["Retrace ke 3545–3560 / 3570–3590", "Bearish rejection", "Break swing low"]),
             (2, "BUY REBOUND", GREEN, False, ["Bertahan di 3516–3506", "Liquidity sweep", "Bullish structure shift", "Break swing high + retest berjaya"])]
    y = 240
    for ci, (n, title, col, down, steps) in enumerate(cards):
        st = 0.3 + ci * 3.0
        a = ap(t, st, 0.5)
        hgt = 160 + len(steps) * 96
        d = ImageDraw.Draw(base, "RGBA")
        x = 60 + (1 - a) * (-200 if ci == 0 else 200)
        d.rounded_rectangle((x, y, x + 960, y + hgt), 30, fill=(14, 15, 22, int(235 * a * out)), outline=rgba(col, a * out), width=4)
        d.ellipse((x + 40, y + 36, x + 120, y + 116), fill=rgba(col, a * out))
        text(base, str(n), x + 80, y + 50, "Black", 52, (10, 10, 14) if col == GREEN else WHITE, "c", a * out)
        text(base, title, x + 150, y + 44, "Black", 66, col, alpha=a * out)
        tri(d, x + 900, y + 76, 26, col, down, a * out)
        sy = y + 160
        for i, s in enumerate(steps):
            k = ap(t, st + 0.6 + i * 0.5, 0.4) * out
            if i > 0:
                d.line((x + 80, sy - 60, x + 80, sy - 6), fill=rgba(col, k), width=4)
            d.ellipse((x + 64, sy + 6, x + 96, sy + 38), outline=rgba(col, k), width=4, fill=rgba(col, 0.5 * k))
            text(base, s, x + 130 + 30 * (1 - k / max(out, 1e-3)), sy + 2, "Bold", 40, WHITE, alpha=k)
            sy += 96
        y += hgt + 50


def sc_levels(base, t, D):
    out = 1 - clamp((t - (D - 0.3)) / 0.3)
    kicker(base, t, "KEY LEVELS TO WATCH", a=out)
    top, bot = 3640, 3370
    y0, y1 = 250, 1420
    Y = lambda p: y0 + (top - p) / (top - bot) * (y1 - y0)
    d = ImageDraw.Draw(base, "RGBA")
    a = ap(t, 0.2, 0.5) * out
    d.line((200, y0, 200, y1), fill=rgba(GREY, a), width=3)
    for p in range(3375, 3641, 25):
        d.line((190, Y(p), 210, Y(p)), fill=rgba(GREY, a), width=2)
        if p % 50 == 0:
            text(base, str(p), 176, Y(p) - 14, "SemiBold", 26, GREY, "r", a)
    zones = [(3590, 3625, (170, 20, 40), "MAJOR RESISTANCE", "3590–3625"),
             (3570, 3590, RED, "RESISTANCE 2", "3570–3590"),
             (3545, 3560, (255, 110, 120), "RESISTANCE 1", "3545–3560"),
             (3506, 3516, (110, 240, 180), "SUPPORT 1", "3516–3506"),
             (3475, 3490, GREEN, "SUPPORT 2", "3490–3475"),
             (3400, 3450, (10, 140, 90), "MAJOR SUPPORT", "3450–3400")]
    for i, (lo, hi, col, lab, rg) in enumerate(zones):
        k = ap(t, 0.5 + i * 0.4, 0.5)
        xr = 230 + 790 * k
        d.rectangle((230, Y(hi), xr, Y(lo)), fill=rgba(col, 0.32 * k * out), outline=rgba(col, k * out), width=3)
        cy = (Y(hi) + Y(lo)) / 2
        text(base, lab, 260, cy - 32, "ExtraBold", 28, col, alpha=k * out)
        text(base, rg, 1000, cy - 30, "Black", 46, WHITE, "r", k * out)
    k = ap(t, 3.0, 0.5) * out
    yl = Y(3537.26)
    pulse = 0.5 + 0.5 * math.sin(t * 7)
    for xx in range(210, 1020, 24):
        d.line((xx, yl, xx + 12, yl), fill=rgba((90, 230, 210), k), width=4)
    d.rounded_rectangle((640, yl - 26, 1020, yl + 26), 12, fill=rgba(TEAL, k * (0.7 + 0.3 * pulse)))
    text(base, "NOW 3537.26", 830, yl - 16, "Black", 32, WHITE, "c", k)
    a = ap(t, 3.8, 0.6) * out
    d.rounded_rectangle((60, 1470, 1020, 1840), 26, fill=(255, 170, 40, int(26 * a)), outline=rgba(AMBER, a), width=3)
    warn_icon(base, 116, 1530, 28, a)
    text(base, "3500–3515", 170, 1508, "Black", 48, AMBER, alpha=a)
    para(base, "Support psikologi & teknikal penting. Jika ditembusi dengan momentum kuat, 3390–3445 jadi zon sokongan seterusnya untuk diperhatikan.",
         100, 1590, 880, "SemiBold", 36, WHITE, 1.3, a)


def sc_check(base, t, D):
    out = 1 - clamp((t - (D - 0.3)) / 0.3)
    kicker(base, t, "ENTRY CONFIRMATION CHECKLIST", a=out)
    tf = [("M5", "Entry trigger"), ("M15", "Confirmation struktur"), ("M30", "Intraday momentum"), ("H1/H4", "Arah trend utama")]
    y = 240
    d = ImageDraw.Draw(base, "RGBA")
    for i, (a_, b_) in enumerate(tf):
        st = 0.3 + i * 0.55
        k = ap(t, st, 0.4) * out
        d.rounded_rectangle((60, y, 1020, y + 120), 24, fill=(255, 255, 255, int(12 * k)), outline=rgba(GOLD, 0.5 * k), width=2)
        check_box(base, 90, y + 30, 60, clamp((t - st - 0.2) / 0.35), GREEN, k)
        pill(base, 180, y + 30, a_, GOLD, 34, k, padx=20, pady=12)
        text(base, b_, 180 + text_w(a_, "ExtraBold", 34) + 70, y + 38, "Bold", 44, WHITE, alpha=k)
        y += 140
    rules = ["Tunggu candle close — jangan bergantung pada wick sahaja.", "Tetapkan SL dan risk management sebelum entry."]
    for i, r in enumerate(rules):
        st = 2.8 + i * 0.8
        k = ap(t, st, 0.4) * out
        check_box(base, 90, y + 12, 60, clamp((t - st - 0.2) / 0.35), GREEN, k)
        h = para(base, r, 180, y + 14, 840, "SemiBold", 42, WHITE, 1.28, k)
        y += max(h, 80) + 30
    st = 4.8
    k = clamp((t - st) / 0.35)
    if k > 0:
        sh = math.sin(t * 110) * 12 * clamp((st + 0.4 - t) / 0.4)
        s = 1 + 0.8 * (1 - eob(k))
        yy = 1520
        box = Image.new("RGBA", (900, 230), (0, 0, 0, 0))
        bd = ImageDraw.Draw(box)
        bd.rounded_rectangle((4, 4, 895, 225), 26, outline=RED + (255,), width=8, fill=(60, 6, 14, 230))
        im1, p1 = sprite("TIADA CONFIRMATION", "Black", 62, WHITE)
        box.alpha_composite(im1, (int(450 - im1.width / 2), 30 - p1 + 4))
        im2, p2 = sprite("= NO ENTRY", "Black", 84, RED, 10, (200, 0, 20))
        box.alpha_composite(im2, (int(450 - im2.width / 2), 110 - p2))
        box = box.rotate(-3 * (1 - k * 0.6), resample=Image.BICUBIC, expand=True)
        if s != 1:
            box = box.resize((int(box.width * s), int(box.height * s)), Image.BILINEAR)
        comp(base, box, W / 2 - box.width / 2 + sh, yy + 115 - box.height / 2, k * out)
        flash(base, t, st, 0.25, col=(255, 40, 60), peak=0.4)


def sc_fund(base, t, D):
    out = 1 - clamp((t - (D - 0.3)) / 0.3)
    k = ap(t, 0.1, 0.5) * out
    pulse = 0.85 + 0.15 * math.sin(t * 6)
    warn_icon(base, W / 2, 300, int(80 * pulse), k)
    text(base, "FUNDAMENTAL WATCH", W / 2, 420, "Black", 76, AMBER, "c", k, glow=10, gcol=(180, 90, 0))
    d = ImageDraw.Draw(base, "RGBA")
    for i, s in enumerate(["Kekuatan USD", "Jangkaan kadar faedah Fed"]):
        a = ap(t, 0.8 + i * 0.4, 0.4) * out
        pill(base, W / 2, 560 + i * 110, s, (40, 42, 58), 40, a, WHITE, "c", padx=36, pady=18, w="Bold")
    a = ap(t, 1.8, 0.6) * out
    x0, y0 = 120, 820
    d.rounded_rectangle((x0, y0, x0 + 840, y0 + 600), 34, fill=(18, 19, 28, int(240 * a)), outline=rgba(RED, a), width=4)
    d.rounded_rectangle((x0, y0, x0 + 840, y0 + 120), 34, fill=rgba(RED, a))
    d.rectangle((x0, y0 + 80, x0 + 840, y0 + 120), fill=rgba(RED, a))
    text(base, "NOVEMBER 2026", x0 + 420, y0 + 38, "Black", 48, WHITE, "c", a)
    text(base, "25", x0 + 420, y0 + 160, "Black", 220, WHITE, "c", a)
    text(base, "RABU", x0 + 420, y0 + 400, "Bold", 40, GREY, "c", a)
    for i, ev in enumerate(["US GDP", "PCE"]):
        b = ap(t, 2.6 + i * 0.4, 0.4) * out
        pill(base, x0 + 270 + i * 300, y0 + 480, ev, GOLD, 44, b, anchor="c")
    b = ap(t, 3.6, 0.5) * out
    para(base, "Berpotensi mencetuskan VOLATILITI BESAR pada gold.", W / 2, 1500, 900, "Bold", 46, WHITE, 1.3, b, "c")


def sc_outro(base, t, D):
    out = 1 - clamp((t - (D - 0.5)) / 0.5)
    a = ap(t, 0.1) * out
    text(base, "Fighters,", W / 2, 260, "Bold", 60, GREY, "c", a)
    text(base, "jangan kejar candle.", W / 2, 350, "Black", 80, WHITE, "c", a)
    steps = [("1", "TUNGGU ZONE"), ("2", "TUNGGU CONFIRMATION"), ("3", "BARU RANCANG ENTRY")]
    d = ImageDraw.Draw(base, "RGBA")
    for i, (n, s) in enumerate(steps):
        k = clamp((t - 0.9 - i * 0.6) / 0.4)
        if k <= 0:
            continue
        y = 560 + i * 190
        x = 60 + (1 - eob(k)) * 300
        col = GOLD if i < 2 else GREEN
        d.rounded_rectangle((x, y, x + 960, y + 150), 28, fill=(16, 17, 26, int(235 * out)), outline=rgba(col, k * out), width=4)
        d.ellipse((x + 30, y + 30, x + 120, y + 120), fill=rgba(col, k * out))
        text(base, n, x + 75, y + 46, "Black", 56, (10, 10, 14), "c", k * out)
        text(base, s, x + 150, y + 48, "Black", 58, WHITE, alpha=k * out)
    k = clamp((t - 3.0) / 0.5)
    text(base, "ZIQFX", W / 2, 1220, "Black", 170, GOLD, "c", k * out, glow=20, gcol=(255, 160, 0), scale=1 + 0.4 * (1 - eob(k)))
    a = ap(t, 3.5) * out
    text(base, "TRADE SAFE  •  RISK FIRST", W / 2, 1440, "ExtraBold", 40, WHITE, "c", a)
    a = ap(t, 4.0) * out
    para(base, "Analisis untuk tujuan pendidikan, bukan nasihat kewangan. Sentiasa urus risiko anda.", W / 2, 1660, 860, "Medium", 30, GREY, 1.3, a, "c")
    flash(base, t, 3.0, 0.25, peak=0.35)


Z1 = make_zone_scene(1, "RESISTANCE", "3545–3560", 3545, 3560, RED, "SELL CONFIRMATION", True,
                     ["Tunggu harga retrace ke kawasan resistance.", "Cari bearish engulfing atau rejection pada M5/M15.",
                      "Tunggu bearish structure shift.", "Break swing low selepas rejection."], [3530, 3516, 3506])
Z2 = make_zone_scene(2, "RESISTANCE", "3570–3590", 3570, 3590, RED, "SELL CONFIRMATION", True,
                     ["Liquidity sweep di kawasan resistance.", "M5/M15 membentuk lower high.",
                      "Candle bearish close & break struktur sokongan kecil.", "Retest gagal reclaim resistance."], [3560, 3545, 3530],
                     warn="Jika harga break & bertahan di atas 3590, momentum bearish intraday perlu dinilai semula.")
Z3A = make_zone_scene(3, "SUPPORT", "3516–3506", 3506, 3516, GREEN, "BUY CONFIRMATION", False,
                      ["Liquidity sweep di bawah support.", "Reclaim semula kawasan 3516–3520.",
                       "M5/M15 bullish engulfing atau bullish structure shift.", "Break swing high dan retest berjaya."], [3540, 3555, 3570])
Z3B = make_zone_scene(3, "SUPPORT", "3516–3506", 3506, 3516, RED, "SELL CONTINUATION", True,
                      ["M15 close kukuh di bawah 3506.", "Harga retest 3506–3516 dari bawah.",
                       "Retest gagal reclaim.", "Bearish confirmation muncul."], [3490, 3475, 3450])
Z4 = make_zone_scene(4, "SUPPORT", "3490–3475", 3475, 3490, GREEN, "BUY CONFIRMATION", False,
                     ["Tunggu rejection atau liquidity sweep yang jelas.", "Harga reclaim semula kawasan 3490.",
                      "M5/M15 tunjuk bullish structure shift.", "Tunggu break swing high dan retest."], [3506, 3516, 3540],
                     warn="Jika harga terus jatuh dengan momentum kuat, jangan paksa BUY hanya kerana harga sudah rendah.")

SCENES = [("intro", sc_intro, 5.5, False), ("greet", sc_greet, 4.5, True), ("context", sc_context, 8.5, True),
          ("mtf", sc_mtf, 9.0, True), ("bias", sc_bias, 8.0, True), ("z1", Z1, 10.5, True), ("z2", Z2, 12.0, True),
          ("z3a", Z3A, 10.5, True), ("z3b", Z3B, 10.5, True), ("z4", Z4, 12.0, True), ("main", sc_main, 9.0, True),
          ("two", sc_two, 10.0, True), ("levels", sc_levels, 10.5, True), ("check", sc_check, 9.5, True),
          ("fund", sc_fund, 8.5, True), ("outro", sc_outro, 7.5, False)]
TOTAL = sum(s[2] for s in SCENES)
STARTS = []
acc = 0
for s in SCENES:
    STARTS.append(acc)
    acc += s[2]


def render_frame(i, fi):
    name, fn, D, ch = SCENES[i]
    t = fi / FPS
    T = STARTS[i] + t
    base = background(T)
    fn(base, t, D)
    if ch:
        chrome(base, T)
    return base.convert("RGB")


def render_scene(i):
    name, fn, D, ch = SCENES[i]
    n = int(round(D * FPS))
    path = os.path.join(HERE, "seg", f"{i:02d}_{name}.mp4")
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                          "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "18",
                          "-pix_fmt", "yuv420p", path], stdin=subprocess.PIPE)
    for fi in range(n):
        p.stdin.write(render_frame(i, fi).tobytes())
    p.stdin.close()
    p.wait()
    return path


# ---------------------------------------------------------------- audio
SR = 44100


def lowpass(x, cutoff):
    # FFT brickwall-ish lowpass with soft rolloff
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    X *= 1 / (1 + (f / cutoff) ** 4)
    return np.fft.irfft(X, len(x))


def highpass(x, cutoff):
    return x - lowpass(x, cutoff)


def make_audio(path):
    n = int(TOTAL * SR) + SR
    L = np.zeros(n)
    R = np.zeros(n)
    bpm = 128
    beat = 60 / bpm
    drop = STARTS[1]
    end_drums = STARTS[-1] + 4.0
    rs = np.random.RandomState(1)

    def add(sig, t0, gain=1.0, pan=0.0):
        s = int(t0 * SR)
        if s >= n:
            return
        e = min(n, s + len(sig))
        L[s:e] += sig[: e - s] * gain * (1 - max(0, pan))
        R[s:e] += sig[: e - s] * gain * (1 + min(0, pan))

    tk = np.arange(int(0.45 * SR)) / SR
    freq = 45 + 110 * np.exp(-tk * 30)
    kick = np.sin(2 * np.pi * np.cumsum(freq) / SR) * np.exp(-tk * 7)
    kick += 0.3 * np.sin(2 * np.pi * np.cumsum(freq * 2) / SR) * np.exp(-tk * 40)
    kick = np.tanh(kick * 1.8)
    ts = np.arange(int(0.25 * SR)) / SR
    snare = highpass(rs.randn(len(ts)), 1200) * np.exp(-ts * 18) * 0.6 + np.sin(2 * np.pi * 190 * ts) * np.exp(-ts * 25) * 0.5
    th = np.arange(int(0.06 * SR)) / SR
    hat = highpass(rs.randn(len(th)), 7000) * np.exp(-th * 70)

    # chord progression (A minor): Am F C G ; bar = 4 beats
    prog = [(45, [57, 60, 64]), (41, [53, 57, 60]), (48, [55, 60, 64]), (43, [55, 59, 62])]
    mf = lambda m: 440 * 2 ** ((m - 69) / 12)

    t = 0.0
    bar = 0
    while t < TOTAL:
        root, chord = prog[bar % 4]
        # pad for full bar
        dur = beat * 4
        tp = np.arange(int(dur * SR)) / SR
        env = np.minimum(1, tp / 0.3) * np.minimum(1, (dur - tp) / 0.3)
        pad = np.zeros(len(tp))
        for m in chord:
            for det in (-0.12, 0.12):
                fr = mf(m) * (1 + det / 100)
                for h, ga in ((1, 1), (2, 0.35), (3, 0.18)):
                    pad += ga * np.sin(2 * np.pi * fr * h * tp + rs.rand() * 6)
        pad = pad * env * 0.05
        add(pad, t, 1.0, -0.2)
        add(pad, t + 0.012, 1.0, 0.2)
        drums = drop <= t < end_drums
        for b in range(4):
            tb = t + b * beat
            if drums:
                add(kick, tb, 0.9)
                if b in (1, 3):
                    add(snare, tb, 0.55)
                for s16 in range(4):
                    add(hat, tb + s16 * beat / 4, 0.22 if s16 % 2 else 0.12, 0.3)
                # bass 8ths w/ sidechain feel
                for e8 in range(2):
                    tb8 = tb + e8 * beat / 2
                    tt = np.arange(int(beat / 2 * SR)) / SR
                    fr = mf(root - 12 + (12 if (b == 3 and e8 == 1) else 0))
                    bs = np.tanh(2.5 * np.sin(2 * np.pi * fr * tt)) * np.minimum(1, tt / 0.04) * np.exp(-tt * 3)
                    add(bs, tb8, 0.28)
            else:
                # sparse sub pulses before drop
                tt = np.arange(int(beat * SR)) / SR
                add(np.sin(2 * np.pi * mf(root - 12) * tt) * np.exp(-tt * 2.5), tb, 0.25)
        t += dur
        bar += 1

    # riser into drop
    rl = drop
    tr = np.arange(int(rl * SR)) / SR
    riser = highpass(rs.randn(len(tr)), 2500) * (tr / rl) ** 3 * 0.35
    riser += 0.15 * np.sin(2 * np.pi * (200 * tr + 300 * tr ** 2 / rl)) * (tr / rl) ** 2
    add(riser, 0, 1.0)

    # impacts + whooshes on scene starts
    ti = np.arange(int(1.6 * SR)) / SR
    boom = np.sin(2 * np.pi * (38 + 40 * np.exp(-ti * 8)) * ti) * np.exp(-ti * 2.6)
    boom += lowpass(rs.randn(len(ti)), 400) * np.exp(-ti * 6) * 0.6
    tw = np.arange(int(0.5 * SR)) / SR
    wn = rs.randn(len(tw))
    whoosh = (highpass(wn, 1500) * 0.5 + lowpass(wn, 1500) * 0.3) * np.sin(np.pi * tw / 0.5) ** 2
    for i, st in enumerate(STARTS):
        if i > 0:
            add(whoosh, st - 0.35, 0.35)
        add(boom, st, 0.55 if i in (0, 1, 4, 10, 13) else 0.3)
    # extra hits for stamp moments
    add(boom, STARTS[13] + 4.8, 0.6)
    add(boom, STARTS[10] + 1.8, 0.5)

    # fade out end
    fo = int(3.0 * SR)
    end = int(TOTAL * SR)
    fade = np.ones(n)
    fade[end - fo:end] = np.linspace(1, 0, fo)
    fade[end:] = 0
    L *= fade
    R *= fade
    mx = max(np.abs(L).max(), np.abs(R).max())
    L, R = np.tanh(L / mx * 1.3) * 0.88, np.tanh(R / mx * 1.3) * 0.88
    data = (np.stack([L, R], 1)[:end] * 32767).astype(np.int16)
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(data.tobytes())


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "all"
    os.makedirs(os.path.join(HERE, "seg"), exist_ok=True)
    if mode == "preview":
        # still frames: scene_index:time
        for arg in sys.argv[2:]:
            i, tt = arg.split(":")
            im = render_frame(int(i), int(float(tt) * FPS))
            im.save(os.path.join(HERE, f"prev_{i}_{tt}.png"))
        sys.exit(0)
    print("total", TOTAL)
    make_audio(os.path.join(HERE, "music.wav"))
    with Pool(4) as pool:
        paths = pool.map(render_scene, range(len(SCENES)))
    with open(os.path.join(HERE, "list.txt"), "w") as f:
        for p in paths:
            f.write(f"file '{p}'\n")
    out = os.path.join(HERE, "ZIQFX_XAUUSD_Outlook_23Nov2026.mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", os.path.join(HERE, "list.txt"),
                    "-i", os.path.join(HERE, "music.wav"), "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest",
                    "-movflags", "+faststart", out], check=True)
    print(out)
