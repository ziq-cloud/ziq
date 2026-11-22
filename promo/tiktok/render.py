"""Render 9:16 TikTok videos: screen footage + hook title + word-synced captions + voice + music.
Usage: python3 render.py [video_key ...]   (needs voice/<key>.mp3 + .align.json, music/<name>.mp3)
"""
import json, os, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
PROMO = os.path.dirname(HERE)
W, H, FPS = 1080, 1920, 30
FW, FH, FX, FY = 900, 1180, 90, 500  # footage card
FD = "/usr/share/fonts/opentype/inter/"
GOLD, GOLD_HI, WHITE, MUTED, BLACK = (226, 178, 92), (255, 222, 140), (255, 255, 255), (185, 175, 160), (8, 7, 6)
_fc = {}
def font(w, s):
    if (w, s) not in _fc: _fc[(w, s)] = ImageFont.truetype(FD + f"Inter-{w}.otf", s)
    return _fc[(w, s)]

def ease(t): t = max(0., min(1., t)); return 1 - (1 - t) ** 3

def src_path(name):
    for p in (os.path.join(PROMO, "assets/rec", name), os.path.join(PROMO, "assets/screens", name), os.path.join(HERE, "src", name)):
        if os.path.exists(p): return p
    raise FileNotFoundError(name)

# ---------- captions from ElevenLabs character alignment ----------
def words_from_alignment(al, t0):
    ch, st, en = al["characters"], al["character_start_times_seconds"], al["character_end_times_seconds"]
    words, cur = [], None
    for c, s, e in zip(ch, st, en):
        if c.isspace():
            if cur: words.append(cur); cur = None
            continue
        if cur is None: cur = [c, s, e]
        else: cur[0] += c; cur[2] = e
    if cur: words.append(cur)
    out = []  # merge spelled letters "Z I Q F X" -> "ZIQFX"
    for w in words:
        bare = w[0].strip(",.?!")
        if len(bare) == 1 and bare.isupper() and out and out[-1].get("spell"):
            out[-1]["w"] = out[-1]["w"].rstrip(",.?!") + w[0]; out[-1]["e"] = w[2]
        else:
            out.append({"w": w[0], "s": w[1], "e": w[2], "spell": len(bare) == 1 and bare.isupper()})
    for w in out: w["s"] += t0; w["e"] += t0
    return out

def chunk_words(words, maxc=20):
    chunks, cur = [], []
    for w in words:
        txt = " ".join(x["w"] for x in cur + [w])
        if cur and (len(txt) > maxc or cur[-1]["w"][-1] in ",.?!"):
            chunks.append(cur); cur = []
        cur.append(w)
    if cur: chunks.append(cur)
    for i, c in enumerate(chunks):
        c_end = chunks[i + 1][0]["s"] if i + 1 < len(chunks) else c[-1]["e"] + 0.6
        for w in c: w["chunk_end"] = c_end
    return chunks

def clean(w): return w.rstrip(",.")

def draw_caption(img, chunk, t, y):
    f = font("Black", 76)
    toks = [clean(w["w"]) for w in chunk]
    widths = [f.getlength(s) for s in toks]; sp = f.getlength(" ")
    total = sum(widths) + sp * (len(toks) - 1)
    pop = ease((t - chunk[0]["s"]) / 0.12)
    d = ImageDraw.Draw(img)
    pad = 28; x0 = (W - total) / 2
    box = Image.new("RGBA", (int(total + pad * 2), 120), (0, 0, 0, int(165 * pop)))
    m = Image.new("L", box.size, 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, box.width - 1, box.height - 1], 26, fill=255)
    img.paste(box, (int(x0 - pad), int(y - 18)), m)
    x = x0
    for w, s, wd in zip(chunk, toks, widths):
        col = GOLD_HI if w["s"] <= t < w["e"] + 0.05 else WHITE
        d.text((x, y + (1 - pop) * 14), s, font=f, fill=col, stroke_width=4, stroke_fill=(0, 0, 0))
        x += wd + sp

# ---------- text helpers ----------
def wrap(text, f, maxw):
    lines = []
    for para in text.split("\n"):
        cur = ""
        for w in para.split():
            t = (cur + " " + w).strip()
            if f.getlength(t) <= maxw or not cur: cur = t
            else: lines.append(cur); cur = w
        lines.append(cur)
    return lines

def ctext(d, y, s, f, fill, stroke=0):
    x = (W - f.getlength(s)) / 2
    d.text((x, y), s, font=f, fill=fill, stroke_width=stroke, stroke_fill=(0, 0, 0))

def rounded_mask(size, r):
    m = Image.new("L", size, 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, size[0] - 1, size[1] - 1], r, fill=255); return m

# ---------- footage ----------
def shot_frames(src, ss, dur, y0, y1, speed=1.0):
    """Yield FW x FH RGB frames: source scaled to width FW, vertical window panning y0 -> y1 (px in scaled space)."""
    n = int(round(dur * FPS))
    vf = (f"setpts=PTS/{speed}," if speed != 1 else "") + f"fps={FPS},scale={FW}:-2"
    inp = ["-loop", "1", "-i", src_path(src)] if src.endswith(".png") else ["-ss", str(ss), "-i", src_path(src)]
    p = subprocess.Popen(["ffmpeg", "-v", "error", *inp, "-t", str(dur + 0.5), "-vf", vf,
                          "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    probe = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height",
                            "-of", "csv=p=0", src_path(src)], capture_output=True, text=True).stdout.split(",")
    sw, sh = int(probe[0]), int(probe[1].split()[0])
    hh = int(round(sh * FW / sw / 2) * 2)
    last = None
    for i in range(n):
        buf = p.stdout.read(FW * hh * 3)
        if len(buf) == FW * hh * 3: last = np.frombuffer(buf, np.uint8).reshape(hh, FW, 3)
        k = i / max(1, n - 1); k = k * k * (3 - 2 * k)
        y = int(min(max(0, y0 + (y1 - y0) * k), hh - FH))
        yield Image.fromarray(last[y:y + FH])
    p.stdout.close(); p.wait()

def background(fr):
    bg = fr.resize((W, int(W * FH / FW))).resize((W, H)).filter(ImageFilter.GaussianBlur(40))
    return Image.blend(bg, Image.new("RGB", (W, H), BLACK), 0.72)

CARD_MASK = rounded_mask((FW, FH), 36)

# ---------- end card ----------
LOGOS = {}
def load_logo(name):
    if name not in LOGOS:
        im = Image.open(os.path.join(HERE, "src", name) if os.path.exists(os.path.join(HERE, "src", name))
                        else os.path.join(PROMO, "assets", name)).convert("RGBA")
        LOGOS[name] = im.crop(im.getbbox())
    return LOGOS[name]

def end_card(img, t, t0, cfg):
    a = ease((t - t0) / 0.35)
    if a <= 0: return
    ov = Image.new("RGBA", (W, H), BLACK + (int(235 * a),))
    img.alpha_composite(ov)
    d = ImageDraw.Draw(img)
    y = 290
    logos = cfg["end_logos"]
    lw = 300 if len(logos) == 1 else 280
    xs = [W / 2] if len(logos) == 1 else [W / 2 - 200, W / 2 + 200]
    for name, cx in zip(logos, xs):
        lg = load_logo(name); s = lw / max(lg.width, lg.height)
        lg = lg.resize((int(lg.width * s), int(lg.height * s)), Image.LANCZOS)
        sc = 0.85 + 0.15 * ease((t - t0) / 0.5)
        lg = lg.resize((max(1, int(lg.width * sc)), max(1, int(lg.height * sc))), Image.LANCZOS)
        if a < 1: lg.putalpha(lg.getchannel("A").point(lambda v: int(v * a)))
        img.alpha_composite(lg, (int(cx - lg.width / 2), int(y + 160 - lg.height / 2)))
    y = 680
    for blk in cfg["end_lines"]:
        kind, txt = blk
        b = ease((t - t0 - 0.25) / 0.35)
        if kind == "h":
            for ln in wrap(txt, font("Black", 74), 940):
                ctext(d, y, ln, font("Black", 74), WHITE); y += 92
            y += 20
        elif kind == "code":
            f = font("Black", 110); tw = f.getlength(txt)
            bx = [(W - tw) / 2 - 50, y, (W + tw) / 2 + 50, y + 170]
            d.rounded_rectangle(bx, 30, outline=GOLD, width=6, fill=(30, 24, 14))
            ctext(d, y + 22, txt, f, GOLD_HI); y += 210
        elif kind == "s":
            for ln in wrap(txt, font("SemiBold", 46), 940):
                ctext(d, y, ln, font("SemiBold", 46), GOLD); y += 62
            y += 14
    for i, ln in enumerate(wrap("Trading melibatkan risiko tinggi kerugian. Bukan nasihat kewangan.", font("Medium", 32), 860)):
        ctext(d, 1350 + i * 44, ln, font("Medium", 32), MUTED)

# ---------- render ----------
def render(key, cfg):
    al = json.load(open(os.path.join(HERE, "voice", key + ".align.json")))
    V0 = 0.35
    words = words_from_alignment(al, V0)
    chunks = chunk_words(words)
    vend = words[-1]["e"]
    total = vend + 1.8
    cta_t = next(w["s"] for w in words if w["w"].strip(",.?!") == cfg["cta_word"] and w["s"] > vend * 0.55) - 0.1
    # distribute shots over [0, cta_t]
    shots = cfg["shots"]; wsum = sum(s.get("w", 1) for s in shots)
    plan, t = [], 0.0
    for s in shots:
        d = cta_t * s.get("w", 1) / wsum + (total - cta_t if s is shots[-1] else 0)
        plan.append((s, t, d)); t += d
    out = os.path.join(HERE, "out", key + ".mp4"); os.makedirs(os.path.dirname(out), exist_ok=True)
    silent = out + ".video.mp4"
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                            "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p", silent],
                           stdin=subprocess.PIPE)
    hook_f = font("Black", 84)
    hook_lines = wrap(cfg["hook"], hook_f, 960)
    ci = 0; n = 0; cover = None
    for s, st, dur in plan:
        bg = None
        for fr in shot_frames(s["src"], s.get("ss", 0), dur, s.get("y0", 0), s.get("y1", s.get("y0", 0)), s.get("speed", 1.0)):
            tt = n / FPS
            if bg is None: bg = background(fr)
            img = bg.copy().convert("RGBA")
            # footage card with gold edge, slight zoom-in on cut
            z = 1 + 0.04 * (1 - ease((tt - st) / 0.4))
            card = fr.resize((int(FW * z), int(FH * z))).crop((int(FW * (z - 1) / 2), int(FH * (z - 1) / 2), int(FW * (z - 1) / 2) + FW, int(FH * (z - 1) / 2) + FH))
            d = ImageDraw.Draw(img)
            d.rounded_rectangle([FX - 4, FY - 4, FX + FW + 3, FY + FH + 3], 40, fill=GOLD)
            img.paste(card, (FX, FY), CARD_MASK)
            # top disclaimer + hook
            ctext(d, 150, "Trading berisiko tinggi  ·  Bukan nasihat kewangan", font("Medium", 28), MUTED)
            ha = ease(tt / 0.4)
            y = 215
            for i, ln in enumerate(hook_lines):
                col = GOLD_HI if i == len(hook_lines) - 1 else WHITE
                ctext(d, y + (1 - ha) * 20, ln, hook_f, col, stroke=3); y += 100
            # tag chip
            if cfg.get("tag"):
                f = font("Bold", 34); tw = f.getlength(cfg["tag"])
                d.rounded_rectangle([FX + 24, FY + 24, FX + 24 + tw + 44, FY + 24 + 62], 31, fill=(0, 0, 0, 200), outline=GOLD, width=3)
                d.text((FX + 46, FY + 35), cfg["tag"], font=f, fill=GOLD_HI)
            end_card(img, tt, cta_t, cfg)
            while ci < len(chunks) and tt >= chunks[ci][-1]["chunk_end"]: ci += 1
            if ci < len(chunks) and tt >= chunks[ci][0]["s"] - 0.05:
                draw_caption(img, chunks[ci], tt, 1450 if tt < cta_t else 1580)
            rgb = img.convert("RGB")
            if cover is None and tt >= 1.2: cover = rgb.copy()
            enc.stdin.write(rgb.tobytes()); n += 1
    enc.stdin.close(); enc.wait()
    cover.save(os.path.join(HERE, "out", key + "_cover.jpg"), quality=90)
    # audio: voice + ducked music
    mus = os.path.join(HERE, "music", cfg["music"] + ".mp3")
    voice = os.path.join(HERE, "voice", key + ".mp3")
    dur = n / FPS
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", silent, "-i", voice, "-stream_loop", "-1", "-i", mus,
                    "-filter_complex",
                    f"[1:a]adelay={int(V0*1000)}|{int(V0*1000)},volume=1.15[v];"
                    f"[2:a]atrim=0:{dur},volume=0.16,afade=t=in:d=0.6,afade=t=out:st={dur-1.6}:d=1.6[m];"
                    f"[v][m]amix=inputs=2:duration=longest:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=11,atrim=0:{dur}[a]",
                    "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "44100",
                    "-movflags", "+faststart", out], check=True)
    os.remove(silent)
    print(f"{key}: {dur:.1f}s -> {out}")

if __name__ == "__main__":
    cfgs = json.load(open(os.path.join(HERE, "videos.json")))
    for k in (sys.argv[1:] or list(cfgs)):
        render(k, cfgs[k])
