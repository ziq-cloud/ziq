"""Replace the small "traxatradingapp.com" under the end-card button of the TRAXA
"Signal group sorok loss" promo with a referral link.

Usage: python3 replace_link_signal_group.py [input.mp4] [output.mp4] [invite_code]
"""
import os, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "assets/signal_group_sorok_loss_BM.mp4")
DST = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, "signal_group_sorok_loss_BM_ZIQFX.mp4")
CODE = sys.argv[3] if len(sys.argv) > 3 else "ZIQFX"
NEW_URL = f"traxatradingapp.com/?invite={CODE}"
W, H, FPS = 1080, 1920, 30

ERASE = (220, 1392, 860, 1476)      # x0, y0, x1, y1 around the original link (text spans 374-703 x 1417-1449)
TEXT_CY = 1433
BG_LEVEL, FULL_LEVEL = 16, 146      # band brightness with no text / with the text fully shown
COLOR = (150, 148, 152)             # the original light grey
font = ImageFont.truetype("/usr/share/fonts/opentype/inter/Inter-Regular.otf", 34)

def probe_duration(p):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p],
                                capture_output=True, text=True).stdout)

def process(a, start_t, t):
    if t < start_t: return None
    x0, y0, x1, y1 = ERASE
    band = a[y0 + 8:y1 - 8, x0:x1].max(axis=2)
    alpha = float(min(1.0, max(0.0, (int(band.max()) - BG_LEVEL) / (FULL_LEVEL - BG_LEVEL))))
    if alpha <= 0.01: return None
    top, bot = a[y0 - 2, x0:x1].astype(float), a[y1 + 1, x0:x1].astype(float)
    k = np.linspace(0, 1, y1 - y0)[:, None, None]
    a[y0:y1, x0:x1] = (top[None] * (1 - k) + bot[None] * k).astype(np.uint8)   # rebuild the soft glow
    img = Image.fromarray(a).convert("RGBA")
    lay = Image.new("RGBA", (W, 160), (0, 0, 0, 0))   # text fades in from blurred to sharp, like the original
    ImageDraw.Draw(lay).text((W / 2, 80), NEW_URL, font=font, anchor="mm", fill=COLOR + (int(255 * alpha),))
    if alpha < 0.98: lay = lay.filter(ImageFilter.GaussianBlur(7 * (1 - alpha)))
    img.alpha_composite(lay, (0, TEXT_CY - 80))
    return img.convert("RGB").tobytes()

def main():
    dur = probe_duration(SRC); start_t = dur - 3.3   # end card is on screen for the last ~3.3 s
    dec = subprocess.Popen(["ffmpeg", "-v", "error", "-i", SRC, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                            "-i", "-", "-i", SRC, "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-crf", "18", "-preset", "medium",
                            "-pix_fmt", "yuv420p", "-c:a", "copy", "-movflags", "+faststart", DST], stdin=subprocess.PIPE)
    n, size = 0, W * H * 3
    while True:
        buf = dec.stdout.read(size)
        if len(buf) < size: break
        out = process(np.frombuffer(buf, np.uint8).reshape(H, W, 3).copy(), start_t, n / FPS)
        enc.stdin.write(out or buf); n += 1
    enc.stdin.close(); enc.wait(); dec.wait()
    print("done", DST, n, "frames")

if __name__ == "__main__":
    main()
