"""Siri video menegak (1080x1920) "Masalah Trader Malaysia" - satu video setiap topik.

Usage:
  python3 make_videos.py              # semua topik
  python3 make_videos.py 3 5          # topik #3 dan #5 sahaja
Env: VOICE (default ElevenLabs "Daud M - Malay Influencer"; nama suara edge-tts seperti ms-MY-OsmanNeural pun boleh),
     ELEVENLABS_API_KEY, RATE (edge-tts sahaja, default +4%), BRAND (default ZIQFX), JOBS (default 4)
Output: out/<slug>.mp4 dan out/<slug>.jpg (cover)
Perlu: ffmpeg, edge-tts (akses rangkaian ke speech.platform.bing.com untuk suara baru).
"""
import hashlib, math, os, random, subprocess, sys, time
from multiprocessing import Pool
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

from topics import TOPICS
from avatar import Avatar, mouth_track

W, H, FPS, SR = 1080, 1920, 30, 44100
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")
VOICE = os.environ.get("VOICE", "dNnVzcebCLVAswzGKvfO")  # ElevenLabs: Daud M - Malay Influencer
EL_MODEL = os.environ.get("EL_MODEL", "eleven_multilingual_v2")
RATE = os.environ.get("RATE", "+4%")
BRAND = os.environ.get("BRAND", "ZIQFX")
VDIR = os.path.join(HERE, "voice", VOICE)
N = len(TOPICS)

FD = "/usr/share/fonts/opentype/inter/"
_fc = {}
def font(w, s):
    if (w, s) not in _fc: _fc[(w, s)] = ImageFont.truetype(FD + f"Inter-{w}.otf", s)
    return _fc[(w, s)]

BG = (9, 10, 16)
WHITE, MUTED = (255, 255, 255), (165, 170, 185)
COL = {"red": (236, 84, 92), "gold": (232, 184, 96), "green": (64, 200, 140)}
GOLD = COL["gold"]

def ease(t): t = max(0.0, min(1.0, t)); return 1 - (1 - t) ** 3
def seg(t, a, b): return max(0.0, min(1.0, (t - a) / (b - a))) if b > a else float(t >= a)

# ---------------- audio ----------------
def elevenlabs(text, mp3, prev="", nxt=""):
    import json, urllib.request
    body = {"text": text, "model_id": EL_MODEL, "previous_text": prev, "next_text": nxt,
            "voice_settings": {"stability": 0.38, "similarity_boost": 0.8, "style": 0.35, "use_speaker_boost": True}}
    req = urllib.request.Request(f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE}?output_format=mp3_44100_128",
                                 data=json.dumps(body).encode(), method="POST",
                                 headers={"xi-api-key": os.environ.get("ELEVENLABS_API_KEY", "x"), "Content-Type": "application/json"})
    for k in range(4):
        try:
            with urllib.request.urlopen(req, timeout=120) as r: open(mp3, "wb").write(r.read()); return
        except Exception as e:
            err = e; time.sleep(3 * (k + 1))
    raise RuntimeError(f"ElevenLabs gagal: {text[:40]}... {err}")

def tts(text, prev="", nxt=""):
    os.makedirs(VDIR, exist_ok=True)
    el = "Neural" not in VOICE
    key = text + (EL_MODEL if el else RATE)
    mp3 = os.path.join(VDIR, hashlib.md5(key.encode()).hexdigest()[:10] + ".mp3")
    if el and not os.path.exists(mp3):
        elevenlabs(text, mp3, prev, nxt)
    if not os.path.exists(mp3):
        cmd = ["edge-tts", "--voice", VOICE, f"--rate={RATE}", "--text", text, "--write-media", mp3]
        if os.environ.get("HTTPS_PROXY"): cmd[1:1] = ["--proxy", os.environ["HTTPS_PROXY"]]
        for _ in range(5):  # servis TTS kadang-kadang pulangkan audio kosong
            r = subprocess.run(cmd, capture_output=True)
            if r.returncode == 0 and os.path.getsize(mp3) > 2000: break
            if os.path.exists(mp3): os.remove(mp3)
            time.sleep(2)
        else:
            raise RuntimeError(f"TTS gagal: {text[:40]}... {r.stderr.decode()[-300:]}")
    raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", mp3, "-f", "s16le", "-ac", "1", "-ar", str(SR), "-"],
                         capture_output=True, check=True).stdout
    a = np.frombuffer(raw, np.int16).astype(np.float32) / 32768
    nz = np.where(np.abs(a) > 0.01)[0]
    return a[max(0, nz[0] - 600):nz[-1] + 1500] if len(nz) else a

def music(dur, seed):
    """Pad lembut (Am-F-C-G) + pulse perlahan, sebagai latar di bawah suara."""
    t = np.arange(int(dur * SR)) / SR
    chords = [(220.0, 261.63, 329.63), (174.61, 220.0, 261.63), (130.81, 196.0, 261.63), (196.0, 246.94, 293.66)]
    out = np.zeros_like(t); bar = 4.0
    for i in range(int(dur / bar) + 1):
        a, b = int(i * bar * SR), int(min(dur, (i + 1) * bar + 0.6) * SR)
        if a >= len(t): break
        tt = t[a:b] - i * bar
        env = np.minimum(1, tt / 0.8) * np.exp(-np.maximum(0, tt - bar) * 4)
        for f in chords[(i + seed) % 4]:
            out[a:b] += env * (np.sin(2 * np.pi * f * tt) + 0.3 * np.sin(2 * np.pi * f * 2.003 * tt)) / 3
    beat = 60 / 92
    ph = (t % beat)
    out += 0.5 * np.sin(2 * np.pi * 55 * t) * np.exp(-ph * 9)  # pulse bass lembut
    out *= np.minimum(1, t / 1.5) * np.minimum(1, (dur - t) / 1.5)
    return out / (np.abs(out).max() + 1e-9)

def build_timeline(i, topic):
    """Pulangkan (lines, scenes, audio). lines: list of dict(text, t0, t1, scene, item)."""
    nxt = TOPICS[i + 1]["title"] if i + 1 < N else None
    script = [("hook", None, topic["hook"][1]),
              ("hook", None, f"Ni masalah trader Malaysia, nombor {i + 1}. {topic['title']}.")]
    for si, (_, _, items) in enumerate(topic["sections"]):
        for ii, (_, nar) in enumerate(items):
            script.append((f"s{si}", ii, nar))
    script.append(("outro", None, "Ingat ye, trading ni risiko dia tinggi. Video ni bukan nasihat kewangan."))
    script.append(("outro", None, f"Follow tau. Next video, pasal {nxt}." if nxt
                   else "Save video ni, share dekat member trader korang."))
    clips, lines, cur, prev_scene = [], [], 0.35, None
    for k, (scene, item, text) in enumerate(script):
        if prev_scene is not None and scene != prev_scene: cur += 0.75  # ruang untuk transisi babak
        a = tts(text, script[k - 1][2] if k else "", script[k + 1][2] if k + 1 < len(script) else "")
        lines.append(dict(text=text.replace(".", ". ").replace("  ", " ").strip(), t0=cur, t1=cur + len(a) / SR, scene=scene, item=item))
        clips.append((cur, a)); cur += len(a) / SR + 0.32; prev_scene = scene
    dur = cur + 1.2
    voice = np.zeros(int(dur * SR) + SR, np.float32)
    for t0, a in clips:
        s = int(t0 * SR); voice[s:s + len(a)] += a
    voice = voice[:int(dur * SR)]
    voice = voice / (np.abs(voice).max() + 1e-9) * 0.92
    # duck muzik bila ada suara
    k = SR // 4; cs = np.concatenate([[0], np.cumsum((np.abs(voice) > 0.02).astype(np.float32))])
    env = (cs[np.minimum(np.arange(len(voice)) + k // 2, len(voice))] - cs[np.maximum(np.arange(len(voice)) - k // 2, 0)]) / k
    mix = voice + music(dur, i) * (0.11 - 0.06 * np.clip(env * 3, 0, 1))
    scenes = {}
    for l in lines:
        s = scenes.setdefault(l["scene"], [l["t0"], l["t1"]]); s[1] = l["t1"]
    return lines, scenes, mix.clip(-1, 1), dur, voice

# ---------------- drawing helpers ----------------
def wrap(text, f, maxw):
    words, rows, cur = text.split(), [], ""
    for w in words:
        test = (cur + " " + w).strip()
        if f.getlength(test) <= maxw or not cur: cur = test
        else: rows.append(cur); cur = w
    if cur: rows.append(cur)
    return rows

_tc = {}
def text_block(text, f, fill, maxw, align="center", lh=1.18, stroke=0):
    k = (text, id(f), fill, maxw, align, stroke)
    if k in _tc: return _tc[k]
    rows = wrap(text, f, maxw); asc, desc = f.getmetrics(); rh = int((asc + desc) * lh)
    w = int(max(f.getlength(r) for r in rows)) + 2 * stroke + 4
    im = Image.new("RGBA", (w, rh * len(rows) + 2 * stroke + 4), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    for j, r in enumerate(rows):
        x = (w - f.getlength(r)) / 2 if align == "center" else 0
        d.text((x + stroke, j * rh + stroke), r, font=f, fill=fill, stroke_width=stroke, stroke_fill=(0, 0, 0))
    _tc[k] = im
    return im

def fade(im, a):
    if a >= 0.999: return im
    im = im.copy(); im.putalpha(im.getchannel("A").point(lambda v: int(v * a))); return im

def put(img, im, x, y, a=1.0):
    if a <= 0.004: return
    img.alpha_composite(fade(im, a), (int(x), int(y)))

def pill(text, f, fg, bg, padx=28, pady=14, outline=None):
    tw = int(f.getlength(text)); asc, desc = f.getmetrics()
    im = Image.new("RGBA", (tw + 2 * padx, asc + desc + 2 * pady), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, im.width - 1, im.height - 1], im.height // 2, fill=bg, outline=outline, width=3 if outline else 0)
    d.text((padx, pady), text, font=f, fill=fg)
    return im

def make_bg(color, seed):
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    r1 = np.sqrt(((xx - W * 0.15) / W) ** 2 + ((yy - H * 0.12) / H) ** 2)
    r2 = np.sqrt(((xx - W * 0.9) / W) ** 2 + ((yy - H * 0.85) / H) ** 2)
    g1 = np.clip(1 - r1 * 1.7, 0, 1) ** 2; g2 = np.clip(1 - r2 * 2.0, 0, 1) ** 2
    bg = np.zeros((H, W, 3), np.float32)
    for c in range(3): bg[..., c] = BG[c] + g1 * color[c] * 0.22 + g2 * GOLD[c] * 0.12
    img = Image.fromarray(bg.clip(0, 255).astype(np.uint8)).convert("RGBA")
    d = ImageDraw.Draw(img)
    for x in range(0, W, 90): d.line([(x, 0), (x, H)], fill=(255, 255, 255, 6))
    for y in range(0, H, 90): d.line([(0, y), (W, y)], fill=(255, 255, 255, 6))
    # strip candle lebar yang digerakkan perlahan
    random.seed(seed); strip = Image.new("RGBA", (W * 3, 520), (0, 0, 0, 0)); sd = ImageDraw.Draw(strip)
    p, cw = 260.0, 30
    for k in range(W * 3 // cw):
        o = p; c = o + random.gauss(0, 22); hi = max(o, c) + abs(random.gauss(0, 12)); lo = min(o, c) - abs(random.gauss(0, 12))
        c = min(470, max(50, c)); col = (64, 200, 140, 34) if c <= o else (236, 84, 92, 34)
        x = k * cw + cw / 2
        sd.line([(x, hi), (x, lo)], fill=col, width=2)
        sd.rectangle([x - 9, min(o, c), x + 9, max(o, c) + 2], fill=col); p = c
    return img.convert("RGB"), strip

# ---------------- scene renderers ----------------
class Renderer:
    def __init__(self, i, topic, lines, scenes, dur):
        self.i, self.tp, self.lines, self.sc, self.dur = i, topic, lines, scenes, dur
        accent = COL["red"]
        self.bg, self.strip = make_bg(accent, i + 7)
        self.top = Image.new("RGBA", (W, 200), (0, 0, 0, 0)); d = ImageDraw.Draw(self.top)
        d.text((60, 92), "MASALAH TRADER MALAYSIA", font=font("Bold", 34), fill=MUTED)
        p = pill(f"#{i + 1:02d}/{N}", font("Bold", 34), BG, GOLD, padx=22, pady=10)
        self.top.alpha_composite(p, (W - 60 - p.width, 82))
        self.brand = text_block(BRAND, font("Bold", 30), (255, 255, 255, 120), 400)
        random.seed(i)
        self.parts = [(random.uniform(0, W), random.uniform(0, H), random.uniform(10, 40), random.uniform(1.5, 4)) for _ in range(40)]
        # kad bullet (dua keadaan: aktif / pasif)
        self.cards = {}
        for si, (_, cname, items) in enumerate(topic["sections"]):
            for ii, (txt, _) in enumerate(items):
                self.cards[(si, ii)] = (self.card(ii + 1, txt, COL[cname], True), self.card(ii + 1, txt, COL[cname], False))
        self.words = self.caption_words()
        self.av = Avatar(400)

    def card(self, n, txt, color, active):
        f = font("SemiBold", 52); tb = text_block(txt, f, WHITE if active else (225, 228, 236), 740, align="left")
        h = max(170, tb.height + 70); im = Image.new("RGBA", (940, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
        d.rounded_rectangle([0, 0, 939, h - 1], 34, fill=(255, 255, 255, 20 if active else 12),
                            outline=color + ((255,) if active else (90,)), width=4 if active else 2)
        d.ellipse([34, h / 2 - 42, 118, h / 2 + 42], fill=color + ((255,) if active else (150,)))
        nt = str(n); nf = font("Bold", 46)
        d.text((76 - nf.getlength(nt) / 2, h / 2 - 30), nt, font=nf, fill=BG)
        im.alpha_composite(tb, (150, int((h - tb.height) / 2)))
        return im

    def caption_words(self):
        out = []
        for l in self.lines:
            ws = l["text"].split(); wts = np.array([len(w) + 2 for w in ws], float)
            edges = l["t0"] + np.concatenate([[0], np.cumsum(wts)]) / wts.sum() * (l["t1"] - l["t0"])
            chunks = [ws[k:k + 4] for k in range(0, len(ws), 4)]
            k = 0
            for ch in chunks:
                out.append(dict(words=ch, t0=edges[k], t1=edges[k + len(ch)], wt=edges[k:k + len(ch) + 1], line_end=l["t1"]))
                k += len(ch)
        return out

    def scene_alpha(self, t, name):
        if name not in self.sc: return 0
        a, b = self.sc[name]
        names = list(self.sc); idx = names.index(name)
        end = self.sc[names[idx + 1]][0] - 0.35 if idx + 1 < len(names) else self.dur + 1
        start = a - 0.4 if idx else -1
        return ease(seg(t, start, start + 0.45)) * (1 - seg(t, end - 0.35, end))

    def frame(self, t):
        img = self.bg.copy().convert("RGBA")
        off = int((t * 18) % (self.strip.width - W))
        img.alpha_composite(self.strip.crop((off, 0, off + W, 520)), (0, 1180))
        d = ImageDraw.Draw(img)
        for x, y0, sp, sz in self.parts:
            y = (y0 - sp * t) % H
            d.ellipse([x - sz, y - sz, x + sz, y + sz], fill=GOLD + (int(40 + sz * 12),))
        img.alpha_composite(self.top)
        d.rectangle([60, 160, 60 + (W - 120) * min(1, t / self.dur), 166], fill=GOLD + (255,))
        d.rectangle([60 + (W - 120) * min(1, t / self.dur), 160, W - 60, 166], fill=(255, 255, 255, 30))
        self.hook(img, t, self.scene_alpha(t, "hook"))
        for si in range(len(self.tp["sections"])): self.section(img, t, si, self.scene_alpha(t, f"s{si}"))
        self.outro(img, t, self.scene_alpha(t, "outro"))
        self.presenter(img, t)
        self.captions(img, t)
        put(img, self.brand, (W - self.brand.width) / 2, H - 120, 1)
        return img.convert("RGB")

    def hook(self, img, t, a):
        if a <= 0: return
        hl = [l for l in self.lines if l["scene"] == "hook"]
        chip = pill(f"MASALAH #{self.i + 1}", font("Bold", 44), WHITE, COL["red"], padx=34, pady=16)
        e = ease(seg(t, 0.1, 0.6)); put(img, chip, (W - chip.width) / 2, 470 - 40 * (1 - e), a * e)
        tb = text_block(self.tp["hook"][0], font("ExtraBold", 96), WHITE, 920, lh=1.12)
        e = ease(seg(t, 0.3, 0.9)); s = 0.85 + 0.15 * e
        im = tb.resize((int(tb.width * s), int(tb.height * s)), Image.LANCZOS) if s < 0.999 else tb
        put(img, im, (W - im.width) / 2, 600 + (tb.height - im.height) / 2, a * e)
        e2 = ease(seg(t, hl[1]["t0"] - 0.1, hl[1]["t0"] + 0.4))
        if e2 > 0:
            y = 600 + tb.height + 60
            d = ImageDraw.Draw(img); d.rectangle([W / 2 - 90, y, W / 2 + 90, y + 6], fill=GOLD + (int(255 * a * e2),))
            tt = text_block(self.tp["title"], font("Bold", 64), GOLD, 900)
            put(img, tt, (W - tt.width) / 2, y + 40 + 30 * (1 - e2), a * e2)

    def section(self, img, t, si, a):
        if a <= 0: return
        head, cname, items = self.tp["sections"][si]
        sl = [l for l in self.lines if l["scene"] == f"s{si}"]
        t0 = sl[0]["t0"]
        chip = pill(head, font("Bold", 46), BG if cname != "red" else WHITE, COL[cname], padx=34, pady=16)
        e = ease(seg(t, t0 - 0.4, t0)); put(img, chip, 70 - 60 * (1 - e), 300, a * e)
        y = 460
        active = max([l["item"] for l in sl if t >= l["t0"] - 0.15] or [-1])
        for ii in range(len(items)):
            on, off = self.cards[(si, ii)]
            st = sl[ii]["t0"] - 0.15
            e = ease(seg(t, st, st + 0.45))
            if e > 0:
                put(img, on if ii == active else off, 70 + 120 * (1 - e), y, a * e * (1 if ii == active else 0.85))
            y += on.height + 30

    def outro(self, img, t, a):
        if a <= 0: return
        ol = [l for l in self.lines if l["scene"] == "outro"]
        e = ease(seg(t, ol[0]["t0"] - 0.4, ol[0]["t0"]))
        warn = pill("INGAT", font("Bold", 46), BG, GOLD, padx=34, pady=16)
        put(img, warn, (W - warn.width) / 2, 360, a * e)
        tb = text_block("Trading berisiko tinggi. Bukan nasihat kewangan.", font("ExtraBold", 74), WHITE, 900)
        put(img, tb, (W - tb.width) / 2, 450 + 30 * (1 - e), a * e)
        e2 = ease(seg(t, ol[1]["t0"] - 0.2, ol[1]["t0"] + 0.3))
        if e2 <= 0: return
        nxt = TOPICS[self.i + 1]["title"] if self.i + 1 < N else None
        y = 480 + tb.height + 50
        box = Image.new("RGBA", (940, 300), (0, 0, 0, 0)); d = ImageDraw.Draw(box)
        d.rounded_rectangle([0, 0, 939, 299], 36, fill=(255, 255, 255, 18), outline=GOLD + (255,), width=3)
        lab = (f"SETERUSNYA  ·  #{self.i + 2:02d}" if nxt else "SIMPAN & SHARE")
        d.text((50, 44), lab, font=font("Bold", 36), fill=GOLD)
        bt = text_block(nxt or "Share dengan kawan trader kau", font("Bold", 58), WHITE, 840, align="left")
        box.alpha_composite(bt, (50, 110))
        put(img, box, 70, y + 40 * (1 - e2), a * e2)
        fl = pill(f"Follow  {BRAND}", font("Bold", 50), BG, WHITE, padx=44, pady=20)
        pulse = 1 + 0.03 * math.sin(t * 6)
        fl2 = fl.resize((int(fl.width * pulse), int(fl.height * pulse)), Image.LANCZOS)
        put(img, fl2, (W - fl2.width) / 2, y + 360 - (fl2.height - fl.height) / 2, a * e2)

    def captions(self, img, t):
        cur = next((c for c in self.words if c["t0"] - 0.05 <= t < max(c["t1"], min(c["line_end"], c["t1"] + 0.3))), None)
        if not cur: return
        f = font("ExtraBold", 60); sp = f.getlength(" ")
        k = int(np.searchsorted(cur["wt"], t, side="right")) - 1
        rows = wrap(" ".join(cur["words"]), f, 960)
        # tetapkan warna setiap perkataan; perkataan aktif berwarna emas
        widx, y = 0, 1555 - (len(rows) - 1) * 40
        layer = Image.new("RGBA", (W, 260), (0, 0, 0, 0)); d = ImageDraw.Draw(layer)
        for r, row in enumerate(rows):
            ws = row.split(); x = (W - f.getlength(row)) / 2
            for w in ws:
                d.text((x, r * 80), w, font=f, fill=GOLD if widx == k else WHITE, stroke_width=6, stroke_fill=(0, 0, 0))
                x += f.getlength(w) + sp; widx += 1
        pop = ease(seg(t, cur["t0"] - 0.05, cur["t0"] + 0.12))
        img.alpha_composite(fade(layer, pop), (0, int(y + 14 * (1 - pop))))

    def presenter(self, img, t):
        """Pembentang 3D: besar di tengah semasa hook, kemudian beralih ke penjuru kiri bawah."""
        k = min(int(t * FPS), len(self.mouth) - 1)
        av = self.av.render(t, self.mouth[k], self.energy[k])
        s0 = self.sc["s0"][0]
        e = ease(seg(t, s0 - 0.9, s0 - 0.1))
        intro = ease(seg(t, 0.0, 0.6))
        w = 400 + (270 - 400) * e
        cx = W / 2 + (30 + 135 - W / 2) * e
        top = 1040 + (1185 - 1040) * e + 80 * (1 - intro)
        if abs(w - 400) > 0.5: av = av.resize((int(w), int(av.height * w / 400)), Image.LANCZOS)
        # cakera emas di belakang pembentang
        disc = Image.new("RGBA", av.size, (0, 0, 0, 0)); dd = ImageDraw.Draw(disc)
        r = av.width * 0.46; c = (av.width / 2, av.height * 0.42)
        dd.ellipse([c[0] - r, c[1] - r, c[0] + r, c[1] + r], fill=GOLD + (40,), outline=GOLD + (150,), width=3)
        put(img, disc, cx - av.width / 2, top, intro)
        put(img, av, cx - av.width / 2, top, intro)

# ---------------- render ----------------
def render(i):
    topic = TOPICS[i]
    lines, scenes, mix, dur, voice = build_timeline(i, topic)
    os.makedirs(OUT, exist_ok=True)
    wav = os.path.join(OUT, f"_{topic['slug']}.wav")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "-", wav],
                   input=mix.astype(np.float32).tobytes(), check=True)
    R = Renderer(i, topic, lines, scenes, dur)
    R.mouth, R.energy = mouth_track(voice, SR, FPS, dur + 1)
    mp4 = os.path.join(OUT, f"{topic['slug']}.mp4")
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                           "-r", str(FPS), "-i", "-", "-i", wav, "-c:v", "libx264", "-preset", "medium", "-crf", "23",
                           "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", mp4],
                          stdin=subprocess.PIPE)
    nfr = int(dur * FPS)
    for fi in range(nfr):
        ff.stdin.write(R.frame(fi / FPS).tobytes())
    ff.stdin.close(); ff.wait()
    R.frame(scenes["hook"][1] - 0.1).save(os.path.join(OUT, f"{topic['slug']}.jpg"), quality=90)
    os.remove(wav)
    return f"{topic['slug']}.mp4  {dur:.1f}s"

if __name__ == "__main__":
    idx = [int(a) - 1 for a in sys.argv[1:]] or list(range(N))
    for i in idx: build_timeline(i, TOPICS[i])  # jana semua suara dulu (berurutan, elak rate-limit)
    with Pool(int(os.environ.get("JOBS", "4"))) as p:
        for r in p.imap_unordered(render, idx): print("siap:", r, flush=True)
