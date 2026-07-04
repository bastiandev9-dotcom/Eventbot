-- ============================================================
-- EVENTBOT - DATABASE SCHEMA (PostgreSQL Compatible)
-- ============================================================

-- 1. EXTENSIONS
-- ============================================================
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- 2. CUSTOM ENUM TYPES
-- ============================================================
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'user_role') THEN
        CREATE TYPE user_role AS ENUM ('admin', 'organizer', 'participant');
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'user_status') THEN
        CREATE TYPE user_status AS ENUM ('active', 'inactive', 'suspended');
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'event_status') THEN
        CREATE TYPE event_status AS ENUM ('upcoming', 'ongoing', 'completed', 'cancelled');
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'ticket_status') THEN
        CREATE TYPE ticket_status AS ENUM ('available', 'sold_out', 'reserved', 'unavailable');
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'registration_status') THEN
        CREATE TYPE registration_status AS ENUM ('pending', 'confirmed', 'cancelled', 'attended');
    END IF;
END $$;

-- 3. TABLES
-- ============================================================

CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    phone VARCHAR(20),
    avatar_url VARCHAR(500),
    role user_role NOT NULL DEFAULT 'participant',
    status user_status NOT NULL DEFAULT 'active',
    email_verified_at TIMESTAMP,
    last_login_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP
);

COMMENT ON TABLE users IS 'Tabel pengguna sistem EventBot';
COMMENT ON COLUMN users.deleted_at IS 'NULL = aktif, terisi = soft deleted';

CREATE TABLE IF NOT EXISTS categories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(50) UNIQUE NOT NULL,
    slug VARCHAR(60) UNIQUE NOT NULL,
    description TEXT,
    color VARCHAR(7) DEFAULT '#3B82F6',
    icon VARCHAR(50),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(200) NOT NULL,
    slug VARCHAR(220) UNIQUE NOT NULL,
    description TEXT,
    short_description VARCHAR(500),
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    start_time TIME,
    end_time TIME,
    location VARCHAR(200) NOT NULL,
    location_map_url VARCHAR(500),
    organizer_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    image_url VARCHAR(500),
    banner_url VARCHAR(500),
    capacity INTEGER DEFAULT 0,
    status event_status NOT NULL DEFAULT 'upcoming',
    is_published BOOLEAN NOT NULL DEFAULT FALSE,
    published_at TIMESTAMP,
    view_count INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP,

    CONSTRAINT valid_event_dates CHECK (start_date <= end_date),
    CONSTRAINT valid_event_times CHECK (
        start_time IS NULL OR end_time IS NULL OR start_time <= end_time OR start_date < end_date
    )
);

COMMENT ON TABLE events IS 'Tabel event dan konferensi';
COMMENT ON COLUMN events.slug IS 'URL-friendly identifier, auto-generated';
COMMENT ON COLUMN events.is_published IS 'Event hanya terlihat publik jika TRUE';

CREATE TABLE IF NOT EXISTS event_categories (
    event_id UUID NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    category_id UUID NOT NULL REFERENCES categories(id) ON DELETE CASCADE,
    PRIMARY KEY (event_id, category_id)
);

CREATE TABLE IF NOT EXISTS tickets (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    event_id UUID NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    price DECIMAL(12,2) NOT NULL DEFAULT 0,
    quantity INTEGER NOT NULL DEFAULT 0,
    sold INTEGER NOT NULL DEFAULT 0,
    max_per_order INTEGER DEFAULT 5,
    benefits TEXT[],
    status ticket_status NOT NULL DEFAULT 'available',
    sale_starts_at TIMESTAMP,
    sale_ends_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP,

    CONSTRAINT valid_quantity CHECK (quantity >= 0),
    CONSTRAINT valid_sold CHECK (sold >= 0),
    CONSTRAINT no_over_selling CHECK (sold <= quantity),
    CONSTRAINT valid_max_per_order CHECK (max_per_order >= 1),
    CONSTRAINT valid_sale_period CHECK (
        sale_ends_at IS NULL OR sale_starts_at IS NULL OR sale_ends_at >= sale_starts_at
    )
);

COMMENT ON TABLE tickets IS 'Tabel tiket per event';

CREATE TABLE IF NOT EXISTS registrations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    ticket_id UUID NOT NULL REFERENCES tickets(id) ON DELETE RESTRICT,
    event_id UUID NOT NULL REFERENCES events(id) ON DELETE RESTRICT,
    quantity INTEGER NOT NULL DEFAULT 1,
    total_price DECIMAL(12,2) NOT NULL DEFAULT 0,
    status registration_status NOT NULL DEFAULT 'pending',
    payment_method VARCHAR(50),
    payment_proof_url VARCHAR(500),
    notes TEXT,
    checked_in_at TIMESTAMP,
    checked_in_by UUID REFERENCES users(id),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    cancelled_at TIMESTAMP,

    CONSTRAINT valid_reg_quantity CHECK (quantity >= 1),
    CONSTRAINT valid_total_price CHECK (total_price >= 0)
);

COMMENT ON TABLE registrations IS 'Tabel pendaftaran/pemesanan tiket';

CREATE TABLE IF NOT EXISTS chat_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    session_token VARCHAR(64) UNIQUE NOT NULL DEFAULT encode(gen_random_bytes(32), 'hex'),
    ip_address INET,
    user_agent TEXT,
    started_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_activity_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMP,
    context_json JSONB DEFAULT '{}'
);

COMMENT ON TABLE chat_sessions IS 'Sesi percakapan chatbot';

CREATE TABLE IF NOT EXISTS chat_messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    intent VARCHAR(50),
    entities_json JSONB DEFAULT '{}',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE chat_messages IS 'Riwayat pesan chatbot';

CREATE TABLE IF NOT EXISTS knowledge_base (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    category VARCHAR(50) NOT NULL,
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    keywords TEXT[],
    priority INTEGER DEFAULT 0,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE knowledge_base IS 'Knowledge base untuk chatbot responses';

CREATE TABLE IF NOT EXISTS system_settings (
    key VARCHAR(100) PRIMARY KEY,
    value TEXT NOT NULL,
    description TEXT,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE system_settings IS 'Konfigurasi aplikasi dinamis';

-- 4. INDEXES
-- ============================================================

CREATE INDEX IF NOT EXISTS idx_users_email ON users(email) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_users_status ON users(status) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_events_organizer ON events(organizer_id) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_events_status ON events(status) WHERE deleted_at IS NULL AND is_published = TRUE;
CREATE INDEX IF NOT EXISTS idx_events_dates ON events(start_date, end_date) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_events_slug ON events(slug) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_events_published ON events(published_at DESC) WHERE is_published = TRUE AND deleted_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_events_search ON events 
    USING gin(to_tsvector('indonesian', coalesce(title,'') || ' ' || coalesce(description,'') || ' ' || coalesce(location,'')));

CREATE INDEX IF NOT EXISTS idx_tickets_event ON tickets(event_id) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_tickets_status ON tickets(status) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_tickets_price ON tickets(price) WHERE deleted_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_registrations_user ON registrations(user_id) WHERE cancelled_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_registrations_ticket ON registrations(ticket_id) WHERE cancelled_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_registrations_event ON registrations(event_id) WHERE cancelled_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_registrations_status ON registrations(status);
CREATE INDEX IF NOT EXISTS idx_registrations_created ON registrations(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_chat_sessions_user ON chat_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_chat_sessions_token ON chat_sessions(session_token);
CREATE INDEX IF NOT EXISTS idx_chat_messages_session ON chat_messages(session_id);
CREATE INDEX IF NOT EXISTS idx_chat_messages_created ON chat_messages(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_kb_category ON knowledge_base(category) WHERE is_active = TRUE;
CREATE INDEX IF NOT EXISTS idx_kb_keywords ON knowledge_base USING gin(keywords) WHERE is_active = TRUE;