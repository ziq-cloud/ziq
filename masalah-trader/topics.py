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
    # ---------------- topik tambahan ----------------
    {
        "slug": "11_overtrading",
        "title": "Overtrading",
        "hook": ("Wajib trade setiap hari?",
                 "Rasa wajib masuk trade setiap hari? Tu bukan rajin. Tu overtrading."),
        "sections": [
            ("TANDA-TANDA", RED, [
                ("Trade walaupun takde setup", "Korang masuk trade, walaupun setup takde pun."),
                ("Belasan trade sehari", "Sehari boleh belasan trade. Spread je dah makan banyak."),
                ("Rasa rugi kalau tak trade", "Rasa macam rugi, kalau satu hari tak buka trade."),
            ]),
            ("APA NAK BUAT", GREEN, [
                ("Tunggu setup terbaik je", "Tunggu setup terbaik je. Yang lain, skip."),
                ("Set had trade harian", "Set had trade harian, dan patuh."),
                ("Tak trade = satu keputusan", "Ingat, tak trade pun, satu keputusan yang bijak."),
            ]),
        ],
    },
    {
        "slug": "12_untung_cepat_tutup_loss_dibiar",
        "title": "Untung cepat tutup, loss dibiar",
        "hook": ("Untung RM20 tutup. Loss RM200 biar?",
                 "Untung dua puluh ringgit, terus tutup. Tapi loss dua ratus ringgit, biar je?"),
        "sections": [
            ("MASALAHNYA", RED, [
                ("Takut untung hilang", "Korang takut untung tu hilang, jadi cepat-cepat tutup."),
                ("Harap loss patah balik", "Tapi bila loss, harap harga patah balik."),
                ("Banyak menang, akaun tetap turun", "Last-last, menang banyak kali pun, akaun tetap turun."),
            ]),
            ("APA NAK BUAT", GREEN, [
                ("Tetapkan target sebelum entry", "Tetapkan target untung, sebelum masuk trade."),
                ("Risk reward minimum 1:2", "Cari setup dengan risk reward, sekurang-kurangnya satu nisbah dua."),
                ("Biar SL & TP yang tutup", "Biar stop loss dengan take profit yang tutup. Bukan emosi."),
            ]),
        ],
    },
    {
        "slug": "13_takde_trading_plan",
        "title": "Takde trading plan",
        "hook": ("Masuk ikut feeling?",
                 "Masuk trade ikut feeling. Keluar pun, ikut feeling."),
        "sections": [
            ("MASALAHNYA", RED, [
                ("Tak tahu bila nak keluar", "Dah masuk, tapi tak tahu bila nak keluar."),
                ("Saiz lot ikut mood", "Saiz lot pun, ikut mood hari tu."),
                ("Takde apa boleh diukur", "Takde plan, so takde apa yang boleh diukur."),
            ]),
            ("APA NAK BUAT", GREEN, [
                ("Tulis: setup, entry, SL, TP", "Tulis plan. Setup apa, entry kat mana, stop loss, take profit."),
                ("Tetapkan risiko setiap trade", "Tetapkan risiko, untuk setiap trade."),
                ("Ikut plan, bukan feeling", "Lepas tu, ikut plan. Bukan feeling."),
            ]),
        ],
    },
    {
        "slug": "14_ego_salahkan_market",
        "title": "Ego, salahkan market",
        "hook": ("Broker tipu! Market manipulasi!",
                 "Broker tipu. Market manipulasi. Semua salah orang lain, kecuali kita?"),
        "sections": [
            ("TANDA-TANDA", RED, [
                ("Salahkan broker & berita", "Bila loss, terus salahkan broker, berita, atau market maker."),
                ("Tak nak cut loss", "Ego tak nak mengaku salah, jadi tak nak cut loss."),
                ("Tak belajar apa-apa", "Akhirnya, takde apa yang dipelajari."),
            ]),
            ("APA NAK BUAT", GREEN, [
                ("Loss = data, bukan hinaan", "Anggap loss tu data. Bukan hinaan."),
                ("Salah plan, atau tak ikut plan?", "Review. Plan yang salah, atau kita yang tak ikut plan?"),
                ("Market tak kenal korang", "Ingat, market tak kenal korang pun. Takde siapa nak tipu korang secara peribadi."),
            ]),
        ],
    },
    {
        "slug": "15_nak_cepat_kaya",
        "title": "Nak cepat kaya",
        "hook": ("Nak double akaun minggu ni?",
                 "Target nak double akaun, dalam seminggu?"),
        "sections": [
            ("KENAPA BAHAYA", RED, [
                ("Target tak realistik", "Target tak realistik, buat korang ambil risiko melampau."),
                ("Lot naik setiap kali menang", "Setiap kali menang, lot naik."),
                ("Satu loss, semua hilang", "Satu loss besar, semua hilang."),
            ]),
            ("APA NAK BUAT", GREEN, [
                ("Fokus proses, bukan duit", "Fokus pada proses, bukan duit."),
                ("Kompaun perlahan-lahan", "Biar akaun membesar perlahan-lahan. Kompaun tu kawan."),
                ("Survive dulu, baru kaya", "Survive dulu dalam market. Baru boleh fikir pasal kaya."),
            ]),
        ],
    },
    {
        "slug": "16_terlalu_banyak_indikator",
        "title": "Chart penuh indikator",
        "hook": ("Chart ke lukisan abstrak?",
                 "Chart korang ni, chart ke lukisan abstrak?"),
        "sections": [
            ("MASALAHNYA", RED, [
                ("Isyarat bercanggah", "Sepuluh indikator, semua bagi isyarat lain-lain."),
                ("Lambat buat keputusan", "Last-last, lambat buat keputusan."),
                ("Tak nampak harga sebenar", "Sampai tak nampak, harga tu sebenarnya buat apa."),
            ]),
            ("APA NAK BUAT", GREEN, [
                ("Mula dengan chart bersih", "Mula dengan chart bersih. Harga, struktur, dan level."),
                ("Satu dua indikator je", "Kalau nak guna, satu atau dua indikator je."),
                ("Faham fungsi setiap satu", "Dan faham, apa fungsi setiap satu."),
            ]),
        ],
    },
    {
        "slug": "17_trade_masa_berita",
        "title": "Trade masa berita besar",
        "hook": ("Berita keluar, terus masuk?",
                 "Berita besar keluar, terus tekan masuk?"),
        "sections": [
            ("APA YANG BERLAKU", RED, [
                ("Spread melebar tiba-tiba", "Masa berita, spread boleh melebar tiba-tiba."),
                ("Slippage, SL terlompat", "Kena slippage. Stop loss pun boleh terlompat."),
                ("Harga naik turun gila", "Harga naik turun gila, dua-dua arah."),
            ]),
            ("APA NAK BUAT", GREEN, [
                ("Semak kalendar ekonomi", "Semak kalendar ekonomi, setiap pagi."),
                ("Elak entry dekat masa berita", "Elak masuk trade, dekat-dekat masa berita."),
                ("Tunggu harga tenang", "Tunggu harga tenang dulu, baru cari setup."),
            ]),
        ],
    },
    {
        "slug": "18_abaikan_timeframe_besar",
        "title": "Abaikan timeframe besar",
        "hook": ("Entry M1, lawan trend Daily?",
                 "Entry kat M1, tapi lawan trend Daily?"),
        "sections": [
            ("APA YANG BERLAKU", RED, [
                ("Nampak 'reversal' kat M1", "Kat M1, nampak macam reversal."),
                ("Trend besar masih kuat", "Padahal, trend besar masih kuat."),
                ("Kena langgar trend", "Last-last, kena langgar dengan trend."),
            ]),
            ("APA NAK BUAT", GREEN, [
                ("Analisis dari timeframe besar", "Mula analisis dari timeframe besar dulu."),
                ("Ikut arah trend utama", "Ikut arah trend utama."),
                ("Timeframe kecil untuk entry je", "Timeframe kecil, guna untuk entry je."),
            ]),
        ],
    },
    {
        "slug": "19_backtest_syok_sendiri",
        "title": "Backtest syok sendiri",
        "hook": ("Backtest +300%, live burn?",
                 "Backtest untung tiga ratus peratus. Masuk live, burn."),
        "sections": [
            ("MASALAHNYA", RED, [
                ("Pilih contoh cantik je", "Pilih contoh yang cantik-cantik je."),
                ("Ubah rules ikut keputusan", "Tukar rules, sampai keputusan nampak cantik."),
                ("Lupa spread & slippage", "Lupa kira spread, komisen, dan slippage."),
            ]),
            ("APA NAK BUAT", GREEN, [
                ("Uji data yang banyak", "Uji dengan data yang banyak, termasuk masa market teruk."),
                ("Rules tetap sebelum uji", "Tetapkan rules sebelum uji. Jangan ubah lepas tengok keputusan."),
                ("Forward test di demo", "Lepas tu, forward test kat demo dulu."),
            ]),
        ],
    },
    {
        "slug": "20_kos_tersembunyi",
        "title": "Kos tersembunyi",
        "hook": ("Selalu untung, akaun tak naik?",
                 "Rasa selalu untung, tapi akaun tak naik-naik?"),
        "sections": [
            ("KOS YANG KORANG LUPA", RED, [
                ("Spread setiap kali entry", "Setiap kali entry, korang dah bayar spread."),
                ("Komisen & swap", "Tambah lagi komisen, dengan swap kalau hold overnight."),
                ("Scalping kecil, kos besar", "Scalping target kecil, kos dia makan sebahagian besar untung."),
            ]),
            ("APA NAK BUAT", GREEN, [
                ("Kira kos sebelum entry", "Kira kos, sebelum masuk trade."),
                ("Pilih akaun & pair kos rendah", "Pilih jenis akaun dan pair, yang kos dia rendah."),
                ("Target jauh lebih besar dari kos", "Pastikan target, jauh lebih besar dari kos."),
            ]),
        ],
    },
    {
        "slug": "21_tak_reti_urus_untung",
        "title": "Tak reti urus untung",
        "hook": ("Untung, tapi tak pernah withdraw?",
                 "Untung sikit, terus withdraw semua. Atau, tak pernah withdraw langsung?"),
        "sections": [
            ("MASALAHNYA", RED, [
                ("Withdraw semua, akaun tak membesar", "Withdraw semua untung, akaun tak pernah membesar."),
                ("Tak pernah withdraw", "Atau tak pernah withdraw. Last-last, hangus dalam market."),
                ("Takde sistem", "Dua-dua, sebab takde sistem."),
            ]),
            ("APA NAK BUAT", GREEN, [
                ("Tetapkan peratus withdraw", "Tetapkan peratus. Contoh, separuh untung withdraw, separuh biar."),
                ("Withdraw ikut jadual", "Withdraw ikut jadual, contoh setiap bulan."),
                ("Untung sebenar = dalam bank", "Ingat, untung sebenar, bila dah masuk bank."),
            ]),
        ],
    },
    {
        "slug": "22_robot_indikator_rahsia",
        "title": "Beli robot & indikator rahsia",
        "hook": ("Robot win rate 99%?",
                 "Robot trading, win rate sembilan puluh sembilan peratus. Harga, dua ribu ringgit?"),
        "sections": [
            ("TANDA-TANDA", RED, [
                ("Backtest cantik, live hancur", "Backtest cantik, tapi live hancur."),
                ("Martingale tersorok", "Ramai guna martingale. Gandakan lot, bila loss."),
                ("Penjual untung dari jualan", "Penjual untung dari jual robot, bukan dari trading."),
            ]),
            ("APA NAK BUAT", GREEN, [
                ("Minta rekod live yang disahkan", "Minta rekod live yang verified. Bukan backtest."),
                ("Uji di demo berbulan", "Uji kat demo, berbulan-bulan dulu."),
                ("Faham logik robot tu", "Faham logik robot tu. Kalau tak faham, jangan guna."),
            ]),
        ],
    },
    {
        "slug": "23_sorok_dari_keluarga",
        "title": "Sorok trading dari keluarga",
        "hook": ("Family tak tahu akaun dah burn?",
                 "Family tak tahu pun, akaun dah burn tiga kali?"),
        "sections": [
            ("KENAPA BAHAYA", RED, [
                ("Stres tanggung seorang", "Stres tu, korang tanggung seorang diri."),
                ("Duit rumah tangga terguna", "Kadang-kadang, duit rumah tangga pun terguna."),
                ("Hilang kepercayaan", "Bila terbongkar, kepercayaan yang hilang."),
            ]),
            ("APA NAK BUAT", GREEN, [
                ("Jujur dengan pasangan", "Jujur dengan pasangan, atau keluarga."),
                ("Bincang had modal bersama", "Bincang sama-sama, berapa had modal yang boleh guna."),
                ("Asingkan duit trading", "Asingkan duit trading, dari duit keluarga."),
            ]),
        ],
    },
    {
        "slug": "24_banding_diri_media_sosial",
        "title": "Banding diri dengan orang lain",
        "hook": ("Dia profit RM10k, aku loss lagi?",
                 "Tengok orang flex profit sepuluh ribu. Kita pulak, loss lagi?"),
        "sections": [
            ("MASALAHNYA", RED, [
                ("Media sosial tunjuk highlight je", "Media sosial tunjuk highlight je. Bukan keseluruhan."),
                ("Rasa ketinggalan, terus FOMO", "Korang rasa ketinggalan, terus FOMO."),
                ("Naikkan risiko nak kejar", "Naikkan risiko, nak kejar orang lain."),
            ]),
            ("APA NAK BUAT", GREEN, [
                ("Banding dengan diri semalam", "Bandingkan dengan diri korang semalam. Bukan dengan orang lain."),
                ("Ukur ikut jurnal sendiri", "Ukur kemajuan, ikut jurnal sendiri."),
                ("Kurang scroll, banyak belajar", "Kurangkan scroll. Banyakkan belajar."),
            ]),
        ],
    },
    {
        "slug": "25_burnout",
        "title": "Burnout trading 24 jam",
        "hook": ("Forex, crypto, 24 jam tak rehat?",
                 "Siang forex, malam crypto. Hujung minggu pun, tengok chart?"),
        "sections": [
            ("TANDA-TANDA", RED, [
                ("Penat, keputusan jadi teruk", "Bila penat, keputusan trading pun jadi teruk."),
                ("Mudah marah & stres", "Mudah marah, dan sentiasa stres."),
                ("Kesihatan & keluarga terabai", "Kesihatan dengan keluarga, terabai."),
            ]),
            ("APA NAK BUAT", GREEN, [
                ("Waktu trading tetap", "Tetapkan waktu trading yang tetap."),
                ("Cuti dari chart", "Ambil cuti dari chart, sekurang-kurangnya sehari seminggu."),
                ("Tidur, sukan, keluarga", "Tidur cukup, bersukan, dan luangkan masa dengan keluarga."),
            ]),
        ],
    },
]
