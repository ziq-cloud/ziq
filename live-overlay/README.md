# TRAXA – overlay TikTok LIVE

Overlay animasi dengan maskot robot kartun untuk TikTok LIVE. Susun atur: **bar atas** (logo, kod, maskot) + **bar bawah** (mesej bergilir, amaran risiko, pop-up kod), **tengah kosong**. Kandungan: logo TRAXA + kod jemputan **ZIQFX**, belon cakap yang menaip sendiri, lilin chart terapung, baris amaran risiko, dan pop-up besar "guna kod ZIQFX" setiap beberapa minit.

## iPad (TikTok app) – kad terapung PiP

TikTok di iPad tak boleh tambah overlay. Guna video jalur nipis `traxa_strip_bm.mp4` / `traxa_strip_en.mp4` (letak di atas, tengah kekal kosong) atau kad besar `traxa_pip_*.mp4` (24 s, berulang). iPad hanya benarkan satu tetingkap terapung, jadi bar atas + bawah serentak hanya untuk PC dalam **Picture-in-Picture**:

1. Buka `pip-player.html` (atau artifact yang diterbitkan) dalam **Safari** iPad → tekan **Jadikan terapung (PiP)**.
2. Seret kad ke bucu atas, jauh dari komen.
3. TikTok → LIVE → **Mobile gaming / kongsi skrin** → mula live, buka app TRAXA / chart.

Kad hanya kelihatan dalam mod kongsi skrin (mod kamera tak rakam skrin).
Jana semula video selepas ubah reka bentuk: `python3 build.py && node render_pip.js bm ZIQFX strip && node render_pip.js bm ZIQFX pip` (ulang dengan `en`).
Pratonton: `overlay.html?mode=strip` / `overlay.html?mode=pip`.

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
| `top` | `top=260` (bar atas, px dari atas) | `250` |
| `bottom` | `bottom=980` (bar bawah, px dari atas) | `1000` |
| `pop` | `pop=5` (minit, `0` = tutup) | `3` |
| `msgs` | `msgs=Mesej 1|Mesej 2` | 4 mesej default |
| `preview` | `preview=1` | – |

## Nota

- Ayat default sengaja elak "buy/sell/TP/SL/untung/jamin" dan ada amaran risiko — ikut sebab yang sama seperti dalam `promo/ADS.md`. TikTok LIVE juga disemak; jangan tunjuk tuntutan untung atau janji keuntungan semasa live.
- Pastikan "Link di bio" memang ada: `https://traxatradingapp.com/?invite=ZIQFX`.
- Ubah reka bentuk dalam `src.html`, kemudian jalankan `python3 build.py` untuk jana semula `overlay.html`.
