# Auto post motivasi trader ke Telegram

Setiap pagi pukul **7:45 pagi (waktu Malaysia)**, GitHub Actions hantar satu ayat semangat dari `quotes.txt` ke channel Telegram. Ayat bertukar setiap hari ikut urutan dalam fail.

## Setup (sekali sahaja)

1. **Buat bot:** chat dengan `@BotFather`, taip `/newbot`, dan salin token yang dia bagi.
2. **Tambah bot ke channel sebagai admin**, dengan kebenaran *Post Messages*.
3. **Simpan secrets di GitHub:** repo `ziq` → Settings → Secrets and variables → Actions → *New repository secret*:
   - `TELEGRAM_BOT_TOKEN` = token bot
   - `TELEGRAM_CHAT_ID` = `@username_channel` (untuk channel private, guna ID nombor seperti `-100xxxxxxxxxx`)
4. **Merge ke branch default (`main`).** GitHub hanya jalankan jadual dari branch default.
5. **Uji:** tab Actions → *Telegram morning quote* → **Run workflow**.

## Ubah suai

- **Tambah atau tukar ayat:** edit `quotes.txt`, satu ayat satu baris.
- **Tukar masa:** edit `cron` dalam `.github/workflows/telegram-morning-quote.yml`. Masa dalam UTC, jadi tolak 8 jam dari waktu Malaysia.
  - Contoh 8:30 pagi MYT = `30 0 * * *`
  - Untuk hari bekerja sahaja (Isnin–Jumaat MYT): `45 23 * * 0-4`
- **Preview tanpa hantar:** `python3 post_quote.py --dry-run --date 2026-12-01`
