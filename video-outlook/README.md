# ZIQFX — XAUUSD Market Outlook Video

Generates a vertical (1080×1920) market-outlook video for XAUUSD: animated charts, zones, checklist,
Malay voiceover (ElevenLabs) and music/SFX. Charts are drawn from live Twelve Data candles, so no
screenshots are needed.

## Files

| File | Purpose |
|------|---------|
| `xau_charts.py` | Fetch XAU/USD candles (M5, M15, M30, H1, H4) from Twelve Data and draw TradingView-style charts into `charts/` |
| `xau_levels.py` | Per-timeframe summary (EMA20/50 trend, market structure, ATR14, swing highs/lows) from `data/` — basis for the daily outlook |
| `make.py` | Shared drawing helpers (fonts, text sprites, background, icons) and the original v1 video |
| `make3.py` | **Main generator**: builds the whole video straight from an outlook text file in the `TEMPLATE_outlook.md` format (parse → ElevenLabs voice → render) |
| `TEMPLATE_outlook.md` | Official ZIQFX outlook wording/format. Daily outlooks are written in this exact format into `outlooks/YYYY-MM-DD.md` |
| `make_news.py` | **News video** (fundamental + technical + forecast + scenarios + trading plan) from a file in `NEWS_TEMPLATE.md` format, saved as `news/YYYY-MM-DD.md` |
| `NEWS_TEMPLATE.md` | Format for high-impact news outlooks. Unknown forecast/previous values are written as `—` (shown as "belum diumumkan") |
| `make2.py` | Outlook video generator: narration spec, TTS, scenes, effects, audio mix |
| `m5.png` … `h4.png` | Fallback screenshots (used only when `charts/` has not been generated, or with `ZIQ_CHARTS=screenshot`) |

## Requirements

- Python 3, `ffmpeg`, Inter font (`/usr/share/fonts/opentype/inter/`)
- `pip install -r requirements.txt`
- API keys, entered as **network secrets** in the Claude cloud environment (never commit them):
  - `api.twelvedata.com` — header `Authorization`, prefix `apikey`
  - `api.elevenlabs.io` — header `xi-api-key` (needs *Text to Speech* + *Voices read*)

The scripts send the placeholder `proxy-injected`; the session proxy replaces it with the real key.

## Workflow (from an outlook text file)

```bash
cd video-outlook
python3 xau_charts.py all && python3 xau_levels.py      # live charts + trend summary
python3 make3.py parse  outlooks/2026-11-24.md          # check what will be narrated
python3 make3.py tts    outlooks/2026-11-24.md          # ElevenLabs Daud M clips (cached per sentence)
python3 make3.py render outlooks/2026-11-24.md          # -> out/ZIQFX_XAUUSD_Outlook_2026-11-24.mp4
```

Use `make3.py dry` instead of `tts` to preview frames (`make3.py preview <file> z1a:10`) without spending voice credits.

## Legacy workflow (make2.py, hard-coded 23 Nov text)

```bash
cd video-outlook
python3 xau_charts.py all     # 1. live candles -> charts/*.png + charts/map.json
# 2. edit the outlook text in make2.py (SPEC + ZONES: bias, zones, bullets, targets, warnings)
python3 make2.py tts          # 3. voice clips (ElevenLabs, Daud M) + timeline.json
python3 make2.py preview z1:10 levels:20   # optional still frames
python3 make2.py all          # 4. render -> ZIQFX_XAUUSD_Outlook_..._raw.mp4
# 5. compress + loudness normalise
ffmpeg -i ZIQFX_XAUUSD_Outlook_23Nov2026_v3_raw.mp4 -c:v libx264 -crf 23 -pix_fmt yuv420p \
  -af loudnorm=I=-14:TP=-1.5:LRA=11 -c:a aac -b:a 192k -movflags +faststart out.mp4
```

Notes:
- Twelve Data free tier allows 8 requests/minute; `xau_charts.py` paces its 5 requests.
- Closed-market weekend bars (Sat 06:00 → Mon 07:00 Malaysia time) are dropped.
- Spot XAU/USD can differ by a few points from a broker's `XAUUSD.c` feed.
- ElevenLabs voice: *Daud M – Deep & Confident Narrator* (`VbhRlZCHaUh9hxeUyRBD`), model `eleven_multilingual_v2`.
- Zone chart framing in `make2.py` (`ZY0`, zone `path` prices) was tuned for the 23 Nov 2026 levels;
  adjust when the price range changes.

## High-impact news video

The USD event calendar comes from the FXMacroData skill in `claude-trading-skills`
(`skills/fxmacrodata-calendar/scripts/fetch_calendar.py --currency usd --min-tier 1`, host `api.fxmacrodata.com`).

```bash
python3 make_news.py parse  news/2026-11-25.md
python3 make_news.py tts    news/2026-11-25.md   # or `dry` + `preview` without voice credits
python3 make_news.py render news/2026-11-25.md   # -> out/ZIQFX_XAUUSD_News_2026-11-25.mp4
```
