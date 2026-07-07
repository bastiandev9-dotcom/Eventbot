# EventBot API Documentation

Base URL: `http://localhost:8000/api/v1`

Semua response menggunakan format JSON. Endpoint yang membutuhkan autentikasi harus menyertakan header:

```
Authorization: Bearer <access_token>
```

---

## Daftar Isi

- [Auth](#auth)
- [Events](#events)
- [Tickets](#tickets)
- [Registrations](#registrations)
- [Chatbot](#chatbot)
- [Admin](#admin)
- [Knowledge Base](#knowledge-base)
- [WebSocket](#websocket)
- [Format Response](#format-response)
- [Kode Error](#kode-error)

---

## Auth

### POST `/auth/register`

Daftarkan akun baru.

**Request Body**

```json
{
  "name": "Budi Santoso",
  "email": "budi@email.com",
  "password": "secret123",
  "role": "participant",
  "phone": "08123456789",
  "bio": "Suka ikut event teknologi"
}
```

| Field    | Tipe   | Wajib | Keterangan                   |
|----------|--------|-------|------------------------------|
| name     | string | ✓     | Nama lengkap, 2–100 karakter |
| email    | string | ✓     | Email unik                   |
| password | string | ✓     | Minimal 6 karakter           |
| role     | string |       | `participant` (default)      |
| phone    | string |       | Nomor telepon                |
| bio      | string |       | Deskripsi singkat            |

> **Catatan:** Role `organizer` sudah tidak tersedia. Registrasi publik hanya menghasilkan role `participant`. Role `admin` hanya bisa di-set langsung di database.

**Response `201`**

```json
{
  "success": true,
  "message": "Akun berhasil dibuat",
  "user": { "id": "uuid", "name": "Budi Santoso", "email": "budi@email.com", "role": "participant" }
}
```

---

### POST `/auth/login`

Login dan dapatkan JWT access token.

**Request Body**

```json
{
  "email": "budi@email.com",
  "password": "secret123"
}
```

**Response `200`**

```json
{
  "success": true,
  "access_token": "eyJhbGci...",
  "token_type": "bearer",
  "user": { "id": "uuid", "name": "Budi Santoso", "role": "participant" }
}
```

---

### GET `/auth/me`

Ambil profil user yang sedang login. **Butuh auth.**

**Response `200`**

```json
{
  "success": true,
  "user": {
    "id": "uuid",
    "name": "Budi Santoso",
    "email": "budi@email.com",
    "role": "participant",
    "phone": "08123456789",
    "bio": "...",
    "created_at": "2026-01-01T00:00:00"
  }
}
```

---

### PUT `/auth/change-password`

Ganti password. **Butuh auth.**

**Request Body**

```json
{
  "old_password": "secret123",
  "new_password": "newpass456"
}
```

**Response `200`**

```json
{ "success": true, "message": "Password berhasil diubah! 🔐" }
```

---

### POST `/auth/logout`

Logout (stateless — client harus hapus token lokal). **Butuh auth.**

**Response `200`**

```json
{ "success": true, "message": "Logout berhasil." }
```

---

## Events

### GET `/events/`

Daftar event dengan filter dan pagination.

- **Guest / Participant:** hanya event dengan `is_published = TRUE`
- **Admin:** semua event termasuk yang belum dipublish

**Query Parameters**

| Parameter  | Tipe   | Default | Keterangan                              |
|------------|--------|---------|-----------------------------------------|
| q          | string | —       | Keyword pencarian judul / deskripsi     |
| location   | string | —       | Filter lokasi (ILIKE)                   |
| category   | string | —       | Slug kategori                           |
| status     | string | —       | `upcoming`, `ongoing`, `completed`, `cancelled` — jika kosong tampilkan semua |
| start_date | string | —       | Format `YYYY-MM-DD`                     |
| end_date   | string | —       | Format `YYYY-MM-DD`                     |
| min_price  | float  | —       | Harga tiket minimum                     |
| max_price  | float  | —       | Harga tiket maksimum                    |
| page       | int    | `1`     | Halaman                                 |
| page_size  | int    | `20`    | Jumlah item per halaman (maks 100)      |

**Response `200`**

```json
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "title": "Tech Conference 2026",
      "location": "Jakarta",
      "start_date": "2026-08-15",
      "status": "upcoming",
      "is_published": true,
      "min_price": 150000,
      "total_quota": 450,
      "total_sold": 120,
      "organizer_name": "Admin EventBot"
    }
  ],
  "page": 1,
  "page_size": 20,
  "count": 11,
  "total_pages": 1
}
```

> `total_quota` = total kuota semua tiket aktif event tersebut (`SUM(tickets.quantity)`)
> `total_sold` = total tiket terjual (`SUM(tickets.sold)`)

---

### GET `/events/trending`

Event paling banyak dilihat.

**Query Parameters:** `limit` (int, default 5, maks 20)

---

### GET `/events/upcoming`

Event yang akan segera berlangsung.

**Query Parameters:** `limit` (int, default 10, maks 50)

---

### GET `/events/{event_id}`

Detail lengkap sebuah event beserta daftar tiketnya.

**Response `200`**

```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "title": "Tech Conference 2026",
    "description": "...",
    "short_description": "...",
    "start_date": "2026-08-15",
    "end_date": "2026-08-16",
    "start_time": "08:00",
    "end_time": "18:00",
    "location": "Jakarta Convention Center",
    "capacity": 500,
    "status": "upcoming",
    "is_published": true,
    "image_url": "https://...",
    "organizer_name": "Admin EventBot",
    "registered_count": 120,
    "tickets": [
      {
        "id": "uuid",
        "name": "Regular",
        "price": 500000,
        "quota": 300,
        "sold_count": 100,
        "remaining": 200,
        "status": "available"
      }
    ]
  }
}
```

---

### GET `/events/{event_id}/recommendations`

Rekomendasi event serupa.

**Query Parameters:** `limit` (int, default 3, maks 10)

---

### POST `/events/`

Buat event baru. **Butuh auth** — role `admin`.

**Request Body**

```json
{
  "title": "Tech Conference 2026",
  "description": "Konferensi teknologi tahunan terbesar di Indonesia.",
  "short_description": "Event teknologi terbesar 2026",
  "start_date": "2026-08-15",
  "end_date": "2026-08-16",
  "start_time": "08:00",
  "end_time": "18:00",
  "location": "Jakarta Convention Center",
  "location_map_url": "https://maps.google.com/...",
  "image_url": "https://...",
  "capacity": 500,
  "status": "upcoming",
  "is_published": false
}
```

| Field             | Tipe    | Wajib | Keterangan                              |
|-------------------|---------|-------|-----------------------------------------|
| title             | string  | ✓     | 5–255 karakter                          |
| description       | string  | ✓     | Deskripsi lengkap                       |
| short_description | string  | ✓     | Maks 500 karakter                       |
| start_date        | string  | ✓     | Format `YYYY-MM-DD`                     |
| end_date          | string  | ✓     | Format `YYYY-MM-DD`                     |
| location          | string  | ✓     | Nama venue                              |
| capacity          | int     |       | 0 = tak terbatas (default: 0)           |
| status            | string  |       | Default `upcoming`                      |
| is_published      | boolean |       | Default `false`                         |

**Response `201`**

```json
{ "success": true, "data": { "id": "uuid", "title": "...", "slug": "..." } }
```

---

### PUT `/events/{event_id}`

Update data event. **Butuh auth** — role `admin`. Semua field opsional.

**Response `200`**

```json
{ "success": true, "data": { "id": "uuid", "title": "...", "updated_at": "..." } }
```

---

### DELETE `/events/{event_id}`

Soft-delete event beserta semua tiketnya (atomic). **Butuh auth** — role `admin`.

**Response `200`**

```json
{ "success": true, "message": "Event berhasil dihapus" }
```

> Soft delete: record tidak benar-benar dihapus, hanya `deleted_at` diisi. Data tiket terkait juga di-soft-delete dalam transaksi yang sama.

---

### GET `/events/organizer/my-events`

List event yang dibuat oleh admin yang sedang login. **Butuh auth.**

---

## Tickets

### GET `/tickets/`

Daftar tiket. Query param opsional: `event_id`.

**Response `200`**

```json
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "event_id": "uuid",
      "name": "Regular",
      "description": "Tiket reguler",
      "price": 500000,
      "quantity": 300,
      "sold": 100,
      "remaining": 200,
      "status": "available",
      "max_per_order": 5
    }
  ]
}
```

---

### GET `/events/{event_id}/tickets`

Daftar tiket milik sebuah event.

---

### GET `/tickets/{ticket_id}`

Detail tiket.

---

### POST `/tickets/`

Buat tiket baru untuk event. **Butuh auth** — role `admin`.

**Request Body**

```json
{
  "event_id": "uuid",
  "name": "VIP",
  "description": "Akses semua sesi + makan siang",
  "price": 850000,
  "quantity": 50,
  "max_per_order": 2,
  "benefits": ["Priority Seat", "Lunch", "E-Certificate"],
  "sale_starts_at": "2026-07-01T00:00:00",
  "sale_ends_at": "2026-08-14T23:59:59"
}
```

---

### PUT `/tickets/{ticket_id}`

Update tiket. **Butuh auth** — role `admin`.

---

### DELETE `/tickets/{ticket_id}`

Soft-delete tiket. **Butuh auth** — role `admin`.

---

## Registrations

### GET `/registrations/my`

Daftar registrasi tiket milik user yang login. **Butuh auth.**

**Response `200`**

```json
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "event_id": "uuid",
      "ticket_id": "uuid",
      "quantity": 2,
      "total_price": 1000000,
      "status": "confirmed",
      "payment_method": "transfer_bank",
      "created_at": "2026-07-01T10:00:00"
    }
  ]
}
```

---

### GET `/registrations/`

Daftar semua registrasi. **Butuh auth** — role `admin`. Query param opsional: `event_id`, `status`.

---

### POST `/registrations/book`

Pesan tiket event. **Butuh auth.**

**Request Body**

```json
{
  "ticket_id": "uuid",
  "quantity": 2,
  "payment_method": "transfer_bank",
  "event_id": "uuid"
}
```

| Field          | Tipe   | Wajib | Keterangan                                      |
|----------------|--------|-------|-------------------------------------------------|
| ticket_id      | string | ✓     | UUID tiket yang dibeli                          |
| quantity       | int    |       | Jumlah tiket, default 1, maks `max_per_order`   |
| payment_method | string |       | `transfer_bank`, `e_wallet`, atau kosong (gratis)|
| event_id       | string |       | UUID event (opsional, untuk validasi tambahan)  |

**Response `200`**

```json
{
  "success": true,
  "registration_id": "uuid",
  "total_price": 1000000,
  "message": "Tiket berhasil dipesan! 🎫"
}
```

---

### POST `/registrations/{registration_id}/confirm-payment`

Konfirmasi pembayaran registrasi. **Butuh auth** — role `admin`.

---

### POST `/registrations/{registration_id}/cancel`

Batalkan registrasi. **Butuh auth** — user sendiri atau admin.

---

## Chatbot

### POST `/chatbot/message`

Kirim pesan ke chatbot dan terima respons NLP.

**Request Body**

```json
{
  "message": "Ada event teknologi di Jakarta bulan Agustus?",
  "session_token": "tok_abc123"
}
```

| Field         | Tipe   | Wajib | Keterangan                                    |
|---------------|--------|-------|-----------------------------------------------|
| message       | string | ✓     | Teks pesan, 1–1000 karakter                   |
| session_token | string |       | Token sesi sebelumnya untuk lanjut percakapan |

**Response `200`**

```json
{
  "success": true,
  "data": {
    "response": "Saya menemukan 3 event teknologi di Jakarta pada Agustus 2026:\n1. Tech Conference...",
    "intent": "cari_event",
    "entities": {
      "location": ["Jakarta"],
      "date": ["Agustus"],
      "category": ["teknologi"]
    },
    "session_token": "tok_abc123",
    "quick_replies": ["🔍 Cari Event Lain", "🎫 Pesan Tiket", "❓ Bantuan"]
  }
}
```

---

### GET `/chatbot/history`

Ambil history percakapan berdasarkan session token.

**Query Parameters:** `session_token` (wajib)

**Response `200`**

```json
{
  "success": true,
  "data": [
    { "role": "user", "content": "Halo", "created_at": "2026-07-05T04:00:00" },
    { "role": "assistant", "content": "Halo! Ada yang bisa saya bantu?", "created_at": "2026-07-05T04:00:01" }
  ]
}
```

---

### GET `/chatbot/intents`

Daftar intent yang didukung chatbot beserta contoh kalimat.

---

## Admin

Semua endpoint di bawah membutuhkan **auth** dengan role `admin`.

### GET `/admin/stats`

Statistik ringkasan dashboard admin.

**Response `200`**

```json
{
  "success": true,
  "data": {
    "total_users": 11,
    "total_events": 11,
    "total_tickets": 97,
    "total_registrations": 16,
    "revenue": 5000000
  }
}
```

### GET `/admin/users`

Daftar semua user. Query param: `role`, `status`, `q`.

### PUT `/admin/users/{user_id}`

Update data user (termasuk role dan status).

### DELETE `/admin/users/{user_id}`

Soft-delete user.

### GET `/admin/registrations`

Semua registrasi dengan detail lengkap.

---

## Knowledge Base

### GET `/knowledge-base/`

Daftar semua entri knowledge base. **Butuh auth** — role `admin`.

### POST `/knowledge-base/`

Tambah entri baru. **Butuh auth** — role `admin`.

**Request Body**

```json
{
  "category": "payment",
  "question": "Bagaimana cara bayar?",
  "answer": "Tersedia transfer bank, e-wallet, dan virtual account.",
  "keywords": ["bayar", "pembayaran", "transfer"],
  "priority": 5
}
```

### PUT `/knowledge-base/{kb_id}`

Update entri. **Butuh auth** — role `admin`.

### DELETE `/knowledge-base/{kb_id}`

Hapus entri. **Butuh auth** — role `admin`.

---

## WebSocket

### `WS /ws/chat/{session_token}`

Koneksi WebSocket untuk chat real-time.

**Kirim pesan**

```json
{ "message": "Ada event musik minggu ini?" }
```

**Terima respons**

```json
{
  "type": "message",
  "data": {
    "response": "Berikut event musik minggu ini...",
    "intent": "cari_event",
    "quick_replies": ["🎵 Lihat Semua", "🎫 Pesan Tiket"]
  }
}
```

---

## Format Response

Semua endpoint mengembalikan envelope yang konsisten:

**Sukses**

```json
{
  "success": true,
  "data": { ... },
  "message": "Opsional"
}
```

**Gagal**

```json
{
  "detail": "Pesan error yang menjelaskan penyebab kegagalan"
}
```

---

## Kode Error

| Kode | Keterangan                                   |
|------|----------------------------------------------|
| 400  | Bad Request — input tidak valid              |
| 401  | Unauthorized — token tidak ada / kedaluwarsa |
| 403  | Forbidden — role tidak diizinkan             |
| 404  | Not Found — resource tidak ditemukan         |
| 422  | Unprocessable Entity — validasi Pydantic     |
| 500  | Internal Server Error                        |
| 503  | Service Unavailable — database tidak terhubung |
