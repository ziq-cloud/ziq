"""Weekly data for the Monday weekly outlook: D1 + W1 candles, charts and structure summary.

Usage:
  python3 weekly.py            # data/d1.json, data/w1.json, charts/d1.png, charts/w1.png + printed summary
"""
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import xau_charts as XC
import xau_levels as XL

XC.TFS = {"d1": ("1day", 160), "w1": ("1week", 120)}
XC.LABEL.update({"d1": "D1", "w1": "W1"})
XC.KEEP = 120

if __name__ == "__main__":
    XC.fetch()
    os.makedirs(XC.OUT, exist_ok=True)
    for tf in XC.TFS:
        XC.render_one(tf)
    for tf in XC.TFS:
        r = XL.analyse(tf)
        print(f"[{tf.upper()}] {r['first_time']} -> {r['last_time']}  close {r['close']}  EMA20 {r['ema20']}  EMA50 {r['ema50']}"
              f"  trend {r['trend']}  structure {r['structure']}  ATR14 {r['atr14']}  range {r['range_low']}-{r['range_high']}")
        print("   swing highs:", ", ".join(f"{p} ({t[:10]})" for t, p in r["swing_highs"]))
        print("   swing lows: ", ", ".join(f"{p} ({t[:10]})" for t, p in r["swing_lows"]))
