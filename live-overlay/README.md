# TRAXA – overlay TikTok LIVE

Overlay telus (1080×1920, menegak) untuk TikTok LIVE: logo TRAXA + kod jemputan **ZIQFX**, mesej bergilir, baris amaran risiko, dan pop-up besar "guna kod ZIQFX" setiap beberapa minit.

`overlay.html` ialah satu fail lengkap (logo & font sudah dimasukkan), tak perlu internet.

## 1. Semak & ubah dulu (pratonton)

Buka dalam Chrome:

```
overlay.html?preview=1
```

Kawasan merah = UI TikTok (nama/viewer di atas, komen di bawah, butang gift di kanan). Ubah kod, bahasa, kiri/kanan, jarak dari atas, kekerapan pop-up dan mesej, tekan **Kemas kini pratonton**, kemudian **Salin URL overlay**.

## 2. Masukkan dalam TikTok LIVE Studio (PC)

1. Buka LIVE Studio → pilih orientasi **Portrait / menegak**.
2. Tambah sumber kamera / skrin (chart) seperti biasa.
3. **Add source → Link** (Browser / URL) → tampal URL yang disalin (bermula `file:///...overlay.html?...`).
   Saiz **1080 × 1920**. Letak sumber ini **paling atas** dalam senarai.
4. Latar overlay telus, jadi kamera/chart nampak di belakang.

## Atau OBS Studio (stream ke TikTok guna stream key)

1. Settings → Video → Base & Output resolution **1080x1920**.
2. Sources → **+ → Browser** → tandakan **Local file** dan pilih `overlay.html`,
   atau nyahtanda dan tampal URL penuh (perlu jika ada tetapan `?code=...`).
   Width **1080**, Height **1920**.
3. Pop-up boleh dipaparkan serta-merta: klik kanan sumber → **Interact** → tekan **P**.

## Tetapan URL

| Parameter | Contoh | Default |
|---|---|---|
| `code` | `code=ZIQFX` | `ZIQFX` |
| `lang` | `lang=en` | `bm` |
| `pos` | `pos=right` | `left` |
| `y` | `y=320` (px dari atas) | `300` |
| `pop` | `pop=5` (minit, `0` = tutup) | `3` |
| `msgs` | `msgs=Mesej 1|Mesej 2` | 4 mesej default |
| `preview` | `preview=1` | – |

## Nota

- Ayat default sengaja elak "buy/sell/TP/SL/untung/jamin" dan ada amaran risiko — ikut sebab yang sama seperti dalam `promo/ADS.md`. TikTok LIVE juga disemak; jangan tunjuk tuntutan untung atau janji keuntungan semasa live.
- Pastikan "Link di bio" memang ada: `https://traxatradingapp.com/?invite=ZIQFX`.
- Ubah reka bentuk dalam `src.html`, kemudian jalankan `python3 build.py` untuk jana semula `overlay.html`.
