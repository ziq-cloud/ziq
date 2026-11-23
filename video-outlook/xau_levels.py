"""Summarise XAU/USD structure per timeframe from data/<tf>.json (run xau_charts.py fetch first).

Usage:
  python3 xau_levels.py            # prints a compact report + writes data/levels.json

Per timeframe: last close, EMA20/EMA50, trend label, ATR14, last swing highs/lows (fractals),
session high/low of the last bars, and simple market-structure (HH/HL vs LH/LL).
"""
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
TFS = ["m5", "m15", "m30", "h1", "h4"]


def ema(vals, n):
    k = 2 / (n + 1)
    out, e = [], vals[0]
    for v in vals:
        e = v * k + e * (1 - k)
        out.append(e)
    return out


def atr(bars, n=14):
    trs = []
    for i, b in enumerate(bars):
        pc = bars[i - 1]["c"] if i else b["o"]
        trs.append(max(b["h"] - b["l"], abs(b["h"] - pc), abs(b["l"] - pc)))
    return sum(trs[-n:]) / min(n, len(trs))


def swings(bars, k=3):
    hs, ls = [], []
    for i in range(k, len(bars) - k):
        win = bars[i - k:i + k + 1]
        if bars[i]["h"] == max(b["h"] for b in win):
            hs.append((bars[i]["t"], round(bars[i]["h"], 2)))
        if bars[i]["l"] == min(b["l"] for b in win):
            ls.append((bars[i]["t"], round(bars[i]["l"], 2)))
    return hs, ls


def structure(hs, ls):
    if len(hs) < 2 or len(ls) < 2:
        return "unclear"
    hh = hs[-1][1] > hs[-2][1]
    hl = ls[-1][1] > ls[-2][1]
    if hh and hl:
        return "bullish (HH + HL)"
    if not hh and not hl:
        return "bearish (LH + LL)"
    return "mixed (" + ("HH" if hh else "LH") + " + " + ("HL" if hl else "LL") + ")"


def analyse(tf):
    bars = json.load(open(os.path.join(DATA, f"{tf}.json")))["bars"]
    closes = [b["c"] for b in bars]
    e20, e50 = ema(closes, 20)[-1], ema(closes, 50)[-1]
    last = closes[-1]
    if last > e20 > e50:
        trend = "bullish"
    elif last < e20 < e50:
        trend = "bearish"
    else:
        trend = "neutral / transition"
    k = 3 if tf in ("m5", "m15") else 2
    hs, ls = swings(bars, k)
    return {
        "tf": tf, "last_time": bars[-1]["t"], "close": round(last, 2),
        "ema20": round(e20, 2), "ema50": round(e50, 2), "trend": trend,
        "atr14": round(atr(bars), 2), "structure": structure(hs, ls),
        "range_high": round(max(b["h"] for b in bars), 2), "range_low": round(min(b["l"] for b in bars), 2),
        "first_time": bars[0]["t"],
        "swing_highs": hs[-5:], "swing_lows": ls[-5:],
    }


def main():
    if not os.path.exists(os.path.join(DATA, "m5.json")):
        sys.exit("no data: run `python3 xau_charts.py fetch` first")
    rep = {tf: analyse(tf) for tf in TFS}
    json.dump(rep, open(os.path.join(DATA, "levels.json"), "w"), indent=1)
    for tf, r in rep.items():
        print(f"[{tf.upper()}] {r['first_time']} -> {r['last_time']}  close {r['close']}  EMA20 {r['ema20']}  EMA50 {r['ema50']}"
              f"  trend {r['trend']}  structure {r['structure']}  ATR14 {r['atr14']}  range {r['range_low']}-{r['range_high']}")
        print("   swing highs:", ", ".join(f"{p} ({t[5:16]})" for t, p in r["swing_highs"]))
        print("   swing lows: ", ", ".join(f"{p} ({t[5:16]})" for t, p in r["swing_lows"]))


if __name__ == "__main__":
    main()
