# Notifikasi news ke Telegram

Setiap news USD tier-1 menghasilkan tiga post ke group INDICATOR SUPPORT (melalui `tg_send.py`):

1. **Video + teks news**: dijadualkan 90 minit sebelum news (lihat `NEWS_TEMPLATE.md`, `make_news.py`).
2. **Amaran 15 minit sebelum** (`news/YYYY-MM-DD-reminder.md`).
3. **ACTUAL keluar**: kira-kira 5 minit selepas news (`news/YYYY-MM-DD-actual.md`).

Semua harga mesti datang dari data live (`xau_charts.py`, `xau_levels.py`) atau post sebelum ini. Nilai previous/forecast/actual mesti disahkan melalui carian web; tulis `—` jika belum disahkan. Jangan sesekali meneka.

## 2. Amaran 15 minit (maks ~800 aksara)

```
⏰ ZIQFX | NEWS ALERT — 15 MINIT LAGI
📰 <nama news> • <jam> waktu Malaysia

📊 Forecast vs Previous:
• <news 1>: Forecast <x> | Previous <y>
• <news 2>: Forecast <x> | Previous <y>

📍 Harga semasa: <harga>
🔴 Resistance: a–b   🟢 Support: a–b

🟢 Data lemah (bawah forecast) → USD lemah → gold berpotensi naik ke <resistance>
🔴 Data kuat (atas forecast) → USD kuat → gold berpotensi turun ke <support>

⚠️ Elak entry 15 minit sebelum dan selepas news. Spread dan slippage boleh melebar.
Fighters, biar news keluar dulu — tiada confirmation = NO ENTRY.
```

## 3. ACTUAL keluar (maks ~1500 aksara)

```
🚨 ZIQFX | NEWS RESULT — <nama news>
📅 <Hari, tarikh> • <jam> waktu Malaysia

📊 Keputusan:
• <news 1>: Actual <a> | Forecast <f> | Previous <p> → <LEBIH TINGGI / LEBIH RENDAH / SELARI> jangkaan
• <news 2>: ...

🔍 Fundamental: <apa maksud data untuk USD, jangkaan Fed dan gold, 2–3 ayat>

⚡ Reaksi gold: dari <harga sebelum news> ke <harga sekarang> (<naik/turun> <n> point), high <h> / low <l> sejak news
🎯 Senario yang aktif: <Senario 1/2/3 dari video news>

📈 Teknikal seterusnya:
🔴 Resistance: a–b   🟢 Support: a–b
• BUY jika: <confirmation + target>
• SELL jika: <confirmation + target>

⚠️ Pergerakan pertama selepas news boleh palsu. Tunggu candle M15 close dan retest.
Fighters, tiada confirmation = NO ENTRY.
```

Jika keputusan sebenar belum boleh disahkan 5 minit selepas news, tunggu dan cuba semula sehingga kira-kira 20 minit selepas news. Kemudian post apa yang sudah disahkan, dan nyatakan nilai yang masih belum disahkan.
