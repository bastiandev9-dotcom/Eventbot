"""
Regex Rules
===========
Intent detection & entity extraction via regex.
"""

import re
from typing import Dict, List, Tuple

# ── INTENT RULES ──────────────────────────────────────────
INTENT_RULES = {
    # ── Sapaan ────────────────────────────────────────────
    "sapaan": [
        r"\b(halo|hai|hey|helo|hi|hello|haii|haloo|halo\s+bot)\b",
        r"\b(assalamualaikum|wa\s*alaikum|waalaikumsalam)\b",
        r"\b(selamat\s+(pagi|siang|sore|malam|datang))\b",
        r"\b(apa\s+kabar|gimana\s+kabar|how\s+are\s+you)\b",
        r"\b(permisi|excuse\s+me|hei|yo|sup)\b",
        r"^(halo?|hai|hi|hey)[.!?\s]*$",   # sapaan singkat di awal kalimat
    ],

    # ── Bantuan ───────────────────────────────────────────
    "tanya_bantuan": [
        r"\b(bantu|bantuan|tolong|panduan|petunjuk|arahan)\b",
        r"\b(fitur|fungsi|kemampuan|bisa\s+apa|bisa\s+ngapain|bisa\s+ngapa\s+aja)\b",
        r"\b(menu|help|ajarin|ajari|ajarkan)\b",
        # "cara pakai/menggunakan/daftar/mendaftar" — KECUALI yang berkaitan dengan tiket/booking
        # (kalimat dengan tiket/booking ditangani oleh daftar_tiket)
        r"\b(cara\s+(?:pakai|menggunakan))\b(?!.*\b(tiket|ticket|booking|beli|pesan)\b)",
        r"\b(cara\s+(daftar|mendaftar))\b(?!.*\b(tiket|ticket|event|acara)\b)",
        r"\b(gimana\s+cara|bagaimana\s+cara)\b(?!.*\b(tiket|ticket|booking|beli|pesan|order)\b)",
        r"\b(apa\s+itu\s+eventbot|eventbot\s+itu\s+apa|ini\s+apa)\b",
        r"\b(langkah|tutorial|guide|petunjuk\s+penggunaan)\b",
        r"\b(tidak\s+tahu|nggak\s+tau|gak\s+tau|bingung)\b",
    ],

    # ── Booking tiket (cek SEBELUM cari_event) ────────────
    "daftar_tiket": [
        r"\b(pesan|booking|beli|ambil|order|purchase)\b.*\b(tiket|ticket)\b",
        r"\b(daftar|registrasi|register)\b.*\b(tiket|ticket)\b",
        r"\b(pesan|booking|beli|order)\b.*\b(event|acara|kegiatan)\b",
        r"\b(mau\s+ikut|ikut|join|gabung|hadir)\b.*\b(event|acara|kegiatan)\b",
        r"\bdaftar\s+(event|acara|kegiatan|sekarang)\b",
        r"\b(ingin|mau|pengen|pengin)\b.*\b(beli|pesan|daftar)\b.*\b(tiket|ticket)\b",
        # "gimana cara booking/beli/pesan tiket" — lebih spesifik dari tanya_bantuan
        r"\b(cara|gimana|bagaimana)\b.*\b(booking|beli|pesan|order)\b.*\b(tiket|ticket)\b",
        r"\b(tiket\s+masih\s+ada|tiket\s+tersedia|sisa\s+tiket)\b",
        r"\b(mau\s+registrasi|mau\s+register|mau\s+mendaftar)\b",
    ],

    # ── Detail event (cek SEBELUM cari_event) ─────────────
    "detail_event": [
        r"\b(detail|tentang|mengenai|soal)\b.*\b(event|acara|konferensi|seminar|workshop|festival)\b",
        r"\b(info|informasi|cerita|ceritakan)\b.*\b(acara|konferensi|seminar|workshop|festival)\b",
        r"\b(tiket|harga|biaya|cost|fee|bayar)\b.*\b(event|acara)\b",
        r"\b(berapa\s+harga|harga\s+tiket|harga\s+masuk|biaya\s+masuk)\b",
        r"\b(lokasi|tempat|venue|di\s+mana|dimana)\b.*\b(event|acara|acara\s+nya)\b",
        r"\b(jam\s+berapa|pukul\s+berapa|kapan\s+mulai|kapan\s+selesai)\b",
        r"\b(siapa\s+pembicara|speaker|narasumber|bintang\s+tamu)\b",
        r"\b(ada\s+berapa\s+tiket|kuota|kapasitas)\b",
        r"\b(event\s+ini|acara\s+ini|acara\s+tadi|event\s+tadi)\b",
        r"\b(lebih\s+lanjut|selengkapnya|lengkapnya|ingin\s+tahu\s+lebih)\b",
    ],

    # ── Cari event ────────────────────────────────────────
    "cari_event": [
        r"\b(cari|temukan|tampilkan|tunjukkan|kasih\s+tau|kasih\s+tahu)\b.*\b(event|konferensi|acara|seminar|workshop|festival|pertunjukan|pameran)\b",
        r"\b(event|konferensi|acara|seminar|workshop|festival)\b.*\b(cari|temukan|ada|tersedia)\b",
        r"\b(event|konferensi|acara|seminar|workshop)\b\s*apa\s*(saja|aja)?\b",
        r"\b(event|acara)\b.*\b(apa|gimana|bagaimana|mana\s+saja|mana\s+aja)\b",
        r"\b(ada\s+event|ada\s+acara|ada\s+kegiatan)\b",
        r"\b(ada\s+apa|yang\s+ada|apa\s+yang\s+ada)\b",
        r"\b(rekomendasi|rekomen|saran|sarankan)\b.*\b(event|acara|kegiatan)\b",
        r"\b(info|informasi)\b.*\bevent\b",
        r"\bdaftar\b.*\b(acara|konferensi|seminar|workshop|festival)\b",
        r"\b(event|acara)\b.*\b(hari\s+ini|besok|minggu\s+ini|bulan\s+ini|weekend|akhir\s+pekan)\b",
        r"\b(event|acara)\b.*\b(gratis|free|murah|terjangkau)\b",
        r"\b(event|acara)\b.*\b(online|virtual|offline|tatap\s+muka)\b",
        r"\b(event|acara|kegiatan)\b.*\b(menarik|bagus|keren|seru)\b",
        r"\b(mau\s+nonton|mau\s+ngilmu|mau\s+belajar)\b",
        r"\b(lihat\s+semua|semua\s+event|tampilkan\s+semua)\b",
        # Pola: "[kategori/topik] event/acara" tanpa kata kerja eksplisit
        r"\b(teknologi|bisnis|musik|gaming|kesehatan|seni|komunitas|pendidikan)\b.*\b(event|acara|seminar|workshop)\b",
        r"\b(event|acara|seminar|workshop)\b.*\b(teknologi|bisnis|musik|gaming|kesehatan|seni|komunitas|pendidikan)\b",
    ],

    # ── Jadwal / registrasi user ──────────────────────────
    "lihat_jadwal": [
        r"\b(jadwal|schedule|kalender)\b",
        r"\b(event\s+saya|acara\s+saya|kegiatan\s+saya|tiket\s+saya)\b",
        r"\b(event|acara)\b.*\b(saya|aku|gue|gw)\b",
        r"\b(sudah\s+daftar|udah\s+daftar|terdaftar|sudah\s+registrasi)\b",
        r"\b(tiket\s+yang\s+saya\s+punya|tiket\s+yang\s+aku\s+punya)\b",
        r"\b(riwayat\s+(pemesanan|registrasi|pendaftaran|tiket))\b",
        r"\b(history|histori)\b.*\b(tiket|event|pemesanan)\b",
        r"\b(event\s+apa\s+yang\s+sudah|acara\s+apa\s+yang\s+sudah)\b",
        r"\b(cek\s+tiket|lihat\s+tiket|periksa\s+tiket)\b",
        r"\b(pesanan\s+saya|order\s+saya|booking\s+saya)\b",
    ],

    # ── Profil ────────────────────────────────────────────
    "profil": [
        r"\b(profil|profile|akun|account)\b",
        r"\b(data\s+diri|data\s+saya|biodata)\b",
        r"\b(nama\s+saya|email\s+saya|nomor\s+saya|hp\s+saya)\b",
        r"\b(siapa\s+saya|siapa\s+aku|info\s+akun)\b",
        r"\b(pengaturan\s+akun|setting\s+akun|ubah\s+profil|edit\s+profil)\b",
        r"\b(ganti\s+password|ubah\s+password|lupa\s+password|reset\s+password)\b",
        r"\b(saldo|poin|reward)\b",
    ],

    # ── Keluar / penutup ──────────────────────────────────
    "keluar": [
        r"\b(keluar|dadah|bye|goodbye|good\s+bye|ciao|au\s+revoir)\b",
        r"\b(sampai\s+jumpa|sampai\s+ketemu|see\s+you|see\s+ya)\b",
        r"\b(quit|exit|selesai|sudah\s+cukup|cukup)\b",
        r"\b(terima\s+kasih|makasih|thanks|thank\s+you|thx|tengkyu)\b",
        r"\b(oke\s+deh|oke\s+makasih|ok\s+thanks|baik\s+terima\s+kasih)\b",
        r"\b(tidak\s+perlu|nggak\s+perlu|gak\s+perlu)\b",
        r"\b(pamit|numpang\s+tanya\s+doang|udah\s+itu\s+aja)\b",
    ],
}

# ── ENTITY PATTERNS ──────────────────────────────────────
ENTITY_PATTERNS = {
    # ── Lokasi ────────────────────────────────────────────
    "location": [
        # "di [kota]" — tangkap satu kata setelah preposisi, bukan lebih
        r"\b(?:di|di\s+kota|di\s+area|di\s+daerah|di\s+wilayah)\s+([A-Za-z]+)\b",
        r"\b(Jakarta(?:\s+(?:Selatan|Pusat|Barat|Utara|Timur))?)\b",
        r"\b(Bandung|Surabaya|Yogyakarta|Jogja|Bali|Denpasar)\b",
        r"\b(Medan|Makassar|Semarang|Malang|Depok|Tangerang|Bekasi|Bogor)\b",
        r"\b(Palembang|Balikpapan|Manado|Pekanbaru|Padang|Banjarmasin)\b",
        r"\b(online|zoom|virtual|hybrid|live\s+streaming|streaming|webinar)\b",
        r"\b(offline|tatap\s+muka|luring|onsite|on\s*site)\b",
    ],

    # ── Tanggal / waktu ───────────────────────────────────
    "date": [
        r"\b(hari\s+ini|today)\b",
        r"\b(besok|tomorrow|lusa|overmorgen)\b",
        r"\b(minggu\s+ini|minggu\s+depan|minggu\s+lalu|pekan\s+ini|pekan\s+depan)\b",
        r"\b(bulan\s+ini|bulan\s+depan|bulan\s+lalu|next\s+month)\b",
        r"\b(weekend|akhir\s+pekan|sabtu|minggu|ahad)\b",
        r"\b(tanggal\s+\d{1,2}(?:\s+\w+)?)\b",
        r"\b(\d{1,2}\s+(?:Januari|Februari|Maret|April|Mei|Juni|Juli|Agustus|September|Oktober|November|Desember))\b",
        r"\b(Januari|Februari|Maret|April|Mei|Juni|Juli|Agustus|September|Oktober|November|Desember)\b",
        r"\b(Jan|Feb|Mar|Apr|Jun|Jul|Agt|Sep|Okt|Nov|Des)\b",
        r"\b(20\d{2})\b",
        r"\b(triwulan|kuartal|semester|Q[1-4])\b",
    ],

    # ── Harga ─────────────────────────────────────────────
    "price": [
        r"\b(gratis|free|gratisan|tidak\s+berbayar|tanpa\s+biaya|cuma-cuma)\b",
        r"\b(di\s+bawah\s+([\d\.]+)\s*(ribu|rb|k|juta|jt)?)\b",
        r"\b(maksimal\s+([\d\.]+)\s*(ribu|rb|k|juta|jt)?)\b",
        r"\b(murah|terjangkau|hemat|ekonomis|budget)\b",
        r"\b(mahal|premium|vip|eksklusif|exclusive)\b",
        r"\b(under\s+\d+|below\s+\d+)\b",
        r"\b([\d\.]+\s*(ribu|rb|k|juta|jt))\b",
    ],

    # ── Kategori ──────────────────────────────────────────
    "category": [
        # Teknologi
        r"\b(teknologi|technology|tech|it|digital|coding|programming|pemrograman)\b",
        r"\b(ai|artificial\s+intelligence|kecerdasan\s+buatan|machine\s+learning|ml|deep\s+learning)\b",
        r"\b(data\s+science|data\s+scientist|big\s+data|analitik|analytic)\b",
        r"\b(cyber\s*security|keamanan\s+siber|hacking|ethical\s+hacker)\b",
        r"\b(web|mobile|android|ios|flutter|react|python|javascript)\b",
        r"\b(cloud|devops|blockchain|metaverse|iot|internet\s+of\s+things)\b",
        # Bisnis
        r"\b(bisnis|business|startup|wirausaha|entrepreneur|kewirausahaan)\b",
        r"\b(marketing|pemasaran|digital\s+marketing|branding|sales)\b",
        r"\b(investasi|saham|crypto|keuangan|finansial|finance)\b",
        r"\b(manajemen|leadership|kepemimpinan|hrm|sdm)\b",
        # Pendidikan
        r"\b(edukasi|pendidikan|education|belajar|workshop|seminar|kursus|pelatihan|training)\b",
        r"\b(beasiswa|scholarship|kampus|universitas|mahasiswa)\b",
        # Hiburan & Seni
        r"\b(hiburan|entertainment|konser|concert|pertunjukan|show)\b",
        r"\b(musik|music|band|festival\s+musik|jazz|pop|indie)\b",
        r"\b(seni|art|budaya|culture|lukis|tari|teater|theater)\b",
        r"\b(film|cinema|bioskop|screening|pameran|galeri|gallery)\b",
        # Komunitas & Sosial
        r"\b(sosial|social|komunitas|community|networking|relawan|volunteer)\b",
        r"\b(meetup|gathering|kopdar|temu\s+kopi|diskusi)\b",
        # Kesehatan
        r"\b(kesehatan|health|wellness|medis|medical|dokter)\b",
        r"\b(yoga|meditasi|meditation|fitness|olahraga|gym|lari|marathon)\b",
        r"\b(mental\s+health|kesehatan\s+mental|psikologi)\b",
        # Gaming & Esports
        r"\b(gaming|game|esport|e-sport|tournament|turnamen|kompetisi)\b",
        r"\b(mobile\s+legends|ml|pubg|valorant|dota|lol|league\s+of\s+legends)\b",
    ],

    # ── Status tiket ──────────────────────────────────────
    "ticket_status": [
        r"\b(tersedia|available|ada\s+tiket|masih\s+ada)\b",
        r"\b(habis|sold\s+out|kehabisan|penuh)\b",
        r"\b(sisa\s+\d+|tinggal\s+\d+)\b",
    ],

    # ── Jumlah tiket ──────────────────────────────────────
    "quantity": [
        r"\b(\d+)\s*(tiket|lembar|pcs|buah)\b",
        r"\b(satu|dua|tiga|empat|lima|enam|tujuh|delapan|sembilan|sepuluh)\s*(tiket|lembar)?\b",
        r"\buntuk\s+(\d+)\s+orang\b",
    ],
}


def match_intent(text: str) -> str:
    """
    Deteksi intent dari input teks user.
    Urutan pengecekan penting — intent lebih spesifik dicek lebih dulu.
    Return intent string atau 'tidak_dikenal'.
    """
    cleaned = text.strip().lower()

    for intent, patterns in INTENT_RULES.items():
        for pattern in patterns:
            if re.search(pattern, cleaned, re.IGNORECASE):
                return intent

    return "tidak_dikenal"


def extract_entities(text: str) -> Dict[str, List[str]]:
    """
    Ekstrak entity dari teks user.
    Return dict {entity_type: [values]}.
    """
    cleaned = text.strip().lower()
    entities = {}

    for entity_type, patterns in ENTITY_PATTERNS.items():
        matches = []
        for pattern in patterns:
            found = re.findall(pattern, cleaned, re.IGNORECASE)
            if found:
                for match in found:
                    if isinstance(match, tuple):
                        matches.extend([m.strip() for m in match if m and m.strip()])
                    else:
                        if match.strip():
                            matches.append(match.strip())

        if matches:
            entities[entity_type] = list(dict.fromkeys(matches))  # deduplicate, preserve order

    # ── Ekstrak nama event spesifik ───────────────────────
    event_match = re.search(
        r"(?:event|acara|konferensi|workshop|seminar|festival)\s+([A-Za-z0-9\s]+?)(?:\s+(?:di|tanggal|pada|bulan|tahun|\d)|[?!.]|$)",
        cleaned, re.IGNORECASE
    )
    if event_match:
        name = event_match.group(1).strip()
        if len(name) > 2:
            entities["event_name"] = [name]

    # ── Ekstrak query bebas ───────────────────────────────
    # Hapus stopwords umum dan sisakan kata kunci pencarian
    stopwords = r"\b(cari|temukan|lihat|daftar|info|event|acara|di|tanggal|berapa|harga|ada|apa|saja|yang|dan|atau|untuk|dari|ke|tentang|mengenai|tolong|mau|minta|gimana|bagaimana|apakah|boleh|bisa|saya|aku|gue)\b"
    query = re.sub(stopwords, "", cleaned, flags=re.IGNORECASE)
    query = re.sub(r"\s+", " ", query).strip()
    if query and len(query) > 2:
        entities["query"] = [query]

    return entities