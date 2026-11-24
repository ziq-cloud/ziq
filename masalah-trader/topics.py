"""Kandungan siri video "Masalah Trader Malaysia".

Setiap topik:
  hook      : (teks skrin, narasi) babak pembuka
  sections  : [(tajuk, warna, [(teks skrin pendek, narasi), ...]), ...]
Narasi ditulis dalam bahasa santai (cara orang bercakap), dan nombor dieja supaya TTS sebut dengan betul.
"""

RED, GOLD, GREEN = "red", "gold", "green"

TOPICS = [
    {
        "slug": "01_scam_skim_cepat_kaya",
        "title": "Scam & skim cepat kaya",
        "hook": ("Untung 30% sebulan, DIJAMIN?",
                 "Untung tiga puluh peratus sebulan, dijamin? Bro, tu bukan trading. Tu scam."),
        "sections": [
            ("TANDA-TANDA SCAM", RED, [
                ("Janji pulangan tetap / dijamin",
                 "Pertama, dia janji pulangan tetap. Siap cakap untung confirm."),
                ("Komisen bila ajak ahli baru",
                 "Kedua, korang dapat komisen kalau ajak member masuk. Tu dah macam skim piramid."),
                ("Akaun 'diurus', susah withdraw",
                 "Ketiga, duit korang dia yang uruskan. Bila nak keluarkan, ada je alasan."),
            ]),
            ("APA NAK BUAT", GREEN, [
                ("Semak Senarai Amaran SC & BNM",
                 "Sebelum masuk apa-apa, check dulu senarai amaran SC dengan Bank Negara. Free je."),
                ("Jangan serah duit / password akaun",
                 "Jangan sesekali bagi duit, atau password akaun trading, dekat orang lain."),
                ("Tiada siapa boleh jamin untung",
                 "Ingat ni. Dalam trading, takde siapa boleh jamin untung."),
            ]),
        ],
    },
    {
        "slug": "02_broker_tak_berlesen",
        "title": "Broker tak berlesen & susah withdraw",
        "hook": ("Deposit senang. Withdraw susah?",
                 "Deposit senang gila. Tapi bila nak withdraw, akaun kena freeze?"),
        "sections": [
            ("TANDA BROKER BERISIKO", RED, [
                ("Tiada lesen regulator yang jelas",
                 "Broker tu takde lesen yang jelas. Atau lesen dia, tak boleh nak check pun."),
                ("Bonus deposit yang melampau",
                 "Bagi bonus deposit seratus peratus. Tapi syarat dia, tersorok."),
                ("Withdraw ditangguh, syarat pelik",
                 "Withdraw kena tunggu berminggu. Lepas tu, tiba-tiba ada caj baru."),
            ]),
            ("APA NAK BUAT", GREEN, [
                ("Semak lesen di laman regulator sendiri",
                 "Check nombor lesen dia terus kat website regulator. Jangan percaya screenshot je."),
                ("Cuba withdraw jumlah kecil dulu",
                 "Lepas deposit, cuba withdraw sikit dulu. Test dia."),
                ("Jangan simpan semua modal di satu broker",
                 "Dan jangan letak semua modal, dalam satu broker."),
            ]),
        ],
    },
    {
        "slug": "03_guru_signal_sorok_loss",
        "title": "Guru & signal group sorok loss",
        "hook": ("Screenshot untung je. Mana loss?",
                 "Group signal asyik post screenshot profit je. Habis, loss dia mana?"),
        "sections": [
            ("TANDA-TANDA", RED, [
                ("Signal yang kena SL dipadam",
                 "Signal yang kena stop loss, dia delete senyap-senyap. Yang profit je, dia repost."),
                ("Flex kereta, jam, gaya hidup",
                 "Lebih banyak flex kereta, jam, holiday. Analisis, takde."),
                ("Kelas mahal, 'konfem profit'",
                 "Lepas tu, jual kelas mahal. Kononnya, confirm profit."),
            ]),
            ("APA NAK BUAT", GREEN, [
                ("Minta rekod penuh yang disahkan",
                 "Minta rekod penuh dia, yang verified. Termasuk semua loss."),
                ("Uji signal di akaun demo sebulan",
                 "Try ikut signal dia kat akaun demo dulu. Sebulan, paling kurang."),
                ("Belajar SEBAB setiap setup",
                 "Dan belajar kenapa setup tu diambil. Supaya korang tak bergantung dengan orang sampai bila-bila."),
            ]),
        ],
    },
    {
        "slug": "04_lot_besar_akaun_kecil",
        "title": "Lot besar, akaun kecil",
        "hook": ("Akaun $100. Buka 1 lot.",
                 "Akaun seratus dolar, terus buka satu lot. Satu candle je, akaun burn."),
        "sections": [
            ("KENAPA BAHAYA", RED, [
                ("Leverage tinggi buat lot nampak 'murah'",
                 "Leverage tinggi, macam satu nisbah seribu, buat lot besar tu nampak murah."),
                ("Tapi rugi pun ikut besar",
                 "Tapi bila harga lari lawan arah, rugi dia pun besar."),
                ("Margin call → stop out",
                 "Last-last, margin call. Broker tutup posisi korang, auto."),
            ]),
            ("APA NAK BUAT", GREEN, [
                ("Risiko 1–2% akaun setiap trade",
                 "Hadkan risiko, satu ke dua peratus je setiap trade."),
                ("Akaun RM2,000 → risiko RM20",
                 "Contoh, akaun dua ribu ringgit. Risiko satu peratus, cuma dua puluh ringgit."),
                ("Kira lot ikut jarak stop loss",
                 "Kira saiz lot ikut jarak stop loss. Bukan ikut feeling."),
            ]),
        ],
    },
    {
        "slug": "05_tiada_stop_loss_sangkut",
        "title": "Tiada stop loss & 'sangkut'",
        "hook": ("\"Nanti dia naik balik la...\"",
                 "Takpe, nanti dia naik balik la. Ayat ni, dah burn banyak akaun."),
        "sections": [
            ("APA YANG BERLAKU", RED, [
                ("Hold posisi rugi berminggu",
                 "Posisi tengah loss, korang biar je berminggu-minggu. Harap harga patah balik."),
                ("Tambah posisi yang sedang rugi",
                 "Lepas tu, tambah lagi posisi yang tengah loss. Konon nak average."),
                ("Swap dikenakan setiap malam",
                 "Sementara tu, caj swap jalan setiap malam."),
            ]),
            ("APA NAK BUAT", GREEN, [
                ("Letak SL sebelum entry",
                 "Tentukan stop loss, sebelum masuk trade."),
                ("Loss kecil = kos bisnes",
                 "Anggap loss kecil tu kos bisnes. Bukan kegagalan."),
                ("Jangan average posisi rugi",
                 "Dan jangan tambah posisi, yang tengah loss."),
            ]),
        ],
    },
    {
        "slug": "06_emosi_fomo_revenge",
        "title": "Emosi: FOMO & revenge trade",
        "hook": ("Baru loss, terus nak 'balas dendam'?",
                 "Baru kena loss, terus rasa nak balas dendam dekat market?"),
        "sections": [
            ("TANDA-TANDA", RED, [
                ("Kejar harga yang dah lari",
                 "Korang kejar harga yang dah lari jauh. Sebab takut terlepas."),
                ("Gandakan lot lepas loss",
                 "Lepas loss, terus double lot. Nak cover cepat."),
                ("Trade sebab bosan",
                 "Atau, buka trade sebab bosan je."),
            ]),
            ("APA NAK BUAT", GREEN, [
                ("Had 2–3 trade sehari",
                 "Set had. Contoh, dua ke tiga trade je sehari."),
                ("2 loss berturut = tutup chart",
                 "Kalau dah dua kali loss berturut-turut, tutup chart. Sambung esok."),
                ("Trading plan bertulis",
                 "Tulis trading plan korang. Masuk trade, bila setup tu betul-betul ada je."),
            ]),
        ],
    },
    {
        "slug": "07_duit_tak_mampu_hilang",
        "title": "Trade guna duit yang tak mampu hilang",
        "hook": ("Duit sewa rumah masuk trading?",
                 "Duit sewa rumah, duit personal loan, duit simpanan. Semua masuk akaun trading?"),
        "sections": [
            ("KENAPA BAHAYA", RED, [
                ("Tekanan duit = keputusan teruk",
                 "Bila duit tu korang perlukan, tekanan dia buat keputusan jadi teruk."),
                ("Hutang tetap kena bayar",
                 "Kalau akaun burn, hutang tetap kena bayar tiap bulan."),
                ("Keluarga ikut terkesan",
                 "Dan yang paling kena, family korang sendiri."),
            ]),
            ("APA NAK BUAT", GREEN, [
                ("Guna duit lebihan sahaja",
                 "Trade guna duit lebihan je. Yang kalau hilang pun, hidup korang tak terjejas."),
                ("Dana kecemasan 3–6 bulan dulu",
                 "Simpan duit kecemasan tiga ke enam bulan dulu."),
                ("Jangan berhutang untuk trading",
                 "Dan jangan sesekali berhutang, semata-mata nak trade."),
            ]),
        ],
    },
    {
        "slug": "08_masa_kerja_tidur",
        "title": "Sesi malam: kerja, tidur & keluarga",
        "hook": ("Market paling aktif masa kau patut tidur",
                 "Masa market paling aktif, kebanyakan trader Malaysia sepatutnya dah tidur."),
        "sections": [
            ("REALITI ZON MASA", RED, [
                ("London buka ~3–4 petang (MYT)",
                 "Sesi London buka, dalam pukul tiga ke empat petang."),
                ("New York buka ~8–9 malam (MYT)",
                 "New York pulak, dalam pukul lapan ke sembilan malam."),
                ("Berita besar (NFP) ~8:30–9:30 malam",
                 "Berita besar macam NFP, keluar malam-malam. Last-last tak cukup tidur, esok kerja pun hancur."),
            ]),
            ("APA NAK BUAT", GREEN, [
                ("Pilih SATU sesi sahaja",
                 "Pilih satu sesi je, yang ngam dengan jadual korang."),
                ("Guna pending order & alert",
                 "Guna pending order dengan alert. Tak payah tenung chart sampai pagi."),
                ("Tetapkan waktu tidur",
                 "Set waktu tidur. Akaun boleh tunggu. Kesihatan, tak boleh."),
            ]),
        ],
    },
    {
        "slug": "09_lompat_strategi_tiada_jurnal",
        "title": "Lompat strategi & tiada jurnal",
        "hook": ("Minggu ni SMC, minggu depan robot",
                 "Minggu ni SMC. Minggu depan indicator. Bulan depan, beli robot pulak."),
        "sections": [
            ("MASALAHNYA", RED, [
                ("Strategi ditukar sebelum diuji",
                 "Strategi tukar, sebelum sempat test betul-betul."),
                ("Tak tahu apa yang salah",
                 "Takde rekod, so korang tak tahu pun apa yang salah."),
                ("Ulang kesilapan yang sama",
                 "Jadi, silap yang sama, ulang balik tiap bulan."),
            ]),
            ("APA NAK BUAT", GREEN, [
                ("Satu strategi, 50–100 trade",
                 "Pegang satu strategi. Test lima puluh sampai seratus trade dulu, kat demo atau backtest."),
                ("Jurnal: entry, sebab, hasil, emosi",
                 "Catat setiap trade dalam jurnal. Entry, sebab, result, dan apa yang korang rasa masa tu."),
                ("Review setiap hujung minggu",
                 "Review jurnal setiap hujung minggu. Baru nampak, corak silap korang."),
            ]),
        ],
    },
    {
        "slug": "10_isu_syariah",
        "title": "Keliru isu syariah",
        "hook": ("Forex: halal atau haram?",
                 "Ramai trader Muslim kat Malaysia keliru. Forex ni sebenarnya, halal ke haram?"),
        "sections": [
            ("APA KATA FATWA", GOLD, [
                ("Muzakarah Fatwa Kebangsaan, 2010",
                 "Tahun dua ribu sepuluh, Muzakarah Jawatankuasa Fatwa Kebangsaan dah bincang pasal ni."),
                ("Forex individu secara lani (spot) melalui platform elektronik: HARAM",
                 "Keputusan dia, forex oleh individu secara lani, melalui platform elektronik, hukumnya haram."),
                ("Isu: riba (swap), margin, serah terima",
                 "Antara isu yang dibangkitkan, riba, margin, dengan syarat serah terima."),
            ]),
            ("APA NAK BUAT", GREEN, [
                ("Akaun 'swap-free' tak selesai semua isu",
                 "Akaun swap free, atau akaun Islamik, tak semestinya settle semua isu tu."),
                ("Rujuk pihak berautoriti agama",
                 "Rujuk pihak berautoriti agama. Bukan ustaz segera kat media sosial."),
                ("Ada pilihan patuh syariah lain",
                 "Ada pilihan lain, contohnya saham patuh syariah, yang disenaraikan oleh SC."),
            ]),
        ],
    },
]
