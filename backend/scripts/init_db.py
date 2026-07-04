"""
EventBot Database Initialization Script
=======================================
Script ini akan:
1. Connect ke PostgreSQL server
2. Execute schema.sql, triggers.sql, functions.sql ke database yang sudah ada
3. Insert seed data (categories, admin, events, tickets, knowledge base)

Usage:
    python backend/scripts/init_db.py

Requirements:
    pip install psycopg2-binary python-dotenv
"""

import os
import sys
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "eventbot")

# Path to SQL files
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SCHEMA_FILE = os.path.join(BASE_DIR, "database", "schema.sql")
TRIGGERS_FILE = os.path.join(BASE_DIR, "database", "triggers.sql")
FUNCTIONS_FILE = os.path.join(BASE_DIR, "database", "functions.sql")


def get_connection(db_name=None, autocommit=False):
    """Create PostgreSQL connection."""
    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=db_name or DB_NAME
    )
    if autocommit:
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    return conn


def execute_sql_file(filepath, description):
    """Execute SQL file against database."""
    print(f"\n🔧 {description}...")

    if not os.path.exists(filepath):
        print(f"   ❌ File not found: {filepath}")
        return False

    conn = get_connection(autocommit=True)
    cursor = conn.cursor()

    with open(filepath, "r", encoding="utf-8") as f:
        sql = f.read()

    try:
        cursor.execute(sql)
        print(f"   ✅ Success!")
        return True
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False
    finally:
        cursor.close()
        conn.close()


def seed_categories(cursor):
    """Insert default categories."""
    print("   🌱 Seeding categories...")
    categories = [
        ("Technology", "technology", "Event teknologi dan digital", "#3B82F6", "fa-microchip"),
        ("Business", "business", "Event bisnis dan entrepreneurship", "#10B981", "fa-briefcase"),
        ("Education", "education", "Workshop dan seminar edukasi", "#F59E0B", "fa-graduation-cap"),
        ("Entertainment", "entertainment", "Konser dan hiburan", "#EC4899", "fa-music"),
        ("Social", "social", "Event sosial dan komunitas", "#8B5CF6", "fa-users"),
        ("Health", "health", "Event kesehatan dan wellness", "#EF4444", "fa-heartbeat"),
        ("Art", "art", "Event seni dan budaya", "#F97316", "fa-palette"),
    ]

    cursor.executemany(
        """INSERT INTO categories (name, slug, description, color, icon)
           VALUES (%s, %s, %s, %s, %s)
           ON CONFLICT (slug) DO NOTHING""",
        categories
    )
    print(f"   ✅ {len(categories)} categories inserted.")


def seed_admin_user(cursor):
    """Insert admin user."""
    print("   🌱 Seeding admin user...")
    cursor.execute("""
        INSERT INTO users (name, email, password_hash, role, status, email_verified_at)
        VALUES (
            'Admin EventBot',
            'admin@eventbot.com',
            '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYHmE5cPZ6K',
            'admin',
            'active',
            CURRENT_TIMESTAMP
        )
        ON CONFLICT (email) DO NOTHING
        RETURNING id;
    """)
    result = cursor.fetchone()
    admin_id = result[0] if result else None

    if not admin_id:
        cursor.execute("SELECT id FROM users WHERE email = 'admin@eventbot.com'")
        row = cursor.fetchone()
        admin_id = row[0] if row else None

    print(f"   ✅ Admin user ready (ID: {admin_id}).")
    return admin_id


def seed_organizer(cursor):
    """Insert organizer user."""
    print("   🌱 Seeding organizer user...")
    cursor.execute("""
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
        ON CONFLICT (email) DO NOTHING
        RETURNING id;
    """)
    result = cursor.fetchone()
    org_id = result[0] if result else None

    if not org_id:
        cursor.execute("SELECT id FROM users WHERE email = 'budi@eventbot.com'")
        row = cursor.fetchone()
        org_id = row[0] if row else None

    print(f"   ✅ Organizer user ready (ID: {org_id}).")
    return org_id


def seed_events(cursor, organizer_id):
    """Insert sample events."""
    print("   🌱 Seeding events...")
    events = [
        (
            "Tech Conference 2025",
            "Konferensi teknologi tahunan terbesar di Indonesia. Menghadirkan pembicara dari Google, Microsoft, dan startup lokal ternama.",
            "Konferensi teknologi tahunan dengan pembicara internasional",
            "2025-12-15", "2025-12-16", "08:00", "17:00",
            "Jakarta Convention Center", "https://maps.google.com/?q=JCC",
            organizer_id,
            "https://images.unsplash.com/photo-1540575467063-178a50c2df87",
            "https://images.unsplash.com/photo-1540575467063-178a50c2df87",
            500, "upcoming", True
        ),
        (
            "AI Workshop: Deep Learning Fundamentals",
            "Workshop hands-on Artificial Intelligence dan Deep Learning untuk pemula. Peserta akan belajar membuat model neural network dari nol.",
            "Workshop AI hands-on untuk pemula",
            "2025-12-20", "2025-12-20", "09:00", "16:00",
            "Bandung Institute of Technology", "https://maps.google.com/?q=ITB",
            organizer_id,
            "https://images.unsplash.com/photo-1485827404703-89b55fcc595e",
            "https://images.unsplash.com/photo-1485827404703-89b55fcc595e",
            100, "upcoming", True
        ),
        (
            "Startup Summit Indonesia 2026",
            "Pertemuan tahunan para founder, investor, dan enthusiast startup. Networking, pitching, dan workshop bisnis.",
            "Pertemuan founder dan investor startup",
            "2026-01-10", "2026-01-12", "08:00", "18:00",
            "Bali Nusa Dua Convention Center", "https://maps.google.com/?q=NusaDua",
            organizer_id,
            "https://images.unsplash.com/photo-1515187029135-18ee286d815b",
            "https://images.unsplash.com/photo-1515187029135-18ee286d815b",
            1000, "upcoming", True
        ),
        (
            "Digital Marketing Masterclass",
            "Pelajari strategi digital marketing terkini dari praktisi industri. SEO, SEM, Social Media, dan Content Marketing.",
            "Masterclass digital marketing lengkap",
            "2025-11-25", "2025-11-25", "10:00", "16:00",
            "Online via Zoom", None,
            organizer_id,
            "https://images.unsplash.com/photo-1460925895917-afdab827c52f",
            "https://images.unsplash.com/photo-1460925895917-afdab827c52f",
            300, "upcoming", True
        ),
        (
            "Yoga & Wellness Retreat",
            "Habiskan akhir pekan dengan yoga, meditasi, dan aktivitas wellness di pegunungan Bandung.",
            "Retreat yoga dan wellness di alam",
            "2025-11-30", "2025-12-01", "07:00", "15:00",
            "Dusun Bambu, Bandung", "https://maps.google.com/?q=DusunBambu",
            organizer_id,
            "https://images.unsplash.com/photo-1544367567-0f2fcb009e0b",
            "https://images.unsplash.com/photo-1544367567-0f2fcb009e0b",
            50, "upcoming", True
        ),
    ]

    event_ids = []
    for event in events:
        cursor.execute("""
            INSERT INTO events (
                title, description, short_description, start_date, end_date,
                start_time, end_time, location, location_map_url, organizer_id,
                image_url, banner_url, capacity, status, is_published, published_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
            ON CONFLICT (slug) DO NOTHING
            RETURNING id;
        """, event)

        result = cursor.fetchone()
        if result:
            event_ids.append((result[0], event[0]))
        else:
            cursor.execute("SELECT id FROM events WHERE title = %s", (event[0],))
            existing = cursor.fetchone()
            if existing:
                event_ids.append((existing[0], event[0]))

    print(f"   ✅ {len(event_ids)} events inserted.")
    return event_ids


def seed_event_categories(cursor, event_ids):
    """Link events to categories."""
    print("   🌱 Linking events to categories...")

    category_map = {
        "Tech Conference 2025": "technology",
        "AI Workshop: Deep Learning Fundamentals": "technology",
        "Startup Summit Indonesia 2026": "business",
        "Digital Marketing Masterclass": "business",
        "Yoga & Wellness Retreat": "health"
    }

    for event_id, title in event_ids:
        cat_slug = category_map.get(title)
        if cat_slug:
            cursor.execute(
                "SELECT id FROM categories WHERE slug = %s",
                (cat_slug,)
            )
            cat_result = cursor.fetchone()
            if cat_result:
                cursor.execute(
                    """INSERT INTO event_categories (event_id, category_id)
                       VALUES (%s, %s)
                       ON CONFLICT DO NOTHING""",
                    (event_id, cat_result[0])
                )

    print(f"   ✅ Events linked to categories.")


def seed_tickets(cursor, event_ids):
    """Insert tickets for events."""
    print("   🌱 Seeding tickets...")

    cursor.execute("SELECT id, title FROM events WHERE deleted_at IS NULL")
    all_events = {row[1]: row[0] for row in cursor.fetchall()}

    tickets = [
        (all_events.get("Tech Conference 2025"), "Early Bird", 
         "Tiket early bird dengan harga spesial. Termasuk lunch dan seminar kit.",
         350000, 50, 2, ["Lunch", "Seminar Kit", "E-Certificate"], 
         "available", "2025-10-01", "2025-11-15"),
        (all_events.get("Tech Conference 2025"), "Regular",
         "Tiket reguler konferensi. Termasuk lunch dan seminar kit.",
         500000, 150, 5, ["Lunch", "Seminar Kit", "E-Certificate"],
         "available", "2025-10-01", "2025-12-14"),
        (all_events.get("Tech Conference 2025"), "VIP Access",
         "Akses VIP dengan seat priority, exclusive networking session, dan merchandise premium.",
         750000, 30, 2, ["Priority Seat", "Networking Session", "Premium Merchandise", "Lunch", "E-Certificate"],
         "available", "2025-10-01", "2025-12-14"),
        (all_events.get("AI Workshop: Deep Learning Fundamentals"), "Workshop Pass",
         "Akses penuh workshop, dataset, dan source code.",
         350000, 50, 1, ["Dataset", "Source Code", "E-Certificate"],
         "available", "2025-10-01", "2025-12-19"),
        (all_events.get("Startup Summit Indonesia 2026"), "VIP Pass",
         "Akses VIP 3 hari, priority seating, dan gala dinner.",
         750000, 100, 3, ["3-Day Access", "Gala Dinner", "Priority Seat", "E-Certificate"],
         "available", "2025-11-01", "2026-01-09"),
        (all_events.get("Startup Summit Indonesia 2026"), "Regular Pass",
         "Akses reguler 3 hari summit.",
         500000, 200, 5, ["3-Day Access", "E-Certificate"],
         "available", "2025-11-01", "2026-01-09"),
        (all_events.get("Digital Marketing Masterclass"), "Early Bird",
         "Harga spesial early bird. Materi recording included.",
         150000, 100, 3, ["Live Session", "Recording", "E-Certificate"],
         "available", "2025-10-01", "2025-11-20"),
        (all_events.get("Digital Marketing Masterclass"), "Regular",
         "Akses live session dan recording.",
         250000, 200, 5, ["Live Session", "Recording", "E-Certificate"],
         "available", "2025-10-01", "2025-11-24"),
        (all_events.get("Yoga & Wellness Retreat"), "Full Package",
         "Akomodasi 1 malam, 4 sesi yoga, meals, dan workshop mindfulness.",
         1200000, 30, 2, ["Akomodasi", "Meals", "Yoga Sessions", "Workshop"],
         "available", "2025-10-01", "2025-11-28"),
        (all_events.get("Yoga & Wellness Retreat"), "Day Pass",
         "Akses 1 hari tanpa menginap. Termasuk 2 sesi yoga dan lunch.",
         400000, 20, 3, ["Day Access", "2 Yoga Sessions", "Lunch"],
         "available", "2025-10-01", "2025-11-29"),
    ]

    valid_tickets = [t for t in tickets if t[0] is not None]

    cursor.executemany("""
        INSERT INTO tickets (
            event_id, name, description, price, quantity, max_per_order,
            benefits, status, sale_starts_at, sale_ends_at
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT DO NOTHING
    """, valid_tickets)

    print(f"   ✅ {len(valid_tickets)} tickets inserted.")


def seed_knowledge_base(cursor):
    """Insert chatbot knowledge base / FAQ."""
    print("   🌱 Seeding knowledge base...")

    kb_entries = [
        ("general", "Apa itu EventBot?", 
         "EventBot adalah asisten virtual untuk manajemen event dan konferensi. Saya bisa membantu Anda mencari event, mendaftar tiket, dan memberikan informasi terkini.",
         ["eventbot", "apa itu", "tentang", "chatbot"], 10),
        ("general", "Bagaimana cara mendaftar event?",
         "Anda bisa mendaftar event dengan cara:\n1. Cari event yang diminati\n2. Pilih tiket yang tersedia\n3. Klik 'Daftar' atau bilang ke saya 'Daftar [nama event]'\n4. Selesaikan pembayaran\n5. Tiket akan muncul di Profil Anda",
         ["daftar", "cara daftar", "booking", "pesan tiket", "register"], 10),
        ("general", "Apakah EventBot gratis?",
         "Ya, menggunakan EventBot untuk mencari dan melihat event adalah gratis. Harga tiket event bervariasi tergantung event yang Anda pilih. Ada juga event gratis lho!",
         ["gratis", "free", "bayar", "harga", "biaya"], 9),
        ("event", "Event apa saja yang tersedia?",
         "Saya bisa membantu Anda mencari event berdasarkan kategori, lokasi, atau tanggal. Coba ketik 'Cari event di Jakarta' atau 'Event teknologi bulan ini'.",
         ["event apa", "daftar event", "tersedia", "cari event"], 9),
        ("event", "Bagaimana cara melihat detail event?",
         "Anda bisa melihat detail event dengan mengetik 'Detail [nama event]' atau mengklik event di halaman Event Explorer. Saya akan menampilkan informasi lengkap.",
         ["detail event", "info event", "informasi event", "lihat event"], 8),
        ("ticket", "Apakah tiket bisa refund?",
         "Kebijakan refund tergantung event masing-masing. Umumnya:\n- Refund 100% jika H-7\n- Refund 50% jika H-3\n- Tidak refund jika H-1 atau saat event.",
         ["refund", "batal", "cancel", "pengembalian uang", "kembali"], 8),
        ("ticket", "Bagaimana cara check-in di event?",
         "Saat event berlangsung, tunjukkan QR code tiket Anda di lokasi check-in. QR code bisa ditemukan di menu Profil > Tiket Saya.",
         ["check in", "check-in", "masuk event", "qr code", "tiket"], 8),
        ("account", "Bagaimana cara mengubah password?",
         "Anda bisa mengubah password di menu Pengaturan > Profil. Klik 'Ubah Password' dan masukkan password lama serta password baru Anda.",
         ["password", "ganti password", "ubah password", "lupa password"], 7),
        ("account", "Bagaimana cara menjadi organizer?",
         "Untuk menjadi organizer, hubungi admin di email admin@eventbot.com dengan subject 'Request Organizer'. Tim kami akan review dan mengubah role akun Anda.",
         ["organizer", "jadi organizer", "buat event", "host event"], 7),
        ("payment", "Metode pembayaran apa yang tersedia?",
         "Kami menerima pembayaran via:\n- Transfer Bank (BCA, Mandiri, BNI)\n- Virtual Account\n- E-wallet (GoPay, OVO, DANA, LinkAja)\n- Kartu Kredit",
         ["pembayaran", "bayar", "payment", "transfer", "gopay", "ovo"], 8),
        ("help", "Bantuan",
         "Saya bisa membantu Anda dengan:\n🔍 Cari event\n📋 Lihat daftar event\n🎫 Daftar tiket\n👤 Lihat profil\n❓ FAQ\n\nAda yang bisa saya bantu?",
         ["bantuan", "help", "fitur", "bisa apa", "menu"], 10),
        ("greeting", "Halo",
         "Halo! 👋 Selamat datang di EventBot!\n\nSaya adalah asisten virtual untuk manajemen event dan konferensi. Ada yang bisa saya bantu hari ini?\n\nCoba ketik:\n• 'Cari event' untuk melihat event tersedia\n• 'Bantuan' untuk melihat semua fitur",
         ["halo", "hai", "hey", "hi", "assalamualaikum"], 10),
    ]

    cursor.executemany("""
        INSERT INTO knowledge_base (category, question, answer, keywords, priority)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT DO NOTHING
    """, kb_entries)

    print(f"   ✅ {len(kb_entries)} knowledge base entries inserted.")


def seed_system_settings(cursor):
    """Insert default system settings."""
    print("   🌱 Seeding system settings...")

    settings = [
        ("chatbot_name", "EventBot", "Nama chatbot yang ditampilkan ke user"),
        ("chatbot_greeting", "Halo! Selamat datang di EventBot! 👋", "Pesan sapaan default chatbot"),
        ("chatbot_fallback", "Maaf, saya tidak mengerti. Coba ketik 'bantuan' untuk melihat fitur yang tersedia.", "Pesan fallback saat intent tidak dikenali"),
        ("max_chat_history", "50", "Maksimal pesan chat yang disimpan per session"),
        ("event_default_image", "https://images.unsplash.com/photo-1540575467063-178a50c2df87", "Gambar default untuk event tanpa image"),
        ("registration_deadline_hours", "24", "Batas waktu pembayaran registrasi (jam)"),
        ("enable_email_notification", "true", "Aktifkan notifikasi email"),
        ("maintenance_mode", "false", "Mode maintenance (true = read-only)"),
    ]

    cursor.executemany("""
        INSERT INTO system_settings (key, value, description)
        VALUES (%s, %s, %s)
        ON CONFLICT (key) DO NOTHING
    """, settings)

    print(f"   ✅ {len(settings)} system settings inserted.")


def seed_data():
    """Insert all seed data."""
    print("\n🔧 [4/6] Seeding data...")

    conn = get_connection(autocommit=True)
    cursor = conn.cursor()

    try:
        seed_categories(cursor)
        admin_id = seed_admin_user(cursor)
        org_id = seed_organizer(cursor)
        event_ids = seed_events(cursor, org_id)
        seed_event_categories(cursor, event_ids)
        seed_tickets(cursor, event_ids)
        seed_knowledge_base(cursor)
        seed_system_settings(cursor)

        print("\n   ✅ All seed data inserted successfully!")
    except Exception as e:
        print(f"\n   ❌ Error seeding data: {e}")
        raise
    finally:
        cursor.close()
        conn.close()


def verify_database():
    """Verify database is properly set up."""
    print("\n🔧 [6/6] Verifying database...")

    conn = get_connection()
    cursor = conn.cursor()

    tables = [
        "users", "categories", "events", "event_categories",
        "tickets", "registrations", "chat_sessions", "chat_messages",
        "knowledge_base", "system_settings"
    ]

    print("   📊 Database Summary:")
    total_rows = 0
    for table in tables:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            total_rows += count
            print(f"      • {table}: {count} rows")
        except Exception as e:
            print(f"      • {table}: ERROR - {e}")

    cursor.close()
    conn.close()
    print(f"\n   ✅ Total: {total_rows} rows across {len(tables)} tables")


def main():
    """Main initialization flow."""
    print("=" * 60)
    print("  🚀 EventBot Database Initialization")
    print("=" * 60)
    print(f"\n  📁 Database: {DB_NAME}")
    print(f"  🖥️  Host: {DB_HOST}:{DB_PORT}")
    print(f"  👤 User: {DB_USER}")

    try:
        # Step 1: Execute schema
        execute_sql_file(SCHEMA_FILE, "[1/4] Creating schema (tables, enums, indexes)")

        # Step 2: Execute triggers
        execute_sql_file(TRIGGERS_FILE, "[2/4] Creating triggers & functions")

        # Step 3: Execute stored functions
        execute_sql_file(FUNCTIONS_FILE, "[3/4] Creating stored procedures")

        # Step 4: Seed data
        seed_data()

        # Step 5: Verify
        verify_database()

        print("\n" + "=" * 60)
        print("  ✅ Database initialization complete!")
        print("  🔑 Admin: admin@eventbot.com / admin123")
        print("  🔑 Organizer: budi@eventbot.com / admin123")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ Initialization failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()