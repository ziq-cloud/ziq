# Masalah Trader Malaysia — siri video (10 topik)

Video menegak 9:16 (1080x1920), suara BM (`ms-MY-OsmanNeural`), sari kata gaya TikTok, ~50–60 saat setiap satu.
Fail dalam `out/`: `<slug>.mp4` + `<slug>.jpg` (cover).

| # | Topik | Fail |
|---|-------|------|
| 1 | Scam & skim cepat kaya | `out/01_scam_skim_cepat_kaya.mp4` |
| 2 | Broker tak berlesen & susah withdraw | `out/02_broker_tak_berlesen.mp4` |
| 3 | Guru & signal group sorok loss | `out/03_guru_signal_sorok_loss.mp4` |
| 4 | Lot besar, akaun kecil (overleverage) | `out/04_lot_besar_akaun_kecil.mp4` |
| 5 | Tiada stop loss & "sangkut" | `out/05_tiada_stop_loss_sangkut.mp4` |
| 6 | Emosi: FOMO & revenge trade | `out/06_emosi_fomo_revenge.mp4` |
| 7 | Trade guna duit yang tak mampu hilang | `out/07_duit_tak_mampu_hilang.mp4` |
| 8 | Sesi malam: kerja, tidur & keluarga | `out/08_masa_kerja_tidur.mp4` |
| 9 | Lompat strategi & tiada jurnal | `out/09_lompat_strategi_tiada_jurnal.mp4` |
| 10 | Keliru isu syariah | `out/10_isu_syariah.mp4` |

Struktur setiap video: hook → "Masalah #N" → 3 tanda/sebab → 3 langkah "Apa nak buat" → amaran risiko + teaser topik seterusnya + Follow.

## Ubah & render semula

- Teks skrin dan narasi: `topics.py` (narasi eja nombor dalam perkataan supaya TTS sebut betul).
- Render: `python3 make_videos.py` (semua) atau `python3 make_videos.py 4` (topik #4 sahaja).
- Env: `VOICE=ms-MY-YasminNeural` (suara perempuan), `BRAND=...`, `RATE=+4%`, `JOBS=4`.
- Suara disimpan dalam `voice/<VOICE>/` (cache); suara baru perlu akses ke `speech.platform.bing.com`.

## Caption cadangan

> Masalah trader Malaysia #N: <topik>. Kau pernah alami? Komen bawah 👇
> Trading berisiko tinggi. Bukan nasihat kewangan.
> #forexmalaysia #tradermalaysia #belajartrading

## Nota fakta

- Senarai Amaran Pelabur (SC) dan Senarai Makluman Pengguna Kewangan (BNM) ialah senarai rasmi yang boleh disemak awam.
- Waktu sesi (London ~3–4 ptg, New York ~8–9 mlm MYT; NFP ~8:30/9:30 mlm) berubah ikut daylight saving AS/UK.
- Topik #10 merujuk keputusan Muzakarah Jawatankuasa Fatwa MKI (2010) tentang forex individu secara lani melalui platform elektronik. Semak dengan pihak berautoriti agama sebelum diterbitkan.
