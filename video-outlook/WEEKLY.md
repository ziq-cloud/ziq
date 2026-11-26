# Post mingguan ke Telegram

## 1. Weekly outlook (Isnin 06:20 waktu Malaysia, sebelum sesi Asia)

Data: `python3 weekly.py` (D1 dan W1) dan `python3 xau_charts.py all && python3 xau_levels.py` (H4/H1).
Kalendar: `fetch_calendar.py --currency usd --min-tier 2` untuk minggu ini (tier 1 dan tier 2), dalam waktu Malaysia.
Fail: `weekly/YYYY-MM-DD-outlook.md` (tarikh Isnin). Post: `tg_send.py text <file> --pin`, `tg_send.py photo charts/d1.png "XAUUSD D1 • minggu <tarikh>"`, `tg_send.py photo charts/w1.png "XAUUSD W1"`.

```
📅 ZIQFX | XAUUSD WEEKLY OUTLOOK ⚔️
🗓 Minggu <tarikh Isnin> – <tarikh Jumaat>

📍 Harga: <close Jumaat> • Range minggu lalu: <low>–<high> (<naik/turun> <n> point)

📊 Struktur besar:
• W1: <trend + struktur HH/HL atau LH/LL, EMA20/EMA50>
• D1: <trend + struktur, swing high/low terkini>
• H4: <ringkas>

🎯 BIAS MINGGUAN: <...> • FOCUS: <...>

🔴 Resistance mingguan: a–b • a–b • a–b
🟢 Support mingguan: a–b • a–b • a–b

📌 Senario minggu ini:
1️⃣ <senario utama + syarat + target>
2️⃣ <senario alternatif + syarat + target>

🗓 Kalendar news USD minggu ini (waktu Malaysia):
• <Hari dd/mm> <jam> — <news> ⭐⭐⭐ (tier 1) / ⭐⭐ (tier 2)

Fighters, rancang minggu ini dengan zon dan confirmation — tiada confirmation = NO ENTRY.
```

## 2. Scorecard mingguan (Sabtu 09:37 waktu Malaysia)

Data: `python3 scorecard.py fetch && python3 scorecard.py report <tarikh Isnin>`. Gunakan hanya angka daripada laporan tu.
Fail: `weekly/YYYY-MM-DD-scorecard.md` (tarikh Isnin). Post: `tg_send.py text <file>`.

```
📈 ZIQFX | SCORECARD MINGGUAN
🗓 <tarikh Isnin> – <tarikh Jumaat>

📊 Ringkasan:
• Setup aktif: <n> • Target tercapai: <x>/<y> (<%>)
• Bias harian betul: <a>/<b> hari

🗓 Harian:
• <Hari>: bias <BIAS> <✅/❌> • <zon yang berfungsi dan target yang tercapai, 1 baris>
• ...

⭐ Zon terbaik minggu ini: <zon + pergerakan>
❌ Yang tak menjadi: <bias salah / zon tak aktif + sebab dari data, contohnya news>

ℹ️ Kiraan mekanikal: zon disentuh → target dicapai selepas itu. Tidak mengambil kira confirmation entry atau SL, jadi ini bukan keputusan P/L.

Fighters, konsisten dengan zon dan confirmation. Jumpa minggu depan ⚔️
```
