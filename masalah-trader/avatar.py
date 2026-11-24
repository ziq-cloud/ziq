"""Watak pembentang gaya 3D (berlorek) yang dijana secara prosedur - tiada aset luar.

Mulut bergerak ikut amplitud suara, mata berkelip, kepala bergoyang/angguk perlahan.
Avatar(size).render(t, mouth_open, energy) -> RGBA
"""
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

SS = 2  # supersampling untuk anti-alias
LIGHT = np.array([-0.45, -0.55, 0.70]); LIGHT = LIGHT / np.linalg.norm(LIGHT)

# warna diambil dari gambar rujukan (kulit sawo matang, rambut hitam, baju Melayu hitam satin)
SKIN = np.array([184, 130, 100], float)
HAIR = np.array([30, 28, 28], float)
SUIT = np.array([44, 44, 50], float)
SILVER = (214, 218, 226)


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


def lump(w, h, color, ang=0.0, spec=0.45, amb=0.55):
    im = shaded_ellipse(w, h, color, spec=spec, amb=amb)
    return im.rotate(ang, Image.BICUBIC, expand=True) if ang else im


class Avatar:
    """Karikatur 3D berdasarkan rupa pemilik: rambut hitam bervolume disisir ke tepi, misai nipis,
    senyum lebar, baju Melayu hitam satin dengan butang perak dan rantai poket."""

    def __init__(self, width=340):
        s = width / 360 * SS; self.s = s
        W, H = int(360 * s), int(470 * s); self.size = (W, H)
        P = lambda v: int(v * s); self.P = P

        # --- badan: baju Melayu hitam satin ---
        body = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        body.alpha_composite(shaded_ellipse(P(350), P(300), SUIT, spec=0.55, amb=0.5, rim=0.3), (P(5), P(330)))
        body.alpha_composite(shaded_ellipse(P(72), P(100), SKIN * 0.82, spec=0.05, cyl=True), (P(144), P(258)))
        d = ImageDraw.Draw(body)
        dark = tuple((SUIT * 0.7).astype(int)); light = tuple((SUIT * 1.5).astype(int))
        # kolar cekak musang
        d.rounded_rectangle([P(140), P(330), P(220), P(352)], P(8), fill=tuple((SUIT * 0.95).astype(int)), outline=dark, width=P(2))
        # belahan butang + butang perak
        d.rectangle([P(171), P(354), P(189), P(470)], fill=tuple((SUIT * 1.1).astype(int)))
        d.line([(P(171), P(354)), (P(171), P(470))], fill=dark, width=P(2))
        for by in (340, 372, 404, 436):
            d.ellipse([P(175), P(by - 5), P(185), P(by + 5)], fill=SILVER, outline=(140, 145, 155), width=P(1))
        # poket + rantai perak
        d.line([(P(236), P(428)), (P(300), P(422))], fill=dark, width=P(3))
        pts = [(P(180 + (262 - 180) * k / 20), P(404 + (424 - 404) * k / 20 + 26 * math.sin(math.pi * k / 20))) for k in range(21)]
        d.line(pts, fill=SILVER, width=P(3), joint="curve")
        d.ellipse([P(258), P(418), P(268), P(430)], fill=(90, 130, 110))
        # kilauan satin pada bahu
        sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(sh).ellipse([P(40), P(345), P(120), P(380)], fill=(255, 255, 255, 40))
        body.alpha_composite(sh.filter(ImageFilter.GaussianBlur(P(8))))
        self.body = body

        # --- kepala ---
        head = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        for ex in (P(64), P(260)):
            head.alpha_composite(shaded_ellipse(P(36), P(56), SKIN * 0.9, spec=0.1), (ex, P(165)))
        head.alpha_composite(shaded_ellipse(P(236), P(248), SKIN, spec=0.25, rim=0.08), (P(62), P(60)))
        head.alpha_composite(self.hair(W, H, P))
        # pipi, hidung
        fx = Image.new("RGBA", (W, H), (0, 0, 0, 0)); fd = ImageDraw.Draw(fx)
        for cx in (P(118), P(242)):
            fd.ellipse([cx - P(24), P(236), cx + P(24), P(262)], fill=(205, 105, 95, 28))
        fd.ellipse([P(176), P(200), P(198), P(252)], fill=(110, 62, 44, 60))
        for nx_ in (P(166), P(194)):
            fd.ellipse([nx_ - P(10), P(240), nx_ + P(10), P(254)], fill=(95, 52, 38, 110))
        fd.ellipse([P(172), P(212), P(180), P(236)], fill=(255, 220, 195, 70))
        # garis senyum (nasolabial)
        fd.arc([P(118), P(240), P(168), P(310)], 160, 230, fill=(120, 70, 52, 90), width=P(3))
        fd.arc([P(192), P(240), P(242), P(310)], 310, 20, fill=(120, 70, 52, 90), width=P(3))
        head.alpha_composite(fx.filter(ImageFilter.GaussianBlur(P(3))))
        # misai nipis
        ms = Image.new("RGBA", (W, H), (0, 0, 0, 0)); md = ImageDraw.Draw(ms)
        md.polygon([(P(146), P(274)), (P(160), P(263)), (P(180), P(266)), (P(200), P(263)), (P(214), P(274)),
                    (P(200), P(268)), (P(180), P(271)), (P(160), P(268))], fill=(26, 20, 18, 220))
        md.ellipse([P(174), P(312), P(186), P(320)], fill=(40, 28, 24, 90))  # janggut kecil bawah bibir
        head.alpha_composite(ms.filter(ImageFilter.GaussianBlur(P(1.2))))
        self.head = head

        shd = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(shd).ellipse([P(30), P(60), P(330), P(470)], fill=(0, 0, 0, 120))
        self.shadow = shd.filter(ImageFilter.GaussianBlur(P(24)))

    @staticmethod
    def hair(W, H, P):
        """Rambut sebagai satu bentuk 'inflated': siluet -> peta tinggi -> lorek 3D + alur helaian."""
        m = Image.new("L", (W, H), 0); d = ImageDraw.Draw(m)
        d.ellipse([P(58), P(12), P(302), P(128)], fill=255)                       # mahkota
        # juntai kanan: sapuan panjang ke tepi, hujung tajam jatuh dekat telinga
        d.polygon([(P(150), P(22)), (P(250), P(30)), (P(304), P(80)), (P(320), P(140)), (P(312), P(200)),
                   (P(300), P(170)), (P(292), P(186)), (P(280), P(150)), (P(262), P(152)), (P(240), P(132)),
                   (P(214), P(142)), (P(196), P(120)), (P(172), P(124)), (P(160), P(100))], fill=255)
        # juntai kiri: curtain jatuh ke paras kening, berhujung tajam
        d.polygon([(P(152), P(26)), (P(96), P(40)), (P(56), P(92)), (P(50), P(168)), (P(64), P(150)),
                   (P(72), P(178)), (P(88), P(140)), (P(104), P(166)), (P(118), P(136)), (P(132), P(146)),
                   (P(142), P(112)), (P(150), P(80))], fill=255)
        d.rectangle([P(62), P(110), P(80), P(178)], fill=255); d.rectangle([P(282), P(110), P(300), P(178)], fill=255)
        mask = np.array(m.filter(ImageFilter.GaussianBlur(P(1.5)))).astype(np.float32) / 255
        h = np.array(m.filter(ImageFilter.GaussianBlur(P(22)))).astype(np.float32) / 255
        # alur helaian mengikut arah sapuan
        g = Image.new("L", (W, H), 0); gd = ImageDraw.Draw(g)
        for k in range(-5, 8):  # helaian ke kanan
            gd.arc([P(150 + k * 22 - 120), P(28), P(150 + k * 22 + 160), P(300)], 205, 290, fill=255, width=P(4))
        for k in range(4):      # helaian ke kiri
            gd.arc([P(60 + k * 20), P(36), P(240 + k * 20), P(320)], 250, 300, fill=255, width=P(4))
        h -= np.array(g.filter(ImageFilter.GaussianBlur(P(4)))).astype(np.float32) / 255 * 0.08
        gy, gx = np.gradient(h * P(60))
        n = np.dstack([-gx, -gy, np.ones_like(h)]); n /= np.linalg.norm(n, axis=2, keepdims=True)
        diff = np.clip((n * LIGHT).sum(2), 0, 1)
        hv = LIGHT + np.array([0, 0, 1.0]); hv /= np.linalg.norm(hv)
        sp = np.clip((n * hv).sum(2), 0, 1) ** 40 * 0.35
        rgb = HAIR[None, None] * (0.55 + 0.7 * diff)[..., None] + 255 * sp[..., None]
        return Image.fromarray(np.dstack([rgb.clip(0, 255), mask * 255]).astype(np.uint8), "RGBA")

    def blink(self, t):
        ph = (t + 0.7) % 3.7
        return 1 - abs(ph - 0.08) / 0.08 if ph < 0.16 else 0.0

    def render(self, t, mouth, energy=0.0):
        P = self.P; W, H = self.size
        head = self.head.copy(); d = ImageDraw.Draw(head)
        bl = self.blink(t); brow = P(4) * energy; look = math.sin(t * 0.6) * P(3)
        skin = tuple(SKIN.astype(int))
        for ex in (P(138), P(222)):
            ey = P(204); eh = max(P(1.5), P(7.5) * (1 - bl))
            d.ellipse([ex - P(18), ey - eh, ex + P(18), ey + eh], fill=(248, 244, 238))
            if bl < 0.7:
                d.ellipse([ex - P(9) + look, ey - P(9), ex + P(9) + look, ey + P(9)], fill=(58, 36, 24))
                d.ellipse([ex - P(4.5) + look, ey - P(4.5), ex + P(4.5) + look, ey + P(4.5)], fill=(10, 8, 6))
                d.ellipse([ex - P(6) + look, ey - P(6), ex - P(2) + look, ey - P(2)], fill=(255, 255, 255))
            d.arc([ex - P(20), ey - P(6), ex + P(20), ey + P(14)], 20, 160, fill=(120, 72, 52), width=P(2))  # kelopak bawah
            d.arc([ex - P(20), ey - P(12), ex + P(20), ey + P(12)], 200, 340, fill=(40, 26, 20), width=P(3))
            d.line([(ex - P(24), ey - P(22) - brow), (ex, ey - P(28) - brow), (ex + P(24), ey - P(25) - brow)],
                   fill=(22, 18, 16), width=P(8), joint="curve")
        # mulut: senyum lebar nampak gigi, buka ikut suara
        mx, my = P(180), P(286); o = max(0.0, min(1.0, mouth))
        mw = P(36) + P(4) * o; up = P(4); dn = P(14) + P(22) * o
        d.chord([mx - mw, my - up - dn * 0.25, mx + mw, my + dn], 0, 180, fill=(70, 22, 28))
        d.chord([mx - mw * 0.92, my - up - P(8), mx + mw * 0.92, my + P(10) + P(2) * o], 0, 180, fill=(246, 244, 238))
        if o > 0.3:
            d.ellipse([mx - mw * 0.5, my + dn * 0.45, mx + mw * 0.5, my + dn * 0.95], fill=(190, 92, 96))
        d.line([(mx - mw - P(2), my - up + P(1)), (mx + mw + P(2), my - up + P(1))], fill=(150, 80, 72), width=P(3))
        d.arc([mx - mw, my - up - dn * 0.25, mx + mw, my + dn + P(2)], 10, 170, fill=(160, 96, 86), width=P(3))
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
        out.putalpha(Image.fromarray(np.minimum(np.array(out.getchannel("A")), np.array(self._fade))))
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
