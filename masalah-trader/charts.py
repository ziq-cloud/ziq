"""Senario chart hidup untuk babak hook setiap video (lihat fx.LiveChart).

path   : titik kunci harga (0..1), diinterpolasi + hingar
labels : (pecahan masa 0..1, teks, warna, emoji) muncul pada candle itu
counter: nilai di penjuru kanan atas (mode: ratio | to_zero | pnl | abs | clock)
stamp  : cop besar di hujung ayat hook pertama (dengan gegar + boom)
"""
CHARTS = {
    "01_scam_skim_cepat_kaya": dict(
        title="PELABURAN 'DIJAMIN'", path=[0.25, 0.32, 0.4, 0.48, 0.56, 0.64, 0.72, 0.8, 0.05], noise=0.012,
        counter=dict(label="Duit korang", mode="to_zero", start=10000, fmt="RM {:,.0f}"),
        labels=[(0.25, "+30% sebulan", "green", "🤑"), (0.55, "Ajak member = komisen", "gold", "👥"),
                (0.93, "Withdraw ditolak", "red", "⛔")],
        stamp=("SKIM RUNTUH", "red", "💥")),
    "02_broker_tak_berlesen": dict(
        title="BAKI AKAUN BROKER", path=[0.3, 0.42, 0.5, 0.56, 0.6, 0.6, 0.6, 0.6], noise=0.025, freeze_at=0.5,
        counter=dict(label="Baki", mode="ratio", start=5000, fmt="RM {:,.0f}"),
        labels=[(0.2, "Bonus deposit 100%", "gold", "🎁"), (0.6, "Withdraw: PENDING...", "gold", "⏳"),
                (0.88, "Caj baru!", "red", "💸")],
        stamp=("AKAUN DIBEKU", "red", "🔒")),
    "03_guru_signal_sorok_loss": dict(
        title="AKAUN IKUT SIGNAL", path=[0.6, 0.72, 0.5, 0.64, 0.42, 0.52, 0.3, 0.36, 0.2], noise=0.02,
        counter=dict(label="Ekuiti", mode="ratio", start=3000, fmt="RM {:,.0f}"),
        labels=[(0.12, "WIN dipost", "green", "📸"), (0.3, "LOSS dipadam", "red", "🗑️"),
                (0.56, "WIN dipost", "green", "📸"), (0.8, "LOSS dipadam", "red", "🗑️")],
        stamp=("REKOD SEBENAR: RUGI", "red", "📉")),
    "04_lot_besar_akaun_kecil": dict(
        title="AKAUN $100 · 1.00 LOT", path=[0.72, 0.78, 0.68, 0.8, 0.7, 0.76, 0.12], noise=0.03, n=28,
        counter=dict(label="Equity", mode="to_zero", start=100, fmt="${:,.0f}"),
        labels=[(0.35, "Leverage 1:1000", "gold", "⚡"), (0.9, "Margin call!", "red", "🚨")],
        stamp=("AKAUN BURN", "red", "🔥")),
    "05_tiada_stop_loss_sangkut": dict(
        title="POSISI TANPA STOP LOSS", path=[0.8, 0.72, 0.62, 0.66, 0.52, 0.42, 0.46, 0.3, 0.15], noise=0.018,
        counter=dict(label="Floating", mode="pnl", end=-1800, fmt="RM {:+,.0f}"),
        labels=[(0.08, "Entry", "gold", "🎯"), (0.38, "Nanti naik balik...", "gold", "🙏"),
                (0.62, "Tambah posisi", "red", "➕"), (0.86, "Swap tiap malam", "red", "🌙")],
        stamp=("MARGIN CALL", "red", "🚨")),
    "06_emosi_fomo_revenge": dict(
        title="FOMO → REVENGE", path=[0.3, 0.34, 0.45, 0.62, 0.88, 0.6, 0.66, 0.4, 0.22], noise=0.02,
        counter=dict(label="P/L", mode="pnl", end=-950, fmt="RM {:+,.0f}"),
        labels=[(0.5, "FOMO masuk kat puncak", "red", "😱"), (0.74, "Revenge: double lot", "red", "😤"),
                (0.95, "Rugi berganda", "red", "💀")],
        stamp=("EMOSI MENANG", "red", "🤯")),
    "07_duit_tak_mampu_hilang": dict(
        title="AKAUN TRADING", path=[0.25, 0.42, 0.58, 0.78, 0.84, 0.6, 0.35, 0.02], noise=0.015,
        counter=dict(label="Baki", mode="abs", scale=15000, fmt="RM {:,.0f}"),
        labels=[(0.14, "+ Duit sewa", "gold", "🏠"), (0.3, "+ Personal loan", "gold", "🏦"),
                (0.46, "+ Simpanan", "gold", "🐷"), (0.95, "Akaun kosong", "red", "🫠")],
        stamp=("HUTANG KEKAL", "red", "📄")),
    "08_masa_kerja_tidur": dict(
        title="SESI NEW YORK (WAKTU MALAYSIA)", path=[0.45, 0.46, 0.44, 0.47, 0.9, 0.3, 0.62, 0.5, 0.52], noise=0.02,
        counter=dict(label="Jam", mode="clock", **{"from": 20 * 60, "to": 27 * 60}),
        labels=[(0.22, "NY buka", "gold", "🗽"), (0.46, "NFP keluar!", "red", "📢"), (0.88, "Esok kerja...", "red", "🥱")],
        stamp=("TAK CUKUP TIDUR", "red", "😴")),
    "09_lompat_strategi_tiada_jurnal": dict(
        title="EKUITI: TUKAR-TUKAR STRATEGI", path=[0.6, 0.5, 0.62, 0.44, 0.56, 0.4, 0.5, 0.32, 0.36], noise=0.02,
        counter=dict(label="Ekuiti", mode="abs", scale=10000, fmt="RM {:,.0f}"),
        labels=[(0.12, "SMC", "gold", "🧠"), (0.38, "Indikator", "gold", "📊"), (0.64, "Robot EA", "gold", "🤖"),
                (0.88, "Tukar lagi...", "red", "🔁")],
        stamp=("TAK KE MANA", "red", "🌀")),
    "10_isu_syariah": dict(
        kind="scale", title="FOREX: HALAL ATAU HARAM?",
        stamp=("RUJUK YANG BERAUTORITI", "gold", "📖")),
    "traxa_bantu_trader": dict(
        title="XAU/USD · M15", path=[0.7, 0.64, 0.56, 0.48, 0.42, 0.39, 0.41, 0.5, 0.6], noise=0.018,
        zones=[(0.34, 0.41, "green", "Zon support"), (0.78, 0.84, "red", "Zon resistance")],
        labels=[(0.6, "Harga masuk zon", "gold", "🔔")],
        stamp=("TAK PAYAH TENUNG CHART", "green", "📲"), stamp_flash=False),
}
