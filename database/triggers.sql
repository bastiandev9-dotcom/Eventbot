-- ============================================================
-- EVENTBOT - TRIGGERS & FUNCTIONS (PostgreSQL Compatible)
-- FIX: DROP TRIGGER IF EXISTS sebelum CREATE TRIGGER
-- ============================================================

-- 1. AUTO-UPDATE TIMESTAMP FUNCTION
-- ============================================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION update_updated_at_column() IS 'Trigger function untuk auto-update kolom updated_at';

-- Apply to all tables with updated_at
DROP TRIGGER IF EXISTS trg_users_updated_at ON users;
CREATE TRIGGER trg_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS trg_events_updated_at ON events;
CREATE TRIGGER trg_events_updated_at
    BEFORE UPDATE ON events
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS trg_tickets_updated_at ON tickets;
CREATE TRIGGER trg_tickets_updated_at
    BEFORE UPDATE ON tickets
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS trg_registrations_updated_at ON registrations;
CREATE TRIGGER trg_registrations_updated_at
    BEFORE UPDATE ON registrations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS trg_knowledge_base_updated_at ON knowledge_base;
CREATE TRIGGER trg_knowledge_base_updated_at
    BEFORE UPDATE ON knowledge_base
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- 2. AUTO-GENERATE SLUG FROM TITLE
-- ============================================================
CREATE OR REPLACE FUNCTION generate_slug()
RETURNS TRIGGER AS $$
DECLARE
    base_slug TEXT;
    final_slug TEXT;
    counter INTEGER := 1;
BEGIN
    base_slug := lower(regexp_replace(NEW.title, '[^a-zA-Z0-9]+', '-', 'g'));
    base_slug := trim(both '-' from base_slug);
    final_slug := base_slug;

    WHILE EXISTS (
        SELECT 1 FROM events 
        WHERE slug = final_slug 
        AND id != COALESCE(NEW.id, '00000000-0000-0000-0000-000000000000'::UUID)
    ) LOOP
        final_slug := base_slug || '-' || counter;
        counter := counter + 1;
    END LOOP;

    NEW.slug := final_slug;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION generate_slug() IS 'Auto-generate URL-friendly slug dari judul event';

DROP TRIGGER IF EXISTS trg_events_generate_slug ON events;
CREATE TRIGGER trg_events_generate_slug
    BEFORE INSERT OR UPDATE OF title ON events
    FOR EACH ROW EXECUTE FUNCTION generate_slug();

-- 3. AUTO-UPDATE TICKET SOLD COUNT
-- ============================================================
CREATE OR REPLACE FUNCTION update_ticket_sold_count()
RETURNS TRIGGER AS $$
BEGIN
    -- INSERT baru: langsung tambah sold sesuai quantity
    IF TG_OP = 'INSERT' THEN
        UPDATE tickets
        SET sold = sold + NEW.quantity
        WHERE id = NEW.ticket_id;

    -- UPDATE: kurangi sold jika registrasi baru saja dibatalkan (dari status apapun)
    ELSIF TG_OP = 'UPDATE' THEN
        IF NEW.status = 'cancelled' AND OLD.status != 'cancelled' THEN
            UPDATE tickets
            SET sold = GREATEST(0, sold - OLD.quantity)
            WHERE id = NEW.ticket_id;
        END IF;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION update_ticket_sold_count() IS 'Update jumlah tiket terjual saat registrasi dibuat atau dibatalkan';

DROP TRIGGER IF EXISTS trg_registrations_update_sold ON registrations;
CREATE TRIGGER trg_registrations_update_sold
    AFTER INSERT OR UPDATE ON registrations
    FOR EACH ROW EXECUTE FUNCTION update_ticket_sold_count();

-- 4. AUTO-UPDATE CHAT SESSION ACTIVITY
-- ============================================================
CREATE OR REPLACE FUNCTION update_chat_session_activity()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE chat_sessions
    SET last_activity_at = CURRENT_TIMESTAMP
    WHERE id = NEW.session_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION update_chat_session_activity() IS 'Update last_activity saat ada pesan baru';

DROP TRIGGER IF EXISTS trg_chat_messages_activity ON chat_messages;
CREATE TRIGGER trg_chat_messages_activity
    AFTER INSERT ON chat_messages
    FOR EACH ROW EXECUTE FUNCTION update_chat_session_activity();

-- 5. SOFT DELETE PROTECTION (Utility - tidak aktifkan triggernya, hanya function)
-- ============================================================
CREATE OR REPLACE FUNCTION soft_delete_user()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE users SET deleted_at = CURRENT_TIMESTAMP WHERE id = OLD.id;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- 6. AUTO-UPDATE EVENT VIEW COUNT (Utility)
-- ============================================================
CREATE OR REPLACE FUNCTION increment_event_view()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE events SET view_count = view_count + 1 WHERE id = NEW.event_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 7. VALIDATE TICKET AVAILABILITY BEFORE INSERT REGISTRATION
-- ============================================================
CREATE OR REPLACE FUNCTION validate_ticket_before_registration()
RETURNS TRIGGER AS $$
DECLARE
    v_ticket RECORD;
BEGIN
    SELECT quantity, sold, status, max_per_order INTO v_ticket
    FROM tickets WHERE id = NEW.ticket_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Tiket tidak ditemukan';
    END IF;

    IF v_ticket.status = 'sold_out' OR (v_ticket.quantity - v_ticket.sold) < NEW.quantity THEN
        RAISE EXCEPTION 'Tiket tidak tersedia. Sisa: %', (v_ticket.quantity - v_ticket.sold);
    END IF;

    IF NEW.quantity > v_ticket.max_per_order THEN
        RAISE EXCEPTION 'Maksimal % tiket per order', v_ticket.max_per_order;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_validate_registration ON registrations;
CREATE TRIGGER trg_validate_registration
    BEFORE INSERT ON registrations
    FOR EACH ROW EXECUTE FUNCTION validate_ticket_before_registration();

-- 8. AUTO-SET PUBLISHED_AT
-- ============================================================
CREATE OR REPLACE FUNCTION set_published_at()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.is_published = TRUE AND OLD.is_published = FALSE THEN
        NEW.published_at = CURRENT_TIMESTAMP;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_events_set_published ON events;
CREATE TRIGGER trg_events_set_published
    BEFORE UPDATE ON events
    FOR EACH ROW EXECUTE FUNCTION set_published_at();

-- 9. PREVENT ORGANIZER DELETE IF HAS EVENTS
-- ============================================================
CREATE OR REPLACE FUNCTION prevent_organizer_delete()
RETURNS TRIGGER AS $$
DECLARE
    event_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO event_count FROM events 
    WHERE organizer_id = OLD.id AND deleted_at IS NULL;

    IF event_count > 0 THEN
        RAISE EXCEPTION 'User masih memiliki % event aktif. Hapus event terlebih dahulu.', event_count;
    END IF;
    RETURN OLD;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_users_prevent_delete ON users;
CREATE TRIGGER trg_users_prevent_delete
    BEFORE DELETE ON users
    FOR EACH ROW EXECUTE FUNCTION prevent_organizer_delete();

-- 10. AUTO-SET LAST LOGIN (Utility - dipanggil dari aplikasi)
-- ============================================================
CREATE OR REPLACE FUNCTION update_last_login()
RETURNS TRIGGER AS $$
BEGIN
    NEW.last_login_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;