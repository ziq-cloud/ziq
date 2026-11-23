"""ZIQFX news-outlook video (fundamental + technical + forecast) from a news text file in NEWS_TEMPLATE.md format.

Usage:
  python3 make_news.py parse   news/2026-11-25.md
  python3 make_news.py dry     news/2026-11-25.md       # estimated timeline, no voice credits
  python3 make_news.py preview news/2026-11-25.md tech:6 s1:8
  python3 make_news.py tts     news/2026-11-25.md       # ElevenLabs clips (shared sentence cache with make3)
  python3 make_news.py render  news/2026-11-25.md       # -> out/ZIQFX_XAUUSD_News_<date>.mp4
"""
import json, math, os, random, re, subprocess, sys, wave
from multiprocessing import Pool

import numpy as np
from PIL import Image, ImageDraw

import make as M
from make import (W, H, FPS, GOLD, GOLD2, RED, GREEN, AMBER, TEAL, WHITE, GREY, clamp, eo, eob, ap, sprite, comp, text,
                  text_w, wrap, para, rgba, rounded_mask, panel_frame, background, tri, warn_icon, check_box, pill, flash,
                  kicker, CH)
from make2 import typed, sweep_text, lightning, embers, post, Seg, out_of, read_wav
import make3 as M3
from make3 import clean, sentences, paragraphs, fnum, RNG, MONTHS, DAYS, bias_col, nice_step

HERE = M.HERE
WORK = os.path.join(HERE, "work_news")
OUT_DIR = os.path.join(HERE, "out")
SR = 44100
_map = os.path.join(HERE, "charts", "map.json")
H1MAP = json.load(open(_map))["h1"] if os.path.exists(_map) else None


# ============================================================ parse
def parse(path):
    raw = open(path, encoding="utf-8").read()
    secs = [[]]
    for line in raw.splitlines():
        if re.match(r"^\s*━{3,}", line):
            secs.append([])
        else:
            secs[-1].append(line)
    o = {"date": None, "time": None, "greeting": "Assalamualaikum fighters!", "news": "", "intro": [], "explain": [],
         "data": [], "fund": [], "tech": [], "levels": [], "bias": "", "last": None, "scen": [], "plan": [], "risk": [],
         "closing": []}
    for sec in secs:
        cl = [clean(l) for l in sec]
        hi = next((i for i, c in enumerate(cl) if c), 0)
        first = (cl[hi] if cl else "").upper()
        body_cl, body = cl[hi + 1:], sec[hi + 1:]
        if first.startswith("APA ITU"):
            for c in body_cl:
                m = re.match(r"^•\s*(.+?)\s*[—–-]\s+(.+)$", c)
                if m:
                    o["explain"].append((m[1], m[2]))
        elif first.startswith("DATA"):
            for c in body_cl:
                if c.startswith("•"):
                    name, _, rest = c.lstrip("• ").partition(":")
                    vals = {}
                    for part in rest.split("|"):
                        k, _, v = part.strip().partition(" ")
                        if k:
                            vals[k.lower()] = v.strip() or "—"
                    o["data"].append({"name": name.strip(), "prev": vals.get("previous", "—"), "fc": vals.get("forecast", "—"),
                                      "act": vals.get("actual")})
        elif "FUNDAMENTAL" in first:
            o["fund"] = [" ".join(p) for p in paragraphs(body)]
        elif "TECHNICAL" in first:
            for p in paragraphs(body):
                for c in p:
                    mb = re.match(r"^BIAS\s*:\s*(.+)$", c, re.I)
                    ml = re.match(r"^LAST PRICE\s*:\s*(.+)$", c, re.I)
                    mv = re.match(rf"^•\s*([^:]+):\s*{RNG}", c)
                    if mb:
                        o["bias"] = mb[1].strip()
                    elif ml:
                        o["last"] = fnum(ml[1])
                    elif mv:
                        o["levels"].append({"label": mv[1].strip(), "a": mv[2], "b": mv[3]})
                txt = [c for c in p if not re.match(r"^(BIAS|LAST PRICE)\s*:|^•", c, re.I)]
                if txt:
                    o["tech"].append(" ".join(txt))
        elif "FORECAST" in first or "SENARIO" in first:
            cur = None
            for c in body_cl:
                if not c:
                    continue
                ms = re.match(r"^SENARIO\s*(\d+)\s*[—–-]\s*(.+)$", c, re.I)
                mt = re.match(r"^Target\s*:\s*(.+)$", c, re.I)
                if ms:
                    cur = {"n": int(ms[1]), "title": ms[2].strip(), "desc": "", "tg": []}
                    o["scen"].append(cur)
                elif mt and cur:
                    cur["tg"] = [x.strip() for x in re.split(r"→|->|,", mt[1]) if re.search(r"\d", x)]
                elif cur:
                    cur["desc"] = (cur["desc"] + " " + c).strip()
        elif "TRADING PLAN" in first:
            o["plan"] = [c.lstrip("• ").strip() for c in body_cl if c.startswith("•")]
        elif "RISK" in first:
            for p in paragraphs(body):
                t = " ".join(p)
                (o["closing"] if t.lower().startswith("fighters") else o["risk"]).append(t)
        else:
            rest = []
            for l in sec:
                c = clean(l)
                md = re.search(rf"({'|'.join(DAYS)}),?\s*(\d{{1,2}})\s+({'|'.join(MONTHS)})\s+(\d{{4}})", c)
                mt = re.search(r"(\d{1,2}[:.]\d{2})\s*(AM|PM)", c, re.I)
                mn = re.match(r"^NEWS\s*:\s*(.+)$", c, re.I)
                if "NEWS OUTLOOK" in c.upper():
                    rest.append("")
                elif md and len(c) < 40:
                    o["date"] = (md[1], int(md[2]), md[3], int(md[4]))
                    rest.append("")
                elif mt and len(c) < 40:
                    o["time"] = (mt[1].replace(".", ":"), mt[2].upper())
                    rest.append("")
                elif mn:
                    o["news"] = mn[1].strip()
                    rest.append("")
                elif c.lower().startswith("assalamualaikum"):
                    o["greeting"] = c
                    rest.append("")
                else:
                    rest.append(l)
            o["intro"] += [" ".join(p) for p in paragraphs(rest)]
    return o


# ============================================================ narration
def say(s):
    s = re.sub(r"(\d+)\.(\d+)\s*%", lambda m: f"{m[1]} perpuluhan {' '.join(M3.DIG[int(c)] for c in m[2])} peratus", s)
    s = s.replace("%", " peratus").replace("YoY", "tahun ke tahun").replace("QoQ", "suku ke suku").replace("MoM", "bulan ke bulan")
    s = re.sub(r"\bPrevious\b", "sebelum ini", s)
    return M3.say(s)


def time_say(tm):
    if not tm:
        return ""
    hh, mm = tm[0].split(":")
    h = int(hh)
    part = {"AM": "pagi"}.get(tm[1], "malam" if h >= 7 or h == 12 else "petang")
    return f"jam {h}{'' if mm == '00' else ' ' + str(int(mm))} {part}"


def val_say(v):
    return "belum diumumkan" if v in ("—", "-", "", None) else v


def build(o):
    spec, data = [], {}
    dname, d, mon, yr = o["date"] if o["date"] else ("", 0, "", 0)
    when = f"{dname}, {d} {mon}" if o["date"] else ""
    spec.append(("hook", False, 0.8, [("h1", f"News high impact: {o['news']}."), ("h2", f"{when}, {time_say(o['time'])}.".strip(", "))]))
    spec.append(("intro", False, 0.5, [("i1", "Zik F X. XAU USD news outlook.")]))
    intro = [s for p in o["intro"] for s in sentences(p)]
    spec.append(("open", True, 0.8, [("g1", o["greeting"])] + [(f"p{i}", s) for i, s in enumerate(intro, 1)]))
    if o["explain"]:
        spec.append(("explain", True, 0.8, [("e0", "Apa itu news ini?")] +
                     [(f"e{i}", f"{n}. {t}") for i, (n, t) in enumerate(o["explain"], 1)]))
    if o["data"]:
        segs = [("d0", "Data yang dijangka.")]
        for i, r in enumerate(o["data"], 1):
            s = f"{r['name']}: sebelum ini {val_say(r['prev'])}, forecast {val_say(r['fc'])}"
            if r.get("act"):
                s += f", actual {r['act']}"
            segs.append((f"d{i}", s + "."))
        spec.append(("data", True, 1.0, segs))
    if o["fund"]:
        spec.append(("fund", True, 0.8, [("f0", "Fundamental analysis.")] +
                     [(f"f{i}", s) for i, s in enumerate([s for p in o["fund"] for s in sentences(p)], 1)]))
    if o["tech"] or o["levels"]:
        segs = [("t0", "Technical analysis.")] + [(f"t{i}", s) for i, s in enumerate([s for p in o["tech"] for s in sentences(p)], 1)]
        segs += [(f"lv{i}", f"{lv['label']}, {lv['a']}–{lv['b']}.") for i, lv in enumerate(o["levels"], 1)]
        spec.append(("tech", True, 1.0, segs))
    for sc in o["scen"]:
        segs = [("hd", f"Senario {M3.NUMW.get(sc['n'], sc['n'])}. {sc['title']}.")] + [(f"x{i}", s) for i, s in enumerate(sentences(sc["desc"]), 1)]
        if sc["tg"]:
            segs.append(("tg", "Target: " + ", ".join(sc["tg"]) + "."))
        spec.append((f"s{sc['n']}", True, 0.8, segs))
    if o["plan"]:
        spec.append(("plan", True, 0.8, [("k0", "Trading plan.")] + [(f"k{i}", s) for i, s in enumerate(o["plan"], 1)]))
    cls = [s for p in o["closing"] for s in sentences(p)]
    segs = [(f"r{i}", s) for i, s in enumerate([s for p in o["risk"] for s in sentences(p)], 1)]
    segs += [(f"c{i}", s) for i, s in enumerate(cls, 1)] + [("oz", "Zik F X. Trade safe, risk first.")]
    spec.append(("outro", False, 2.5, segs))
    data["o"] = o
    return spec, data


SPEC, DATA, TL, ORDER, TOTAL, SEGS = None, None, None, None, 1.0, {}


def load(path, timeline=True):
    global SPEC, DATA, TL, ORDER, TOTAL, SEGS
    o = parse(path)
    SPEC, DATA = build(o)
    SEGS = {n: dict(segs) for n, _, _, segs in SPEC}
    ORDER = [s[0] for s in SPEC]
    tp = os.path.join(WORK, "timeline.json")
    TL = None
    if timeline and os.path.exists(tp):
        TL = json.load(open(tp))
        if list(TL) != ORDER:
            TL = None
    if TL:
        TOTAL = sum(TL[n]["D"] for n in ORDER)
        M.TOTAL = TOTAL
    if o["date"]:
        _, d, mon, yr = o["date"]
        M.CHROME_RIGHT = f"NEWS  •  {d:02d}.{MONTHS.index(mon) + 1:02d}.{yr}"
    return o


def gen_tts(dry):
    # reuse make3's ElevenLabs + timeline builder with this spec and our own work dir
    M3.SPEC = [(n, ch, tail, [(k, say(s)) for k, s in segs]) for n, ch, tail, segs in SPEC]
    M3.WORK = WORK
    _say = M3.say
    M3.say = lambda s: s  # text is already converted
    try:
        M3.gen_tts(dry=dry)
    finally:
        M3.say = _say


# ============================================================ chrome
_tk = {}


def chrome_news(base, T):
    M.chrome(base, T)
    o = DATA["o"]
    if "im" not in _tk:
        parts = [f"NEWS: {o['news'].upper()}"]
        if o["time"]:
            parts.append(f"{o['date'][0].upper() if o['date'] else ''} {o['time'][0]} {o['time'][1]} MYT".strip())
        parts += [f"{lv['label'].upper()} {lv['a']}–{lv['b']}" for lv in o["levels"]]
        parts.append("ELAK ENTRY 15 MINIT SEBELUM & SELEPAS NEWS")
        _tk["im"] = sprite("   " + "   •   ".join(parts) + "   •", "Bold", 28, WHITE)[0]
    tk = _tk["im"]
    d = ImageDraw.Draw(base, "RGBA")
    y0 = 1840
    d.rectangle((0, y0, W, H - 8), fill=(8, 9, 14, 235))
    d.line((0, y0, W, y0), fill=rgba(RED, 0.8), width=2)
    blink = 0.75 + 0.25 * (1 if int(T * 2) % 2 else 0)
    d.rectangle((0, y0 + 2, 150, H - 8), fill=rgba(RED, blink))
    text(base, "NEWS", 75, y0 + 22, "Black", 28, WHITE, "c")
    off = (T * 110) % tk.width
    strip = Image.new("RGB", (W - 150, H - 8 - y0 - 2), (8, 9, 14))
    x = -off
    while x < W:
        strip.paste(tk, (int(x), 14), tk)
        x += tk.width
    base.paste(strip, (150, y0 + 2))


def typed_block(base, t, S, keys_texts, x, y, maxw, bottom, sizes=(42, 38, 34, 31, 28), anchor="l", alt=True, gap=24):
    for size in sizes:
        if sum(len(wrap(s, "SemiBold", size, maxw)) * size * 1.3 + gap for _, s in keys_texts) <= bottom - y:
            break
    for i, (k, s) in enumerate(keys_texts):
        col = GOLD2 if (alt and i % 2) else WHITE
        h = typed(base, s, x, y, maxw, t, S.st(k), S.d(k), "Bold" if i % 2 == 0 else "SemiBold", size, col, 1.3, 1.0, anchor)
        y += h + gap
    return y


# ============================================================ scenes
def sc_hook(base, t, D, S):
    o = DATA["o"]
    out = out_of(t, D)
    base.paste(Image.blend(Image.new("RGB", (W, H), (40, 0, 8)), background(t), 0.55), (0, 0))
    embers(base, t, out)
    s1 = S.st("h1")
    blink = 1 if int(t * 3) % 2 == 0 else 0.45
    pill(base, W / 2, 300, "⚡ NEWS ALERT ⚡".replace("⚡", "!"), RED, 70, clamp(t / 0.3) * out * blink, WHITE, "c", 50, 24, "Black")
    k = clamp((t - s1) / 0.35)
    names = [x.strip() for x in re.split(r",|&| dan ", o["news"]) if x.strip()]
    y = 520
    for i, nm in enumerate(names[:4]):
        ki = clamp((t - s1 - i * 0.35) / 0.35)
        sh = math.sin(t * 110) * 12 * clamp((s1 + i * 0.35 + 0.3 - t) / 0.3) if t > s1 + i * 0.35 else 0
        sweep_text(base, nm.upper(), W / 2 + sh, y, "Black", 130 if len(nm) < 9 else 96, GOLD, "c", ki * out, 18, (255, 140, 0),
                   prog=(t - s1 - 1.4) / 0.8, scale=1 + 0.5 * (1 - eob(ki)))
        y += 170
    s2 = S.st("h2")
    k2 = ap(t, s2, 0.4) * out
    if o["date"]:
        text(base, f"{o['date'][0].upper()}, {o['date'][1]} {o['date'][2].upper()}", W / 2, y + 60, "ExtraBold", 60, WHITE, "c", k2)
    if o["time"]:
        sweep_text(base, f"{o['time'][0]} {o['time'][1]}", W / 2, y + 160, "Black", 150, (255, 90, 100), "c", k2, 16, (200, 0, 20),
                   prog=(t - s2 - 0.5) / 0.7)
        text(base, "WAKTU MALAYSIA", W / 2, y + 340, "Bold", 40, GREY, "c", k2)
    lightning(base, t, s1, 250, 0, 560, 760, seed=5)
    lightning(base, t, s2, 880, 0, 700, 900, col=(255, 200, 90), seed=11)


def sc_intro(base, t, D, S):
    out = out_of(t, D)
    k = clamp((t - 0.15) / 0.55)
    sweep_text(base, "ZIQFX", W / 2, 640, "Black", 230, GOLD, "c", k * out, 22, (255, 170, 0), prog=(t - 0.9) / 0.9,
               scale=1.0 + 0.7 * (1 - eob(k)))
    d = ImageDraw.Draw(base, "RGBA")
    lw = 760 * ap(t, 0.8, 0.6)
    d.rectangle((W / 2 - lw / 2, 880, W / 2 + lw / 2, 886), fill=rgba(RED, out))
    a2 = ap(t, 1.0, 0.5)
    text(base, "XAUUSD", W / 2, 930 + 40 * (1 - a2), "Black", 130, WHITE, "c", a2 * out)
    a3 = ap(t, 1.35, 0.5)
    text(base, "NEWS  OUTLOOK", W / 2, 1100 + 40 * (1 - a3), "ExtraBold", 80, (255, 90, 100), "c", a3 * out, glow=10, gcol=(200, 0, 20))
    pill(base, W / 2, 1260, "FUNDAMENTAL  •  TEKNIKAL  •  FORECAST", (40, 42, 56), 34, ap(t, 1.8) * out, GOLD, "c")
    flash(base, t, 0.15, 0.35, peak=0.6)


def sc_open(base, t, D, S):
    out = out_of(t, D)
    o = DATA["o"]
    embers(base, t, 0.6 * out)
    a = ap(t, S.st("g1"))
    text(base, "Assalamualaikum", W / 2, 260 + 30 * (1 - a), "ExtraBold", 84, WHITE, "c", a * out)
    sweep_text(base, "FIGHTERS!", W / 2, 380, "Black", 150, GOLD, "c", clamp((t - S.en("g1") + 0.8) / 0.4) * out, 20, (255, 150, 0),
               prog=(t - S.en("g1")) / 0.8)
    pill(base, W / 2, 620, o["news"].upper(), RED, 46 if len(o["news"]) < 26 else 36, ap(t, S.en("g1"), 0.4) * out, WHITE, "c", 36, 20, "Black")
    keys = [(k, s) for k, s in SEGS["open"].items() if k.startswith("p")]
    typed_block(base, t, S, keys, W / 2, 780, 920, 1800, anchor="c")


def sc_explain(base, t, D, S):
    out = out_of(t, D)
    kicker(base, t, "APA ITU NEWS INI?", a=out)
    items = DATA["o"]["explain"]
    n = len(items)
    avail = 1820 - 240
    hcard = min(420, avail / max(1, n) - 30)
    d = ImageDraw.Draw(base, "RGBA")
    cols = [GOLD, (90, 200, 255), (255, 120, 200), GREEN]
    for i, (nm, txt) in enumerate(items):
        k = f"e{i + 1}"
        a = ap(t, S.st(k), 0.4) * out
        y = 240 + i * (hcard + 30)
        x = 60 + (1 - a) * 200
        col = cols[i % len(cols)]
        d.rounded_rectangle((x, y, x + 960, y + hcard), 28, fill=(14, 15, 22, int(235 * a)), outline=rgba(col, a), width=4)
        pill(base, x + 36, y + 28, nm.upper(), col, 40, a, (10, 10, 14), padx=24, pady=12)
        for size in (40, 36, 32, 29, 26):
            if len(wrap(txt, "SemiBold", size, 880)) * size * 1.3 <= hcard - 120:
                break
        typed(base, txt, x + 40, y + 110, 880, t, S.st(k), S.d(k), "SemiBold", size, WHITE, 1.3, out)


def sc_data(base, t, D, S):
    out = out_of(t, D)
    kicker(base, t, "DATA • PREVIOUS vs FORECAST", a=out)
    rows = DATA["o"]["data"]
    d = ImageDraw.Draw(base, "RGBA")
    y = 260
    hasact = any(r.get("act") for r in rows)
    cols = ["PREVIOUS", "FORECAST"] + (["ACTUAL"] if hasact else [])
    cw = 250 if not hasact else 200
    x0 = 1020 - cw * len(cols)
    a = ap(t, S.st("d0"), 0.4) * out
    for j, c in enumerate(cols):
        text(base, c, x0 + cw * j + cw / 2, y, "ExtraBold", 28, GREY, "c", a)
    y += 60
    rh = min(240, (1780 - y) / max(1, len(rows)) - 20)
    for i, r in enumerate(rows):
        k = f"d{i + 1}"
        ka = ap(t, S.st(k), 0.4) * out
        d.rounded_rectangle((60, y, 1020, y + rh), 26, fill=(14, 15, 22, int(235 * ka)), outline=rgba(GOLD, 0.7 * ka), width=3)
        nm_lines = wrap(r["name"], "Black", 44, x0 - 110)
        for li, ln in enumerate(nm_lines[:2]):
            text(base, ln, 90, y + rh / 2 - 28 * len(nm_lines[:2]) + li * 56, "Black", 44, WHITE, alpha=ka)
        vals = [r["prev"], r["fc"]] + ([r.get("act") or "—"] if hasact else [])
        for j, v in enumerate(vals):
            kv = clamp((t - S.st(k) - 0.6 - j * 0.9) / 0.35) * out
            colv = GREY if v in ("—", "-") else (GOLD if j == 1 else WHITE)
            disp = "—" if v in ("—", "-") else v
            s_ = 1 + 0.4 * (1 - eob(kv))
            if kv > 0:
                text(base, disp, x0 + cw * j + cw / 2, y + rh / 2 - 30, "Black", 60 if len(disp) < 7 else 44, colv, "c", kv, scale=s_)
        y += rh + 20
    if any(v in ("—", "-") for r in rows for v in (r["prev"], r["fc"])):
        text(base, "— = belum diumumkan / belum disahkan", W / 2, min(y + 10, 1790), "SemiBold", 28, GREY, "c", a)


def sc_fund(base, t, D, S):
    out = out_of(t, D)
    kicker(base, t, "FUNDAMENTAL ANALYSIS", a=out)
    d = ImageDraw.Draw(base, "RGBA")
    a = ap(t, S.st("f0"), 0.4) * out
    chips = [("USD", (90, 200, 255)), ("FED", GOLD), ("YIELD", (255, 120, 200)), ("RISK", AMBER)]
    for i, (c, col) in enumerate(chips):
        pill(base, 60 + i * 245, 230, c, col, 34, ap(t, S.st("f0") + i * 0.15, 0.3) * out, (10, 10, 14), padx=40, pady=14)
    keys = [(k, s) for k, s in SEGS["fund"].items() if k != "f0"]
    d.rounded_rectangle((60, 340, 1020, 1810), 28, fill=(14, 15, 22, int(200 * a)), outline=rgba(GOLD, 0.5 * a), width=3)
    typed_block(base, t, S, keys, 100, 390, 880, 1780)


def h1_frame(levels, last, extra=(), x0f=0.62, pad_right=0.0):
    """Crop the H1 chart to recent bars (+ price axis), frame it around the levels, optionally pad a forecast area."""
    c = CH["h1"]
    a_, b_ = H1MAP["a"], H1MAP["b"]
    Yc = lambda p: a_ - b_ * p
    ps = [last] + [p for lv in levels for p in (lv["lo"], lv["hi"])] + list(extra)
    pmax, pmin = max(ps), min(ps)
    span = max(pmax - pmin, 20)
    pmax += span * 0.15
    pmin -= span * 0.15
    yt, yb = Yc(pmax), Yc(pmin)
    xs = int(1615 * x0f)
    cw = c.width - xs
    padw = int(cw * pad_right)
    canvas = Image.new("RGB", (cw + padw, int(yb - yt)), (0, 0, 0))
    st_, sb_ = max(0, int(yt)), min(c.height, int(yb))
    if sb_ > st_:
        canvas.paste(c.crop((xs, st_, c.width, sb_)), (0, int(st_ - yt)))
    return canvas, yt, Yc, cw


_hcache = {}


def h1_panel(key, levels, last, extra, PW=960, PH=640, pad_right=0.0):
    """Returns (image, Y(price, top), forecast_x0_frac): forecast area starts at that fraction of the panel width."""
    if key not in _hcache:
        canvas, yt, Yc, cw = h1_frame(levels, last, extra, pad_right=pad_right)
        im = canvas.resize((PW, PH), Image.LANCZOS).convert("RGBA")
        im.putalpha(rounded_mask(PW, PH, 22))
        sy = PH / canvas.height
        _hcache[key] = (im, lambda p, yy, sy=sy, yt=yt, Yc=Yc: yy + (Yc(p) - yt) * sy, cw / canvas.width)
    return _hcache[key]


def lv_list():
    out = []
    for lv in DATA["o"]["levels"]:
        a, b = fnum(lv["a"]), fnum(lv["b"])
        out.append(dict(label=lv["label"], rng=f"{lv['a']}–{lv['b']}", lo=min(a, b), hi=max(a, b),
                        res="RESIST" in lv["label"].upper()))
    return out


def last_price():
    o = DATA["o"]
    return o["last"] if o["last"] else (H1MAP["close"] if H1MAP else 0)


def sc_tech(base, t, D, S):
    out = out_of(t, D)
    o = DATA["o"]
    kicker(base, t, "TECHNICAL ANALYSIS", a=out)
    levels = lv_list()
    last = last_price()
    im, Y, _f = h1_panel("tech", levels, last, ())
    a = ap(t, 0.3, 0.5)
    y0 = 230
    comp(base, im, 60, y0, a * out)
    d = ImageDraw.Draw(base, "RGBA")
    for i, lv in enumerate(levels):
        k = ap(t, S.st(f"lv{i + 1}"), 0.5) * out
        col = RED if lv["res"] else GREEN
        ya, yb = Y(lv["hi"], y0), Y(lv["lo"], y0)
        if yb - ya < 10:
            ya, yb = ya - 5, yb + 5
        xr = 60 + im.width * k
        d.rectangle((60, ya, xr, yb), fill=rgba(col, 0.28 * k), outline=rgba(col, k), width=3)
        if k > 0.3:
            text(base, f"{lv['label'].upper()}  {lv['rng']}", 80, ya - 34 if lv["res"] else yb + 6, "ExtraBold", 24, col, alpha=k)
    yl = Y(last, y0)
    for xx in range(60, 1000, 22):
        d.line((xx, yl, xx + 10, yl), fill=rgba((90, 230, 210), a * out), width=3)
    panel_frame(base, 60, y0, im.width, im.height, GOLD, a * out)
    pill(base, 84, y0 + 16, "H1", GOLD, 26, a * out, padx=16, pady=8)
    yb2 = y0 + im.height + 30
    if o["bias"]:
        bc = bias_col(o["bias"])
        pill(base, 60, yb2, f"BIAS: {o['bias'].upper()}", bc, 36, ap(t, S.st("t0"), 0.4) * out, WHITE if bc == RED else (10, 10, 14))
    pill(base, 1020 - text_w(f"LAST {last:.2f}", "ExtraBold", 36) - 52, yb2, f"LAST {last:.2f}", TEAL, 36, ap(t, S.st("t0"), 0.4) * out, WHITE)
    keys = [(k, s) for k, s in SEGS["tech"].items() if re.match(r"t\d+$", k) and k != "t0"]
    typed_block(base, t, S, keys, 70, yb2 + 100, 940, 1810, sizes=(38, 34, 31, 28, 25))


def make_scen(name):
    def sc(base, t, D, S):
        out = out_of(t, D)
        o = DATA["o"]
        n = int(name[1:])
        scn = next(s for s in o["scen"] if s["n"] == n)
        tu = scn["title"].upper()
        col = GREEN if "BULL" in tu or "LEMAH" in tu else (RED if "BEAR" in tu or "KUAT" in tu else AMBER)
        a = ap(t, 0.0, 0.4)
        pill(base, 60, 136, f"SENARIO {n}", col, 36, a, WHITE if col == RED else (10, 10, 14))
        for size in (64, 56, 48, 42):
            if text_w(tu, "Black", size) < 960:
                break
        sweep_text(base, tu, 60, 220, "Black", size, col, "l", clamp(t / 0.5), 12, tuple(int(c * 0.6) for c in col), prog=(t - 0.7) / 0.8)
        levels = lv_list()
        last = last_price()
        tg = [fnum(x) for x in scn["tg"]]
        im, Y, ffrac = h1_panel(f"scen{n}", levels, last, tg, PH=520, pad_right=0.75)
        y0 = 330
        pa = ap(t, 0.2, 0.5)
        comp(base, im, 60, y0, pa * out)
        d = ImageDraw.Draw(base, "RGBA")
        for lv in levels:
            c2 = RED if lv["res"] else GREEN
            d.rectangle((60, Y(lv["hi"], y0), 60 + im.width, Y(lv["lo"], y0) + 2), fill=rgba(c2, 0.18 * pa), outline=rgba(c2, 0.6 * pa), width=2)
        # projected path
        X0 = 60 + im.width * ffrac + 6
        X1 = 60 + im.width - 20
        for gy in range(int(y0) + 8, int(y0 + im.height), 22):
            d.line((X0, gy, X0, gy + 10), fill=rgba(GOLD, 0.6 * pa), width=2)
        text(base, "FORECAST", X0 + 12, y0 + 12, "Black", 24, col, alpha=pa)
        xkeys = [k for k in S.S if k.startswith("x")]
        st = S.st(xkeys[0]) if xkeys else 0.8
        en = S.en(xkeys[-1]) if xkeys else D - 1
        prog = clamp((t - st) / max(0.5, en - st))
        if tg:
            pts_p = [last, last + (tg[0] - last) * 0.15, last - (tg[0] - last) * 0.12, last + (tg[0] - last) * 0.5] + tg
        else:
            band = max(5, abs(levels[0]["hi"] - last) * 0.5) if levels else 10
            pts_p = [last, last + band, last - band, last + band * 0.8, last - band * 0.8, last + band * 0.4, last]
        pts = [(X0 + (X1 - X0) * i / (len(pts_p) - 1), Y(p, y0)) for i, p in enumerate(pts_p)]
        segl = [math.hypot(b[0] - a_[0], b[1] - a_[1]) for a_, b in zip(pts, pts[1:])]
        target, acc, drawn = sum(segl) * prog, 0, [pts[0]]
        for (a_, b), L in zip(zip(pts, pts[1:]), segl):
            if acc + L <= target:
                drawn.append(b)
                acc += L
            else:
                f = (target - acc) / L if L else 0
                drawn.append((a_[0] + (b[0] - a_[0]) * f, a_[1] + (b[1] - a_[1]) * f))
                break
        if len(drawn) > 1 and prog > 0:
            d.line(drawn, fill=rgba(col, 0.3), width=14, joint="curve")
            d.line(drawn, fill=rgba(WHITE, 1), width=5, joint="curve")
            hx, hy = drawn[-1]
            d.ellipse((hx - 11, hy - 11, hx + 11, hy + 11), fill=rgba(GOLD, 1), outline=(255, 255, 255, 255), width=3)
        panel_frame(base, 60, y0, im.width, im.height, col, pa * out)
        pill(base, 84, y0 + 16, "H1", GOLD, 26, pa * out, padx=16, pady=8)
        y = y0 + im.height + 40
        keys = [(k, SEGS[name][k]) for k in xkeys]
        y = typed_block(base, t, S, keys, 70, y, 940, 1560 if tg else 1800, sizes=(40, 36, 32, 29, 26), alt=False)
        if tg:
            tst, tdur = S.st("tg"), S.d("tg")
            yy = max(y + 10, 1590)
            text(base, "TARGET", 70, yy, "ExtraBold", 32, col, alpha=ap(t, tst, 0.4))
            yy += 50
            nt = len(scn["tg"])
            gap = 70
            cw = min(250, (940 - gap * (nt - 1)) / nt)
            x = 70
            for i, v in enumerate(scn["tg"]):
                ct = tst + 0.35 + i * (tdur - 0.35) / nt
                kk = clamp((t - ct) / 0.3)
                if kk > 0:
                    d.rounded_rectangle((x, yy, x + cw, yy + 100), 22, fill=rgba(col, 0.16 * kk), outline=rgba(col, kk), width=4)
                    text(base, v, x + cw / 2, yy + 26, "Black", 52, WHITE, "c", kk)
                if i < nt - 1:
                    text(base, "→", x + cw + gap / 2, yy + 26, "Black", 50, col, "c", clamp((t - ct - 0.2) / 0.3))
                x += cw + gap
        if out < 1:
            base.paste((7, 8, 14), (0, 0, W, H), Image.new("L", (W, H), int(255 * (1 - out))))
        flash(base, t, 0.0, 0.2, col=col, peak=0.35)
    return sc


def sc_plan(base, t, D, S):
    out = out_of(t, D)
    kicker(base, t, "TRADING PLAN • WAKTU NEWS", a=out)
    items = [(k, s) for k, s in SEGS["plan"].items() if k != "k0"]
    y = 240
    for size in (42, 38, 34, 31):
        if sum(max(len(wrap(s, "SemiBold", size, 820)) * size * 1.28, 70) + 34 for _, s in items) < 1800 - y:
            break
    d = ImageDraw.Draw(base, "RGBA")
    for k, s in items:
        st = S.st(k)
        ka = ap(t, st, 0.35) * out
        h = max(len(wrap(s, "SemiBold", size, 820)) * size * 1.28, 70)
        d.rounded_rectangle((60, y - 12, 1020, y + h + 12), 22, fill=(255, 255, 255, int(10 * ka)), outline=rgba(GOLD, 0.4 * ka), width=2)
        check_box(base, 86, y + 4, 56, clamp((t - S.en(k) + 0.3) / 0.35), GREEN, ka)
        typed(base, s, 170, y + 6, 820, t, st, S.d(k), "SemiBold", size, WHITE, 1.28, out)
        y += h + 34


def sc_outro(base, t, D, S):
    out = out_of(t, D, 0.6)
    keys_r = [(k, s) for k, s in SEGS["outro"].items() if k.startswith("r")]
    keys_c = [(k, s) for k, s in SEGS["outro"].items() if k.startswith("c")]
    d = ImageDraw.Draw(base, "RGBA")
    if keys_r:
        a = ap(t, S.st(keys_r[0][0]), 0.4) * out
        warn_icon(base, W / 2, 230, 70, a)
        text(base, "RISK WARNING", W / 2, 330, "Black", 76, AMBER, "c", a, 10, (180, 90, 0))
        d.rounded_rectangle((60, 450, 1020, 920), 26, fill=(255, 170, 40, int(26 * a)), outline=rgba(AMBER, a), width=3)
        typed_block(base, t, S, keys_r, 100, 490, 880, 900, sizes=(38, 34, 31, 28), alt=False)
    if keys_c:
        typed_block(base, t, S, keys_c, W / 2, 980, 960, 1180, sizes=(46, 40, 36, 32), anchor="c")
    st = S.st("oz")
    k = clamp((t - st) / 0.5)
    embers(base, t, 0.8 * k * out)
    sweep_text(base, "ZIQFX", W / 2, 1260, "Black", 170, GOLD, "c", k * out, 20, (255, 160, 0), prog=(t - st - 0.6) / 0.9,
               scale=1 + 0.4 * (1 - eob(k)))
    text(base, "TRADE SAFE  •  RISK FIRST", W / 2, 1480, "ExtraBold", 40, WHITE, "c", ap(t, st + 0.5) * out)
    para(base, "Analisis untuk tujuan pendidikan, bukan nasihat kewangan. Forecast bukan jaminan pergerakan harga.", W / 2, 1660,
         860, "Medium", 30, GREY, 1.3, ap(t, st + 1.0) * out, "c")


FN = {"hook": sc_hook, "intro": sc_intro, "open": sc_open, "explain": sc_explain, "data": sc_data, "fund": sc_fund,
      "tech": sc_tech, "plan": sc_plan, "outro": sc_outro}


def fn_for(name):
    return FN.get(name) or make_scen(name)


def render_frame(name, fi):
    info = TL[name]
    S = Seg(info["S"])
    D = info["D"]
    t = fi / FPS
    T = info["start"] + t
    base = background(T)
    fn_for(name)(base, t, D, S)
    if info["chrome"]:
        chrome_news(base, T)
    return post(base, T, t, D, 0.0)


def render_scene(name):
    D = TL[name]["D"]
    n = int(round(D * FPS))
    path = os.path.join(WORK, "seg", f"{ORDER.index(name):02d}_{name}.mp4")
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                          "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "21", "-pix_fmt", "yuv420p", path],
                         stdin=subprocess.PIPE)
    for fi in range(n):
        p.stdin.write(render_frame(name, fi).tobytes())
    p.stdin.close()
    p.wait()


def make_audio(path):
    lowpass, highpass = M.lowpass, M.highpass
    n = int(TOTAL * SR) + SR
    mus, sfx, vox = np.zeros((n, 2)), np.zeros((n, 2)), np.zeros(n)
    rs = np.random.RandomState(2)

    def add(buf, sig, t0, gain=1.0, pan=0.0):
        s = int(t0 * SR)
        if 0 <= s < n:
            e = min(n, s + len(sig))
            buf[s:e, 0] += sig[: e - s] * gain * (1 - max(0, pan))
            buf[s:e, 1] += sig[: e - s] * gain * (1 + min(0, pan))

    for name, _, _, segs in SPEC:
        for k, txt in segs:
            st, d = TL[name]["S"][k]
            v = read_wav(M3.clip_path(say(txt))[:-4] + ".wav")
            s = int((TL[name]["start"] + st) * SR)
            e = min(n, s + len(v))
            vox[s:e] += v[: e - s]
    vox /= max(1e-6, np.abs(vox).max())
    # darker, tense music bed: minor pads + slow pulse
    beat = 60 / 110
    prog = [(45, [57, 60, 64]), (41, [53, 57, 60]), (43, [55, 58, 62]), (40, [52, 55, 59])]
    mf = lambda m: 440 * 2 ** ((m - 69) / 12)
    tk = np.arange(int(0.45 * SR)) / SR
    kick = np.tanh(1.8 * np.sin(2 * np.pi * np.cumsum(45 + 110 * np.exp(-tk * 30)) / SR) * np.exp(-tk * 7))
    th = np.arange(int(0.05 * SR)) / SR
    hat = highpass(rs.randn(len(th)), 7000) * np.exp(-th * 80)
    t, bar, pads = 0.0, 0, {}
    start_drums = TL["open"]["start"]
    while t < TOTAL:
        root, chord = prog[bar % 4]
        dur = beat * 4
        if bar % 4 not in pads:
            tp = np.arange(int(dur * SR)) / SR
            env = np.minimum(1, tp / 0.4) * np.minimum(1, (dur - tp) / 0.4)
            pad = sum(ga * np.sin(2 * np.pi * mf(m) * h * tp) for m in chord for h, ga in ((1, 1), (2, 0.3)))
            pads[bar % 4] = pad * env * 0.06
        add(mus, pads[bar % 4], t, 1.0)
        for b in range(4):
            tb = t + b * beat
            if start_drums <= t < TOTAL - 4:
                if b in (0, 2):
                    add(mus, kick, tb, 0.8)
                for e in range(2):
                    add(mus, hat, tb + e * beat / 2, 0.12, 0.3)
            tt = np.arange(int(beat * SR)) / SR
            add(mus, np.tanh(2 * np.sin(2 * np.pi * mf(root - 12) * tt)) * np.exp(-tt * 3), tb, 0.22)
        t += dur
        bar += 1
    env = np.convolve(np.abs(vox), np.ones(int(0.25 * SR)) / int(0.25 * SR), mode="same")
    env = np.clip(env / (env.max() * 0.25 + 1e-9), 0, 1)
    mus *= (1 - 0.62 * env)[:, None]
    ti = np.arange(int(1.6 * SR)) / SR
    boom = np.sin(2 * np.pi * (38 + 40 * np.exp(-ti * 8)) * ti) * np.exp(-ti * 2.6)
    tw = np.arange(int(0.5 * SR)) / SR
    whoosh = highpass(rs.randn(len(tw)), 1500) * np.sin(np.pi * tw / 0.5) ** 2 * 0.5
    ta = np.arange(int(1.2 * SR)) / SR
    alarm = lowpass(np.sign(np.sin(2 * np.pi * np.where((ta * 4).astype(int) % 2 == 0, 880, 660) * ta)) * 0.35, 3000)
    tth = np.arange(int(2.2 * SR)) / SR
    thunder = lowpass(rs.randn(len(tth)), 200) * np.exp(-tth * 1.6) * 3 + highpass(rs.randn(len(tth)), 1500) * np.exp(-tth * 9) * 0.5
    tt_ = np.arange(int(0.012 * SR)) / SR
    tick = highpass(rs.randn(len(tt_)), 3000) * np.exp(-tt_ * 400)
    for i, name in enumerate(ORDER):
        st = TL[name]["start"]
        if i:
            add(sfx, whoosh, st - 0.35, 0.35)
        add(sfx, boom, st, 0.5 if name in ("hook", "open", "tech") or name.startswith("s") else 0.3)
    add(sfx, alarm, 0.05, 0.3)
    add(sfx, thunder, TL["hook"]["S"]["h1"][0], 0.5)
    add(sfx, thunder, TL["hook"]["S"]["h2"][0], 0.5)
    rr = random.Random(3)
    for name in ORDER:
        if name in ("hook", "intro"):
            continue
        for k, (st, d) in TL[name]["S"].items():
            if k in ("t0", "f0", "k0", "d0", "e0", "hd", "tg", "g1", "oz") or k.startswith("lv"):
                continue
            x = 0
            while x < d * 0.85:
                add(sfx, tick, TL[name]["start"] + st + x, rr.uniform(0.04, 0.07), rr.uniform(-0.3, 0.3))
                x += rr.uniform(0.05, 0.09)
    end = int(TOTAL * SR)
    fade = np.ones(n)
    fade[end - 3 * SR:end] = np.linspace(1, 0, 3 * SR)
    fade[end:] = 0
    mix = mus / max(1e-6, np.abs(mus).max()) * 0.38 + sfx / max(1e-6, np.abs(sfx).max()) * 0.42 + vox[:, None] * 0.85
    mix = np.tanh(mix * fade[:, None] * 1.1) * 0.93
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((mix[:end] * 32767).astype(np.int16).tobytes())


def _winit(path):
    load(path)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    mode, path = sys.argv[1], sys.argv[2]
    os.makedirs(os.path.join(WORK, "seg"), exist_ok=True)
    o = load(path, timeline=False)
    if mode == "parse":
        for name, _, _, segs in SPEC:
            print(f"== {name}")
            for k, s in segs:
                print(f"   {k:4s} {say(s)}")
        sys.exit(0)
    if mode in ("tts", "dry"):
        gen_tts(mode == "dry")
        sys.exit(0)
    load(path)
    if not TL:
        sys.exit("no timeline: run `make_news.py tts` (or `dry`) first")
    if mode == "preview":
        for arg in sys.argv[3:]:
            nm, tt = arg.split(":")
            render_frame(nm, int(float(tt) * FPS)).save(os.path.join(WORK, f"pn_{nm}_{tt}.png"))
        sys.exit(0)
    if mode == "render":
        if any(v.get("dry") for v in TL.values()):
            sys.exit("timeline is a dry estimate: run `make_news.py tts` before rendering")
        os.makedirs(OUT_DIR, exist_ok=True)
        make_audio(os.path.join(WORK, "mix.wav"))
        with Pool(4, initializer=_winit, initargs=(path,)) as pool:
            pool.map(render_scene, sorted(ORDER, key=lambda nm: -TL[nm]["D"]))
        with open(os.path.join(WORK, "list.txt"), "w") as f:
            for i, nm in enumerate(ORDER):
                f.write(f"file '{os.path.join(WORK, 'seg', f'{i:02d}_{nm}.mp4')}'\n")
        tag = f"{o['date'][3]}-{MONTHS.index(o['date'][2]) + 1:02d}-{o['date'][1]:02d}" if o["date"] else "latest"
        out = os.path.join(OUT_DIR, f"ZIQFX_XAUUSD_News_{tag}.mp4")
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", os.path.join(WORK, "list.txt"),
                        "-i", os.path.join(WORK, "mix.wav"), "-c:v", "libx264", "-preset", "medium", "-crf", "23", "-pix_fmt",
                        "yuv420p", "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-ar", "44100", "-c:a", "aac", "-b:a", "192k",
                        "-movflags", "+faststart", out], check=True)
        print(out)
