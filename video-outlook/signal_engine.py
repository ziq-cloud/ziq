"""Paper-trading signal engine for the daily ZIQFX outlook zones (Phase 1: report only, nothing is posted).

Usage:
  python3 signal_engine.py run 2026-11-26 [--bars data/week_m15.json]   # signals + outcomes for one trading day
  python3 signal_engine.py stats                                         # cumulative paper results (signals/*.json)

Rules (fixed, mechanical — so the results are honest and repeatable):
  • Session window: 07:00–05:00 Malaysia time (Asia + London + New York; skips the illiquid roll-over hours). Max 3 signals per day, one open at a time.
  • SELL confirmation (resistance zone lo–hi): after an M15 candle trades into the zone, the first bearish M15 candle
    (close < open) that closes below the previous candle's low and below the zone top is the trigger.
    Entry = its close. SL = highest high since the zone touch + 2.0. BUY confirmation is the mirror at support.
  • SELL continuation (support zone): an M15 close below lo arms it; the first later candle that trades back up to lo
    and closes bearish below lo is the trigger. SL = zone hi + 2.0. BUY continuation is the mirror.
  • Skip the signal if risk (|entry − SL|) is under 4 or over 25 points, or if reward to TP1 is under 1R.
  • Management on later M15 bars: SL first if a bar touches both (conservative). After TP1, SL moves to entry.
    Exit at TP3, at SL, or at the 05:00 cut-off close. Result is in R (risk multiples) and points.
"""
import glob, json, os, sys
from datetime import datetime, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
SIG_DIR = os.path.join(HERE, "signals")
BUF, MIN_RISK, MAX_RISK, MAX_PER_DAY = 2.0, 4.0, 25.0, 3


def load_bars(path):
    d = json.load(open(path))
    return d["bars"] if isinstance(d, dict) else d


def window(bars, day):
    s = datetime.strptime(day, "%Y-%m-%d").replace(hour=7)
    e = s + timedelta(hours=22)
    a, b = s.strftime("%Y-%m-%d %H:%M"), e.strftime("%Y-%m-%d %H:%M")
    return [x for x in bars if a <= x["t"] < b]


def setups(outlook):
    out = []
    for z in outlook["zones"]:
        for b in z["blocks"]:
            tg = [float(x) for x in b["tg"]]
            if tg:
                out.append(dict(zone=z["num"], kind=z["kind"], rng=z["rng"], lo=z["lo"], hi=z["hi"], side=b["side"],
                                cont=b["type"] == "continuation", tg=tg))
    return out


def find_trigger(bars, s, start):
    """Return (index, entry, sl) of the first trigger at or after start, else None."""
    touched, armed, ext = None, False, None
    for i in range(max(start, 1), len(bars)):
        b, p = bars[i], bars[i - 1]
        if not s["cont"]:
            if touched is None and b["l"] <= s["hi"] and b["h"] >= s["lo"]:
                touched = i
                ext = b["h"] if s["side"] == "SELL" else b["l"]
            if touched is not None:
                ext = max(ext, b["h"]) if s["side"] == "SELL" else min(ext, b["l"])
                if s["side"] == "SELL" and b["c"] < b["o"] and b["c"] < p["l"] and b["c"] < s["hi"]:
                    return i, b["c"], ext + BUF
                if s["side"] == "BUY" and b["c"] > b["o"] and b["c"] > p["h"] and b["c"] > s["lo"]:
                    return i, b["c"], ext - BUF
        else:
            if not armed:
                armed = (b["c"] < s["lo"]) if s["side"] == "SELL" else (b["c"] > s["hi"])
                continue
            if s["side"] == "SELL" and b["h"] >= s["lo"] and b["c"] < b["o"] and b["c"] < s["lo"]:
                return i, b["c"], s["hi"] + BUF
            if s["side"] == "BUY" and b["l"] <= s["hi"] and b["c"] > b["o"] and b["c"] > s["hi"]:
                return i, b["c"], s["lo"] - BUF
    return None


def manage(bars, i0, side, entry, sl, tg):
    risk = abs(entry - sl)
    stop, hit = sl, []
    for b in bars[i0 + 1:]:
        if side == "SELL":
            if b["h"] >= stop:
                return dict(exit=round(stop, 2), exit_at=b["t"], reason="SL" if not hit else "BE", tp_hit=hit,
                            r=round((entry - stop) / risk, 2), pts=round(entry - stop, 2))
            for k, t in enumerate(tg):
                if k + 1 not in hit and b["l"] <= t:
                    hit.append(k + 1)
                    if k == 0:
                        stop = entry
            if len(hit) == len(tg):
                return dict(exit=tg[-1], exit_at=b["t"], reason=f"TP{len(tg)}", tp_hit=hit,
                            r=round((entry - tg[-1]) / risk, 2), pts=round(entry - tg[-1], 2))
        else:
            if b["l"] <= stop:
                return dict(exit=round(stop, 2), exit_at=b["t"], reason="SL" if not hit else "BE", tp_hit=hit,
                            r=round((stop - entry) / risk, 2), pts=round(stop - entry, 2))
            for k, t in enumerate(tg):
                if k + 1 not in hit and b["h"] >= t:
                    hit.append(k + 1)
                    if k == 0:
                        stop = entry
            if len(hit) == len(tg):
                return dict(exit=tg[-1], exit_at=b["t"], reason=f"TP{len(tg)}", tp_hit=hit,
                            r=round((tg[-1] - entry) / risk, 2), pts=round(tg[-1] - entry, 2))
    last = bars[-1]["c"]
    pnl = (entry - last) if side == "SELL" else (last - entry)
    return dict(exit=round(last, 2), exit_at=bars[-1]["t"], reason="cut-off", tp_hit=hit, r=round(pnl / risk, 2), pts=round(pnl, 2))


def run(day, bars_path):
    import make3
    outlook = make3.parse(os.path.join(HERE, "outlooks", f"{day}.md"))
    bars = window(load_bars(bars_path), day)
    if len(bars) < 4:
        sys.exit(f"not enough M15 bars in the 07:00–05:00 window for {day}")
    sigs, cursor, used = [], 1, set()
    while sum(1 for x in sigs if not x.get("skipped")) < MAX_PER_DAY and cursor < len(bars):
        best = None
        for k, s in enumerate(setups(outlook)):
            if k in used:
                continue
            r = find_trigger(bars, s, cursor)
            if r and (best is None or r[0] < best[1][0]):
                best = (k, r)
        if not best:
            break
        k, (i, entry, sl) = best
        s = setups(outlook)[k]
        used.add(k)
        risk = abs(entry - sl)
        tg = [t for t in s["tg"] if (t < entry if s["side"] == "SELL" else t > entry)]
        if not (MIN_RISK <= risk <= MAX_RISK) or not tg or abs(tg[0] - entry) < risk:
            sigs.append(dict(skipped=True, why=f"risk {risk:.1f} / TP1 {tg[0] if tg else '-'}", at=bars[i]["t"],
                             setup=f"Z{s['zone']} {s['side']} {'continuation' if s['cont'] else 'confirmation'} {s['rng']}"))
            cursor = i + 1
            continue
        res = manage(bars, i, s["side"], entry, sl, tg)
        sigs.append(dict(at=bars[i]["t"], setup=f"Z{s['zone']} {s['side']} {'continuation' if s['cont'] else 'confirmation'} {s['rng']}",
                         side=s["side"], entry=round(entry, 2), sl=round(sl, 2), tp=tg, risk=round(risk, 2), **res))
        cursor = next((j for j, b in enumerate(bars) if b["t"] > res["exit_at"]), len(bars))
    os.makedirs(SIG_DIR, exist_ok=True)
    json.dump({"day": day, "signals": sigs}, open(os.path.join(SIG_DIR, f"{day}.json"), "w"), indent=1)
    print(f"== {day} ({len(bars)} M15 bars, 07:00–05:00 MYT)")
    for s in sigs:
        if s.get("skipped"):
            print(f"   skip {s['at'][11:16]} {s['setup']} ({s['why']})")
        else:
            print(f"   {s['at'][11:16]} {s['side']} @ {s['entry']} SL {s['sl']} TP {s['tp']} -> {s['reason']} "
                  f"{s['pts']:+.2f} pts ({s['r']:+.2f}R) TP hit {s['tp_hit']}")
    if not sigs:
        print("   no signal")


def stats():
    rows = [s for f in sorted(glob.glob(os.path.join(SIG_DIR, "*.json"))) for s in json.load(open(f))["signals"]
            if not s.get("skipped")]
    if not rows:
        print("no signals yet")
        return
    wins = [s for s in rows if s["r"] > 0]
    be = [s for s in rows if s["r"] == 0]
    print(f"signals {len(rows)} | win {len(wins)} | breakeven {len(be)} | loss {len(rows) - len(wins) - len(be)} | "
          f"win rate {len(wins) / len(rows) * 100:.0f}% | total {sum(s['r'] for s in rows):+.2f}R / {sum(s['pts'] for s in rows):+.1f} pts")


if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == "run":
        bp = sys.argv[sys.argv.index("--bars") + 1] if "--bars" in sys.argv else os.path.join(HERE, "data", "m15.json")
        run(sys.argv[2], bp)
    elif len(sys.argv) >= 2 and sys.argv[1] == "stats":
        stats()
    else:
        sys.exit(__doc__)
