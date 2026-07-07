# Arsitektur EventBot

EventBot adalah aplikasi web manajemen event berbasis chatbot NLP yang dibangun dengan arsitektur **monorepo two-tier**: backend REST API (FastAPI) dan frontend dashboard (Streamlit), keduanya terhubung ke satu database PostgreSQL.

---

## Daftar Isi

- [Gambaran Umum](#gambaran-umum)
- [Struktur Direktori](#struktur-direktori)
- [Backend](#backend)
- [Frontend](#frontend)
- [Database](#database)
- [NLP Pipeline](#nlp-pipeline)
- [Alur Data](#alur-data)
- [Keputusan Desain](#keputusan-desain)

---

## Gambaran Umum

```
┌─────────────────────────────────────────────────────┐
│                      Browser                        │
│                                                     │
│   ┌──────────────────────────────────────────────┐  │
│   │         Streamlit Frontend (:8501)           │  │
│   │  views/ · components/ · hooks/ · utils/     │  │
│   └──────────────────┬───────────────────────────┘  │
└─────────────────────-│─────────────────────────────-┘
                       │ HTTP / WebSocket
                       ▼
┌──────────────────────────────────────────────────────┐
│           FastAPI Backend (:8000)                    │
│                                                      │
│  /api/v1/auth      /api/v1/events                   │
│  /api/v1/tickets   /api/v1/registrations            │
│  /api/v1/chatbot   /api/v1/admin                    │
│  /api/v1/knowledge_base   /ws/chat/{token}          │
│                                                      │
│  ┌────────────┐  ┌──────────┐  ┌─────────────────┐  │
│  │  Services  │  │   NLP    │  │  Repositories   │  │
│  │            │  │ Pipeline │  │                 │  │
│  └─────┬──────┘  └────┬─────┘  └────────┬────────┘  │
└────────│──────────────│─────────────────│────────────┘
         └──────────────┴─────────────────┘
                        │
                        ▼
┌──────────────────────────────────────────────────────┐
│           PostgreSQL Database (:5432)                │
│  users · events · tickets · registrations           │
│  categories · chat_sessions · chat_messages         │
│  knowledge_base · system_settings                   │
└──────────────────────────────────────────────────────┘
```

---

## Struktur Direktori

```
eventbot/
├── backend/                  # FastAPI REST API
│   ├── main.py               # Entry point app
│   ├── .env                  # Konfigurasi environment (tidak di-commit)
│   ├── .env.example          # Template konfigurasi
│   ├── requirements.txt      # Dependensi Python backend
│   ├── api/
│   │   ├── v1/               # Endpoint router v1
│   │   │   ├── auth.py
│   │   │   ├── events.py
│   │   │   ├── tickets.py
│   │   │   ├── registrations.py
│   │   │   ├── chatbot.py
│   │   │   ├── admin.py
│   │   │   └── knowledge_base.py
│   │   ├── websocket.py      # WebSocket chat real-time
│   │   └── deps.py           # Dependency injection (auth)
│   ├── services/             # Business logic layer
│   │   ├── auth_service.py
│   │   ├── event_service.py
│   │   ├── ticket_service.py
│   │   ├── registration_service.py
│   │   ├── chatbot_service.py
│   │   ├── notification_service.py
│   │   └── recommendation_service.py
│   ├── repositories/         # Data access layer
│   │   ├── base_repository.py
│   │   ├── user_repository.py
│   │   ├── event_repository.py
│   │   ├── ticket_repository.py
│   │   └── registration_repository.py
│   ├── models/               # DB model (raw SQL via psycopg2)
│   │   ├── user.py
│   │   ├── event.py
│   │   ├── ticket.py
│   │   ├── registration.py
│   │   ├── category.py
│   │   ├── chat_history.py
│   │   ├── knowledge_base.py
│   │   └── system_settings.py
│   ├── nlp/                  # NLP engine
│   │   ├── regex_rules.py         # Intent detection & entity extraction
│   │   ├── response_templates.py  # Response builder
│   │   └── context_manager.py     # Conversation state
│   ├── config/
│   │   ├── settings.py       # Environment variables
│   │   ├── database.py       # Connection pool (psycopg2)
│   │   └── security.py       # JWT utilities
│   ├── utils/
│   │   ├── validators.py
│   │   ├── formatters.py
│   │   └── exceptions.py
│   ├── uploads/
│   │   └── events/           # File gambar event yang diupload
│   └── tests/
│       ├── test_auth.py
│       ├── test_events.py
│       ├── test_chatbot.py
│       ├── test_backend.py
│       └── conftest.py
│
├── frontend/                 # Streamlit dashboard
│   ├── app.py                # Entry point + routing SPA
│   ├── requirements.txt      # Dependensi Python frontend
│   ├── views/                # Halaman-halaman aplikasi
│   │   ├── Landing.py
│   │   ├── Login_register.py
│   │   ├── Event_Explorer.py
│   │   ├── Chatbot.py
│   │   ├── Profil_saya.py
│   │   ├── Manajemen_Event.py
│   │   ├── Manajemen_Ticket.py
│   │   ├── Manajemen_User.py
│   │   ├── Dashboard_admin.py
│   │   ├── Knowledge_Base.py
│   │   ├── Pengaturan.py
│   │   └── About.py
│   ├── components/           # Komponen UI yang dapat dipakai ulang
│   │   ├── navbar.py
│   │   ├── sidebar.py
│   │   ├── auth_form.py
│   │   ├── hero_section.py
│   │   ├── event_card.py
│   │   ├── ticket_card.py
│   │   ├── buy_ticket_modal.py
│   │   ├── chat_bubble.py
│   │   ├── quick_reply.py
│   │   ├── filter_panel.py
│   │   ├── data_table.py
│   │   ├── metric_card.py
│   │   ├── toast.py
│   │   └── footer.py
│   ├── hooks/                # State & API logic (React-style hooks)
│   │   ├── use_auth.py
│   │   ├── use_chat.py
│   │   ├── use_events.py
│   │   └── use_theme.py
│   ├── utils/
│   │   ├── api_client.py       # HTTP client ke backend
│   │   ├── session_manager.py  # st.session_state wrapper
│   │   ├── state_persistence.py
│   │   └── formatters.py
│   ├── styles/
│   │   ├── theme_manager.py
│   │   ├── global.css
│   │   ├── dark_theme.css
│   │   ├── glassmorphism.css
│   │   └── animation.css
│   └── assets/               # (kosong — placeholder untuk asset statis)
│
├── database/
│   ├── schema.sql            # DDL tabel + tipe enum + index
│   ├── functions.sql         # PostgreSQL stored functions
│   └── triggers.sql          # Auto-update trigger (slug, updated_at)
│
└── docs/
    ├── api-docs.md
    ├── chatbot-intents.md
    ├── architecture.md       # ← dokumen ini
    └── deployment.md
```

---

## Backend

### Layer Architecture

Backend mengikuti pola **3-layer architecture**:

```
API Layer (FastAPI Router)
      ↓ validasi input (Pydantic)
Service Layer (business logic)
      ↓ query builder
Model / Repository Layer (SQL via psycopg2)
      ↓
PostgreSQL
```

**API Layer** (`backend/api/v1/`) hanya bertanggung jawab atas validasi request, pemanggilan service, dan formatting response HTTP. Tidak ada logic bisnis di sini.

**Service Layer** (`backend/services/`) berisi semua logic bisnis: validasi aturan domain, orkestrasi antar model, dan pemanggilan NLP pipeline untuk chatbot.

**Model Layer** (`backend/models/`) menjalankan query SQL langsung menggunakan psycopg2 (tanpa ORM). Setiap model berisi method CRUD spesifik untuk tabelnya masing-masing.

### Autentikasi

JWT (HS256) stateless. Token dikirim via `Authorization: Bearer <token>` header. Token berisi `user_id`, `role`, dan `exp`. Tidak ada server-side session storage.

```
Login → AuthService.login() → bcrypt verify → generate JWT → return token
Request → deps.require_auth(token) → decode JWT → return user dict
```

Role yang tersedia: `admin`, `participant`. (Role `organizer` dihapus — semua fungsi organizer dijalankan oleh `admin`.)

### Soft Delete

Tabel `events` dan `tickets` menggunakan soft delete via kolom `deleted_at`. Saat event dihapus, proses berjalan secara **atomic dalam satu transaksi**:

```
DELETE event → UPDATE events SET deleted_at = NOW()
             → UPDATE tickets SET deleted_at = NOW() WHERE event_id = ...
             → COMMIT (atau ROLLBACK jika ada error)
```

### Database Connection

Menggunakan `psycopg2.pool.ThreadedConnectionPool` (singleton) dengan min 1 dan maks 10 koneksi. Setiap request mengambil koneksi dari pool dan mengembalikannya setelah selesai via context manager `get_db_connection()`.

### Kapasitas Event

Kapasitas yang ditampilkan di frontend dihitung dari **total kuota tiket aktif** (`SUM(tickets.quantity)`), bukan dari field `capacity` di tabel events. Field `capacity` tetap ada sebagai referensi admin saat membuat event, tapi tampilan publik menggunakan data tiket yang lebih akurat.

```sql
COALESCE(SUM(t.quantity), 0) AS total_quota
COALESCE(SUM(t.sold), 0)     AS total_sold
```

### WebSocket

`/ws/chat/{session_token}` menggunakan FastAPI WebSocket untuk chat real-time tanpa polling. Pesan diteruskan ke `ChatbotService.process_message()` yang sama dengan endpoint REST.

---

## Frontend

### Pattern

Frontend Streamlit mengadopsi pola **hooks** terinspirasi dari React:

- **Views** (`views/`) — mengatur layout dan memanggil komponen + hooks; tidak berisi logic bisnis
- **Components** (`components/`) — elemen UI yang dapat dipakai ulang
- **Hooks** (`hooks/`) — semua state management dan pemanggilan API dikapsulasi di sini
- **Utils** (`utils/`) — helper murni tanpa side effect (formatter, HTTP client, session)

```
view.py
  └── calls hooks/use_events.py → api_client → Backend API
  └── renders components/event_card.py
  └── manages state via SessionManager (st.session_state)
```

### Routing

Streamlit SPA (Single Page Application) dengan routing berbasis `st.session_state["current_page"]`. Navigasi dikontrol secara programatik via `st.session_state` dan `st.rerun()`. Tidak menggunakan fitur multipage bawaan Streamlit.

Proteksi halaman:
- `_PROTECTED_PAGES` — redirect ke login jika belum login
- `_ADMIN_ONLY_PAGES` — tampilkan "Akses Ditolak" jika bukan admin

### Session State

Semua state autentikasi dikelola oleh `SessionManager` (wrapper type-safe di atas `st.session_state`):

| Key | Isi |
|-----|-----|
| `is_logged_in` | bool — status login |
| `user` | dict — data user aktif |
| `access_token` | string — JWT token |
| `user_role` | string — `guest`, `participant`, atau `admin` |
| `theme` | string — selalu `dark` |
| `chat_history` | list — history percakapan lokal |
| `chat_session_token` | string — token sesi chatbot |
| `current_page` | string — halaman aktif |

### Cache Event

Hook `use_events` menerapkan caching sederhana via `st.session_state` dengan TTL 10 detik untuk mengurangi API call berulang. Cache di-invalidate otomatis setelah operasi create, update, atau delete event.

Fungsi `_bust_event_cache()` di `Manajemen_Event.py` menghapus cache secara selektif — hanya key dengan prefix `events_` dan `event_detail_`, **tidak menyentuh** key autentikasi.

### Tema

Dark mode (fixed). CSS disuntikkan ke halaman via `st.markdown("<style>...</style>")` oleh `ThemeManager`. File CSS tersedia di `styles/`.

---

## Database

### Tabel Utama

| Tabel | Keterangan |
|-------|------------|
| `users` | Pengguna (admin, participant) |
| `categories` | Kategori event (teknologi, bisnis, dll) |
| `events` | Data event utama |
| `tickets` | Jenis tiket per event |
| `registrations` | Pemesanan tiket oleh user |
| `event_categories` | Relasi many-to-many event ↔ kategori |
| `chat_sessions` | Sesi percakapan chatbot |
| `chat_messages` | Pesan individual dalam sesi chat |
| `knowledge_base` | Pasangan tanya-jawab untuk fallback chatbot |
| `system_settings` | Konfigurasi aplikasi (greeting, dll) |

### Enum Types (PostgreSQL)

```sql
user_role:           admin | participant
user_status:         active | inactive | suspended
event_status:        upcoming | ongoing | completed | cancelled
ticket_status:       available | sold_out | reserved | unavailable
registration_status: pending | confirmed | cancelled | attended
```

### Relasi

```
users (1) ──── (N) events           [organizer_id]
events (1) ──── (N) tickets         [event_id]
events (N) ──── (N) categories      [event_categories]
users  (1) ──── (N) registrations   [user_id]
tickets (1) ──── (N) registrations  [ticket_id]
users  (1) ──── (N) chat_sessions   [user_id, nullable]
chat_sessions (1) ──── (N) chat_messages [session_id]
```

### Index

Index utama sudah didefinisikan di `database/schema.sql`:

- `idx_events_organizer`, `idx_events_status`, `idx_events_dates`, `idx_events_slug`
- `idx_events_search` — GIN index untuk full-text search (Indonesian)
- `idx_tickets_event`, `idx_tickets_status`
- `idx_registrations_user`, `idx_registrations_event`

---

## NLP Pipeline

```
Input teks user
       │
       ▼
  Preprocessing
  (lowercase, strip)
       │
       ▼
  match_intent(text)          ← regex_rules.INTENT_RULES
  (return intent string)
       │
       ▼
  extract_entities(text)      ← regex_rules.ENTITY_PATTERNS
  (return entity dict)
       │
       ▼
  ContextManager.get_context(session_id)
  (ambil last_event_id, last_intent, dll)
       │
       ▼
  ChatbotService._build_response(intent, entities, context)
       │
       ├── cari_event    → EventModel.search(query, location, category)
       ├── detail_event  → EventModel.get_by_id() atau search by name
       ├── daftar_tiket  → cek auth → arahkan booking
       ├── lihat_jadwal  → RegistrationModel.get_by_user()
       ├── profil        → UserModel.get_by_id()
       ├── tidak_dikenal → KnowledgeBaseModel.search() → fallback
       └── lainnya       → ResponseBuilder template
       │
       ▼
  ResponseBuilder.xxx()
  (return response string + quick_replies)
       │
       ▼
  ChatMessageModel.create()      ← simpan ke DB
  ContextManager.update_context()
       │
       ▼
  Return { response, intent, entities, session_token, quick_replies }
```

---

## Alur Data

### Login

```
[Form Login] → use_auth.login() → POST /api/v1/auth/login
    → AuthService.login() → bcrypt.verify()
    → generate JWT → return token + user
    → SessionManager.login(user, token)
    → st.session_state.is_logged_in = True
```

### Cari Event

```
[Filter Panel] → use_events.fetch_events() → GET /api/v1/events/?q=...
    → EventService.search_events() → EventModel.search()
    → return list events (termasuk total_quota, total_sold per event)
    → render EventCard (kapasitas = total_quota tiket)
```

### Hapus Event

```
[Tombol Hapus] → konfirmasi dialog → use_events.delete_event(id)
    → DELETE /api/v1/events/{id}
    → EventModel.delete() → transaksi atomic:
         UPDATE events SET deleted_at = NOW()
         UPDATE tickets SET deleted_at = NOW()
         COMMIT
    → _bust_event_cache() → invalidate cache event
    → st.rerun() → tampilkan toast sukses
```

### Chat

```
[Chat Input] → use_chat.send_message() → POST /api/v1/chatbot/message
    → ChatbotService.process_message()
    → match_intent() + extract_entities()
    → _build_response() → DB query jika perlu
    → return response + quick_replies
    → SessionManager.add_chat_message() → render ChatBubble
```

---

## Keputusan Desain

**Mengapa psycopg2, bukan SQLAlchemy?**
Untuk transparansi penuh atas query SQL — cocok untuk konteks tugas akademik yang mengedepankan pemahaman database. Raw SQL juga lebih mudah dioptimalkan dan di-debug.

**Mengapa Streamlit, bukan React/Vue?**
Streamlit memungkinkan pembuatan antarmuka web interaktif dengan Python murni tanpa memerlukan JavaScript atau build tooling. Cocok untuk prototyping cepat dan project akademik.

**Mengapa rule-based NLP, bukan model ML?**
Sesuai konteks mata kuliah Teori Bahasa dan Otomata — chatbot berbasis regex dan finite automata adalah implementasi langsung dari konsep yang dipelajari. Tidak memerlukan dataset training dan berjalan tanpa GPU.

**Mengapa JWT stateless?**
Menyederhanakan deployment (tidak perlu Redis/session store). Cukup untuk skala project akademik.

**Mengapa hooks pattern di Streamlit?**
Memisahkan logic bisnis dari presentasi, membuat kode lebih mudah diuji dan dipahami, serta mengikuti prinsip single responsibility.

**Mengapa kapasitas dihitung dari tiket, bukan field `capacity`?**
Field `capacity` di tabel events adalah nilai yang diisi admin saat membuat event dan bisa tidak sinkron dengan jumlah tiket yang sebenarnya dibuat. Menghitung `SUM(tickets.quantity)` memastikan angka yang ditampilkan selalu akurat sesuai tiket aktif yang tersedia.

**Mengapa role `organizer` dihapus?**
Untuk menyederhanakan sistem role — semua operasi manajemen event (buat, edit, hapus) hanya dilakukan oleh `admin`. Ini mengurangi kompleksitas middleware auth dan logic bisnis.
