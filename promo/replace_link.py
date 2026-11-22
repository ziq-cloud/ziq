"""Replace the sign-up link on the end card of the TRAXA "Wild trader" promo with a referral link.

Usage: python3 replace_link.py [input.mp4] [output.mp4]

Only frames of the end card (from END_START seconds) are touched:
  * the typed URL under "TRY IT FREE" is erased and redrawn (same typewriter progress and fade),
  * the "at traxatradingapp.com." subtitle is redrawn with the referral link (same highlight states).
"""
import os, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "assets/wild_trader_promo_BM.mp4")
DST = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, "wild_trader_promo_BM_ZIQFX.mp4")
NEW_URL = "traxatradingapp.com/?invite=ZIQFX"
W, H, FPS = 1080, 1920, 30
END_START = 57.5                      # end card begins here

URL_BAND = (120, 1100, 960, 1200)     # x0, y0, x1, y1 of the typed URL
URL_X0, URL_X1 = 241, 839             # left / right edge of the original URL when fully typed
CAP_BAND = (100, 1700, 980, 1825)     # subtitle area
GOLD, GRAY, BORDER, DARK = (224, 186, 87), (125, 125, 125), (95, 90, 80), (15, 13, 10)

url_font = ImageFont.truetype(os.path.join(HERE, "assets/fonts/oxanium-latin-500-normal.woff"), 46)
while url_font.getlength(NEW_URL) > 820: url_font = ImageFont.truetype(url_font.path, url_font.size - 1)
cap_font = ImageFont.truetype("/usr/share/fonts/opentype/inter/Inter-Bold.otf", 36)

def redraw_url(img, a):
    x0, y0, x1, y1 = URL_BAND
    br = a[y0:y1, x0:x1].max(axis=2)
    cols = np.where((br > 10).any(axis=0))[0]
    if not len(cols): return
    prog = min(1.0, max(0.0, (cols.max() + x0 - URL_X0) / (URL_X1 - URL_X0)))
    alpha = br.max() / 255
    a[y0:y1, x0:x1] = a[y0 - 4:y0 - 2, x0:x1].mean(axis=0, keepdims=True).astype(np.uint8)  # erase (background is flat black)
    img.paste(Image.fromarray(a[y0:y1, x0:x1]), (x0, y0))
    n = round(prog * len(NEW_URL))
    if n == 0: return
    d = ImageDraw.Draw(img); full = url_font.getlength(NEW_URL)
    c = tuple(int(255 * alpha) for _ in range(3))
    d.text((W / 2 - full / 2, (y0 + y1) / 2 + 2), NEW_URL[:n], font=url_font, fill=c, anchor="lm")
    if prog < 1:  # typing cursor
        cx = W / 2 - full / 2 + url_font.getlength(NEW_URL[:n]) + 6
        d.line([(cx, (y0 + y1) / 2 - 22), (cx, (y0 + y1) / 2 + 22)], fill=c, width=3)

def redraw_caption(img, a):
    x0, y0, x1, y1 = CAP_BAND
    cap = a[y0:y1, x0:x1].astype(int)
    lit = cap.max(axis=2) > 12
    cols = np.where(lit.any(axis=0))[0]
    if not len(cols) or cols.max() - cols.min() < 420: return   # short subtitle ("free," etc.): leave it
    gold = (cap[..., 0] > 180) & (cap[..., 1] > 140) & (cap[..., 2] < 130)
    gx = np.where(gold.any(axis=0))[0]
    state = "plain" if not len(gx) else ("at" if gx.max() + x0 < 420 else "url")
    alpha = cap.max() / 255
    a[y0:y1, x0:x1] = 0; img.paste(Image.fromarray(a[y0:y1, x0:x1]), (x0, y0))
    d = ImageDraw.Draw(img)
    words = [("at", state == "at"), (NEW_URL, state == "url")]
    gap = 14; ws = [cap_font.getlength(w) for w, _ in words]
    tw = sum(ws) + gap; cy = 1762; sx = W / 2 - tw / 2
    sc = lambda c: tuple(int(v * alpha) for v in c)
    d.rectangle([sx - 22, cy - 26, sx + tw + 22, cy + 26], outline=sc(BORDER), width=2)
    x = sx
    for (w, hl), wd in zip(words, ws):
        if hl:
            d.rectangle([x - 6, cy - 21, x + wd + 6, cy + 21], fill=sc(GOLD))
            d.text((x, cy), w, font=cap_font, fill=sc(DARK), anchor="lm")
        else:
            dim = state == "at" and w == NEW_URL
            d.text((x, cy), w, font=cap_font, fill=sc(GRAY if dim else (255, 255, 255)), anchor="lm")
        x += wd + gap

def main():
    dec = subprocess.Popen(["ffmpeg", "-v", "error", "-i", SRC, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                            "-i", "-", "-i", SRC, "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-crf", "18", "-preset", "medium",
                            "-pix_fmt", "yuv420p", "-c:a", "copy", "-movflags", "+faststart", DST], stdin=subprocess.PIPE)
    n = 0; size = W * H * 3
    while True:
        buf = dec.stdout.read(size)
        if len(buf) < size: break
        if n / FPS >= END_START:
            a = np.frombuffer(buf, np.uint8).reshape(H, W, 3).copy()
            img = Image.fromarray(a)
            redraw_url(img, a); a = np.array(img)
            redraw_caption(img, a)
            buf = img.tobytes()
        enc.stdin.write(buf); n += 1
    enc.stdin.close(); enc.wait(); dec.wait()
    print("done", DST, n, "frames")

if __name__ == "__main__":
    main()
