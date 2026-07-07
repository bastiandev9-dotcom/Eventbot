# Chatbot Intents — EventBot NLP

Dokumen ini menjelaskan semua intent yang dikenali chatbot EventBot, pola regex yang digunakan untuk deteksinya, contoh kalimat, entity yang diekstrak, dan respons yang dihasilkan.

Chatbot EventBot menggunakan pendekatan **rule-based NLP** berbasis regex — implementasi langsung dari konsep Teori Bahasa dan Otomata (finite automata / regular expression). Tidak memerlukan model machine learning eksternal.

---

## Daftar Isi

- [Cara Kerja NLP](#cara-kerja-nlp)
- [Intent](#intent)
  - [sapaan](#1-sapaan)
  - [tanya_bantuan](#2-tanya_bantuan)
  - [cari_event](#3-cari_event)
  - [detail_event](#4-detail_event)
  - [daftar_tiket](#5-daftar_tiket)
  - [lihat_jadwal](#6-lihat_jadwal)
  - [profil](#7-profil)
  - [keluar](#8-keluar)
  - [tidak_dikenal](#9-tidak_dikenal-fallback)
- [Entity Extraction](#entity-extraction)
- [Context Management](#context-management)
- [Quick Replies](#quick-replies)
- [Prioritas Matching](#prioritas-matching)

---

## Cara Kerja NLP

```
User Input
    │
    ▼
Preprocessing (lowercase, strip)
    │
    ▼
Intent Detection (regex match INTENT_RULES)
    │
    ▼
Entity Extraction (regex match ENTITY_PATTERNS)
    │
    ▼
Context Lookup (session state)
    │
    ▼
Response Builder → respons teks + quick_replies
    │
    ▼
Context Update (simpan intent, entity, event terakhir)
```

Proses terjadi di `backend/nlp/regex_rules.py` (matching) dan `backend/services/chatbot_service.py` (orkestrasi).

---

## Intent

### 1. `sapaan`

Deteksi saat user memberi salam atau menyapa chatbot.

**Pola regex:**
```
\b(halo|hai|hey|helo|hi|assalamualaikum|selamat\s+(pagi|siang|sore|malam))\b
```

**Contoh kalimat:**
- "Halo"
- "Hai EventBot"
- "Hey, ada yang bisa bantu?"
- "Assalamualaikum"
- "Selamat pagi"
- "Hi bot"

**Respons:**
> Halo! Selamat datang di EventBot! 👋
>
> Saya bisa membantu Anda dengan:
> 🔍 Cari event
> 📋 Lihat daftar event
> 🎫 Daftar tiket
> ❓ Bantuan
>
> Ada yang bisa saya bantu?

**Quick replies:** `🔍 Cari Event` | `📋 Lihat Event` | `❓ Bantuan`

---

### 2. `tanya_bantuan`

Deteksi saat user meminta panduan atau informasi fitur.

**Pola regex:**
```
\b(bantu|bantuan|tolong|panduan|fitur|bisa\s+apa|menu|help)\b
\b(cara\s+pakai|cara\s+menggunakan)\b
```

**Contoh kalimat:**
- "Bantuan"
- "Kamu bisa apa?"
- "Menu"
- "Help"
- "Cara pakai chatbot ini"
- "Tolong jelaskan fiturnya"

**Respons:**

Menu bantuan lengkap yang menjelaskan semua fitur:
- Cara mencari event
- Cara melihat daftar event
- Cara booking tiket
- Cara melihat profil dan jadwal

**Quick replies:** `🔍 Cari Event di Jakarta` | `📋 Event Teknologi` | `🎫 Tiket Saya`

---

### 3. `cari_event`

Deteksi saat user ingin mencari atau menelusuri event.

**Pola regex:**
```
\b(cari|temukan|lihat)\b.*\b(event|konferensi|acara|seminar|workshop)\b
\b(event|acara)\b.*\b(apa|gimana|bagaimana)\b
\b(event|konferensi|acara|seminar|workshop)\b\s*apa\s*saja\b
\b(ada\s+apa|yang\s+ada)\b
\b(rekomendasi|saran)\b.*\b(event|acara)\b
\b(info|informasi)\b.*\bevent\b
\bdaftar\b.*\b(acara|konferensi|seminar|workshop)\b
```

**Contoh kalimat:**
- "Cari event teknologi di Jakarta"
- "Ada event apa saja minggu ini?"
- "Event musik bulan Agustus"
- "Rekomendasi seminar tentang AI"
- "Info event gratis di Bandung"
- "Lihat daftar workshop"

**Entity yang diekstrak:**
- `location` — kota atau mode (online/offline)
- `category` — bidang event
- `date` — tanggal atau periode
- `price` — preferensi harga
- `query` — kata kunci bebas

**Respons:** Daftar event (maks 5) yang cocok dengan filter, atau pesan "tidak ditemukan" jika kosong.

**Quick replies:** `📋 Lihat Detail` | `🎫 Daftar Tiket` | `🔍 Cari Lainnya`

---

### 4. `detail_event`

Deteksi saat user ingin tahu lebih lanjut tentang event tertentu.

> **Catatan:** Intent ini memiliki **prioritas lebih tinggi** dari `cari_event` karena pola-polanya overlap. Rule `detail_event` diperiksa lebih dulu.

**Pola regex:**
```
\b(detail|tentang)\b.*\b(event|acara|konferensi|seminar)\b
\b(info|informasi)\b.*\b(acara|konferensi|seminar|workshop)\b
\b(tiket|harga|lokasi)\b.*\b(event|acara)\b
\b(berapa\s+harga|harga\s+tiket)\b
```

**Contoh kalimat:**
- "Detail event Tech Conference 2026"
- "Info tentang seminar AI"
- "Berapa harga tiket workshop Python?"
- "Lokasi event besok di mana?"
- "Informasi acara weekend ini"

**Entity yang diekstrak:**
- `event_name` — nama event spesifik
- Jika tidak ada nama, chatbot menggunakan event terakhir dari **context**

**Respons:** Kartu detail event berisi judul, deskripsi, tanggal, lokasi, organizer, dan daftar tiket tersedia.

**Quick replies:** `🎫 Daftar Tiket` | `🔍 Cari Event Lain` | `📍 Lihat Lokasi`

---

### 5. `daftar_tiket`

Deteksi saat user ingin memesan atau mendaftar tiket event.

> **Catatan:** Intent ini memiliki **prioritas tertinggi** (diperiksa sebelum `cari_event` dan `detail_event`) karena kata "daftar event" bisa ambigu.

**Pola regex:**
```
\b(pesan|booking|beli|ambil)\b.*\b(tiket|ticket)\b
\b(daftar|pesan|booking|beli)\b.*\b(tiket|ticket)\b
\b(pesan|booking|beli)\b.*\b(event|acara)\b
\b(mau\s+ikut|ikut|join)\b.*\b(event|acara)\b
\bdaftar\s+event\b
```

**Contoh kalimat:**
- "Pesan tiket Tech Conference"
- "Booking tiket konser"
- "Mau ikut event AI summit"
- "Daftar event workshop Python"
- "Beli tiket 2 orang"
- "Join seminar besok"

**Perilaku:**
- Jika user **belum login** → balas minta login dulu
- Jika user **sudah login** → arahkan ke halaman booking (fitur dalam pengembangan)

**Quick replies (belum login):** `🔐 Login` | `🔍 Cari Event`

---

### 6. `lihat_jadwal`

Deteksi saat user ingin melihat event yang sudah didaftarkan.

**Pola regex:**
```
\b(jadwal|schedule|kalender|event\s+saya|tiket\s+saya)\b
\b(event|acara)\b.*\b(saya|aku|gue)\b
\b(sudah\s+daftar|terdaftar)\b
```

**Contoh kalimat:**
- "Jadwal saya"
- "Event saya"
- "Tiket saya"
- "Lihat schedule"
- "Sudah daftar event apa saja?"
- "Kalender acara saya"

**Perilaku:**
- Jika belum login → minta login
- Jika sudah login → tampilkan daftar registrasi dengan status (confirmed ✅, pending ⏳, attended 🎉)

**Quick replies:** `🎫 Daftar Lagi` | `👤 Profil Saya`

---

### 7. `profil`

Deteksi saat user ingin melihat data akun mereka.

**Pola regex:**
```
\b(profil|profile|akun|account|data\s+diri)\b
\b(nama\s+saya|email\s+saya|data\s+saya)\b
```

**Contoh kalimat:**
- "Profil saya"
- "Lihat akun"
- "Data diri saya"
- "Email saya apa?"
- "Account saya"

**Perilaku:**
- Jika belum login → minta login
- Jika sudah login → tampilkan nama, email, role, dan status akun

**Quick replies:** `🎫 Tiket Saya` | `📅 Jadwal Saya` | `⚙️ Pengaturan`

---

### 8. `keluar`

Deteksi saat user mengakhiri percakapan.

**Pola regex:**
```
\b(keluar|dadah|bye|sampai\s+jumpa|quit|exit|terima\s+kasih)\b
```

**Contoh kalimat:**
- "Bye"
- "Terima kasih"
- "Dadah"
- "Sampai jumpa"
- "Exit"
- "Makasih ya"

**Respons:**
> Terima kasih telah menggunakan EventBot! 👋
>
> Sampai jumpa di event-event menarik berikutnya.
> Jika butuh bantuan, saya selalu di sini!

**Quick replies:** `👋 Halo Lagi` | `🔍 Cari Event`

---

### 9. `tidak_dikenal` (Fallback)

Digunakan saat tidak ada intent yang cocok.

**Kondisi:** Semua pola regex gagal mencocokkan input.

**Perilaku:** Chatbot mencoba mencari jawaban di **Knowledge Base** (tabel `knowledge_base` di database). Jika ada hasil yang relevan, jawaban dari KB ditampilkan. Jika tidak ada, fallback message ditampilkan.

**Respons default:**
> Maaf, saya tidak mengerti. Coba ketik 'bantuan' untuk melihat fitur yang tersedia.

**Quick replies:** `❓ Bantuan` | `🔍 Cari Event` | `👋 Sapa EventBot`

---

## Entity Extraction

Entity adalah informasi spesifik yang diekstrak dari kalimat user untuk mempersempit pencarian.

### `location`

Lokasi event yang disebutkan user.

| Pola | Contoh |
|------|--------|
| `di [Kota]` | "di Jakarta", "di Bandung" |
| Nama kota langsung | "Jakarta", "Bali", "Yogyakarta" |
| Mode virtual | "online", "zoom", "virtual", "hybrid" |

Kota yang dikenali: Jakarta, Bandung, Surabaya, Yogyakarta, Bali, Medan, Makassar, Semarang, Malang, Depok, Tangerang, Bekasi.

---

### `date`

Waktu atau periode event.

| Pola | Contoh |
|------|--------|
| Relatif | "besok", "lusa", "minggu depan", "bulan depan" |
| Tanggal | "tanggal 15", "15 Juli" |
| Nama bulan | "Agustus", "Desember" |
| Tahun | "2026" |

---

### `price`

Preferensi harga.

| Pola | Contoh |
|------|--------|
| Batas atas | "di bawah 100 ribu", "di bawah 500k" |
| Gratis | "gratis", "free" |
| Premium | "premium", "VIP", "mahal" |

---

### `category`

Kategori atau bidang event.

| Nilai | Kata kunci yang dikenali |
|-------|--------------------------|
| Teknologi | teknologi, technology, tech, IT, digital |
| Bisnis | bisnis, business, startup, entrepreneur |
| Edukasi | edukasi, education, workshop, seminar, kursus |
| Hiburan | hiburan, entertainment, konser, musik |
| Sosial | sosial, komunitas, community |
| Kesehatan | kesehatan, health, wellness, yoga |
| Seni | seni, art, budaya, culture |

---

### `event_name`

Nama event spesifik yang disebutkan user.

Diekstrak dengan pola:
```
(?:event|acara|konferensi|workshop|seminar)\s+([A-Za-z\s]+?)(?:\s+(?:di|tanggal|pada|\d)|$)
```

Contoh: dari "detail event Tech Conference 2026" → `event_name = "Tech Conference"`

---

### `query`

Kata kunci bebas setelah menghapus stopwords umum. Digunakan sebagai fallback pencarian jika entity spesifik tidak ditemukan.

---

## Context Management

Chatbot menyimpan **context percakapan** per sesi (in-memory, bisa diganti Redis untuk production).

| Key context | Isi | Dipakai oleh |
|-------------|-----|--------------|
| `last_intent` | Intent terakhir user | Debugging, analitik |
| `last_entities` | Entity terakhir yang diekstrak | Referensi untuk turn berikutnya |
| `last_event_id` | ID event terakhir yang dibahas | `detail_event` (tanpa nama eksplisit) |
| `interaction_count` | Jumlah turn percakapan | Analitik sesi |

**Contoh penggunaan context:**

```
User: "Cari event AI di Jakarta"
Bot: [tampilkan 3 event AI]

User: "Detail yang pertama"
Bot: [gunakan last_event_id dari context → tampilkan detail event #1]
```

---

## Quick Replies

Quick replies adalah tombol pilihan cepat yang muncul setelah setiap respons bot. Tujuannya membantu user melanjutkan percakapan tanpa mengetik.

| Intent pemicu | Quick replies |
|---------------|---------------|
| sapaan | Cari Event, Lihat Event, Bantuan |
| tanya_bantuan | Cari Event di Jakarta, Event Teknologi, Tiket Saya |
| cari_event (ada hasil) | Lihat Detail, Daftar Tiket, Cari Lainnya |
| cari_event (kosong) | Cari Lagi, Bantuan |
| detail_event | Daftar Tiket, Cari Event Lain, Lihat Lokasi |
| daftar_tiket (belum login) | Login, Cari Event |
| lihat_jadwal | Daftar Lagi, Profil Saya |
| profil | Tiket Saya, Jadwal Saya, Pengaturan |
| keluar | Halo Lagi, Cari Event |
| tidak_dikenal | Bantuan, Cari Event, Sapa EventBot |

---

## Prioritas Matching

Intent diperiksa **secara berurutan** dari atas ke bawah. Urutan ini penting untuk menghindari ambiguitas:

```
1. sapaan
2. tanya_bantuan
3. daftar_tiket      ← sebelum cari_event (kata "daftar event" ambigu)
4. detail_event      ← sebelum cari_event (kata "info acara X" ambigu)
5. cari_event
6. lihat_jadwal
7. profil
8. keluar
9. tidak_dikenal     ← fallback
```

Intent pertama yang cocok langsung digunakan; sisanya tidak diperiksa.
