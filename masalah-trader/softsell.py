"""Babak soft-sell TRAXA di hujung setiap video siri (sebelum penutup).

Setiap ayat dikaitkan dengan topik dan hanya sebut ciri yang memang ada dalam skrin app
(promo/assets/screens): paras harga penting + sebab setup, notifikasi setup/keputusan/amaran berita,
analisis support/resistance setiap timeframe, dan kelas edukasi. Elak tuntutan untung.
"""
import copy, os

SCR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "promo", "assets", "screens")
LEVELS, NOTIF, EDU = (os.path.join(SCR, f) for f in ("levels.png", "notif.png", "edu.png"))
CODE = "ZIQFX"

_EDU = ("Kelas edukasi dalam app",
        "Nak belajar cara yang betul? Dalam TRAXA ada kelas edukasi, dari market structure sampai breakout.", EDU)

SOFT = {
    "01_scam_skim_cepat_kaya": ("Belajar analisis sendiri",
        "Daripada serah duit dekat orang, lebih baik belajar analisis sendiri. TRAXA ada kelas edukasi, dan setiap setup siap dengan sebab dia.", EDU),
    "02_broker_tak_berlesen": ("Fokus pada analisis",
        "Bila dah pilih broker yang betul, fokus pada analisis. TRAXA tunjuk paras harga penting, dengan sebab setiap setup.", LEVELS),
    "03_guru_signal_sorok_loss": ("Setup + sebab + keputusan",
        "Dalam TRAXA, setiap setup ada sebab dia. Keputusan setup pun, termasuk yang kena stop loss, masuk terus dalam notifikasi.", NOTIF),
    "04_lot_besar_akaun_kecil": ("Paras penting = senang kira lot",
        "Dalam TRAXA, setiap setup tunjuk paras harga penting. Senang nak kira jarak stop loss, dan saiz lot.", LEVELS),
    "05_tiada_stop_loss_sangkut": ("Paras penting sebelum entry",
        "Setiap setup dalam TRAXA tunjuk paras harga penting, jadi korang boleh plan stop loss sebelum masuk.", LEVELS),
    "06_emosi_fomo_revenge": ("Alert bila harga dekat zon",
        "Daripada kejar harga, biar alert TRAXA bagitahu, bila harga dah dekat zon penting.", NOTIF),
    "07_duit_tak_mampu_hilang": _EDU,
    "08_masa_kerja_tidur": ("Notifikasi terus ke phone",
        "Tak payah berjaga. TRAXA hantar notifikasi setup baru, dan amaran berita, terus ke phone.", NOTIF),
    "09_lompat_strategi_tiada_jurnal": ("Kelas edukasi tersusun",
        "TRAXA ada kelas edukasi yang tersusun, dari market structure sampai breakout. Belajar satu-satu, ikut turutan.", EDU),
    "10_isu_syariah": _EDU,
    "11_overtrading": ("Setup datang, bukan dipaksa",
        "Dengan TRAXA, setup masuk dalam notifikasi bila ada je. Tak payah paksa diri cari trade.", NOTIF),
    "12_untung_cepat_tutup_loss_dibiar": ("Tahu paras penting awal",
        "Setiap setup TRAXA tunjuk paras harga penting, jadi korang tahu target dan risiko, sebelum masuk.", LEVELS),
    "13_takde_trading_plan": ("Panduan untuk plan",
        "Guna setup TRAXA sebagai panduan plan korang. Paras penting, dan sebab setup tu, semua ada.", LEVELS),
    "14_ego_salahkan_market": ("Sebab yang jelas, senang review",
        "Setiap setup TRAXA ada sebab yang jelas. Senang nak review, apa yang sebenarnya salah.", LEVELS),
    "15_nak_cepat_kaya": _EDU,
    "16_terlalu_banyak_indikator": ("S/R setiap timeframe, satu skrin",
        "TRAXA ringkaskan trend, support dan resistance setiap timeframe, dalam satu skrin. Chart pun kemas.", LEVELS),
    "17_trade_masa_berita": ("Amaran berita 30 minit awal",
        "TRAXA hantar amaran berita, tiga puluh minit sebelum berita USD impak tinggi dan sederhana.", NOTIF),
    "18_abaikan_timeframe_besar": ("M5 sampai D1, satu skrin",
        "Dalam TRAXA, trend dan support resistance dari M5 sampai D1, semua dalam satu skrin.", LEVELS),
    "19_backtest_syok_sendiri": ("Keputusan setup dalam notifikasi",
        "Dalam TRAXA, keputusan setiap setup dihantar dalam notifikasi. Korang boleh nilai sendiri, prestasi sebenar.", NOTIF),
    "20_kos_tersembunyi": ("Kualiti, bukan kuantiti",
        "Fokus pada setup berkualiti, bukan kuantiti. TRAXA tunjuk paras harga penting, dan sebab setiap setup.", LEVELS),
    "21_tak_reti_urus_untung": _EDU,
    "22_robot_indikator_rahsia": ("Bukan kotak hitam",
        "Daripada robot kotak hitam, TRAXA tunjuk sebab setiap setup, supaya korang faham apa yang berlaku.", LEVELS),
    "23_sorok_dari_keluarga": _EDU,
    "24_banding_diri_media_sosial": _EDU,
    "25_burnout": ("Tak perlu tenung chart 24 jam",
        "TRAXA hantar notifikasi terus ke phone. Tak perlu tenung chart, dua puluh empat jam.", NOTIF),
}


def with_softsell(topic):
    """Salinan topik dengan babak TRAXA ditambah sebagai seksyen terakhir (bentuk telefon)."""
    if "cta" in topic or topic["slug"] not in SOFT or os.environ.get("SOFTSELL", "1") != "1":
        return topic
    txt, nar, shot = SOFT[topic["slug"]]
    t = copy.deepcopy(topic)
    t["sections"].append(("TIPS: CUBA TRAXA", "gold", [
        (txt, nar),
        (f"Kod jemputan: {CODE}", "Cuba TRAXA. Daftar guna kod jemputan Z, I, Q, F, X. Link ada kat bio."),
    ], [shot, shot]))
    return t
