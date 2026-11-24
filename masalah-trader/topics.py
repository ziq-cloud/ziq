"""Kandungan siri video "Masalah Trader Malaysia".

Setiap topik:
  hook      : (teks skrin, narasi) babak pembuka
  sections  : [(tajuk, warna, [(teks skrin pendek, narasi), ...]), ...]
Narasi ditulis dalam bentuk sebutan (nombor dieja) supaya TTS sebut dengan betul.
"""

RED, GOLD, GREEN = "red", "gold", "green"

TOPICS = [
    {
        "slug": "01_scam_skim_cepat_kaya",
        "title": "Scam & skim cepat kaya",
        "hook": ("Untung 30% sebulan, DIJAMIN?",
                 "Untung tiga puluh peratus sebulan, dijamin? Itu bukan trading. Itu scam."),
        "sections": [
            ("TANDA-TANDA SCAM", RED, [
                ("Janji pulangan tetap / dijamin",
                 "Tanda pertama, mereka janji pulangan tetap, atau kata untung dijamin."),
                ("Komisen bila ajak ahli baru",
                 "Kedua, kau dapat komisen bila ajak kawan masuk. Itu ciri skim piramid."),
                ("Akaun 'diurus', susah withdraw",
                 "Ketiga, duit kau diurus orang lain, dan bila nak keluarkan duit, macam-macam alasan."),
            ]),
            ("APA NAK BUAT", GREEN, [
                ("Semak Senarai Amaran SC & BNM",
                 "Sebelum masuk apa-apa, semak Senarai Amaran Pelabur Suruhanjaya Sekuriti, dan Senarai Makluman Pengguna Kewangan Bank Negara."),
                ("Jangan serah duit / password akaun",
                 "Jangan serahkan duit atau kata laluan akaun trading kau kepada sesiapa."),
                ("Tiada siapa boleh jamin untung",
                 "Ingat, dalam trading, tiada siapa boleh jamin untung."),
            ]),
        ],
    },
    {
        "slug": "02_broker_tak_berlesen",
        "title": "Broker tak berlesen & susah withdraw",
        "hook": ("Deposit senang. Withdraw susah?",
                 "Deposit senang, tapi bila nak withdraw, akaun kena sekat?"),
        "sections": [
            ("TANDA BROKER BERISIKO", RED, [
                ("Tiada lesen regulator yang jelas",
                 "Broker tak ada lesen daripada mana-mana regulator yang dikenali, atau lesennya tak boleh disemak."),
                ("Bonus deposit yang melampau",
                 "Tawar bonus deposit seratus peratus atau lebih, tapi dengan syarat tersembunyi."),
                ("Withdraw ditangguh, syarat pelik",
                 "Withdraw ditangguh berminggu-minggu, atau tiba-tiba ada caj dan syarat baru."),
            ]),
            ("APA NAK BUAT", GREEN, [
                ("Semak lesen di laman regulator sendiri",
                 "Semak nombor lesen terus di laman web regulator itu sendiri, bukan percaya screenshot."),
                ("Cuba withdraw jumlah kecil dulu",
                 "Lepas deposit, cuba withdraw jumlah kecil dulu untuk uji."),
                ("Jangan simpan semua modal di satu broker",
                 "Dan jangan simpan semua modal kau dalam satu broker."),
            ]),
        ],
    },
    {
        "slug": "03_guru_signal_sorok_loss",
        "title": "Guru & signal group sorok loss",
        "hook": ("Screenshot untung je. Mana loss?",
                 "Group signal tunjuk screenshot untung je. Mana pergi screenshot loss?"),
        "sections": [
            ("TANDA-TANDA", RED, [
                ("Signal yang kena SL dipadam",
                 "Signal yang kena stop loss dipadam senyap-senyap, yang untung je dipost semula."),
                ("Flex kereta, jam, gaya hidup",
                 "Lebih banyak flex kereta, jam dan percutian, daripada terangkan analisis."),
                ("Kelas mahal, 'konfem profit'",
                 "Jual kelas mahal dengan janji konfem profit."),
            ]),
            ("APA NAK BUAT", GREEN, [
                ("Minta rekod penuh yang disahkan",
                 "Minta rekod prestasi penuh yang disahkan pihak ketiga, termasuk semua loss."),
                ("Uji signal di akaun demo sebulan",
                 "Ikut signal tu dalam akaun demo dulu, sekurang-kurangnya sebulan."),
                ("Belajar SEBAB setiap setup",
                 "Dan belajar sebab di sebalik setiap setup, supaya kau tak bergantung selamanya."),
            ]),
        ],
    },
    {
        "slug": "04_lot_besar_akaun_kecil",
        "title": "Lot besar, akaun kecil",
        "hook": ("Akaun $100. Buka 1 lot.",
                 "Akaun seratus dolar, buka satu lot. Satu candle je, akaun hangus."),
        "sections": [
            ("KENAPA BAHAYA", RED, [
                ("Leverage tinggi buat lot nampak 'murah'",
                 "Leverage tinggi, macam satu nisbah seribu, buat lot besar nampak murah."),
                ("Tapi rugi pun ikut besar",
                 "Tapi bila harga lawan arah, rugi pun ikut besar."),
                ("Margin call → stop out",
                 "Akhirnya margin call, dan broker tutup posisi kau secara automatik."),
            ]),
            ("APA NAK BUAT", GREEN, [
                ("Risiko 1–2% akaun setiap trade",
                 "Hadkan risiko satu hingga dua peratus akaun untuk setiap trade."),
                ("Akaun RM2,000 → risiko RM20",
                 "Contoh, akaun dua ribu ringgit, risiko satu peratus, cuma dua puluh ringgit."),
                ("Kira lot ikut jarak stop loss",
                 "Kira saiz lot ikut jarak stop loss, bukan ikut rasa."),
            ]),
        ],
    },
    {
        "slug": "05_tiada_stop_loss_sangkut",
        "title": "Tiada stop loss & 'sangkut'",
        "hook": ("\"Nanti dia naik balik la...\"",
                 "Nanti dia naik balik la. Ayat ni dah hanguskan banyak akaun."),
        "sections": [
            ("APA YANG BERLAKU", RED, [
                ("Hold posisi rugi berminggu",
                 "Posisi rugi dibiarkan berminggu-minggu, berharap harga patah balik."),
                ("Tambah posisi yang sedang rugi",
                 "Lepas tu tambah lagi posisi yang sedang rugi, konon nak purata harga."),
                ("Swap dikenakan setiap malam",
                 "Sementara itu, caj swap dikenakan setiap malam."),
            ]),
            ("APA NAK BUAT", GREEN, [
                ("Letak SL sebelum entry",
                 "Tentukan dan letak stop loss sebelum masuk trade."),
                ("Loss kecil = kos bisnes",
                 "Anggap loss kecil sebagai kos bisnes, bukan kegagalan."),
                ("Jangan average posisi rugi",
                 "Dan jangan tambah posisi yang sedang rugi."),
            ]),
        ],
    },
    {
        "slug": "06_emosi_fomo_revenge",
        "title": "Emosi: FOMO & revenge trade",
        "hook": ("Baru loss, terus nak 'balas dendam'?",
                 "Baru kena loss, terus nak balas dendam pada market?"),
        "sections": [
            ("TANDA-TANDA", RED, [
                ("Kejar harga yang dah lari",
                 "Kau kejar harga yang dah lari jauh, sebab takut terlepas."),
                ("Gandakan lot lepas loss",
                 "Lepas loss, kau gandakan lot untuk cepat tutup rugi."),
                ("Trade sebab bosan",
                 "Atau kau buka trade semata-mata sebab bosan."),
            ]),
            ("APA NAK BUAT", GREEN, [
                ("Had 2–3 trade sehari",
                 "Tetapkan had, contohnya dua atau tiga trade sehari."),
                ("2 loss berturut = tutup chart",
                 "Kalau dua loss berturut-turut, tutup chart. Sambung esok."),
                ("Trading plan bertulis",
                 "Tulis trading plan, dan trade hanya bila setup kau muncul."),
            ]),
        ],
    },
    {
        "slug": "07_duit_tak_mampu_hilang",
        "title": "Trade guna duit yang tak mampu hilang",
        "hook": ("Duit sewa rumah masuk trading?",
                 "Duit sewa rumah, duit pinjaman peribadi, duit simpanan, semua masuk akaun trading?"),
        "sections": [
            ("KENAPA BAHAYA", RED, [
                ("Tekanan duit = keputusan teruk",
                 "Bila duit tu kau perlukan, tekanan buat keputusan trading jadi teruk."),
                ("Hutang tetap kena bayar",
                 "Kalau akaun hangus, hutang tetap kena bayar setiap bulan."),
                ("Keluarga ikut terkesan",
                 "Dan yang paling terkesan, keluarga kau sendiri."),
            ]),
            ("APA NAK BUAT", GREEN, [
                ("Guna duit lebihan sahaja",
                 "Trade hanya dengan duit lebihan, yang kalau hilang pun hidup kau tak terjejas."),
                ("Dana kecemasan 3–6 bulan dulu",
                 "Sediakan dana kecemasan tiga hingga enam bulan dulu."),
                ("Jangan berhutang untuk trading",
                 "Dan jangan sekali-kali berhutang untuk trading."),
            ]),
        ],
    },
    {
        "slug": "08_masa_kerja_tidur",
        "title": "Sesi malam: kerja, tidur & keluarga",
        "hook": ("Market paling aktif masa kau patut tidur",
                 "Masa market paling aktif, kebanyakan trader Malaysia patut dah tidur."),
        "sections": [
            ("REALITI ZON MASA", RED, [
                ("London buka ~3–4 petang (MYT)",
                 "Sesi London buka sekitar pukul tiga atau empat petang waktu Malaysia."),
                ("New York buka ~8–9 malam (MYT)",
                 "Sesi New York pula sekitar pukul lapan atau sembilan malam."),
                ("Berita besar (NFP) ~8:30–9:30 malam",
                 "Berita besar macam NFP keluar sekitar lapan setengah atau sembilan setengah malam. Akhirnya tak cukup tidur, kerja esok terganggu."),
            ]),
            ("APA NAK BUAT", GREEN, [
                ("Pilih SATU sesi sahaja",
                 "Pilih satu sesi sahaja yang sesuai dengan jadual kau."),
                ("Guna pending order & alert",
                 "Guna pending order dan alert harga, tak perlu tengok chart sepanjang malam."),
                ("Tetapkan waktu tidur",
                 "Tetapkan waktu tidur. Akaun boleh tunggu, kesihatan tak boleh."),
            ]),
        ],
    },
    {
        "slug": "09_lompat_strategi_tiada_jurnal",
        "title": "Lompat strategi & tiada jurnal",
        "hook": ("Minggu ni SMC, minggu depan robot",
                 "Minggu ni SMC, minggu depan indikator, bulan depan beli robot."),
        "sections": [
            ("MASALAHNYA", RED, [
                ("Strategi ditukar sebelum diuji",
                 "Strategi ditukar sebelum sempat diuji dengan betul."),
                ("Tak tahu apa yang salah",
                 "Tanpa rekod, kau tak tahu apa sebenarnya yang salah."),
                ("Ulang kesilapan yang sama",
                 "Jadi kesilapan yang sama berulang setiap bulan."),
            ]),
            ("APA NAK BUAT", GREEN, [
                ("Satu strategi, 50–100 trade",
                 "Pegang satu strategi, dan uji sekurang-kurangnya lima puluh hingga seratus trade, di demo atau backtest."),
                ("Jurnal: entry, sebab, hasil, emosi",
                 "Catat setiap trade dalam jurnal. Entry, sebab, keputusan, dan emosi masa tu."),
                ("Review setiap hujung minggu",
                 "Review jurnal setiap hujung minggu, baru kau nampak corak kesilapan."),
            ]),
        ],
    },
    {
        "slug": "10_isu_syariah",
        "title": "Keliru isu syariah",
        "hook": ("Forex: halal atau haram?",
                 "Ramai trader Muslim di Malaysia keliru. Forex ni halal atau haram?"),
        "sections": [
            ("APA KATA FATWA", GOLD, [
                ("Muzakarah Fatwa Kebangsaan, 2010",
                 "Pada tahun dua ribu sepuluh, Muzakarah Jawatankuasa Fatwa Kebangsaan membincangkan isu ini."),
                ("Forex individu secara lani (spot) melalui platform elektronik: HARAM",
                 "Keputusannya, dagangan forex oleh individu secara lani melalui platform elektronik adalah haram."),
                ("Isu: riba (swap), margin, serah terima",
                 "Antara isu yang dibangkitkan ialah riba, margin, dan syarat serah terima."),
            ]),
            ("APA NAK BUAT", GREEN, [
                ("Akaun 'swap-free' tak selesai semua isu",
                 "Akaun swap free atau akaun Islamik tak semestinya selesaikan semua isu tu."),
                ("Rujuk pihak berautoriti agama",
                 "Rujuk pihak berautoriti agama, bukan ustaz segera di media sosial."),
                ("Ada pilihan patuh syariah lain",
                 "Ada pilihan lain, contohnya saham patuh syariah yang disenaraikan Suruhanjaya Sekuriti."),
            ]),
        ],
    },
]
