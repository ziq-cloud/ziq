import asyncio, json, math, os, random, re, subprocess, sys, wave
from multiprocessing import Pool

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

import make as M
from make import (W, H, FPS, GOLD, GOLD2, RED, GREEN, AMBER, TEAL, WHITE, GREY, font, clamp, eo, eob, ap, sprite, comp,
                  text, text_w, wrap, para, rgba, rounded_mask, panel_frame, background, draw_candles, tri, warn_icon,
                  check_box, pill, flash, kicker, CH, M5_Y)

HERE = M.HERE
TTS_DIR = os.path.join(HERE, "tts_el")
EL_VOICE = "VbhRlZCHaUh9hxeUyRBD"  # Daud M - Deep & Confident Narrator (ElevenLabs)
VOICE = "ms-MY-OsmanNeural"

# ============================================================ narration spec
TF = lambda s: s
SPEC = [
    ("hook", False, 0.8, [("h1", "Gold junam lebih seribu seratus dolar dari puncak!"), ("h2", "Apa seterusnya?")]),
    ("intro", False, 0.6, [("i1", "Zik F X. Gold, XAU USD market outlook."), ("i2", "Isnin, 23 November 2026.")]),
    ("greet", True, 0.6, [("g1", "Assalamualaikum dan good morning, fighters!")]),
    ("context", True, 2.0, [("c1", "Gold memulakan minggu baharu dalam keadaan tekanan jualan yang masih kuat selepas kejatuhan besar minggu lalu.")]),
    ("mtf", True, 1.0, [("m1", "Berdasarkan struktur H4 dan H1, trend utama masih bearish,"),
                        ("m2", "manakala M15 dan M30 menunjukkan harga sedang cuba membuat pemulihan kecil berhampiran kawasan 3537."),
                        ("m3", "Buat masa ini, kenaikan harga masih belum cukup untuk mengesahkan reversal."),
                        ("m4", "Fokus kita adalah melihat reaksi harga di kawasan support dan resistance sebelum mencari peluang entry.")]),
    ("bias", True, 1.0, [("b1", "Bias utama: STRONG BEARISH."), ("b2", "Intraday: BEARISH ke NEUTRAL."),
                         ("b3", "Focus: SELL ON RALLY."), ("b4", "Last price: 3537.26.")]),
]

ZONES = {
    "z1": dict(num=1, kind="RESISTANCE", rng="3545–3560", lo=3545, hi=3560, col=RED, sec="SELL CONFIRMATION", down=True,
               bullets=["Tunggu harga retrace ke kawasan resistance.", "Cari bearish engulfing atau rejection pada M5/M15.",
                        "Tunggu bearish structure shift.", "Break swing low selepas rejection."], tg=[3530, 3516, 3506],
               path=[(3537, 0), (3546, .15), (3540, .25), (3557, .42), (3563, .48), (3549, .58), (3554, .64), (3530, .8), (3516, .9), (3506, 1)]),
    "z2": dict(num=2, kind="RESISTANCE", rng="3570–3590", lo=3570, hi=3590, col=RED, sec="SELL CONFIRMATION", down=True,
               bullets=["Harga membuat liquidity sweep di kawasan resistance.", "M5/M15 membentuk lower high.",
                        "Candle bearish close dan break struktur sokongan kecil.", "Retest gagal reclaim resistance."], tg=[3560, 3545, 3530],
               warn="Jika harga berjaya break dan bertahan di atas 3590, momentum bearish intraday perlu dinilai semula.",
               path=[(3537, 0), (3560, .2), (3552, .28), (3584, .45), (3595, .5), (3575, .6), (3582, .66), (3550, .82), (3530, 1)]),
    "z3a": dict(num=3, kind="SUPPORT", rng="3516–3506", lo=3506, hi=3516, col=GREEN, sec="BUY CONFIRMATION", down=False,
                bullets=["Harga membuat liquidity sweep di bawah support.", "Reclaim semula kawasan 3516–3520.",
                         "M5/M15 membentuk bullish engulfing atau bullish structure shift.", "Break swing high dan retest berjaya."],
                tg=[3540, 3555, 3570],
                path=[(3537, 0), (3522, .2), (3528, .28), (3509, .42), (3501, .48), (3518, .6), (3512, .66), (3540, .82), (3555, .92), (3570, 1)]),
    "z3b": dict(num=3, kind="SUPPORT", rng="3516–3506", lo=3506, hi=3516, col=RED, sec="SELL CONTINUATION", down=True,
                bullets=["M15 close kukuh di bawah 3506.", "Harga retest 3506–3516 dari bawah.", "Retest gagal reclaim.",
                         "Bearish confirmation muncul."], tg=[3490, 3475, 3450],
                path=[(3537, 0), (3518, .2), (3500, .38), (3494, .44), (3512, .58), (3503, .68), (3490, .8), (3475, .9), (3458, 1)]),
    "z4": dict(num=4, kind="SUPPORT", rng="3490–3475", lo=3475, hi=3490, col=GREEN, sec="BUY CONFIRMATION", down=False,
               bullets=["Tunggu rejection atau liquidity sweep yang jelas.", "Harga reclaim semula kawasan 3490.",
                        "M5/M15 menunjukkan bullish structure shift.", "Tunggu break swing high dan retest."], tg=[3506, 3516, 3540],
               warn="Jika harga terus jatuh dengan momentum kuat, jangan paksa BUY hanya kerana harga sudah berada di kawasan rendah.",
               path=[(3537, 0), (3515, .18), (3521, .25), (3492, .4), (3470, .48), (3488, .6), (3483, .66), (3506, .8), (3516, .9), (3540, 1)]),
}
NUMW = {1: "satu", 2: "dua", 3: "tiga", 4: "empat"}
for zk, z in ZONES.items():
    segs = []
    if zk == "z3b":
        segs.append(("hd", "Masih di zon tiga. Kalau support pecah:"))
    else:
        segs.append(("hd", f"Zon {NUMW[z['num']]}. {z['kind'].lower()} {z['rng']}."))
    segs.append(("sec", z["sec"].lower() + "."))
    for i, b in enumerate(z["bullets"]):
        segs.append((f"b{i}", b))
    segs.append(("tg", "Target: " + ", ".join(str(v) for v in z["tg"]) + "."))
    if z.get("warn"):
        segs.append(("w", z["warn"]))
    z["segs"] = segs

SPEC += [(zk, True, 0.8, ZONES[zk]["segs"]) for zk in ("z1", "z2", "z3a", "z3b", "z4")]
SPEC += [
    ("main", True, 1.0, [("s1", "Main market scenario."), ("s2", "Selagi harga berada di bawah resistance 3570–3590,"),
                         ("s3", "keutamaan masih kepada SELL ON RALLY."),
                         ("s4", "Struktur H4 dan H1 menunjukkan tekanan bearish yang dominan."),
                         ("s5", "Kenaikan kecil pada timeframe rendah perlu dianggap sebagai pullback, selagi belum berlaku perubahan struktur yang jelas.")]),
    ("two", True, 1.0, [("t0", "Dua senario utama."), ("t1", "Satu. SELL ON RALLY."),
                        ("t1a", "Harga retrace ke 3545–3560 atau 3570–3590,"), ("t1b", "bearish rejection,"), ("t1c", "break swing low."),
                        ("t2", "Dua. BUY REBOUND."), ("t2a", "Harga bertahan di 3516–3506,"), ("t2b", "liquidity sweep,"),
                        ("t2c", "bullish structure shift,"), ("t2d", "break swing high dan retest berjaya.")]),
    ("levels", True, 1.0, [("l0", "Key levels to watch."), ("lr1", "Resistance satu, 3545–3560."), ("lr2", "Resistance dua, 3570–3590."),
                           ("lmr", "Major resistance, 3590–3625."), ("ls1", "Support satu, 3516–3506."), ("ls2", "Support dua, 3490–3475."),
                           ("lms", "Major support, 3450–3400."),
                           ("lp1", "Kawasan 3500–3515 merupakan support psikologi dan teknikal penting."),
                           ("lp2", "Jika ditembusi dengan momentum kuat, kawasan 3390–3445 menjadi zon sokongan lebih jauh untuk diperhatikan.")]),
    ("check", True, 1.2, [("k0", "Entry confirmation checklist."), ("k1", "M5, entry trigger."), ("k2", "M15, confirmation struktur."),
                          ("k3", "M30, intraday momentum."), ("k4", "H1 dan H4, arah trend utama."),
                          ("k5", "Tunggu candle close, jangan bergantung pada wick sahaja."),
                          ("k6", "Tetapkan SL dan risk management sebelum entry."), ("k7", "Tiada confirmation? NO ENTRY!")]),
    ("fund", True, 1.0, [("f0", "Fundamental watch."), ("f1", "Pasaran masih memberi perhatian kepada kekuatan USD"),
                         ("f2", "dan jangkaan kadar faedah Federal Reserve."),
                         ("f3", "Minggu ini, data US GDP dan PCE pada 25 November berpotensi mencetuskan volatiliti besar pada gold.")]),
    ("outro", False, 3.0, [("o1", "Fighters, jangan terburu-buru mengejar candle."), ("o2", "Tunggu harga datang ke zone,"),
                           ("o3", "tunggu confirmation,"), ("o4", "kemudian baru rancang entry."), ("o5", "Zik F X. Trade safe, risk first.")]),
]

DIG = "kosong satu dua tiga empat lima enam tujuh lapan sembilan".split()
KEEP_CAPS = {"USD", "GDP", "PCE", "US", "XAU", "SL"}


def say(s):
    s = s.replace("H1/H4", "H1 dan H4").replace("M5/M15", "M5 dan M15").replace("&", " dan ")
    s = re.sub(r"(\d)\s*–\s*(\d)", r"\1 hingga \2", s)
    s = s.replace("→", " ke ")
    s = re.sub(r"\bSL\b", "stop loss", s)
    s = re.sub(r"\b([MH])(\d{1,2})\b", r"\1 \2", s)

    def price(m):
        out = " ".join(DIG[int(c)] for c in m.group(1))
        if m.group(2):
            out += " perpuluhan " + " ".join(DIG[int(c)] for c in m.group(2))
        return out

    s = re.sub(r"\b(3\d{3})(?:\.(\d+))?\b", price, s)
    s = re.sub(r"\b[A-Z]{2,}\b", lambda m: m.group(0) if m.group(0) in KEEP_CAPS else m.group(0).lower(), s)
    return s


LEAD, GAP = 0.45, 0.22


# ============================================================ TTS + timeline
def gen_tts():
    import certifi
    if os.path.exists("/root/.ccr/ca-bundle.crt"):  # Claude cloud session proxy CA
        certifi.where = lambda: "/root/.ccr/ca-bundle.crt"
    os.makedirs(TTS_DIR, exist_ok=True)
    jobs = []
    for name, _, _, segs in SPEC:
        for k, txt in segs:
            p = os.path.join(TTS_DIR, f"{name}_{k}.mp3")
            if not os.path.exists(p) or os.path.getsize(p) == 0:
                jobs.append((p, say(txt)))
    from concurrent.futures import ThreadPoolExecutor

    def el(job):
        p, txt = job
        body = json.dumps({"text": txt, "model_id": "eleven_multilingual_v2",
                           "voice_settings": {"stability": 0.45, "similarity_boost": 0.8, "style": 0.25}})
        for attempt in range(5):
            r = subprocess.run(["curl", "-s", "--max-time", "120", "-o", p, "-w", "%{http_code}",
                                f"https://api.elevenlabs.io/v1/text-to-speech/{EL_VOICE}?output_format=mp3_44100_128",
                                "-H", "xi-api-key: proxy-injected", "-H", "Content-Type: application/json", "-d", body],
                               capture_output=True, text=True)
            if r.stdout.strip() == "200":
                return
            print("retry", p, r.stdout, open(p, "rb").read(200) if os.path.exists(p) else b"", file=sys.stderr)
            import time
            time.sleep(3 * (attempt + 1))
        if os.path.exists(p):
            os.remove(p)
        raise RuntimeError(p)

    with ThreadPoolExecutor(4) as ex:
        list(ex.map(el, jobs))
    jobs = []
    sem = asyncio.Semaphore(4)

    async def one(p, txt):
        async with sem:
            for attempt in range(4):
                try:
                    import edge_tts
                    await edge_tts.Communicate(txt, VOICE, rate="+10%").save(p)
                    return
                except Exception as e:
                    print("retry", p, e, file=sys.stderr)
                    await asyncio.sleep(2 * (attempt + 1))
            raise RuntimeError(p)

    async def main():
        await asyncio.gather(*(one(p, t) for p, t in jobs))

    asyncio.run(main())
    # decode + trim silence -> wav
    tl, T = {}, 0.0
    for name, ch, tail, segs in SPEC:
        t = LEAD
        S = {}
        for k, _ in segs:
            mp3 = os.path.join(TTS_DIR, f"{name}_{k}.mp3")
            wav = mp3[:-4] + ".wav"
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", mp3, "-af",
                            "silenceremove=start_periods=1:start_threshold=-45dB,areverse,silenceremove=start_periods=1:start_threshold=-45dB,areverse",
                            "-ar", "44100", "-ac", "1", wav], check=True)
            with wave.open(wav) as w:
                d = w.getnframes() / w.getframerate()
            S[k] = [t, d]
            t += d + GAP
        D = t - GAP + tail
        tl[name] = {"S": S, "D": round(D * FPS) / FPS, "start": T, "chrome": ch}
        T += tl[name]["D"]
    json.dump(tl, open(os.path.join(HERE, "timeline.json"), "w"), indent=1)
    print("total", T)


TL = json.load(open(os.path.join(HERE, "timeline.json"))) if os.path.exists(os.path.join(HERE, "timeline.json")) else None
ORDER = [s[0] for s in SPEC]
TOTAL = sum(TL[n]["D"] for n in ORDER) if TL else 1
M.TOTAL = TOTAL
DROP = TL["greet"]["start"] if TL else 0
BEAT = 60 / 128


class Seg:
    def __init__(self, S):
        self.S = S

    def st(self, k):
        return self.S[k][0]

    def d(self, k):
        return self.S[k][1]

    def en(self, k):
        return self.S[k][0] + self.S[k][1]


# ============================================================ new effect helpers
def typed(base, s, x, y, maxw, t, st, dur, w="SemiBold", size=40, color=WHITE, lh=1.28, alpha=1.0, anchor="l", speed=0.85):
    """Typewriter paragraph: chars revealed in sync with narration."""
    if t < st:
        return len(wrap(s, w, size, maxw)) * size * lh
    lines = wrap(s, w, size, maxw)
    total = sum(len(l) for l in lines)
    n = int(total * clamp((t - st) / max(0.3, dur * speed)))
    a = alpha * clamp((t - st) / 0.15)
    shown = 0
    yy = y
    cur = None
    for ln in lines:
        k = clamp(n - shown, 0, len(ln))
        part = ln[: int(k)]
        if part:
            if anchor == "c":
                full_w = text_w(ln, w, size)
                text(base, part, x - full_w / 2, yy, w, size, color, "l", a)
                cx = x - full_w / 2 + text_w(part, w, size)
            else:
                text(base, part, x, yy, w, size, color, "l", a)
                cx = x + text_w(part, w, size)
            cur = (cx, yy)
        shown += len(ln)
        yy += size * lh
    if n < total and cur and int(t * 6) % 2 == 0:
        d = ImageDraw.Draw(base, "RGBA")
        d.rectangle((cur[0] + 6, cur[1], cur[0] + 6 + size * 0.45, cur[1] + size * 0.95), fill=rgba(GOLD, a))
    return len(lines) * size * lh


def sweep_text(base, s, x, y, w, size, color, anchor="c", alpha=1.0, glow=0, gcol=None, prog=-1, scale=1.0):
    text(base, s, x, y, w, size, color, anchor, alpha, glow, gcol, scale)
    if not (0 < prog < 1) or alpha <= 0.05:
        return
    im, pad = sprite(s, w, size, color)
    a = np.asarray(im.getchannel("A"), dtype=np.float32) / 255
    hh, ww = a.shape
    xx = np.arange(ww)[None, :] + np.arange(hh)[:, None] * 0.45
    c = -0.3 * ww + prog * 1.6 * ww
    band = np.clip(1 - np.abs(xx - c) / (ww * 0.09), 0, 1) ** 1.5
    m = Image.fromarray((a * band * 230 * alpha).astype(np.uint8))
    vw = im.width - 2 * pad
    px = x - im.width / 2 if anchor == "c" else (x - pad if anchor == "l" else x - vw - pad)
    base.paste((255, 255, 240), (int(px), int(y - pad)), m)


def bolt_points(x0, y0, x1, y1, seed, rough=0.35, depth=6):
    r = random.Random(seed)
    pts = [(x0, y0), (x1, y1)]
    disp = math.hypot(x1 - x0, y1 - y0) * rough
    for _ in range(depth):
        new = [pts[0]]
        for a, b in zip(pts, pts[1:]):
            mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
            dx, dy = b[0] - a[0], b[1] - a[1]
            L = math.hypot(dx, dy) or 1
            off = r.uniform(-disp, disp)
            new += [(mx - dy / L * off, my + dx / L * off), b]
        pts = new
        disp /= 2
    return pts


def lightning(base, t, start, x0, y0, x1, y1, col=(255, 90, 110), seed=1):
    k = t - start
    if not (0 <= k <= 0.45):
        return
    fl = 1.0 if int(k * 30) % 3 != 1 else 0.35
    a = (1 - k / 0.45) * fl
    seed2 = seed + int(k * 12)
    pts = bolt_points(x0, y0, x1, y1, seed2)
    minx, maxx = int(min(p[0] for p in pts)) - 60, int(max(p[0] for p in pts)) + 60
    miny, maxy = int(min(p[1] for p in pts)) - 60, int(max(p[1] for p in pts)) + 60
    minx, miny = max(0, minx), max(0, miny)
    maxx, maxy = min(W, maxx), min(H, maxy)
    lw, lh = maxx - minx, maxy - miny
    if lw <= 0 or lh <= 0:
        return
    layer = Image.new("RGBA", (lw, lh), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    rel = [(p[0] - minx, p[1] - miny) for p in pts]
    d.line(rel, fill=col + (255,), width=16)
    # branch
    r = random.Random(seed2 + 99)
    i = len(rel) // 3
    bx, by = rel[i]
    br = bolt_points(bx, by, bx + r.uniform(-260, 260), by + r.uniform(150, 320), seed2 + 5, depth=5)
    d.line(br, fill=col + (255,), width=8)
    glow = layer.filter(ImageFilter.GaussianBlur(14))
    d2 = ImageDraw.Draw(layer)
    d2.line(rel, fill=(255, 255, 255, 255), width=5)
    d2.line(br, fill=(255, 255, 255, 255), width=3)
    for L in (glow, glow, layer):
        al = L.getchannel("A").point(lambda v: int(v * a))
        base.paste(L.convert("RGB"), (minx, miny), al)
    flash(base, t, start, 0.12, col=(255, 230, 235), peak=0.5)


EMB = [(random.Random(i).uniform(0, W), random.Random(i * 7).uniform(0, 1), random.Random(i * 13).uniform(120, 380),
        random.Random(i * 3).uniform(2, 6), random.Random(i * 5).uniform(0, 6.28)) for i in range(90)]


def embers(base, t, inten=1.0, col_a=(255, 120, 30), col_b=(255, 60, 40)):
    if inten <= 0.02:
        return
    d = ImageDraw.Draw(base, "RGBA")
    for i, (x, ph0, sp, sz, ph) in enumerate(EMB):
        life = (ph0 + t * sp / H) % 1.0
        y = H - life * (H + 100)
        xx = x + 40 * math.sin(t * 1.3 + ph) + life * 60 * math.sin(ph)
        fl = 0.6 + 0.4 * math.sin(t * 15 + ph * 3)
        a = inten * fl * (1 - life) * min(1, life * 6)
        col = col_a if i % 2 else col_b
        d.ellipse((xx - sz * 2.6, y - sz * 2.6, xx + sz * 2.6, y + sz * 2.6), fill=rgba(col, 0.18 * a))
        d.ellipse((xx - sz, y - sz, xx + sz, y + sz), fill=rgba((255, 210, 120), 0.9 * a))


TICKER_TXT = "   R1 3545–3560   •   R2 3570–3590   •   MAJOR R 3590–3625   •   S1 3516–3506   •   S2 3490–3475   •   MAJOR S 3450–3400   •   BIAS: STRONG BEARISH   •   SELL ON RALLY   •   NO CONFIRMATION = NO ENTRY   •"
_tick = None


def ticker(base, T):
    global _tick
    if _tick is None:
        im, pad = sprite(TICKER_TXT, "Bold", 28, WHITE)
        _tick = im
    d = ImageDraw.Draw(base, "RGBA")
    y0 = 1840
    d.rectangle((0, y0, W, H - 8), fill=(8, 9, 14, 235))
    d.line((0, y0, W, y0), fill=rgba(GOLD, 0.7), width=2)
    d.rectangle((0, y0 + 2, 150, H - 8), fill=rgba(GOLD, 1))
    text(base, "LEVELS", 75, y0 + 22, "Black", 26, (12, 10, 6), "c")
    tw = _tick.width
    off = (T * 110) % tw
    x = 150 - off
    strip = Image.new("RGB", (W - 150, H - 8 - y0 - 2), (8, 9, 14))
    while x < W:
        strip.paste(_tick, (int(x - 150), 14), _tick)
        x += tw
    base.paste(strip, (150, y0 + 2))


def chrome2(base, T):
    M.chrome(base, T)
    ticker(base, T)


# ---------------- post FX
def post(img, T, t, D, glitch=0.0):
    # beat zoom punch
    if False:  # beat zoom-punch disabled (caused dizziness)
        db = (T - DROP) % BEAT
        s = 1 + 0.014 * math.exp(-db * 9)
        if s > 1.0015:
            cw, ch = W / s, H / s
            img = img.crop(((W - cw) / 2, (H - ch) / 2, (W + cw) / 2, (H + ch) / 2)).resize((W, H), Image.BILINEAR)
    g = glitch
    if t < 0.15:
        g = max(g, 0.45 * (1 - t / 0.15))
    if g > 0.02:
        a = np.asarray(img).copy()
        r = random.Random(int(T * FPS))
        dx = int(18 * g) + 2
        a[..., 0] = np.roll(a[..., 0], dx, axis=1)
        a[..., 2] = np.roll(a[..., 2], -dx, axis=1)
        for _ in range(int(10 * g)):
            y = r.randrange(0, H - 80)
            h = r.randrange(8, 70)
            a[y:y + h] = np.roll(a[y:y + h], r.randint(-60, 60) * (1 if g > 0.3 else 0) + r.randint(-20, 20), axis=1)
        if g > 0.5:
            a[::4] = (a[::4] * 0.75).astype(np.uint8)
        img = Image.fromarray(a)
    return img


# ============================================================ scenes
def out_of(t, D, f=0.3):
    return 1 - clamp((t - (D - f)) / f)


def sc_hook(base, t, D, S):
    out = out_of(t, D)
    c = CH["h4"]
    z = 1.15 + 0.25 * eo(t / D)
    cw, chh = c.width / z, c.height / z
    cx0, cy0 = (c.width - cw) * 0.98, (c.height - chh) * 0.9
    crop = c.crop((int(cx0), int(cy0), int(cx0 + cw), int(cy0 + chh)))
    hh = H
    ww = int(crop.width * hh / crop.height)
    big = crop.resize((ww, hh), Image.BILINEAR)
    big = big.crop(((ww - W) // 2 + 300, 0, (ww - W) // 2 + 300 + W, H))
    base.paste(Image.blend(Image.new("RGB", (W, H), (40, 0, 6)), big, 0.55), (0, 0))
    embers(base, t, 0.9 * out, (255, 60, 40), (255, 140, 40))
    s1 = S.st("h1")
    k = clamp((t - s1) / 0.35)
    sh = math.sin(t * 110) * 14 * clamp((s1 + 0.4 - t) / 0.4) if t > s1 else 0
    text(base, "GOLD JUNAM", W / 2 + sh, 470, "Black", 150, RED, "c", k * out, 18, (200, 0, 20), 1 + 0.6 * (1 - eob(k)))
    k2 = clamp((t - s1 - 0.7) / 0.35)
    sweep_text(base, "$1,100+", W / 2, 680, "Black", 260, WHITE, "c", k2 * out, 22, (255, 60, 60), prog=(t - s1 - 1.2) / 0.8,
               scale=1 + 0.5 * (1 - eob(k2)))
    k3 = ap(t, s1 + 1.4, 0.4)
    text(base, "DARI PUNCAK OGOS", W / 2, 1010 + 30 * (1 - k3), "ExtraBold", 64, GOLD, "c", k3 * out)
    s2 = S.st("h2")
    k4 = clamp((t - s2) / 0.3)
    pill(base, W / 2, 1250, "APA SETERUSNYA?", GOLD, 84, k4 * out, (12, 10, 6), "c", 50, 26, "Black")
    lightning(base, t, s1, 300, 0, 620, 900, seed=3)
    lightning(base, t, s2, 900, 0, 760, 1250, col=(255, 200, 90), seed=9)


def sc_intro(base, t, D, S):
    out = out_of(t, D)
    draw_candles(base, t, out)
    k = clamp((t - 0.15) / 0.55)
    s = 1.0 + 0.7 * (1 - eob(k))
    sweep_text(base, "ZIQFX", W / 2, 640, "Black", 230, GOLD, "c", k * out, 22, (255, 170, 0), prog=(t - 0.9) / 0.9, scale=s)
    d = ImageDraw.Draw(base, "RGBA")
    lw = 760 * ap(t, 0.8, 0.6)
    d.rectangle((W / 2 - lw / 2, 880, W / 2 + lw / 2, 886), fill=rgba(GOLD, out))
    a2 = ap(t, 1.0, 0.5)
    text(base, "XAUUSD", W / 2, 930 + 40 * (1 - a2), "Black", 130, WHITE, "c", a2 * out)
    a3 = ap(t, 1.35, 0.5)
    text(base, "MARKET  OUTLOOK", W / 2, 1100 + 40 * (1 - a3), "ExtraBold", 72, GOLD, "c", a3 * out, glow=10, gcol=(200, 120, 0))
    a4 = ap(t, S.st("i2"), 0.5)
    pill(base, W / 2, 1250, "ISNIN  •  23 NOVEMBER 2026", RED, 40, a4 * out, WHITE, "c")
    a5 = ap(t, S.st("i2") + 0.5, 0.5)
    text(base, "GOLD (XAU) vs US DOLLAR", W / 2, 1380, "SemiBold", 34, GREY, "c", a5 * out)
    # crossed swords flash
    sw = ap(t, 0.15, 0.35)
    if sw > 0:
        for sgn in (-1, 1):
            cx, cy = W / 2, 330
            L = 170 * sw
            ang = math.radians(45 * sgn)
            x0, y0 = cx - math.sin(ang) * L, cy + math.cos(ang) * L
            x1, y1 = cx + math.sin(ang) * L, cy - math.cos(ang) * L
            d.line((x0, y0, x1, y1), fill=rgba((230, 230, 240), out), width=10)
            d.line((x0 - 24 * math.cos(ang), y0 - 24 * math.sin(ang) - 0, x0 + 24 * math.cos(ang), y0 + 24 * math.sin(ang)), fill=rgba(GOLD, out), width=12)
    flash(base, t, 0.15, 0.35, peak=0.7)


def sc_greet(base, t, D, S):
    out = out_of(t, D)
    embers(base, t, out)
    a1 = ap(t, 0.1)
    text(base, "Assalamualaikum", W / 2, 640 + 40 * (1 - a1), "ExtraBold", 92, WHITE, "c", a1 * out)
    a2 = ap(t, 0.5)
    text(base, "& good morning,", W / 2, 780 + 40 * (1 - a2), "SemiBold", 70, GREY, "c", a2 * out)
    tf = max(1.0, S.en("g1") - 1.0)
    k = clamp((t - tf) / 0.4)
    sh = math.sin(t * 90) * 14 * clamp((tf + 0.5 - t) / 0.5) if t > tf else 0
    sweep_text(base, "FIGHTERS!", W / 2 + sh, 990, "Black", 190, GOLD, "c", k * out, 24, (255, 150, 0),
               prog=(t - tf - 0.5) / 0.8, scale=1 + 0.6 * (1 - eob(k)))
    a4 = ap(t, tf + 0.5)
    pill(base, W / 2, 1260, "MINGGU BAHARU  •  OUTLOOK GOLD", (40, 42, 56), 34, a4 * out, GOLD, "c")
    flash(base, t, tf, 0.25, col=(255, 200, 80), peak=0.45)


def live_candle(base, x, y_of, t, a=1.0, w=14):
    d = ImageDraw.Draw(base, "RGBA")
    o = 3533.5
    c = 3537.26 + 2.6 * math.sin(t * 3.1) + 1.3 * math.sin(t * 7.7)
    hi, lo = max(o, c) + 2.2, min(o, c) - 1.5
    col = GREEN if c >= o else RED
    d.line((x, y_of(hi), x, y_of(lo)), fill=rgba(col, a), width=3)
    d.rectangle((x - w / 2, y_of(max(o, c)), x + w / 2, y_of(min(o, c)) + 2), fill=rgba(col, a))
    return c


def sc_context(base, t, D, S):
    out = out_of(t, D)
    kicker(base, t, "MARKET CONTEXT", a=out)
    a = ap(t, 0.2, 0.6)
    text(base, "TEKANAN JUALAN", 60, 220 + 30 * (1 - a), "Black", 92, RED, alpha=a * out, glow=12, gcol=(180, 0, 20))
    text(base, "MASIH KUAT", 60, 330 + 30 * (1 - a), "Black", 92, WHITE, alpha=a * out)
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
    typed(base, "Gold memulakan minggu baharu dalam keadaan tekanan jualan yang masih kuat selepas kejatuhan besar minggu lalu.",
          60, 1060, 960, t, S.st("c1"), S.d("c1"), "SemiBold", 44, WHITE, 1.32, out)
    st = S.en("c1") - 0.6
    c2 = ap(t, st, 0.6)
    d = ImageDraw.Draw(base, "RGBA")
    d.rounded_rectangle((60, 1380, 1020, 1640), 26, fill=(255, 255, 255, int(14 * c2 * out)), outline=rgba(TEAL, c2 * out), width=3)
    text(base, "LAST PRICE", 100, 1420, "Bold", 34, GREY, alpha=c2 * out)
    val = 3700 - (3700 - 3537.26) * eo((t - st) / 1.4)
    sweep_text(base, f"{val:,.2f}", 100, 1480, "Black", 110, (90, 230, 210), "l", c2 * out, 10, (0, 140, 130), prog=(t - st - 1.5) / 0.8)
    tri(d, 930, 1510, 46, RED, True, c2 * out)


def sc_mtf(base, t, D, S):
    out = out_of(t, D)
    kicker(base, t, "STRUKTUR MULTI-TIMEFRAME", a=out)
    items = [("h4", "H4", "BEARISH", RED, "m1"), ("h1", "H1", "BEARISH", RED, "m1"),
             ("m30", "M30", "PEMULIHAN KECIL", AMBER, "m2"), ("m15", "M15", "PEMULIHAN KECIL", AMBER, "m2")]
    tw = 468
    for i, (k, lbl, tag, col, sk) in enumerate(items):
        a = ap(t, S.st(sk) + (i % 2) * 0.3, 0.5)
        x = 60 + (i % 2) * (tw + 24)
        y = 220 + (i // 2) * 300 + 40 * (1 - a)
        im = M.chart_panel(k, tw)
        comp(base, im, x, y, a * out)
        panel_frame(base, x, y, tw, im.height, col, a * out)
        pill(base, x + 14, y + 14, lbl, GOLD, 26, a * out, padx=16, pady=8)
        d = ImageDraw.Draw(base, "RGBA")
        bw = text_w(tag, "ExtraBold", 26) + 30
        d.rounded_rectangle((x + tw - bw - 14, y + im.height - 60, x + tw - 14, y + im.height - 14), 12, fill=rgba(col, a * out))
        text(base, tag, x + tw - bw / 2 - 14, y + im.height - 50, "ExtraBold", 26, (12, 10, 10), "c", a * out)
    d = ImageDraw.Draw(base, "RGBA")
    a = ap(t, S.st("m1"), 0.5)
    y0 = 800
    d.rounded_rectangle((60, y0, 1020, y0 + 230), 26, fill=(255, 59, 78, int(28 * a * out)), outline=rgba(RED, a * out), width=3)
    text(base, "H4 + H1", 100, y0 + 30, "Black", 56, RED, alpha=a * out)
    typed(base, "Trend utama masih BEARISH.", 100, y0 + 120, 880, t, S.st("m1"), S.d("m1"), "SemiBold", 44, WHITE, alpha=out)
    a = ap(t, S.st("m2"), 0.5)
    y1 = 1060
    d.rounded_rectangle((60, y1, 1020, y1 + 290), 26, fill=(255, 170, 40, int(24 * a * out)), outline=rgba(AMBER, a * out), width=3)
    text(base, "M30 + M15", 100, y1 + 30, "Black", 56, AMBER, alpha=a * out)
    typed(base, "Harga sedang cuba membuat pemulihan kecil berhampiran kawasan 3537.", 100, y1 + 120, 880, t, S.st("m2"), S.d("m2"),
          "SemiBold", 42, WHITE, alpha=out)
    h = typed(base, "Kenaikan harga masih BELUM CUKUP untuk mengesahkan reversal.", 70, 1390, 940, t, S.st("m3"), S.d("m3"),
              "Bold", 40, GOLD2, alpha=out)
    typed(base, "Fokus: reaksi harga di kawasan support & resistance sebelum mencari peluang entry.", 70, 1400 + h + 10, 940, t,
          S.st("m4"), S.d("m4"), "SemiBold", 38, WHITE, alpha=out)


def sc_bias(base, t, D, S):
    out = out_of(t, D)
    kicker(base, t, "MARKET BIAS", a=out)
    rows = [("BIAS UTAMA", "STRONG BEARISH", RED, "down", "b1"), ("INTRADAY", "BEARISH → NEUTRAL", AMBER, None, "b2"),
            ("FOCUS", "SELL ON RALLY", GOLD, None, "b3"), ("LAST PRICE", None, TEAL, None, "b4")]
    shake = 0
    for i, (lab, val, col, ic, sk) in enumerate(rows):
        st = S.st(sk)
        k = clamp((t - st) / 0.4)
        if k <= 0:
            continue
        if st < t < st + 0.3:
            shake = math.sin(t * 100) * 8 * (st + 0.3 - t) / 0.3
        x = 60 + (1 - eob(k)) * (-1100 if i % 2 == 0 else 1100)
        y = 240 + i * 380
        d = ImageDraw.Draw(base, "RGBA")
        d.rounded_rectangle((x, y, x + 960, y + 320), 30, fill=(14, 15, 22, int(235 * out)), outline=rgba(col, out), width=4)
        d.rectangle((x, y + 30, x + 12, y + 290), fill=rgba(col, out))
        text(base, lab, x + 60, y + 48, "Bold", 38, GREY, alpha=out)
        if val:
            size = 96 if len(val) < 15 else 80
            sweep_text(base, val, x + 60 + shake, y + 140, "Black", size, col, "l", out, 12, tuple(int(c * 0.6) for c in col),
                       prog=(t - st - 0.5) / 0.7)
        else:
            v = 3400 + 137.26 * eo((t - st) / 1.2)
            sweep_text(base, f"{v:,.2f}", x + 60, y + 130, "Black", 120, (90, 230, 210), "l", out, 12, (0, 140, 130), prog=(t - st - 1.3) / 0.7)
        if ic == "down":
            tri(d, x + 880, y + 80, 34, RED, True, out)
    embers(base, t, 0.6 * out * clamp((t - S.st("b1")) / 0.5))
    lightning(base, t, S.st("b1"), 820, 0, 560, 560, seed=21)


ZY0 = 300  # crop top in 2000-space for zone chart
ZPAD = 110


def zone_chart_img():
    c = CH["m5"]
    im = Image.new("RGB", (c.width, c.height - ZY0 + ZPAD), (0, 0, 0))
    im.paste(c.crop((0, ZY0, c.width, c.height)), (0, 0))
    return im


ZCH = zone_chart_img()
_zpanel = {}


def zone_panel(w):
    if w not in _zpanel:
        h = int(ZCH.height * w / ZCH.width)
        im = ZCH.resize((w, h), Image.LANCZOS).convert("RGBA")
        im.putalpha(rounded_mask(w, h, 22))
        _zpanel[w] = im
    return _zpanel[w]


def chart_zone(base, t, z, S, y0):
    w = 960
    im = zone_panel(w)
    sc = w / ZCH.width
    a = ap(t, 0.1, 0.5)
    yy = y0 + 30 * (1 - a)
    comp(base, im, 60, yy, a)
    Y = lambda p: yy + (M5_Y(p) - ZY0) * sc
    X = lambda f: 60 + f * (1745 - 130) * sc
    d = ImageDraw.Draw(base, "RGBA")
    col = z["col"]
    k = ap(t, 0.5, 0.7)
    xr = X(1.0)
    xl = xr - (xr - 60) * k
    pulse = 0.5 + 0.5 * math.sin(t * 6)
    ya, yb = Y(z["hi"]), Y(z["lo"])
    d.rectangle((xl, ya, xr, yb), fill=rgba(col, (0.22 + 0.12 * pulse) * k), outline=rgba(col, k), width=3)
    if k > 0.3:
        ly = ya - 40 if ya - 40 > yy + 60 else yb + 8
        text(base, z["rng"], 90, ly, "ExtraBold", 28, col, alpha=k)
    # projection region
    st, en = S.st("b0"), S.en("b3")
    pk = ap(t, st - 0.3, 0.4)
    fx0, fx1 = 0.45, 0.93
    if pk > 0:
        d.rectangle((X(fx0), yy + 2, X(fx1), yy + im.height - 2), fill=(0, 0, 0, int(165 * pk)))
        for gy in range(int(yy) + 8, int(yy + im.height), 22):
            d.line((X(fx0), gy, X(fx0), gy + 10), fill=rgba(GOLD, 0.6 * pk), width=2)
        text(base, "SENARIO", X(fx0) + 14, yy + 14, "Black", 24, GOLD, alpha=pk)
        prog = clamp((t - st) / max(0.5, en - st - 0.3))
        pts = [(X(fx0 + 0.03 + f * (fx1 - fx0 - 0.06)), Y(p)) for p, f in z["path"]]
        # cumulative length
        segl = [math.hypot(b[0] - a_[0], b[1] - a_[1]) for a_, b in zip(pts, pts[1:])]
        tot = sum(segl)
        target = tot * prog
        drawn = [pts[0]]
        acc = 0
        for (a_, b), L in zip(zip(pts, pts[1:]), segl):
            if acc + L <= target:
                drawn.append(b)
                acc += L
            else:
                f = (target - acc) / L if L else 0
                drawn.append((a_[0] + (b[0] - a_[0]) * f, a_[1] + (b[1] - a_[1]) * f))
                break
        if len(drawn) > 1:
            d.line(drawn, fill=rgba(WHITE, 0.25 * pk), width=14, joint="curve")
            d.line(drawn, fill=rgba(WHITE, pk), width=5, joint="curve")
            hx, hy = drawn[-1]
            d.ellipse((hx - 11, hy - 11, hx + 11, hy + 11), fill=rgba(GOLD, pk), outline=(255, 255, 255, int(255 * pk)), width=3)
            # mark sweep point
            sw_i = max(range(len(z["path"])), key=lambda i: z["path"][i][0]) if z["down"] else min(range(len(z["path"])), key=lambda i: z["path"][i][0])
            if z["kind"] == "SUPPORT" and z["down"]:
                sw_i = 4
            if len(drawn) - 1 > sw_i:
                sx, sy = pts[sw_i]
                rr = 18 + 6 * pulse
                d.ellipse((sx - rr, sy - rr, sx + rr, sy + rr), outline=rgba(AMBER, pk), width=4)
                lab = "RETEST" if (z["kind"] == "SUPPORT" and z["down"]) else "SWEEP"
                ly = sy - 62 if z["down"] else sy + 28
                text(base, lab, sx, ly, "Black", 24, AMBER, "c", pk)
            if prog >= 1:
                ex, ey = pts[-1]
                tri(d, ex, ey + (14 if z["down"] else -14), 18, col, z["down"], pk)
    # live candle at far right
    lx = X(0.978)
    c = live_candle(base, lx, Y, t, a)
    py = Y(c)
    for xx in range(60, int(X(1.0)), 22):
        d.line((xx, py, xx + 10, py), fill=rgba((90, 230, 210), 0.7 * a), width=2)
    d.rounded_rectangle((X(1.0) + 2, py - 16, 60 + w - 4, py + 16), 6, fill=rgba(TEAL, a))
    text(base, f"{c:.2f}", (X(1.0) + 60 + w) / 2, py - 10, "Bold", 18, WHITE, "c", a)
    panel_frame(base, 60, yy, w, im.height, col, a)
    pill(base, 84, yy + 16, "M5", GOLD, 26, a, padx=16, pady=8)
    return yy + im.height


def make_zone(zk):
    z = ZONES[zk]

    def sc(base, t, D, S):
        S = S
        out = out_of(t, D)
        col = z["col"]
        a = ap(t, 0.0, 0.4)
        pill(base, 60, 136, f"ZONE {z['num']}", col, 36, a, (10, 10, 14) if col != RED else WHITE)
        text(base, z["kind"] + (" • BREAKDOWN" if zk == "z3b" else ""), 290, 146, "ExtraBold", 40, col, alpha=a)
        k = clamp(t / 0.5)
        sweep_text(base, z["rng"], 60, 215, "Black", 120, WHITE, "l", k, 14, tuple(int(c * 0.7) for c in col),
                   prog=(t - 0.7) / 0.8, scale=1 + 0.3 * (1 - eob(k)))
        bottom = chart_zone(base, t, z, S, 360)
        y = bottom + 34
        sa = ap(t, S.st("sec"), 0.4)
        d = ImageDraw.Draw(base, "RGBA")
        tri(d, 96, y + 26, 22, col, z["down"], sa)
        text(base, z["sec"], 136, y + 4, "Black", 46, col, alpha=sa)
        y += 82
        for i, b in enumerate(z["bullets"]):
            st = S.st(f"b{i}")
            ba = ap(t, st, 0.3)
            xo = 30 * (1 - ba)
            d.ellipse((70 + xo, y + 2, 118 + xo, y + 50), fill=rgba(col, ba))
            text(base, str(i + 1), 94 + xo, y + 12, "Black", 28, (10, 10, 14), "c", ba)
            h = typed(base, b, 144, y + 2, 870, t, st, S.d(f"b{i}"), "SemiBold", 42, WHITE, 1.25, 1.0)
            y += max(h, 56) + 18
        tst, tdur = S.st("tg"), S.d("tg")
        ta = ap(t, tst, 0.4)
        y += 6
        text(base, "TARGET", 70, y, "ExtraBold", 32, col, alpha=ta)
        y += 52
        cw, gap = 250, 70
        x = 70
        for i, v in enumerate(z["tg"]):
            ct = tst + 0.35 + i * (tdur - 0.35) / 3
            kk = clamp((t - ct) / 0.3)
            if kk > 0:
                s = 1 + 0.35 * (1 - eob(kk))
                bw, bh = cw * s, 104 * s
                bx, by = x + cw / 2 - bw / 2, y + 52 - bh / 2
                d.rounded_rectangle((bx, by, bx + bw, by + bh), 22, fill=rgba(col, 0.16 * kk + 0.5 * max(0, 1 - (t - ct) / 0.5)),
                                    outline=rgba(col, kk), width=4)
                text(base, f"TP{i + 1}", x + 22, y + 14, "Bold", 22, GREY, alpha=kk)
                text(base, str(v), x + cw / 2 + 14, y + 36, "Black", 56, WHITE, "c", kk)
            if i < len(z["tg"]) - 1:
                text(base, "→", x + cw + gap / 2, y + 30, "Black", 50, col, "c", clamp((t - ct - 0.2) / 0.3))
            x += cw + gap
        y += 104
        if z.get("warn"):
            ws = S.st("w")
            wa = ap(t, ws, 0.3)
            yy = y + 26
            lines = wrap(z["warn"], "SemiBold", 32, 800)
            hh = len(lines) * 42 + 40
            blink = 0.6 + 0.4 * (1 if int((t - ws) * 4) % 2 == 0 else 0) if t - ws < 1.5 else 1
            d.rounded_rectangle((60, yy, 1020, yy + hh), 22, fill=(255, 170, 40, int(30 * wa)), outline=rgba(AMBER, wa * blink), width=4)
            warn_icon(base, 112, yy + hh / 2, 30, wa * blink)
            typed(base, z["warn"], 170, yy + 20, 800, t, ws, S.d("w"), "SemiBold", 32, WHITE, 1.3, 1.0)
        if out < 1:
            base.paste((7, 8, 14), (0, 0, W, H), Image.new("L", (W, H), int(255 * (1 - out))))
        flash(base, t, 0.0, 0.2, col=col, peak=0.35)

    return sc


def sc_main(base, t, D, S):
    out = out_of(t, D)
    kicker(base, t, "MAIN MARKET SCENARIO", a=out)
    s2 = S.st("s2")
    a = ap(t, s2)
    text(base, "Selagi harga di bawah", W / 2, 300 + 30 * (1 - a), "Bold", 54, GREY, "c", a * out)
    k = clamp((t - s2 - 1.2) / 0.45)
    sweep_text(base, "3570–3590", W / 2, 400, "Black", 150, WHITE, "c", k * out, 16, (180, 0, 30), prog=(t - s2 - 1.8) / 0.8,
               scale=1 + 0.4 * (1 - eob(k)))
    s3 = S.st("s3")
    a = ap(t, s3)
    text(base, "keutamaan masih kepada", W / 2, 620 + 30 * (1 - a), "Bold", 54, GREY, "c", a * out)
    hit = s3 + 0.9
    k = clamp((t - hit) / 0.45)
    sh = math.sin(t * 100) * 10 * clamp((hit + 0.4 - t) / 0.4) if t > hit else 0
    sweep_text(base, "SELL ON RALLY", W / 2 + sh, 730, "Black", 128, RED, "c", k * out, 22, (220, 0, 30), prog=(t - hit - 0.6) / 0.8,
               scale=1 + 0.5 * (1 - eob(k)))
    embers(base, t, out * clamp((t - hit) / 0.6))
    lightning(base, t, hit, 140, 560, 380, 980, seed=33)
    a = ap(t, S.st("s4"), 0.5)
    d = ImageDraw.Draw(base, "RGBA")
    d.rounded_rectangle((60, 960, 1020, 1640), 28, fill=(14, 15, 22, int(225 * a * out)), outline=rgba(GOLD, 0.6 * a * out), width=3)
    h = typed(base, "Struktur H4 dan H1 menunjukkan tekanan bearish yang dominan.", 110, 1010, 860, t, S.st("s4"), S.d("s4"),
              "Bold", 44, WHITE, 1.3, out)
    typed(base, "Kenaikan kecil pada timeframe rendah perlu dianggap sebagai PULLBACK selagi belum berlaku perubahan struktur yang jelas.",
          110, 1010 + h + 40, 860, t, S.st("s5"), S.d("s5"), "SemiBold", 42, GOLD2, 1.3, out)


def sc_two(base, t, D, S):
    out = out_of(t, D)
    kicker(base, t, "DUA SENARIO UTAMA", a=out)
    cards = [(1, "SELL ON RALLY", RED, True, "t1", [("t1a", "Retrace ke 3545–3560 / 3570–3590"), ("t1b", "Bearish rejection"), ("t1c", "Break swing low")]),
             (2, "BUY REBOUND", GREEN, False, "t2", [("t2a", "Bertahan di 3516–3506"), ("t2b", "Liquidity sweep"),
                                                     ("t2c", "Bullish structure shift"), ("t2d", "Break swing high + retest berjaya")])]
    y = 240
    for ci, (n, title, col, down, sk, steps) in enumerate(cards):
        st = S.st(sk)
        a = ap(t, st, 0.5)
        hgt = 160 + len(steps) * 96
        d = ImageDraw.Draw(base, "RGBA")
        x = 60 + (1 - a) * (-200 if ci == 0 else 200)
        d.rounded_rectangle((x, y, x + 960, y + hgt), 30, fill=(14, 15, 22, int(235 * a * out)), outline=rgba(col, a * out), width=4)
        d.ellipse((x + 40, y + 36, x + 120, y + 116), fill=rgba(col, a * out))
        text(base, str(n), x + 80, y + 50, "Black", 52, (10, 10, 14) if col == GREEN else WHITE, "c", a * out)
        sweep_text(base, title, x + 150, y + 44, "Black", 66, col, "l", a * out, prog=(t - st - 0.4) / 0.7)
        tri(d, x + 900, y + 76, 26, col, down, a * out)
        sy = y + 160
        for i, (kk, s) in enumerate(steps):
            k = ap(t, S.st(kk), 0.3) * out
            if i > 0:
                d.line((x + 80, sy - 60, x + 80, sy - 6), fill=rgba(col, k), width=4)
            d.ellipse((x + 64, sy + 6, x + 96, sy + 38), outline=rgba(col, k), width=4, fill=rgba(col, 0.5 * k))
            typed(base, s, x + 130, sy + 2, 820, t, S.st(kk), S.d(kk), "Bold", 40, WHITE, 1.2, out)
            sy += 96
        y += hgt + 50


def sc_levels(base, t, D, S):
    out = out_of(t, D)
    kicker(base, t, "KEY LEVELS TO WATCH", a=out)
    top, bot = 3640, 3370
    y0, y1 = 250, 1380
    Y = lambda p: y0 + (top - p) / (top - bot) * (y1 - y0)
    d = ImageDraw.Draw(base, "RGBA")
    a = ap(t, 0.2, 0.5) * out
    d.line((200, y0, 200, y1), fill=rgba(GREY, a), width=3)
    for p in range(3375, 3641, 25):
        d.line((190, Y(p), 210, Y(p)), fill=rgba(GREY, a), width=2)
        if p % 50 == 0:
            text(base, str(p), 176, Y(p) - 14, "SemiBold", 26, GREY, "r", a)
    zones = [(3590, 3625, (170, 20, 40), "MAJOR RESISTANCE", "3590–3625", "lmr"),
             (3570, 3590, RED, "RESISTANCE 2", "3570–3590", "lr2"),
             (3545, 3560, (255, 110, 120), "RESISTANCE 1", "3545–3560", "lr1"),
             (3506, 3516, (110, 240, 180), "SUPPORT 1", "3516–3506", "ls1"),
             (3475, 3490, GREEN, "SUPPORT 2", "3490–3475", "ls2"),
             (3400, 3450, (10, 140, 90), "MAJOR SUPPORT", "3450–3400", "lms")]
    for (lo, hi, col, lab, rg, sk) in zones:
        st = S.st(sk)
        k = ap(t, st, 0.5)
        hl = max(0, 1 - (t - st) / 1.2) if t > st else 0
        xr = 230 + 790 * k
        d.rectangle((230, Y(hi), xr, Y(lo)), fill=rgba(col, (0.32 + 0.4 * hl) * k * out), outline=rgba(col, k * out), width=3)
        cy = (Y(hi) + Y(lo)) / 2
        text(base, lab, 260, cy - 32, "ExtraBold", 28, col, alpha=k * out)
        sweep_text(base, rg, 1000, cy - 30, "Black", 46, WHITE, "r", k * out, prog=(t - st - 0.3) / 0.6)
    k = ap(t, S.st("l0"), 0.5) * out
    yl = Y(3537.26)
    pulse = 0.5 + 0.5 * math.sin(t * 7)
    for xx in range(210, 1020, 24):
        d.line((xx, yl, xx + 12, yl), fill=rgba((90, 230, 210), k), width=4)
    d.rounded_rectangle((640, yl - 26, 1020, yl + 26), 12, fill=rgba(TEAL, k * (0.7 + 0.3 * pulse)))
    text(base, "NOW 3537.26", 830, yl - 16, "Black", 32, WHITE, "c", k)
    a = ap(t, S.st("lp1"), 0.5) * out
    d.rounded_rectangle((60, 1420, 1020, 1815), 26, fill=(255, 170, 40, int(26 * a)), outline=rgba(AMBER, a), width=3)
    warn_icon(base, 116, 1474, 28, a)
    text(base, "3500–3515", 170, 1452, "Black", 48, AMBER, alpha=a)
    h = typed(base, "Support psikologi & teknikal penting.", 100, 1530, 880, t, S.st("lp1"), S.d("lp1"), "Bold", 36, WHITE, 1.3, out)
    typed(base, "Jika ditembusi dengan momentum kuat, kawasan 3390–3445 menjadi zon sokongan lebih jauh untuk diperhatikan.",
          100, 1530 + h + 10, 880, t, S.st("lp2"), S.d("lp2"), "SemiBold", 34, WHITE, 1.3, out)


def sc_check(base, t, D, S):
    out = out_of(t, D)
    kicker(base, t, "ENTRY CONFIRMATION CHECKLIST", a=out)
    tf = [("M5", "Entry trigger", "k1"), ("M15", "Confirmation struktur", "k2"), ("M30", "Intraday momentum", "k3"),
          ("H1/H4", "Arah trend utama", "k4")]
    y = 230
    d = ImageDraw.Draw(base, "RGBA")
    for (a_, b_, sk) in tf:
        st = S.st(sk)
        k = ap(t, st, 0.35) * out
        d.rounded_rectangle((60, y, 1020, y + 120), 24, fill=(255, 255, 255, int(12 * k)), outline=rgba(GOLD, 0.5 * k), width=2)
        check_box(base, 90, y + 30, 60, clamp((t - S.en(sk) + 0.4) / 0.35), GREEN, k)
        pill(base, 180, y + 30, a_, GOLD, 34, k, padx=20, pady=12)
        typed(base, b_, 180 + text_w(a_, "ExtraBold", 34) + 70, y + 38, 600, t, st, S.d(sk), "Bold", 44, WHITE, 1.2, out)
        y += 140
    for sk, r in (("k5", "Tunggu candle close, jangan bergantung pada wick sahaja."), ("k6", "Tetapkan SL dan risk management sebelum entry.")):
        st = S.st(sk)
        k = ap(t, st, 0.35) * out
        check_box(base, 90, y + 12, 60, clamp((t - S.en(sk) + 0.3) / 0.35), GREEN, k)
        h = typed(base, r, 180, y + 14, 840, t, st, S.d(sk), "SemiBold", 42, WHITE, 1.28, out)
        y += max(h, 80) + 30
    st = S.st("k7") + 0.5
    k = clamp((t - st) / 0.35)
    if k > 0:
        sh = math.sin(t * 110) * 12 * clamp((st + 0.4 - t) / 0.4)
        s = 1 + 0.8 * (1 - eob(k))
        yy = 1500
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
        embers(base, t, 0.7 * out * k)
    lightning(base, t, st, 200, 900, 480, 1500, seed=41)
    lightning(base, t, st + 0.05, 900, 880, 700, 1520, seed=47)


def sc_fund(base, t, D, S):
    out = out_of(t, D)
    k = ap(t, 0.1, 0.5) * out
    pulse = 0.85 + 0.15 * math.sin(t * 6)
    warn_icon(base, W / 2, 300, int(80 * pulse), k)
    sweep_text(base, "FUNDAMENTAL WATCH", W / 2, 420, "Black", 76, AMBER, "c", k, 10, (180, 90, 0), prog=(t - 0.6) / 0.8)
    for i, (sk, s) in enumerate((("f1", "Kekuatan USD"), ("f2", "Jangkaan kadar faedah Fed"))):
        a = clamp((t - S.st(sk) - 0.3) / 0.3)
        s_ = 1 + 0.3 * (1 - eob(a))
        if a > 0:
            pill(base, W / 2, 560 + i * 110, s, (40, 42, 58), int(40 * s_), a * out, WHITE, "c", padx=36, pady=18, w="Bold")
    st = S.st("f3")
    a = ap(t, st, 0.6) * out
    d = ImageDraw.Draw(base, "RGBA")
    x0, y0 = 120, 820
    d.rounded_rectangle((x0, y0, x0 + 840, y0 + 600), 34, fill=(18, 19, 28, int(240 * a)), outline=rgba(RED, a), width=4)
    d.rounded_rectangle((x0, y0, x0 + 840, y0 + 120), 34, fill=rgba(RED, a))
    d.rectangle((x0, y0 + 80, x0 + 840, y0 + 120), fill=rgba(RED, a))
    text(base, "NOVEMBER 2026", x0 + 420, y0 + 38, "Black", 48, WHITE, "c", a)
    sweep_text(base, "25", x0 + 420, y0 + 160, "Black", 220, WHITE, "c", a, prog=(t - st - 2.0) / 0.8)
    text(base, "RABU", x0 + 420, y0 + 400, "Bold", 40, GREY, "c", a)
    for i, ev in enumerate(["US GDP", "PCE"]):
        b = ap(t, st + 1.2 + i * 0.4, 0.4) * out
        pill(base, x0 + 270 + i * 300, y0 + 480, ev, GOLD, 44, b, anchor="c")
    typed(base, "Berpotensi mencetuskan VOLATILITI BESAR pada gold.", W / 2, 1490, 900, t, st + 1.5, S.d("f3") - 1.5, "Bold", 46, WHITE, 1.3, out, "c")


def sc_outro(base, t, D, S):
    out = out_of(t, D, 0.6)
    a = ap(t, S.st("o1")) * out
    text(base, "Fighters,", W / 2, 260, "Bold", 60, GREY, "c", a)
    typed(base, "jangan kejar candle.", W / 2, 350, 1000, t, S.st("o1") + 0.6, S.d("o1") - 0.6, "Black", 80, WHITE, 1.2, out, "c")
    steps = [("o2", "1", "TUNGGU ZONE"), ("o3", "2", "TUNGGU CONFIRMATION"), ("o4", "3", "BARU RANCANG ENTRY")]
    d = ImageDraw.Draw(base, "RGBA")
    for i, (sk, n, s) in enumerate(steps):
        k = clamp((t - S.st(sk)) / 0.4)
        if k <= 0:
            continue
        y = 560 + i * 190
        x = 60 + (1 - eob(k)) * 300
        col = GOLD if i < 2 else GREEN
        d.rounded_rectangle((x, y, x + 960, y + 150), 28, fill=(16, 17, 26, int(235 * out)), outline=rgba(col, k * out), width=4)
        d.ellipse((x + 30, y + 30, x + 120, y + 120), fill=rgba(col, k * out))
        text(base, n, x + 75, y + 46, "Black", 56, (10, 10, 14), "c", k * out)
        sweep_text(base, s, x + 150, y + 48, "Black", 58, WHITE, "l", k * out, prog=(t - S.st(sk) - 0.3) / 0.6)
    st = S.st("o5")
    k = clamp((t - st) / 0.5)
    embers(base, t, 0.8 * k * out)
    sweep_text(base, "ZIQFX", W / 2, 1220, "Black", 170, GOLD, "c", k * out, 20, (255, 160, 0), prog=(t - st - 0.6) / 0.9,
               scale=1 + 0.4 * (1 - eob(k)))
    a = ap(t, st + 0.5) * out
    text(base, "TRADE SAFE  •  RISK FIRST", W / 2, 1440, "ExtraBold", 40, WHITE, "c", a)
    a = ap(t, st + 1.0) * out
    para(base, "Analisis untuk tujuan pendidikan, bukan nasihat kewangan. Sentiasa urus risiko anda.", W / 2, 1660, 860, "Medium", 30, GREY, 1.3, a, "c")
    flash(base, t, st, 0.25, peak=0.35)


FN = {"hook": sc_hook, "intro": sc_intro, "greet": sc_greet, "context": sc_context, "mtf": sc_mtf, "bias": sc_bias,
      "main": sc_main, "two": sc_two, "levels": sc_levels, "check": sc_check, "fund": sc_fund, "outro": sc_outro}
for zk in ZONES:
    FN[zk] = make_zone(zk)


def render_frame(name, fi):
    info = TL[name]
    S = Seg(info["S"])
    D = info["D"]
    t = fi / FPS
    T = info["start"] + t
    base = background(T)
    FN[name](base, t, D, S)
    if info["chrome"]:
        chrome2(base, T)
    g = 0.0
    if name == "hook":
        s2 = S.st("h2")
        if 0 <= t - s2 < 0.35:
            g = 1 - (t - s2) / 0.35
    return post(base, T, t, D, g)


def render_scene(name):
    D = TL[name]["D"]
    n = int(round(D * FPS))
    idx = ORDER.index(name)
    path = os.path.join(HERE, "seg2", f"{idx:02d}_{name}.mp4")
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                          "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "19",
                          "-pix_fmt", "yuv420p", path], stdin=subprocess.PIPE)
    for fi in range(n):
        p.stdin.write(render_frame(name, fi).tobytes())
    p.stdin.close()
    p.wait()
    return path


# ============================================================ audio
SR = 44100
lowpass, highpass = M.lowpass, M.highpass


def read_wav(p):
    with wave.open(p) as w:
        return np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float64) / 32768


def make_audio(path):
    n = int(TOTAL * SR) + SR
    mus = np.zeros((n, 2))
    sfx = np.zeros((n, 2))
    vox = np.zeros(n)
    rs = np.random.RandomState(1)

    def add(buf, sig, t0, gain=1.0, pan=0.0):
        s = int(t0 * SR)
        if s >= n or s < 0:
            return
        e = min(n, s + len(sig))
        buf[s:e, 0] += sig[: e - s] * gain * (1 - max(0, pan))
        buf[s:e, 1] += sig[: e - s] * gain * (1 + min(0, pan))

    # ---------- voice
    for name in ORDER:
        info = TL[name]
        for k, (st, d) in info["S"].items():
            v = read_wav(os.path.join(TTS_DIR, f"{name}_{k}.wav"))
            s = int((info["start"] + st) * SR)
            e = min(n, s + len(v))
            vox[s:e] += v[: e - s]
    vox /= max(1e-6, np.abs(vox).max())
    vox *= 0.95
    # ---------- music
    beat = BEAT
    drop = DROP
    end_drums = TL["outro"]["start"] + 3.0
    tk = np.arange(int(0.45 * SR)) / SR
    freq = 45 + 110 * np.exp(-tk * 30)
    kick = np.tanh(1.8 * (np.sin(2 * np.pi * np.cumsum(freq) / SR) * np.exp(-tk * 7)
                          + 0.3 * np.sin(2 * np.pi * np.cumsum(freq * 2) / SR) * np.exp(-tk * 40)))
    ts = np.arange(int(0.25 * SR)) / SR
    snare = highpass(rs.randn(len(ts)), 1200) * np.exp(-ts * 18) * 0.6 + np.sin(2 * np.pi * 190 * ts) * np.exp(-ts * 25) * 0.5
    th = np.arange(int(0.06 * SR)) / SR
    hat = highpass(rs.randn(len(th)), 7000) * np.exp(-th * 70)
    prog = [(45, [57, 60, 64]), (41, [53, 57, 60]), (48, [55, 60, 64]), (43, [55, 59, 62])]
    mf = lambda m: 440 * 2 ** ((m - 69) / 12)
    t, bar = 0.0, 0
    pads = {}
    while t < TOTAL:
        root, chord = prog[bar % 4]
        dur = beat * 4
        if bar % 4 not in pads:
            tp = np.arange(int(dur * SR)) / SR
            env = np.minimum(1, tp / 0.3) * np.minimum(1, (dur - tp) / 0.3)
            pad = np.zeros(len(tp))
            for m in chord:
                for det in (-0.12, 0.12):
                    fr = mf(m) * (1 + det / 100)
                    for h, ga in ((1, 1), (2, 0.35), (3, 0.18)):
                        pad += ga * np.sin(2 * np.pi * fr * h * tp + rs.rand() * 6)
            pads[bar % 4] = pad * env * 0.05
        pad = pads[bar % 4]
        add(mus, pad, t, 1.0, -0.2)
        add(mus, pad, t + 0.012, 1.0, 0.2)
        drums = drop <= t < end_drums
        for b in range(4):
            tb = t + b * beat
            if drums:
                add(mus, kick, tb, 0.9)
                if b in (1, 3):
                    add(mus, snare, tb, 0.55)
                for s16 in range(4):
                    add(mus, hat, tb + s16 * beat / 4, 0.22 if s16 % 2 else 0.12, 0.3)
                for e8 in range(2):
                    tt = np.arange(int(beat / 2 * SR)) / SR
                    fr = mf(root - 12 + (12 if (b == 3 and e8 == 1) else 0))
                    bs = np.tanh(2.5 * np.sin(2 * np.pi * fr * tt)) * np.minimum(1, tt / 0.04) * np.exp(-tt * 3)
                    add(mus, bs, tb + e8 * beat / 2, 0.28)
            else:
                tt = np.arange(int(beat * SR)) / SR
                add(mus, np.sin(2 * np.pi * mf(root - 12) * tt) * np.exp(-tt * 2.5), tb, 0.25)
        t += dur
        bar += 1
    # riser into drop
    rl = drop - TL["intro"]["start"]
    tr = np.arange(int(rl * SR)) / SR
    riser = highpass(rs.randn(len(tr)), 2500) * (tr / rl) ** 3 * 0.35 + 0.15 * np.sin(2 * np.pi * (200 * tr + 300 * tr ** 2 / rl)) * (tr / rl) ** 2
    add(mus, riser, TL["intro"]["start"], 1.0)
    # duck music under voice
    env = np.abs(vox)
    k = int(0.25 * SR)
    env = np.convolve(env, np.ones(k) / k, mode="same")
    env = np.clip(env / (env.max() * 0.25 + 1e-9), 0, 1)
    duck = 1 - 0.62 * env
    mus *= duck[:, None]

    # ---------- SFX library
    ti = np.arange(int(1.6 * SR)) / SR
    boom = np.sin(2 * np.pi * (38 + 40 * np.exp(-ti * 8)) * ti) * np.exp(-ti * 2.6) + lowpass(rs.randn(len(ti)), 400) * np.exp(-ti * 6) * 0.6
    tw = np.arange(int(0.5 * SR)) / SR
    wn = rs.randn(len(tw))
    whoosh = (highpass(wn, 1500) * 0.5 + lowpass(wn, 1500) * 0.3) * np.sin(np.pi * tw / 0.5) ** 2
    tg_ = np.arange(int(0.25 * SR)) / SR
    glitch = np.sign(np.sin(2 * np.pi * 180 * tg_ * (1 + 3 * tg_))) * (rs.rand(len(tg_)) > 0.5) * np.exp(-tg_ * 10) * 0.5
    glitch = np.round(glitch * 4) / 4
    tc = np.arange(int(0.7 * SR)) / SR
    ching = sum(np.sin(2 * np.pi * f * tc) * np.exp(-tc * dcy) * g for f, dcy, g in
                ((2093, 6, 0.5), (2637, 7, 0.4), (3136, 8, 0.3), (4186, 10, 0.2)))
    ching = np.concatenate([np.zeros(int(0.07 * SR)), ching])
    ching[: len(tc)] += highpass(rs.randn(len(tc)), 5000) * np.exp(-tc * 40) * 0.5
    ta_ = np.arange(int(0.9 * SR)) / SR
    alarm = np.sign(np.sin(2 * np.pi * np.where((ta_ * 4).astype(int) % 2 == 0, 880, 660) * ta_)) * 0.35
    alarm = lowpass(alarm, 3000) * np.minimum(1, (0.9 - ta_) / 0.05)
    tt_ = np.arange(int(0.012 * SR)) / SR
    tick = highpass(rs.randn(len(tt_)), 3000) * np.exp(-tt_ * 400)
    tth = np.arange(int(2.2 * SR)) / SR
    crack = highpass(rs.randn(len(tth)), 1500) * np.exp(-tth * 9) * (rs.rand(len(tth)) > 0.6)
    thunder = crack * 0.6 + lowpass(rs.randn(len(tth)), 200) * np.exp(-tth * 1.6) * 3.0 + np.sin(2 * np.pi * 35 * tth) * np.exp(-tth * 2) * 0.6
    tsw = np.arange(int(1.4 * SR)) / SR
    sword = sum(np.sin(2 * np.pi * f * tsw) * np.exp(-tsw * dcy) for f, dcy in ((1523, 3), (2311, 4), (3547, 5), (4890, 7), (6210, 9)))
    sword = sword * 0.3 + highpass(rs.randn(len(tsw)), 4000) * np.exp(-tsw * 30) * 0.8
    shing = highpass(rs.randn(int(0.35 * SR)), 5000) * np.linspace(0, 1, int(0.35 * SR)) ** 2 * 0.5

    def A(name, k=None, off=0.0):
        info = TL[name]
        return info["start"] + (info["S"][k][0] if k else 0) + off

    for i, name in enumerate(ORDER):
        st = TL[name]["start"]
        if i > 0:
            add(sfx, whoosh, st - 0.35, 0.35)
        add(sfx, glitch, st, 0.25)
        add(sfx, boom, st, 0.55 if name in ("hook", "greet", "bias", "main", "check") else 0.3)
    # intro sword clash
    add(sfx, shing, A("intro") - 0.2, 0.5)
    add(sfx, sword, A("intro", None, 0.15), 0.55)
    # thunders
    for nm, k, off in (("hook", "h1", 0), ("hook", "h2", 0), ("bias", "b1", 0), ("main", "s3", 0.9), ("check", "k7", 0.5)):
        add(sfx, thunder, A(nm, k, off), 0.55)
    add(sfx, glitch, A("hook", "h2"), 0.5)
    # cha-ching on targets, alarms on warnings
    for zk in ZONES:
        st, dur = TL[zk]["S"]["tg"]
        for i in range(3):
            add(sfx, ching, TL[zk]["start"] + st + 0.35 + i * (dur - 0.35) / 3, 0.35)
        if "w" in TL[zk]["S"]:
            add(sfx, alarm, A(zk, "w"), 0.22)
    # typewriter ticks for typed segments
    TYPED = {"context": ["c1"], "mtf": ["m1", "m2", "m3", "m4"], "main": ["s4", "s5"], "levels": ["lp1", "lp2"],
             "check": ["k1", "k2", "k3", "k4", "k5", "k6"], "fund": ["f3"], "outro": ["o1"],
             "two": ["t1a", "t1b", "t1c", "t2a", "t2b", "t2c", "t2d"]}
    for zk in ZONES:
        TYPED[zk] = [f"b{i}" for i in range(4)] + (["w"] if "w" in TL[zk]["S"] else [])
    rr = random.Random(5)
    for nm, keys in TYPED.items():
        for k in keys:
            st, d = TL[nm]["S"][k]
            tt0 = TL[nm]["start"] + st
            x = 0
            while x < d * 0.85:
                add(sfx, tick, tt0 + x, rr.uniform(0.05, 0.09), rr.uniform(-0.3, 0.3))
                x += rr.uniform(0.05, 0.09)
    # stamp + zone ticks (checkmarks)
    tb = np.arange(int(0.15 * SR)) / SR
    blip = np.sin(2 * np.pi * 1320 * tb) * np.exp(-tb * 30)
    for k in ("k1", "k2", "k3", "k4"):
        add(sfx, blip, A("check", k) + TL["check"]["S"][k][1] - 0.2, 0.25)
    for k in ("k5", "k6"):
        add(sfx, blip, A("check", k) + TL["check"]["S"][k][1] - 0.1, 0.25)

    # ---------- mix
    end = int(TOTAL * SR)
    fo = int(3.0 * SR)
    fade = np.ones(n)
    fade[end - fo:end] = np.linspace(1, 0, fo)
    fade[end:] = 0
    mus /= max(1e-6, np.abs(mus).max())
    sfx /= max(1e-6, np.abs(sfx).max())
    mix = mus * 0.42 + sfx * 0.45 + vox[:, None] * 0.85
    mix *= fade[:, None]
    mix = np.tanh(mix * 1.1) * 0.93
    data = (mix[:end] * 32767).astype(np.int16)
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(data.tobytes())


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "all"
    if mode == "tts":
        gen_tts()
        sys.exit(0)
    os.makedirs(os.path.join(HERE, "seg2"), exist_ok=True)
    if mode == "preview":
        for arg in sys.argv[2:]:
            nm, tt = arg.split(":")
            render_frame(nm, int(float(tt) * FPS)).save(os.path.join(HERE, f"p2_{nm}_{tt}.png"))
        sys.exit(0)
    if mode == "audio":
        make_audio(os.path.join(HERE, "mix.wav"))
        sys.exit(0)
    print("total", TOTAL)
    make_audio(os.path.join(HERE, "mix.wav"))
    names = sorted(ORDER, key=lambda n: -TL[n]["D"])
    with Pool(4) as pool:
        pool.map(render_scene, names)
    with open(os.path.join(HERE, "list2.txt"), "w") as f:
        for i, n in enumerate(ORDER):
            f.write(f"file '{os.path.join(HERE, 'seg2', f'{i:02d}_{n}.mp4')}'\n")
    out = os.path.join(HERE, "ZIQFX_XAUUSD_Outlook_23Nov2026_v3_raw.mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", os.path.join(HERE, "list2.txt"),
                    "-i", os.path.join(HERE, "mix.wav"), "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest",
                    "-movflags", "+faststart", out], check=True)
    print(out)
