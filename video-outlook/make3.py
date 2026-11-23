"""ZIQFX outlook video generated straight from an outlook text file (TEMPLATE_outlook.md format).

Usage:
  python3 make3.py parse  outlooks/2026-11-24.md      # show what was parsed + narration
  python3 make3.py tts    outlooks/2026-11-24.md      # ElevenLabs voice clips + timeline (cached by text)
  python3 make3.py dry    outlooks/2026-11-24.md      # estimated timeline without TTS (for previews)
  python3 make3.py preview outlooks/2026-11-24.md z1a:10 levels:12
  python3 make3.py render outlooks/2026-11-24.md      # -> out/ZIQFX_XAUUSD_Outlook_<date>.mp4

Charts come from charts/ (run `python3 xau_charts.py all` and `python3 xau_levels.py` first).
"""
import hashlib, json, math, os, random, re, subprocess, sys, wave
from datetime import date
from multiprocessing import Pool

import numpy as np
from PIL import Image, ImageDraw

import make as M
from make import (W, H, FPS, GOLD, GOLD2, RED, GREEN, AMBER, TEAL, WHITE, GREY, clamp, eo, eob, ap, sprite, comp, text,
                  text_w, wrap, para, rgba, rounded_mask, panel_frame, background, draw_candles, tri, warn_icon, check_box,
                  pill, flash, kicker, CH, M5_Y)
from make2 import typed, sweep_text, lightning, embers, post, Seg, out_of, read_wav, say as say0, DIG

HERE = M.HERE
WORK = os.path.join(HERE, "work")
TTS_DIR = os.path.join(WORK, "tts")
OUT_DIR = os.path.join(HERE, "out")
EL_VOICE = "VbhRlZCHaUh9hxeUyRBD"  # Daud M - Deep & Confident Narrator
EL_MODEL = os.environ.get("ZIQ_EL_MODEL", "eleven_flash_v2_5")  # flash = half the credits; set eleven_multilingual_v2 for top quality
LEAD, GAP = 0.45, 0.22
SR = 44100

MONTHS = ["Januari", "Februari", "Mac", "April", "Mei", "Jun", "Julai", "Ogos", "September", "Oktober", "November", "Disember"]
DAYS = ["Isnin", "Selasa", "Rabu", "Khamis", "Jumaat", "Sabtu", "Ahad"]
NUMW = {1: "satu", 2: "dua", 3: "tiga", 4: "empat", 5: "lima", 6: "enam"}
EMOJI_RE = re.compile("[☀-➿⬀-⯿\U0001F000-\U0001FFFF️‍⃣]")
NUM = r"\d+(?:\.\d+)?"
RNG = rf"({NUM})\s*[–-]\s*({NUM})"


# ============================================================ parsing
def clean(s):
    return re.sub(r"\s+", " ", EMOJI_RE.sub("", s)).strip()


def sentences(p):
    p = re.sub(r"\s*\.\s*\.$", ".", p.strip())
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+(?=[A-Z0-9])", p) if s.strip() and s.strip() != "."]


def paragraphs(lines):
    out, cur = [], []
    for l in lines:
        c = clean(l)
        if not c:
            if cur:
                out.append(cur)
                cur = []
        else:
            cur.append(c)
    if cur:
        out.append(cur)
    return out


def fnum(s):
    return float(re.sub(r"[^\d.]", "", s))


def parse(path):
    raw = open(path, encoding="utf-8").read()
    secs = [[]]
    for line in raw.splitlines():
        if re.match(r"^\s*━{3,}", line) or re.match(r"^\s*[-=_]{5,}\s*$", line):
            secs.append([])
        else:
            secs[-1].append(line)
    o = {"date": None, "greeting": "Assalamualaikum & good morning, fighters!", "intro": [], "bias": {}, "zones": [],
         "main": [], "scen": [], "levels": [], "levels_note": [], "check": [], "fund": [], "closing": []}
    for sec in secs:
        cl = [clean(l) for l in sec]
        hi = next((i for i, c in enumerate(cl) if c), 0)
        first = cl[hi] if cl else ""
        body_cl, body = cl[hi + 1:], sec[hi + 1:]
        up = first.upper()
        m = re.match(rf"ZONE\s*(\d+)\s*[—–-]\s*(RESISTANCE|SUPPORT)\s*{RNG}", first, re.I)
        if m:
            parse_zone(o, m, body_cl)
        elif "MAIN MARKET SCENARIO" in up:
            parse_main(o, body_cl)
        elif "KEY LEVELS" in up:
            for c in body_cl:
                mm = re.match(rf"^•\s*([^:]+):\s*{RNG}", c)
                if mm:
                    o["levels"].append({"label": mm[1].strip(), "a": mm[2], "b": mm[3]})
            for p in paragraphs(body):
                if not p[0].startswith("•"):
                    o["levels_note"] += sentences(" ".join(p))
        elif "CHECKLIST" in up:
            o["check"] = [c.lstrip("• ").strip() for c in cl if c.startswith("•")]
        elif "FUNDAMENTAL" in up:
            for p in paragraphs(body):
                t = " ".join(p)
                (o["closing"] if t.lower().startswith("fighters") else o["fund"]).append(t)
        else:
            parse_head(o, sec)
    return o


def parse_head(o, sec):
    rest = []
    for l in sec:
        c = clean(l)
        mb = re.match(r"^(BIAS UTAMA|INTRADAY|FOCUS|LAST PRICE)\s*:\s*(.+)$", c, re.I)
        md = re.search(rf"({'|'.join(DAYS)}),?\s*(\d{{1,2}})\s+({'|'.join(MONTHS)})\s+(\d{{4}})", c)
        if mb:
            o["bias"][mb[1].upper()] = mb[2].strip()
            rest.append("")
        elif "MARKET OUTLOOK" in c.upper():
            rest.append("")
        elif md and len(c) < 40:
            o["date"] = (md[1], int(md[2]), md[3], int(md[4]))
            rest.append("")
        elif c.lower().startswith("assalamualaikum"):
            o["greeting"] = c
            rest.append("")
        else:
            rest.append(l)
    o["intro"] += [" ".join(p) for p in paragraphs(rest)]


def parse_zone(o, m, cl):
    a, b = fnum(m[3]), fnum(m[4])
    z = {"num": int(m[1]), "kind": m[2].upper(), "rng": f"{m[3]}–{m[4]}", "lo": min(a, b), "hi": max(a, b), "blocks": []}
    cur = None
    for c in cl:
        if not c:
            continue
        mb = re.match(r"^(BUY|SELL)\s+(confirmation|continuation)\s*:?\s*$", c, re.I)
        if mb:
            cur = {"side": mb[1].upper(), "type": mb[2].lower(), "bullets": [], "tg": [], "warn": None}
            z["blocks"].append(cur)
            continue
        if cur is None:
            cur = {"side": "SELL" if z["kind"] == "RESISTANCE" else "BUY", "type": "confirmation", "bullets": [], "tg": [], "warn": None}
            z["blocks"].append(cur)
        if c.startswith("•"):
            cur["bullets"].append(c.lstrip("• ").strip())
            continue
        mt = re.match(r"^Target\s*:\s*(.+)$", c, re.I)
        if mt:
            cur["tg"] = [x.strip() for x in re.split(r"→|->|,", mt[1]) if re.search(r"\d", x)]
            continue
        cur["warn"] = (cur["warn"] + " " if cur["warn"] else "") + c
    o["zones"].append(z)


def parse_main(o, cl):
    mode = "main"
    buf, scen = [], None
    for c in cl:
        if "DUA SENARIO" in c.upper() or "SENARIO UTAMA" in c.upper():
            mode = "scen"
            if buf:
                o["main"].append(" ".join(buf))
                buf = []
            continue
        if mode == "main":
            if not c:
                if buf:
                    o["main"].append(" ".join(buf))
                    buf = []
            else:
                buf.append(c)
        else:
            if not c:
                continue
            ms = re.match(r"^(\d+)\s*[.)]?\s*([A-Z][A-Z /&]+)$", c)
            if ms:
                scen = {"title": ms[2].strip(), "flow": ""}
                o["scen"].append(scen)
            elif scen is not None:
                scen["flow"] = (scen["flow"] + " " + c).strip()
    if buf:
        o["main"].append(" ".join(buf))


# ============================================================ narration helpers
def say(s):
    s = re.sub(r"\b(Resistance|Support|Zon|Zone)\s+(\d)\b", lambda m: f"{m[1]} {NUMW.get(int(m[2]), m[2])}", s)
    s = s.replace("=", " bermakna ")
    s = re.sub(r"\b([4-9]\d{3})(?:\.(\d+))?\b",
               lambda m: " ".join(DIG[int(c)] for c in m[1]) + (" perpuluhan " + " ".join(DIG[int(c)] for c in m[2]) if m[2] else ""), s)
    return say0(s)


def bias_col(v):
    v = v.upper()
    if "BEAR" in v and "NEUTRAL" not in v:
        return RED
    if "BULL" in v and "NEUTRAL" not in v:
        return GREEN
    return AMBER


def gen_path(side, cont, lo, hi, last, tg):
    w = max(hi - lo, 3.0)
    t = (tg + [tg[-1]] * 3)[:3] if tg else ([lo - w, lo - 2 * w, lo - 3 * w] if side == "SELL" else [hi + w, hi + 2 * w, hi + 3 * w])
    if not cont and side == "SELL":
        return [(last, 0), (lo + 0.3 * w, .15), ((last + lo) / 2 if last < lo else lo - 0.2 * w, .25), (hi - 0.1 * w, .42),
                (hi + 0.35 * w, .48), (lo + 0.1 * w, .58), (lo + 0.55 * w, .64), (t[0], .8), (t[1], .9), (t[2], 1)]
    if not cont and side == "BUY":
        return [(last, 0), (hi - 0.3 * w, .15), ((last + hi) / 2 if last > hi else hi + 0.2 * w, .25), (lo + 0.1 * w, .42),
                (lo - 0.35 * w, .48), (hi - 0.1 * w, .58), (hi - 0.55 * w, .64), (t[0], .8), (t[1], .9), (t[2], 1)]
    if cont and side == "SELL":   # breakdown of support, retest from below
        return [(last, 0), (hi, .2), (lo - 0.6 * w, .38), (lo - w, .44), (lo + 0.5 * w, .58), (lo - 0.3 * w, .68),
                (t[0], .8), (t[1], .9), (t[2], 1)]
    return [(last, 0), (lo, .2), (hi + 0.6 * w, .38), (hi + w, .44), (hi - 0.5 * w, .58), (hi + 0.3 * w, .68),
            (t[0], .8), (t[1], .9), (t[2], 1)]


EVENTS = ["GDP", "PCE", "CPI", "PPI", "NFP", "Non-Farm", "FOMC", "ISM", "PMI", "JOLTS", "Retail Sales", "Jobless Claims",
          "Unemployment", "Powell", "Fed Minutes"]


def build(o):
    """Turn the parsed outlook into scene specs: list of (name, chrome, tail, [(key, spoken)]) + per-scene data."""
    spec, data = [], {}
    bias = o["bias"]
    last_s = re.sub(r"[^\d.]", "", bias.get("LAST PRICE", "")) or None
    last = float(last_s) if last_s else M5_CLOSE
    bias_main = bias.get("BIAS UTAMA", "")
    spec.append(("hook", False, 0.8, [("h1", f"XAU USD kini di {last_s or f'{last:.2f}'}."), ("h2", "Apa seterusnya?")]))
    if o["date"]:
        dname, d, mon, yr = o["date"]
        dline = f"{dname}, {d} {mon} {yr}."
    else:
        dline = ""
    spec.append(("intro", False, 0.6, [("i1", "Zik F X. Gold, XAU USD market outlook.")] + ([("i2", dline)] if dline else [])))
    spec.append(("greet", True, 0.6, [("g1", o["greeting"])]))
    intro_s = [s for p in o["intro"] for s in sentences(p)]
    if intro_s:
        spec.append(("context", True, 1.8, [("c1", intro_s[0])]))
    if len(intro_s) > 1:
        spec.append(("mtf", True, 1.0, [(f"m{i}", s) for i, s in enumerate(intro_s[1:], 1)]))
    rows = [(k, v) for k, v in bias.items()]
    if rows:
        lab = {"BIAS UTAMA": "Bias utama", "INTRADAY": "Intraday", "FOCUS": "Focus", "LAST PRICE": "Last price"}
        spec.append(("bias", True, 1.0, [(f"b{i}", f"{lab.get(k, k)}: {v.replace('→', 'ke')}.") for i, (k, v) in enumerate(rows, 1)]))
    for z in o["zones"]:
        for j, b in enumerate(z["blocks"]):
            key = f"z{z['num']}{'abcd'[j]}"
            cont = b["type"] == "continuation"
            if j == 0:
                hd = f"Zon {NUMW.get(z['num'], z['num'])}. {z['kind'].lower()} {z['rng']}."
            elif cont:
                hd = f"Masih di zon {NUMW.get(z['num'], z['num'])}. Kalau {z['kind'].lower()} pecah:"
            else:
                hd = f"Zon {NUMW.get(z['num'], z['num'])}, senario {b['side'].lower()}."
            segs = [("hd", hd), ("sec", f"{b['side'].lower()} {b['type']}.")]
            segs += [(f"b{i}", s) for i, s in enumerate(b["bullets"])]
            if b["tg"]:
                segs.append(("tg", "Target: " + ", ".join(b["tg"]) + "."))
            if b["warn"]:
                segs.append(("w", b["warn"]))
            tg_f = [fnum(x) for x in b["tg"]]
            data[key] = dict(num=z["num"], kind=z["kind"], rng=z["rng"], lo=z["lo"], hi=z["hi"], side=b["side"], cont=cont,
                             col=RED if b["side"] == "SELL" else GREEN, down=b["side"] == "SELL",
                             sec=f"{b['side']} {b['type'].upper()}", bullets=b["bullets"], tg=b["tg"], warn=b["warn"],
                             extra=(" • BREAKDOWN" if z["kind"] == "SUPPORT" else " • BREAKOUT") if cont else "",
                             path=gen_path(b["side"], cont, z["lo"], z["hi"], last, tg_f))
            spec.append((key, True, 0.8, segs))
    if o["main"]:
        p0 = o["main"][0]
        segs = [("s1", "Main market scenario.")]
        big = None
        mm = re.search(rf"(di bawah|di atas)\s+(?:\w+\s+)?{RNG}", p0, re.I)
        if "," in p0:
            a, b_ = p0.split(",", 1)
            segs += [("s2", a.strip() + ","), ("s3", b_.strip())]
            mf = re.search(r"([A-Z][A-Z ]{3,}[A-Z])\s*\.?$", b_.strip())
            if mm:
                big = dict(pre=f"Selagi harga {mm[1].lower()}", rng=f"{mm[2]}–{mm[3]}",
                           mid=(b_.strip()[: mf.start()].strip() if mf else "keutamaan"), focus=(mf[1] if mf else bias.get("FOCUS", "")))
        else:
            segs.append(("s2", p0))
        rest = [s for p in o["main"][1:] for s in sentences(p)]
        segs += [(f"s{i}", s) for i, s in enumerate(rest, 4)]
        data["main"] = dict(big=big, rest=[(f"s{i}", s) for i, s in enumerate(rest, 4)], p0=p0)
        spec.append(("main", True, 1.0, segs))
    if o["scen"]:
        segs = [("t0", f"{'Dua' if len(o['scen']) == 2 else NUMW.get(len(o['scen']), '')} senario utama.".capitalize())]
        cards = []
        for i, sc in enumerate(o["scen"], 1):
            steps = [x.strip(" .") for x in sc["flow"].split("→") if x.strip(" .")]
            segs.append((f"t{i}", f"{NUMW.get(i, i).capitalize()}. {sc['title']}."))
            keys = []
            for j, st in enumerate(steps):
                k = f"t{i}{'abcdefgh'[j]}"
                segs.append((k, st + ("," if j < len(steps) - 1 else ".")))
                keys.append((k, st[0].upper() + st[1:]))
            cards.append(dict(n=i, title=sc["title"], key=f"t{i}", steps=keys,
                              col=RED if "SELL" in sc["title"].upper() else GREEN, down="SELL" in sc["title"].upper()))
        data["two"] = cards
        spec.append(("two", True, 1.0, segs))
    if o["levels"]:
        segs = [("l0", "Key levels to watch.")]
        items = []
        for i, lv in enumerate(o["levels"], 1):
            segs.append((f"l{i}", f"{lv['label']}, {lv['a']}–{lv['b']}."))
            items.append(dict(key=f"l{i}", label=lv["label"], rng=f"{lv['a']}–{lv['b']}", lo=min(fnum(lv["a"]), fnum(lv["b"])),
                              hi=max(fnum(lv["a"]), fnum(lv["b"]))))
        notes = [(f"lp{i}", s) for i, s in enumerate(o["levels_note"], 1)]
        segs += notes
        data["levels"] = dict(items=items, notes=notes, last=last)
        spec.append(("levels", True, 1.0, segs))
    if o["check"]:
        segs = [("k0", "Entry confirmation checklist.")]
        items = []
        for i, c in enumerate(o["check"], 1):
            k = f"k{i}"
            if "NO ENTRY" in c.upper():
                left = c.split("=")[0].strip(" .") if "=" in c else "Tiada confirmation"
                segs.append((k, f"{left}? NO ENTRY!"))
                items.append(dict(key=k, kind="stamp", a=left.upper(), b="= NO ENTRY"))
            elif "—" in c or " - " in c:
                a, b_ = re.split(r"\s*(?:—| - )\s*", c, maxsplit=1)
                segs.append((k, f"{a.replace('/', ' dan ')}, {b_}"))
                items.append(dict(key=k, kind="tf", a=a, b=b_.strip(" .")))
            else:
                segs.append((k, c))
                items.append(dict(key=k, kind="rule", a=c))
        data["check"] = items
        spec.append(("check", True, 1.2, segs))
    if o["fund"]:
        fs = [s for p in o["fund"] for s in sentences(p)]
        segs = [("f0", "Fundamental watch.")] + [(f"f{i}", s) for i, s in enumerate(fs, 1)]
        alltxt = " ".join(fs)
        md = re.search(rf"(\d{{1,2}})\s+({'|'.join(MONTHS)})", alltxt)
        cal = None
        if md:
            yr = o["date"][3] if o["date"] else date.today().year
            dd = date(yr, MONTHS.index(md[2]) + 1, int(md[1]))
            cal = dict(day=int(md[1]), month=md[2].upper(), year=yr, wd=DAYS[dd.weekday()].upper())
        evs = [e for e in EVENTS if re.search(rf"\b{re.escape(e)}\b", alltxt, re.I)][:3]
        data["fund"] = dict(sents=[(f"f{i}", s) for i, s in enumerate(fs, 1)], cal=cal, events=evs)
        spec.append(("fund", True, 1.0, segs))
    cls = [s for p in o["closing"] for s in sentences(p)] or ["Fighters, jangan terburu-buru mengejar candle.",
                                                            "Tunggu harga datang ke zone, tunggu confirmation, kemudian baru rancang entry."]
    segs = [("o1", cls[0])]
    steps = []
    if len(cls) > 1:
        parts = [x.strip(" .") for x in re.split(r",", " ".join(cls[1:])) if x.strip(" .")]
        for i, p in enumerate(parts[:3], 2):
            segs.append((f"o{i}", p + ("," if i - 2 < len(parts[:3]) - 1 else ".")))
            disp = re.sub(r"^(kemudian|dan|lalu)\s+", "", p, flags=re.I)
            disp = re.sub(r"\bharga datang ke\b", "", disp, flags=re.I)
            steps.append((f"o{i}", re.sub(r"\s+", " ", disp).strip().upper()))
    segs.append(("oz", "Zik F X. Trade safe, risk first."))
    data["outro"] = dict(first=cls[0], steps=steps)
    spec.append(("outro", False, 3.0, segs))
    data["last"] = last
    data["bias"] = bias
    data["date"] = o["date"]
    return spec, data


# ============================================================ globals filled at runtime
_m5 = json.load(open(os.path.join(HERE, "charts", "map.json")))["m5"] if os.path.exists(os.path.join(HERE, "charts", "map.json")) else None
M5_CLOSE = _m5["close"] if _m5 else 0.0
SPEC, DATA, TL, ORDER, TOTAL = None, None, None, None, 1.0


def load(path, timeline=True):
    global SPEC, DATA, TL, ORDER, TOTAL
    o = parse(path)
    SPEC, DATA = build(o)
    ORDER = [s[0] for s in SPEC]
    tp = os.path.join(WORK, "timeline.json")
    if timeline and os.path.exists(tp):
        TL = json.load(open(tp))
        if [n for n in TL] != ORDER:
            TL = None
    if TL:
        TOTAL = sum(TL[n]["D"] for n in ORDER)
        M.TOTAL = TOTAL
    if o["date"]:
        _, d, mon, yr = o["date"]
        M.CHROME_RIGHT = f"XAUUSD  •  {d:02d}.{MONTHS.index(mon) + 1:02d}.{yr}"
    return o


# ============================================================ TTS + timeline
def clip_path(spoken):
    h = hashlib.md5((EL_VOICE + EL_MODEL + spoken).encode()).hexdigest()[:16]
    return os.path.join(TTS_DIR, h + ".mp3")


def gen_tts(dry=False):
    from concurrent.futures import ThreadPoolExecutor
    os.makedirs(TTS_DIR, exist_ok=True)
    jobs = []
    for name, _, _, segs in SPEC:
        for k, txt in segs:
            p = clip_path(say(txt))
            if not dry and (not os.path.exists(p) or os.path.getsize(p) < 1000):
                jobs.append((p, say(txt)))

    def el(job):
        p, txt = job
        req = {"text": txt, "model_id": EL_MODEL, "voice_settings": {"stability": 0.45, "similarity_boost": 0.8, "style": 0.25}}
        if "flash" in EL_MODEL or "turbo" in EL_MODEL:
            req["language_code"] = "ms"
        body = json.dumps(req)
        for attempt in range(5):
            r = subprocess.run(["curl", "-s", "--max-time", "120", "-o", p, "-w", "%{http_code}",
                                f"https://api.elevenlabs.io/v1/text-to-speech/{EL_VOICE}?output_format=mp3_44100_128",
                                "-H", "xi-api-key: proxy-injected", "-H", "Content-Type: application/json", "-d", body],
                               capture_output=True, text=True)
            if r.stdout.strip() == "200":
                return
            print("tts retry", r.stdout, open(p, "rb").read(200) if os.path.exists(p) else b"", file=sys.stderr)
            import time
            time.sleep(3 * (attempt + 1))
        if os.path.exists(p):
            os.remove(p)
        sys.exit(f"ElevenLabs failed for: {txt[:60]}")

    if jobs:
        with ThreadPoolExecutor(4) as ex:
            list(ex.map(el, jobs))
    tl, T = {}, 0.0
    for name, ch, tail, segs in SPEC:
        t = LEAD
        S = {}
        for k, txt in segs:
            if dry:
                d = max(0.8, len(say(txt)) / 15.0)
            else:
                mp3 = clip_path(say(txt))
                wav = mp3[:-4] + ".wav"
                if not os.path.exists(wav):
                    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", mp3, "-af",
                                    "silenceremove=start_periods=1:start_threshold=-45dB,areverse,silenceremove=start_periods=1:start_threshold=-45dB,areverse",
                                    "-ar", "44100", "-ac", "1", wav], check=True)
                with wave.open(wav) as w:
                    d = w.getnframes() / w.getframerate()
            S[k] = [t, d]
            t += d + GAP
        D = t - GAP + tail
        tl[name] = {"S": S, "D": round(D * FPS) / FPS, "start": T, "chrome": ch, "dry": dry}
        T += tl[name]["D"]
    json.dump(tl, open(os.path.join(WORK, "timeline.json"), "w"), indent=1)
    print(f"total {T:.1f}s  ({len(jobs)} new clips)")


# ============================================================ chrome / ticker
_tick = {}


def ticker_text():
    def ab(l):
        lab = l.upper().replace("RESISTANCE", "R").replace("SUPPORT", "S")
        return re.sub(r"^([RS]) (\d)$", r"\1\2", lab)

    parts = [f"{ab(i['label'])} {i['rng']}" for i in DATA.get("levels", {}).get("items", [])]
    b = DATA["bias"]
    if b.get("BIAS UTAMA"):
        parts.append(f"BIAS: {b['BIAS UTAMA'].upper()}")
    if b.get("FOCUS"):
        parts.append(b["FOCUS"].upper())
    parts.append("NO CONFIRMATION = NO ENTRY")
    return "   " + "   •   ".join(parts) + "   •"


def chrome3(base, T):
    M.chrome(base, T)
    if "im" not in _tick:
        _tick["im"] = sprite(ticker_text(), "Bold", 28, WHITE)[0]
    tk = _tick["im"]
    d = ImageDraw.Draw(base, "RGBA")
    y0 = 1840
    d.rectangle((0, y0, W, H - 8), fill=(8, 9, 14, 235))
    d.line((0, y0, W, y0), fill=rgba(GOLD, 0.7), width=2)
    d.rectangle((0, y0 + 2, 150, H - 8), fill=rgba(GOLD, 1))
    text(base, "LEVELS", 75, y0 + 22, "Black", 26, (12, 10, 6), "c")
    off = (T * 110) % tk.width
    strip = Image.new("RGB", (W - 150, H - 8 - y0 - 2), (8, 9, 14))
    x = -off
    while x < W:
        strip.paste(tk, (int(x), 14), tk)
        x += tk.width
    base.paste(strip, (150, y0 + 2))


# ============================================================ scenes
def sc_hook(base, t, D, S):
    out = out_of(t, D)
    c = CH["h4"]
    z = 1.15 + 0.25 * eo(t / D)
    cw, chh = c.width / z, c.height / z
    cx0, cy0 = (c.width - cw) * 0.98, (c.height - chh) * 0.5
    crop = c.crop((int(cx0), int(cy0), int(cx0 + cw), int(cy0 + chh)))
    ww = int(crop.width * H / crop.height)
    big = crop.resize((ww, H), Image.BILINEAR)
    big = big.crop((ww - W - 40, 0, ww - 40, H))
    bc = bias_col(DATA["bias"].get("BIAS UTAMA", ""))
    tint = tuple(int(v * 0.16) for v in bc)
    base.paste(Image.blend(Image.new("RGB", (W, H), tint), big, 0.5), (0, 0))
    embers(base, t, 0.9 * out)
    s1 = S.st("h1")
    k = clamp((t - s1) / 0.35)
    sh = math.sin(t * 110) * 14 * clamp((s1 + 0.4 - t) / 0.4) if t > s1 else 0
    text(base, "XAUUSD", W / 2 + sh, 430, "Black", 150, WHITE, "c", k * out, 16, (120, 120, 140), 1 + 0.6 * (1 - eob(k)))
    k2 = clamp((t - s1 - 0.6) / 0.35)
    sweep_text(base, f"{DATA['last']:,.2f}", W / 2, 640, "Black", 210, GOLD, "c", k2 * out, 22, (255, 150, 0),
               prog=(t - s1 - 1.1) / 0.8, scale=1 + 0.5 * (1 - eob(k2)))
    k3 = ap(t, s1 + 1.2, 0.4)
    bm = DATA["bias"].get("BIAS UTAMA", "")
    if bm:
        pill(base, W / 2, 940, bm.upper(), bc, 56, k3 * out, WHITE if bc == RED else (10, 10, 14), "c", 40, 20, "Black")
    s2 = S.st("h2")
    k4 = clamp((t - s2) / 0.3)
    pill(base, W / 2, 1250, "APA SETERUSNYA?", GOLD, 84, k4 * out, (12, 10, 6), "c", 50, 26, "Black")
    lightning(base, t, s1, 300, 0, 620, 900, seed=3)
    lightning(base, t, s2, 900, 0, 760, 1250, col=(255, 200, 90), seed=9)


def sc_intro(base, t, D, S):
    out = out_of(t, D)
    draw_candles(base, t, out)
    k = clamp((t - 0.15) / 0.55)
    sweep_text(base, "ZIQFX", W / 2, 640, "Black", 230, GOLD, "c", k * out, 22, (255, 170, 0), prog=(t - 0.9) / 0.9,
               scale=1.0 + 0.7 * (1 - eob(k)))
    d = ImageDraw.Draw(base, "RGBA")
    lw = 760 * ap(t, 0.8, 0.6)
    d.rectangle((W / 2 - lw / 2, 880, W / 2 + lw / 2, 886), fill=rgba(GOLD, out))
    a2 = ap(t, 1.0, 0.5)
    text(base, "XAUUSD", W / 2, 930 + 40 * (1 - a2), "Black", 130, WHITE, "c", a2 * out)
    a3 = ap(t, 1.35, 0.5)
    text(base, "MARKET  OUTLOOK", W / 2, 1100 + 40 * (1 - a3), "ExtraBold", 72, GOLD, "c", a3 * out, glow=10, gcol=(200, 120, 0))
    if DATA["date"] and "i2" in S.S:
        dn, dd, mon, yr = DATA["date"]
        pill(base, W / 2, 1250, f"{dn.upper()}  •  {dd} {mon.upper()} {yr}", RED, 40, ap(t, S.st("i2"), 0.5) * out, WHITE, "c")
    text(base, "GOLD (XAU) vs US DOLLAR", W / 2, 1380, "SemiBold", 34, GREY, "c", ap(t, 2.0, 0.5) * out)
    sw = ap(t, 0.15, 0.35)
    if sw > 0:
        for sgn in (-1, 1):
            cx, cy = W / 2, 330
            L = 170 * sw
            ang = math.radians(45 * sgn)
            x0, y0 = cx - math.sin(ang) * L, cy + math.cos(ang) * L
            x1, y1 = cx + math.sin(ang) * L, cy - math.cos(ang) * L
            d.line((x0, y0, x1, y1), fill=rgba((230, 230, 240), out), width=10)
            d.line((x0 - 24 * math.cos(ang), y0 - 24 * math.sin(ang), x0 + 24 * math.cos(ang), y0 + 24 * math.sin(ang)),
                   fill=rgba(GOLD, out), width=12)
    flash(base, t, 0.15, 0.35, peak=0.7)


def sc_greet(base, t, D, S):
    out = out_of(t, D)
    embers(base, t, out)
    g = clean(DATA.get("greeting_disp", "")) or "Assalamualaikum"
    a1 = ap(t, 0.1)
    text(base, "Assalamualaikum", W / 2, 640 + 40 * (1 - a1), "ExtraBold", 92, WHITE, "c", a1 * out)
    a2 = ap(t, 0.5)
    text(base, "& good morning,", W / 2, 780 + 40 * (1 - a2), "SemiBold", 70, GREY, "c", a2 * out)
    tf = max(1.0, S.en("g1") - 1.0)
    k = clamp((t - tf) / 0.4)
    sh = math.sin(t * 90) * 14 * clamp((tf + 0.5 - t) / 0.5) if t > tf else 0
    sweep_text(base, "FIGHTERS!", W / 2 + sh, 990, "Black", 190, GOLD, "c", k * out, 24, (255, 150, 0),
               prog=(t - tf - 0.5) / 0.8, scale=1 + 0.6 * (1 - eob(k)))
    pill(base, W / 2, 1260, "MARKET OUTLOOK  •  XAUUSD", (40, 42, 56), 34, ap(t, tf + 0.5) * out, GOLD, "c")
    flash(base, t, tf, 0.25, col=(255, 200, 80), peak=0.45)


def sc_context(base, t, D, S):
    out = out_of(t, D)
    kicker(base, t, "MARKET CONTEXT", a=out)
    bm = DATA["bias"].get("BIAS UTAMA", "MARKET UPDATE").upper().split()
    l1, l2 = (" ".join(bm[:-1]), bm[-1]) if len(bm) > 1 else ("BIAS", bm[0])
    col = bias_col(" ".join(bm))
    a = ap(t, 0.2, 0.6)
    text(base, l1, 60, 220 + 30 * (1 - a), "Black", 92, WHITE, alpha=a * out)
    text(base, l2, 60, 330 + 30 * (1 - a), "Black", 92, col, alpha=a * out, glow=12, gcol=tuple(int(v * 0.6) for v in col))
    c = CH["h4"]
    z = 1.0 + 0.35 * eo(t / D)
    cw, chh = c.width / z, c.height / z
    cx0, cy0 = (c.width - cw) * 0.95, (c.height - chh) * 0.5
    crop = c.crop((int(cx0), int(cy0), int(cx0 + cw), int(cy0 + chh))).resize((960, 491), Image.BILINEAR).convert("RGBA")
    crop.putalpha(rounded_mask(960, 491, 22))
    pa = ap(t, 0.5, 0.6)
    comp(base, crop, 60, 500 + 50 * (1 - pa), pa * out)
    panel_frame(base, 60, 500 + 50 * (1 - pa), 960, 491, col, pa * out)
    pill(base, 84, 520 + 50 * (1 - pa), "H4", GOLD, 30, pa * out)
    c1 = dict(SPEC_SEGS["context"])["c1"]
    size = 44 if len(c1) < 160 else 38
    typed(base, c1, 60, 1060, 960, t, S.st("c1"), S.d("c1"), "SemiBold", size, WHITE, 1.32, out)
    st = S.en("c1") - 0.6
    c2 = ap(t, st, 0.6)
    d = ImageDraw.Draw(base, "RGBA")
    d.rounded_rectangle((60, 1450, 1020, 1710), 26, fill=(255, 255, 255, int(14 * c2 * out)), outline=rgba(TEAL, c2 * out), width=3)
    text(base, "LAST PRICE", 100, 1490, "Bold", 34, GREY, alpha=c2 * out)
    lp = DATA["last"]
    val = lp + 120 * (1 - eo((t - st) / 1.4)) * (1 if col == RED else -1)
    sweep_text(base, f"{val:,.2f}", 100, 1550, "Black", 110, (90, 230, 210), "l", c2 * out, 10, (0, 140, 130), prog=(t - st - 1.5) / 0.8)
    tri(d, 930, 1580, 46, col, col == RED, c2 * out)


def _levels():
    p = os.path.join(HERE, "data", "levels.json")
    return json.load(open(p)) if os.path.exists(p) else {}


LV = _levels()


def sc_mtf(base, t, D, S):
    out = out_of(t, D)
    kicker(base, t, "STRUKTUR MULTI-TIMEFRAME", a=out)
    segs = SPEC_SEGS["mtf"]
    t0 = S.st(segs[0][0])
    tw = 468
    for i, k in enumerate(("h4", "h1", "m30", "m15")):
        tr = LV.get(k, {}).get("trend", "")
        tag, col = ("BULLISH", GREEN) if tr == "bullish" else (("BEARISH", RED) if tr == "bearish" else (("NEUTRAL", AMBER) if tr else ("", GOLD)))
        a = ap(t, t0 + (i // 2) * 0.8 + (i % 2) * 0.25, 0.5)
        x = 60 + (i % 2) * (tw + 24)
        y = 220 + (i // 2) * 290 + 40 * (1 - a)
        im = M.chart_panel(k, tw)
        comp(base, im, x, y, a * out)
        panel_frame(base, x, y, tw, im.height, col, a * out)
        pill(base, x + 14, y + 14, k.upper(), GOLD, 26, a * out, padx=16, pady=8)
        if tag:
            d = ImageDraw.Draw(base, "RGBA")
            bw = text_w(tag, "ExtraBold", 26) + 30
            d.rounded_rectangle((x + tw - bw - 14, y + im.height - 60, x + tw - 14, y + im.height - 14), 12, fill=rgba(col, a * out))
            text(base, tag, x + tw - bw / 2 - 14, y + im.height - 50, "ExtraBold", 26, (12, 10, 10), "c", a * out)
    # typed sentences, auto-sized to fit
    top, bottom = 830, 1810
    for size in (40, 37, 34, 31, 28):
        hh = sum(len(wrap(s, "SemiBold", size, 920)) * size * 1.28 + 22 for _, s in segs)
        if hh <= bottom - top:
            break
    y = top
    for i, (k, s) in enumerate(segs):
        col = GOLD2 if i % 2 else WHITE
        h = typed(base, s, 80, y, 920, t, S.st(k), S.d(k), "SemiBold" if i % 2 == 0 else "Bold", size, col, 1.28, out)
        y += h + 22


def sc_bias(base, t, D, S):
    out = out_of(t, D)
    kicker(base, t, "MARKET BIAS", a=out)
    rows = list(DATA["bias"].items())
    shake = 0
    n = len(rows)
    gap = min(380, 1560 / max(1, n))
    for i, (lab, val) in enumerate(rows):
        sk = f"b{i + 1}"
        st = S.st(sk)
        k = clamp((t - st) / 0.4)
        if k <= 0:
            continue
        if lab == "FOCUS":
            col = GOLD
        elif lab == "LAST PRICE":
            col = TEAL
        else:
            col = bias_col(val) if lab == "BIAS UTAMA" else AMBER
        if st < t < st + 0.3:
            shake = math.sin(t * 100) * 8 * (st + 0.3 - t) / 0.3
        x = 60 + (1 - eob(k)) * (-1100 if i % 2 == 0 else 1100)
        y = 240 + i * gap
        d = ImageDraw.Draw(base, "RGBA")
        d.rounded_rectangle((x, y, x + 960, y + gap - 60), 30, fill=(14, 15, 22, int(235 * out)), outline=rgba(col, out), width=4)
        d.rectangle((x, y + 30, x + 12, y + gap - 90), fill=rgba(col, out))
        text(base, lab, x + 60, y + 44, "Bold", 38, GREY, alpha=out)
        if lab == "LAST PRICE":
            v = DATA["last"] - 137.26 * (1 - eo((t - st) / 1.2))
            sweep_text(base, f"{v:,.2f}", x + 60, y + 120, "Black", 112, (90, 230, 210), "l", out, 12, (0, 140, 130), prog=(t - st - 1.3) / 0.7)
        else:
            vv = val.upper()
            size = 96 if len(vv) < 15 else (80 if len(vv) < 19 else 64)
            sweep_text(base, vv, x + 60 + shake, y + 130, "Black", size, col, "l", out, 12, tuple(int(c * 0.6) for c in col),
                       prog=(t - st - 0.5) / 0.7)
        if lab == "BIAS UTAMA" and col in (RED, GREEN):
            tri(d, x + 880, y + 80, 34, col, col == RED, out)
    embers(base, t, 0.6 * out * clamp((t - S.st("b1")) / 0.5))
    lightning(base, t, S.st("b1"), 820, 0, 560, 560, seed=21)


# ---------- zone chart with dynamic framing
_zcache = {}


def zone_frame(zk):
    if zk in _zcache:
        return _zcache[zk]
    z = DATA[zk]
    c = CH["m5"]
    prices = [p for p, _ in z["path"]] + [z["lo"], z["hi"], M5_CLOSE or DATA["last"]]
    pmax, pmin = max(prices), min(prices)
    span = max(pmax - pmin, 10)
    pmax += span * 0.14
    pmin -= span * 0.14
    yt, yb = M5_Y(pmax), M5_Y(pmin)
    ph_full = yb - yt
    canvas = Image.new("RGB", (c.width, int(ph_full)), (0, 0, 0))
    src_top, src_bot = max(0, int(yt)), min(c.height, int(yb))
    if src_bot > src_top:
        canvas.paste(c.crop((0, src_top, c.width, src_bot)), (0, int(src_top - yt)))
    PW = 960
    PH = int(clamp(ph_full * PW / c.width, 300, 400))
    im = canvas.resize((PW, PH), Image.LANCZOS).convert("RGBA")
    im.putalpha(rounded_mask(PW, PH, 22))
    sy = PH / ph_full
    sx = PW / c.width
    _zcache[zk] = (im, yt, sx, sy)
    return _zcache[zk]


def live_candle(base, x, y_of, t, base_p, a=1.0, w=14):
    d = ImageDraw.Draw(base, "RGBA")
    o = base_p - 3.5
    c = base_p + 2.6 * math.sin(t * 3.1) + 1.3 * math.sin(t * 7.7)
    hi, lo = max(o, c) + 2.2, min(o, c) - 1.5
    col = GREEN if c >= o else RED
    d.line((x, y_of(hi), x, y_of(lo)), fill=rgba(col, a), width=3)
    d.rectangle((x - w / 2, y_of(max(o, c)), x + w / 2, y_of(min(o, c)) + 2), fill=rgba(col, a))
    return c


def chart_zone(base, t, zk, S, y0):
    z = DATA[zk]
    im, yt, sx, sy = zone_frame(zk)
    w = im.width
    a = ap(t, 0.1, 0.5)
    yy = y0 + 30 * (1 - a)
    comp(base, im, 60, yy, a)
    Y = lambda p: yy + (M5_Y(p) - yt) * sy
    X = lambda f: 60 + f * (1745 - 130) * sx
    d = ImageDraw.Draw(base, "RGBA")
    col = z["col"]
    k = ap(t, 0.5, 0.7)
    xr = X(1.0)
    xl = xr - (xr - 60) * k
    pulse = 0.5 + 0.5 * math.sin(t * 6)
    ya, yb = Y(z["hi"]), Y(z["lo"])
    if yb - ya < 8:
        ya, yb = ya - 4, yb + 4
    d.rectangle((xl, ya, xr, yb), fill=rgba(col, (0.22 + 0.12 * pulse) * k), outline=rgba(col, k), width=3)
    if k > 0.3:
        ly = ya - 40 if ya - 40 > yy + 60 else yb + 8
        text(base, z["rng"], 90, ly, "ExtraBold", 28, col, alpha=k)
    bkeys = [kk for kk in S.S if re.match(r"b\d+$", kk)]
    if bkeys:
        st, en = S.st(bkeys[0]), S.en(bkeys[-1])
        pk = ap(t, st - 0.3, 0.4)
        fx0, fx1 = 0.45, 0.93
        if pk > 0:
            d.rectangle((X(fx0), yy + 2, X(fx1), yy + im.height - 2), fill=(0, 0, 0, int(165 * pk)))
            for gy in range(int(yy) + 8, int(yy + im.height), 22):
                d.line((X(fx0), gy, X(fx0), gy + 10), fill=rgba(GOLD, 0.6 * pk), width=2)
            text(base, "SENARIO", X(fx0) + 14, yy + 14, "Black", 24, GOLD, alpha=pk)
            prog = clamp((t - st) / max(0.5, en - st - 0.3))
            pts = [(X(fx0 + 0.03 + f * (fx1 - fx0 - 0.06)), Y(p)) for p, f in z["path"]]
            segl = [math.hypot(b[0] - a_[0], b[1] - a_[1]) for a_, b in zip(pts, pts[1:])]
            target = sum(segl) * prog
            drawn, acc = [pts[0]], 0
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
                if len(drawn) - 1 > 4:
                    sx_, sy_ = pts[4]
                    rr = 18 + 6 * pulse
                    d.ellipse((sx_ - rr, sy_ - rr, sx_ + rr, sy_ + rr), outline=rgba(AMBER, pk), width=4)
                    lab = "RETEST" if z["cont"] else "SWEEP"
                    text(base, lab, sx_, sy_ - 62 if z["down"] else sy_ + 28, "Black", 24, AMBER, "c", pk)
                if prog >= 1:
                    ex, ey = pts[-1]
                    tri(d, ex, ey + (14 if z["down"] else -14), 18, col, z["down"], pk)
    base_p = M5_CLOSE or DATA["last"]
    c = live_candle(base, X(0.978), Y, t, base_p, a)
    py = Y(c)
    if yy < py < yy + im.height:
        for xx in range(60, int(X(1.0)), 22):
            d.line((xx, py, xx + 10, py), fill=rgba((90, 230, 210), 0.7 * a), width=2)
        d.rounded_rectangle((X(1.0) + 2, py - 16, 60 + w - 4, py + 16), 6, fill=rgba(TEAL, a))
        text(base, f"{c:.2f}", (X(1.0) + 60 + w) / 2, py - 10, "Bold", 18, WHITE, "c", a)
    panel_frame(base, 60, yy, w, im.height, col, a)
    pill(base, 84, yy + 16, "M5", GOLD, 26, a, padx=16, pady=8)
    return yy + im.height


def make_zone(zk):
    def sc(base, t, D, S):
        z = DATA[zk]
        out = out_of(t, D)
        col = z["col"]
        a = ap(t, 0.0, 0.4)
        pill(base, 60, 136, f"ZONE {z['num']}", col, 36, a, (10, 10, 14) if col != RED else WHITE)
        text(base, z["kind"] + z["extra"], 290, 146, "ExtraBold", 40, col, alpha=a)
        k = clamp(t / 0.5)
        sweep_text(base, z["rng"], 60, 215, "Black", 120, WHITE, "l", k, 14, tuple(int(c * 0.7) for c in col),
                   prog=(t - 0.7) / 0.8, scale=1 + 0.3 * (1 - eob(k)))
        bottom = chart_zone(base, t, zk, S, 360)
        y = bottom + 34
        d = ImageDraw.Draw(base, "RGBA")
        sa = ap(t, S.st("sec"), 0.4)
        tri(d, 96, y + 26, 22, col, z["down"], sa)
        text(base, z["sec"], 136, y + 4, "Black", 46, col, alpha=sa)
        y += 82
        # auto-size bullets so targets + warning fit above the ticker
        reserve = 190 + (len(wrap(z["warn"], "SemiBold", 32, 800)) * 42 + 70 if z["warn"] else 0)
        for size in (42, 39, 36, 33, 30):
            hh = sum(max(len(wrap(b, "SemiBold", size, 870)) * size * 1.25, 56) + 18 for b in z["bullets"])
            if y + hh + reserve < 1830:
                break
        for i, b in enumerate(z["bullets"]):
            st = S.st(f"b{i}")
            ba = ap(t, st, 0.3)
            xo = 30 * (1 - ba)
            d.ellipse((70 + xo, y + 2, 118 + xo, y + 50), fill=rgba(col, ba))
            text(base, str(i + 1), 94 + xo, y + 12, "Black", 28, (10, 10, 14), "c", ba)
            h = typed(base, b, 144, y + 2, 870, t, st, S.d(f"b{i}"), "SemiBold", size, WHITE, 1.25, 1.0)
            y += max(h, 56) + 18
        if z["tg"]:
            tst, tdur = S.st("tg"), S.d("tg")
            y += 6
            text(base, "TARGET", 70, y, "ExtraBold", 32, col, alpha=ap(t, tst, 0.4))
            y += 52
            n = len(z["tg"])
            gap = 70
            cw = min(250, (940 - gap * (n - 1)) / n)
            x = 70
            for i, v in enumerate(z["tg"]):
                ct = tst + 0.35 + i * (tdur - 0.35) / n
                kk = clamp((t - ct) / 0.3)
                if kk > 0:
                    s = 1 + 0.35 * (1 - eob(kk))
                    bw, bh = cw * s, 104 * s
                    bx, by = x + cw / 2 - bw / 2, y + 52 - bh / 2
                    d.rounded_rectangle((bx, by, bx + bw, by + bh), 22, fill=rgba(col, 0.16 * kk + 0.5 * max(0, 1 - (t - ct) / 0.5)),
                                        outline=rgba(col, kk), width=4)
                    text(base, f"TP{i + 1}", x + 22, y + 14, "Bold", 22, GREY, alpha=kk)
                    text(base, v, x + cw / 2 + 14, y + 36, "Black", 56 if cw >= 230 else 46, WHITE, "c", kk)
                if i < n - 1:
                    text(base, "→", x + cw + gap / 2, y + 30, "Black", 50, col, "c", clamp((t - ct - 0.2) / 0.3))
                x += cw + gap
            y += 104
        if z["warn"]:
            ws = S.st("w")
            wa = ap(t, ws, 0.3)
            yy = y + 26
            lines = wrap(z["warn"], "SemiBold", 32, 800)
            hh = len(lines) * 42 + 40
            blink = (0.6 + 0.4 * (1 if int((t - ws) * 4) % 2 == 0 else 0)) if t - ws < 1.5 else 1
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
    md = DATA["main"]
    big = md["big"]
    d = ImageDraw.Draw(base, "RGBA")
    if big:
        s2 = S.st("s2")
        a = ap(t, s2)
        text(base, big["pre"], W / 2, 300 + 30 * (1 - a), "Bold", 54, GREY, "c", a * out)
        k = clamp((t - s2 - 1.0) / 0.45)
        sweep_text(base, big["rng"], W / 2, 400, "Black", 150, WHITE, "c", k * out, 16, (180, 0, 30), prog=(t - s2 - 1.6) / 0.8,
                   scale=1 + 0.4 * (1 - eob(k)))
        s3 = S.st("s3")
        a = ap(t, s3)
        text(base, big["mid"], W / 2, 620 + 30 * (1 - a), "Bold", 54 if len(big["mid"]) < 26 else 44, GREY, "c", a * out)
        hit = s3 + 0.9
        fc = bias_col(big["focus"]) if "BUY" not in big["focus"].upper() else GREEN
        fc = RED if "SELL" in big["focus"].upper() else fc
        k = clamp((t - hit) / 0.45)
        sh = math.sin(t * 100) * 10 * clamp((hit + 0.4 - t) / 0.4) if t > hit else 0
        fs = 128 if len(big["focus"]) <= 14 else 100
        sweep_text(base, big["focus"].upper(), W / 2 + sh, 730, "Black", fs, fc, "c", k * out, 22, tuple(int(v * 0.8) for v in fc),
                   prog=(t - hit - 0.6) / 0.8, scale=1 + 0.5 * (1 - eob(k)))
        embers(base, t, out * clamp((t - hit) / 0.6))
        lightning(base, t, hit, 140, 560, 380, 980, seed=33)
        y0 = 960
    else:
        typed(base, md["p0"], 80, 260, 920, t, S.st("s2"), S.d("s2"), "Bold", 48, WHITE, 1.3, out)
        y0 = 760
    rest = md["rest"]
    if rest:
        a = ap(t, S.st(rest[0][0]), 0.5)
        d.rounded_rectangle((60, y0, 1020, 1800), 28, fill=(14, 15, 22, int(225 * a * out)), outline=rgba(GOLD, 0.6 * a * out), width=3)
        y = y0 + 50
        for size in (44, 40, 36, 32):
            if sum(len(wrap(s, "Bold", size, 860)) * size * 1.3 + 40 for _, s in rest) < 1780 - y:
                break
        for i, (k, s) in enumerate(rest):
            h = typed(base, s, 110, y, 860, t, S.st(k), S.d(k), "Bold" if i == 0 else "SemiBold", size, WHITE if i == 0 else GOLD2, 1.3, out)
            y += h + 40


def sc_two(base, t, D, S):
    out = out_of(t, D)
    kicker(base, t, "DUA SENARIO UTAMA" if len(DATA["two"]) == 2 else "SENARIO UTAMA", a=out)
    y = 240
    for ci, cd in enumerate(DATA["two"]):
        col = cd["col"]
        st = S.st(cd["key"])
        a = ap(t, st, 0.5)
        hgt = 160 + len(cd["steps"]) * 96
        d = ImageDraw.Draw(base, "RGBA")
        x = 60 + (1 - a) * (-200 if ci % 2 == 0 else 200)
        d.rounded_rectangle((x, y, x + 960, y + hgt), 30, fill=(14, 15, 22, int(235 * a * out)), outline=rgba(col, a * out), width=4)
        d.ellipse((x + 40, y + 36, x + 120, y + 116), fill=rgba(col, a * out))
        text(base, str(cd["n"]), x + 80, y + 50, "Black", 52, (10, 10, 14) if col == GREEN else WHITE, "c", a * out)
        sweep_text(base, cd["title"], x + 150, y + 44, "Black", 66 if len(cd["title"]) < 16 else 52, col, "l", a * out, prog=(t - st - 0.4) / 0.7)
        tri(d, x + 900, y + 76, 26, col, cd["down"], a * out)
        sy = y + 160
        for i, (kk, s) in enumerate(cd["steps"]):
            k = ap(t, S.st(kk), 0.3) * out
            if i > 0:
                d.line((x + 80, sy - 60, x + 80, sy - 6), fill=rgba(col, k), width=4)
            d.ellipse((x + 64, sy + 6, x + 96, sy + 38), outline=rgba(col, k), width=4, fill=rgba(col, 0.5 * k))
            typed(base, s, x + 130, sy + 2, 820, t, S.st(kk), S.d(kk), "Bold", 40 if len(s) < 40 else 34, WHITE, 1.2, out)
            sy += 96
        y += hgt + 50


def nice_step(rng, n=6):
    raw = rng / n
    mag = 10 ** math.floor(math.log10(raw))
    for m in (1, 2, 2.5, 5, 10):
        if raw <= m * mag:
            return m * mag
    return 10 * mag


def sc_levels(base, t, D, S):
    out = out_of(t, D)
    kicker(base, t, "KEY LEVELS TO WATCH", a=out)
    L = DATA["levels"]
    items = L["items"]
    ps = [i["lo"] for i in items] + [i["hi"] for i in items] + [L["last"]]
    for _, s in L["notes"]:
        for a_, b_ in re.findall(RNG, s):
            ps += [fnum(a_), fnum(b_)]
    top, bot = max(ps), min(ps)
    pad = (top - bot) * 0.06 + 2
    top, bot = top + pad, bot - pad
    y0, y1 = 250, 1380
    Y = lambda p: y0 + (top - p) / (top - bot) * (y1 - y0)
    d = ImageDraw.Draw(base, "RGBA")
    a = ap(t, 0.2, 0.5) * out
    d.line((200, y0, 200, y1), fill=rgba(GREY, a), width=3)
    step = nice_step(top - bot)
    p = math.ceil(bot / step) * step
    while p <= top:
        d.line((190, Y(p), 210, Y(p)), fill=rgba(GREY, a), width=2)
        text(base, f"{p:g}", 176, Y(p) - 14, "SemiBold", 26, GREY, "r", a)
        p += step
    for it in items:
        lab = it["label"].upper()
        res = "RESIST" in lab
        major = "MAJOR" in lab
        col = ((170, 20, 40) if major else RED) if res else ((10, 140, 90) if major else GREEN)
        st = S.st(it["key"])
        k = ap(t, st, 0.5)
        hl = max(0, 1 - (t - st) / 1.2) if t > st else 0
        xr = 230 + 790 * k
        ya, yb = Y(it["hi"]), Y(it["lo"])
        if yb - ya < 22:
            c_ = (ya + yb) / 2
            ya, yb = c_ - 11, c_ + 11
        d.rectangle((230, ya, xr, yb), fill=rgba(col, (0.32 + 0.4 * hl) * k * out), outline=rgba(col, k * out), width=3)
        cy = (ya + yb) / 2
        text(base, lab, 260, cy - 32 if yb - ya > 60 else cy - 13, "ExtraBold", 24, col, alpha=k * out)
        sweep_text(base, it["rng"], 1000, cy - 23, "Black", 40, WHITE, "r", k * out, prog=(t - st - 0.3) / 0.6)
    k = ap(t, S.st("l0"), 0.5) * out
    yl = Y(L["last"])
    pulse = 0.5 + 0.5 * math.sin(t * 7)
    for xx in range(210, 1020, 24):
        d.line((xx, yl, xx + 12, yl), fill=rgba((90, 230, 210), k), width=4)
    d.rounded_rectangle((640, yl - 26, 1020, yl + 26), 12, fill=rgba(TEAL, k * (0.7 + 0.3 * pulse)))
    text(base, f"NOW {L['last']:.2f}", 830, yl - 16, "Black", 32, WHITE, "c", k)
    notes = L["notes"]
    if notes:
        a = ap(t, S.st(notes[0][0]), 0.5) * out
        d.rounded_rectangle((60, 1420, 1020, 1815), 26, fill=(255, 170, 40, int(26 * a)), outline=rgba(AMBER, a), width=3)
        warn_icon(base, 116, 1474, 28, a)
        m = re.search(RNG, notes[0][1])
        text(base, f"{m[1]}–{m[2]}" if m else "PERHATIAN", 170, 1452, "Black", 48, AMBER, alpha=a)
        y = 1530
        for size in (36, 33, 30, 27):
            if sum(len(wrap(s, "SemiBold", size, 880)) * size * 1.3 + 10 for _, s in notes) < 270:
                break
        for i, (kk, s) in enumerate(notes):
            h = typed(base, s, 100, y, 880, t, S.st(kk), S.d(kk), "Bold" if i == 0 else "SemiBold", size, WHITE, 1.3, out)
            y += h + 10


def sc_check(base, t, D, S):
    out = out_of(t, D)
    kicker(base, t, "ENTRY CONFIRMATION CHECKLIST", a=out)
    y = 230
    d = ImageDraw.Draw(base, "RGBA")
    stamp = None
    for it in DATA["check"]:
        k_ = it["key"]
        st = S.st(k_)
        k = ap(t, st, 0.35) * out
        if it["kind"] == "tf":
            d.rounded_rectangle((60, y, 1020, y + 120), 24, fill=(255, 255, 255, int(12 * k)), outline=rgba(GOLD, 0.5 * k), width=2)
            check_box(base, 90, y + 30, 60, clamp((t - S.en(k_) + 0.4) / 0.35), GREEN, k)
            pill(base, 180, y + 30, it["a"], GOLD, 34, k, padx=20, pady=12)
            typed(base, it["b"], 180 + text_w(it["a"], "ExtraBold", 34) + 70, y + 38, 560, t, st, S.d(k_), "Bold", 42, WHITE, 1.2, out)
            y += 140
        elif it["kind"] == "rule":
            check_box(base, 90, y + 12, 60, clamp((t - S.en(k_) + 0.3) / 0.35), GREEN, k)
            h = typed(base, it["a"], 180, y + 14, 840, t, st, S.d(k_), "SemiBold", 40, WHITE, 1.28, out)
            y += max(h, 80) + 26
        else:
            stamp = it
    if stamp:
        st = S.st(stamp["key"]) + 0.5
        k = clamp((t - st) / 0.35)
        if k > 0:
            sh = math.sin(t * 110) * 12 * clamp((st + 0.4 - t) / 0.4)
            s = 1 + 0.8 * (1 - eob(k))
            yy = max(y + 40, 1500)
            yy = min(yy, 1580)
            box = Image.new("RGBA", (900, 230), (0, 0, 0, 0))
            bd = ImageDraw.Draw(box)
            bd.rounded_rectangle((4, 4, 895, 225), 26, outline=RED + (255,), width=8, fill=(60, 6, 14, 230))
            im1, p1 = sprite(stamp["a"], "Black", 62 if len(stamp["a"]) < 20 else 50, WHITE)
            box.alpha_composite(im1, (int(450 - im1.width / 2), 30 - p1 + 4))
            im2, p2 = sprite(stamp["b"], "Black", 84, RED, 10, (200, 0, 20))
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
    F = DATA["fund"]
    k = ap(t, 0.1, 0.5) * out
    pulse = 0.85 + 0.15 * math.sin(t * 6)
    warn_icon(base, W / 2, 280, int(80 * pulse), k)
    sweep_text(base, "FUNDAMENTAL WATCH", W / 2, 400, "Black", 76, AMBER, "c", k, 10, (180, 90, 0), prog=(t - 0.6) / 0.8)
    sents = F["sents"]
    d = ImageDraw.Draw(base, "RGBA")
    if F["cal"]:
        y = 540
        h = typed(base, sents[0][1], W / 2, y, 920, t, S.st(sents[0][0]), S.d(sents[0][0]), "Bold", 40, WHITE, 1.3, out, "c")
        st = S.st(sents[-1][0])
        a = ap(t, st, 0.6) * out
        x0, y0 = 120, max(560 + h + 40, 820)
        cal = F["cal"]
        d.rounded_rectangle((x0, y0, x0 + 840, y0 + 560), 34, fill=(18, 19, 28, int(240 * a)), outline=rgba(RED, a), width=4)
        d.rounded_rectangle((x0, y0, x0 + 840, y0 + 120), 34, fill=rgba(RED, a))
        d.rectangle((x0, y0 + 80, x0 + 840, y0 + 120), fill=rgba(RED, a))
        text(base, f"{cal['month']} {cal['year']}", x0 + 420, y0 + 38, "Black", 48, WHITE, "c", a)
        sweep_text(base, str(cal["day"]), x0 + 420, y0 + 150, "Black", 200, WHITE, "c", a, prog=(t - st - 2.0) / 0.8)
        text(base, cal["wd"], x0 + 420, y0 + 375, "Bold", 40, GREY, "c", a)
        evs = F["events"]
        for i, ev in enumerate(evs):
            b = ap(t, st + 1.0 + i * 0.4, 0.4) * out
            pill(base, x0 + 420 + (i - (len(evs) - 1) / 2) * 280, y0 + 450, ev, GOLD, 44, b, anchor="c")
        if len(sents) > 1:
            rest = " ".join(s for _, s in sents[1:])
            typed(base, rest, W / 2, y0 + 600, 920, t, S.st(sents[1][0]), S.en(sents[-1][0]) - S.st(sents[1][0]), "Bold", 36, GOLD2, 1.3, out, "c")
    else:
        y = 540
        for size in (44, 40, 36, 32):
            if sum(len(wrap(s, "Bold", size, 920)) * size * 1.3 + 30 for _, s in sents) < 1250:
                break
        for i, (kk, s) in enumerate(sents):
            h = typed(base, s, W / 2, y, 920, t, S.st(kk), S.d(kk), "Bold", size, WHITE if i % 2 == 0 else GOLD2, 1.3, out, "c")
            y += h + 30


def sc_outro(base, t, D, S):
    out = out_of(t, D, 0.6)
    O = DATA["outro"]
    first = O["first"]
    if "," in first:
        a_, b_ = first.split(",", 1)
    else:
        a_, b_ = "", first
    text(base, a_.strip() + ("," if a_ else ""), W / 2, 260, "Bold", 60, GREY, "c", ap(t, S.st("o1")) * out)
    typed(base, b_.strip(), W / 2, 350, 1000, t, S.st("o1") + 0.6, S.d("o1") - 0.6, "Black", 72 if len(b_) < 30 else 56, WHITE, 1.2, out, "c")
    d = ImageDraw.Draw(base, "RGBA")
    for i, (sk, s) in enumerate(O["steps"]):
        k = clamp((t - S.st(sk)) / 0.4)
        if k <= 0:
            continue
        y = 560 + i * 190
        x = 60 + (1 - eob(k)) * 300
        col = GOLD if i < len(O["steps"]) - 1 else GREEN
        d.rounded_rectangle((x, y, x + 960, y + 150), 28, fill=(16, 17, 26, int(235 * out)), outline=rgba(col, k * out), width=4)
        d.ellipse((x + 30, y + 30, x + 120, y + 120), fill=rgba(col, k * out))
        text(base, str(i + 1), x + 75, y + 46, "Black", 56, (10, 10, 14), "c", k * out)
        fs = 58 if text_w(s, "Black", 58) < 780 else 46
        sweep_text(base, s, x + 150, y + 48 + (58 - fs) / 2, "Black", fs, WHITE, "l", k * out, prog=(t - S.st(sk) - 0.3) / 0.6)
    st = S.st("oz")
    k = clamp((t - st) / 0.5)
    embers(base, t, 0.8 * k * out)
    sweep_text(base, "ZIQFX", W / 2, 1220, "Black", 170, GOLD, "c", k * out, 20, (255, 160, 0), prog=(t - st - 0.6) / 0.9,
               scale=1 + 0.4 * (1 - eob(k)))
    text(base, "TRADE SAFE  •  RISK FIRST", W / 2, 1440, "ExtraBold", 40, WHITE, "c", ap(t, st + 0.5) * out)
    para(base, "Analisis untuk tujuan pendidikan, bukan nasihat kewangan. Sentiasa urus risiko anda.", W / 2, 1660, 860,
         "Medium", 30, GREY, 1.3, ap(t, st + 1.0) * out, "c")
    flash(base, t, st, 0.25, peak=0.35)


BASE_FN = {"hook": sc_hook, "intro": sc_intro, "greet": sc_greet, "context": sc_context, "mtf": sc_mtf, "bias": sc_bias,
           "main": sc_main, "two": sc_two, "levels": sc_levels, "check": sc_check, "fund": sc_fund, "outro": sc_outro}
SPEC_SEGS = {}


def fn_for(name):
    return BASE_FN.get(name) or make_zone(name)


def init(path):
    global SPEC_SEGS
    load(path)
    SPEC_SEGS = {n: segs for n, _, _, segs in SPEC}


def render_frame(name, fi):
    info = TL[name]
    S = Seg(info["S"])
    D = info["D"]
    t = fi / FPS
    T = info["start"] + t
    base = background(T)
    fn_for(name)(base, t, D, S)
    if info["chrome"]:
        chrome3(base, T)
    g = 0.0
    if name == "hook":
        s2 = S.st("h2")
        if 0 <= t - s2 < 0.35:
            g = 1 - (t - s2) / 0.35
    return post(base, T, t, D, g)


def _worker_init(path):
    init(path)


def render_scene(name):
    D = TL[name]["D"]
    n = int(round(D * FPS))
    idx = ORDER.index(name)
    path = os.path.join(WORK, "seg", f"{idx:02d}_{name}.mp4")
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                          "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "21",
                          "-pix_fmt", "yuv420p", path], stdin=subprocess.PIPE)
    for fi in range(n):
        p.stdin.write(render_frame(name, fi).tobytes())
    p.stdin.close()
    p.wait()
    return path


# ============================================================ audio
def make_audio(path):
    import make as MM
    lowpass, highpass = MM.lowpass, MM.highpass
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

    for name, _, _, segs in SPEC:
        info = TL[name]
        for k, txt in segs:
            st, d = info["S"][k]
            v = read_wav(clip_path(say(txt))[:-4] + ".wav")
            s = int((info["start"] + st) * SR)
            e = min(n, s + len(v))
            vox[s:e] += v[: e - s]
    vox /= max(1e-6, np.abs(vox).max())
    beat = 60 / 128
    drop = TL["greet"]["start"]
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
    t, bar, pads = 0.0, 0, {}
    while t < TOTAL:
        root, chord = prog[bar % 4]
        dur = beat * 4
        if bar % 4 not in pads:
            tp = np.arange(int(dur * SR)) / SR
            env = np.minimum(1, tp / 0.3) * np.minimum(1, (dur - tp) / 0.3)
            pad = np.zeros(len(tp))
            for m in chord:
                for det in (-0.12, 0.12):
                    for h, ga in ((1, 1), (2, 0.35), (3, 0.18)):
                        pad += ga * np.sin(2 * np.pi * mf(m) * (1 + det / 100) * h * tp + rs.rand() * 6)
            pads[bar % 4] = pad * env * 0.05
        add(mus, pads[bar % 4], t, 1.0, -0.2)
        add(mus, pads[bar % 4], t + 0.012, 1.0, 0.2)
        for b in range(4):
            tb = t + b * beat
            if drop <= t < end_drums:
                add(mus, kick, tb, 0.9)
                if b in (1, 3):
                    add(mus, snare, tb, 0.55)
                for s16 in range(4):
                    add(mus, hat, tb + s16 * beat / 4, 0.22 if s16 % 2 else 0.12, 0.3)
                for e8 in range(2):
                    tt = np.arange(int(beat / 2 * SR)) / SR
                    bs = np.tanh(2.5 * np.sin(2 * np.pi * mf(root - 12 + (12 if (b == 3 and e8 == 1) else 0)) * tt)) \
                        * np.minimum(1, tt / 0.04) * np.exp(-tt * 3)
                    add(mus, bs, tb + e8 * beat / 2, 0.28)
            else:
                tt = np.arange(int(beat * SR)) / SR
                add(mus, np.sin(2 * np.pi * mf(root - 12) * tt) * np.exp(-tt * 2.5), tb, 0.25)
        t += dur
        bar += 1
    rl = drop - TL["intro"]["start"]
    tr = np.arange(int(rl * SR)) / SR
    add(mus, highpass(rs.randn(len(tr)), 2500) * (tr / rl) ** 3 * 0.35 + 0.15 * np.sin(2 * np.pi * (200 * tr + 300 * tr ** 2 / rl)) * (tr / rl) ** 2,
        TL["intro"]["start"])
    env = np.convolve(np.abs(vox), np.ones(int(0.25 * SR)) / int(0.25 * SR), mode="same")
    env = np.clip(env / (env.max() * 0.25 + 1e-9), 0, 1)
    mus *= (1 - 0.62 * env)[:, None]
    # sfx
    ti = np.arange(int(1.6 * SR)) / SR
    boom = np.sin(2 * np.pi * (38 + 40 * np.exp(-ti * 8)) * ti) * np.exp(-ti * 2.6) + lowpass(rs.randn(len(ti)), 400) * np.exp(-ti * 6) * 0.6
    tw = np.arange(int(0.5 * SR)) / SR
    wn = rs.randn(len(tw))
    whoosh = (highpass(wn, 1500) * 0.5 + lowpass(wn, 1500) * 0.3) * np.sin(np.pi * tw / 0.5) ** 2
    tg_ = np.arange(int(0.25 * SR)) / SR
    glitch = np.round(np.sign(np.sin(2 * np.pi * 180 * tg_ * (1 + 3 * tg_))) * (rs.rand(len(tg_)) > 0.5) * np.exp(-tg_ * 10) * 2) / 4
    tc = np.arange(int(0.7 * SR)) / SR
    ching = sum(np.sin(2 * np.pi * f * tc) * np.exp(-tc * dc) * g for f, dc, g in ((2093, 6, .5), (2637, 7, .4), (3136, 8, .3), (4186, 10, .2)))
    ching[: len(tc)] += highpass(rs.randn(len(tc)), 5000) * np.exp(-tc * 40) * 0.5
    ta_ = np.arange(int(0.9 * SR)) / SR
    alarm = lowpass(np.sign(np.sin(2 * np.pi * np.where((ta_ * 4).astype(int) % 2 == 0, 880, 660) * ta_)) * 0.35, 3000) * np.minimum(1, (0.9 - ta_) / 0.05)
    tt_ = np.arange(int(0.012 * SR)) / SR
    tick = highpass(rs.randn(len(tt_)), 3000) * np.exp(-tt_ * 400)
    tth = np.arange(int(2.2 * SR)) / SR
    thunder = highpass(rs.randn(len(tth)), 1500) * np.exp(-tth * 9) * (rs.rand(len(tth)) > 0.6) * 0.6 \
        + lowpass(rs.randn(len(tth)), 200) * np.exp(-tth * 1.6) * 3.0 + np.sin(2 * np.pi * 35 * tth) * np.exp(-tth * 2) * 0.6
    tsw = np.arange(int(1.4 * SR)) / SR
    sword = sum(np.sin(2 * np.pi * f * tsw) * np.exp(-tsw * dc) for f, dc in ((1523, 3), (2311, 4), (3547, 5), (4890, 7), (6210, 9))) * 0.3 \
        + highpass(rs.randn(len(tsw)), 4000) * np.exp(-tsw * 30) * 0.8
    tb_ = np.arange(int(0.15 * SR)) / SR
    blip = np.sin(2 * np.pi * 1320 * tb_) * np.exp(-tb_ * 30)

    def A(name, k=None, off=0.0):
        return TL[name]["start"] + (TL[name]["S"][k][0] if k else 0) + off

    for i, name in enumerate(ORDER):
        st = TL[name]["start"]
        if i:
            add(sfx, whoosh, st - 0.35, 0.35)
        add(sfx, glitch, st, 0.2)
        add(sfx, boom, st, 0.55 if name in ("hook", "greet", "bias", "main", "check") else 0.3)
    add(sfx, sword, A("intro", None, 0.15), 0.55)
    add(sfx, thunder, A("hook", "h1"), 0.55)
    add(sfx, thunder, A("hook", "h2"), 0.55)
    if "bias" in TL:
        add(sfx, thunder, A("bias", "b1"), 0.55)
    if "main" in TL and DATA["main"]["big"]:
        add(sfx, thunder, A("main", "s3", 0.9), 0.55)
    if "check" in TL:
        for it in DATA["check"]:
            if it["kind"] == "stamp":
                add(sfx, thunder, A("check", it["key"], 0.5), 0.55)
            else:
                add(sfx, blip, A("check", it["key"]) + TL["check"]["S"][it["key"]][1] - 0.2, 0.25)
    typed_keys = {"context": ["c1"], "mtf": [k for k, _ in SPEC_SEGS.get("mtf", [])]}
    if "main" in DATA:
        typed_keys["main"] = [k for k, _ in DATA["main"]["rest"]]
    if "two" in DATA:
        typed_keys["two"] = [k for c in DATA["two"] for k, _ in c["steps"]]
    if "levels" in DATA:
        typed_keys["levels"] = [k for k, _ in DATA["levels"]["notes"]]
    if "check" in DATA:
        typed_keys["check"] = [it["key"] for it in DATA["check"] if it["kind"] != "stamp"]
    for name in ORDER:
        if re.match(r"z\d", name):
            S = TL[name]["S"]
            typed_keys[name] = [k for k in S if re.match(r"b\d+$", k) or k == "w"]
            if "tg" in S:
                nt = len(DATA[name]["tg"])
                for i in range(nt):
                    add(sfx, ching, TL[name]["start"] + S["tg"][0] + 0.35 + i * (S["tg"][1] - 0.35) / nt, 0.35)
            if "w" in S:
                add(sfx, alarm, A(name, "w"), 0.22)
    rr = random.Random(5)
    for nm, keys in typed_keys.items():
        if nm not in TL:
            continue
        for k in keys:
            st, d = TL[nm]["S"][k]
            x = 0
            while x < d * 0.85:
                add(sfx, tick, TL[nm]["start"] + st + x, rr.uniform(0.05, 0.09), rr.uniform(-0.3, 0.3))
                x += rr.uniform(0.05, 0.09)
    end = int(TOTAL * SR)
    fo = int(3.0 * SR)
    fade = np.ones(n)
    fade[end - fo:end] = np.linspace(1, 0, fo)
    fade[end:] = 0
    mix = mus / max(1e-6, np.abs(mus).max()) * 0.42 + sfx / max(1e-6, np.abs(sfx).max()) * 0.45 + vox[:, None] * 0.85
    mix = np.tanh(mix * fade[:, None] * 1.1) * 0.93
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((mix[:end] * 32767).astype(np.int16).tobytes())


# ============================================================ main
if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    mode, path = sys.argv[1], sys.argv[2]
    os.makedirs(os.path.join(WORK, "seg"), exist_ok=True)
    o = load(path, timeline=False)
    SPEC_SEGS = {n: segs for n, _, _, segs in SPEC}
    if mode == "parse":
        for name, ch, tail, segs in SPEC:
            print(f"== {name}")
            for k, s in segs:
                print(f"   {k:4s} {say(s)}")
        print("zones:", {k: (v["rng"], v["sec"], v["tg"], [round(p) for p, _ in v["path"]]) for k, v in DATA.items() if re.match(r"z\d", k)})
        sys.exit(0)
    if mode in ("tts", "dry"):
        gen_tts(dry=mode == "dry")
        sys.exit(0)
    init(path)
    if not TL:
        sys.exit("no timeline for this outlook: run `make3.py tts` (or `dry` for previews) first")
    if mode == "preview":
        for arg in sys.argv[3:]:
            nm, tt = arg.split(":")
            render_frame(nm, int(float(tt) * FPS)).save(os.path.join(WORK, f"p3_{nm}_{tt}.png"))
        sys.exit(0)
    if mode == "render":
        if any(v.get("dry") for v in TL.values()):
            sys.exit("timeline is a dry estimate: run `make3.py tts` before rendering")
        os.makedirs(OUT_DIR, exist_ok=True)
        print("total", TOTAL)
        make_audio(os.path.join(WORK, "mix.wav"))
        names = sorted(ORDER, key=lambda n: -TL[n]["D"])
        with Pool(4, initializer=_worker_init, initargs=(path,)) as pool:
            pool.map(render_scene, names)
        with open(os.path.join(WORK, "list.txt"), "w") as f:
            for i, n in enumerate(ORDER):
                f.write(f"file '{os.path.join(WORK, 'seg', f'{i:02d}_{n}.mp4')}'\n")
        tag = f"{o['date'][3]}-{MONTHS.index(o['date'][2]) + 1:02d}-{o['date'][1]:02d}" if o["date"] else "latest"
        out = os.path.join(OUT_DIR, f"ZIQFX_XAUUSD_Outlook_{tag}.mp4")
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", os.path.join(WORK, "list.txt"),
                        "-i", os.path.join(WORK, "mix.wav"), "-c:v", "libx264", "-preset", "medium", "-crf", "23",
                        "-pix_fmt", "yuv420p", "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-ar", "44100", "-c:a", "aac",
                        "-b:a", "192k", "-movflags", "+faststart", out], check=True)
        print(out)
