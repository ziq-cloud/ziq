"""Generate a vertical (1080x1920) promo video for TikTok / Telegram.
Usage: python3 make_video.py  -> writes out/traxa_promo.mp4 and out/cover.jpg
"""
import math, os, random, subprocess, time, wave
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
        x = (x + sz * 25 * math.sin(t * .35)) % W  # bigger (closer) particles drift more: parallax
        a = int(110 * (0.5 + 0.5 * math.sin(t * 2 + ph)))
        d.ellipse([x - sz, y - sz, x + sz, y + sz], fill=GOLD_HI + (a,))

# ---------- drawing helpers ----------
def paste_alpha(img, im, xy, a):
    if a <= 0: return
    if a < 1:
        im = im.copy(); im.putalpha(im.getchannel("A").point(lambda v: int(v * a)))
    img.alpha_composite(im, (int(xy[0]), int(xy[1])))

def text_img(s, f, fill, stroke=0, stroke_fill=(0, 0, 0)):
    s = tr(s)
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

# ---------- 3D: perspective warp of a flat layer ----------
def _coeffs(dst, src):
    A, B = [], []
    for (X, Y), (u, v) in zip(dst, src):
        A.append([X, Y, 1, 0, 0, 0, -u * X, -u * Y]); B.append(u)
        A.append([0, 0, 0, X, Y, 1, -v * X, -v * Y]); B.append(v)
    return np.linalg.solve(np.array(A, float), np.array(B, float)).tolist()

def warp3d(img, layer, cx, cy, ry=0.0, rx=0.0, scale=1.0, a=1.0, f=2400, shade=True):
    """Rotate a flat RGBA layer around its centre (ry: Y axis, rx: X axis, degrees) and project it."""
    if a <= 0: return
    w, h = layer.size; cy_, sy_ = math.cos(math.radians(ry)), math.sin(math.radians(ry))
    cx_, sx_ = math.cos(math.radians(rx)), math.sin(math.radians(rx))
    pts = []
    for x, y in ((-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2)):
        X, Z = x * cy_, -x * sy_
        Y, Z = y * cx_ - Z * sx_, y * sx_ + Z * cx_
        k = f / max(200, f + Z) * scale
        pts.append((cx + X * k, cy + Y * k))
    x0 = int(min(p[0] for p in pts)); y0 = int(min(p[1] for p in pts))
    x1 = int(max(p[0] for p in pts)) + 1; y1 = int(max(p[1] for p in pts)) + 1
    if x1 < 0 or x0 > W or y1 < 0 or y0 > H or x1 - x0 < 2 or y1 - y0 < 2: return
    if shade:  # faces turned away from the camera get darker
        dark = 0.6 * (1 - abs(cy_ * cx_))
        if dark > 0.01:
            rgb = layer.convert("RGB").point(lambda v: int(v * (1 - dark))); rgb.putalpha(layer.getchannel("A")); layer = rgb
    c = _coeffs([(px - x0, py - y0) for px, py in pts], [(0, 0), (w, 0), (w, h), (0, h)])
    out = layer.transform((x1 - x0, y1 - y0), Image.PERSPECTIVE, c, Image.BICUBIC)
    # clip to canvas so alpha_composite never gets a negative offset
    cl, ct = max(0, -x0), max(0, -y0); cr, cb = min(out.width, W - x0), min(out.height, H - y0)
    if cr <= cl or cb <= ct: return
    paste_alpha(img, out.crop((cl, ct, cr, cb)), (x0 + cl, y0 + ct), a)

def logo3d(img, src, cx, cy, size, a, ang, glow=None, depth=16):
    """Logo spinning around the Y axis, with an extruded gold edge."""
    if a <= 0 or size < 2: return
    s_ = size / max(src.size)
    im = src.resize((max(1, int(src.width * s_)), max(1, int(src.height * s_))), Image.LANCZOS)
    c = math.cos(math.radians(ang)); sn = math.sin(math.radians(ang))
    face = im if c >= 0 else im.transpose(Image.FLIP_LEFT_RIGHT)
    fw = max(2, int(im.width * abs(c)))
    face = face.resize((fw, im.height), Image.LANCZOS)
    if glow: logo(img, im, cx, cy, size, a * .9 * (0.4 + 0.6 * abs(c)), glow=glow)
    edge = Image.new("RGBA", face.size, GOLD_LO + (255,)); edge.putalpha(face.getchannel("A"))
    for k in range(depth, 0, -1):  # extrusion
        paste_alpha(img, edge, (cx - fw / 2 - sn * k * .9, cy - im.height / 2), a)
    lit = face.convert("RGB").point(lambda v: int(min(255, v * (0.7 + 0.3 * abs(c))))); lit.putalpha(face.getchannel("A"))
    paste_alpha(img, lit, (cx - fw / 2, cy - im.height / 2), a)

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
LANG = os.environ.get("LANG_VIDEO", "en")  # "en" or "bm"
VOICE = os.environ.get("VOICE", "en-US-AndrewNeural" if LANG == "en" else "ms-MY-OsmanNeural")
EN = {
    "Masih teka-teka": "Still guessing", "bila nak ENTRY?": "your ENTRY?",
    "Biar signal yang datang kat kau": "Let the signals come to you",
    "Signal trading terus di telefon anda": "Trading signals, right on your phone",
    "3 PAIR UTAMA": "3 MAIN PAIRS", "Gold  \u2022  Bitcoin  \u2022  Oil  \u2014  harga live": "Gold  \u2022  Bitcoin  \u2022  Oil  \u2014  live prices",
    "REASON SETIAP ENTRY": "A REASON FOR EVERY ENTRY", "Entry, SL & TP siap dengan sebab": "Entry, SL & TP with the reason why",
    "NOTIFIKASI SETIAP SIGNAL": "ALERTS FOR EVERY SIGNAL", "Setup baru, keputusan, berita & get ready alert": "New setups, results, news & get-ready alerts",
    "Key level untuk setiap timeframe": "Key levels for every timeframe",
    "BERITA & FUNDAMENTAL": "NEWS & FUNDAMENTALS", "Kalendar berita USD terus dalam app": "USD news calendar, built right in",
    "KELAS EDUKASI": "EDUCATION LESSONS", "Market structure hingga breakout": "From market structure to breakouts",
    "Setup baru: GOLD SELL": "New setup: GOLD SELL", "M15  \u2022  Entry, SL & TP siap dengan reason": "M15  \u2022  Entry, SL & TP with the reason",
    "Harga hampir ke zon, setup mungkin datang": "Price nearing a zone, a setup may come",
    "Amaran berita USD": "USD news warning", "30 minit sebelum berita impak tinggi": "30 min before high-impact news",
    "sekarang": "now",
    "Baru 3 minggu dilancarkan": "Just 3 weeks since launch", "TRADER": "TRADERS", "NEGARA": "COUNTRIES",
    "Daftar sekarang": "Sign up now", "guna kod jemputan saya": "with my invite code", "Link pendaftaran:": "Sign-up link:",
    "Link ada di bio / pinned \u2191": "Link in bio / pinned \u2191",
    "Join channel Telegram": "Join our Telegram channel", "Follow untuk tips & update trading": "Follow for tips & trading updates",
    "Kod jemputan: ZIQFX": "Invite code: ZIQFX",
    "Trading melibatkan risiko. Hanya labur apa yang": "Trading involves risk. Only trade what you can",
    "anda sanggup rugi. Bukan nasihat kewangan.": "afford to lose. Not financial advice.",
}
def tr(s): return EN.get(s, s) if LANG == "en" else s
VDIR = os.path.join(HERE, "voice", VOICE)
RATE = "+15%" if LANG == "bm" else "+5%"
LINES = [
    ("hook1", "Masih teka-teka bila nak entry?"),
    ("hook2", "Biar signal yang datang kat kau."),
    ("brand", "Cuba TRAXA Trading App. Signal trading terus di telefon anda."),
    ("p1", "Ada tiga pair utama: Gold, Bitcoin dan Oil, dengan harga live."),
    ("p2", "Setiap setup ada entry, stop loss dan take profit, siap dengan reason kenapa setup itu dihantar."),
    ("p3", "Setup baru, keputusan, amaran berita dan get ready alert, semua terus masuk notifikasi telefon."),
    ("p4", "Support, resistance dan key level untuk setiap timeframe."),
    ("pn", "Kalendar berita USD dan fundamental emas pun ada dalam app."),
    ("p5", "Ada juga kelas edukasi, dari market structure sampai breakout."),
    ("proof", "Baru tiga minggu dilancarkan, dah lebih lima ribu trader dari tiga puluh lapan negara, dengan lebih tiga ratus feedback."),
    ("cta1", "Daftar sekarang, guna kod jemputan saya."),
    ("code", "Z, I, Q, F, X."),
    ("cta2", "Link pendaftaran ada di bio dan pinned."),
    ("outro", "Join channel Telegram, i-Fang F X, untuk tips dan update trading."),
    ("risk", "Ingat, trading ada risiko. Labur dengan bijak."),
]
if LANG == "en":
    LINES = [
        ("hook1", "Still guessing your entry?"),
        ("hook2", "Let the signals come to you."),
        ("brand", "Try TRAXA Trading App. Trading signals, right on your phone."),
        ("p1", "Three main pairs: Gold, Bitcoin and Oil, with live prices."),
        ("p2", "Every setup comes with entry, stop loss and take profit, plus the reason why it was sent."),
        ("p3", "New setups, results, news warnings and get-ready alerts, pushed straight to your phone."),
        ("p4", "Support, resistance and key levels for every timeframe."),
        ("pn", "The USD news calendar and gold fundamentals are built right in."),
        ("p5", "Plus education lessons, from market structure to breakouts."),
        ("proof", "Just three weeks since launch: over five thousand traders, thirty-eight countries, and more than three hundred feedback posts."),
        ("cta1", "Sign up now with my invite code."),
        ("code", "Z. I. Q. F. X."),
        ("cta2", "The sign-up link is in my bio and pinned."),
        ("outro", "Join the i-Fang F X Telegram channel for tips and trading updates."),
        ("risk", "Remember, trading involves risk. Trade responsibly."),
    ]
SCENE_START = {"brand", "p1", "p2", "p3", "p4", "pn", "p5", "proof", "cta1", "outro"}  # a new scene begins with these lines

def tts(key, text):
    os.makedirs(VDIR, exist_ok=True)
    import hashlib
    mp3 = os.path.join(VDIR, f"{key}_{hashlib.md5((text + RATE).encode()).hexdigest()[:6]}.mp3")
    if not os.path.exists(mp3):  # needs network access to speech.platform.bing.com
        cmd = ["edge-tts", "--voice", VOICE, f"--rate={RATE}", "--text", text, "--write-media", mp3]
        if os.environ.get("HTTPS_PROXY"): cmd[1:1] = ["--proxy", os.environ["HTTPS_PROXY"]]
        for attempt in range(4):  # the TTS service occasionally returns no audio; retry
            r = subprocess.run(cmd, capture_output=True)
            if r.returncode == 0 and os.path.getsize(mp3) > 2000: break
            if os.path.exists(mp3): os.remove(mp3)
            time.sleep(2)
        else:
            raise RuntimeError(f"TTS failed for {key}: {r.stderr.decode()[-300:]}")
    raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", mp3, "-f", "s16le", "-ac", "1", "-ar", "44100", "-"],
                         capture_output=True, check=True).stdout
    a = np.frombuffer(raw, np.int16).astype(np.float32) / 32768
    nz = np.where(np.abs(a) > 0.01)[0]  # trim silence
    return a[max(0, nz[0] - 800):nz[-1] + 2000] if len(nz) else a

CLIPS, T = {}, {}
cur = 0.2
for key, text in LINES:
    if key in SCENE_START: cur += 0.35
    if key == "brand": cur += 1.4 if LANG == "en" else 0.7  # let the notification banners land
    a = tts(key, text); CLIPS[key] = a; T[key] = (cur, cur + len(a) / 44100)
    cur = T[key][1] + 0.15
DUR = cur + 1.2
N = int(FPS * DUR)
S1 = 0
S2, S3, S4, S5 = (T[k][0] - 0.25 for k in ("brand", "p1", "cta1", "outro"))
SP = T["proof"][0] - 0.25
SHOT_T = [T[k][0] - 0.25 for k in ("p1", "p2", "p3", "p4", "pn", "p5")] + [SP]
CUTS = [S2, SP, S4, S5]

# ---------- app screenshots shown inside a phone mockup ----------
# boxes are in 921-px-wide screenshot coordinates: (x0, y0, x1, y1, appear-after-seconds)
# source is a screenshot name, or ("rec", file, start, end) for a slice of a screen recording
SHOTS = [
    (("rec", "rec3.mp4", 0.0, 5.0), "3 PAIR UTAMA", "Gold  \u2022  Bitcoin  \u2022  Oil  \u2014  harga live", 130, 0, []),
    (("rec", "rec3.mp4", 5.0, 11.0), "REASON SETIAP ENTRY", "Entry, SL & TP siap dengan sebab", 130, 0, []),
    ("notif", "NOTIFIKASI SETIAP SIGNAL", "Setup baru, keputusan, berita & get ready alert", 130, 0,
     [(58, 488, 863, 1108, .6), (58, 1197, 863, 1640, 3.4)]),
    ("levels", "SUPPORT & RESISTANCE", "Key level untuk setiap timeframe", 130, 120,
     [(72, 490, 848, 1035, .6), (75, 1130, 848, 1405, 2.4)]),
    (("rec", "rec4.mp4", 4.3, 10.4), "BERITA & FUNDAMENTAL", "Kalendar berita USD terus dalam app", 130, 0, []),
    (("rec", "rec6.mp4", 0.0, 4.3), "KELAS EDUKASI", "Market structure hingga breakout", 130, 0, []),
]
PW, PH, BZ = 620, 1180, 16  # phone screen size and bezel
SC = PW / 921
SCREENS = {}
for name, *_ in SHOTS:
    if not isinstance(name, str): continue
    im = Image.open(os.path.join(HERE, f"assets/screens/{name}.png")).convert("RGB")
    SCREENS[name] = im.resize((PW, int(im.height * PW / im.width)), Image.LANCZOS)
SCREEN_MASK = Image.new("L", (PW, PH), 0); ImageDraw.Draw(SCREEN_MASK).rounded_rectangle([0, 0, PW - 1, PH - 1], 58, fill=255)
PHONE = Image.new("RGBA", (PW + 2 * BZ, PH + 2 * BZ), (0, 0, 0, 0))
ImageDraw.Draw(PHONE).rounded_rectangle([0, 0, PW + 2 * BZ - 1, PH + 2 * BZ - 1], 72, fill=(20, 18, 16, 255), outline=GOLD + (200,), width=3)
PHONE_GLOW = Image.new("RGBA", (PHONE.width + 200, PHONE.height + 200), (0, 0, 0, 0))
ImageDraw.Draw(PHONE_GLOW).rounded_rectangle([100, 100, 100 + PHONE.width, 100 + PHONE.height], 72, fill=GOLD + (110,))
PHONE_GLOW = PHONE_GLOW.filter(ImageFilter.GaussianBlur(45))

# ---------- real screen recordings ----------
def extract(src, dst, vf, dur, ss=0.0):
    d = os.path.join(OUT, dst)
    if not os.path.isdir(d) or not os.listdir(d):
        os.makedirs(d, exist_ok=True)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(ss), "-i", os.path.join(HERE, "assets/rec", src), "-t", str(dur),
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

REC_SHOTS = {}
for sh in SHOTS:
    if not isinstance(sh[0], str):
        _, f, r0, r1 = sh[0]
        REC_SHOTS[(f, r0, r1)] = extract(f, f"rec_{f}_{r0}_{r1}", f"fps={FPS},scale={PW}:-2", r1 - r0, ss=r0)

M3 = 100  # glow margin around the phone layer
def phone_layer(scr, ys, boxes=(), sheen=0.0):
    L = Image.new("RGBA", (PW + 2 * BZ + 2 * M3, PH + 2 * BZ + 2 * M3), (0, 0, 0, 0))
    L.alpha_composite(PHONE_GLOW, (0, 0)); L.alpha_composite(PHONE, (M3, M3))
    sc = scr.crop((0, ys, PW, ys + PH)).convert("RGBA"); sc.putalpha(SCREEN_MASK)
    ox, oy = M3 + BZ, M3 + BZ; L.alpha_composite(sc, (ox, oy))
    if boxes:
        lay = Image.new("RGBA", L.size, (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
        for (x0, by0, x1, by1, al) in boxes:
            bt0, bt1 = max(oy, oy + by0 * SC - ys - 6), min(oy + PH, oy + by1 * SC - ys + 6)
            d.rounded_rectangle([ox + x0 * SC - 6, bt0, ox + x1 * SC + 6, bt1], 22, outline=GOLD_HI + (int(255 * al),), width=6)
        L.alpha_composite(lay.filter(ImageFilter.GaussianBlur(10))); L.alpha_composite(lay)
    if sheen > 0.01:  # glass reflection that slides with the rotation
        g = Image.new("RGBA", (PW, PH), (0, 0, 0, 0)); gd = ImageDraw.Draw(g)
        bx = int(PW * (0.5 + 0.9 * sheen))
        gd.polygon([(bx - 260, 0), (bx - 60, 0), (bx - 360, PH), (bx - 560, PH)], fill=(255, 255, 255, 46))
        g = g.filter(ImageFilter.GaussianBlur(30))
        g.putalpha(Image.fromarray(np.minimum(np.array(g.getchannel("A")), np.array(SCREEN_MASK))))
        L.alpha_composite(g, (ox, oy))
    return L

def phone3d(img, scr, ys, pin, pout, t, a, boxes=(), zoom=None):
    """Phone swings in from the right (rotating on Y), floats, then swings out to the left.
    zoom = (x, y, amount, z): push the camera towards screen point (x, y) in 921-px screenshot coords."""
    zp = zoom[2] if zoom else 0.0
    ry = (78 * (1 - pin) - 78 * ease(pout)) + 5 * math.sin(t * 1.1) * (1 - .8 * zp)
    rx = 4 * math.sin(t * .8 + 1) * (1 - .8 * zp)
    cx = W / 2 + 520 * (1 - pin) - 520 * ease(pout)
    cy = 450 + PH / 2 + 20 * math.sin(t * 1.3) * (1 - zp)
    L = phone_layer(scr, ys, boxes, sheen=ry / 90)
    z = 1.0
    if zp > 0:
        sx, sy, _, zmax = zoom; z = 1 + (zmax - 1) * zp
        dxp = M3 + BZ + sx * SC - L.width / 2; dyp = M3 + BZ + sy * SC - ys - L.height / 2
        cx = (1 - zp) * cx + zp * (W / 2 - dxp * z); cy = (1 - zp) * cy + zp * (1000 - dyp * z)
    warp3d(img, L, cx, cy, ry=ry, rx=rx, a=a, scale=z)

# shot index -> (x, y in 921-px coords, start offset, end offset, max zoom)
ZOOMS = {0: (460, 500, 1.2, 3.4, 1.55), 1: (560, 1120, 1.4, 4.4, 1.75), 2: (460, 800, 1.0, 3.0, 1.35), 3: (460, 760, .9, 2.6, 1.4)}

def phone_shot(img, i, t):
    name, title, sub, y0, pan, boxes = SHOTS[i]
    s0, s1 = SHOT_T[i], SHOT_T[i + 1]
    zm = None
    if i in ZOOMS:
        zx, zy, z0, z1, zmax = ZOOMS[i]; z1 = min(z1, s1 - s0 - .6)
        zp = ease(seg(t, s0 + z0, s0 + z0 + .5)) * (1 - ease(seg(t, s0 + z1 - .45, s0 + z1)))
        if zp > 0: zm = (zx, zy, zp, zmax)
    pin, pout = ease(seg(t, s0, s0 + .6)), seg(t, s1 - .4, s1)
    a = min(1, pin * 1.5) * (1 - pout ** 3)
    dx = int(W * (1 - pin)) - int(W * ease(pout))
    tf = 1 - (zm[2] if zm else 0)
    ctext(img, 250, title, font("Black", 64), "gold", pin * (1 - pout) * tf, dx=dx, glow=GOLD)
    ctext(img, 345, sub, font("Medium", 44), WHITE, ease(seg(t, s0 + .2, s0 + .6)) * (1 - pout) * tf, dx=dx)
    if isinstance(name, str):
        src = SCREENS[name]
    else:  # play the recording slice across the shot
        _, f, r0, r1 = name
        frames = REC_SHOTS[(f, r0, r1)]
        k = int(seg(t, s0 + .3, s1 - .3) * (len(frames) - 1))
        src = hide_dot(Image.open(frames[k]).convert("RGB"))
    ys = min(int(y0 * SC + pan * SC * ease(seg(t, s0 + .5, s1 - .4))), src.height - PH)
    bx = []
    for (x0, by0, x1, by1, off) in boxes:
        ha = ease(seg(t, s0 + off, s0 + off + .4)) * (1 - pout)
        if ha > 0: bx.append((x0, by0, x1, by1, ha * (0.75 + 0.25 * math.sin((t - s0 - off) * 6))))
    phone3d(img, src, ys, pin, pout, t, a, bx, zoom=zm)

def at(k, off=0): return T[k][0] + off
_bar = 60 / 140 * 4
KICKS = [bi * _bar + st * _bar / 16 for bi in range(int(DUR / _bar) + 1) for st in (0, 7, 10) if bi * _bar >= S2 - 1e-6]
_h = T["hook2"][0]
BANNERS_SPEC = [(_h + .3, "Setup baru: GOLD SELL", "M15  \u2022  Entry, SL & TP siap dengan reason"),
                (_h + .9, "Get ready: BITCOIN", "Harga hampir ke zon, setup mungkin datang"),
                (_h + 1.5, "Amaran berita USD", "30 minit sebelum berita impak tinggi")]
DINGS = [b[0] for b in BANNERS_SPEC]
COUNT_LEN = 1.8
_c0, _c1 = T["code"]
CODE_STOPS = [_c0 + (_c1 - _c0) * (i + .7) / len(CODE) for i in range(len(CODE))]
_p0, _p1 = T["proof"]
COUNTS = [_p0 + (_p1 - _p0) * f for f in (.22, .5, .72)]  # when each stat starts counting

BANNERS = BANNERS_SPEC
def _ifang_big():
    s_ = 760 / max(IFANG.size); im = IFANG.resize((int(IFANG.width * s_), int(IFANG.height * s_)), Image.LANCZOS)
    L = Image.new("RGBA", (im.width + 200, im.height + 200), (0, 0, 0, 0))
    sh = Image.new("RGBA", im.size, GOLD + (255,)); sh.putalpha(im.getchannel("A"))
    L.alpha_composite(sh, (100, 100)); L = L.filter(ImageFilter.GaussianBlur(40)); L.alpha_composite(im, (100, 100))
    return L
IFANG_BIG = _ifang_big()
ICON_SMALL = TRAXA.resize((84, 84), Image.LANCZOS)
def notif_banner(img, y, title, body, t, t0, out):
    p = seg(t, t0, t0 + .5); a = min(1, ease(p) * 1.6) * out
    if a <= 0: return
    bw, bh, m = W - 140, 180, 20
    L = Image.new("RGBA", (bw + 2 * m, bh + 2 * m), (0, 0, 0, 0)); d = ImageDraw.Draw(L)
    d.rounded_rectangle([m, m, m + bw, m + bh], 38, fill=(38, 36, 34, 240), outline=GOLD + (140,), width=2)
    L.alpha_composite(ICON_SMALL, (m + 30, m + 48))
    d.text((m + 140, m + 28), "TRAXA", font=font("SemiBold", 32), fill=MUTED)
    d.text((m + bw - 160, m + 28), tr("sekarang"), font=font("Regular", 30), fill=MUTED)
    d.text((m + 140, m + 70), tr(title), font=font("Bold", 44), fill=WHITE)
    d.text((m + 140, m + 124), tr(body), font=font("Regular", 34), fill=(210, 205, 195))
    q = back(p)
    warp3d(img, L, W / 2, y + bh / 2 - 160 * (1 - q), rx=-75 * (1 - q) + 3 * math.sin(t * 1.5 + y),
           ry=4 * math.sin(t * 1.1 + y / 200), scale=0.75 + 0.25 * q, a=a)

# ---------- TikTok-style word-by-word captions ----------
CAP_FIX = {"Z. I. Q. F. X.": "ZIQFX", "Z, I, Q, F, X.": "ZIQFX", "i-Fang F X": "iFANG FX"}
def _caption_chunks():
    chunks = []
    for key, text in LINES:
        for a_, b_ in CAP_FIX.items(): text = text.replace(a_, b_)
        words = [w.strip(".,:") for w in text.split()]
        words = [w for w in words if w]
        t0, t1 = T[key]; wts = [len(w) + 2 for w in words]; tot = sum(wts); cur_ = t0; timed = []
        for w, wt in zip(words, wts):
            d_ = (t1 - t0) * wt / tot; timed.append((w, cur_, cur_ + d_)); cur_ += d_
        group = []
        for item in timed:
            if group and len(" ".join(g[0] for g in group + [item])) > 20:
                chunks.append(group); group = []
            group.append(item)
        if group: chunks.append(group)
    out = []
    for i, g in enumerate(chunks):  # hold each chunk until the next one starts (if the gap is short)
        end = g[-1][2]; nxt = chunks[i + 1][0][1] if i + 1 < len(chunks) else end + .3
        out.append((g, g[0][1] - .05, nxt if nxt - end < .4 else end + .2))
    return out
CAPS = _caption_chunks()
_band = np.zeros((H, 1), np.float32)
_band[:240, 0] = np.linspace(.8, 0, 240) ** 1.5
_band[1560:, 0] = np.linspace(0, .9, H - 1560) ** .8
EDGE_BANDS = Image.fromarray(np.dstack([np.zeros((H, W, 3), np.uint8),
                                       np.repeat((_band * 255).astype(np.uint8), W, axis=1)]), "RGBA")

def captions(img, t):
    for g, c0, c1 in CAPS:
        if not c0 <= t < c1: continue
        pop = .85 + .15 * back(seg(t, c0, c0 + .18))
        f = font("Black", 58); imgs = []
        for w, w0, w1 in g:
            on = w0 <= t < w1 + .05
            asc, desc = f.getmetrics(); st_ = 7
            ti = Image.new("RGBA", (int(f.getlength(w)) + 2 * st_ + 4, asc + desc + 2 * st_), (0, 0, 0, 0))
            ImageDraw.Draw(ti).text((st_ + 2, st_), w, font=f, fill=GOLD_HI if on else WHITE, stroke_width=st_, stroke_fill=(0, 0, 0))
            sc_ = pop * (1.12 if on else 1.0)
            imgs.append(ti.resize((int(ti.width * sc_), int(ti.height * sc_)), Image.LANCZOS))
        gap = 18; tw = sum(i_.width for i_ in imgs) + gap * (len(imgs) - 1); x = (W - tw) / 2
        for i_ in imgs:
            img.alpha_composite(i_, (int(x), int(1688 - i_.height / 2))); x += i_.width + gap
        return

def frame(n):
    t = n / FPS
    img = BASE.copy().convert("RGBA")
    # chart, stronger during hook
    strength = 0.55 if t < S2 else 0.16
    if t >= S2 - .3 and t < S2: strength = 0.55 - 0.39 * seg(t, S2 - .3, S2)
    ch = chart_layer(t, strength); px_ = int(40 * math.sin(t * .35))
    img.alpha_composite(ch.crop((max(0, -px_), 0, W - max(0, px_), H)), (max(0, px_), 0))
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
        pin = ease(seg(t, S2, S2 + .6)); pout = seg(t, S3 - .4, S3)
        a = pin * (1 - pout); dx = -int(W * ease(pout))
        ctext(img, 190, "TRAXA", font("Black", 130), "gold", a, dx=dx, scale=0.7 + 0.3 * back(seg(t, S2, S2 + .6)), glow=GOLD)
        ctext(img, 350, "Signal trading terus di telefon anda", font("Medium", 46), WHITE, ease(seg(t, S2 + .4, S2 + .8)) * (1 - pout), dx=dx)
        rt = min(2.5, max(0, t - S2 - .3) * 0.75)  # stop on the home screen, before the feedback feed
        scr = hide_dot(Image.open(REC_INTRO[int(rt * FPS)]).convert("RGB"))
        phone3d(img, scr, int(130 * SC), pin, ease(pout) * 0 + pout, t, min(1, pin * 1.5) * (1 - pout ** 3))

    # --- Scene 3: app tour ---
    if S3 <= t < SP:
        for i in range(len(SHOTS)):
            if SHOT_T[i] <= t < SHOT_T[i + 1]: phone_shot(img, i, t)

    # --- Scene 3b: social proof counters ---
    if SP <= t < S4:
        out = 1 - seg(t, S4 - .4, S4)
        k = int((t - SP) * FPS); fb = Image.open(REC_FEED[min(k, len(REC_FEED) - 1)]).convert("RGBA")
        paste_alpha(img, fb, (0, 0), 0.35 * ease(seg(t, SP, SP + .5)) * out)
        sp = ease(seg(t, SP, SP + 1.2)); logo3d(img, TRAXA, W / 2, 360, 200, out * min(1, sp * 3), -360 * (1 - sp) + 18 * math.sin(t * 1.4), glow=GOLD)
        ctext(img, 510, "Baru 3 minggu dilancarkan", font("Bold", 64), WHITE, ease(seg(t, SP, SP + .5)) * out)
        p0, p1_ = T["proof"]; dur = p1_ - p0
        stats = [(5000, "+", "TRADER", COUNTS[0]), (38, "", "NEGARA", COUNTS[1]), (300, "+", "FEEDBACK", COUNTS[2])]
        for i, (val, suf, label, st) in enumerate(stats):
            a = ease(seg(t, st - .3, st + .1)) * out
            if a <= 0: continue
            y0 = 660 + i * 300; m = 30
            L = Image.new("RGBA", (860 + 2 * m, 250 + 2 * m), (0, 0, 0, 0)); d = ImageDraw.Draw(L)
            d.rounded_rectangle([m, m, m + 860, m + 250], 40, fill=(30, 27, 22, 200), outline=GOLD + (190,), width=3)
            c0, c1 = st - .3, st + COUNT_LEN
            v = int(round(val * (1 - (1 - seg(t, c0, c1)) ** 4)))  # fast start, slow landing
            q = seg(t, c1, c1 + .35); pop = 1 + .14 * math.sin(math.pi * q)
            if 0 < q < 1:  # flash the card when the number lands
                fl = Image.new("RGBA", L.size, (0, 0, 0, 0))
                ImageDraw.Draw(fl).rounded_rectangle([m, m, m + 860, m + 250], 40, outline=GOLD_HI + (int(255 * math.sin(math.pi * q)),), width=10)
                L.alpha_composite(fl.filter(ImageFilter.GaussianBlur(12)))
            ti = text_img(f"{v:,}{suf if seg(t, c0, c1) >= 1 else ''}", font("Black", 130), "gold")
            if pop != 1: ti = ti.resize((int(ti.width * pop), int(ti.height * pop)), Image.LANCZOS)
            L.alpha_composite(ti, (m + 50, int(m + 125 - ti.height / 2)))
            li = text_img(label, font("Bold", 46), WHITE)
            L.alpha_composite(li, (m + 810 - li.width, int(m + 125 - li.height / 2)))
            pin_ = back(seg(t, st - .3, st + .3))
            warp3d(img, L, W / 2, y0 + 125, rx=80 * (1 - pin_) + 3 * math.sin(t * 1.2 + i),
                   ry=7 * math.sin(t * .9 + i * 1.7), a=a)

    # --- Scene 4: CTA with code ---
    if S4 <= t < S5:
        out = 1 - seg(t, S5 - .4, S5)
        sp = ease(seg(t, S4, S4 + 1.0)); logo3d(img, TRAXA, W / 2, 400, 170, out * min(1, sp * 3), 360 * (1 - sp) + 15 * math.sin(t * 1.3))
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
            fnt = font("Black", int(180 * pulse))
            slots = [text_img(ch, fnt, BLACK) for ch in CODE]
            tw = sum(sl.width for sl in slots); hh = max(sl.height for sl in slots)
            x = cx - tw / 2; fr = int(t * FPS)
            for i, (ch, sl) in enumerate(zip(CODE, slots)):
                if t < CODE_STOPS[i]:  # still spinning: random glyph, scrolling down
                    rnd = random.Random(fr * 31 + i * 7).choice("ABCDEFGHJKLMNPQRSTUVWXYZ0123456789")
                    gi = text_img(rnd, fnt, BLACK); off = ((t * 14 + i * .37) % 1 - .5) * 70
                    paste_alpha(img, gi, (x + (sl.width - gi.width) / 2, cy - hh / 2 + off), a2 * .55)
                else:
                    bounce = -22 * math.sin(math.pi * seg(t, CODE_STOPS[i], CODE_STOPS[i] + .22))
                    paste_alpha(img, sl, (x, cy - hh / 2 + bounce), a2)
                x += sl.width
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
        sz = IFANG_BIG.size
        warp3d(img, IFANG_BIG, W / 2, 720, ry=-90 * (1 - back(p)) + 8 * math.sin(t * 1.2), rx=4 * math.sin(t * .9),
               a=min(1, ease(p) * 2), shade=False)
        a = ease(seg(t, at("outro") - .1, at("outro", .4)))
        ctext(img, 1080, "Join channel Telegram", font("SemiBold", 60), WHITE, a)
        if a > 0:
            lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
            d.rounded_rectangle([130, 1180, W - 130, 1320], 70, fill=TG + (int(255 * a),))
            img.alpha_composite(lay)
        ctext(img, 1212, "t.me/iFangFx", font("Black", 72), WHITE, a)
        ctext(img, 1400, "Follow untuk tips & update trading", font("Medium", 48), MUTED, ease(seg(t, at("outro", 1.6), at("outro", 2.1))))
        ctext(img, 1480, "Kod jemputan: ZIQFX", font("Bold", 56), "gold", ease(seg(t, at("risk") - .2, at("risk", .3))))

    # --- zoom punch on each kick ---
    past = [k for k in KICKS if 0 <= t - k < .35]
    if past:
        z = 1 + .022 * math.exp(-(t - past[-1]) * 14)
        big = img.resize((int(W * z), int(H * z)), Image.BILINEAR)
        img = big.crop(((big.width - W) // 2, (big.height - H) // 2, (big.width - W) // 2 + W, (big.height - H) // 2 + H))
    img.alpha_composite(EDGE_BANDS)
    captions(img, t)

    # --- persistent overlays ---
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
    if t < S5:  # channel watermark
        logo(img, IFANG, 140, 130, 190, 0.92)
        d.text((250, 112), "t.me/iFangFx", font=font("SemiBold", 38), fill=WHITE + (200,))
    for i, s in enumerate(["Trading melibatkan risiko. Hanya labur apa yang", "anda sanggup rugi. Bukan nasihat kewangan."]):
        s = tr(s)
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
    for st in COUNTS:  # counter ticks that slow down, then a chime
        c0, c1 = st - .3, st + COUNT_LEN
        for k in range(28):  # one tick per equal step of the displayed number
            p = 1 - (1 - k / 28) ** .25
            tt, e = env(int(.012 * sr), 400)
            add(c0 + (c1 - c0) * p, np.sin(2 * np.pi * 2600 * tt) * e, 0.12)
        tt, e = env(int(.6 * sr), 7)
        add(c1, (np.sin(2 * np.pi * 1568 * tt) + .5 * np.sin(2 * np.pi * 2349 * tt)) * e * np.minimum(1, tt * 400), 0.3)
    for i, cs in enumerate(CODE_STOPS):  # slot machine: a click per letter, chime on the last
        tt, e = env(int(.03 * sr), 160)
        add(cs, np.sin(2 * np.pi * 1900 * tt) * e, 0.22)
        if i == len(CODE_STOPS) - 1:
            tt, e = env(int(.8 * sr), 5)
            add(cs + .05, (np.sin(2 * np.pi * 1318.5 * tt) + .6 * np.sin(2 * np.pi * 1975.5 * tt) + .4 * np.sin(2 * np.pi * 2637 * tt)) * e * np.minimum(1, tt * 400), 0.3)
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
