"""Weekly scorecard: check each daily outlook's zones and targets against what price actually did.

Usage:
  python3 scorecard.py fetch                 # data/week_m15.json (last ~8 trading days of M15)
  python3 scorecard.py report 2026-11-23     # score outlooks for the week starting that Monday -> stdout + JSON

Rules (mechanical, no judgement):
  • A trading day = 06:00 Malaysia time to 06:00 the next day (outlook validity window).
  • Zone TOUCHED  = price traded inside [lo, hi] that day.
  • Confirmation block (SELL/BUY confirmation): counted from the first touch; a target is HIT when price
    later reached it (low <= target for SELL, high >= target for BUY).
  • Continuation block (SELL/BUY continuation): ACTIVE when an M15 candle closed beyond the zone
    (below lo for SELL, above hi for BUY); targets counted after that close.
  • Bias: STRONG BEARISH/BEARISH right if the day closed below its open, BULLISH right if above.
This ignores entry confirmation and whether a stop would have been hit first; it measures whether the
levels mattered, not trading P/L.
"""
import json, os, subprocess, sys, time
from datetime import datetime, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)


def fetch():
    url = ("https://api.twelvedata.com/time_series?symbol=XAU/USD&interval=15min&outputsize=1000"
           "&timezone=Asia/Kuala_Lumpur&order=ASC")
    for attempt in range(4):
        r = subprocess.run(["curl", "-s", "--max-time", "60", url, "-H", "Authorization: apikey proxy-injected"],
                           capture_output=True, text=True)
        try:
            d = json.loads(r.stdout)
        except json.JSONDecodeError:
            d = {}
        if d.get("status") == "ok":
            break
        print("retry", d.get("message", r.stdout[:120]), file=sys.stderr)
        time.sleep(10 * (attempt + 1))
    else:
        sys.exit("failed to fetch M15 history")
    bars = [{"t": v["datetime"], "o": float(v["open"]), "h": float(v["high"]), "l": float(v["low"]), "c": float(v["close"])}
            for v in d["values"]]
    os.makedirs(os.path.join(HERE, "data"), exist_ok=True)
    json.dump(bars, open(os.path.join(HERE, "data", "week_m15.json"), "w"))
    print(f"{len(bars)} M15 bars {bars[0]['t']} -> {bars[-1]['t']}")


def day_bars(bars, day):
    start = datetime.strptime(day, "%Y-%m-%d").replace(hour=6)
    end = start + timedelta(days=1)
    s, e = start.strftime("%Y-%m-%d %H:%M"), end.strftime("%Y-%m-%d %H:%M")
    return [b for b in bars if s <= b["t"] < e]


def score_block(bars, z, side, cont, tg):
    lo, hi = z["lo"], z["hi"]
    start = None
    for i, b in enumerate(bars):
        if cont:
            if (side == "SELL" and b["c"] < lo) or (side == "BUY" and b["c"] > hi):
                start = i
                break
        elif b["l"] <= hi and b["h"] >= lo:
            start = i
            break
    if start is None:
        return {"status": "not_active", "hit": []}
    after = bars[start:]
    hit = []
    for t in tg:
        if side == "SELL" and min(b["l"] for b in after) <= t:
            hit.append(t)
        elif side == "BUY" and max(b["h"] for b in after) >= t:
            hit.append(t)
    return {"status": "active", "since": bars[start]["t"][11:16], "hit": hit}


def report(monday):
    import make3
    bars = json.load(open(os.path.join(HERE, "data", "week_m15.json")))
    d0 = datetime.strptime(monday, "%Y-%m-%d")
    days = [(d0 + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(5)]
    out = []
    for day in days:
        path = os.path.join(HERE, "outlooks", f"{day}.md")
        if not os.path.exists(path):
            continue
        o = make3.parse(path)
        db = day_bars(bars, day)
        if not db:
            out.append({"day": day, "note": "no price data"})
            continue
        bias = o["bias"].get("BIAS UTAMA", "")
        up = db[-1]["c"] > db[0]["o"]
        bias_ok = ("BEAR" in bias.upper() and not up) or ("BULL" in bias.upper() and up) if bias else None
        rec = {"day": day, "open": round(db[0]["o"], 2), "close": round(db[-1]["c"], 2),
               "high": round(max(b["h"] for b in db), 2), "low": round(min(b["l"] for b in db), 2),
               "bias": bias, "bias_ok": bias_ok, "zones": []}
        for z in o["zones"]:
            for b in z["blocks"]:
                tg = [make3.fnum(x) for x in b["tg"]]
                r = score_block(db, z, b["side"], b["type"] == "continuation", tg)
                rec["zones"].append({"zone": z["num"], "kind": z["kind"], "rng": z["rng"],
                                     "block": f"{b['side']} {b['type']}", "targets": b["tg"], **r})
        out.append(rec)
    json.dump(out, open(os.path.join(HERE, "data", f"scorecard_{monday}.json"), "w"), indent=1)
    tot_blocks = sum(1 for r in out for z in r.get("zones", []) if z["status"] == "active")
    tot_tg = sum(len(z["targets"]) for r in out for z in r.get("zones", []) if z["status"] == "active")
    tot_hit = sum(len(z["hit"]) for r in out for z in r.get("zones", []))
    bias_n = [r["bias_ok"] for r in out if r.get("bias_ok") is not None]
    for r in out:
        print(f"\n{r['day']}  O {r.get('open')} H {r.get('high')} L {r.get('low')} C {r.get('close')}  bias {r.get('bias')} "
              f"-> {'BETUL' if r.get('bias_ok') else 'SALAH' if r.get('bias_ok') is False else '-'}")
        for z in r.get("zones", []):
            print(f"   Z{z['zone']} {z['kind']} {z['rng']} {z['block']}: {z['status']}"
                  + (f" from {z['since']}, hit {z['hit']} of {z['targets']}" if z["status"] == "active" else ""))
    print(f"\nTOTAL: active setups {tot_blocks}, targets hit {tot_hit}/{tot_tg}, bias correct {sum(bias_n)}/{len(bias_n)}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    if sys.argv[1] == "fetch":
        fetch()
    elif sys.argv[1] == "report" and len(sys.argv) > 2:
        report(sys.argv[2])
    else:
        sys.exit(__doc__)
