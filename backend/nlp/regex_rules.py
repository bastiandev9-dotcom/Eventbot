"""
Regex Rules
===========
Intent detection & entity extraction via regex.
"""

import re
from typing import Dict, List, Tuple

# ── INTENT RULES ──────────────────────────────────────────
INTENT_RULES = {
    "sapaan": [
        r"\b(halo|hai|hey|helo|hi|assalamualaikum|selamat\s+(pagi|siang|sore|malam))\b",
    ],
    "tanya_bantuan": [
        r"\b(bantu|bantuan|tolong|panduan|fitur|bisa\s+apa|menu|help)\b",
        r"\b(cara\s+pakai|cara\s+menggunakan)\b",
    ],
    # daftar_tiket HARUS sebelum cari_event karena "daftar event" bisa ambigu
    "daftar_tiket": [
        r"\b(pesan|booking|beli|ambil)\b.*\b(tiket|ticket)\b",
        r"\b(daftar|pesan|booking|beli)\b.*\b(tiket|ticket)\b",
        r"\b(pesan|booking|beli)\b.*\b(event|acara)\b",
        r"\b(mau\s+ikut|ikut|join)\b.*\b(event|acara)\b",
        r"\bdaftar\s+event\b",
    ],
    # detail_event HARUS sebelum cari_event karena "info acara X" bisa ambigu
    "detail_event": [
        r"\b(detail|tentang)\b.*\b(event|acara|konferensi|seminar)\b",
        r"\b(info|informasi)\b.*\b(acara|konferensi|seminar|workshop)\b",
        r"\b(tiket|harga|lokasi)\b.*\b(event|acara)\b",
        r"\b(berapa\s+harga|harga\s+tiket)\b",
    ],
    "cari_event": [
        r"\b(cari|temukan|lihat)\b.*\b(event|konferensi|acara|seminar|workshop)\b",
        r"\b(event|konferensi|acara|seminar|workshop)\b.*\b(cari|temukan|lihat|info|informasi)\b",
        r"\b(event|konferensi|acara|seminar|workshop)\b\s*apa\s*saja\b",
        r"\b(event|acara)\b.*\b(apa|gimana|bagaimana)\b",
        r"\b(ada\s+apa|yang\s+ada)\b",
        r"\b(rekomendasi|saran)\b.*\b(event|acara)\b",
        r"\b(info|informasi)\b.*\bevent\b",
        r"\bdaftar\b.*\b(acara|konferensi|seminar|workshop)\b",
        r"\bdaftar\b.*\b(konferensi|seminar|workshop)\b",
    ],
    "lihat_jadwal": [
        r"\b(jadwal|schedule|kalender|event\s+saya|tiket\s+saya)\b",
        r"\b(event|acara)\b.*\b(saya|aku|gue)\b",
        r"\b(sudah\s+daftar|terdaftar)\b",
    ],
    "profil": [
        r"\b(profil|profile|akun|account|data\s+diri)\b",
        r"\b(nama\s+saya|email\s+saya|data\s+saya)\b",
    ],
    "keluar": [
        r"\b(keluar|dadah|bye|sampai\s+jumpa|quit|exit|terima\s+kasih)\b",
    ],
}

# ── ENTITY PATTERNS ──────────────────────────────────────
ENTITY_PATTERNS = {
    "location": [
        r"\b(di|di\s+kota|di\s+area)\s+([A-Za-z\s]+)",
        r"\b(Jakarta|Bandung|Surabaya|Yogyakarta|Bali|Medan|Makassar|Semarang|Malang|Depok|Tangerang|Bekasi)\b",
        r"\b(online|zoom|virtual|hybrid)\b",
    ],
    "date": [
        r"\b(besok|lusa|minggu\s+depan|bulan\s+depan)\b",
        r"\b(tanggal\s+\d{1,2})\b",
        r"\b(Januari|Februari|Maret|April|Mei|Juni|Juli|Agustus|September|Oktober|November|Desember)\b",
        r"\b(\d{4})\b",
    ],
    "price": [
        r"\b(di\s+bawah\s+([\d\.]+)(\s*ribu|k)?)\b",
        r"\b(murah|gratis|free|hemat)\b",
        r"\b(mahal|premium|vip)\b",
    ],
    "category": [
        r"\b(teknologi|technology|tech|it|digital)\b",
        r"\b(bisnis|business|startup|entrepreneur)\b",
        r"\b(edukasi|education|workshop|seminar|kursus)\b",
        r"\b(hiburan|entertainment|konser|musik)\b",
        r"\b(sosial|social|komunitas|community)\b",
        r"\b(kesehatan|health|wellness|yoga)\b",
        r"\b(seni|art|budaya|culture)\b",
    ],
}


def match_intent(text: str) -> str:
    """
    Deteksi intent dari input teks user.
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
                # Handle tuple return dari regex groups
                for match in found:
                    if isinstance(match, tuple):
                        matches.extend([m for m in match if m])
                    else:
                        matches.append(match)

        if matches:
            entities[entity_type] = list(set(matches))  # Remove duplicates

    # Extract event name (anything between "event" and "di/tanggal" or end)
    event_match = re.search(r"(?:event|acara|konferensi|workshop|seminar)\s+([A-Za-z\s]+?)(?:\s+(?:di|tanggal|pada|\d)|$)", cleaned, re.IGNORECASE)
    if event_match:
        entities["event_name"] = [event_match.group(1).strip()]

    # Extract query (full text minus common words)
    query = re.sub(r"\b(cari|temukan|lihat|daftar|info|event|acara|di|tanggal|berapa|harga)\b", "", cleaned)
    query = query.strip()
    if query and len(query) > 2:
        entities["query"] = [query]

    return entities