"""Efek 'gempak': chart hidup ikut topik, lantai grid 3D, warp 3D, glitch, zoom punch, gegar, emoji, SFX."""
import math, random
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H = 1080, 1920
GOLD = (232, 184, 96); RED = (236, 84, 92); GREEN = (64, 200, 140); WHITE = (255, 255, 255); MUTED = (165, 170, 185)
CC = {"red": RED, "green": GREEN, "gold": GOLD}
FD = "/usr/share/fonts/opentype/inter/"
_fc = {}
def font(w, s):
    if (w, s) not in _fc: _fc[(w, s)] = ImageFont.truetype(FD + f"Inter-{w}.otf", s)
    return _fc[(w, s)]

def ease(t): t = max(0.0, min(1.0, t)); return 1 - (1 - t) ** 3
def back(t):
    t = max(0.0, min(1.0, t)); c = 1.9; return 1 + (c + 1) * (t - 1) ** 3 + c * (t - 1) ** 2
def seg(t, a, b): return max(0.0, min(1.0, (t - a) / (b - a))) if b > a else float(t >= a)

def put(img, im, x, y, a=1.0):
    """Tampal RGBA dengan alfa a; selamat untuk koordinat negatif / luar kanvas."""
    if a <= 0.004 or im is None: return
    x, y = int(x), int(y)
    l, t_ = max(0, -x), max(0, -y); r, b = min(im.width, img.width - x), min(im.height, img.height - y)
    if r <= l or b <= t_: return
    im = im.crop((l, t_, r, b)) if (l or t_ or r < im.width or b < im.height) else im
    if a < 0.999:
        im = im.copy(); im.putalpha(im.getchannel("A").point(lambda v: int(v * a)))
    img.alpha_composite(im, (x + l, y + t_))

# ---------------- emoji ----------------
_ec = {}
def emoji(ch, size):
    k = (ch, size)
    if k not in _ec:
        f = ImageFont.truetype("/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf", 109)
        im = Image.new("RGBA", (160, 160), (0, 0, 0, 0))
        ImageDraw.Draw(im).text((10, 10), ch, font=f, embedded_color=True)
        bb = im.getbbox() or (0, 0, 1, 1); im = im.crop(bb)
        s = size / max(im.size); _ec[k] = im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))), Image.LANCZOS)
    return _ec[k]

def scaled(im, s):
    if abs(s - 1) < 0.01: return im
    return im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))), Image.BILINEAR)

# ---------------- 3D ----------------
def _coeffs(dst, src):
    A, B = [], []
    for (X, Y), (u, v) in zip(dst, src):
        A.append([X, Y, 1, 0, 0, 0, -u * X, -u * Y]); B.append(u)
        A.append([0, 0, 0, X, Y, 1, -v * X, -v * Y]); B.append(v)
    return np.linalg.solve(np.array(A, float), np.array(B, float)).tolist()

def warp3d(img, layer, cx, cy, ry=0.0, rx=0.0, scale=1.0, a=1.0, f=2200):
    """Putar lapisan rata di sekitar paksi Y/X (darjah) dan unjur dengan perspektif."""
    if a <= 0: return
    if abs(ry) < 0.3 and abs(rx) < 0.3:
        im = scaled(layer, scale); put(img, im, cx - im.width / 2, cy - im.height / 2, a); return
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
    if x1 - x0 < 2 or y1 - y0 < 2: return
    c = _coeffs([(px - x0, py - y0) for px, py in pts], [(0, 0), (w, 0), (w, h), (0, h)])
    out = layer.transform((x1 - x0, y1 - y0), Image.PERSPECTIVE, c, Image.BILINEAR)
    put(img, out, x0, y0, a)

def floor3d(img, t, horizon=1150, color=GOLD):
    """Lantai grid 3D bercahaya yang bergerak ke arah kamera."""
    lay = Image.new("RGBA", (W, H - horizon), (0, 0, 0, 0)); d = ImageDraw.Draw(lay); h = H - horizon
    for k in range(1, 16):
        z = k - (t * 1.4) % 1
        y = 260 / z - 18
        if 0 <= y < h:
            a = int(min(150, 30 + 900 / (z * z + 4)))
            d.line([(0, y), (W, y)], fill=color + (a,), width=2 if z < 3 else 1)
    for x0 in range(-14, 15):
        d.line([(W / 2 + x0 * 30, 0), (W / 2 + x0 * 330, h * 1.4)], fill=color + (55,), width=1)
    g = Image.new("L", (1, h)); g.putdata([int(255 * min(1, (h - y) / h * 1.3) * min(1, y / 40 + 0.15)) for y in range(h)])
    lay.putalpha(Image.fromarray(np.minimum(np.array(lay.getchannel("A")), np.array(g.resize((W, h))))))
    img.alpha_composite(lay, (0, horizon))
    d2 = ImageDraw.Draw(img)
    for k, a in ((10, 25), (4, 60), (1, 140)):
        d2.rectangle([0, horizon - k, W, horizon + k], fill=color + (a,))

# ---------------- pasca-proses kamera ----------------
def camera(img, zoom=1.0, dx=0, dy=0):
    if zoom <= 1.0005 and not dx and not dy: return img
    cw, ch = W / zoom, H / zoom
    x0 = (W - cw) / 2 - dx / zoom; y0 = (H - ch) / 2 - dy / zoom
    return img.transform((W, H), Image.EXTENT, (x0, y0, x0 + cw, y0 + ch), Image.BILINEAR)

def glitch(img, k, seed):
    """k 0..1 kekuatan: hirisan mendatar tersasar + anjakan saluran RGB."""
    if k <= 0.01: return img
    a = np.array(img); rnd = random.Random(seed)
    for _ in range(int(6 + 10 * k)):
        y = rnd.randrange(0, H - 40); hh = rnd.randrange(8, 90); sh = int(rnd.uniform(-1, 1) * 120 * k)
        a[y:y + hh] = np.roll(a[y:y + hh], sh, axis=1)
    s = int(16 * k)
    a[..., 0] = np.roll(a[..., 0], s, axis=1); a[..., 2] = np.roll(a[..., 2], -s, axis=1)
    return Image.fromarray(a)

def flash(img, k, col=(255, 255, 255)):
    if k <= 0.01: return img
    return Image.blend(img, Image.new("RGB", img.size, col), min(0.8, k))

# ---------------- SFX (disintesis, tiada fail luar) ----------------
def _env(n, att, dec, sr):
    t = np.arange(n) / sr
    return np.minimum(1, t / max(att, 1e-4)) * np.exp(-t / dec)

def sfx(kind, sr=44100, seed=0):
    rng = np.random.default_rng(seed)
    if kind == "whoosh":
        n = int(0.45 * sr); x = rng.standard_normal(n)
        X = np.fft.rfft(x); fr = np.fft.rfftfreq(n, 1 / sr)
        X *= np.exp(-((np.log(fr + 1) - np.log(1400)) ** 2) / 0.9)
        x = np.fft.irfft(X, n); t = np.arange(n) / n
        return x / np.abs(x).max() * np.sin(np.pi * t) ** 2 * 0.55
    if kind == "boom":
        n = int(0.9 * sr); t = np.arange(n) / sr
        f = 70 * np.exp(-t * 3) + 32; ph = 2 * np.pi * np.cumsum(f) / sr
        x = np.sin(ph) * np.exp(-t * 4.5) + 0.35 * rng.standard_normal(n) * np.exp(-t * 30)
        return x / np.abs(x).max() * 0.9
    if kind == "pop":
        n = int(0.12 * sr); t = np.arange(n) / sr
        f = 700 + 900 * t / t[-1]; x = np.sin(2 * np.pi * np.cumsum(f) / sr) * _env(n, 0.003, 0.04, sr)
        return x * 0.5
    if kind == "ding":
        n = int(1.0 * sr); t = np.arange(n) / sr
        x = (np.sin(2 * np.pi * 1318 * t) + 0.5 * np.sin(2 * np.pi * 2637 * t)) * _env(n, 0.002, 0.35, sr)
        return x * 0.4
    if kind == "glitch":
        n = int(0.25 * sr); x = np.sign(rng.standard_normal(n // 300 + 1)).repeat(300)[:n]
        x *= (rng.random(n // 1500 + 1) > 0.4).repeat(1500)[:n]
        return x * 0.22 * _env(n, 0.001, 0.15, sr)
    if kind == "riser":
        n = int(0.6 * sr); t = np.arange(n) / sr
        x = rng.standard_normal(n) * (t / t[-1]) ** 2
        return x / np.abs(x).max() * 0.3
    return np.zeros(1)

# ---------------- chart hidup ----------------
def chart_times(lines):
    """Masa chart pada babak hook: mula selepas tajuk 'slam', cop (stamp) di hujung ayat hook pertama."""
    hl = [l for l in lines if l["scene"] == "hook"]
    return 0.7, max(1.8, hl[0]["t1"] - 0.15)

def label_times(cfg, lines):
    t0, t1 = chart_times(lines)
    return [t0 + fr * (t1 - t0) for fr, *_ in cfg.get("labels", [])]

class LiveChart:
    def __init__(self, cfg, seed, top=770, h=380):
        self.c, self.top, self.h = cfg, top, h
        self.x0, self.x1 = 60, 1020
        self.kind = cfg.get("kind", "candles")
        if self.kind == "scale": return
        n = cfg.get("n", 44); kp = np.array(cfg["path"], float)
        xs = np.linspace(0, 1, len(kp)); xi = np.linspace(0, 1, n)
        base = np.interp(xi, xs, kp)
        rnd = np.random.default_rng(seed); amp = cfg.get("noise", 0.035)
        noise = np.cumsum(rnd.normal(0, amp, n)) * 0.35 + rnd.normal(0, amp, n)
        noise -= np.linspace(noise[0], noise[-1], n)
        fz = cfg.get("freeze_at")
        if fz: noise *= np.clip((fz - xi) / 0.08, 0.05, 1)
        self.close = base + noise
        self.close[0], self.close[-1] = base[0], base[-1]
        self.open = np.concatenate([[self.close[0]], self.close[:-1]])
        wick = np.abs(rnd.normal(0, amp * 0.9, n)) * (np.clip((fz - xi) / 0.08, 0.05, 1) if fz else 1)
        self.hi = np.maximum(self.open, self.close) + wick; self.lo = np.minimum(self.open, self.close) - wick
        lo = min(self.lo.min(), min([z[0] for z in cfg.get("zones", [])] or [9])); hi = max(self.hi.max(), max([z[1] for z in cfg.get("zones", [])] or [-9]))
        self.pmin, self.pmax = lo - 0.05, hi + 0.08
        self.n = n

    def y(self, v):
        pt, pb = self.top + 100, self.top + self.h - 30
        return pb - (v - self.pmin) / (self.pmax - self.pmin) * (pb - pt)

    def value(self, i):
        c = self.c.get("counter");
        if not c: return None
        mode = c.get("mode", "ratio"); v0 = self.close[0]; ve = self.close[-1]; v = self.close[i]
        if mode == "ratio": val = c["start"] * v / max(v0, 1e-6)
        elif mode == "to_zero": val = c["start"] * max(0, (v - ve)) / max(v0 - ve, 1e-6)
        elif mode == "pnl": val = c["end"] * (v - v0) / (ve - v0 if ve != v0 else 1)
        elif mode == "abs": val = c["scale"] * max(0, v)
        elif mode == "clock":
            m = c["from"] + (c["to"] - c["from"]) * i / (self.n - 1); hh, mm = divmod(int(m) % 1440, 60)
            return f"{hh:02d}:{mm:02d}"
        return c["fmt"].format(val)

    def draw(self, img, t, t0, t1, alpha, lines_t=None):
        if alpha <= 0: return 0.0
        p = seg(t, t0, t1)
        lay = Image.new("RGBA", (W, self.h + 40), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
        top = 0
        d.rounded_rectangle([self.x0, top, self.x1, top + self.h], 30, fill=(12, 14, 22, 215), outline=GOLD + (110,), width=2)
        ttl = self.c.get("title", "")
        d.text((self.x0 + 30, top + 26), ttl, font=font("Bold", 30), fill=MUTED)
        stamp_k = seg(t, t1, t1 + 0.35)
        if self.kind == "scale":
            self._scale(d, t, p)
        else:
            vis = p * (self.n - 1) + 1
            k = int(vis); fr = vis - k
            cw = (self.x1 - self.x0 - 60) / self.n
            Y = lambda v: self.y(v) - self.top
            for z0, z1, zc, zl in self.c.get("zones", []):
                d.rectangle([self.x0 + 20, Y(z1), self.x1 - 20, Y(z0)], fill=CC[zc] + (40,))
                d.line([(self.x0 + 20, Y(z1)), (self.x1 - 20, Y(z1))], fill=CC[zc] + (140,), width=2)
                d.text((self.x1 - 30 - font("SemiBold", 24).getlength(zl), Y(z1) - 32), zl, font=font("SemiBold", 24), fill=CC[zc])
            pts = []
            for i in range(min(k + 1, self.n)):
                o, c = self.open[i], self.close[i]; h_, l_ = self.hi[i], self.lo[i]
                if i == k:  # candle semasa sedang terbentuk
                    c = o + (c - o) * fr; h_ = max(o, c) + (h_ - max(self.open[i], self.close[i])) * fr
                    l_ = min(o, c) - (min(self.open[i], self.close[i]) - l_) * fr
                    if fr < 0.05: continue
                x = self.x0 + 30 + i * cw + cw / 2
                col = GREEN if c >= o else RED
                d.line([(x, Y(h_)), (x, Y(l_))], fill=col + (255,), width=3)
                d.rectangle([x - cw * 0.32, min(Y(o), Y(c)), x + cw * 0.32, max(Y(o), Y(c)) + 2], fill=col + (255,))
                pts.append((x, Y(c)))
            if len(pts) > 1: d.line(pts, fill=GOLD + (120,), width=3)
            if pts:  # titik harga semasa + garis
                x, yv = pts[-1]
                d.line([(x, yv), (self.x1 - 20, yv)], fill=WHITE + (70,), width=1)
                d.ellipse([x - 7, yv - 7, x + 7, yv + 7], fill=WHITE)
            idx = max(0, min(self.n - 1, int(round(p * (self.n - 1)))))
            v = self.value(idx)
            if v is not None:
                c = self.c["counter"]
                col = RED if (c.get("mode") in ("to_zero", "pnl") and p > 0.05) or (self.close[idx] < self.close[0] - 0.05) else GREEN
                if c.get("mode") == "clock": col = GOLD
                vt = font("ExtraBold", 50)
                d.text((self.x1 - 30 - vt.getlength(v), top + 16), v, font=vt, fill=col)
                lb = c.get("label", "")
                d.text((self.x1 - 30 - vt.getlength(v) - 16 - font("SemiBold", 26).getlength(lb), top + 32), lb, font=font("SemiBold", 26), fill=MUTED)
            # label peristiwa
            for (fr_, text, colname, emo) in self.c.get("labels", []):
                tl = t0 + fr_ * (t1 - t0)
                if t < tl: continue
                e = back(seg(t, tl, tl + 0.3)); i = max(0, min(self.n - 1, int(fr_ * (self.n - 1))))
                x = self.x0 + 30 + i * cw + cw / 2; yv = Y(self.close[i])
                tag = self._tag(text, CC[colname], emo)
                tag = scaled(tag, max(0.05, e))
                tx = min(self.x1 - 20 - tag.width, max(self.x0 + 20, x - tag.width / 2))
                ty = yv - tag.height - 26 if yv - tag.height - 26 > 80 else yv + 26
                d.line([(x, yv), (x, ty + (tag.height if ty < yv else 0))], fill=CC[colname] + (200,), width=2)
                lay.alpha_composite(tag, (int(tx), int(ty)))
        # cop di hujung
        st = self.c.get("stamp")
        if st and t1 <= t < t1 + 2.0:
            text, colname, emo = st
            e = seg(t, t1, t1 + 0.22); s = 2.4 - 1.4 * ease(e)
            stp = scaled(self._stamp(text, CC[colname], emo), s)
            fa = 1 - seg(t, t1 + 1.5, t1 + 2.0)
            if stp.width <= W:
                put(lay, stp, (W - stp.width) / 2, top + self.h / 2 - stp.height / 2 + 20, fa)
            if self.c.get("stamp_flash", True) and e < 1:
                fl = Image.new("RGBA", lay.size, CC[colname] + (int(90 * (1 - e)),)); lay.alpha_composite(fl)
        ent = ease(seg(t, 0.2, 0.7))
        warp3d(img, lay, W / 2, self.top + lay.height / 2 + 60 * (1 - ent), rx=55 * (1 - ent), a=alpha * ent)
        return stamp_k

    def _tag(self, text, col, emo):
        k = (text, col, emo)
        if not hasattr(self, "_tc"): self._tc = {}
        if k in self._tc: return self._tc[k]
        f = font("ExtraBold", 30); tw = f.getlength(text); em = emoji(emo, 40) if emo else None
        w = int(tw + 40 + (em.width + 10 if em else 0)); h = 60
        im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
        d.rounded_rectangle([0, 0, w - 1, h - 1], 30, fill=(10, 10, 16, 235), outline=col + (255,), width=3)
        x = 18
        if em: im.alpha_composite(em, (x, (h - em.height) // 2)); x += em.width + 10
        d.text((x, 13), text, font=f, fill=WHITE)
        self._tc[k] = im; return im

    def _stamp(self, text, col, emo):
        k = ("stamp", text)
        if not hasattr(self, "_tc"): self._tc = {}
        if k in self._tc: return self._tc[k]
        f = font("Black", 76) if False else font("ExtraBold", 76)
        em = emoji(emo, 90) if emo else None
        tw = f.getlength(text); w = int(min(900, tw + 80 + (em.width + 20 if em else 0))); h = 150
        if tw + 80 + (em.width + 20 if em else 0) > 900:
            f = font("ExtraBold", int(76 * (900 - 80 - (em.width + 20 if em else 0)) / tw)); tw = f.getlength(text)
        im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
        d.rounded_rectangle([4, 4, w - 5, h - 5], 24, fill=(10, 10, 16, 200), outline=col + (255,), width=8)
        x = (w - tw - (em.width + 20 if em else 0)) / 2
        if em: im.alpha_composite(em, (int(x), (h - em.height) // 2)); x += em.width + 20
        asc, desc = f.getmetrics(); d.text((x, (h - asc - desc) / 2), text, font=f, fill=col)
        im = im.rotate(-6, Image.BICUBIC, expand=True)
        self._tc[k] = im; return im

    def _scale(self, d, t, p):
        """Neraca halal/haram yang berayun (topik syariah)."""
        cx, cy = W / 2, 150
        ang = math.radians(12 * math.sin(t * 2.2) * (1 - 0.6 * p))
        L = 300
        d.polygon([(cx - 60, cy + 200), (cx + 60, cy + 200), (cx, cy + 10)], fill=GOLD + (255,))
        d.rectangle([cx - 8, cy, cx + 8, cy + 200], fill=GOLD + (255,))
        ex = (math.cos(ang) * L, math.sin(ang) * L)
        a_ = (cx - ex[0], cy - ex[1]); b_ = (cx + ex[0], cy + ex[1])
        d.line([a_, b_], fill=GOLD + (255,), width=10)
        d.ellipse([cx - 18, cy - 18, cx + 18, cy + 18], fill=WHITE)
        for (px, py), txt, col in ((a_, "HALAL?", GREEN), (b_, "HARAM?", RED)):
            d.line([(px, py), (px - 70, py + 90)], fill=GOLD + (200,), width=3); d.line([(px, py), (px + 70, py + 90)], fill=GOLD + (200,), width=3)
            d.chord([px - 90, py + 50, px + 90, py + 130], 0, 180, fill=col + (230,))
            f = font("ExtraBold", 34); d.text((px - f.getlength(txt) / 2, py + 2 + 120), txt, font=f, fill=col)
