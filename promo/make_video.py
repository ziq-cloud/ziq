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
RATE = "+15%"
LINES = [
    ("hook1", "Masih teka-teka bila nak entry?"),
    ("hook2", "Biar signal yang datang kat kau."),
    ("brand", "Cuba TRAXA Trading App. Signal trading terus di telefon anda."),
    ("p1", "Ada tiga pair utama: Gold, Bitcoin dan Oil, dengan harga live."),
    ("p2", "Setiap setup ada entry, stop loss dan take profit, siap dengan reason kenapa setup itu dihantar."),
    ("p3", "Setup baru, keputusan, amaran berita dan get ready alert, semua terus masuk notifikasi telefon."),
    ("p4", "Support, resistance dan key level untuk setiap timeframe."),
    ("p5", "Ada juga kelas edukasi, dari market structure sampai breakout."),
    ("proof", "Baru tiga minggu dilancarkan, dah lebih lima ribu trader dari tiga puluh lapan negara, dengan lebih tiga ratus feedback."),
    ("cta1", "Daftar sekarang, guna kod jemputan saya."),
    ("code", "Z, I, Q, F, X."),
    ("cta2", "Link pendaftaran ada di bio dan pinned."),
    ("outro", "Join channel Telegram, i-Fang F X, untuk tips dan update trading."),
    ("risk", "Ingat, trading ada risiko. Labur dengan bijak."),
]
SCENE_START = {"brand", "p1", "p2", "p3", "p4", "p5", "proof", "cta1", "outro"}  # a new scene begins with these lines

def tts(key, text):
    os.makedirs(VDIR, exist_ok=True)
    import hashlib
    mp3 = os.path.join(VDIR, f"{key}_{hashlib.md5((text + RATE).encode()).hexdigest()[:6]}.mp3")
    if not os.path.exists(mp3):  # needs network access to speech.platform.bing.com
        cmd = ["edge-tts", "--voice", VOICE, f"--rate={RATE}", "--text", text, "--write-media", mp3]
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
    if key == "brand": cur += 0.7  # let the notification banners land
    a = tts(key, text); CLIPS[key] = a; T[key] = (cur, cur + len(a) / 44100)
    cur = T[key][1] + 0.15
DUR = cur + 1.2
N = int(FPS * DUR)
S1 = 0
S2, S3, S4, S5 = (T[k][0] - 0.25 for k in ("brand", "p1", "cta1", "outro"))
SP = T["proof"][0] - 0.25
SHOT_T = [T[f"p{i}"][0] - 0.25 for i in range(1, 6)] + [SP]
CUTS = [S2, SP, S4, S5]

# ---------- app screenshots shown inside a phone mockup ----------
# boxes are in 921-px-wide screenshot coordinates: (x0, y0, x1, y1, appear-after-seconds)
SHOTS = [
    ("home", "3 PAIR UTAMA", "Gold  \u2022  Bitcoin  \u2022  Oil  \u2014  harga live", 130, 60,
     [(35, 325, 886, 690, .6)]),
    ("chart", "REASON SETIAP ENTRY", "Entry, SL & TP siap dengan sebab", 130, 0,
     [(72, 630, 848, 706, .8), (372, 1040, 700, 1625, 3.0)]),
    ("notif", "NOTIFIKASI SETIAP SIGNAL", "Setup baru, keputusan, berita & get ready alert", 130, 0,
     [(58, 488, 863, 1108, .6), (58, 1197, 863, 1640, 3.4)]),
    ("levels", "SUPPORT & RESISTANCE", "Key level untuk setiap timeframe", 130, 120,
     [(72, 490, 848, 1035, .6), (75, 1130, 848, 1405, 2.4)]),
    ("edu", "KELAS EDUKASI", "Market structure hingga breakout", 130, 80,
     [(35, 690, 886, 1765, .6)]),
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

# ---------- real screen recordings ----------
def extract(src, dst, vf, dur):
    d = os.path.join(OUT, dst)
    if not os.path.isdir(d) or not os.listdir(d):
        os.makedirs(d, exist_ok=True)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", os.path.join(HERE, "assets/rec", src), "-t", str(dur),
                        "-vf", vf, "-q:v", "3", os.path.join(d, "%04d.jpg")], check=True)
    return sorted(os.path.join(d, f) for f in os.listdir(d))
REC_INTRO = extract("rec2.mov", "rec_intro", f"fps={FPS},scale={PW}:-2", 4.8)   # splash -> swipe -> globe -> home
REC_FEED = extract("rec1.mov", "rec_feed", f"fps={FPS},scale={W}:-2,crop={W}:{H}:0:200,gblur=sigma=14", 8.4)  # feedback feed, blurred

DOT = (565, 575, 46)  # iOS AssistiveTouch button position in the scaled recording
_dm = Image.new("L", (W, H), 0)
def hide_dot(im):
    cx, cy, r = DOT; a = np.array(im)
    yy_, xx_ = np.ogrid[:a.shape[0], :a.shape[1]]; d2 = (xx_ - cx) ** 2 + (yy_ - cy) ** 2
    ring = a[(d2 > (r + 4) ** 2) & (d2 < (r + 12) ** 2)]
    a[d2 <= r * r] = np.median(ring, axis=0).astype(np.uint8)
    out = Image.fromarray(a); box = (cx - r - 14, cy - r - 14, cx + r + 14, cy + r + 14)
    out.paste(out.crop(box).filter(ImageFilter.GaussianBlur(6)), box[:2]); return out

def phone_frame(img, scr, px, py, a, ys=0):
    paste_alpha(img, PHONE_GLOW, (px - BZ - 100, py - BZ - 100), a)
    paste_alpha(img, PHONE, (px - BZ, py - BZ), a)
    if -PW < px < W:
        sc = scr.crop((0, ys, PW, ys + PH)).convert("RGBA"); sc.putalpha(SCREEN_MASK.point(lambda v: int(v * a)))
        img.alpha_composite(sc, (px, py))

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
        pulse = 0.75 + 0.25 * math.sin((t - s0 - off) * 6)
        bx0, bx1 = px + x0 * SC - 6, px + x1 * SC + 6
        bty0, bty1 = py + by0 * SC - ys - 6, py + by1 * SC - ys + 6
        bty0, bty1 = max(py, bty0), min(py + PH, bty1)
        d.rounded_rectangle([bx0, bty0, bx1, bty1], 22, outline=GOLD_HI + (int(255 * ha * pulse),), width=6)
    g = lay.filter(ImageFilter.GaussianBlur(10)); img.alpha_composite(g); img.alpha_composite(lay)

def at(k, off=0): return T[k][0] + off
_h = T["hook2"][0]
BANNERS_SPEC = [(_h + .3, "Setup baru: GOLD SELL", "M15  \u2022  Entry, SL & TP siap dengan reason"),
                (_h + .9, "Get ready: BITCOIN", "Harga hampir ke zon, setup mungkin datang"),
                (_h + 1.5, "Amaran berita USD", "30 minit sebelum berita impak tinggi")]
DINGS = [b[0] for b in BANNERS_SPEC]

BANNERS = BANNERS_SPEC
ICON_SMALL = TRAXA.resize((84, 84), Image.LANCZOS)
def notif_banner(img, y, title, body, t, t0, out):
    p = seg(t, t0, t0 + .4); a = ease(p) * out
    if a <= 0: return
    yy = y - int(120 * (1 - back(p)))
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    d.rounded_rectangle([70, yy, W - 70, yy + 180], 38, fill=(38, 36, 34, int(235 * a)), outline=GOLD + (int(120 * a),), width=2)
    img.alpha_composite(lay.filter(ImageFilter.GaussianBlur(0)))
    paste_alpha(img, ICON_SMALL, (100, yy + 48), a)
    d2 = ImageDraw.Draw(lay2 := Image.new("RGBA", (W, H), (0, 0, 0, 0)))
    d2.text((210, yy + 28), "TRAXA", font=font("SemiBold", 32), fill=MUTED + (int(255 * a),))
    d2.text((W - 230, yy + 28), "sekarang", font=font("Regular", 30), fill=MUTED + (int(255 * a),))
    d2.text((210, yy + 70), title, font=font("Bold", 44), fill=WHITE + (int(255 * a),))
    d2.text((210, yy + 124), body, font=font("Regular", 34), fill=(210, 205, 195, int(255 * a)))
    img.alpha_composite(lay2)

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
        words = [("Masih teka-teka", 330, "Bold", 92, WHITE, at("hook1") - .1),
                 ("bila nak ENTRY?", 450, "Black", 118, "gold", at("hook1", .7)),
                 ("Biar signal yang datang kat kau", 680, "Bold", 60, WHITE, at("hook2") - .1)]
        for s_, y, w, sz, col, st in words:
            p = seg(t, st, st + .35)
            ctext(img, y, s_, font(w, sz), col, ease(p) * out, scale=0.6 + 0.4 * back(p),
                  glow=GOLD if col == "gold" else None)
        for i, (t0, title, body) in enumerate(BANNERS):
            notif_banner(img, 820 + i * 215, title, body, t, t0, out)

    # --- Scene 2: Traxa reveal with real screen recording ---
    if S2 <= t < S3:
        pin = ease(seg(t, S2, S2 + .5)); pout = seg(t, S3 - .35, S3)
        a = pin * (1 - pout); dx = -int(W * ease(pout))
        ctext(img, 190, "TRAXA", font("Black", 130), "gold", a, dx=dx, scale=0.7 + 0.3 * back(seg(t, S2, S2 + .6)), glow=GOLD)
        ctext(img, 350, "Signal trading terus di telefon anda", font("Medium", 46), WHITE, ease(seg(t, S2 + .4, S2 + .8)) * (1 - pout), dx=dx)
        rt = min(2.5, max(0, t - S2 - .3) * 0.75)  # stop on the home screen, before the feedback feed
        scr = hide_dot(Image.open(REC_INTRO[int(rt * FPS)]).convert("RGB"))
        phone_frame(img, scr, (W - PW) // 2 + dx, 450 + int(300 * (1 - pin)), a, ys=int(130 * SC))

    # --- Scene 3: app tour ---
    if S3 <= t < SP:
        for i in range(len(SHOTS)):
            if SHOT_T[i] <= t < SHOT_T[i + 1]: phone_shot(img, i, t)

    # --- Scene 3b: social proof counters ---
    if SP <= t < S4:
        out = 1 - seg(t, S4 - .4, S4)
        k = int((t - SP) * FPS); fb = Image.open(REC_FEED[min(k, len(REC_FEED) - 1)]).convert("RGBA")
        paste_alpha(img, fb, (0, 0), 0.35 * ease(seg(t, SP, SP + .5)) * out)
        logo(img, TRAXA, W / 2, 360, 200 * back(seg(t, SP, SP + .6)), out, glow=GOLD)
        ctext(img, 510, "Baru 3 minggu dilancarkan", font("Bold", 64), WHITE, ease(seg(t, SP, SP + .5)) * out)
        p0, p1_ = T["proof"]; dur = p1_ - p0
        stats = [(5000, "+", "TRADER", p0 + dur * .22), (38, "", "NEGARA", p0 + dur * .5), (300, "+", "FEEDBACK", p0 + dur * .72)]
        for i, (val, suf, label, st) in enumerate(stats):
            a = ease(seg(t, st - .3, st + .1)) * out
            if a <= 0: continue
            y0 = 660 + i * 300; x0 = 110 + int(150 * (1 - a))
            lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
            d.rounded_rectangle([x0, y0, x0 + 860, y0 + 250], 40, fill=(255, 255, 255, int(16 * a)), outline=GOLD + (int(190 * a),), width=3)
            img.alpha_composite(lay)
            v = int(round(val * ease(seg(t, st - .3, st + .9))))
            ti = text_img(f"{v:,}{suf}", font("Black", 130), "gold")
            paste_alpha(img, ti, (x0 + 50, y0 + 125 - ti.height / 2), a)
            li = text_img(label, font("Bold", 46), WHITE)
            paste_alpha(img, li, (x0 + 810 - li.width, y0 + 125 - li.height / 2), a)

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
    """Original trap-style beat: 140 bpm, A minor, beat drops when the brand appears."""
    sr = 44100; t = np.arange(int(sr * DUR)) / sr
    out = np.zeros_like(t); rng = np.random.default_rng(5)
    step = 60 / 140 / 4                      # 16th note
    bar = step * 16
    def add(t0, sig, g=1.0):
        i = int(t0 * sr)
        if 0 <= i < len(out): out[i:i + len(sig)] += sig[:len(out) - i] * g
    def env(L, dec): tt = np.arange(L) / sr; return tt, np.exp(-tt * dec)
    def saw(f, tt, n=8): return sum(np.sin(2 * np.pi * f * k * tt) / k for k in range(1, n))
    # Am - F - Dm - E  (root for 808, chord tones for plucks)
    prog = [(55.0, [440, 523.3, 659.3]), (43.65, [349.2, 440, 523.3]),
            (36.71, [293.7, 349.2, 440]), (41.2, [329.6, 415.3, 493.9])]
    drop = S2
    nb = int(DUR / bar) + 1
    for bi in range(nb):
        b0 = bi * bar; root, ch = prog[bi % 4]
        on = b0 >= drop - 1e-6
        # plucky arpeggio (always on)
        arp = [0, 1, 2, 1, 0, 2, 1, 2]
        for k in range(8):
            f = ch[arp[k]] * (2 if k in (3, 7) else 1)
            tt, e = env(int(step * 2 * sr), 9)
            add(b0 + k * step * 2, saw(f, tt, 6) * e, 0.05)
        # soft pad
        tt = np.arange(int(bar * sr)) / sr
        pe = np.minimum(1, tt * 4) * np.minimum(1, (bar - tt) * 6)
        add(b0, sum(np.sin(2 * np.pi * f / 2 * tt) for f in ch) * pe, 0.035)
        if not on: continue
        # 808 bass with glide + saturation
        for st_, ln in ((0, 7), (10, 6)):
            tt = np.arange(int(step * ln * sr)) / sr
            f = root * (1 + 0.6 * np.exp(-tt * 40))
            sig = np.tanh(2.2 * np.sin(2 * np.pi * np.cumsum(f) / sr)) * np.minimum(1, (step * ln - tt) * 20)
            add(b0 + st_ * step, sig, 0.45)
        # kick
        for st_ in (0, 7, 10):
            tt, e = env(int(.2 * sr), 18)
            add(b0 + st_ * step, np.sin(2 * np.pi * (45 + 120 * np.exp(-tt * 45)) * tt) * e, 0.7)
        # clap / snare on beat 3 (half-time)
        tt, e = env(int(.18 * sr), 28)
        add(b0 + 8 * step, (rng.standard_normal(len(tt)) * .8 + np.sin(2 * np.pi * 190 * tt)) * e, 0.32)
        # hi-hats: 8ths, with 32nd rolls at the end of every 2nd bar
        hats = [i * 2 * step for i in range(8)]
        if bi % 2: hats = hats[:6] + [12 * step + i * step / 2 for i in range(8)]
        for h in hats:
            tt, e = env(int(.035 * sr), 110)
            add(b0 + h, rng.standard_normal(len(tt)) * e, 0.10)
    for d0 in DINGS:  # notification chime
        tt, e = env(int(.5 * sr), 9)
        add(d0, (np.sin(2 * np.pi * 1318.5 * tt) + .6 * np.sin(2 * np.pi * 1975.5 * tt)) * e * np.minimum(1, tt * 400), 0.35)
    for c in CUTS:  # riser whoosh into each scene change
        L = int(.6 * sr); tt = np.arange(L) / sr
        add(c - .6, rng.standard_normal(L) * (tt / .6) ** 2, 0.22)
    fade = np.minimum(1, np.minimum(t / .3, (DUR - t) / 1.5)); out *= fade
    out = out / np.abs(out).max() * 0.22  # music bed under the voice
    if os.environ.get("MUSIC") == "0": out[:] = 0  # voice-only version
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
