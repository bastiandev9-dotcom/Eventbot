-- ============================================================
-- EVENTBOT - STORED FUNCTIONS & PROCEDURES (PostgreSQL Compatible)
-- FIX: COMMENT ON FUNCTION dengan signature lengkap
-- ============================================================

-- 1. CEK KETERSEDIAAN TIKET
-- ============================================================
CREATE OR REPLACE FUNCTION check_ticket_availability(p_ticket_id UUID)
RETURNS TABLE (
    available BOOLEAN,
    remaining INTEGER,
    ticket_name VARCHAR,
    event_title VARCHAR,
    price DECIMAL(12,2),
    max_per_order INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        (t.quantity - t.sold > 0) as available,
        (t.quantity - t.sold)::INTEGER as remaining,
        t.name::VARCHAR,
        e.title::VARCHAR,
        t.price,
        t.max_per_order
    FROM tickets t
    JOIN events e ON t.event_id = e.id
    WHERE t.id = p_ticket_id 
      AND t.deleted_at IS NULL 
      AND e.deleted_at IS NULL
      AND e.is_published = TRUE;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION check_ticket_availability(UUID) IS 'Cek sisa tiket dan info harga sebelum pemesanan';

-- 2. REGISTRASI / BOOKING EVENT
-- ============================================================
CREATE OR REPLACE FUNCTION register_to_event(
    p_user_id UUID,
    p_ticket_id UUID,
    p_quantity INTEGER DEFAULT 1,
    p_payment_method VARCHAR(50) DEFAULT NULL
)
RETURNS TABLE (
    success BOOLEAN,
    registration_id UUID,
    total_price DECIMAL(12,2),
    message TEXT
) AS $$
DECLARE
    v_ticket RECORD;
    v_event_id UUID;
    v_total_price DECIMAL(12,2);
    v_registration_id UUID;
    v_remaining INTEGER;
BEGIN
    SELECT t.*, e.id as event_id INTO v_ticket
    FROM tickets t
    JOIN events e ON t.event_id = e.id
    WHERE t.id = p_ticket_id 
      AND t.deleted_at IS NULL 
      AND e.deleted_at IS NULL
      AND e.is_published = TRUE;

    IF NOT FOUND THEN
        RETURN QUERY SELECT FALSE, NULL::UUID, 0::DECIMAL(12,2), 'Tiket tidak ditemukan atau event tidak tersedia.'::TEXT;
        RETURN;
    END IF;

    v_remaining := v_ticket.quantity - v_ticket.sold;

    IF v_remaining < p_quantity THEN
        RETURN QUERY SELECT FALSE, NULL::UUID, 0::DECIMAL(12,2), 
            ('Tiket tidak tersedia. Sisa: ' || v_remaining)::TEXT;
        RETURN;
    END IF;

    IF p_quantity > v_ticket.max_per_order THEN
        RETURN QUERY SELECT FALSE, NULL::UUID, 0::DECIMAL(12,2), 
            ('Maksimal ' || v_ticket.max_per_order || ' tiket per order')::TEXT;
        RETURN;
    END IF;

    v_total_price := v_ticket.price * p_quantity;
    v_event_id := v_ticket.event_id;

    INSERT INTO registrations (user_id, ticket_id, event_id, quantity, total_price, status, payment_method)
    VALUES (p_user_id, p_ticket_id, v_event_id, p_quantity, v_total_price, 'pending', p_payment_method)
    RETURNING id INTO v_registration_id;

    RETURN QUERY SELECT TRUE, v_registration_id, v_total_price, 
        ('Pendaftaran berhasil dibuat! Total: Rp ' || to_char(v_total_price, 'FM999,999,999,999'))::TEXT;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION register_to_event(UUID, UUID, INTEGER, VARCHAR) IS 'Proses booking tiket dengan validasi otomatis';

-- 3. CARI EVENT DENGAN FILTER
-- ============================================================
CREATE OR REPLACE FUNCTION search_events(
    p_query TEXT DEFAULT NULL,
    p_location VARCHAR(200) DEFAULT NULL,
    p_category_slug VARCHAR(60) DEFAULT NULL,
    p_start_date DATE DEFAULT NULL,
    p_end_date DATE DEFAULT NULL,
    p_status event_status DEFAULT 'upcoming',
    p_min_price DECIMAL(12,2) DEFAULT NULL,
    p_max_price DECIMAL(12,2) DEFAULT NULL,
    p_limit INTEGER DEFAULT 20,
    p_offset INTEGER DEFAULT 0
)
RETURNS TABLE (
    id UUID,
    title VARCHAR(200),
    slug VARCHAR(220),
    short_description VARCHAR(500),
    start_date DATE,
    end_date DATE,
    location VARCHAR(200),
    image_url VARCHAR(500),
    status event_status,
    min_price DECIMAL(12,2),
    organizer_name VARCHAR(100),
    categories TEXT[]
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        e.id,
        e.title,
        e.slug,
        e.short_description,
        e.start_date,
        e.end_date,
        e.location,
        e.image_url,
        e.status,
        MIN(t.price) as min_price,
        u.name as organizer_name,
        ARRAY_AGG(DISTINCT c.name) as categories
    FROM events e
    JOIN users u ON e.organizer_id = u.id
    LEFT JOIN event_categories ec ON e.id = ec.event_id
    LEFT JOIN categories c ON ec.category_id = c.id
    LEFT JOIN tickets t ON e.id = t.event_id AND t.deleted_at IS NULL
    WHERE e.deleted_at IS NULL
      AND e.is_published = TRUE
      AND (p_status IS NULL OR e.status = p_status)
      AND (p_location IS NULL OR e.location ILIKE '%' || p_location || '%')
      AND (p_category_slug IS NULL OR c.slug = p_category_slug)
      AND (p_start_date IS NULL OR e.start_date >= p_start_date)
      AND (p_end_date IS NULL OR e.end_date <= p_end_date)
      AND (p_query IS NULL OR 
           to_tsvector('indonesian', coalesce(e.title,'') || ' ' || coalesce(e.description,'') || ' ' || coalesce(e.location,'')) 
           @@ plainto_tsquery('indonesian', p_query))
    GROUP BY e.id, e.title, e.slug, e.short_description, e.start_date, e.end_date, 
             e.location, e.image_url, e.status, u.name
    HAVING (p_min_price IS NULL OR MIN(t.price) >= p_min_price)
       AND (p_max_price IS NULL OR MIN(t.price) <= p_max_price)
    ORDER BY e.start_date ASC
    LIMIT p_limit OFFSET p_offset;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION search_events(TEXT, VARCHAR, VARCHAR, DATE, DATE, event_status, DECIMAL, DECIMAL, INTEGER, INTEGER) 
IS 'Pencarian event dengan filter kompleks: lokasi, kategori, tanggal, harga, dan full-text search';

-- 4. DAPATKAN DETAIL EVENT LENGKAP
-- ============================================================
CREATE OR REPLACE FUNCTION get_event_detail(p_event_id UUID)
RETURNS TABLE (
    id UUID,
    title VARCHAR(200),
    slug VARCHAR(220),
    description TEXT,
    short_description VARCHAR(500),
    start_date DATE,
    end_date DATE,
    start_time TIME,
    end_time TIME,
    location VARCHAR(200),
    location_map_url VARCHAR(500),
    image_url VARCHAR(500),
    banner_url VARCHAR(500),
    capacity INTEGER,
    status event_status,
    view_count INTEGER,
    organizer_name VARCHAR(100),
    organizer_id UUID,
    categories TEXT[],
    tickets JSONB
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        e.id,
        e.title,
        e.slug,
        e.description,
        e.short_description,
        e.start_date,
        e.end_date,
        e.start_time,
        e.end_time,
        e.location,
        e.location_map_url,
        e.image_url,
        e.banner_url,
        e.capacity,
        e.status,
        e.view_count,
        u.name as organizer_name,
        u.id as organizer_id,
        ARRAY_AGG(DISTINCT c.name) as categories,
        COALESCE(
            jsonb_agg(
                jsonb_build_object(
                    'id', t.id,
                    'name', t.name,
                    'price', t.price,
                    'remaining', t.quantity - t.sold,
                    'status', t.status,
                    'benefits', t.benefits
                ) ORDER BY t.price ASC
            ) FILTER (WHERE t.id IS NOT NULL),
            '[]'::jsonb
        ) as tickets
    FROM events e
    JOIN users u ON e.organizer_id = u.id
    LEFT JOIN event_categories ec ON e.id = ec.event_id
    LEFT JOIN categories c ON ec.category_id = c.id
    LEFT JOIN tickets t ON e.id = t.event_id AND t.deleted_at IS NULL
    WHERE e.id = p_event_id AND e.deleted_at IS NULL
    GROUP BY e.id, u.name, u.id;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION get_event_detail(UUID) IS 'Ambil detail lengkap event termasuk tiket dan kategori';

-- 5. STATISTIK DASHBOARD ADMIN
-- ============================================================
CREATE OR REPLACE FUNCTION get_admin_dashboard_stats()
RETURNS TABLE (
    total_users BIGINT,
    total_events BIGINT,
    total_registrations BIGINT,
    total_revenue DECIMAL(15,2),
    upcoming_events BIGINT,
    ongoing_events BIGINT,
    completed_events BIGINT,
    active_users BIGINT,
    pending_registrations BIGINT,
    confirmed_registrations BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        (SELECT COUNT(*) FROM users WHERE deleted_at IS NULL) as total_users,
        (SELECT COUNT(*) FROM events WHERE deleted_at IS NULL) as total_events,
        (SELECT COUNT(*) FROM registrations WHERE cancelled_at IS NULL) as total_registrations,
        (SELECT COALESCE(SUM(total_price), 0) FROM registrations WHERE status = 'confirmed') as total_revenue,
        (SELECT COUNT(*) FROM events WHERE status = 'upcoming' AND deleted_at IS NULL AND is_published = TRUE) as upcoming_events,
        (SELECT COUNT(*) FROM events WHERE status = 'ongoing' AND deleted_at IS NULL AND is_published = TRUE) as ongoing_events,
        (SELECT COUNT(*) FROM events WHERE status = 'completed' AND deleted_at IS NULL) as completed_events,
        (SELECT COUNT(*) FROM users WHERE status = 'active' AND deleted_at IS NULL) as active_users,
        (SELECT COUNT(*) FROM registrations WHERE status = 'pending') as pending_registrations,
        (SELECT COUNT(*) FROM registrations WHERE status = 'confirmed') as confirmed_registrations;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION get_admin_dashboard_stats() IS 'Statistik overview untuk dashboard admin';

-- 6. STATISTIK USER (PESERTA)
-- ============================================================
CREATE OR REPLACE FUNCTION get_user_stats(p_user_id UUID)
RETURNS TABLE (
    events_registered BIGINT,
    tickets_owned BIGINT,
    total_spent DECIMAL(15,2),
    upcoming_events BIGINT,
    attended_events BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        (SELECT COUNT(DISTINCT event_id) FROM registrations WHERE user_id = p_user_id AND cancelled_at IS NULL) as events_registered,
        (SELECT COALESCE(SUM(quantity), 0) FROM registrations WHERE user_id = p_user_id AND cancelled_at IS NULL) as tickets_owned,
        (SELECT COALESCE(SUM(total_price), 0) FROM registrations WHERE user_id = p_user_id AND status = 'confirmed') as total_spent,
        (SELECT COUNT(DISTINCT r.event_id) FROM registrations r
         JOIN events e ON r.event_id = e.id
         WHERE r.user_id = p_user_id AND r.cancelled_at IS NULL 
           AND e.status IN ('upcoming', 'ongoing')) as upcoming_events,
        (SELECT COUNT(DISTINCT r.event_id) FROM registrations r
         WHERE r.user_id = p_user_id AND r.status = 'attended') as attended_events;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION get_user_stats(UUID) IS 'Statistik personal untuk dashboard peserta';

-- 7. KNOWLEDGE BASE SEARCH (untuk Chatbot)
-- ============================================================
CREATE OR REPLACE FUNCTION search_knowledge_base(p_query TEXT, p_limit INTEGER DEFAULT 3)
RETURNS TABLE (
    id UUID,
    question TEXT,
    answer TEXT,
    category VARCHAR(50),
    similarity_score FLOAT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        kb.id,
        kb.question,
        kb.answer,
        kb.category,
        similarity(kb.question, p_query) as similarity_score
    FROM knowledge_base kb
    WHERE kb.is_active = TRUE
      AND (kb.question ILIKE '%' || p_query || '%'
           OR kb.answer ILIKE '%' || p_query || '%'
           OR p_query = ANY(kb.keywords))
    ORDER BY 
        CASE WHEN kb.question ILIKE '%' || p_query || '%' THEN 1 ELSE 2 END,
        kb.priority DESC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION search_knowledge_base(TEXT, INTEGER) IS 'Cari jawaban dari knowledge base untuk chatbot';

-- 8. CHAT SESSION MANAGEMENT
-- ============================================================
CREATE OR REPLACE FUNCTION create_chat_session(
    p_user_id UUID DEFAULT NULL,
    p_ip_address INET DEFAULT NULL,
    p_user_agent TEXT DEFAULT NULL
)
RETURNS UUID AS $$
DECLARE
    v_session_id UUID;
BEGIN
    INSERT INTO chat_sessions (user_id, ip_address, user_agent)
    VALUES (p_user_id, p_ip_address, p_user_agent)
    RETURNING id INTO v_session_id;

    RETURN v_session_id;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION create_chat_session(UUID, INET, TEXT) IS 'Buat sesi chat baru dan kembalikan session_id';

-- 9. SIMPAN PESAN CHAT
-- ============================================================
CREATE OR REPLACE FUNCTION save_chat_message(
    p_session_id UUID,
    p_role VARCHAR(20),
    p_content TEXT,
    p_intent VARCHAR(50) DEFAULT NULL,
    p_entities_json JSONB DEFAULT '{}'
)
RETURNS UUID AS $$
DECLARE
    v_message_id UUID;
BEGIN
    INSERT INTO chat_messages (session_id, role, content, intent, entities_json)
    VALUES (p_session_id, p_role, p_content, p_intent, p_entities_json)
    RETURNING id INTO v_message_id;

    RETURN v_message_id;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION save_chat_message(UUID, VARCHAR, TEXT, VARCHAR, JSONB) IS 'Simpan pesan chat ke history';

-- 10. AMBIL HISTORY CHAT
-- ============================================================
CREATE OR REPLACE FUNCTION get_chat_history(
    p_session_id UUID,
    p_limit INTEGER DEFAULT 50
)
RETURNS TABLE (
    id UUID,
    role VARCHAR(20),
    content TEXT,
    intent VARCHAR(50),
    entities_json JSONB,
    created_at TIMESTAMP
) AS $$
BEGIN
    RETURN QUERY
    SELECT cm.id, cm.role, cm.content, cm.intent, cm.entities_json, cm.created_at
    FROM chat_messages cm
    WHERE cm.session_id = p_session_id
    ORDER BY cm.created_at ASC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION get_chat_history(UUID, INTEGER) IS 'Ambil riwayat percakapan chatbot';

-- 11. SOFT DELETE EVENT (CASCADE ke tiket)
-- ============================================================
CREATE OR REPLACE FUNCTION soft_delete_event(p_event_id UUID)
RETURNS BOOLEAN AS $$
BEGIN
    UPDATE events SET deleted_at = CURRENT_TIMESTAMP WHERE id = p_event_id;
    UPDATE tickets SET deleted_at = CURRENT_TIMESTAMP WHERE event_id = p_event_id;
    RETURN FOUND;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION soft_delete_event(UUID) IS 'Soft delete event dan semua tiketnya';

-- 12. GET RECOMMENDED EVENTS
-- ============================================================
CREATE OR REPLACE FUNCTION get_recommended_events(
    p_event_id UUID,
    p_limit INTEGER DEFAULT 3
)
RETURNS TABLE (
    id UUID,
    title VARCHAR(200),
    slug VARCHAR(220),
    start_date DATE,
    location VARCHAR(200),
    image_url VARCHAR(500),
    min_price DECIMAL(12,2)
) AS $$
DECLARE
    v_category_ids UUID[];
BEGIN
    SELECT ARRAY_AGG(category_id) INTO v_category_ids
    FROM event_categories WHERE event_id = p_event_id;

    RETURN QUERY
    SELECT 
        e.id,
        e.title,
        e.slug,
        e.start_date,
        e.location,
        e.image_url,
        MIN(t.price) as min_price
    FROM events e
    JOIN event_categories ec ON e.id = ec.event_id
    LEFT JOIN tickets t ON e.id = t.event_id AND t.deleted_at IS NULL
    WHERE e.id != p_event_id
      AND e.deleted_at IS NULL
      AND e.is_published = TRUE
      AND e.status IN ('upcoming', 'ongoing')
      AND ec.category_id = ANY(v_category_ids)
    GROUP BY e.id, e.title, e.slug, e.start_date, e.location, e.image_url
    ORDER BY e.start_date ASC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION get_recommended_events(UUID, INTEGER) IS 'Rekomendasi event berdasarkan kategori serupa';