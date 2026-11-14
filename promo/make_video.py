"""Generate a vertical (1080x1920) promo video for TikTok / Telegram.
Usage: python3 make_video.py  -> writes out/traxa_promo.mp4 and out/cover.jpg
"""
import math, os, random, subprocess, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 1080, 1920, 30
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out"); FR = os.path.join(OUT, "frames")
os.makedirs(FR, exist_ok=True)

CODE = "ZIQFX"
LINK = "traxatradingapp.com/?invite=ZIQFX"
FD = "/usr/share/fonts/opentype/inter/"
_fc = {}
def font(w, s):
    k = (w, s)
    if k not in _fc: _fc[k] = ImageFont.truetype(FD + f"Inter-{w}.otf", s)
    return _fc[k]

# Traxa palette: black, gold, red, blue
BLACK = (8, 7, 6)
GOLD, GOLD_HI, GOLD_LO = (226, 178, 92), (255, 226, 150), (160, 112, 44)
RED, BLUE, WHITE, MUTED = (224, 84, 88), (72, 140, 232), (255, 255, 255), (170, 160, 145)
TG = (42, 171, 238)

TRAXA = Image.open(os.path.join(HERE, "assets/traxa_icon.png")).convert("RGBA")
IFANG = Image.open(os.path.join(HERE, "assets/ifangfx_logo.png")).convert("RGBA")
IFANG = IFANG.crop(IFANG.getbbox())

def ease(t): t = max(0, min(1, t)); return 1 - (1 - t) ** 3
def back(t):  # overshoot ease
    t = max(0, min(1, t)); c = 1.9; return 1 + (c + 1) * (t - 1) ** 3 + c * (t - 1) ** 2
def seg(t, a, b): return max(0.0, min(1.0, (t - a) / (b - a)))
def win(t, a, b, fi=.5, fo=.4): return ease(seg(t, a, a + fi)) * (1 - seg(t, b - fo, b))

# ---------- static background: black with warm radial glow + vignette ----------
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
r = np.sqrt(((xx - W / 2) / W) ** 2 + ((yy - H * 0.42) / H) ** 2)
glow = np.clip(1 - r * 1.8, 0, 1) ** 2
bg = np.zeros((H, W, 3), np.float32)
for i in range(3): bg[..., i] = BLACK[i] + glow * (np.array([70, 48, 18])[i])
BASE = Image.fromarray(bg.clip(0, 255).astype(np.uint8))

# gold vertical gradient used to fill text/shapes
gy = np.linspace(0, 1, 400)[:, None]
gcol = np.concatenate([(np.array(GOLD_HI) * (1 - gy) + np.array(GOLD_LO) * gy)[..., None, :]] * 4, axis=1)
GOLD_GRAD = Image.fromarray(gcol.astype(np.uint8)).resize((2000, 400))

# ---------- candles (random walk, trending up) ----------
random.seed(11)
candles, p = [], 100.0
for _ in range(80):
    o = p; c = o + random.gauss(0.45, 2.0); hi = max(o, c) + abs(random.gauss(0, 1.1)); lo = min(o, c) - abs(random.gauss(0, 1.1))
    candles.append((o, hi, lo, c)); p = c

def chart_layer(t, strength):
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    vis = min(len(candles), int(10 + t * 3.2))
    cs = candles[max(0, vis - 24):vis]
    lo = min(x[2] for x in cs); hi = max(x[1] for x in cs)
    top, bot = 420, 1500; cw = W / 24
    def y(v): return bot - (v - lo) / (hi - lo + 1e-6) * (bot - top)
    a = int(255 * strength)
    pts = []
    for i, (o, h, l, c) in enumerate(cs):
        col = (60, 200, 140) if c >= o else RED
        x = i * cw + cw / 2
        d.line([(x, y(h)), (x, y(l))], fill=col + (a,), width=3)
        d.rectangle([x - cw * .3, min(y(o), y(c)), x + cw * .3, max(y(o), y(c)) + 2], fill=col + (a,))
        pts.append((x, y(c)))
    if len(pts) > 1: d.line(pts, fill=GOLD + (int(a * .8),), width=4)
    return lay

# ---------- particles ----------
random.seed(3)
parts = [(random.uniform(0, W), random.uniform(0, H), random.uniform(15, 60), random.uniform(1.5, 4.5), random.uniform(0, 6.28)) for _ in range(70)]
def particles(d, t):
    for x, y0, sp, sz, ph in parts:
        y = (y0 - sp * t) % H
        a = int(110 * (0.5 + 0.5 * math.sin(t * 2 + ph)))
        d.ellipse([x - sz, y - sz, x + sz, y + sz], fill=GOLD_HI + (a,))

# ---------- drawing helpers ----------
def paste_alpha(img, im, xy, a):
    if a <= 0: return
    if a < 1:
        im = im.copy(); im.putalpha(im.getchannel("A").point(lambda v: int(v * a)))
    img.alpha_composite(im, (int(xy[0]), int(xy[1])))

def text_img(s, f, fill, stroke=0, stroke_fill=(0, 0, 0)):
    bb = f.getbbox(s, stroke_width=stroke)
    im = Image.new("RGBA", (bb[2] - bb[0] + 4, bb[3] - bb[1] + 4), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    if fill == "gold":
        mask = Image.new("L", im.size, 0)
        ImageDraw.Draw(mask).text((2 - bb[0], 2 - bb[1]), s, font=f, fill=255)
        g = GOLD_GRAD.resize(im.size)
        im.paste(g, (0, 0), mask)
    else:
        d.text((2 - bb[0], 2 - bb[1]), s, font=f, fill=fill, stroke_width=stroke, stroke_fill=stroke_fill)
    return im

def ctext(img, y, s, f, fill, a=1.0, dy=0, scale=1.0, glow=None, dx=0):
    if a <= 0: return
    im = text_img(s, f, fill)
    if scale != 1.0:
        im = im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))), Image.LANCZOS)
    x = (W - im.width) / 2 + dx; yy = y + dy - (im.height - im.height / scale) / 2 if scale != 1 else y + dy
    if glow:
        g = Image.new("RGBA", (im.width + 120, im.height + 120), glow + (0,))
        m = Image.new("L", g.size, 0); m.paste(im.getchannel("A"), (60, 60))
        g.putalpha(m); g = g.filter(ImageFilter.GaussianBlur(18))
        paste_alpha(img, g, (x - 60, yy - 60), a * .8)
    paste_alpha(img, im, (x, yy), a)

def logo(img, src, cx, cy, size, a, glow=None, rot=0):
    if a <= 0 or size < 2: return
    s = size / max(src.size)
    im = src.resize((max(1, int(src.width * s)), max(1, int(src.height * s))), Image.LANCZOS)
    if rot: im = im.rotate(rot, Image.BICUBIC, expand=True)
    if glow:
        g = Image.new("RGBA", (im.width + 160, im.height + 160), (0, 0, 0, 0))
        sh = Image.new("RGBA", im.size, glow + (255,)); sh.putalpha(im.getchannel("A"))
        g.alpha_composite(sh, (80, 80)); g = g.filter(ImageFilter.GaussianBlur(40))
        paste_alpha(img, g, (cx - g.width / 2, cy - g.height / 2), a)
    paste_alpha(img, im, (cx - im.width / 2, cy - im.height / 2), a)

def shine(img, box, t, radius):
    """diagonal light sweep across a rounded box, t in 0..1"""
    if not 0 < t < 1: return
    x0, y0, x1, y1 = box; w, h = x1 - x0, y1 - y0
    band = Image.new("RGBA", (w, h), (0, 0, 0, 0)); bd = ImageDraw.Draw(band)
    cx = -200 + t * (w + 400)
    bd.polygon([(cx, 0), (cx + 90, 0), (cx - 30, h), (cx - 120, h)], fill=(255, 255, 255, 120))
    band = band.filter(ImageFilter.GaussianBlur(8))
    m = Image.new("L", (w, h), 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, w - 1, h - 1], radius, fill=255)
    band.putalpha(Image.fromarray(np.minimum(np.array(band.getchannel("A")), np.array(m))))
    img.alpha_composite(band, (x0, y0))

# ---------- voiceover (Malay neural TTS) + timeline ----------
VOICE = os.environ.get("VOICE", "ms-MY-OsmanNeural")
VDIR = os.path.join(HERE, "voice", VOICE)
LINES = [
    ("hook1", "Nak mula trading?"),
    ("hook2", "Tapi tak tahu mula dari mana?"),
    ("brand", "Cuba TRAXA Trading App. Signal trading terus di telefon anda."),
    ("p1", "Ada tiga pair utama: Gold, Bitcoin dan Oil, dengan harga live."),
    ("p2", "Setiap setup ada entry, stop loss dan take profit, siap dengan reason kenapa setup itu dihantar."),
    ("p3", "Analisis trend lengkap, dari M5 sampai D1."),
    ("p4", "Dan ada video panduan untuk yang baru mula."),
    ("cta1", "Daftar sekarang, guna kod jemputan saya."),
    ("code", "Z, I, Q, F, X."),
    ("cta2", "Link pendaftaran ada di bio dan pinned."),
    ("outro", "Join channel Telegram, i-Fang F X, untuk tips dan update trading."),
    ("risk", "Ingat, trading ada risiko. Labur dengan bijak."),
]
SCENE_START = {"brand", "p1", "p2", "p3", "p4", "cta1", "outro"}  # a new scene begins with these lines

def tts(key, text):
    os.makedirs(VDIR, exist_ok=True)
    import hashlib
    mp3 = os.path.join(VDIR, f"{key}_{hashlib.md5(text.encode()).hexdigest()[:6]}.mp3")
    if not os.path.exists(mp3):  # needs network access to speech.platform.bing.com
        cmd = ["edge-tts", "--voice", VOICE, "--rate=+8%", "--text", text, "--write-media", mp3]
        if os.environ.get("HTTPS_PROXY"): cmd[1:1] = ["--proxy", os.environ["HTTPS_PROXY"]]
        subprocess.run(cmd, check=True)
    raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", mp3, "-f", "s16le", "-ac", "1", "-ar", "44100", "-"],
                         capture_output=True, check=True).stdout
    a = np.frombuffer(raw, np.int16).astype(np.float32) / 32768
    nz = np.where(np.abs(a) > 0.01)[0]  # trim silence
    return a[max(0, nz[0] - 800):nz[-1] + 2000] if len(nz) else a

CLIPS, T = {}, {}
cur = 0.2
for key, text in LINES:
    if key in SCENE_START: cur += 0.35
    a = tts(key, text); CLIPS[key] = a; T[key] = (cur, cur + len(a) / 44100)
    cur = T[key][1] + 0.15
DUR = cur + 1.2
N = int(FPS * DUR)
S1 = 0
S2, S3, S4, S5 = (T[k][0] - 0.25 for k in ("brand", "p1", "cta1", "outro"))
SHOT_T = [T[f"p{i}"][0] - 0.25 for i in range(1, 5)] + [S4]
CUTS = [S2, S4, S5]

# ---------- app screenshots shown inside a phone mockup ----------
# boxes are in 921-px-wide screenshot coordinates: (x0, y0, x1, y1, appear-after-seconds)
SHOTS = [
    ("home", "3 PAIR UTAMA", "Gold  \u2022  Bitcoin  \u2022  Oil  \u2014  harga live", 130, 60,
     [(35, 325, 886, 690, .6)]),
    ("chart", "REASON SETIAP ENTRY", "Entry, SL & TP siap dengan sebab", 130, 0,
     [(72, 630, 848, 706, .8), (372, 1040, 700, 1625, 3.0)]),
    ("analysis", "ANALISIS MULTI-TIMEFRAME", "Trend dari M5 hingga D1", 130, 120,
     [(75, 742, 848, 1000, .6), (108, 1345, 812, 1760, 1.8)]),
    ("guides", "VIDEO PANDUAN", "Belajar guna app langkah demi langkah", 300, 30,
     [(35, 650, 886, 1760, .6)]),
]
PW, PH, BZ = 620, 1180, 16  # phone screen size and bezel
SC = PW / 921
SCREENS = {}
for name, *_ in SHOTS:
    im = Image.open(os.path.join(HERE, f"assets/screens/{name}.png")).convert("RGB")
    SCREENS[name] = im.resize((PW, int(im.height * PW / im.width)), Image.LANCZOS)
SCREEN_MASK = Image.new("L", (PW, PH), 0); ImageDraw.Draw(SCREEN_MASK).rounded_rectangle([0, 0, PW - 1, PH - 1], 58, fill=255)
PHONE = Image.new("RGBA", (PW + 2 * BZ, PH + 2 * BZ), (0, 0, 0, 0))
ImageDraw.Draw(PHONE).rounded_rectangle([0, 0, PW + 2 * BZ - 1, PH + 2 * BZ - 1], 72, fill=(20, 18, 16, 255), outline=GOLD + (200,), width=3)
PHONE_GLOW = Image.new("RGBA", (PHONE.width + 200, PHONE.height + 200), (0, 0, 0, 0))
ImageDraw.Draw(PHONE_GLOW).rounded_rectangle([100, 100, 100 + PHONE.width, 100 + PHONE.height], 72, fill=GOLD + (110,))
PHONE_GLOW = PHONE_GLOW.filter(ImageFilter.GaussianBlur(45))

def phone_shot(img, i, t):
    name, title, sub, y0, pan, boxes = SHOTS[i]
    s0, s1 = SHOT_T[i], SHOT_T[i + 1]
    pin, pout = ease(seg(t, s0, s0 + .5)), seg(t, s1 - .35, s1)
    a = pin * (1 - pout)
    dx = int(W * (1 - pin)) - int(W * ease(pout))
    # titles
    ctext(img, 250, title, font("Black", 64), "gold", a, dx=dx, glow=GOLD)
    ctext(img, 345, sub, font("Medium", 44), WHITE, ease(seg(t, s0 + .2, s0 + .6)) * (1 - pout), dx=dx)
    # phone
    px = (W - PW) // 2 + dx; py = 450
    paste_alpha(img, PHONE_GLOW, (px - BZ - 100, py - BZ - 100), a)
    paste_alpha(img, PHONE, (px - BZ, py - BZ), a)
    src = SCREENS[name]
    ys = int(y0 * SC + pan * SC * ease(seg(t, s0 + .5, s1 - .4)))
    ys = min(ys, src.height - PH)
    scr = src.crop((0, ys, PW, ys + PH)).convert("RGBA"); scr.putalpha(SCREEN_MASK.point(lambda v: int(v * a)))
    img.alpha_composite(scr, (max(-PW, min(W, px)), py)) if -PW < px < W else None
    # pulsing highlight boxes
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    for (x0, by0, x1, by1, off) in boxes:
        ha = ease(seg(t, s0 + off, s0 + off + .4)) * (1 - pout)
        if ha <= 0: continue
        pulse = 0.6 + 0.4 * math.sin((t - s0 - off) * 6)
        bx0, bx1 = px + x0 * SC - 6, px + x1 * SC + 6
        bty0, bty1 = py + by0 * SC - ys - 6, py + by1 * SC - ys + 6
        bty0, bty1 = max(py, bty0), min(py + PH, bty1)
        d.rounded_rectangle([bx0, bty0, bx1, bty1], 22, outline=GOLD_HI + (int(255 * ha * pulse),), width=6)
    g = lay.filter(ImageFilter.GaussianBlur(10)); img.alpha_composite(g); img.alpha_composite(lay)

def at(k, off=0): return T[k][0] + off

def frame(n):
    t = n / FPS
    img = BASE.copy().convert("RGBA")
    # chart, stronger during hook
    strength = 0.55 if t < S2 else 0.16
    if t >= S2 - .3 and t < S2: strength = 0.55 - 0.39 * seg(t, S2 - .3, S2)
    img.alpha_composite(chart_layer(t, strength))
    pl = Image.new("RGBA", (W, H), (0, 0, 0, 0)); particles(ImageDraw.Draw(pl), t); img.alpha_composite(pl)

    # --- Scene 1: hook ---
    if t < S2 + .1:
        out = 1 - seg(t, S2 - .3, S2)
        words = [("Nak mula", 560, "Bold", 100, WHITE, at("hook1") - .1), ("trading?", 680, "Black", 150, "gold", at("hook1", .4)),
                 ("Tapi tak tahu", 900, "Bold", 84, WHITE, at("hook2") - .1), ("mula dari mana?", 1000, "Bold", 84, WHITE, at("hook2", .45))]
        for s, y, w, sz, col, st in words:
            p = seg(t, st, st + .35)
            ctext(img, y, s, font(w, sz), col, ease(p) * out, scale=0.6 + 0.4 * back(p),
                  glow=GOLD if col == "gold" else None)
        ctext(img, 1200, "Tonton sampai habis ↓", font("Medium", 50), MUTED, ease(seg(t, T["hook2"][1] - .2, T["hook2"][1] + .2)) * out)

    # --- Scene 2: Traxa reveal ---
    if S2 <= t < S3:
        a = win(t, S2, S3, .4, .4); p = seg(t, S2, S2 + .7)
        size = 420 * back(p)
        logo(img, TRAXA, W / 2, 720, size, a, glow=GOLD)
        ctext(img, 1000, "TRAXA", font("Black", 180), "gold", win(t, S2 + .5, S3, .5, .4), glow=GOLD)
        ctext(img, 1210, "T R A D I N G   A P P", font("SemiBold", 52), WHITE, win(t, S2 + .8, S3, .5, .4))
        ctext(img, 1320, "Signal trading terus di telefon anda", font("Medium", 50), MUTED, win(t, at("brand", 1.4), S3, .5, .4))

    # --- Scene 3: app tour ---
    if S3 <= t < S4:
        for i in range(len(SHOTS)):
            if SHOT_T[i] <= t < SHOT_T[i + 1]: phone_shot(img, i, t)

    # --- Scene 4: CTA with code ---
    if S4 <= t < S5:
        out = 1 - seg(t, S5 - .4, S5)
        logo(img, TRAXA, W / 2, 400, 170 * ease(seg(t, S4, S4 + .4)), out)
        ctext(img, 540, "Daftar sekarang", font("Black", 100), WHITE, ease(seg(t, S4, S4 + .4)) * out)
        ctext(img, 670, "guna kod jemputan saya", font("Medium", 56), MUTED, ease(seg(t, S4 + .2, S4 + .6)) * out)
        p = seg(t, at("code") - .35, at("code") + .15); a2 = ease(p) * out
        if a2 > 0:
            pulse = back(p) * (1 + 0.025 * math.sin((t - S4) * 7))
            bw, bh = int(780 * pulse), int(270 * pulse); cx, cy = W // 2, 930
            box = [cx - bw // 2, cy - bh // 2, cx + bw // 2, cy + bh // 2]
            # glow
            g = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ImageDraw.Draw(g).rounded_rectangle(box, 54, fill=GOLD + (int(150 * a2),))
            img.alpha_composite(g.filter(ImageFilter.GaussianBlur(40)))
            m = Image.new("L", (bw, bh), 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, bw - 1, bh - 1], 54, fill=int(255 * a2))
            img.paste(GOLD_GRAD.resize((bw, bh)), (box[0], box[1]), m)
            ti = text_img(CODE, font("Black", int(180 * pulse)), BLACK)
            paste_alpha(img, ti, (cx - ti.width / 2, cy - ti.height / 2), a2)
            shine(img, box, ((t - at("code")) % 1.6) / 1.0, 54)
        a3 = ease(seg(t, at("cta2") - .2, at("cta2") + .3)) * out
        ctext(img, 1140, "Link pendaftaran:", font("Medium", 48), MUTED, a3)
        if a3 > 0:
            lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
            d.rounded_rectangle([70, 1210, W - 70, 1330], 30, fill=(255, 255, 255, int(16 * a3)), outline=GOLD + (int(255 * a3),), width=3)
            img.alpha_composite(lay)
        ctext(img, 1242, LINK, font("Bold", 48), GOLD_HI, a3)
        ctext(img, 1410, "Link ada di bio / pinned ↑", font("SemiBold", 52), WHITE, ease(seg(t, at("cta2", .9), at("cta2", 1.4))) * out)

    # --- Scene 5: iFANG FX outro ---
    if t >= S5:
        p = seg(t, S5, S5 + .7)
        logo(img, IFANG, W / 2, 720, 760 * back(p), ease(p), glow=GOLD)
        a = ease(seg(t, at("outro") - .1, at("outro", .4)))
        ctext(img, 1080, "Join channel Telegram", font("SemiBold", 60), WHITE, a)
        if a > 0:
            lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
            d.rounded_rectangle([130, 1180, W - 130, 1320], 70, fill=TG + (int(255 * a),))
            img.alpha_composite(lay)
        ctext(img, 1212, "t.me/iFangFx", font("Black", 72), WHITE, a)
        ctext(img, 1400, "Follow untuk tips & update trading", font("Medium", 48), MUTED, ease(seg(t, at("outro", 1.6), at("outro", 2.1))))
        ctext(img, 1480, "Kod jemputan: ZIQFX", font("Bold", 56), "gold", ease(seg(t, at("risk") - .2, at("risk", .3))))

    # --- persistent overlays ---
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
    if t < S5:  # channel watermark
        logo(img, IFANG, 140, 130, 190, 0.92)
        d.text((250, 112), "t.me/iFangFx", font=font("SemiBold", 38), fill=WHITE + (200,))
    for i, s in enumerate(["Trading melibatkan risiko. Hanya labur apa yang", "anda sanggup rugi. Bukan nasihat kewangan."]):
        f = font("Regular", 32); w = d.textlength(s, font=f)
        d.text(((W - w) / 2, 1770 + i * 44), s, font=f, fill=MUTED + (220,))
    d.rectangle([0, H - 10, int(W * t / DUR), H], fill=GOLD + (230,))
    # flash on scene cuts
    for c in CUTS:
        if c - .05 <= t < c + .25:
            fa = 1 - seg(t, c - .05, c + .25)
            d.rectangle([0, 0, W, H], fill=GOLD_HI + (int(90 * fa),))
    img.alpha_composite(ov)
    img.convert("RGB").save(os.path.join(FR, f"{n:05d}.jpg"), quality=92)

def music(path):
    sr = 44100; t = np.arange(int(sr * DUR)) / sr; bpm = 120; beat = 60 / bpm
    out = np.zeros_like(t)
    def add(i, s):
        if i < len(out): out[i:i + len(s)] += s[:len(out) - i]
    for k in np.arange(0, DUR, beat):  # kick
        L = int(.25 * sr); tt = np.arange(L) / sr
        add(int(k * sr), np.sin(2 * np.pi * (50 + 90 * np.exp(-tt * 30)) * tt) * np.exp(-tt * 12) * .8)
    rng = np.random.default_rng(1)
    for k in np.arange(beat / 2, DUR, beat):  # hats
        L = int(.05 * sr); add(int(k * sr), rng.standard_normal(L) * np.exp(-np.arange(L) / sr * 80) * .12)
    for k in np.arange(beat, DUR, beat * 2):  # clap
        L = int(.12 * sr); add(int(k * sr), rng.standard_normal(L) * np.exp(-np.arange(L) / sr * 35) * .22)
    chords = [[220, 261.6, 329.6], [174.6, 220, 261.6], [261.6, 329.6, 392], [196, 246.9, 293.7]]
    for ci, k in enumerate(np.arange(0, DUR, 2.0)):  # pad
        L = int(2 * sr); tt = np.arange(L) / sr
        env = np.minimum(1, tt * 8) * np.minimum(1, (2 - tt) * 8)
        add(int(k * sr), sum(np.sin(2 * np.pi * f * tt) + .3 * np.sin(4 * np.pi * f * tt) for f in chords[ci % 4]) * env * .07)
    for c in [S2, S3, S4, S5]:  # riser whoosh into each cut
        L = int(.6 * sr); tt = np.arange(L) / sr
        add(int((c - .6) * sr), rng.standard_normal(L) * (tt / .6) ** 2 * .25)
    fade = np.minimum(1, np.minimum(t / .3, (DUR - t) / 1.2)); out *= fade
    out = out / np.abs(out).max() * 0.22  # music bed under the voice
    vo = np.zeros_like(out)
    for k, (a0, _) in T.items():
        a = CLIPS[k]; i = int(a0 * sr); vo[i:i + len(a)] += a[:len(vo) - i]
    vo = vo / (np.abs(vo).max() + 1e-9) * 0.9
    duck = np.convolve((np.abs(vo) > 0.02).astype(np.float32), np.ones(4410) / 4410, "same")
    mix = out * (1 - 0.45 * np.clip(duck * 3, 0, 1)) + vo
    out = np.int16(np.clip(mix / max(1.0, np.abs(mix).max()), -1, 1) * 0.95 * 32767)
    with wave.open(path, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes(out.tobytes())

if __name__ == "__main__":
    import sys
    only = [int(x) for x in sys.argv[1:]]
    for n in (only or range(N)): frame(n)
    if only: sys.exit()
    wav = os.path.join(OUT, "music.wav"); music(wav)
    mp4 = os.path.join(OUT, "traxa_promo.mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", os.path.join(FR, "%05d.jpg"),
                    "-i", wav, "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "19", "-preset", "medium",
                    "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", mp4], check=True)
    Image.open(os.path.join(FR, f"{int((at('cta2', 1.6)) * FPS):05d}.jpg")).save(os.path.join(OUT, "cover.jpg"), quality=92)
    print("done", mp4)
