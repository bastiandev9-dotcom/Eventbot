-- ============================================================
-- EVENTBOT - SEED DATA
-- PostgreSQL Compatible
-- ============================================================

-- 1. CATEGORIES
-- ============================================================
INSERT INTO categories (name, slug, description, color, icon) VALUES
    ('Technology', 'technology', 'Event teknologi dan digital', '#3B82F6', 'fa-microchip'),
    ('Business', 'business', 'Event bisnis dan entrepreneurship', '#10B981', 'fa-briefcase'),
    ('Education', 'education', 'Workshop dan seminar edukasi', '#F59E0B', 'fa-graduation-cap'),
    ('Entertainment', 'entertainment', 'Konser dan hiburan', '#EC4899', 'fa-music'),
    ('Social', 'social', 'Event sosial dan komunitas', '#8B5CF6', 'fa-users'),
    ('Health', 'health', 'Event kesehatan dan wellness', '#EF4444', 'fa-heartbeat'),
    ('Art', 'art', 'Event seni dan budaya', '#F97316', 'fa-palette')
ON CONFLICT (slug) DO NOTHING;

-- 2. USERS (Admin & Organizer)
-- ============================================================
INSERT INTO users (name, email, password_hash, role, status, email_verified_at) 
VALUES (
    'Admin EventBot',
    'admin@eventbot.com',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYHmE5cPZ6K',
    'admin',
    'active',
    CURRENT_TIMESTAMP
)
ON CONFLICT (email) DO NOTHING;

INSERT INTO users (name, email, password_hash, role, status, phone, email_verified_at) 
VALUES (
    'Budi Organizer',
    'budi@eventbot.com',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYHmE5cPZ6K',
    'organizer',
    'active',
    '081234567890',
    CURRENT_TIMESTAMP
)
ON CONFLICT (email) DO NOTHING;

-- 3. EVENTS
-- ============================================================
INSERT INTO events (
    title, description, short_description, start_date, end_date,
    start_time, end_time, location, location_map_url, organizer_id,
    image_url, banner_url, capacity, status, is_published, published_at
) VALUES (
    'Tech Conference 2025',
    'Konferensi teknologi tahunan terbesar di Indonesia. Menghadirkan pembicara dari Google, Microsoft, dan startup lokal ternama.',
    'Konferensi teknologi tahunan dengan pembicara internasional',
    '2025-12-15', '2025-12-16', '08:00', '17:00',
    'Jakarta Convention Center', 'https://maps.google.com/?q=JCC',
    (SELECT id FROM users WHERE email = 'budi@eventbot.com'),
    'https://images.unsplash.com/photo-1540575467063-178a50c2df87',
    'https://images.unsplash.com/photo-1540575467063-178a50c2df87',
    500, 'upcoming', TRUE, CURRENT_TIMESTAMP
)
ON CONFLICT (slug) DO NOTHING;

INSERT INTO events (
    title, description, short_description, start_date, end_date,
    start_time, end_time, location, location_map_url, organizer_id,
    image_url, banner_url, capacity, status, is_published, published_at
) VALUES (
    'AI Workshop: Deep Learning Fundamentals',
    'Workshop hands-on Artificial Intelligence dan Deep Learning untuk pemula. Peserta akan belajar membuat model neural network dari nol.',
    'Workshop AI hands-on untuk pemula',
    '2025-12-20', '2025-12-20', '09:00', '16:00',
    'Bandung Institute of Technology', 'https://maps.google.com/?q=ITB',
    (SELECT id FROM users WHERE email = 'budi@eventbot.com'),
    'https://images.unsplash.com/photo-1485827404703-89b55fcc595e',
    'https://images.unsplash.com/photo-1485827404703-89b55fcc595e',
    100, 'upcoming', TRUE, CURRENT_TIMESTAMP
)
ON CONFLICT (slug) DO NOTHING;

INSERT INTO events (
    title, description, short_description, start_date, end_date,
    start_time, end_time, location, location_map_url, organizer_id,
    image_url, banner_url, capacity, status, is_published, published_at
) VALUES (
    'Startup Summit Indonesia 2026',
    'Pertemuan tahunan para founder, investor, dan enthusiast startup. Networking, pitching, dan workshop bisnis.',
    'Pertemuan founder dan investor startup',
    '2026-01-10', '2026-01-12', '08:00', '18:00',
    'Bali Nusa Dua Convention Center', 'https://maps.google.com/?q=NusaDua',
    (SELECT id FROM users WHERE email = 'budi@eventbot.com'),
    'https://images.unsplash.com/photo-1515187029135-18ee286d815b',
    'https://images.unsplash.com/photo-1515187029135-18ee286d815b',
    1000, 'upcoming', TRUE, CURRENT_TIMESTAMP
)
ON CONFLICT (slug) DO NOTHING;

INSERT INTO events (
    title, description, short_description, start_date, end_date,
    start_time, end_time, location, location_map_url, organizer_id,
    image_url, banner_url, capacity, status, is_published, published_at
) VALUES (
    'Digital Marketing Masterclass',
    'Pelajari strategi digital marketing terkini dari praktisi industri. SEO, SEM, Social Media, dan Content Marketing.',
    'Masterclass digital marketing lengkap',
    '2025-11-25', '2025-11-25', '10:00', '16:00',
    'Online via Zoom', NULL,
    (SELECT id FROM users WHERE email = 'budi@eventbot.com'),
    'https://images.unsplash.com/photo-1460925895917-afdab827c52f',
    'https://images.unsplash.com/photo-1460925895917-afdab827c52f',
    300, 'upcoming', TRUE, CURRENT_TIMESTAMP
)
ON CONFLICT (slug) DO NOTHING;

INSERT INTO events (
    title, description, short_description, start_date, end_date,
    start_time, end_time, location, location_map_url, organizer_id,
    image_url, banner_url, capacity, status, is_published, published_at
) VALUES (
    'Yoga & Wellness Retreat',
    'Habiskan akhir pekan dengan yoga, meditasi, dan aktivitas wellness di pegunungan Bandung.',
    'Retreat yoga dan wellness di alam',
    '2025-11-30', '2025-12-01', '07:00', '15:00',
    'Dusun Bambu, Bandung', 'https://maps.google.com/?q=DusunBambu',
    (SELECT id FROM users WHERE email = 'budi@eventbot.com'),
    'https://images.unsplash.com/photo-1544367567-0f2fcb009e0b',
    'https://images.unsplash.com/photo-1544367567-0f2fcb009e0b',
    50, 'upcoming', TRUE, CURRENT_TIMESTAMP
)
ON CONFLICT (slug) DO NOTHING;

-- 4. EVENT_CATEGORIES (Many-to-Many)
-- ============================================================
INSERT INTO event_categories (event_id, category_id)
SELECT e.id, c.id 
FROM events e, categories c
WHERE e.title = 'Tech Conference 2025' AND c.slug = 'technology'
ON CONFLICT DO NOTHING;

INSERT INTO event_categories (event_id, category_id)
SELECT e.id, c.id 
FROM events e, categories c
WHERE e.title = 'AI Workshop: Deep Learning Fundamentals' AND c.slug = 'technology'
ON CONFLICT DO NOTHING;

INSERT INTO event_categories (event_id, category_id)
SELECT e.id, c.id 
FROM events e, categories c
WHERE e.title = 'Startup Summit Indonesia 2026' AND c.slug = 'business'
ON CONFLICT DO NOTHING;

INSERT INTO event_categories (event_id, category_id)
SELECT e.id, c.id 
FROM events e, categories c
WHERE e.title = 'Digital Marketing Masterclass' AND c.slug = 'business'
ON CONFLICT DO NOTHING;

INSERT INTO event_categories (event_id, category_id)
SELECT e.id, c.id 
FROM events e, categories c
WHERE e.title = 'Yoga & Wellness Retreat' AND c.slug = 'health'
ON CONFLICT DO NOTHING;

-- 5. TICKETS
-- ============================================================
INSERT INTO tickets (
    event_id, name, description, price, quantity, max_per_order,
    benefits, status, sale_starts_at, sale_ends_at
) 
SELECT e.id, 'Early Bird', 
    'Tiket early bird dengan harga spesial. Termasuk lunch dan seminar kit.',
    350000, 50, 2, ARRAY['Lunch', 'Seminar Kit', 'E-Certificate'],
    'available', '2025-10-01', '2025-11-15'
FROM events e WHERE e.title = 'Tech Conference 2025'
ON CONFLICT DO NOTHING;

INSERT INTO tickets (
    event_id, name, description, price, quantity, max_per_order,
    benefits, status, sale_starts_at, sale_ends_at
) 
SELECT e.id, 'Regular',
    'Tiket reguler konferensi. Termasuk lunch dan seminar kit.',
    500000, 150, 5, ARRAY['Lunch', 'Seminar Kit', 'E-Certificate'],
    'available', '2025-10-01', '2025-12-14'
FROM events e WHERE e.title = 'Tech Conference 2025'
ON CONFLICT DO NOTHING;

INSERT INTO tickets (
    event_id, name, description, price, quantity, max_per_order,
    benefits, status, sale_starts_at, sale_ends_at
) 
SELECT e.id, 'VIP Access',
    'Akses VIP dengan seat priority, exclusive networking session, dan merchandise premium.',
    750000, 30, 2, ARRAY['Priority Seat', 'Networking Session', 'Premium Merchandise', 'Lunch', 'E-Certificate'],
    'available', '2025-10-01', '2025-12-14'
FROM events e WHERE e.title = 'Tech Conference 2025'
ON CONFLICT DO NOTHING;

INSERT INTO tickets (
    event_id, name, description, price, quantity, max_per_order,
    benefits, status, sale_starts_at, sale_ends_at
) 
SELECT e.id, 'Workshop Pass',
    'Akses penuh workshop, dataset, dan source code.',
    350000, 50, 1, ARRAY['Dataset', 'Source Code', 'E-Certificate'],
    'available', '2025-10-01', '2025-12-19'
FROM events e WHERE e.title = 'AI Workshop: Deep Learning Fundamentals'
ON CONFLICT DO NOTHING;

INSERT INTO tickets (
    event_id, name, description, price, quantity, max_per_order,
    benefits, status, sale_starts_at, sale_ends_at
) 
SELECT e.id, 'VIP Pass',
    'Akses VIP 3 hari, priority seating, dan gala dinner.',
    750000, 100, 3, ARRAY['3-Day Access', 'Gala Dinner', 'Priority Seat', 'E-Certificate'],
    'available', '2025-11-01', '2026-01-09'
FROM events e WHERE e.title = 'Startup Summit Indonesia 2026'
ON CONFLICT DO NOTHING;

INSERT INTO tickets (
    event_id, name, description, price, quantity, max_per_order,
    benefits, status, sale_starts_at, sale_ends_at
) 
SELECT e.id, 'Regular Pass',
    'Akses reguler 3 hari summit.',
    500000, 200, 5, ARRAY['3-Day Access', 'E-Certificate'],
    'available', '2025-11-01', '2026-01-09'
FROM events e WHERE e.title = 'Startup Summit Indonesia 2026'
ON CONFLICT DO NOTHING;

INSERT INTO tickets (
    event_id, name, description, price, quantity, max_per_order,
    benefits, status, sale_starts_at, sale_ends_at
) 
SELECT e.id, 'Early Bird',
    'Harga spesial early bird. Materi recording included.',
    150000, 100, 3, ARRAY['Live Session', 'Recording', 'E-Certificate'],
    'available', '2025-10-01', '2025-11-20'
FROM events e WHERE e.title = 'Digital Marketing Masterclass'
ON CONFLICT DO NOTHING;

INSERT INTO tickets (
    event_id, name, description, price, quantity, max_per_order,
    benefits, status, sale_starts_at, sale_ends_at
) 
SELECT e.id, 'Regular',
    'Akses live session dan recording.',
    250000, 200, 5, ARRAY['Live Session', 'Recording', 'E-Certificate'],
    'available', '2025-10-01', '2025-11-24'
FROM events e WHERE e.title = 'Digital Marketing Masterclass'
ON CONFLICT DO NOTHING;

INSERT INTO tickets (
    event_id, name, description, price, quantity, max_per_order,
    benefits, status, sale_starts_at, sale_ends_at
) 
SELECT e.id, 'Full Package',
    'Akomodasi 1 malam, 4 sesi yoga, meals, dan workshop mindfulness.',
    1200000, 30, 2, ARRAY['Akomodasi', 'Meals', 'Yoga Sessions', 'Workshop'],
    'available', '2025-10-01', '2025-11-28'
FROM events e WHERE e.title = 'Yoga & Wellness Retreat'
ON CONFLICT DO NOTHING;

INSERT INTO tickets (
    event_id, name, description, price, quantity, max_per_order,
    benefits, status, sale_starts_at, sale_ends_at
) 
SELECT e.id, 'Day Pass',
    'Akses 1 hari tanpa menginap. Termasuk 2 sesi yoga dan lunch.',
    400000, 20, 3, ARRAY['Day Access', '2 Yoga Sessions', 'Lunch'],
    'available', '2025-10-01', '2025-11-29'
FROM events e WHERE e.title = 'Yoga & Wellness Retreat'
ON CONFLICT DO NOTHING;

-- 6. KNOWLEDGE_BASE (FAQ untuk Chatbot)
-- ============================================================
INSERT INTO knowledge_base (category, question, answer, keywords, priority) VALUES
    ('general', 'Apa itu EventBot?', 
     'EventBot adalah asisten virtual untuk manajemen event dan konferensi. Saya bisa membantu Anda mencari event, mendaftar tiket, dan memberikan informasi terkini.',
     ARRAY['eventbot', 'apa itu', 'tentang', 'chatbot'], 10)
ON CONFLICT DO NOTHING;

INSERT INTO knowledge_base (category, question, answer, keywords, priority) VALUES
    ('general', 'Bagaimana cara mendaftar event?',
     'Anda bisa mendaftar event dengan cara:
1. Cari event yang diminati
2. Pilih tiket yang tersedia
3. Klik ''Daftar'' atau bilang ke saya ''Daftar [nama event]''
4. Selesaikan pembayaran
5. Tiket akan muncul di Profil Anda',
     ARRAY['daftar', 'cara daftar', 'booking', 'pesan tiket', 'register'], 10)
ON CONFLICT DO NOTHING;

INSERT INTO knowledge_base (category, question, answer, keywords, priority) VALUES
    ('general', 'Apakah EventBot gratis?',
     'Ya, menggunakan EventBot untuk mencari dan melihat event adalah gratis. Harga tiket event bervariasi tergantung event yang Anda pilih. Ada juga event gratis lho!',
     ARRAY['gratis', 'free', 'bayar', 'harga', 'biaya'], 9)
ON CONFLICT DO NOTHING;

INSERT INTO knowledge_base (category, question, answer, keywords, priority) VALUES
    ('event', 'Event apa saja yang tersedia?',
     'Saya bisa membantu Anda mencari event berdasarkan kategori, lokasi, atau tanggal. Coba ketik ''Cari event di Jakarta'' atau ''Event teknologi bulan ini''.',
     ARRAY['event apa', 'daftar event', 'tersedia', 'cari event'], 9)
ON CONFLICT DO NOTHING;

INSERT INTO knowledge_base (category, question, answer, keywords, priority) VALUES
    ('event', 'Bagaimana cara melihat detail event?',
     'Anda bisa melihat detail event dengan mengetik ''Detail [nama event]'' atau mengklik event di halaman Event Explorer. Saya akan menampilkan informasi lengkap.',
     ARRAY['detail event', 'info event', 'informasi event', 'lihat event'], 8)
ON CONFLICT DO NOTHING;

INSERT INTO knowledge_base (category, question, answer, keywords, priority) VALUES
    ('ticket', 'Apakah tiket bisa refund?',
     'Kebijakan refund tergantung event masing-masing. Umumnya:
- Refund 100% jika H-7
- Refund 50% jika H-3
- Tidak refund jika H-1 atau saat event.',
     ARRAY['refund', 'batal', 'cancel', 'pengembalian uang', 'kembali'], 8)
ON CONFLICT DO NOTHING;

INSERT INTO knowledge_base (category, question, answer, keywords, priority) VALUES
    ('ticket', 'Bagaimana cara check-in di event?',
     'Saat event berlangsung, tunjukkan QR code tiket Anda di lokasi check-in. QR code bisa ditemukan di menu Profil > Tiket Saya.',
     ARRAY['check in', 'check-in', 'masuk event', 'qr code', 'tiket'], 8)
ON CONFLICT DO NOTHING;

INSERT INTO knowledge_base (category, question, answer, keywords, priority) VALUES
    ('account', 'Bagaimana cara mengubah password?',
     'Anda bisa mengubah password di menu Pengaturan > Profil. Klik ''Ubah Password'' dan masukkan password lama serta password baru Anda.',
     ARRAY['password', 'ganti password', 'ubah password', 'lupa password'], 7)
ON CONFLICT DO NOTHING;

INSERT INTO knowledge_base (category, question, answer, keywords, priority) VALUES
    ('account', 'Bagaimana cara menjadi organizer?',
     'Untuk menjadi organizer, hubungi admin di email admin@eventbot.com dengan subject ''Request Organizer''. Tim kami akan review dan mengubah role akun Anda.',
     ARRAY['organizer', 'jadi organizer', 'buat event', 'host event'], 7)
ON CONFLICT DO NOTHING;

INSERT INTO knowledge_base (category, question, answer, keywords, priority) VALUES
    ('payment', 'Metode pembayaran apa yang tersedia?',
     'Kami menerima pembayaran via:
- Transfer Bank (BCA, Mandiri, BNI)
- Virtual Account
- E-wallet (GoPay, OVO, DANA, LinkAja)
- Kartu Kredit',
     ARRAY['pembayaran', 'bayar', 'payment', 'transfer', 'gopay', 'ovo'], 8)
ON CONFLICT DO NOTHING;

INSERT INTO knowledge_base (category, question, answer, keywords, priority) VALUES
    ('help', 'Bantuan',
     'Saya bisa membantu Anda dengan:
🔍 Cari event
📋 Lihat daftar event
🎫 Daftar tiket
👤 Lihat profil
❓ FAQ

Ada yang bisa saya bantu?',
     ARRAY['bantuan', 'help', 'fitur', 'bisa apa', 'menu'], 10)
ON CONFLICT DO NOTHING;

INSERT INTO knowledge_base (category, question, answer, keywords, priority) VALUES
    ('greeting', 'Halo',
     'Halo! 👋 Selamat datang di EventBot!

Saya adalah asisten virtual untuk manajemen event dan konferensi. Ada yang bisa saya bantu hari ini?

Coba ketik:
• ''Cari event'' untuk melihat event tersedia
• ''Bantuan'' untuk melihat semua fitur',
     ARRAY['halo', 'hai', 'hey', 'hi', 'assalamualaikum'], 10)
ON CONFLICT DO NOTHING;

-- 7. SYSTEM_SETTINGS
-- ============================================================
INSERT INTO system_settings (key, value, description) VALUES
    ('chatbot_name', 'EventBot', 'Nama chatbot yang ditampilkan ke user')
ON CONFLICT (key) DO NOTHING;

INSERT INTO system_settings (key, value, description) VALUES
    ('chatbot_greeting', 'Halo! Selamat datang di EventBot! 👋', 'Pesan sapaan default chatbot')
ON CONFLICT (key) DO NOTHING;

INSERT INTO system_settings (key, value, description) VALUES
    ('chatbot_fallback', 'Maaf, saya tidak mengerti. Coba ketik ''bantuan'' untuk melihat fitur yang tersedia.', 'Pesan fallback saat intent tidak dikenali')
ON CONFLICT (key) DO NOTHING;

INSERT INTO system_settings (key, value, description) VALUES
    ('max_chat_history', '50', 'Maksimal pesan chat yang disimpan per session')
ON CONFLICT (key) DO NOTHING;

INSERT INTO system_settings (key, value, description) VALUES
    ('event_default_image', 'https://images.unsplash.com/photo-1540575467063-178a50c2df87', 'Gambar default untuk event tanpa image')
ON CONFLICT (key) DO NOTHING;

INSERT INTO system_settings (key, value, description) VALUES
    ('registration_deadline_hours', '24', 'Batas waktu pembayaran registrasi (jam)')
ON CONFLICT (key) DO NOTHING;

INSERT INTO system_settings (key, value, description) VALUES
    ('enable_email_notification', 'true', 'Aktifkan notifikasi email')
ON CONFLICT (key) DO NOTHING;

INSERT INTO system_settings (key, value, description) VALUES
    ('maintenance_mode', 'false', 'Mode maintenance (true = read-only)')
ON CONFLICT (key) DO NOTHING;