"""Watak pembentang gaya 3D (berlorek) yang dijana secara prosedur - tiada aset luar.

Mulut bergerak ikut amplitud suara, mata berkelip, kepala bergoyang/angguk perlahan.
Avatar(size).render(t, mouth_open, energy) -> RGBA
"""
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

SS = 2  # supersampling untuk anti-alias
LIGHT = np.array([-0.45, -0.55, 0.70]); LIGHT = LIGHT / np.linalg.norm(LIGHT)

SKIN = np.array([206, 150, 112], float)
HAIR = np.array([28, 22, 20], float)
SUIT = np.array([30, 40, 68], float)
SHIRT = np.array([236, 238, 244], float)
TIE = np.array([214, 160, 70], float)


def shaded_ellipse(w, h, color, spec=0.35, amb=0.42, cyl=False, rim=0.0):
    """Ellipsoid (atau silinder jika cyl) dengan lorek diffuse + specular -> RGBA."""
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    nx = (xx + 0.5 - w / 2) / (w / 2); ny = (yy + 0.5 - h / 2) / (h / 2)
    r2 = nx ** 2 + (0 if cyl else ny ** 2)
    inside = (nx ** 2 + ny ** 2 <= 1) if not cyl else (np.abs(nx) <= 1)
    nz = np.sqrt(np.clip(1 - r2, 0, 1))
    nyy = np.zeros_like(ny) if cyl else ny
    diff = np.clip(nx * LIGHT[0] + nyy * LIGHT[1] + nz * LIGHT[2], 0, 1)
    # specular (Blinn)
    hv = LIGHT + np.array([0, 0, 1.0]); hv /= np.linalg.norm(hv)
    sp = np.clip(nx * hv[0] + nyy * hv[1] + nz * hv[2], 0, 1) ** 28 * spec
    rimv = (1 - nz) ** 3 * rim
    rgb = color[None, None, :] * (amb + 0.68 * diff)[..., None] + 255 * (sp + rimv)[..., None]
    a = inside.astype(np.float32)
    # tepi lembut
    edge = np.clip((1 - np.sqrt(nx ** 2 + (0 if cyl else ny ** 2))) * min(w, h) / 2.5, 0, 1) if not cyl else 1
    out = np.dstack([rgb.clip(0, 255), (a * edge * 255)]).astype(np.uint8)
    return Image.fromarray(out, "RGBA")


class Avatar:
    def __init__(self, width=340):
        self.w0 = width
        s = width / 360 * SS; self.s = s
        W, H = int(360 * s), int(470 * s); self.size = (W, H)
        P = lambda v: int(v * s)
        self.P = P
        # --- badan (statik) ---
        body = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        torso = shaded_ellipse(P(340), P(300), SUIT, spec=0.15, rim=0.25)
        body.alpha_composite(torso, (P(10), P(330)))
        neck = shaded_ellipse(P(70), P(110), SKIN * 0.85, spec=0.05, cyl=True)
        body.alpha_composite(neck, (P(145), P(255)))
        d = ImageDraw.Draw(body)
        d.polygon([(P(132), P(338)), (P(228), P(338)), (P(180), P(430))], fill=tuple(SHIRT.astype(int)))  # kolar
        d.polygon([(P(170), P(352)), (P(190), P(352)), (P(197), P(470)), (P(180), P(480)), (P(163), P(470))],
                  fill=tuple(TIE.astype(int)))
        d.polygon([(P(166), P(340)), (P(194), P(340)), (P(188), P(356)), (P(172), P(356))], fill=tuple((TIE * 0.8).astype(int)))
        # lapel
        d.polygon([(P(132), P(338)), (P(160), P(338)), (P(176), P(440)), (P(110), P(370))], fill=tuple((SUIT * 1.25).astype(int)))
        d.polygon([(P(228), P(338)), (P(200), P(338)), (P(184), P(440)), (P(250), P(370))], fill=tuple((SUIT * 1.15).astype(int)))
        self.body = body
        # --- kepala (statik: muka + telinga + rambut) ---
        head = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        for ex in (P(66), P(258)):
            head.alpha_composite(shaded_ellipse(P(38), P(58), SKIN * 0.92, spec=0.1), (ex, P(160)))
        face = shaded_ellipse(P(214), P(254), SKIN, spec=0.22, rim=0.08)
        head.alpha_composite(face, (P(73), P(52)))
        # rambut: ellipsoid gelap, dipotong dengan garis rambut
        hair = shaded_ellipse(P(232), P(200), HAIR, spec=0.5, amb=0.6)
        ha = np.array(hair); hh, hw = ha.shape[:2]
        yy, xx = np.mgrid[0:hh, 0:hw]
        line = P(78) + (np.abs(xx - hw / 2) / (hw / 2)) ** 2 * P(70) - np.sin(xx / hw * 7) * P(6)
        ha[..., 3] = np.where(yy < line, ha[..., 3], 0)
        hair = Image.fromarray(ha)
        head.alpha_composite(hair, (P(64), P(30)))
        # pipi kemerahan
        blush = Image.new("RGBA", (W, H), (0, 0, 0, 0)); bd = ImageDraw.Draw(blush)
        for cx in (P(122), P(238)):
            bd.ellipse([cx - P(22), P(232), cx + P(22), P(256)], fill=(220, 110, 100, 60))
        head.alpha_composite(blush.filter(ImageFilter.GaussianBlur(P(8))))
        # hidung: bayang + highlight
        nose = Image.new("RGBA", (W, H), (0, 0, 0, 0)); nd = ImageDraw.Draw(nose)
        nd.ellipse([P(178), P(205), P(200), P(252)], fill=(120, 70, 50, 70))
        nd.ellipse([P(168), P(232), P(196), P(252)], fill=(110, 62, 44, 90))
        head.alpha_composite(nose.filter(ImageFilter.GaussianBlur(P(5))))
        hl = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(hl).ellipse([P(172), P(214), P(180), P(236)], fill=(255, 225, 200, 90))
        head.alpha_composite(hl.filter(ImageFilter.GaussianBlur(P(2))))
        self.head = head
        # bayang lembut di bawah avatar
        sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(sh).ellipse([P(30), P(60), P(330), P(470)], fill=(0, 0, 0, 120))
        self.shadow = sh.filter(ImageFilter.GaussianBlur(P(24)))

    def blink(self, t):
        ph = (t + 0.7) % 3.7
        if ph < 0.16: return 1 - abs(ph - 0.08) / 0.08
        return 0.0

    def render(self, t, mouth, energy=0.0):
        P = self.P; W, H = self.size
        head = self.head.copy(); d = ImageDraw.Draw(head)
        bl = self.blink(t)
        brow = P(4) * energy
        look = math.sin(t * 0.6) * P(3)
        for ex in (P(140), P(220)):
            ey = P(196)
            eh = max(P(1.5), P(12) * (1 - bl))
            d.ellipse([ex - P(18), ey - eh, ex + P(18), ey + eh], fill=(250, 248, 244))
            if bl < 0.7:
                ir = P(10)
                d.ellipse([ex - ir + look, ey - ir, ex + ir + look, ey + ir], fill=(70, 42, 26))
                d.ellipse([ex - P(5) + look, ey - P(5), ex + P(5) + look, ey + P(5)], fill=(12, 8, 6))
                d.ellipse([ex - P(6) + look, ey - P(7), ex - P(1) + look, ey - P(2)], fill=(255, 255, 255))
            # kelopak mata atas
            d.arc([ex - P(20), ey - P(14), ex + P(20), ey + P(14)], 200, 340, fill=(60, 36, 28), width=P(3))
            # kening
            d.line([(ex - P(22), ey - P(26) - brow), (ex, ey - P(32) - brow), (ex + P(22), ey - P(28) - brow)],
                   fill=(30, 22, 18), width=P(7), joint="curve")
        # mulut
        mx, my = P(180), P(276)
        o = max(0.0, min(1.0, mouth))
        mw = P(26) + P(6) * o
        if o < 0.08:
            d.arc([mx - P(28), my - P(14), mx + P(28), my + P(8)], 20, 160, fill=(120, 52, 48), width=P(4))
        else:
            mh = P(3) + P(24) * o
            d.ellipse([mx - mw, my - mh * 0.45, mx + mw, my + mh], fill=(84, 28, 34))
            if o > 0.25:  # gigi atas + lidah
                d.chord([mx - mw * 0.8, my - mh * 0.45, mx + mw * 0.8, my + mh * 0.35], 180, 360, fill=(245, 242, 236))
                d.ellipse([mx - mw * 0.55, my + mh * 0.35, mx + mw * 0.55, my + mh * 0.95], fill=(196, 92, 96))
            d.arc([mx - mw - P(2), my - mh * 0.45 - P(2), mx + mw + P(2), my + mh + P(2)], 0, 360,
                  fill=(150, 70, 62), width=P(3))
        # gerakan kepala: goyang + angguk ikut tenaga suara
        ang = 2.2 * math.sin(t * 1.25) + 1.5 * math.sin(t * 0.53) + 3.0 * energy * math.sin(t * 7)
        head = head.rotate(ang, Image.BICUBIC, center=(W / 2, P(320)))
        out = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        out.alpha_composite(self.shadow)
        breath = int(P(2) * math.sin(t * 1.8))
        out.alpha_composite(self.body, (0, breath))
        out.alpha_composite(head, (int(P(2) * math.sin(t * 0.9)), int(-P(5) * energy + breath * 0.5)))
        out = out.resize((W // SS, H // SS), Image.LANCZOS)
        if not hasattr(self, "_fade"):
            h = out.height; g = np.clip((h - np.arange(h)) / (h * 0.16), 0, 1)
            self._fade = Image.fromarray((np.repeat(g[:, None], out.width, 1) * 255).astype(np.uint8))
        a = np.minimum(np.array(out.getchannel("A")), np.array(self._fade)); out.putalpha(Image.fromarray(a))
        return out


def mouth_track(voice, sr, fps, dur):
    """Amplitud RMS setiap frame -> (bukaan mulut 0..1, tenaga licin 0..1)."""
    n = int(dur * fps); hop = sr / fps
    v = np.concatenate([voice, np.zeros(int((dur + 1) * sr))])
    rms = np.array([np.sqrt(np.mean(v[int(k * hop):int((k + 1) * hop)] ** 2) + 1e-12) for k in range(n)])
    ref = np.percentile(rms[rms > 0.01], 90) if (rms > 0.01).any() else 1
    m = np.clip((rms - 0.012) / (ref - 0.012 + 1e-9), 0, 1) ** 0.8
    # pecahkan kepada "suku kata" supaya mulut buka-tutup, bukan terbuka terus
    jitter = 0.65 + 0.35 * np.abs(np.sin(np.arange(n) * 1.9))
    m = m * jitter
    sm = np.copy(m)
    for k in range(1, n): sm[k] = max(m[k], sm[k - 1] * 0.55)
    en = np.convolve(m, np.ones(12) / 12, "same")
    return sm, np.clip(en, 0, 1)
