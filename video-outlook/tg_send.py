"""Post ZIQFX outlook text, charts and videos to the Telegram group.

Usage:
  python3 tg_send.py text  outlooks/2026-11-26.md [--pin]
  python3 tg_send.py photo charts/h1.png "caption"
  python3 tg_send.py video out/ZIQFX_XAUUSD_Outlook_2026-11-26.mp4 "caption"

Token: env TELEGRAM_BOT_TOKEN, else the local file ~/.ziq_telegram_token (never committed).
Chat:  env TELEGRAM_CHAT_ID, else the INDICATOR SUPPORT group.
Bots may upload at most 50 MB, so videos are re-encoded to 720x1280 until they fit.
"""
import json, os, subprocess, sys, tempfile

DEFAULT_CHAT = "-1003846220767"  # INDICATOR SUPPORT
LIMIT = 48 * 1024 * 1024


def token():
    t = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not t:
        p = os.path.expanduser("~/.ziq_telegram_token")
        if os.path.exists(p):
            t = open(p).read().strip()
    if not t:
        sys.exit("Telegram token missing: set TELEGRAM_BOT_TOKEN or ~/.ziq_telegram_token")
    return t


CHAT = os.environ.get("TELEGRAM_CHAT_ID", DEFAULT_CHAT)


def call(method, fields=None, files=None, timeout=600):
    args = ["curl", "-s", "--max-time", str(timeout), f"https://api.telegram.org/bot{token()}/{method}"]
    for k, v in (fields or {}).items():
        args += ["--form-string", f"{k}={v}"]
    for k, path in (files or {}).items():
        args += ["-F", f"{k}=@{path}"]
    r = subprocess.run(args, capture_output=True, text=True)
    try:
        d = json.loads(r.stdout)
    except json.JSONDecodeError:
        sys.exit(f"Telegram {method}: bad response {r.stdout[:200]} {r.stderr[:200]}")
    if not d.get("ok"):
        sys.exit(f"Telegram {method} failed: {d.get('description')}")
    return d["result"]


def send_text(text):
    # Telegram text limit is 4096 chars: split on separator lines / paragraphs
    chunks, cur = [], ""
    for block in text.split("\n\n"):
        piece = (cur + "\n\n" + block) if cur else block
        if len(piece) > 3900 and cur:
            chunks.append(cur)
            cur = block
        else:
            cur = piece
    if cur:
        chunks.append(cur)
    ids = [call("sendMessage", {"chat_id": CHAT, "text": c})["message_id"] for c in chunks]
    return ids


def pin(message_id):
    """Pin a message (bot needs the 'Pin messages' admin right); never fatal."""
    r = subprocess.run(["curl", "-s", "--max-time", "30", f"https://api.telegram.org/bot{token()}/pinChatMessage",
                        "--form-string", f"chat_id={CHAT}", "--form-string", f"message_id={message_id}",
                        "--form-string", "disable_notification=true"], capture_output=True, text=True)
    try:
        d = json.loads(r.stdout)
    except json.JSONDecodeError:
        d = {"ok": False, "description": r.stdout[:120]}
    if not d.get("ok"):
        print(f"pin failed: {d.get('description')}", file=sys.stderr)
    return d.get("ok", False)


def fit_video(path):
    if os.path.getsize(path) <= LIMIT:
        return path
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path],
                               capture_output=True, text=True).stdout.strip())
    out = os.path.join(tempfile.mkdtemp(), "tg_" + os.path.basename(path))
    kbps = int(LIMIT * 8 / 1024 / dur * 0.92) - 96  # video bitrate budget
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", path, "-vf", "scale=720:1280", "-c:v", "libx264",
                    "-preset", "medium", "-b:v", f"{max(kbps, 300)}k", "-maxrate", f"{max(kbps, 300) * 2}k",
                    "-bufsize", f"{max(kbps, 300) * 4}k", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "96k",
                    "-movflags", "+faststart", out], check=True)
    return out


def send_video(path, caption=""):
    p = fit_video(path)
    thumb = p + ".jpg"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", "3", "-i", p, "-frames:v", "1", "-vf", "scale=320:-1", thumb])
    files = {"video": p}
    if os.path.exists(thumb):
        files["thumbnail"] = thumb
    call("sendVideo", {"chat_id": CHAT, "caption": caption[:1000], "supports_streaming": "true",
                       "width": "720", "height": "1280"}, files, timeout=1200)
    return os.path.getsize(p)


def send_photo(path, caption=""):
    call("sendPhoto", {"chat_id": CHAT, "caption": caption[:1000]}, {"photo": path})


if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    kind, path = sys.argv[1], sys.argv[2]
    cap = sys.argv[3] if len(sys.argv) > 3 and not sys.argv[3].startswith("--") else ""
    if kind == "text":
        ids = send_text(open(path, encoding="utf-8").read().strip())
        print("messages:", len(ids))
        if "--pin" in sys.argv[3:]:
            print("pinned:", pin(ids[0]))
    elif kind == "photo":
        send_photo(path, cap)
        print("photo sent")
    elif kind == "video":
        print("video sent, bytes:", send_video(path, cap))
    else:
        sys.exit(__doc__)
