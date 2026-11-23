# ZIQFX — XAUUSD Market Outlook Video

Generates a vertical (1080×1920) market-outlook video for XAUUSD: animated charts, zones, checklist,
Malay voiceover (ElevenLabs) and music/SFX. Charts are drawn from live Twelve Data candles, so no
screenshots are needed.

## Files

| File | Purpose |
|------|---------|
| `xau_charts.py` | Fetch XAU/USD candles (M5, M15, M30, H1, H4) from Twelve Data and draw TradingView-style charts into `charts/` |
| `make.py` | Shared drawing helpers (fonts, text sprites, background, icons) and the original v1 video |
| `make2.py` | Outlook video generator: narration spec, TTS, scenes, effects, audio mix |
| `m5.png` … `h4.png` | Fallback screenshots (used only when `charts/` has not been generated, or with `ZIQ_CHARTS=screenshot`) |

## Requirements

- Python 3, `ffmpeg`, Inter font (`/usr/share/fonts/opentype/inter/`)
- `pip install -r requirements.txt`
- API keys, entered as **network secrets** in the Claude cloud environment (never commit them):
  - `api.twelvedata.com` — header `Authorization`, prefix `apikey`
  - `api.elevenlabs.io` — header `xi-api-key` (needs *Text to Speech* + *Voices read*)

The scripts send the placeholder `proxy-injected`; the session proxy replaces it with the real key.

## Workflow

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
