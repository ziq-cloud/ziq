"""Video berasingan: macam mana TRAXA bantu trader (tidak dicampur dengan siri Masalah Trader Malaysia).

Render: python3 make_videos.py traxa  ->  out/traxa_bantu_trader.mp4
Elak tuntutan untung / win rate; jangan sebut buy/sell dalam narasi.
"""
import os

SCR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "promo", "assets", "screens")

TRAXA = {
    "slug": "traxa_bantu_trader",
    "title": "TRAXA Trading App",
    "series": "TRAXA TRADING APP",
    "chip": "KENALI TRAXA",
    "chip_color": "gold",
    "hook": ("Penat tenung chart sampai pagi?",
             "Penat tenung chart sampai pagi, tapi masih teka-teka nak masuk kat mana?"),
    "intro": "Jom aku tunjuk, macam mana TRAXA bantu trader macam kita.",
    "sections": [
        ("MASALAH BIASA TRADER", "red", [
            ("Teka-teka paras harga penting",
             "Ramai trader masih teka-teka, paras harga mana yang penting."),
            ("Ikut signal, tapi tak tahu sebab",
             "Ikut signal orang, tapi tak tahu pun kenapa setup tu diambil."),
            ("Tenung chart sampai lewat malam",
             "Lepas tu, tenung chart sampai lewat malam. Esok kerja, mengantuk."),
        ]),
        ("MACAM MANA TRAXA BANTU", "green", [
            ("Setiap setup: paras penting + SEBAB",
             "Dalam TRAXA, setiap setup tunjuk paras harga penting, siap dengan sebab kenapa setup tu dihantar."),
            ("Support & resistance setiap timeframe",
             "Support, resistance, dengan key level untuk setiap timeframe pun ada."),
            ("Notifikasi terus ke phone",
             "Setup baru, keputusan, dengan amaran berita, semua masuk notifikasi phone. Tak payah tenung chart."),
            ("Kelas edukasi untuk pemula",
             "Dan ada kelas edukasi, dari market structure sampai breakout. Supaya korang faham, bukan ikut buta-buta."),
        ], [os.path.join(SCR, "levels.png"), os.path.join(SCR, "levels.png"),
            os.path.join(SCR, "notif.png"), os.path.join(SCR, "edu.png")]),
    ],
    "outro": ["Ingat ye, trading ni risiko dia tinggi. TRAXA alat bantu analisis, bukan jaminan untung.",
              "Nak cuba? Daftar guna kod jemputan aku. Z, I, Q, F, X. Link ada kat bio."],
    "cta": {"code": "ZIQFX", "link": "traxatradingapp.com/?invite=ZIQFX"},
}
