"""Generate a vertical (1080x1920) promo video for TikTok / Telegram.
Usage: python3 make_video.py  -> writes out/traxa_promo.mp4
"""
import math, os, random, subprocess, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS, DUR = 1080, 1920, 30, 20
N = FPS * DUR
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out"); FR = os.path.join(OUT, "frames")
os.makedirs(FR, exist_ok=True)

CODE = "ZIQFX"
LINK = "traxatradingapp.com/?invite=ZIQFX"
F = "/usr/share/fonts/opentype/inter/"
def font(w, s): return ImageFont.truetype(F + f"Inter-{w}.otf", s)
BG1, BG2 = (6, 10, 24), (12, 26, 54)
GREEN, RED, GOLD, WHITE, MUTED = (0, 214, 143), (255, 77, 106), (255, 196, 61), (255, 255, 255), (150, 165, 195)

def ease(t): t = max(0, min(1, t)); return 1 - (1 - t) ** 3
def seg(t, a, b): return max(0.0, min(1.0, (t - a) / (b - a)))

# background gradient
grad = np.zeros((H, W, 3), np.uint8)
for i, c in enumerate(zip(BG1, BG2)):
    grad[..., i] = np.linspace(c[0], c[1], H)[:, None].astype(np.uint8)
BASE = Image.fromarray(grad)

# random-walk candles
random.seed(7)
candles, p = [], 100.0
for _ in range(60):
    o = p; c = o + random.gauss(0.35, 2.2); hi = max(o, c) + abs(random.gauss(0, 1.2)); lo = min(o, c) - abs(random.gauss(0, 1.2))
    candles.append((o, hi, lo, c)); p = c

def draw_chart(d, t, alpha):
    visible = min(len(candles), int(8 + t * 4))
    cs = candles[max(0, visible - 22):visible]
    lo = min(x[2] for x in cs); hi = max(x[1] for x in cs)
    top, bot = 380, 1450; cw = W / 22
    def y(v): return bot - (v - lo) / (hi - lo + 1e-6) * (bot - top)
    for i, (o, h, l, c) in enumerate(cs):
        col = GREEN if c >= o else RED
        col = tuple(int(v * alpha) + int(BG1[k] * (1 - alpha)) for k, v in enumerate(col))
        x = i * cw + cw / 2
        d.line([(x, y(h)), (x, y(l))], fill=col, width=3)
        d.rectangle([x - cw * 0.32, min(y(o), y(c)), x + cw * 0.32, max(y(o), y(c)) + 2], fill=col)

def ctext(d, y, s, f, fill, a=1.0, dy=0):
    fill = tuple(int(fill[k] * a + 0 * (1 - a)) for k in range(3)) + (int(255 * a),)
    w = d.textlength(s, font=f); d.text(((W - w) / 2, y + dy), s, font=f, fill=fill)

def pill(d, box, fill, r=40, outline=None, width=0):
    d.rounded_rectangle(box, r, fill=fill, outline=outline, width=width)

def frame(n):
    t = n / FPS
    img = BASE.copy()
    # chart layer (dimmed)
    chart = Image.new("RGB", (W, H), BG1); cd = ImageDraw.Draw(chart)
    draw_chart(cd, t, 1.0)
    dim = 0.55 if t < 3 else 0.18
    img = Image.blend(img, Image.composite(chart, img, chart.convert("L").point(lambda v: 255 if v > 30 else 0)), dim)
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(ov)

    # Scene 1: hook 0-3.2s
    if t < 3.4:
        a = ease(seg(t, 0, .5)) * (1 - seg(t, 3.0, 3.4))
        ctext(d, 640, "Nak mula trading", font("Bold", 92), WHITE, a, 40 * (1 - ease(seg(t, 0, .5))))
        a2 = ease(seg(t, .5, 1.0)) * (1 - seg(t, 3.0, 3.4))
        ctext(d, 760, "tapi tak tahu", font("Bold", 92), WHITE, a2)
        a3 = ease(seg(t, 1.0, 1.5)) * (1 - seg(t, 3.0, 3.4))
        ctext(d, 880, "mula dari mana?", font("ExtraBold", 104), GOLD, a3)
        a4 = ease(seg(t, 1.8, 2.3)) * (1 - seg(t, 3.0, 3.4))
        ctext(d, 1060, "Tonton sampai habis ↓", font("Medium", 52), MUTED, a4)

    # Scene 2: brand reveal 3.2-7.5s
    if 3.2 <= t < 7.8:
        a = ease(seg(t, 3.2, 3.9)) * (1 - seg(t, 7.3, 7.8))
        s = 0.8 + 0.2 * ease(seg(t, 3.2, 4.0))
        r = int(150 * s); cx, cy = W // 2, 700
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(0, 214, 143, int(255 * a)))
        # up arrow logo
        d.polygon([(cx, cy - r * .55), (cx + r * .5, cy + r * .05), (cx + r * .18, cy + r * .05),
                   (cx + r * .18, cy + r * .5), (cx - r * .18, cy + r * .5), (cx - r * .18, cy + r * .05),
                   (cx - r * .5, cy + r * .05)], fill=(6, 10, 24, int(255 * a)))
        ctext(d, 900, "TRAXA", font("Black", 170), WHITE, a)
        ctext(d, 1090, "TRADING APP", font("SemiBold", 64), GREEN, a)
        a2 = ease(seg(t, 4.4, 5.0)) * (1 - seg(t, 7.3, 7.8))
        ctext(d, 1220, "Trading terus dari telefon anda", font("Medium", 54), MUTED, a2)

    # Scene 3: features 7.5-13.5s
    if 7.5 <= t < 13.8:
        out = 1 - seg(t, 13.3, 13.8)
        ctext(d, 470, "Kenapa TRAXA?", font("ExtraBold", 96), WHITE, ease(seg(t, 7.5, 8.1)) * out)
        feats = [("1", "Daftar cepat & mudah"), ("2", "Pantau pasaran secara live"),
                 ("3", "Mesra pengguna baru"), ("4", "Akses di mana-mana")]
        for i, (num, txt) in enumerate(feats):
            st = 8.2 + i * 0.9; a = ease(seg(t, st, st + .5)) * out
            if a <= 0: continue
            x0 = 90 + int(120 * (1 - a)); y0 = 680 + i * 220
            pill(d, [x0, y0, x0 + 900, y0 + 170], (255, 255, 255, int(22 * a)), 36, (0, 214, 143, int(200 * a)), 3)
            d.ellipse([x0 + 35, y0 + 35, x0 + 135, y0 + 135], fill=(0, 214, 143, int(255 * a)))
            f = font("Black", 60); w = d.textlength(num, font=f)
            d.text((x0 + 85 - w / 2, y0 + 47), num, font=f, fill=(6, 10, 24, int(255 * a)))
            d.text((x0 + 170, y0 + 52), txt, font=font("SemiBold", 54), fill=(255, 255, 255, int(255 * a)))

    # Scene 4: CTA 13.5-20s
    if t >= 13.5:
        a = ease(seg(t, 13.5, 14.1))
        ctext(d, 440, "Daftar sekarang", font("ExtraBold", 100), WHITE, a)
        ctext(d, 570, "guna kod jemputan saya", font("Medium", 58), MUTED, a)
        a2 = ease(seg(t, 14.2, 14.8)); pulse = 1 + 0.03 * math.sin((t - 14.2) * 6) * a2
        bw, bh = int(760 * pulse), int(260 * pulse); cx, cy = W // 2, 840
        pill(d, [cx - bw // 2, cy - bh // 2, cx + bw // 2, cy + bh // 2], (255, 196, 61, int(255 * a2)), 50)
        f = font("Black", int(170 * pulse)); w = d.textlength(CODE, font=f)
        bb = d.textbbox((0, 0), CODE, font=f)
        d.text((cx - w / 2, cy - (bb[3] + bb[1]) / 2), CODE, font=f, fill=(6, 10, 24, int(255 * a2)))
        a3 = ease(seg(t, 15.2, 15.8))
        ctext(d, 1060, "Link pendaftaran:", font("Medium", 50), MUTED, a3)
        pill(d, [70, 1140, W - 70, 1260], (0, 214, 143, int(40 * a3)), 30, (0, 214, 143, int(255 * a3)), 3)
        ctext(d, 1170, LINK, font("Bold", 50), GREEN, a3)
        a4 = ease(seg(t, 16.3, 16.9))
        ctext(d, 1340, "Link ada di bio / pinned ↑", font("SemiBold", 54), WHITE, a4)

    # Persistent disclaimer
    ctext(d, 1760, "Trading melibatkan risiko. Hanya labur apa yang", font("Regular", 34), MUTED, 0.9)
    ctext(d, 1805, "anda sanggup rugi. Bukan nasihat kewangan.", font("Regular", 34), MUTED, 0.9)
    # progress bar
    d.rectangle([0, H - 12, int(W * t / DUR), H], fill=(0, 214, 143, 220))

    img = Image.alpha_composite(img.convert("RGBA"), ov).convert("RGB")
    img.save(os.path.join(FR, f"{n:05d}.jpg"), quality=92)

def music(path):
    sr = 44100; t = np.arange(int(sr * DUR)) / sr; bpm = 120; beat = 60 / bpm
    out = np.zeros_like(t)
    # kick on every beat
    for k in np.arange(0, DUR, beat):
        i = int(k * sr); L = int(.25 * sr); tt = np.arange(L) / sr
        seg_ = np.sin(2 * np.pi * (50 + 90 * np.exp(-tt * 30)) * tt) * np.exp(-tt * 12)
        out[i:i + L] += seg_[:len(out) - i] * .8
    # hi-hat offbeats
    rng = np.random.default_rng(1)
    for k in np.arange(beat / 2, DUR, beat):
        i = int(k * sr); L = int(.05 * sr)
        out[i:i + L] += (rng.standard_normal(L) * np.exp(-np.arange(L) / sr * 80))[:len(out) - i] * .12
    # chord pad (Am - F - C - G), 2s each
    chords = [[220, 261.6, 329.6], [174.6, 220, 261.6], [261.6, 329.6, 392], [196, 246.9, 293.7]]
    for ci, k in enumerate(np.arange(0, DUR, 2.0)):
        i = int(k * sr); L = int(2 * sr); tt = np.arange(L) / sr
        env = np.minimum(1, tt * 8) * np.minimum(1, (2 - tt) * 8)
        s = sum(np.sin(2 * np.pi * f * tt) + .3 * np.sin(4 * np.pi * f * tt) for f in chords[ci % 4]) * env * .07
        out[i:i + L] += s[:len(out) - i]
    fade = np.minimum(1, np.minimum(t / .5, (DUR - t) / 1.0)); out *= fade
    out = np.int16(out / np.abs(out).max() * 0.85 * 32767)
    with wave.open(path, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes(out.tobytes())

if __name__ == "__main__":
    for n in range(N): frame(n)
    wav = os.path.join(OUT, "music.wav"); music(wav)
    mp4 = os.path.join(OUT, "traxa_promo.mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", os.path.join(FR, "%05d.jpg"),
                    "-i", wav, "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20", "-preset", "medium",
                    "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", mp4], check=True)
    # thumbnail / cover
    Image.open(os.path.join(FR, f"{int(16*FPS):05d}.jpg")).save(os.path.join(OUT, "cover.jpg"), quality=92)
    print("done", mp4)
