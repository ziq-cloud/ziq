#!/usr/bin/env python3
"""Post a daily trader motivation quote to a Telegram channel.

Env vars:
  TELEGRAM_BOT_TOKEN  bot token from @BotFather (required unless --dry-run)
  TELEGRAM_CHAT_ID    "@channel_username" or numeric id like -100xxxxxxxxxx

The quote is chosen by the date in Malaysia time (UTC+8), so it rotates
through quotes.txt in order and every day gets a different line.
"""

from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import os
import sys
import urllib.parse
import urllib.request
from pathlib import Path

MYT = dt.timezone(dt.timedelta(hours=8))
QUOTES_FILE = Path(__file__).with_name("quotes.txt")
HARI = ["Isnin", "Selasa", "Rabu", "Khamis", "Jumaat", "Sabtu", "Ahad"]
BULAN = ["Januari", "Februari", "Mac", "April", "Mei", "Jun", "Julai",
         "Ogos", "September", "Oktober", "November", "Disember"]


def load_quotes(path: Path = QUOTES_FILE) -> list[str]:
    lines = [ln.strip() for ln in path.read_text(encoding="utf-8").splitlines()]
    quotes = [ln for ln in lines if ln and not ln.startswith("#")]
    if not quotes:
        raise ValueError(f"No quotes found in {path}")
    return quotes


def pick_quote(quotes: list[str], day: dt.date) -> str:
    return quotes[day.toordinal() % len(quotes)]


def build_message(quote: str, day: dt.date) -> str:
    tarikh = f"{HARI[day.weekday()]}, {day.day} {BULAN[day.month - 1]} {day.year}"
    return (
        f"🌅 <b>Selamat Pagi, Traders!</b>\n"
        f"<i>{tarikh}</i>\n\n"
        f"💬 {html.escape(quote)}\n\n"
        f"#MotivasiTrader #Trading"
    )


def send(token: str, chat_id: str, text: str) -> dict:
    data = urllib.parse.urlencode(
        {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    ).encode()
    req = urllib.request.Request(
        f"https://api.telegram.org/bot{token}/sendMessage", data=data
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--dry-run", action="store_true", help="print, don't send")
    p.add_argument("--date", help="YYYY-MM-DD (default: today in MYT)")
    args = p.parse_args(argv)

    day = dt.date.fromisoformat(args.date) if args.date else dt.datetime.now(MYT).date()
    text = build_message(pick_quote(load_quotes(), day), day)

    if args.dry_run:
        print(text)
        return 0

    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        print("Error: set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID", file=sys.stderr)
        return 1
    try:
        result = send(token, chat_id, text)
    except urllib.error.HTTPError as e:
        print(f"Telegram error {e.code}: {e.read().decode(errors='replace')}", file=sys.stderr)
        return 1
    if not result.get("ok"):
        print(f"Telegram error: {result}", file=sys.stderr)
        return 1
    print("Posted:", text.splitlines()[3])
    return 0


if __name__ == "__main__":
    sys.exit(main())
