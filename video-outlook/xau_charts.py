"""Fetch XAU/USD candles from Twelve Data and render TradingView-style chart images.

Usage:
  python3 xau_charts.py fetch            # download M5..H4 candles into data/
  python3 xau_charts.py render           # draw charts/<tf>.png + charts/map.json from data/
  python3 xau_charts.py all              # both

The API key is injected by the session proxy (Authorization: apikey ...), never stored here.
Output images are 1745x892 (same frame the video generator uses for chart panels).
"""
import json, math, os, subprocess, sys, time
from datetime import datetime

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
OUT = os.path.join(HERE, "charts")
TZ = "Asia/Kuala_Lumpur"
KEEP = 220
TFS = {tf: (iv, 400) for tf, iv in (("m5", "5min"), ("m15", "15min"), ("m30", "30min"), ("h1", "1h"), ("h4", "4h"))}
LABEL = {"m5": "M5", "m15": "M15", "m30": "M30", "h1": "H1", "h4": "H4"}

W, H = 1745, 892
PLOT_R = 1615          # plot area right edge (price axis to the right)
PLOT_T, PLOT_B = 95, 830
UP, DN = (38, 166, 154), (239, 83, 80)
GRID = (36, 38, 46)
AXIS = (200, 203, 212)
FONT = "/usr/share/fonts/opentype/inter/Inter-{}.otf"


def f(w, s):
    return ImageFont.truetype(FONT.format(w), s)


def market_open(ts):
    """Gold is closed roughly Sat 06:00 -> Mon 07:00 Malaysia time; the feed fills that gap with flat bars."""
    dt = datetime.strptime(ts[:16], "%Y-%m-%d %H:%M")
    wd, hr = dt.weekday(), dt.hour
    if wd == 5 and hr >= 6:
        return False
    if wd == 6:
        return False
    if wd == 0 and hr < 7:
        return False
    return True


def fetch():
    os.makedirs(DATA, exist_ok=True)
    for k, (tf, (iv, n)) in enumerate(TFS.items()):
        if k:
            time.sleep(8)  # free tier: 8 credits per minute
        url = (f"https://api.twelvedata.com/time_series?symbol=XAU/USD&interval={iv}"
               f"&outputsize={n}&timezone={TZ}&order=ASC")
        for attempt in range(4):
            r = subprocess.run(["curl", "-s", "--max-time", "30", url, "-H", "Authorization: apikey proxy-injected"],
                               capture_output=True, text=True)
            try:
                d = json.loads(r.stdout)
            except json.JSONDecodeError:
                d = {"status": "error", "message": r.stdout[:200]}
            if d.get("status") == "ok":
                break
            print(f"{tf}: {d.get('message', d)} (retry)", file=sys.stderr)
            time.sleep(8 * (attempt + 1))
        else:
            sys.exit(f"failed to fetch {tf}")
        bars = [{"t": v["datetime"], "o": float(v["open"]), "h": float(v["high"]), "l": float(v["low"]), "c": float(v["close"])}
                for v in d["values"]]
        # drop weekend / closed-market filler bars (zero range)
        bars = [b for b in bars if market_open(b["t"])][-KEEP:]
        json.dump({"tf": tf, "interval": iv, "tz": TZ, "bars": bars}, open(os.path.join(DATA, f"{tf}.json"), "w"))
        print(f"{tf}: {len(bars)} bars, last {bars[-1]['t']} close {bars[-1]['c']:.2f}")


def nice_step(rng, n=8):
    raw = rng / n
    mag = 10 ** math.floor(math.log10(raw))
    for m in (1, 2, 2.5, 5, 10):
        if raw <= m * mag:
            return m * mag
    return 10 * mag


def render_one(tf):
    d = json.load(open(os.path.join(DATA, f"{tf}.json")))
    bars = d["bars"]
    hi = max(b["h"] for b in bars)
    lo = min(b["l"] for b in bars)
    pad = (hi - lo) * 0.06
    p_top, p_bot = hi + pad, lo - pad
    b_ = (PLOT_B - PLOT_T) / (p_top - p_bot)   # px per price unit
    a_ = PLOT_T + p_top * b_                     # y = a - b*p
    Y = lambda p: a_ - b_ * p
    im = Image.new("RGB", (W, H), (0, 0, 0))
    d_ = ImageDraw.Draw(im)
    n = len(bars)
    slot = (PLOT_R - 20) / n
    X = lambda i: 10 + slot * (i + 0.5)
    # price grid + labels
    step = nice_step(p_top - p_bot)
    p = math.ceil(p_bot / step) * step
    while p <= p_top:
        y = Y(p)
        for x in range(0, PLOT_R, 14):
            d_.line((x, y, x + 6, y), fill=GRID)
        d_.text((PLOT_R + 12, y - 15), f"{p:.2f}", font=f("Medium", 26), fill=AXIS)
        p += step
    # time grid + labels (about 7 labels)
    every = max(1, n // 7)
    for i in range(every // 2, n, every):
        x = X(i)
        for y in range(PLOT_T - 60, PLOT_B, 14):
            d_.line((x, y, x, y + 6), fill=GRID)
        dt = datetime.strptime(bars[i]["t"][:16], "%Y-%m-%d %H:%M")
        lab = dt.strftime("%d %b %H:%M")
        tw = d_.textlength(lab, font=f("Medium", 24))
        d_.text((x - tw / 2, PLOT_B + 22), lab, font=f("Medium", 24), fill=AXIS)
    d_.line((PLOT_R, 0, PLOT_R, H), fill=(60, 63, 72), width=2)
    d_.line((0, PLOT_B + 10, PLOT_R, PLOT_B + 10), fill=(60, 63, 72), width=2)
    # candles
    bw = max(2, slot * 0.62)
    for i, b in enumerate(bars):
        col = UP if b["c"] >= b["o"] else DN
        x = X(i)
        d_.line((x, Y(b["h"]), x, Y(b["l"])), fill=col, width=max(1, int(slot * 0.14)))
        y0, y1 = Y(max(b["o"], b["c"])), Y(min(b["o"], b["c"]))
        d_.rectangle((x - bw / 2, y0, x + bw / 2, max(y1, y0 + 1)), fill=col)
    # last price line + tag
    last = bars[-1]
    col = UP if last["c"] >= last["o"] else DN
    yl = Y(last["c"])
    for x in range(0, PLOT_R, 10):
        d_.line((x, yl, x + 5, yl), fill=col, width=2)
    d_.rectangle((PLOT_R + 2, yl - 18, W - 2, yl + 18), fill=col)
    d_.text((PLOT_R + 12, yl - 15), f"{last['c']:.2f}", font=f("Bold", 26), fill=(255, 255, 255))
    # header
    d_.text((16, 10), f"XAUUSD  •  {LABEL[tf]}", font=f("Bold", 34), fill=(235, 236, 240))
    d_.text((16, 52), "Gold Spot vs US Dollar  •  Twelve Data", font=f("Regular", 24), fill=(150, 154, 166))
    im.save(os.path.join(OUT, f"{tf}.png"))
    return {"a": a_, "b": b_, "plot_r": PLOT_R, "first": bars[0]["t"], "last": last["t"], "close": last["c"],
            "high": hi, "low": lo}


def render():
    os.makedirs(OUT, exist_ok=True)
    mp = {tf: render_one(tf) for tf in TFS}
    json.dump(mp, open(os.path.join(OUT, "map.json"), "w"), indent=1)
    for tf, m in mp.items():
        print(f"{tf}: {m['first']} -> {m['last']}  close {m['close']:.2f}  range {m['low']:.2f}-{m['high']:.2f}")


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "all"
    if mode in ("fetch", "all"):
        fetch()
    if mode in ("render", "all"):
        render()
