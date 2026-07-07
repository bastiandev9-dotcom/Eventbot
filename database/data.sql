--
-- PostgreSQL database dump
--

\restrict ShPfWhUSwh3JeELSQ3d1zHd53AQGxKwCyTP9ZGOLp6Iry6DN6kk5FCRUVmf8EF2

-- Dumped from database version 17.6
-- Dumped by pg_dump version 17.6

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: pgcrypto; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS pgcrypto WITH SCHEMA public;


--
-- Name: EXTENSION pgcrypto; Type: COMMENT; Schema: -; Owner: -
--

COMMENT ON EXTENSION pgcrypto IS 'cryptographic functions';


--
-- Name: uuid-ossp; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS "uuid-ossp" WITH SCHEMA public;


--
-- Name: EXTENSION "uuid-ossp"; Type: COMMENT; Schema: -; Owner: -
--

COMMENT ON EXTENSION "uuid-ossp" IS 'generate universally unique identifiers (UUIDs)';


--
-- Name: event_status; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.event_status AS ENUM (
    'upcoming',
    'ongoing',
    'completed',
    'cancelled'
);


--
-- Name: registration_status; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.registration_status AS ENUM (
    'pending',
    'confirmed',
    'cancelled',
    'attended'
);


--
-- Name: ticket_status; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.ticket_status AS ENUM (
    'available',
    'sold_out',
    'reserved',
    'unavailable'
);


--
-- Name: user_role; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.user_role AS ENUM (
    'admin',
    'participant'
);


--
-- Name: user_status; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.user_status AS ENUM (
    'active',
    'inactive',
    'suspended'
);


--
-- Name: check_ticket_availability(uuid); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.check_ticket_availability(p_ticket_id uuid) RETURNS TABLE(available boolean, remaining integer, ticket_name character varying, event_title character varying, price numeric, max_per_order integer)
    LANGUAGE plpgsql
    AS $$
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
$$;


--
-- Name: FUNCTION check_ticket_availability(p_ticket_id uuid); Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON FUNCTION public.check_ticket_availability(p_ticket_id uuid) IS 'Cek sisa tiket dan info harga sebelum pemesanan';


--
-- Name: create_chat_session(uuid, inet, text); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.create_chat_session(p_user_id uuid DEFAULT NULL::uuid, p_ip_address inet DEFAULT NULL::inet, p_user_agent text DEFAULT NULL::text) RETURNS uuid
    LANGUAGE plpgsql
    AS $$
DECLARE
    v_session_id UUID;
BEGIN
    INSERT INTO chat_sessions (user_id, ip_address, user_agent)
    VALUES (p_user_id, p_ip_address, p_user_agent)
    RETURNING id INTO v_session_id;

    RETURN v_session_id;
END;
$$;


--
-- Name: FUNCTION create_chat_session(p_user_id uuid, p_ip_address inet, p_user_agent text); Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON FUNCTION public.create_chat_session(p_user_id uuid, p_ip_address inet, p_user_agent text) IS 'Buat sesi chat baru dan kembalikan session_id';


--
-- Name: generate_slug(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.generate_slug() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
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
$$;


--
-- Name: FUNCTION generate_slug(); Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON FUNCTION public.generate_slug() IS 'Auto-generate URL-friendly slug dari judul event';


--
-- Name: get_admin_dashboard_stats(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.get_admin_dashboard_stats() RETURNS TABLE(total_users bigint, total_events bigint, total_registrations bigint, total_revenue numeric, upcoming_events bigint, ongoing_events bigint, completed_events bigint, active_users bigint, pending_registrations bigint, confirmed_registrations bigint)
    LANGUAGE plpgsql
    AS $$
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
$$;


--
-- Name: FUNCTION get_admin_dashboard_stats(); Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON FUNCTION public.get_admin_dashboard_stats() IS 'Statistik overview untuk dashboard admin';


--
-- Name: get_chat_history(uuid, integer); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.get_chat_history(p_session_id uuid, p_limit integer DEFAULT 50) RETURNS TABLE(id uuid, role character varying, content text, intent character varying, entities_json jsonb, created_at timestamp without time zone)
    LANGUAGE plpgsql
    AS $$
BEGIN
    RETURN QUERY
    SELECT cm.id, cm.role, cm.content, cm.intent, cm.entities_json, cm.created_at
    FROM chat_messages cm
    WHERE cm.session_id = p_session_id
    ORDER BY cm.created_at ASC
    LIMIT p_limit;
END;
$$;


--
-- Name: FUNCTION get_chat_history(p_session_id uuid, p_limit integer); Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON FUNCTION public.get_chat_history(p_session_id uuid, p_limit integer) IS 'Ambil riwayat percakapan chatbot';


--
-- Name: get_event_detail(uuid); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.get_event_detail(p_event_id uuid) RETURNS TABLE(id uuid, title character varying, slug character varying, description text, short_description character varying, start_date date, end_date date, start_time time without time zone, end_time time without time zone, location character varying, location_map_url character varying, image_url character varying, banner_url character varying, capacity integer, status public.event_status, view_count integer, organizer_name character varying, organizer_id uuid, categories text[], tickets jsonb)
    LANGUAGE plpgsql
    AS $$
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
$$;


--
-- Name: FUNCTION get_event_detail(p_event_id uuid); Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON FUNCTION public.get_event_detail(p_event_id uuid) IS 'Ambil detail lengkap event termasuk tiket dan kategori';


--
-- Name: get_recommended_events(uuid, integer); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.get_recommended_events(p_event_id uuid, p_limit integer DEFAULT 3) RETURNS TABLE(id uuid, title character varying, slug character varying, start_date date, location character varying, image_url character varying, min_price numeric)
    LANGUAGE plpgsql
    AS $$
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
$$;


--
-- Name: FUNCTION get_recommended_events(p_event_id uuid, p_limit integer); Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON FUNCTION public.get_recommended_events(p_event_id uuid, p_limit integer) IS 'Rekomendasi event berdasarkan kategori serupa';


--
-- Name: get_user_stats(uuid); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.get_user_stats(p_user_id uuid) RETURNS TABLE(events_registered bigint, tickets_owned bigint, total_spent numeric, upcoming_events bigint, attended_events bigint)
    LANGUAGE plpgsql
    AS $$
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
$$;


--
-- Name: FUNCTION get_user_stats(p_user_id uuid); Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON FUNCTION public.get_user_stats(p_user_id uuid) IS 'Statistik personal untuk dashboard peserta';


--
-- Name: increment_event_view(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.increment_event_view() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    UPDATE events SET view_count = view_count + 1 WHERE id = NEW.event_id;
    RETURN NEW;
END;
$$;


--
-- Name: prevent_organizer_delete(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.prevent_organizer_delete() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
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
$$;


--
-- Name: register_to_event(uuid, uuid, integer, text); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.register_to_event(p_user_id uuid, p_ticket_id uuid, p_quantity integer DEFAULT 1, p_payment_method text DEFAULT NULL::text) RETURNS TABLE(success boolean, registration_id uuid, total_price numeric, message text)
    LANGUAGE plpgsql
    AS $$
DECLARE
    v_ticket RECORD;
    v_event_id UUID;
    v_total_price DECIMAL(12,2);
    v_registration_id UUID;
    v_remaining INTEGER;
    v_status registration_status;
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
    v_event_id    := v_ticket.event_id;

    IF v_ticket.price = 0 OR v_ticket.price IS NULL THEN
        v_status := 'confirmed'::registration_status;
    ELSE
        v_status := 'pending'::registration_status;
    END IF;

    INSERT INTO registrations (user_id, ticket_id, event_id, quantity, total_price, status, payment_method)
    VALUES (p_user_id, p_ticket_id, v_event_id, p_quantity, v_total_price, v_status, p_payment_method)
    RETURNING id INTO v_registration_id;

    RETURN QUERY SELECT TRUE, v_registration_id, v_total_price, 
        ('Pendaftaran berhasil! ' ||
         CASE WHEN v_status = 'confirmed'::registration_status
              THEN 'Tiket gratis langsung aktif.'
              ELSE 'Menunggu konfirmasi pembayaran dari admin.'
         END)::TEXT;
END;
$$;


--
-- Name: register_to_event(uuid, uuid, integer, character varying); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.register_to_event(p_user_id uuid, p_ticket_id uuid, p_quantity integer DEFAULT 1, p_payment_method character varying DEFAULT NULL::character varying) RETURNS TABLE(success boolean, registration_id uuid, total_price numeric, message text)
    LANGUAGE plpgsql
    AS $$
DECLARE
    v_ticket RECORD;
    v_event_id UUID;
    v_total_price DECIMAL(12,2);
    v_registration_id UUID;
    v_remaining INTEGER;
    v_status registration_status;
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
    v_event_id    := v_ticket.event_id;

    IF v_ticket.price = 0 OR v_ticket.price IS NULL THEN
        v_status := 'confirmed'::registration_status;
    ELSE
        v_status := 'pending'::registration_status;
    END IF;

    INSERT INTO registrations (user_id, ticket_id, event_id, quantity, total_price, status, payment_method)
    VALUES (p_user_id, p_ticket_id, v_event_id, p_quantity, v_total_price, v_status, p_payment_method)
    RETURNING id INTO v_registration_id;

    RETURN QUERY SELECT TRUE, v_registration_id, v_total_price, 
        ('Pendaftaran berhasil! ' ||
         CASE WHEN v_status = 'confirmed'::registration_status
              THEN 'Tiket gratis langsung aktif.'
              ELSE 'Menunggu konfirmasi pembayaran dari admin.'
         END)::TEXT;
END;
$$;


--
-- Name: save_chat_message(uuid, character varying, text, character varying, jsonb); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.save_chat_message(p_session_id uuid, p_role character varying, p_content text, p_intent character varying DEFAULT NULL::character varying, p_entities_json jsonb DEFAULT '{}'::jsonb) RETURNS uuid
    LANGUAGE plpgsql
    AS $$
DECLARE
    v_message_id UUID;
BEGIN
    INSERT INTO chat_messages (session_id, role, content, intent, entities_json)
    VALUES (p_session_id, p_role, p_content, p_intent, p_entities_json)
    RETURNING id INTO v_message_id;

    RETURN v_message_id;
END;
$$;


--
-- Name: FUNCTION save_chat_message(p_session_id uuid, p_role character varying, p_content text, p_intent character varying, p_entities_json jsonb); Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON FUNCTION public.save_chat_message(p_session_id uuid, p_role character varying, p_content text, p_intent character varying, p_entities_json jsonb) IS 'Simpan pesan chat ke history';


--
-- Name: search_events(text, character varying, character varying, date, date, public.event_status, numeric, numeric, integer, integer); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.search_events(p_query text DEFAULT NULL::text, p_location character varying DEFAULT NULL::character varying, p_category_slug character varying DEFAULT NULL::character varying, p_start_date date DEFAULT NULL::date, p_end_date date DEFAULT NULL::date, p_status public.event_status DEFAULT 'upcoming'::public.event_status, p_min_price numeric DEFAULT NULL::numeric, p_max_price numeric DEFAULT NULL::numeric, p_limit integer DEFAULT 20, p_offset integer DEFAULT 0) RETURNS TABLE(id uuid, title character varying, slug character varying, short_description character varying, start_date date, end_date date, location character varying, image_url character varying, status public.event_status, min_price numeric, organizer_name character varying, categories text[])
    LANGUAGE plpgsql
    AS $$
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
$$;


--
-- Name: FUNCTION search_events(p_query text, p_location character varying, p_category_slug character varying, p_start_date date, p_end_date date, p_status public.event_status, p_min_price numeric, p_max_price numeric, p_limit integer, p_offset integer); Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON FUNCTION public.search_events(p_query text, p_location character varying, p_category_slug character varying, p_start_date date, p_end_date date, p_status public.event_status, p_min_price numeric, p_max_price numeric, p_limit integer, p_offset integer) IS 'Pencarian event dengan filter kompleks: lokasi, kategori, tanggal, harga, dan full-text search';


--
-- Name: search_knowledge_base(text, integer); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.search_knowledge_base(p_query text, p_limit integer DEFAULT 3) RETURNS TABLE(id uuid, question text, answer text, category character varying, similarity_score double precision)
    LANGUAGE plpgsql
    AS $$
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
$$;


--
-- Name: FUNCTION search_knowledge_base(p_query text, p_limit integer); Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON FUNCTION public.search_knowledge_base(p_query text, p_limit integer) IS 'Cari jawaban dari knowledge base untuk chatbot';


--
-- Name: set_published_at(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.set_published_at() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    IF NEW.is_published = TRUE AND OLD.is_published = FALSE THEN
        NEW.published_at = CURRENT_TIMESTAMP;
    END IF;
    RETURN NEW;
END;
$$;


--
-- Name: soft_delete_event(uuid); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.soft_delete_event(p_event_id uuid) RETURNS boolean
    LANGUAGE plpgsql
    AS $$
BEGIN
    UPDATE events SET deleted_at = CURRENT_TIMESTAMP WHERE id = p_event_id;
    UPDATE tickets SET deleted_at = CURRENT_TIMESTAMP WHERE event_id = p_event_id;
    RETURN FOUND;
END;
$$;


--
-- Name: FUNCTION soft_delete_event(p_event_id uuid); Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON FUNCTION public.soft_delete_event(p_event_id uuid) IS 'Soft delete event dan semua tiketnya';


--
-- Name: soft_delete_user(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.soft_delete_user() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    UPDATE users SET deleted_at = CURRENT_TIMESTAMP WHERE id = OLD.id;
    RETURN NULL;
END;
$$;


--
-- Name: update_chat_session_activity(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.update_chat_session_activity() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    UPDATE chat_sessions
    SET last_activity_at = CURRENT_TIMESTAMP
    WHERE id = NEW.session_id;
    RETURN NEW;
END;
$$;


--
-- Name: FUNCTION update_chat_session_activity(); Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON FUNCTION public.update_chat_session_activity() IS 'Update last_activity saat ada pesan baru';


--
-- Name: update_last_login(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.update_last_login() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    NEW.last_login_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$;


--
-- Name: update_ticket_sold_count(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.update_ticket_sold_count() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    -- INSERT baru: langsung tambah sold sesuai quantity
    IF TG_OP = 'INSERT' THEN
        UPDATE tickets
        SET sold = sold + NEW.quantity
        WHERE id = NEW.ticket_id;

    -- UPDATE: kurangi sold jika baru dibatalkan (dari status apapun)
    ELSIF TG_OP = 'UPDATE' THEN
        -- Tiket baru saja dibatalkan (dari status aktif manapun)
        IF NEW.status = 'cancelled' AND OLD.status != 'cancelled' THEN
            UPDATE tickets
            SET sold = GREATEST(0, sold - OLD.quantity)
            WHERE id = NEW.ticket_id;
        END IF;
    END IF;

    RETURN NEW;
END;
$$;


--
-- Name: FUNCTION update_ticket_sold_count(); Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON FUNCTION public.update_ticket_sold_count() IS 'Update jumlah tiket terjual saat status registrasi berubah';


--
-- Name: update_updated_at_column(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.update_updated_at_column() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$;


--
-- Name: FUNCTION update_updated_at_column(); Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON FUNCTION public.update_updated_at_column() IS 'Trigger function untuk auto-update kolom updated_at';


--
-- Name: validate_ticket_before_registration(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.validate_ticket_before_registration() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
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
$$;


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: categories; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.categories (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    name character varying(50) NOT NULL,
    slug character varying(60) NOT NULL,
    description text,
    color character varying(7) DEFAULT '#3B82F6'::character varying,
    icon character varying(50),
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


--
-- Name: chat_messages; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.chat_messages (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    session_id uuid NOT NULL,
    role character varying(20) NOT NULL,
    content text NOT NULL,
    intent character varying(50),
    entities_json jsonb DEFAULT '{}'::jsonb,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT chat_messages_role_check CHECK (((role)::text = ANY ((ARRAY['user'::character varying, 'assistant'::character varying, 'system'::character varying])::text[])))
);


--
-- Name: TABLE chat_messages; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.chat_messages IS 'Riwayat pesan chatbot';


--
-- Name: chat_sessions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.chat_sessions (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    user_id uuid,
    session_token character varying(64) DEFAULT encode(public.gen_random_bytes(32), 'hex'::text) NOT NULL,
    ip_address inet,
    user_agent text,
    started_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    last_activity_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    ended_at timestamp without time zone,
    context_json jsonb DEFAULT '{}'::jsonb
);


--
-- Name: TABLE chat_sessions; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.chat_sessions IS 'Sesi percakapan chatbot';


--
-- Name: event_categories; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.event_categories (
    event_id uuid NOT NULL,
    category_id uuid NOT NULL
);


--
-- Name: events; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.events (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    title character varying(200) NOT NULL,
    slug character varying(220) NOT NULL,
    description text,
    short_description character varying(500),
    start_date date NOT NULL,
    end_date date NOT NULL,
    start_time time without time zone,
    end_time time without time zone,
    location character varying(200) NOT NULL,
    location_map_url character varying(500),
    organizer_id uuid NOT NULL,
    image_url character varying(500),
    banner_url character varying(500),
    capacity integer DEFAULT 0,
    status public.event_status DEFAULT 'upcoming'::public.event_status NOT NULL,
    is_published boolean DEFAULT false NOT NULL,
    published_at timestamp without time zone,
    view_count integer DEFAULT 0 NOT NULL,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    deleted_at timestamp without time zone,
    CONSTRAINT valid_event_dates CHECK ((start_date <= end_date)),
    CONSTRAINT valid_event_times CHECK (((start_time IS NULL) OR (end_time IS NULL) OR (start_time <= end_time) OR (start_date < end_date)))
);


--
-- Name: TABLE events; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.events IS 'Tabel event dan konferensi';


--
-- Name: COLUMN events.slug; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.events.slug IS 'URL-friendly identifier, auto-generated';


--
-- Name: COLUMN events.is_published; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.events.is_published IS 'Event hanya terlihat publik jika TRUE';


--
-- Name: knowledge_base; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.knowledge_base (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    category character varying(50) NOT NULL,
    question text NOT NULL,
    answer text NOT NULL,
    keywords text[],
    priority integer DEFAULT 0,
    is_active boolean DEFAULT true NOT NULL,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


--
-- Name: TABLE knowledge_base; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.knowledge_base IS 'Knowledge base untuk chatbot responses';


--
-- Name: registrations; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.registrations (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    user_id uuid NOT NULL,
    ticket_id uuid NOT NULL,
    event_id uuid NOT NULL,
    quantity integer DEFAULT 1 NOT NULL,
    total_price numeric(12,2) DEFAULT 0 NOT NULL,
    status public.registration_status DEFAULT 'pending'::public.registration_status NOT NULL,
    payment_method character varying(50),
    payment_proof_url character varying(500),
    notes text,
    checked_in_at timestamp without time zone,
    checked_in_by uuid,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    cancelled_at timestamp without time zone,
    CONSTRAINT valid_reg_quantity CHECK ((quantity >= 1)),
    CONSTRAINT valid_total_price CHECK ((total_price >= (0)::numeric))
);


--
-- Name: TABLE registrations; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.registrations IS 'Tabel pendaftaran/pemesanan tiket';


--
-- Name: system_settings; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.system_settings (
    key character varying(100) NOT NULL,
    value text NOT NULL,
    description text,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


--
-- Name: TABLE system_settings; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.system_settings IS 'Konfigurasi aplikasi dinamis';


--
-- Name: tickets; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.tickets (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    event_id uuid NOT NULL,
    name character varying(100) NOT NULL,
    description text,
    price numeric(12,2) DEFAULT 0 NOT NULL,
    quantity integer DEFAULT 0 NOT NULL,
    sold integer DEFAULT 0 NOT NULL,
    max_per_order integer DEFAULT 5,
    benefits text[],
    status public.ticket_status DEFAULT 'available'::public.ticket_status NOT NULL,
    sale_starts_at timestamp without time zone,
    sale_ends_at timestamp without time zone,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    deleted_at timestamp without time zone,
    CONSTRAINT no_over_selling CHECK ((sold <= quantity)),
    CONSTRAINT valid_max_per_order CHECK ((max_per_order >= 1)),
    CONSTRAINT valid_quantity CHECK ((quantity >= 0)),
    CONSTRAINT valid_sale_period CHECK (((sale_ends_at IS NULL) OR (sale_starts_at IS NULL) OR (sale_ends_at >= sale_starts_at))),
    CONSTRAINT valid_sold CHECK ((sold >= 0))
);


--
-- Name: TABLE tickets; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.tickets IS 'Tabel tiket per event';


--
-- Name: users; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.users (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    name character varying(100) NOT NULL,
    email character varying(100) NOT NULL,
    password_hash character varying(255) NOT NULL,
    phone character varying(20),
    avatar_url character varying(500),
    role public.user_role DEFAULT 'participant'::public.user_role NOT NULL,
    status public.user_status DEFAULT 'active'::public.user_status NOT NULL,
    email_verified_at timestamp without time zone,
    last_login_at timestamp without time zone,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    deleted_at timestamp without time zone
);


--
-- Name: TABLE users; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.users IS 'Tabel pengguna sistem EventBot';


--
-- Name: COLUMN users.deleted_at; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.users.deleted_at IS 'NULL = aktif, terisi = soft deleted';


--
-- Data for Name: categories; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.categories (id, name, slug, description, color, icon, created_at) FROM stdin;
c2cbf1fa-2592-4155-a73c-c1985221d7b1	Technology	technology	Event teknologi dan digital	#3B82F6	fa-microchip	2026-07-04 00:21:49.963762
d3d90ec3-ffb0-4e75-8cec-8df35997bb3f	Business	business	Event bisnis dan entrepreneurship	#10B981	fa-briefcase	2026-07-04 00:21:49.963762
d93ca8b9-a782-4d15-b7e6-e2814878f50f	Education	education	Workshop dan seminar edukasi	#F59E0B	fa-graduation-cap	2026-07-04 00:21:49.963762
33f87506-6d79-42ad-a47d-a982817418f3	Entertainment	entertainment	Konser dan hiburan	#EC4899	fa-music	2026-07-04 00:21:49.963762
ee288b96-bbc6-4574-9f57-910702ac8601	Social	social	Event sosial dan komunitas	#8B5CF6	fa-users	2026-07-04 00:21:49.963762
217c1b82-6d45-419c-a6ca-c3cf73b82161	Health	health	Event kesehatan dan wellness	#EF4444	fa-heartbeat	2026-07-04 00:21:49.963762
afce46ca-7591-4d59-b70b-3ef2e8d0faf9	Art	art	Event seni dan budaya	#F97316	fa-palette	2026-07-04 00:21:49.963762
d674f467-2956-4243-95c9-4290c11539f6	Teknologi	teknologi	Event teknologi dan digital	#3B82F6	fa-microchip	2026-07-07 01:01:40.585526
6bfaac29-1915-4475-9cc4-23c133102720	Bisnis	bisnis	Event bisnis dan entrepreneurship	#10B981	fa-briefcase	2026-07-07 01:01:40.585526
5f6dc821-5db0-4e2f-bedf-2263aa886315	Pendidikan	pendidikan	Workshop dan seminar edukasi	#F59E0B	fa-graduation-cap	2026-07-07 01:01:40.585526
98cfd928-5349-463c-8f48-ad1269808351	Hiburan	hiburan	Konser dan hiburan	#EC4899	fa-music	2026-07-07 01:01:40.585526
7c5462f6-9e2d-448f-8b68-4fc6c36feac7	Komunitas	komunitas	Event sosial dan komunitas	#8B5CF6	fa-users	2026-07-07 01:01:40.585526
0fdb53a1-a73d-4826-bf6f-0809027a826a	Kesehatan	kesehatan	Event kesehatan dan wellness	#EF4444	fa-heartbeat	2026-07-07 01:01:40.585526
237a4e18-1d40-4d31-a87f-a7d30b464c6e	Seni & Budaya	seni-budaya	Event seni dan budaya	#F97316	fa-palette	2026-07-07 01:01:40.585526
2f3d093c-8d47-4c48-99bd-05da9a195c78	Olahraga	olahraga	Event olahraga dan kebugaran	#06B6D4	fa-dumbbell	2026-07-07 01:01:40.585526
a916ab54-92e9-47be-b1d4-a5a8a1f70e0d	Gaming	gaming	Tournament dan event gaming	#7C3AED	fa-gamepad	2026-07-07 01:01:40.585526
\.


--
-- Data for Name: chat_messages; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.chat_messages (id, session_id, role, content, intent, entities_json, created_at) FROM stdin;
355e88d7-4286-4d5b-8eb8-5d876c964c09	a43f86d0-9d46-4924-a0bb-1cea7495cefc	user	halo	sapaan	{"query": ["halo"]}	2026-07-04 01:55:30.950013
75251de9-675e-4b85-800e-8cad661e5d80	a43f86d0-9d46-4924-a0bb-1cea7495cefc	assistant	Halo! Selamat datang di EventBot! 👋\n\nSaya bisa membantu Anda dengan:\n🔍 Cari event\n📋 Lihat daftar event\n🎫 Daftar tiket\n❓ Bantuan\n\nAda yang bisa saya bantu?	sapaan	\N	2026-07-04 01:55:30.954288
c14f270f-593f-4a51-9a12-301411bc47a5	a43f86d0-9d46-4924-a0bb-1cea7495cefc	user	cari event	cari_event	\N	2026-07-04 01:55:30.957661
8e441749-cd94-4e66-85ac-9c3a68606136	a43f86d0-9d46-4924-a0bb-1cea7495cefc	assistant	🎪 **Event Ditemukan**\n\n**1. Tech Conference 2025**\n📅 2025-12-15 | 📍 Jakarta Convention Center\n💰 Rp 350,000\n\n**2. Digital Marketing Masterclass**\n📅 2025-11-25 | 📍 Online via Zoom\n💰 Rp 150,000\n\n**3. Startup Summit Indonesia 2026**\n📅 2026-01-10 | 📍 Bali Nusa Dua Convention Center\n💰 Rp 500,000\n\n**4. AI Workshop: Deep Learning Fundamentals**\n📅 2025-12-20 | 📍 Bandung Institute of Technology\n💰 Rp 350,000\n\n**5. Yoga & Wellness Retreat**\n📅 2025-11-30 | 📍 Dusun Bambu, Bandung\n💰 Rp 400,000\n\n	cari_event	\N	2026-07-04 01:55:30.959221
b1ee5a44-226a-4c13-86e6-dbf37303e364	a43f86d0-9d46-4924-a0bb-1cea7495cefc	user	bantuan	tanya_bantuan	{"query": ["bantuan"]}	2026-07-04 01:55:30.96106
28da2b3f-da3d-4881-8ef0-24704ac9a437	a43f86d0-9d46-4924-a0bb-1cea7495cefc	assistant	📚 **Menu Bantuan EventBot**\n\nBerikut yang bisa saya bantu:\n\n**🔍 Cari Event**\n• 'Cari event di Jakarta'\n• 'Event teknologi bulan ini'\n• 'Event gratis'\n\n**📋 Lihat Event**\n• 'Lihat semua event'\n• 'Event yang akan datang'\n\n**🎫 Tiket & Booking**\n• 'Daftar tiket [nama event]'\n• 'Lihat tiket saya'\n\n**👤 Akun**\n• 'Profil saya'\n• 'Jadwal event saya'	tanya_bantuan	\N	2026-07-04 01:55:30.962438
d34b5361-bd37-4859-98b6-991925c2f156	2332a02f-8d08-49e7-bbbf-85d4a923d9be	user	halo	sapaan	{"query": ["halo"]}	2026-07-04 01:56:11.547928
daf3758a-6a0d-4e62-b604-a3eb77b963be	2332a02f-8d08-49e7-bbbf-85d4a923d9be	assistant	Halo! Selamat datang di EventBot! 👋\n\nSaya bisa membantu Anda dengan:\n🔍 Cari event\n📋 Lihat daftar event\n🎫 Daftar tiket\n❓ Bantuan\n\nAda yang bisa saya bantu?	sapaan	\N	2026-07-04 01:56:11.549687
c4ae8417-f259-47af-bdd4-8ade72d44884	2332a02f-8d08-49e7-bbbf-85d4a923d9be	user	cari event	cari_event	\N	2026-07-04 01:56:11.552555
c309e20c-d21a-478d-8e2f-f7fb1e39a927	2332a02f-8d08-49e7-bbbf-85d4a923d9be	assistant	🎪 **Event Ditemukan**\n\n**1. Tech Conference 2025**\n📅 2025-12-15 | 📍 Jakarta Convention Center\n💰 Rp 350,000\n\n**2. Digital Marketing Masterclass**\n📅 2025-11-25 | 📍 Online via Zoom\n💰 Rp 150,000\n\n**3. Startup Summit Indonesia 2026**\n📅 2026-01-10 | 📍 Bali Nusa Dua Convention Center\n💰 Rp 500,000\n\n**4. AI Workshop: Deep Learning Fundamentals**\n📅 2025-12-20 | 📍 Bandung Institute of Technology\n💰 Rp 350,000\n\n**5. Yoga & Wellness Retreat**\n📅 2025-11-30 | 📍 Dusun Bambu, Bandung\n💰 Rp 400,000\n\n	cari_event	\N	2026-07-04 01:56:11.553952
0a29760c-7e73-4081-8687-885e32a233f3	2332a02f-8d08-49e7-bbbf-85d4a923d9be	user	bantuan	tanya_bantuan	{"query": ["bantuan"]}	2026-07-04 01:56:11.555708
c80a1024-82d3-41d7-87fc-883234dbdb5b	2332a02f-8d08-49e7-bbbf-85d4a923d9be	assistant	📚 **Menu Bantuan EventBot**\n\nBerikut yang bisa saya bantu:\n\n**🔍 Cari Event**\n• 'Cari event di Jakarta'\n• 'Event teknologi bulan ini'\n• 'Event gratis'\n\n**📋 Lihat Event**\n• 'Lihat semua event'\n• 'Event yang akan datang'\n\n**🎫 Tiket & Booking**\n• 'Daftar tiket [nama event]'\n• 'Lihat tiket saya'\n\n**👤 Akun**\n• 'Profil saya'\n• 'Jadwal event saya'	tanya_bantuan	\N	2026-07-04 01:56:11.556923
9287c32a-bb31-4475-9948-869f2e2ef310	7711478f-1610-45a6-ab82-c1e78379e2e8	user	halo	sapaan	{"query": ["halo"]}	2026-07-04 01:59:57.474656
8e6618c8-9a54-40a7-9656-806d5a2f8b50	7711478f-1610-45a6-ab82-c1e78379e2e8	assistant	Halo! Selamat datang di EventBot! 👋\n\nSaya bisa membantu Anda dengan:\n🔍 Cari event\n📋 Lihat daftar event\n🎫 Daftar tiket\n❓ Bantuan\n\nAda yang bisa saya bantu?	sapaan	\N	2026-07-04 01:59:57.476951
84220d11-af57-407b-9575-b92500d6edf4	7711478f-1610-45a6-ab82-c1e78379e2e8	user	cari event	cari_event	\N	2026-07-04 01:59:57.480091
a428dc5d-9692-4026-857e-0cb236519717	7711478f-1610-45a6-ab82-c1e78379e2e8	assistant	🎪 **Event Ditemukan**\n\n**1. Tech Conference 2025**\n📅 2025-12-15 | 📍 Jakarta Convention Center\n💰 Rp 350,000\n\n**2. Digital Marketing Masterclass**\n📅 2025-11-25 | 📍 Online via Zoom\n💰 Rp 150,000\n\n**3. Startup Summit Indonesia 2026**\n📅 2026-01-10 | 📍 Bali Nusa Dua Convention Center\n💰 Rp 500,000\n\n**4. AI Workshop: Deep Learning Fundamentals**\n📅 2025-12-20 | 📍 Bandung Institute of Technology\n💰 Rp 350,000\n\n**5. Yoga & Wellness Retreat**\n📅 2025-11-30 | 📍 Dusun Bambu, Bandung\n💰 Rp 400,000\n\n	cari_event	\N	2026-07-04 01:59:57.48169
780dda85-b7d7-49f0-8a21-c4de88e220ef	7711478f-1610-45a6-ab82-c1e78379e2e8	user	bantuan	tanya_bantuan	{"query": ["bantuan"]}	2026-07-04 01:59:57.483519
81dd02ea-f10b-4560-a011-95d4888f7293	7711478f-1610-45a6-ab82-c1e78379e2e8	assistant	📚 **Menu Bantuan EventBot**\n\nBerikut yang bisa saya bantu:\n\n**🔍 Cari Event**\n• 'Cari event di Jakarta'\n• 'Event teknologi bulan ini'\n• 'Event gratis'\n\n**📋 Lihat Event**\n• 'Lihat semua event'\n• 'Event yang akan datang'\n\n**🎫 Tiket & Booking**\n• 'Daftar tiket [nama event]'\n• 'Lihat tiket saya'\n\n**👤 Akun**\n• 'Profil saya'\n• 'Jadwal event saya'	tanya_bantuan	\N	2026-07-04 01:59:57.485217
36880391-b50e-42de-af56-bf1bb9717c8a	108134ad-e54f-4ce2-8158-b5f9a5de54f2	user	halo	sapaan	{"query": ["halo"]}	2026-07-04 02:00:22.679631
4de30e86-b044-4132-a3d2-193b95a97519	108134ad-e54f-4ce2-8158-b5f9a5de54f2	assistant	Halo! Selamat datang di EventBot! 👋\n\nSaya bisa membantu Anda dengan:\n🔍 Cari event\n📋 Lihat daftar event\n🎫 Daftar tiket\n❓ Bantuan\n\nAda yang bisa saya bantu?	sapaan	\N	2026-07-04 02:00:22.681634
2f31ef67-9e16-464d-a505-6e0d1ae56230	108134ad-e54f-4ce2-8158-b5f9a5de54f2	user	cari event	cari_event	\N	2026-07-04 02:00:22.684727
43db156b-9a64-4dbb-8109-478052d65935	108134ad-e54f-4ce2-8158-b5f9a5de54f2	assistant	🎪 **Event Ditemukan**\n\n**1. Tech Conference 2025**\n📅 2025-12-15 | 📍 Jakarta Convention Center\n💰 Rp 350,000\n\n**2. Digital Marketing Masterclass**\n📅 2025-11-25 | 📍 Online via Zoom\n💰 Rp 150,000\n\n**3. Startup Summit Indonesia 2026**\n📅 2026-01-10 | 📍 Bali Nusa Dua Convention Center\n💰 Rp 500,000\n\n**4. AI Workshop: Deep Learning Fundamentals**\n📅 2025-12-20 | 📍 Bandung Institute of Technology\n💰 Rp 350,000\n\n**5. Yoga & Wellness Retreat**\n📅 2025-11-30 | 📍 Dusun Bambu, Bandung\n💰 Rp 400,000\n\n	cari_event	\N	2026-07-04 02:00:22.686301
b072e88f-bd44-4f65-bee8-329e7ea77b79	108134ad-e54f-4ce2-8158-b5f9a5de54f2	user	bantuan	tanya_bantuan	{"query": ["bantuan"]}	2026-07-04 02:00:22.688408
b2c8044b-e035-486d-9593-23572a7b9f81	108134ad-e54f-4ce2-8158-b5f9a5de54f2	assistant	📚 **Menu Bantuan EventBot**\n\nBerikut yang bisa saya bantu:\n\n**🔍 Cari Event**\n• 'Cari event di Jakarta'\n• 'Event teknologi bulan ini'\n• 'Event gratis'\n\n**📋 Lihat Event**\n• 'Lihat semua event'\n• 'Event yang akan datang'\n\n**🎫 Tiket & Booking**\n• 'Daftar tiket [nama event]'\n• 'Lihat tiket saya'\n\n**👤 Akun**\n• 'Profil saya'\n• 'Jadwal event saya'	tanya_bantuan	\N	2026-07-04 02:00:22.689805
22ded4b3-d1b4-4768-8893-8b8404f9112e	f0b26282-055f-430d-98ec-b93b507530de	user	halo	sapaan	{"query": ["halo"]}	2026-07-04 02:00:43.249824
f5dbea3c-f19b-4260-97aa-36197f0c9f94	f0b26282-055f-430d-98ec-b93b507530de	assistant	Halo! Selamat datang di EventBot! 👋\n\nSaya bisa membantu Anda dengan:\n🔍 Cari event\n📋 Lihat daftar event\n🎫 Daftar tiket\n❓ Bantuan\n\nAda yang bisa saya bantu?	sapaan	\N	2026-07-04 02:00:43.251808
bd53ea44-b3ac-4cc6-95cc-f4e86659783e	f0b26282-055f-430d-98ec-b93b507530de	user	cari event	cari_event	\N	2026-07-04 02:00:43.254882
27d39589-5a4d-4f81-8d20-d6d49eaebe1b	f0b26282-055f-430d-98ec-b93b507530de	assistant	🎪 **Event Ditemukan**\n\n**1. Tech Conference 2025**\n📅 2025-12-15 | 📍 Jakarta Convention Center\n💰 Rp 350,000\n\n**2. Digital Marketing Masterclass**\n📅 2025-11-25 | 📍 Online via Zoom\n💰 Rp 150,000\n\n**3. Startup Summit Indonesia 2026**\n📅 2026-01-10 | 📍 Bali Nusa Dua Convention Center\n💰 Rp 500,000\n\n**4. AI Workshop: Deep Learning Fundamentals**\n📅 2025-12-20 | 📍 Bandung Institute of Technology\n💰 Rp 350,000\n\n**5. Yoga & Wellness Retreat**\n📅 2025-11-30 | 📍 Dusun Bambu, Bandung\n💰 Rp 400,000\n\n	cari_event	\N	2026-07-04 02:00:43.256293
ee7b48dc-e745-4ed1-9f05-4fae11ab4dd4	f0b26282-055f-430d-98ec-b93b507530de	user	bantuan	tanya_bantuan	{"query": ["bantuan"]}	2026-07-04 02:00:43.25804
b9ad4f91-1cd9-4d1d-87cc-f8aa126d5b43	f0b26282-055f-430d-98ec-b93b507530de	assistant	📚 **Menu Bantuan EventBot**\n\nBerikut yang bisa saya bantu:\n\n**🔍 Cari Event**\n• 'Cari event di Jakarta'\n• 'Event teknologi bulan ini'\n• 'Event gratis'\n\n**📋 Lihat Event**\n• 'Lihat semua event'\n• 'Event yang akan datang'\n\n**🎫 Tiket & Booking**\n• 'Daftar tiket [nama event]'\n• 'Lihat tiket saya'\n\n**👤 Akun**\n• 'Profil saya'\n• 'Jadwal event saya'	tanya_bantuan	\N	2026-07-04 02:00:43.259478
03a03300-0772-479d-b62a-c67bdcdc2f9b	9bc5d750-bd21-4336-97dd-a74c689bcebb	user	halo	sapaan	{"query": ["halo"]}	2026-07-04 02:01:18.316581
1d6a2539-fe74-4650-91a9-83effccf6098	9bc5d750-bd21-4336-97dd-a74c689bcebb	assistant	Halo! Selamat datang di EventBot! 👋\n\nSaya bisa membantu Anda dengan:\n🔍 Cari event\n📋 Lihat daftar event\n🎫 Daftar tiket\n❓ Bantuan\n\nAda yang bisa saya bantu?	sapaan	\N	2026-07-04 02:01:18.344421
8596f65d-cd0f-452f-8dd8-b1751215ecaf	9bc5d750-bd21-4336-97dd-a74c689bcebb	user	cari event	cari_event	\N	2026-07-04 02:01:18.35018
27391c9e-e29b-45fa-a9e5-00f8d1b57195	9bc5d750-bd21-4336-97dd-a74c689bcebb	assistant	🎪 **Event Ditemukan**\n\n**1. Tech Conference 2025**\n📅 2025-12-15 | 📍 Jakarta Convention Center\n💰 Rp 350,000\n\n**2. Digital Marketing Masterclass**\n📅 2025-11-25 | 📍 Online via Zoom\n💰 Rp 150,000\n\n**3. Startup Summit Indonesia 2026**\n📅 2026-01-10 | 📍 Bali Nusa Dua Convention Center\n💰 Rp 500,000\n\n**4. AI Workshop: Deep Learning Fundamentals**\n📅 2025-12-20 | 📍 Bandung Institute of Technology\n💰 Rp 350,000\n\n**5. Yoga & Wellness Retreat**\n📅 2025-11-30 | 📍 Dusun Bambu, Bandung\n💰 Rp 400,000\n\n	cari_event	\N	2026-07-04 02:01:18.35342
27da2ee3-ab60-4c38-93c7-b92cab1d385a	9bc5d750-bd21-4336-97dd-a74c689bcebb	user	bantuan	tanya_bantuan	{"query": ["bantuan"]}	2026-07-04 02:01:18.356888
f6063c25-c7ba-4f3b-bfa9-332efad57e97	9bc5d750-bd21-4336-97dd-a74c689bcebb	assistant	📚 **Menu Bantuan EventBot**\n\nBerikut yang bisa saya bantu:\n\n**🔍 Cari Event**\n• 'Cari event di Jakarta'\n• 'Event teknologi bulan ini'\n• 'Event gratis'\n\n**📋 Lihat Event**\n• 'Lihat semua event'\n• 'Event yang akan datang'\n\n**🎫 Tiket & Booking**\n• 'Daftar tiket [nama event]'\n• 'Lihat tiket saya'\n\n**👤 Akun**\n• 'Profil saya'\n• 'Jadwal event saya'	tanya_bantuan	\N	2026-07-04 02:01:18.35979
855536ae-b4b9-4943-b439-a7c5f1ae6e6d	4de9abac-0f89-4458-b380-a536a6aa722d	user	halo	sapaan	{"query": ["halo"]}	2026-07-04 02:01:33.324558
50b56f3b-1d1b-4b3a-9a3b-e78e9a8590fa	4de9abac-0f89-4458-b380-a536a6aa722d	assistant	Halo! Selamat datang di EventBot! 👋\n\nSaya bisa membantu Anda dengan:\n🔍 Cari event\n📋 Lihat daftar event\n🎫 Daftar tiket\n❓ Bantuan\n\nAda yang bisa saya bantu?	sapaan	\N	2026-07-04 02:01:33.326462
0bc163df-2839-4253-82a2-b1ea82e43182	4de9abac-0f89-4458-b380-a536a6aa722d	user	cari event	cari_event	\N	2026-07-04 02:01:33.329623
8493c531-02b4-4052-bb07-c2def2d85660	4de9abac-0f89-4458-b380-a536a6aa722d	assistant	🎪 **Event Ditemukan**\n\n**1. Tech Conference 2025**\n📅 2025-12-15 | 📍 Jakarta Convention Center\n💰 Rp 350,000\n\n**2. Digital Marketing Masterclass**\n📅 2025-11-25 | 📍 Online via Zoom\n💰 Rp 150,000\n\n**3. Startup Summit Indonesia 2026**\n📅 2026-01-10 | 📍 Bali Nusa Dua Convention Center\n💰 Rp 500,000\n\n**4. AI Workshop: Deep Learning Fundamentals**\n📅 2025-12-20 | 📍 Bandung Institute of Technology\n💰 Rp 350,000\n\n**5. Yoga & Wellness Retreat**\n📅 2025-11-30 | 📍 Dusun Bambu, Bandung\n💰 Rp 400,000\n\n	cari_event	\N	2026-07-04 02:01:33.3313
a2dcf0b8-fa56-42b6-8a6c-ed81257a706e	4de9abac-0f89-4458-b380-a536a6aa722d	user	bantuan	tanya_bantuan	{"query": ["bantuan"]}	2026-07-04 02:01:33.333137
4baf3e91-7653-417d-9a1f-a1c2f73f5c4c	4de9abac-0f89-4458-b380-a536a6aa722d	assistant	📚 **Menu Bantuan EventBot**\n\nBerikut yang bisa saya bantu:\n\n**🔍 Cari Event**\n• 'Cari event di Jakarta'\n• 'Event teknologi bulan ini'\n• 'Event gratis'\n\n**📋 Lihat Event**\n• 'Lihat semua event'\n• 'Event yang akan datang'\n\n**🎫 Tiket & Booking**\n• 'Daftar tiket [nama event]'\n• 'Lihat tiket saya'\n\n**👤 Akun**\n• 'Profil saya'\n• 'Jadwal event saya'	tanya_bantuan	\N	2026-07-04 02:01:33.334422
7bb71d2b-3fdf-450a-8670-87ffc54b4e34	25e6ea1c-428c-4efb-82b6-6f315be1bb2c	user	halo	sapaan	{"query": ["halo"]}	2026-07-05 05:08:59.366831
f289a287-80e5-4464-8e95-7b39a21646d7	25e6ea1c-428c-4efb-82b6-6f315be1bb2c	assistant	Halo! Selamat datang di EventBot! 👋\n\nSaya bisa membantu Anda dengan:\n🔍 Cari event\n📋 Lihat daftar event\n🎫 Daftar tiket\n❓ Bantuan\n\nAda yang bisa saya bantu?	sapaan	\N	2026-07-05 05:08:59.391278
af4dc7f3-7b48-4783-89c6-fc5a7d71a74c	25e6ea1c-428c-4efb-82b6-6f315be1bb2c	user	cari event	cari_event	\N	2026-07-05 05:08:59.396106
aec0f4f0-4416-4b46-bbbe-6a5ccef4f923	25e6ea1c-428c-4efb-82b6-6f315be1bb2c	assistant	🎪 **Event Ditemukan**\n\n**1. Tech Conference 2025**\n📅 2025-12-15 | 📍 Jakarta Convention Center\n💰 Rp 350,000\n\n**2. Digital Marketing Masterclass**\n📅 2025-11-25 | 📍 Online via Zoom\n💰 Rp 150,000\n\n**3. Startup Summit Indonesia 2026**\n📅 2026-01-10 | 📍 Bali Nusa Dua Convention Center\n💰 Rp 500,000\n\n**4. AI Workshop: Deep Learning Fundamentals**\n📅 2025-12-20 | 📍 Bandung Institute of Technology\n💰 Rp 350,000\n\n**5. Yoga & Wellness Retreat**\n📅 2025-11-30 | 📍 Dusun Bambu, Bandung\n💰 Rp 400,000\n\n	cari_event	\N	2026-07-05 05:08:59.397857
005b7b82-d86f-4a2d-827a-ce2b019d8519	25e6ea1c-428c-4efb-82b6-6f315be1bb2c	user	bantuan	tanya_bantuan	{"query": ["bantuan"]}	2026-07-05 05:08:59.399896
36530226-7015-45b8-b87e-5f78151dcf95	25e6ea1c-428c-4efb-82b6-6f315be1bb2c	assistant	📚 **Menu Bantuan EventBot**\n\nBerikut yang bisa saya bantu:\n\n**🔍 Cari Event**\n• 'Cari event di Jakarta'\n• 'Event teknologi bulan ini'\n• 'Event gratis'\n\n**📋 Lihat Event**\n• 'Lihat semua event'\n• 'Event yang akan datang'\n\n**🎫 Tiket & Booking**\n• 'Daftar tiket [nama event]'\n• 'Lihat tiket saya'\n\n**👤 Akun**\n• 'Profil saya'\n• 'Jadwal event saya'	tanya_bantuan	\N	2026-07-05 05:08:59.401681
54e2c7e0-a340-493c-aa26-45e7b0aa41a4	76d04d86-50ff-420e-aea4-2e4ff104eb05	user	halo	sapaan	{"query": ["halo"]}	2026-07-05 05:11:10.771707
2a1af83f-8ff1-4f67-a60c-c9c36473d022	76d04d86-50ff-420e-aea4-2e4ff104eb05	assistant	Halo! Selamat datang di EventBot! 👋\n\nSaya bisa membantu Anda dengan:\n🔍 Cari event\n📋 Lihat daftar event\n🎫 Daftar tiket\n❓ Bantuan\n\nAda yang bisa saya bantu?	sapaan	\N	2026-07-05 05:11:10.774604
b64af863-e06a-46a2-95ac-a9ed106d6321	76d04d86-50ff-420e-aea4-2e4ff104eb05	user	cari event	cari_event	\N	2026-07-05 05:11:10.778644
f47a81d1-691c-49bd-bdcc-1be9399e3277	76d04d86-50ff-420e-aea4-2e4ff104eb05	assistant	🎪 **Event Ditemukan**\n\n**1. Tech Conference 2025**\n📅 2025-12-15 | 📍 Jakarta Convention Center\n💰 Rp 350,000\n\n**2. Digital Marketing Masterclass**\n📅 2025-11-25 | 📍 Online via Zoom\n💰 Rp 150,000\n\n**3. Startup Summit Indonesia 2026**\n📅 2026-01-10 | 📍 Bali Nusa Dua Convention Center\n💰 Rp 500,000\n\n**4. AI Workshop: Deep Learning Fundamentals**\n📅 2025-12-20 | 📍 Bandung Institute of Technology\n💰 Rp 350,000\n\n**5. Yoga & Wellness Retreat**\n📅 2025-11-30 | 📍 Dusun Bambu, Bandung\n💰 Rp 400,000\n\n	cari_event	\N	2026-07-05 05:11:10.780469
8b333e6e-de1c-4b14-b095-78181be4e0cc	76d04d86-50ff-420e-aea4-2e4ff104eb05	user	bantuan	tanya_bantuan	{"query": ["bantuan"]}	2026-07-05 05:11:10.782627
6eda65e1-e85e-4a1a-8c04-535f24bf368d	76d04d86-50ff-420e-aea4-2e4ff104eb05	assistant	📚 **Menu Bantuan EventBot**\n\nBerikut yang bisa saya bantu:\n\n**🔍 Cari Event**\n• 'Cari event di Jakarta'\n• 'Event teknologi bulan ini'\n• 'Event gratis'\n\n**📋 Lihat Event**\n• 'Lihat semua event'\n• 'Event yang akan datang'\n\n**🎫 Tiket & Booking**\n• 'Daftar tiket [nama event]'\n• 'Lihat tiket saya'\n\n**👤 Akun**\n• 'Profil saya'\n• 'Jadwal event saya'	tanya_bantuan	\N	2026-07-05 05:11:10.784241
0fcb4da3-ab7a-4fee-9e11-1c4b38b28f5a	792cac3a-20bf-4c06-9f0f-893305ae74c8	user	halo	sapaan	{"query": ["halo"]}	2026-07-05 05:11:43.857021
93f191c8-21a9-41e2-bdc2-5827855f7a6d	792cac3a-20bf-4c06-9f0f-893305ae74c8	assistant	Halo! Selamat datang di EventBot! 👋\n\nSaya bisa membantu Anda dengan:\n🔍 Cari event\n📋 Lihat daftar event\n🎫 Daftar tiket\n❓ Bantuan\n\nAda yang bisa saya bantu?	sapaan	\N	2026-07-05 05:11:43.858895
7ef5ca2e-0072-4164-931a-5344a69ea71e	792cac3a-20bf-4c06-9f0f-893305ae74c8	user	cari event	cari_event	\N	2026-07-05 05:11:43.862349
1fd8bafb-329f-4948-a754-b167279908d9	47c5713d-0cae-453e-aa20-264856ed8750	user	🔐 Login	tidak_dikenal	{"query": ["🔐 login"]}	2026-07-06 04:33:23.769405
ec349934-6402-44d5-a579-e8809c335347	47c5713d-0cae-453e-aa20-264856ed8750	assistant	Maaf, saya tidak mengerti. Coba ketik 'bantuan' untuk melihat fitur yang tersedia.	tidak_dikenal	\N	2026-07-06 04:33:23.773324
b8019066-0075-4563-84e6-f6ce63defa0b	792cac3a-20bf-4c06-9f0f-893305ae74c8	assistant	🎪 **Event Ditemukan**\n\n**1. Tech Conference 2025**\n📅 2025-12-15 | 📍 Jakarta Convention Center\n💰 Rp 350,000\n\n**2. Digital Marketing Masterclass**\n📅 2025-11-25 | 📍 Online via Zoom\n💰 Rp 150,000\n\n**3. Startup Summit Indonesia 2026**\n📅 2026-01-10 | 📍 Bali Nusa Dua Convention Center\n💰 Rp 500,000\n\n**4. AI Workshop: Deep Learning Fundamentals**\n📅 2025-12-20 | 📍 Bandung Institute of Technology\n💰 Rp 350,000\n\n**5. Yoga & Wellness Retreat**\n📅 2025-11-30 | 📍 Dusun Bambu, Bandung\n💰 Rp 400,000\n\n	cari_event	\N	2026-07-05 05:11:43.863889
d906709a-0ed3-4790-9a40-21aa44e10970	792cac3a-20bf-4c06-9f0f-893305ae74c8	user	bantuan	tanya_bantuan	{"query": ["bantuan"]}	2026-07-05 05:11:43.866345
6d6988e1-5949-4a0f-be67-9fdacb3d9292	792cac3a-20bf-4c06-9f0f-893305ae74c8	assistant	📚 **Menu Bantuan EventBot**\n\nBerikut yang bisa saya bantu:\n\n**🔍 Cari Event**\n• 'Cari event di Jakarta'\n• 'Event teknologi bulan ini'\n• 'Event gratis'\n\n**📋 Lihat Event**\n• 'Lihat semua event'\n• 'Event yang akan datang'\n\n**🎫 Tiket & Booking**\n• 'Daftar tiket [nama event]'\n• 'Lihat tiket saya'\n\n**👤 Akun**\n• 'Profil saya'\n• 'Jadwal event saya'	tanya_bantuan	\N	2026-07-05 05:11:43.867707
5a523edf-a616-490d-a7c1-70dfadfae324	b7de0fa3-f25c-4546-937f-135270c45393	user	halo	sapaan	{"query": ["halo"]}	2026-07-05 05:12:11.895559
26d9861a-9466-494d-8cf1-f061be61cac2	b7de0fa3-f25c-4546-937f-135270c45393	assistant	Halo! Selamat datang di EventBot! 👋\n\nSaya bisa membantu Anda dengan:\n🔍 Cari event\n📋 Lihat daftar event\n🎫 Daftar tiket\n❓ Bantuan\n\nAda yang bisa saya bantu?	sapaan	\N	2026-07-05 05:12:11.897393
a9558a42-c5fc-424d-91d7-23cc2070c638	b7de0fa3-f25c-4546-937f-135270c45393	user	cari event	cari_event	\N	2026-07-05 05:12:11.900279
322cc228-f925-44d7-b379-44a8d8c8a7b9	b7de0fa3-f25c-4546-937f-135270c45393	assistant	🎪 **Event Ditemukan**\n\n**1. Tech Conference 2025**\n📅 2025-12-15 | 📍 Jakarta Convention Center\n💰 Rp 350,000\n\n**2. Digital Marketing Masterclass**\n📅 2025-11-25 | 📍 Online via Zoom\n💰 Rp 150,000\n\n**3. Startup Summit Indonesia 2026**\n📅 2026-01-10 | 📍 Bali Nusa Dua Convention Center\n💰 Rp 500,000\n\n**4. AI Workshop: Deep Learning Fundamentals**\n📅 2025-12-20 | 📍 Bandung Institute of Technology\n💰 Rp 350,000\n\n**5. Yoga & Wellness Retreat**\n📅 2025-11-30 | 📍 Dusun Bambu, Bandung\n💰 Rp 400,000\n\n	cari_event	\N	2026-07-05 05:12:11.901577
1dfb1257-f729-4f62-9f9e-a6bfad0ee18f	b7de0fa3-f25c-4546-937f-135270c45393	user	bantuan	tanya_bantuan	{"query": ["bantuan"]}	2026-07-05 05:12:11.903353
3070a79b-7874-40c9-9d0a-f257b8b4ce64	b7de0fa3-f25c-4546-937f-135270c45393	assistant	📚 **Menu Bantuan EventBot**\n\nBerikut yang bisa saya bantu:\n\n**🔍 Cari Event**\n• 'Cari event di Jakarta'\n• 'Event teknologi bulan ini'\n• 'Event gratis'\n\n**📋 Lihat Event**\n• 'Lihat semua event'\n• 'Event yang akan datang'\n\n**🎫 Tiket & Booking**\n• 'Daftar tiket [nama event]'\n• 'Lihat tiket saya'\n\n**👤 Akun**\n• 'Profil saya'\n• 'Jadwal event saya'	tanya_bantuan	\N	2026-07-05 05:12:11.904865
6094c43e-6edd-48a4-8cea-dc7936c038be	c103c788-cbf9-43d4-87fc-119e663c8a7b	user	halo	sapaan	{"query": ["halo"]}	2026-07-05 05:49:23.692564
e9393251-b996-440f-83c9-25c32dec3979	c103c788-cbf9-43d4-87fc-119e663c8a7b	assistant	Halo! Selamat datang di EventBot! 👋\n\nSaya bisa membantu Anda dengan:\n🔍 Cari event\n📋 Lihat daftar event\n🎫 Daftar tiket\n❓ Bantuan\n\nAda yang bisa saya bantu?	sapaan	\N	2026-07-05 05:49:23.719714
e8e57881-0e5b-4e0d-99b0-62e973b99355	c103c788-cbf9-43d4-87fc-119e663c8a7b	user	cari event	cari_event	\N	2026-07-05 05:49:23.723963
28f68c30-724b-4e87-bb9f-637cdcbf193a	c103c788-cbf9-43d4-87fc-119e663c8a7b	assistant	🎪 **Event Ditemukan**\n\n**1. Tech Conference 2025**\n📅 2025-12-15 | 📍 Jakarta Convention Center\n💰 Rp 350,000\n\n**2. Digital Marketing Masterclass**\n📅 2025-11-25 | 📍 Online via Zoom\n💰 Rp 150,000\n\n**3. Startup Summit Indonesia 2026**\n📅 2026-01-10 | 📍 Bali Nusa Dua Convention Center\n💰 Rp 500,000\n\n**4. AI Workshop: Deep Learning Fundamentals**\n📅 2025-12-20 | 📍 Bandung Institute of Technology\n💰 Rp 350,000\n\n**5. Yoga & Wellness Retreat**\n📅 2025-11-30 | 📍 Dusun Bambu, Bandung\n💰 Rp 400,000\n\n	cari_event	\N	2026-07-05 05:49:23.725454
ee03cb0e-7fc0-4ce8-9335-8946c9838e39	c103c788-cbf9-43d4-87fc-119e663c8a7b	user	bantuan	tanya_bantuan	{"query": ["bantuan"]}	2026-07-05 05:49:23.727369
fd1e5a4a-df37-45f0-b4ab-0f04cef953e8	c103c788-cbf9-43d4-87fc-119e663c8a7b	assistant	📚 **Menu Bantuan EventBot**\n\nBerikut yang bisa saya bantu:\n\n**🔍 Cari Event**\n• 'Cari event di Jakarta'\n• 'Event teknologi bulan ini'\n• 'Event gratis'\n\n**📋 Lihat Event**\n• 'Lihat semua event'\n• 'Event yang akan datang'\n\n**🎫 Tiket & Booking**\n• 'Daftar tiket [nama event]'\n• 'Lihat tiket saya'\n\n**👤 Akun**\n• 'Profil saya'\n• 'Jadwal event saya'	tanya_bantuan	\N	2026-07-05 05:49:23.728889
cae38be3-64da-459e-ad89-72826a4f2dac	3226e36a-a363-45d8-89b2-ad9f15fb7c7c	user	halo	sapaan	{"query": ["halo"]}	2026-07-05 05:54:16.011128
823f9855-5d09-4326-a0cd-b90df8140325	3226e36a-a363-45d8-89b2-ad9f15fb7c7c	assistant	Halo! Selamat datang di EventBot! 👋\n\nSaya bisa membantu Anda dengan:\n🔍 Cari event\n📋 Lihat daftar event\n🎫 Daftar tiket\n❓ Bantuan\n\nAda yang bisa saya bantu?	sapaan	\N	2026-07-05 05:54:16.013305
20bc9414-4394-475c-8385-215ba84d2d34	3226e36a-a363-45d8-89b2-ad9f15fb7c7c	user	cari event	cari_event	\N	2026-07-05 05:54:16.016338
b9d7263c-24af-4c64-9798-9159f40a19d1	3226e36a-a363-45d8-89b2-ad9f15fb7c7c	assistant	🎪 **Event Ditemukan**\n\n**1. Tech Conference 2025**\n📅 2025-12-15 | 📍 Jakarta Convention Center\n💰 Rp 350,000\n\n**2. Digital Marketing Masterclass**\n📅 2025-11-25 | 📍 Online via Zoom\n💰 Rp 150,000\n\n**3. Startup Summit Indonesia 2026**\n📅 2026-01-10 | 📍 Bali Nusa Dua Convention Center\n💰 Rp 500,000\n\n**4. AI Workshop: Deep Learning Fundamentals**\n📅 2025-12-20 | 📍 Bandung Institute of Technology\n💰 Rp 350,000\n\n**5. Yoga & Wellness Retreat**\n📅 2025-11-30 | 📍 Dusun Bambu, Bandung\n💰 Rp 400,000\n\n	cari_event	\N	2026-07-05 05:54:16.017861
f9882697-e90a-466a-b737-351177843e08	3226e36a-a363-45d8-89b2-ad9f15fb7c7c	user	bantuan	tanya_bantuan	{"query": ["bantuan"]}	2026-07-05 05:54:16.019968
041b985d-b50e-4a63-a9ce-57333c926b6a	3226e36a-a363-45d8-89b2-ad9f15fb7c7c	assistant	📚 **Menu Bantuan EventBot**\n\nBerikut yang bisa saya bantu:\n\n**🔍 Cari Event**\n• 'Cari event di Jakarta'\n• 'Event teknologi bulan ini'\n• 'Event gratis'\n\n**📋 Lihat Event**\n• 'Lihat semua event'\n• 'Event yang akan datang'\n\n**🎫 Tiket & Booking**\n• 'Daftar tiket [nama event]'\n• 'Lihat tiket saya'\n\n**👤 Akun**\n• 'Profil saya'\n• 'Jadwal event saya'	tanya_bantuan	\N	2026-07-05 05:54:16.021533
93fbf69f-5f5d-401f-b7a3-d9806205125d	227d7d39-b96f-4bf6-ae0c-5ab351b27768	user	Ada event apa?	cari_event	{"query": ["ada  apa?"]}	2026-07-06 04:14:19.120215
bd17e6f9-046f-49bd-a434-5ab624bd2401	227d7d39-b96f-4bf6-ae0c-5ab351b27768	assistant	Maaf, saya tidak menemukan event yang sesuai. Coba kata kunci lain?	cari_event	\N	2026-07-06 04:14:19.155814
45fb2b55-2a19-4e55-aa8f-cffe2663542a	227d7d39-b96f-4bf6-ae0c-5ab351b27768	user	hai	sapaan	{"query": ["hai"]}	2026-07-06 04:14:30.387384
dfefce08-5d10-4d44-ac70-d42f55192778	227d7d39-b96f-4bf6-ae0c-5ab351b27768	assistant	Halo! Selamat datang di EventBot! 👋\n\nSaya bisa membantu Anda dengan:\n🔍 Cari event\n📋 Lihat daftar event\n🎫 Daftar tiket\n❓ Bantuan\n\nAda yang bisa saya bantu?	sapaan	\N	2026-07-06 04:14:30.391766
fe0e1cd6-9185-4ae8-9309-9c26ebdd2071	47c5713d-0cae-453e-aa20-264856ed8750	user	Ada event apa?	cari_event	{"query": ["ada  apa?"]}	2026-07-06 04:32:57.727048
05d45ecb-d098-4ecf-b93f-c165dd2ee434	47c5713d-0cae-453e-aa20-264856ed8750	assistant	Maaf, saya tidak menemukan event yang sesuai. Coba kata kunci lain?	cari_event	\N	2026-07-06 04:32:57.743732
675c990f-649d-4bc6-9f2c-f5a446066e09	47c5713d-0cae-453e-aa20-264856ed8750	user	hai	sapaan	{"query": ["hai"]}	2026-07-06 04:33:05.602347
be326951-bf64-45f5-bfcb-bb829bfba461	47c5713d-0cae-453e-aa20-264856ed8750	assistant	Halo! Selamat datang di EventBot! 👋\n\nSaya bisa membantu Anda dengan:\n🔍 Cari event\n📋 Lihat daftar event\n🎫 Daftar tiket\n❓ Bantuan\n\nAda yang bisa saya bantu?	sapaan	\N	2026-07-06 04:33:05.607584
1614bdfd-804a-4836-82ca-a797dc5c49a1	47c5713d-0cae-453e-aa20-264856ed8750	user	daftar tiket	daftar_tiket	{"query": ["tiket"]}	2026-07-06 04:33:16.584099
8441f846-9ada-4f39-8a23-d877554fc4e3	47c5713d-0cae-453e-aa20-264856ed8750	assistant	Silakan login terlebih dahulu untuk mendaftar event. Klik menu Login di atas.	daftar_tiket	\N	2026-07-06 04:33:16.592884
2df84d24-5595-4f39-9e97-2195477391ee	59a20e00-8599-4ca7-b0db-828329cbf540	user	Ada event apa?	cari_event	{"query": ["ada  apa?"]}	2026-07-06 21:17:30.420761
76787511-bb63-4353-85e2-07e140aceec6	59a20e00-8599-4ca7-b0db-828329cbf540	assistant	Maaf, saya tidak menemukan event yang sesuai. Coba kata kunci lain?	cari_event	\N	2026-07-06 21:17:30.462539
49721be4-2c6e-4a80-a3d5-01348b3a71fc	59a20e00-8599-4ca7-b0db-828329cbf540	user	hai	sapaan	{"query": ["hai"]}	2026-07-06 21:17:38.306346
266708bc-0340-4f8f-8bea-592725e1dab8	59a20e00-8599-4ca7-b0db-828329cbf540	assistant	Halo! Selamat datang di EventBot! 👋\n\nSaya bisa membantu Anda dengan:\n🔍 Cari event\n📋 Lihat daftar event\n🎫 Daftar tiket\n❓ Bantuan\n\nAda yang bisa saya bantu?	sapaan	\N	2026-07-06 21:17:38.313561
b94028bf-82bb-49a2-9e47-5d098060197a	59a20e00-8599-4ca7-b0db-828329cbf540	user	assalamualaikum	sapaan	{"query": ["assalamualaikum"]}	2026-07-06 21:17:49.897786
476ab0b1-83f6-4368-aa00-eca8b4ad686c	59a20e00-8599-4ca7-b0db-828329cbf540	assistant	Halo! Selamat datang di EventBot! 👋\n\nSaya bisa membantu Anda dengan:\n🔍 Cari event\n📋 Lihat daftar event\n🎫 Daftar tiket\n❓ Bantuan\n\nAda yang bisa saya bantu?	sapaan	\N	2026-07-06 21:17:49.902095
14f6e7b1-a781-4714-8228-46b4a01140e0	59a20e00-8599-4ca7-b0db-828329cbf540	user	cari event	cari_event	\N	2026-07-06 21:18:01.161446
214b93c8-46f6-4df9-818c-83b3456782c6	59a20e00-8599-4ca7-b0db-828329cbf540	assistant	🎪 **Event Ditemukan**\n\n**1. Tech Conference 2025**\n📅 2025-12-15 | 📍 Jakarta Convention Center\n💰 Rp 350,000\n\n**2. Digital Marketing Masterclass**\n📅 2025-11-25 | 📍 Online via Zoom\n💰 Rp 150,000\n\n**3. Startup Summit Indonesia 2026**\n📅 2026-01-10 | 📍 Bali Nusa Dua Convention Center\n💰 Rp 500,000\n\n**4. AI Workshop: Deep Learning Fundamentals**\n📅 2025-12-20 | 📍 Bandung Institute of Technology\n💰 Rp 350,000\n\n**5. Yoga & Wellness Retreat**\n📅 2025-11-30 | 📍 Dusun Bambu, Bandung\n💰 Rp 400,000\n\n	cari_event	\N	2026-07-06 21:18:01.165282
549b85cd-6612-459f-aa39-9bc4766af75d	59a20e00-8599-4ca7-b0db-828329cbf540	user	📋 Lihat Detail	tidak_dikenal	{"query": ["📋  detail"]}	2026-07-06 21:18:28.148908
9b0fb236-8ec3-49cb-a4c5-191e3adbe4e6	59a20e00-8599-4ca7-b0db-828329cbf540	assistant	Maaf, saya tidak mengerti. Coba ketik 'bantuan' untuk melihat fitur yang tersedia.	tidak_dikenal	\N	2026-07-06 21:18:28.153566
b279ae79-582b-49a1-806e-bc603f400642	59a20e00-8599-4ca7-b0db-828329cbf540	user	bantuan	tanya_bantuan	{"query": ["bantuan"]}	2026-07-06 21:18:37.229897
af49e89e-8ef4-4cc9-821a-b1b10911f3b9	59a20e00-8599-4ca7-b0db-828329cbf540	assistant	📚 **Menu Bantuan EventBot**\n\nBerikut yang bisa saya bantu:\n\n**🔍 Cari Event**\n• 'Cari event di Jakarta'\n• 'Event teknologi bulan ini'\n• 'Event gratis'\n\n**📋 Lihat Event**\n• 'Lihat semua event'\n• 'Event yang akan datang'\n\n**🎫 Tiket & Booking**\n• 'Daftar tiket [nama event]'\n• 'Lihat tiket saya'\n\n**👤 Akun**\n• 'Profil saya'\n• 'Jadwal event saya'	tanya_bantuan	\N	2026-07-06 21:18:37.235998
e3f958ea-992b-4741-839c-1c59342a82fe	59a20e00-8599-4ca7-b0db-828329cbf540	user	lihat event	cari_event	\N	2026-07-06 21:18:49.189908
956a697f-a4b5-4b2e-860f-112393b0b4c5	59a20e00-8599-4ca7-b0db-828329cbf540	assistant	🎪 **Event Ditemukan**\n\n**1. Tech Conference 2025**\n📅 2025-12-15 | 📍 Jakarta Convention Center\n💰 Rp 350,000\n\n**2. Digital Marketing Masterclass**\n📅 2025-11-25 | 📍 Online via Zoom\n💰 Rp 150,000\n\n**3. Startup Summit Indonesia 2026**\n📅 2026-01-10 | 📍 Bali Nusa Dua Convention Center\n💰 Rp 500,000\n\n**4. AI Workshop: Deep Learning Fundamentals**\n📅 2025-12-20 | 📍 Bandung Institute of Technology\n💰 Rp 350,000\n\n**5. Yoga & Wellness Retreat**\n📅 2025-11-30 | 📍 Dusun Bambu, Bandung\n💰 Rp 400,000\n\n	cari_event	\N	2026-07-06 21:18:49.1978
c506edb3-8bfd-42d2-a36f-bbf3cbd537f9	12f90245-7bcd-4551-9665-67bd3e526aa6	user	Ada event apa?	cari_event	{"query": ["ada  apa?"]}	2026-07-06 21:33:49.261052
251a0e12-6fed-4f18-a4b9-0f58f67ed3e2	12f90245-7bcd-4551-9665-67bd3e526aa6	assistant	Maaf, saya tidak menemukan event yang sesuai. Coba kata kunci lain?	cari_event	\N	2026-07-06 21:33:49.305882
edd63a89-14f5-4c44-ad85-62241f4a8e0a	fb89aafe-d81b-46d3-8aae-8f8259431438	user	Ada event apa?	cari_event	{"query": ["ada  apa?"]}	2026-07-07 18:45:20.46395
0f1df4a2-a21f-4051-acc7-5f4e6c3ecb3f	fb89aafe-d81b-46d3-8aae-8f8259431438	assistant	Maaf, saya tidak menemukan event yang sesuai. Coba kata kunci lain?	cari_event	\N	2026-07-07 18:45:20.496865
e77db677-73b9-4e8e-b6f2-96890bd2ec15	a069a0a4-df3e-4095-b793-d50ffdc44441	user	Ada event apa?	cari_event	{"query": ["ada  apa?"]}	2026-07-07 18:47:30.779572
d3c6da23-cbda-4186-9517-ee8decc77a17	a069a0a4-df3e-4095-b793-d50ffdc44441	assistant	Maaf, saya tidak menemukan event yang sesuai. Coba kata kunci lain?	cari_event	\N	2026-07-07 18:47:30.793637
2d23fc3f-221c-4a06-9aef-abfd51524eda	399a6702-87fb-424c-980e-d69e4e531129	user	hai	sapaan	{"query": ["hai"]}	2026-07-07 18:49:03.123478
594301a0-09ba-41b0-bd65-606125b4a5c8	399a6702-87fb-424c-980e-d69e4e531129	assistant	Halo! Selamat datang di EventBot! 👋\n\nSaya bisa membantu Anda dengan:\n🔍 Cari event\n📋 Lihat daftar event\n🎫 Daftar tiket\n❓ Bantuan\n\nAda yang bisa saya bantu?	sapaan	\N	2026-07-07 18:49:03.143134
\.


--
-- Data for Name: chat_sessions; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.chat_sessions (id, user_id, session_token, ip_address, user_agent, started_at, last_activity_at, ended_at, context_json) FROM stdin;
a2461bd0-e031-431a-b8e2-1fd79a045dde	\N	95f5974876ca176b275fcbe24547b0e45f53e51de0865ece0783d6bdcbe1e7a0	\N	\N	2026-07-04 01:53:00.791863	2026-07-04 01:53:00.791863	\N	{}
aea05e13-ef5c-42a4-9eca-e3cc7dfda504	\N	3caa6961ea975222c1cb82db978c11356c231e03c351fe3cb7cdc75796bb27d3	\N	\N	2026-07-04 01:55:06.985967	2026-07-04 01:55:06.985967	\N	{}
aa805338-3b2e-4a64-b708-8c0429511b3b	\N	1jlwCiHe-C5OGnbpjfZqIZIuecVZ3gusf1G9E5MNKqc	\N	\N	2026-07-04 01:55:06.992249	2026-07-04 01:55:06.992249	\N	{}
e72162b5-b1e9-4b81-8cb8-5a4c6ab8c295	\N	d728d7dd82eb83526fbcdefed3539a4d5eff17ab798ee1db9685d4c611cfa4d6	\N	\N	2026-07-04 01:55:30.941863	2026-07-04 01:55:30.941863	\N	{}
4de9abac-0f89-4458-b380-a536a6aa722d	\N	7QxXDs343jCXEKOsIdQL4uHkylmJZFt-6qsvujxVISo	\N	\N	2026-07-04 02:01:33.323083	2026-07-04 02:01:33.334422	\N	{}
ac5eb196-c5a8-4f9e-9a13-750f5f61105c	\N	c6e0afbd74081307a9741206d0b967e46437ff434914b51b55a94a7fe1953e82	\N	\N	2026-07-05 05:08:59.300159	2026-07-05 05:08:59.300159	\N	{}
c103c788-cbf9-43d4-87fc-119e663c8a7b	\N	v18U9ZkzOYgAPdhruPG2JLE0QzHeyLL4u48_oHSsl3o	\N	\N	2026-07-05 05:49:23.689732	2026-07-05 05:49:23.728889	\N	{}
8839505e-1fe2-4cfb-b764-b3a7df53837c	\N	7505d6853a487bfed4478ffff004edfd8387f71d7428158b4d1b8980ab9910a7	\N	\N	2026-07-05 05:54:16.003555	2026-07-05 05:54:16.003555	\N	{}
a43f86d0-9d46-4924-a0bb-1cea7495cefc	\N	f1NArH6eJmqVyo7NmEThV1G9vJ8syxInlsqtrmLcuXA	\N	\N	2026-07-04 01:55:30.948521	2026-07-04 01:55:30.962438	\N	{}
9120c9e1-557a-49f1-bbff-f803dfc28823	\N	46bbbc36d929fc3ceaf76390cc5c5100fda243d1d4fd6d64431efddf457e31f0	\N	\N	2026-07-04 01:56:11.540219	2026-07-04 01:56:11.540219	\N	{}
a069a0a4-df3e-4095-b793-d50ffdc44441	af8764bc-db84-48eb-8196-3cbc53397abe	jjmHOhG-64WB6is9BQxYB6edLLI3tXag0jBg5ZcyaxM	\N	\N	2026-07-07 18:47:30.756936	2026-07-07 18:47:30.793637	\N	{}
25e6ea1c-428c-4efb-82b6-6f315be1bb2c	\N	y6LDhkRzQBSDdd--6_dg-fDIX6ATJEW41BM5nNZUd7g	\N	\N	2026-07-05 05:08:59.365	2026-07-05 05:08:59.401681	\N	{}
b2a3c823-f8fe-4c57-82cd-c22517f49a31	\N	4e58174c753f7b83af1e16f73fd3e66b8674c85f33d0026a4b6434990f351db3	\N	\N	2026-07-05 05:11:10.763859	2026-07-05 05:11:10.763859	\N	{}
2332a02f-8d08-49e7-bbbf-85d4a923d9be	\N	UtmWam9Is_4w6kaijQYCIvPDbjJDkrCXiVGTkmcctu4	\N	\N	2026-07-04 01:56:11.546385	2026-07-04 01:56:11.556923	\N	{}
5f8a9fff-6005-4f50-8aa7-5119a0a260aa	\N	96e7b014404723c1804e389d6ab16f181a372b629367c8482944833b44b7a05b	\N	\N	2026-07-04 01:59:57.464288	2026-07-04 01:59:57.464288	\N	{}
c058e17a-915a-494b-a14c-5a8bebd7aac5	af8764bc-db84-48eb-8196-3cbc53397abe	594ccba9c721728d5d6e107a84d34237b1cce1a89e23fee06f7d72b515347fed	\N	\N	2026-07-07 18:49:03.077124	2026-07-07 18:49:03.077124	\N	{}
3226e36a-a363-45d8-89b2-ad9f15fb7c7c	\N	A8eITkbD-wf2cNhgsVGWiliweXViaq3b_pHq-DBUkqo	\N	\N	2026-07-05 05:54:16.009724	2026-07-05 05:54:16.021533	\N	{}
7711478f-1610-45a6-ab82-c1e78379e2e8	\N	N-HHj6KP4aY9OMMvOkMToBA_fc_rHKu3zqxvkVJKmqw	\N	\N	2026-07-04 01:59:57.473007	2026-07-04 01:59:57.485217	\N	{}
bc9bced0-d673-4ec3-adfe-a031eb8d48cd	\N	72355cf09d2c295b67101ceb40d8cca3365335593fd0dc75cb22b0455ec1d20d	\N	\N	2026-07-04 02:00:22.67195	2026-07-04 02:00:22.67195	\N	{}
cc1c5614-6f0e-40d2-b57c-4bbc0611cb63	\N	31ccefc4f710f73e1c1d415de13ec4e801c36de6dfd133e44f1e2d203d22e53c	\N	\N	2026-07-06 04:14:18.818748	2026-07-06 04:14:18.818748	\N	{}
76d04d86-50ff-420e-aea4-2e4ff104eb05	\N	xD7NjlxXeHX-AEPSk1LwB-OP7vehbkKtUyaWIfu4XSI	\N	\N	2026-07-05 05:11:10.770174	2026-07-05 05:11:10.784241	\N	{}
dc6b427e-e8ea-4488-a4b2-da5dbde7c344	\N	ab5360e46b31e76f0fc76f04c23ddfa727835ce9d40bc1ecd5f0c79e6b0a2b9c	\N	\N	2026-07-05 05:11:43.849915	2026-07-05 05:11:43.849915	\N	{}
108134ad-e54f-4ce2-8158-b5f9a5de54f2	\N	iZEjYddrNyz9MW4DBO8oVLTPcTpAEbZ9Pf7eAHeaskE	\N	\N	2026-07-04 02:00:22.678088	2026-07-04 02:00:22.689805	\N	{}
f991fed1-dae8-43af-8db3-a35f89e33fd4	\N	71079fff9aaeb64da80c79dcdbfc29605286bb6740a365aa880bc9382c6d28f4	\N	\N	2026-07-04 02:00:43.241861	2026-07-04 02:00:43.241861	\N	{}
399a6702-87fb-424c-980e-d69e4e531129	af8764bc-db84-48eb-8196-3cbc53397abe	Z3lQGpFD88uwUeHzdA6uUcjahERa2Is-tt-l4ENJgy8	\N	\N	2026-07-07 18:49:03.113439	2026-07-07 18:49:03.143134	\N	{}
227d7d39-b96f-4bf6-ae0c-5ab351b27768	\N	0rcGHiSnJRTMvV1kE5ACCuKa_Ve0d-8CvbUCwRUHWHU	\N	\N	2026-07-06 04:14:19.106751	2026-07-06 04:14:30.391766	\N	{}
792cac3a-20bf-4c06-9f0f-893305ae74c8	\N	QhNfzSTNJhHqGKhdW6VWqZr6uIuD2iV3taZt2EZRERU	\N	\N	2026-07-05 05:11:43.85568	2026-07-05 05:11:43.867707	\N	{}
f0b26282-055f-430d-98ec-b93b507530de	\N	pV9m9hYZTekYRwRinSVKUA6x4eqRt-NrEYtGcGFquGU	\N	\N	2026-07-04 02:00:43.248256	2026-07-04 02:00:43.259478	\N	{}
371227d2-4523-4c40-bc87-6aefca411f00	\N	3a31aead7e8e10620dae18a56d874f2909b080f11a91a7c8d75b505905ad4dc1	\N	\N	2026-07-04 02:01:18.309143	2026-07-04 02:01:18.309143	\N	{}
dcf5d37e-6aa7-4bce-9ddb-3a739aa5e126	\N	c3823034eb0b764626c6e8761121caa1a97116fecff1bc1fd2931f5f52547bb3	\N	\N	2026-07-05 05:12:11.888032	2026-07-05 05:12:11.888032	\N	{}
3b087975-c8e2-4b01-b9fa-fd0b88197310	\N	e29c81f242a2b4a5ed05b0171935f8daa23ca96b1082cff9db0bc656bce4f399	\N	\N	2026-07-06 04:32:57.668827	2026-07-06 04:32:57.668827	\N	{}
9bc5d750-bd21-4336-97dd-a74c689bcebb	\N	USV5S8uVRNhH8M1BPZzdowbgOAAdDto1_XQdpdOw0LI	\N	\N	2026-07-04 02:01:18.315257	2026-07-04 02:01:18.35979	\N	{}
89c0fbdb-84ea-41cf-bfc0-a81f742c9f1f	\N	9d43c8808ce40efd2769aec78d5570b3168df354d7122233c714c71fee26c904	\N	\N	2026-07-04 02:01:33.316284	2026-07-04 02:01:33.316284	\N	{}
b7de0fa3-f25c-4546-937f-135270c45393	\N	eE7CFV9gZHsTXsgyIxwXi6LR5hxlRvLa79X6vTgXVHA	\N	\N	2026-07-05 05:12:11.894081	2026-07-05 05:12:11.904865	\N	{}
411a160c-3946-47d3-b974-090b70b880e3	\N	712550b58e95bce33738697d7543a18110bf4f158efec9b827ee13318ebcfc0d	\N	\N	2026-07-05 05:49:23.678529	2026-07-05 05:49:23.678529	\N	{}
59a20e00-8599-4ca7-b0db-828329cbf540	\N	ocWcP2ltlibztHlu78Pc_ZNFswU-FFgjxY32S6Y9HQ4	\N	\N	2026-07-06 21:17:30.400945	2026-07-06 21:18:49.1978	\N	{}
e9e736a8-59ea-40e4-9800-d2f5a8677a14	\N	f6d1e2c6a46739865b4ada784e8322b31ce729ed8a5f6ea88d73c1e29405c3fa	\N	\N	2026-07-06 21:33:49.193231	2026-07-06 21:33:49.193231	\N	{}
47c5713d-0cae-453e-aa20-264856ed8750	\N	VxusDJd_zjc6PO3kTUy2MUyG7y2OEMbhIARTSKrMA1M	\N	\N	2026-07-06 04:32:57.708274	2026-07-06 04:33:23.773324	\N	{}
12f90245-7bcd-4551-9665-67bd3e526aa6	\N	otFjrM-oCutAPsnLYUPFfMDfDRg2BcKvHd-IgU05-sc	\N	\N	2026-07-06 21:33:49.238213	2026-07-06 21:33:49.305882	\N	{}
95ccedbd-31a6-4f35-b01e-6ea0c29e644d	\N	b8356f95f9a25eb0a2c0cd6bcb8f8b8e2142c1aae2e40bff0b65971ea1192598	\N	\N	2026-07-06 21:17:29.916537	2026-07-06 21:17:29.916537	\N	{}
0f935d51-ab86-4550-a7c3-8df0f4a19751	af8764bc-db84-48eb-8196-3cbc53397abe	4c15ea441f0ae0b272cacc45eec69e8517777d046f00108fedd3088bc66bd595	\N	\N	2026-07-07 18:45:19.940633	2026-07-07 18:45:19.940633	\N	{}
fb89aafe-d81b-46d3-8aae-8f8259431438	af8764bc-db84-48eb-8196-3cbc53397abe	fqe1cf2Igcy84jQAuTD0dNDwGrDtEgtbT4nGI6HapSw	\N	\N	2026-07-07 18:45:20.425373	2026-07-07 18:45:20.496865	\N	{}
d61989ed-5b64-4a7e-b31f-0c4c1ee8b570	af8764bc-db84-48eb-8196-3cbc53397abe	1e87f631705bd2850578883ccb0d6a3cb91bcb21c6f72d684dced8fb34778476	\N	\N	2026-07-07 18:47:30.708204	2026-07-07 18:47:30.708204	\N	{}
\.


--
-- Data for Name: event_categories; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.event_categories (event_id, category_id) FROM stdin;
0a019072-29ac-441c-8d3c-e52c71114f42	c2cbf1fa-2592-4155-a73c-c1985221d7b1
b3c5f04d-2863-4a74-b9f2-765f163756e1	c2cbf1fa-2592-4155-a73c-c1985221d7b1
93318dae-7097-46e4-afe0-4c78511b0429	d3d90ec3-ffb0-4e75-8cec-8df35997bb3f
31cb6533-5162-4799-90d7-65980692ebbb	d3d90ec3-ffb0-4e75-8cec-8df35997bb3f
b759906a-6451-48af-8d3b-c001c3bd5a49	217c1b82-6d45-419c-a6ca-c3cf73b82161
85173956-b502-439d-a285-0be667965271	d674f467-2956-4243-95c9-4290c11539f6
2f7c7417-5b21-4109-a42b-653ec7cb067b	d674f467-2956-4243-95c9-4290c11539f6
2f7c7417-5b21-4109-a42b-653ec7cb067b	5f6dc821-5db0-4e2f-bedf-2263aa886315
93318dae-7097-46e4-afe0-4c78511b0429	6bfaac29-1915-4475-9cc4-23c133102720
31cb6533-5162-4799-90d7-65980692ebbb	6bfaac29-1915-4475-9cc4-23c133102720
31cb6533-5162-4799-90d7-65980692ebbb	5f6dc821-5db0-4e2f-bedf-2263aa886315
b759906a-6451-48af-8d3b-c001c3bd5a49	0fdb53a1-a73d-4826-bf6f-0809027a826a
935b3682-2fdd-49f1-aa7c-a64aceef9bda	d674f467-2956-4243-95c9-4290c11539f6
935b3682-2fdd-49f1-aa7c-a64aceef9bda	5f6dc821-5db0-4e2f-bedf-2263aa886315
e9e2842e-8f47-403f-b6f8-00dba624e7cc	d674f467-2956-4243-95c9-4290c11539f6
e9e2842e-8f47-403f-b6f8-00dba624e7cc	237a4e18-1d40-4d31-a87f-a7d30b464c6e
e86105ce-a7ee-4a00-8d13-8f562d1ba54a	d674f467-2956-4243-95c9-4290c11539f6
e743f623-f41b-43c8-97d7-b6b048f0a86c	d674f467-2956-4243-95c9-4290c11539f6
e743f623-f41b-43c8-97d7-b6b048f0a86c	7c5462f6-9e2d-448f-8b68-4fc6c36feac7
39a9ab59-029d-4048-99ad-3d7cb0c920fb	a916ab54-92e9-47be-b1d4-a5a8a1f70e0d
39a9ab59-029d-4048-99ad-3d7cb0c920fb	98cfd928-5349-463c-8f48-ad1269808351
55e2a11f-b84c-4240-9c68-09fd14fb409b	98cfd928-5349-463c-8f48-ad1269808351
55e2a11f-b84c-4240-9c68-09fd14fb409b	237a4e18-1d40-4d31-a87f-a7d30b464c6e
eda83126-377a-4b28-b44b-ef458f1eaae7	d674f467-2956-4243-95c9-4290c11539f6
eda83126-377a-4b28-b44b-ef458f1eaae7	5f6dc821-5db0-4e2f-bedf-2263aa886315
\.


--
-- Data for Name: events; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.events (id, title, slug, description, short_description, start_date, end_date, start_time, end_time, location, location_map_url, organizer_id, image_url, banner_url, capacity, status, is_published, published_at, view_count, created_at, updated_at, deleted_at) FROM stdin;
2f7c7417-5b21-4109-a42b-653ec7cb067b	AI & Machine Learning Workshop	ai-machine-learning-workshop	Workshop hands-on Artificial Intelligence dan Machine Learning untuk pemula hingga menengah. Peserta akan belajar membuat model prediksi, klasifikasi gambar, dan NLP dari nol menggunakan Python dan TensorFlow.	Workshop AI praktis untuk pemula — bawa laptop!	2026-08-22	2026-08-22	09:00:00	17:00:00	Gedung Telkom, Bandung	\N	55fbcee3-6fdc-474f-98ab-8939b8b7ae88	https://images.unsplash.com/photo-1485827404703-89b55fcc595e?w=800	\N	80	upcoming	t	2026-07-07 01:01:41.739376	0	2026-07-07 01:01:41.739376	2026-07-08 04:12:50.071728	2026-07-08 04:12:50.071728
31cb6533-5162-4799-90d7-65980692ebbb	Digital Marketing Masterclass	digital-marketing-masterclass	-	Masterclass digital marketing lengkap	2026-07-07	2026-07-07	10:00:00	16:00:00	Online via Zoom	\N	55fbcee3-6fdc-474f-98ab-8939b8b7ae88	http://localhost:8000/uploads/events/pakai-ini.png	https://images.unsplash.com/photo-1460925895917-afdab827c52f	300	upcoming	t	2026-07-07 19:15:45.663573	0	2026-07-04 00:21:49.963762	2026-07-07 19:46:43.841597	2026-07-07 19:46:43.841597
935b3682-2fdd-49f1-aa7c-a64aceef9bda	Mobile App Development Bootcamp	mobile-app-development-bootcamp	Bootcamp intensif 3 hari belajar membuat aplikasi mobile menggunakan React Native dan Flutter. Dari design UI/UX hingga deploy ke App Store dan Play Store.	Bootcamp intensif React Native & Flutter — bikin app sendiri!	2026-08-28	2026-08-30	08:00:00	17:00:00	Coworking Space GoWork, Jakarta Selatan	\N	55fbcee3-6fdc-474f-98ab-8939b8b7ae88	https://images.unsplash.com/photo-1512941937669-90a1b58e7e9c?w=800	\N	60	upcoming	t	2026-07-07 01:01:41.747288	0	2026-07-07 01:01:41.747288	2026-07-07 01:01:41.747288	\N
e9e2842e-8f47-403f-b6f8-00dba624e7cc	UI/UX Design Intensive Workshop	ui-ux-design-intensive-workshop	Workshop intensif desain UI/UX modern menggunakan Figma. Belajar design thinking, user research, prototyping, dan usability testing dari desainer senior Tokopedia dan Gojek.	Workshop UI/UX dengan Figma — dari wireframe ke prototype	2026-09-20	2026-09-21	09:00:00	16:00:00	Design Hub, Kemang, Jakarta	\N	4dde6422-d264-40e1-b6dc-191a4717d912	https://images.unsplash.com/photo-1561070791-2526d30994b5?w=800	\N	40	upcoming	t	2026-07-07 01:01:41.749048	0	2026-07-07 01:01:41.749048	2026-07-07 01:01:41.749048	\N
e86105ce-a7ee-4a00-8d13-8f562d1ba54a	Cybersecurity Conference 2026	cybersecurity-conference-2026	Konferensi keamanan siber yang membahas ancaman terbaru, zero-day vulnerabilities, cloud security, dan best practices industri. Dihadiri BSSN, pakar cybersecurity, dan perusahaan teknologi.	Konferensi keamanan siber nasional — lindungi aset digital	2026-10-05	2026-10-06	08:00:00	17:00:00	Hotel Pullman, Jakarta Pusat	\N	55fbcee3-6fdc-474f-98ab-8939b8b7ae88	https://images.unsplash.com/photo-1550751827-4bd374c3f58b?w=800	\N	250	upcoming	t	2026-07-07 01:01:41.75111	0	2026-07-07 01:01:41.75111	2026-07-07 01:01:41.75111	\N
e743f623-f41b-43c8-97d7-b6b048f0a86c	Komunitas Python Indonesia Meetup	komunitas-python-indonesia-meetup	Meetup bulanan komunitas Python Indonesia. Sharing session, live coding, diskusi library terbaru, dan networking sesama Pythonista. Gratis untuk semua!	Meetup komunitas Python Indonesia — gratis dan seru!	2026-08-18	2026-08-18	18:30:00	21:00:00	Hacktiv8, Kemanggisan, Jakarta	\N	4dde6422-d264-40e1-b6dc-191a4717d912	https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5?w=800	\N	100	upcoming	t	2026-07-07 01:01:41.75289	0	2026-07-07 01:01:41.75289	2026-07-07 01:01:41.75289	\N
39a9ab59-029d-4048-99ad-3d7cb0c920fb	E-Sports Tournament MLBB 2026	e-sports-tournament-mlbb-2026	Tournament Mobile Legends Bang Bang antar kampus se-Jabodetabek. Total hadiah 50 juta rupiah. Open registration untuk tim 5 orang mahasiswa aktif.	Tournament MLBB antar kampus — total hadiah 50 juta!	2026-09-15	2026-09-17	10:00:00	22:00:00	Mall of Indonesia, Jakarta Utara	\N	4dde6422-d264-40e1-b6dc-191a4717d912	https://images.unsplash.com/photo-1542751371-adc38448a05e?w=800	\N	500	upcoming	t	2026-07-07 01:01:41.754603	0	2026-07-07 01:01:41.754603	2026-07-07 01:01:41.754603	\N
b759906a-6451-48af-8d3b-c001c3bd5a49	Yoga & Wellness Retreat	yoga-wellness-retreat	Habiskan akhir pekan dengan yoga, meditasi, dan aktivitas wellness di pegunungan Bandung.	Retreat yoga dan wellness di alam	2026-07-07	2026-07-07	07:00:00	15:00:00	Dusun Bambu, Bandung	https://maps.google.com/?q=DusunBambu	55fbcee3-6fdc-474f-98ab-8939b8b7ae88	http://localhost:8000/uploads/events/yoga.jpg	https://images.unsplash.com/photo-1544367567-0f2fcb009e0b	50	upcoming	t	2026-07-04 00:21:49.963762	0	2026-07-04 00:21:49.963762	2026-07-07 19:26:52.124588	\N
0a019072-29ac-441c-8d3c-e52c71114f42	Tech Conference 2025	tech-conference-2025		Konferensi teknologi tahunan dengan pembicara internasional	2026-07-07	2026-07-07	08:00:00	17:00:00	Jakarta Convention Center	https://maps.google.com/?q=JCC	55fbcee3-6fdc-474f-98ab-8939b8b7ae88	http://localhost:8000/uploads/events/cd8c631b088e4e5493ff989f7a0b4863.png	https://images.unsplash.com/photo-1540575467063-178a50c2df87	500	upcoming	t	2026-07-07 19:15:45.663573	0	2026-07-04 00:21:49.963762	2026-07-07 19:46:32.542979	2026-07-07 19:46:32.542979
b3c5f04d-2863-4a74-b9f2-765f163756e1	AI Workshop: Deep Learning Fundamentals	ai-workshop-deep-learning-fundamentals	cihuy	Workshop AI hands-on untuk pemula	2026-07-08	2026-07-08	09:00:00	16:00:00	Bandung Institute of Technology	https://maps.google.com/?q=ITB	55fbcee3-6fdc-474f-98ab-8939b8b7ae88	https://images.unsplash.com/photo-1485827404703-89b55fcc595e	https://images.unsplash.com/photo-1485827404703-89b55fcc595e	100	upcoming	t	2026-07-04 00:21:49.963762	0	2026-07-04 00:21:49.963762	2026-07-08 03:58:52.83672	\N
3cfec46a-c208-4a55-8a30-5dabd432e254	blabalab	blabalab	mafebkwef	sefjbkweff	2026-07-08	2026-07-08	09:00:00	10:00:00	adkanfe	\N	aed90366-01e7-448d-ac18-5827ee6e58f0	\N	\N	50	upcoming	t	2026-07-08 04:09:07.026771	0	2026-07-08 04:08:42.89298	2026-07-08 04:09:39.415906	2026-07-08 04:09:39.415906
93318dae-7097-46e4-afe0-4c78511b0429	Startup Summit Indonesia 2026	startup-summit-indonesia-2026	Pertemuan tahunan para founder, investor, dan enthusiast startup. Networking, pitching, dan workshop bisnis.	Pertemuan founder dan investor startup	2026-01-10	2026-01-12	08:00:00	18:00:00	Bali Nusa Dua Convention Center	https://maps.google.com/?q=NusaDua	55fbcee3-6fdc-474f-98ab-8939b8b7ae88	https://images.unsplash.com/photo-1515187029135-18ee286d815b	https://images.unsplash.com/photo-1515187029135-18ee286d815b	1000	upcoming	t	2026-07-04 00:21:49.963762	0	2026-07-04 00:21:49.963762	2026-07-08 04:11:07.575699	2026-07-08 04:11:07.575699
90df67fd-5b5e-4b1b-aa8b-9c8ed5462398	sdfsef	sdfsef	aefew	afkjwjebf	2026-07-08	2026-07-08	09:00:00	10:00:00	afqwf	\N	aed90366-01e7-448d-ac18-5827ee6e58f0	\N	\N	7	upcoming	t	\N	0	2026-07-08 04:36:29.379187	2026-07-08 04:36:48.568217	2026-07-08 04:36:48.568217
55e2a11f-b84c-4240-9c68-09fd14fb409b	Indie Music Festival Bandung	indie-music-festival-bandung	Festival musik indie terbesar di Bandung menampilkan 30+ band lokal dan nasional. 2 panggung, food festival, art installation, dan merchandise market.	Festival musik indie 2 hari — 30+ band, 2 panggung	2026-09-27	2026-09-28	13:00:00	23:00:00	Lapangan Tegallega, Bandung	\N	55fbcee3-6fdc-474f-98ab-8939b8b7ae88	https://images.unsplash.com/photo-1501386761578-eac5c94b800a?w=800	\N	3000	upcoming	t	2026-07-07 01:01:41.757562	0	2026-07-07 01:01:41.757562	2026-07-07 01:01:41.757562	\N
eda83126-377a-4b28-b44b-ef458f1eaae7	Data Science Bootcamp Weekend	data-science-bootcamp-weekend	Bootcamp data science 2 hari untuk pemula. Materi: Python pandas, data visualization, SQL, machine learning dasar, dan studi kasus industri nyata.	Bootcamp data science weekend — dari data ke insight	2026-08-09	2026-08-10	08:00:00	17:00:00	DQLab, Sudirman, Jakarta	\N	55fbcee3-6fdc-474f-98ab-8939b8b7ae88	https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=800	\N	50	upcoming	t	2026-07-07 01:01:41.760537	0	2026-07-07 01:01:41.760537	2026-07-07 01:01:41.760537	\N
850a83ab-1dcf-4cbe-a427-d918e753efbe	Workshop UI/UX Figma 2026	workshop-ui-ux-figma-2026	Pelajari cara membuat wireframe, prototype, dan design system menggunakan Figma bersama desainer senior. Cocok untuk mahasiswa dan fresh graduate yang ingin berkarir di bidang desain.	Workshop intensif desain UI/UX menggunakan Figma untuk pemula	2026-09-10	2026-09-11	09:00:00	17:00:00	Coworking Space WeWork, Jakarta Selatan	\N	aed90366-01e7-448d-ac18-5827ee6e58f0	https://images.unsplash.com/photo-1561070791-2526d30994b5?w=800	\N	40	upcoming	t	\N	0	2026-07-07 19:44:34.924066	2026-07-07 19:44:34.924066	\N
85173956-b502-439d-a285-0be667965271	Tech Conference 2026	tech-conference-2026	-	Konferensi teknologi terbesar dengan 50+ pembicara internasional	2026-07-07	2026-07-07	08:00:00	18:00:00	Jakarta Convention Center, Senayan	\N	55fbcee3-6fdc-474f-98ab-8939b8b7ae88	http://localhost:8000/uploads/events/f7385d1425664359bd18e3a3db09b56c.png	\N	500	upcoming	t	2026-07-07 19:15:45.663573	0	2026-07-07 01:01:41.466075	2026-07-07 19:46:59.855096	2026-07-07 19:46:59.855096
427ba515-dfd7-41b7-ae5e-053002e15b49	Python for Data Science Bootcamp	python-for-data-science-bootcamp	Bootcamp intensif 2 hari belajar Python untuk data science. Materi meliputi NumPy, Pandas, Matplotlib, Seaborn, dan Machine Learning dasar menggunakan Scikit-learn. Cocok untuk pemula yang ingin berkarier di bidang data.	Bootcamp intensif belajar Python untuk data science dari nol hingga mahir	2026-08-20	2026-08-21	10:00:00	18:00:00	Universitas Bina Nusantara, Jakarta	\N	aed90366-01e7-448d-ac18-5827ee6e58f0	\N	\N	46	upcoming	t	\N	0	2026-07-07 20:03:57.32439	2026-07-07 20:03:57.32439	\N
ad113d03-7944-478e-8e2a-fd75a94d3abe	Sesi diskusi dan demo penggunaan AI generatif dalam workflow pengembangan software modern.	sesi-diskusi-dan-demo-penggunaan-ai-generatif-dalam-workflow-pengembangan-software-modern	cihuy	cihuy	2026-07-08	2026-07-08	09:00:00	17:00:00	Gedung Telkom, Jl. Gatot Subroto No.52, Jakarta Selatan	\N	aed90366-01e7-448d-ac18-5827ee6e58f0	\N	\N	30	upcoming	t	\N	0	2026-07-08 03:57:45.645958	2026-07-08 04:07:12.157694	2026-07-08 04:07:12.157694
3f0a8899-3077-40e0-ae1c-5fb456890597	Tech Summit Jakarta 2026	tech-summit-jakarta-2026	Acara tahunan yang menghadirkan pembicara dari perusahaan teknologi terkemuka. Agenda meliputi keynote, workshop, dan networking session.	Konferensi teknologi terbesar di Jakarta tahun 2026	2026-08-15	2026-08-16	09:00:00	17:00:00	Jakarta Convention Center	\N	aed90366-01e7-448d-ac18-5827ee6e58f0	https://images.unsplash.com/photo-1540575467063-178a50c2df87?w=800	\N	500	upcoming	t	\N	0	2026-07-07 19:37:48.254703	2026-07-08 04:23:04.652263	2026-07-08 04:23:04.652263
dfad8ceb-7a70-45d8-9d2a-d6b7c5a4067e	bjbjgigui	bjbjgigui	sfkbwe	kjsbef	2026-07-08	2026-07-08	09:00:00	10:00:00	sfsej	\N	aed90366-01e7-448d-ac18-5827ee6e58f0	\N	\N	10	upcoming	t	\N	0	2026-07-08 04:25:03.255096	2026-07-08 04:25:24.018102	2026-07-08 04:25:24.018102
\.


--
-- Data for Name: knowledge_base; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.knowledge_base (id, category, question, answer, keywords, priority, is_active, created_at, updated_at) FROM stdin;
0007de13-60d9-41f2-a3dc-5e7725ab17ce	general	Apa itu EventBot?	EventBot adalah asisten virtual untuk manajemen event dan konferensi. Saya bisa membantu Anda mencari event, mendaftar tiket, dan memberikan informasi terkini.	{eventbot,"apa itu",tentang,chatbot}	10	t	2026-07-04 00:21:49.963762	2026-07-04 00:21:49.963762
1f58b8eb-017e-4330-a045-98644861ca06	general	Bagaimana cara mendaftar event?	Anda bisa mendaftar event dengan cara:\n1. Cari event yang diminati\n2. Pilih tiket yang tersedia\n3. Klik 'Daftar' atau bilang ke saya 'Daftar [nama event]'\n4. Selesaikan pembayaran\n5. Tiket akan muncul di Profil Anda	{daftar,"cara daftar",booking,"pesan tiket",register}	10	t	2026-07-04 00:21:49.963762	2026-07-04 00:21:49.963762
b3386e7d-d979-47a4-99c0-2be7ffd8f380	general	Apakah EventBot gratis?	Ya, menggunakan EventBot untuk mencari dan melihat event adalah gratis. Harga tiket event bervariasi tergantung event yang Anda pilih. Ada juga event gratis lho!	{gratis,free,bayar,harga,biaya}	9	t	2026-07-04 00:21:49.963762	2026-07-04 00:21:49.963762
70458158-f863-4e1d-ad9a-4a77025e0972	event	Event apa saja yang tersedia?	Saya bisa membantu Anda mencari event berdasarkan kategori, lokasi, atau tanggal. Coba ketik 'Cari event di Jakarta' atau 'Event teknologi bulan ini'.	{"event apa","daftar event",tersedia,"cari event"}	9	t	2026-07-04 00:21:49.963762	2026-07-04 00:21:49.963762
ef5d4e16-5a50-4c3c-bda2-7ab2f056900a	event	Bagaimana cara melihat detail event?	Anda bisa melihat detail event dengan mengetik 'Detail [nama event]' atau mengklik event di halaman Event Explorer. Saya akan menampilkan informasi lengkap.	{"detail event","info event","informasi event","lihat event"}	8	t	2026-07-04 00:21:49.963762	2026-07-04 00:21:49.963762
47ac2f50-e6bf-4f84-86e7-a7fffe69b4d6	ticket	Apakah tiket bisa refund?	Kebijakan refund tergantung event masing-masing. Umumnya:\n- Refund 100% jika H-7\n- Refund 50% jika H-3\n- Tidak refund jika H-1 atau saat event.	{refund,batal,cancel,"pengembalian uang",kembali}	8	t	2026-07-04 00:21:49.963762	2026-07-04 00:21:49.963762
46934322-7bf6-40b6-bff1-7577540898e4	ticket	Bagaimana cara check-in di event?	Saat event berlangsung, tunjukkan QR code tiket Anda di lokasi check-in. QR code bisa ditemukan di menu Profil > Tiket Saya.	{"check in",check-in,"masuk event","qr code",tiket}	8	t	2026-07-04 00:21:49.963762	2026-07-04 00:21:49.963762
86455f4d-de4a-4c1f-a53a-1cfaea3c378a	account	Bagaimana cara mengubah password?	Anda bisa mengubah password di menu Pengaturan > Profil. Klik 'Ubah Password' dan masukkan password lama serta password baru Anda.	{password,"ganti password","ubah password","lupa password"}	7	t	2026-07-04 00:21:49.963762	2026-07-04 00:21:49.963762
6c623a13-a4f5-4f0b-8b5b-f48753f4f655	account	Bagaimana cara menjadi organizer?	Untuk menjadi organizer, hubungi admin di email admin@eventbot.com dengan subject 'Request Organizer'. Tim kami akan review dan mengubah role akun Anda.	{organizer,"jadi organizer","buat event","host event"}	7	t	2026-07-04 00:21:49.963762	2026-07-04 00:21:49.963762
cb2c3803-45bd-40ce-8894-36f9efa9c30a	payment	Metode pembayaran apa yang tersedia?	Kami menerima pembayaran via:\n- Transfer Bank (BCA, Mandiri, BNI)\n- Virtual Account\n- E-wallet (GoPay, OVO, DANA, LinkAja)\n- Kartu Kredit	{pembayaran,bayar,payment,transfer,gopay,ovo}	8	t	2026-07-04 00:21:49.963762	2026-07-04 00:21:49.963762
97ff8dd8-e673-4602-ad9b-190ff6b9e892	help	Bantuan	Saya bisa membantu Anda dengan:\n🔍 Cari event\n📋 Lihat daftar event\n🎫 Daftar tiket\n👤 Lihat profil\n❓ FAQ\n\nAda yang bisa saya bantu?	{bantuan,help,fitur,"bisa apa",menu}	10	t	2026-07-04 00:21:49.963762	2026-07-04 00:21:49.963762
a54d9c14-b433-494e-bda2-50bbb4a0d76e	greeting	Halo	Halo! 👋 Selamat datang di EventBot!\n\nSaya adalah asisten virtual untuk manajemen event dan konferensi. Ada yang bisa saya bantu hari ini?\n\nCoba ketik:\n• 'Cari event' untuk melihat event tersedia\n• 'Bantuan' untuk melihat semua fitur	{halo,hai,hey,hi,assalamualaikum}	10	t	2026-07-04 00:21:49.963762	2026-07-04 00:21:49.963762
0c3368d1-e686-4b40-81ca-7c17f42a65bd	greeting	Halo	Halo! Selamat datang di EventBot! Saya bisa membantu kamu menemukan dan mendaftar event seru. Coba ketik 'cari event' atau 'bantuan'.	{halo,hai,hi,hey,"selamat pagi","selamat siang",assalamualaikum}	8	t	2026-07-07 01:13:42.709186	2026-07-07 01:13:42.709186
6ccc5834-bd42-454d-9bf6-4d7bdc5350fe	help	Bantuan	Saya bisa membantu dengan:\n- Cari event berdasarkan kategori/lokasi\n- Info detail event\n- Daftar dan beli tiket\n- Lihat tiket kamu\n- FAQ seputar EventBot	{bantuan,help,fitur,"bisa apa",menu,"apa yang bisa"}	8	t	2026-07-07 01:13:42.712132	2026-07-07 01:13:42.712132
89bdcef4-bce7-49ef-bde1-8758fea260d7	event	Cara mendaftar event	Cara daftar event:\n1. Cari event yang kamu minati\n2. Klik 'Detail'\n3. Pilih jenis tiket\n4. Klik 'Daftar Sekarang'\n5. Selesaikan pembayaran\n6. Tiket muncul di Profil Saya	{daftar,"cara daftar",booking,"pesan tiket","beli tiket",register}	8	t	2026-07-07 01:13:42.713329	2026-07-07 01:13:42.713329
0549eaa6-00ff-494d-8886-95619368a3e9	ticket	Cara melihat tiket	Tiket kamu bisa dilihat di menu 'Profil Saya' > tab 'Tiket Saya'. Di sana ada kode tiket dan status pembayaran.	{"tiket saya","lihat tiket","cek tiket","tiket mana"}	8	t	2026-07-07 01:13:42.714576	2026-07-07 01:13:42.714576
80f0c1b4-5fa9-4dd6-bcdb-696727e57a75	payment	Metode pembayaran	Tersedia metode pembayaran:\n- Transfer Bank (BCA, Mandiri, BNI, BRI)\n- E-Wallet (GoPay, OVO, DANA)\n- Virtual Account	{bayar,pembayaran,payment,transfer,gopay,ovo,dana}	8	t	2026-07-07 01:13:42.71603	2026-07-07 01:13:42.71603
92d0cc55-5360-4abc-922e-305602df5592	refund	Kebijakan refund	Kebijakan refund tiap event berbeda. Umumnya:\n- H-7: refund 100%\n- H-3: refund 50%\n- H-1 atau saat event: tidak ada refund\nHubungi penyelenggara untuk info lebih lanjut.	{refund,batalkan,cancel,"kembalikan uang",batal}	8	t	2026-07-07 01:13:42.717532	2026-07-07 01:13:42.717532
c00632f4-7ecb-4804-a83e-990eb21ead55	checkin	Cara check-in	Saat event: tunjukkan kode tiket di Profil Saya kepada petugas check-in. Kode unik kamu akan diverifikasi.	{"check in",checkin,"masuk event","verifikasi tiket"}	8	t	2026-07-07 01:13:42.718871	2026-07-07 01:13:42.718871
37c00e51-3ab3-4c34-b911-fa034474691e	account	Ubah password	Ganti password di menu Profil Saya > tab Ganti Password. Masukkan password lama dan password baru.	{"ganti password","ubah password","lupa password","reset password"}	8	t	2026-07-07 01:13:42.720095	2026-07-07 01:13:42.720095
bf63040d-b31d-4f40-846b-c685fad73657	general	Tentang EventBot	EventBot adalah platform chatbot cerdas untuk menemukan dan mendaftar event. Dibangun dengan FastAPI dan Streamlit, menggunakan teknologi NLP berbasis regex.	{eventbot,"apa itu eventbot",tentang,about,platform}	8	t	2026-07-07 01:13:42.721319	2026-07-07 01:13:42.721319
\.


--
-- Data for Name: registrations; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.registrations (id, user_id, ticket_id, event_id, quantity, total_price, status, payment_method, payment_proof_url, notes, checked_in_at, checked_in_by, created_at, updated_at, cancelled_at) FROM stdin;
d30e8c8a-c5cc-4112-b6f5-3adcc0bc432b	96384a65-d4a5-46aa-89b0-33783e975314	3c6caf96-c7ed-46f0-ac5e-da0547df67df	0a019072-29ac-441c-8d3c-e52c71114f42	1	350000.00	confirmed	transfer_bank	\N	\N	\N	\N	2026-07-07 01:13:42.689744	2026-07-07 01:13:42.689744	\N
0e82df19-2f86-410a-ab3e-640964805af4	96384a65-d4a5-46aa-89b0-33783e975314	a7b25fea-2f16-474d-93ce-892dad7813d9	0a019072-29ac-441c-8d3c-e52c71114f42	1	500000.00	confirmed	transfer_bank	\N	\N	\N	\N	2026-07-07 01:13:42.697637	2026-07-07 01:13:42.697637	\N
4dd14a8b-2d19-4d6c-a529-4a43c3faab6b	de9e760f-abf0-4223-8fc0-7d867e517d16	30c66966-56c1-4a53-b308-426b3ec6b9b4	0a019072-29ac-441c-8d3c-e52c71114f42	1	750000.00	confirmed	transfer_bank	\N	\N	\N	\N	2026-07-07 01:13:42.699086	2026-07-07 01:13:42.699086	\N
0ee82e64-3045-4a3e-9025-ffbf7c9a8ee7	de9e760f-abf0-4223-8fc0-7d867e517d16	f3394073-aa60-4597-a017-93e863636dc4	b3c5f04d-2863-4a74-b9f2-765f163756e1	1	350000.00	confirmed	transfer_bank	\N	\N	\N	\N	2026-07-07 01:13:42.700445	2026-07-07 01:13:42.700445	\N
8875f70a-368a-462d-b3fd-2a760dee9abe	965dbfb5-a4a1-4f6d-9721-12a1083648ef	2bf9e347-1dcb-48ed-9ceb-6af55f6c2bea	93318dae-7097-46e4-afe0-4c78511b0429	1	750000.00	confirmed	transfer_bank	\N	\N	\N	\N	2026-07-07 01:13:42.70179	2026-07-07 01:13:42.70179	\N
d6787e55-25a8-436b-8d9d-c9658736d532	965dbfb5-a4a1-4f6d-9721-12a1083648ef	d6264685-85f8-43b7-a6bc-aad9400b1cbb	93318dae-7097-46e4-afe0-4c78511b0429	1	500000.00	confirmed	transfer_bank	\N	\N	\N	\N	2026-07-07 01:13:42.703045	2026-07-07 01:13:42.703045	\N
7767449d-45f4-4337-910f-b2c30a1de328	7e54f2d6-d384-4f00-a50e-6dcd7418cade	8d5b03d1-ec94-4f1f-9cd4-d87df3ebc46c	31cb6533-5162-4799-90d7-65980692ebbb	1	150000.00	confirmed	transfer_bank	\N	\N	\N	\N	2026-07-07 01:13:42.704343	2026-07-07 01:13:42.704343	\N
aff01acf-c67c-42c0-933a-9a31b27faaf6	7e54f2d6-d384-4f00-a50e-6dcd7418cade	51366732-3e3a-44a1-9ccd-d6147715a8fa	31cb6533-5162-4799-90d7-65980692ebbb	1	250000.00	confirmed	transfer_bank	\N	\N	\N	\N	2026-07-07 01:13:42.705527	2026-07-07 01:13:42.705527	\N
e74493c0-516b-4ebf-aa0d-388636548f55	38cd080b-abda-4d9b-b6e6-1180e5cb2292	0d08ef1f-8136-42a7-b991-9f1bcb25e495	b759906a-6451-48af-8d3b-c001c3bd5a49	1	1200000.00	confirmed	transfer_bank	\N	\N	\N	\N	2026-07-07 01:13:42.706731	2026-07-07 01:13:42.706731	\N
e6af6536-b734-4522-85cc-a4132ac01cc3	38cd080b-abda-4d9b-b6e6-1180e5cb2292	d43f8abd-6028-4e5b-9013-3942594ac647	b759906a-6451-48af-8d3b-c001c3bd5a49	1	400000.00	confirmed	transfer_bank	\N	\N	\N	\N	2026-07-07 01:13:42.707972	2026-07-07 01:13:42.707972	\N
2abf8977-1900-4aed-beaf-346565c31225	af8764bc-db84-48eb-8196-3cbc53397abe	30c66966-56c1-4a53-b308-426b3ec6b9b4	0a019072-29ac-441c-8d3c-e52c71114f42	1	750000.00	pending	transfer_bank	\N	\N	\N	\N	2026-07-07 02:32:31.104694	2026-07-07 02:32:31.104694	\N
24430e70-871e-4ff3-a21a-4d6af8658e19	af8764bc-db84-48eb-8196-3cbc53397abe	a7b25fea-2f16-474d-93ce-892dad7813d9	0a019072-29ac-441c-8d3c-e52c71114f42	1	500000.00	confirmed	e_wallet	\N	\N	\N	\N	2026-07-07 02:35:33.998229	2026-07-07 02:56:42.963876	\N
37535390-875e-40bf-8e09-0858480741f8	af8764bc-db84-48eb-8196-3cbc53397abe	b93e51d2-524c-4558-bd2b-5f8fb6c52980	2f7c7417-5b21-4109-a42b-653ec7cb067b	1	350000.00	confirmed	transfer_bank	\N	\N	\N	\N	2026-07-07 04:33:49.471552	2026-07-07 04:34:49.799641	\N
21bb5084-e0f3-46d9-87ba-44f1f4a5ad69	af8764bc-db84-48eb-8196-3cbc53397abe	09852234-eab6-46a4-94c1-03e8365d72f9	427ba515-dfd7-41b7-ae5e-053002e15b49	1	75000.00	cancelled	transfer_bank	\N	\N	\N	\N	2026-07-07 20:08:17.871537	2026-07-07 20:17:46.273555	2026-07-07 20:17:46.273555
c6dae45f-a100-4806-ac27-2c76d6824547	af8764bc-db84-48eb-8196-3cbc53397abe	09852234-eab6-46a4-94c1-03e8365d72f9	427ba515-dfd7-41b7-ae5e-053002e15b49	1	75000.00	confirmed	transfer_bank	\N	\N	\N	\N	2026-07-07 20:18:09.309522	2026-07-07 20:18:50.470487	\N
16a8a8cb-80d5-400c-9fc1-3a91491681e8	af8764bc-db84-48eb-8196-3cbc53397abe	09852234-eab6-46a4-94c1-03e8365d72f9	427ba515-dfd7-41b7-ae5e-053002e15b49	1	75000.00	cancelled	e_wallet	\N	\N	\N	\N	2026-07-07 20:27:40.426832	2026-07-07 20:31:29.343801	2026-07-07 20:31:29.343801
\.


--
-- Data for Name: system_settings; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.system_settings (key, value, description, updated_at) FROM stdin;
chatbot_name	EventBot	Nama chatbot yang ditampilkan ke user	2026-07-04 00:21:49.963762
chatbot_greeting	Halo! Selamat datang di EventBot! 👋	Pesan sapaan default chatbot	2026-07-04 00:21:49.963762
chatbot_fallback	Maaf, saya tidak mengerti. Coba ketik 'bantuan' untuk melihat fitur yang tersedia.	Pesan fallback saat intent tidak dikenali	2026-07-04 00:21:49.963762
max_chat_history	50	Maksimal pesan chat yang disimpan per session	2026-07-04 00:21:49.963762
event_default_image	https://images.unsplash.com/photo-1540575467063-178a50c2df87	Gambar default untuk event tanpa image	2026-07-04 00:21:49.963762
registration_deadline_hours	24	Batas waktu pembayaran registrasi (jam)	2026-07-04 00:21:49.963762
enable_email_notification	true	Aktifkan notifikasi email	2026-07-04 00:21:49.963762
maintenance_mode	false	Mode maintenance (true = read-only)	2026-07-04 00:21:49.963762
registration_deadline_hrs	24	Batas waktu bayar (jam)	2026-07-07 01:13:42.72328
\.


--
-- Data for Name: tickets; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.tickets (id, event_id, name, description, price, quantity, sold, max_per_order, benefits, status, sale_starts_at, sale_ends_at, created_at, updated_at, deleted_at) FROM stdin;
68c07f9d-6c31-4cb3-9f95-d96b4d7ea5ce	b3c5f04d-2863-4a74-b9f2-765f163756e1	Early bid	\N	30000.00	10	0	5	\N	available	\N	\N	2026-07-08 02:52:45.299445	2026-07-08 03:31:38.511995	2026-07-08 03:31:38.511995
c6da009d-81ff-4f1e-9773-10f6fc103103	b3c5f04d-2863-4a74-b9f2-765f163756e1	Regular	\N	100000.00	30	0	5	\N	available	\N	\N	2026-07-08 02:50:32.303762	2026-07-08 03:32:46.830199	\N
4613e6c6-af72-4cbf-9822-0242ced4a309	850a83ab-1dcf-4cbe-a427-d918e753efbe	Test Tiket	test	100000.00	50	0	5	\N	available	\N	\N	2026-07-08 03:44:41.181086	2026-07-08 03:44:41.181086	\N
129b9a7e-de51-448f-a35e-e81bca422be5	850a83ab-1dcf-4cbe-a427-d918e753efbe	Regular	\N	150000.00	100	0	5	\N	available	\N	\N	2026-07-08 03:46:54.095086	2026-07-08 03:46:54.095086	\N
274cad22-1db5-4819-a6df-2d385b788c24	e9e2842e-8f47-403f-b6f8-00dba624e7cc	Regular	\N	20000.00	30	0	5	\N	available	\N	\N	2026-07-08 03:42:32.851663	2026-07-08 03:50:43.83046	\N
04611049-6749-4328-a8fc-e68c7b0ec654	93318dae-7097-46e4-afe0-4c78511b0429	General Pass	Akses 3 hari semua sesi dan networking.	499000.00	600	0	5	{"3-Day Access",E-Certificate}	available	2026-01-01 00:00:00	2026-01-09 00:00:00	2026-07-07 01:02:29.878755	2026-07-08 04:11:07.575699	2026-07-08 04:11:07.575699
2bf9e347-1dcb-48ed-9ceb-6af55f6c2bea	93318dae-7097-46e4-afe0-4c78511b0429	VIP Pass	Akses VIP 3 hari, priority seating, dan gala dinner.	750000.00	100	1	3	{"3-Day Access","Gala Dinner","Priority Seat",E-Certificate}	available	2025-11-01 00:00:00	2026-01-09 00:00:00	2026-07-04 00:21:49.963762	2026-07-08 04:11:07.575699	2026-07-08 04:11:07.575699
d6264685-85f8-43b7-a6bc-aad9400b1cbb	93318dae-7097-46e4-afe0-4c78511b0429	Regular Pass	Akses reguler 3 hari summit.	500000.00	200	1	5	{"3-Day Access",E-Certificate}	available	2025-11-01 00:00:00	2026-01-09 00:00:00	2026-07-04 00:21:49.963762	2026-07-08 04:11:07.575699	2026-07-08 04:11:07.575699
b93e51d2-524c-4558-bd2b-5f8fb6c52980	2f7c7417-5b21-4109-a42b-653ec7cb067b	Workshop Pass	Akses penuh workshop, dataset, source code, dan sertifikat.	350000.00	60	1	1	{Dataset,"Source Code",E-Certificate,Lunch}	available	2026-07-07 01:01:41.789575	2026-08-22 00:00:00	2026-07-07 01:01:41.789575	2026-07-08 04:12:50.071728	2026-07-08 04:12:50.071728
e9cb541b-5234-40f6-bf3c-547d907cc947	2f7c7417-5b21-4109-a42b-653ec7cb067b	Workshop + Mentoring	Workshop + 1 sesi mentoring pribadi setelah event.	500000.00	20	0	1	{Dataset,"Source Code",E-Certificate,Lunch,"1-on-1 Mentoring"}	available	2026-07-07 01:01:41.790866	2026-08-22 00:00:00	2026-07-07 01:01:41.790866	2026-07-08 04:12:50.071728	2026-07-08 04:12:50.071728
d58dfc40-0393-42c4-848e-c935ffa03731	2f7c7417-5b21-4109-a42b-653ec7cb067b	Workshop Pass	Akses penuh workshop, dataset, source code, dan sertifikat.	100000.00	20	0	1	{Dataset,"Source Code",E-Certificate,Lunch}	available	2026-07-07 01:02:06.564304	2026-08-21 00:00:00	2026-07-07 01:02:06.564304	2026-07-08 04:12:50.071728	2026-07-08 04:12:50.071728
db7477f2-0441-47e6-a5f4-6e9e2bf7e63e	2f7c7417-5b21-4109-a42b-653ec7cb067b	Workshop + Mentoring	Workshop + 1 sesi mentoring pribadi setelah event.	500000.00	20	0	1	{Dataset,"Source Code",E-Certificate,Lunch,"1-on-1 Mentoring"}	available	2026-07-07 01:02:06.565567	2026-08-21 00:00:00	2026-07-07 01:02:06.565567	2026-07-08 04:12:50.071728	2026-07-08 04:12:50.071728
5b6bb876-f5e4-4fc4-bc9d-21470eb8c24d	2f7c7417-5b21-4109-a42b-653ec7cb067b	Workshop + Mentoring	Workshop + 1 sesi mentoring pribadi setelah event.	500000.00	20	0	1	{Dataset,"Source Code",E-Certificate,Lunch,"1-on-1 Mentoring"}	available	2026-01-01 00:00:00	2026-08-21 00:00:00	2026-07-07 01:02:29.877248	2026-07-08 04:12:50.071728	2026-07-08 04:12:50.071728
3c6caf96-c7ed-46f0-ac5e-da0547df67df	0a019072-29ac-441c-8d3c-e52c71114f42	Early Bird	Tiket early bird dengan harga spesial. Termasuk lunch dan seminar kit.	350000.00	50	0	2	{Lunch,"Seminar Kit",E-Certificate}	available	2025-10-01 00:00:00	2025-11-15 00:00:00	2026-07-04 00:21:49.963762	2026-07-07 19:46:32.542979	2026-07-07 19:46:32.542979
8d5b03d1-ec94-4f1f-9cd4-d87df3ebc46c	31cb6533-5162-4799-90d7-65980692ebbb	Early Bird	Harga spesial early bird. Materi recording included.	150000.00	100	0	3	{"Live Session",Recording,E-Certificate}	available	2025-10-01 00:00:00	2025-11-20 00:00:00	2026-07-04 00:21:49.963762	2026-07-07 19:46:43.841597	2026-07-07 19:46:43.841597
51366732-3e3a-44a1-9ccd-d6147715a8fa	31cb6533-5162-4799-90d7-65980692ebbb	Regular	Akses live session dan recording.	250000.00	200	0	5	{"Live Session",Recording,E-Certificate}	available	2025-10-01 00:00:00	2025-11-24 00:00:00	2026-07-04 00:21:49.963762	2026-07-07 19:46:43.841597	2026-07-07 19:46:43.841597
4860383c-0f7f-4238-8a22-a6d25d84d4d0	85173956-b502-439d-a285-0be667965271	Early Bird	Tiket early bird harga spesial. Termasuk lunch dan seminar kit.	350000.00	100	0	2	{Lunch,"Seminar Kit",E-Certificate,"Networking Session"}	available	2026-07-07 01:01:41.78097	2026-08-16 00:00:00	2026-07-07 01:01:41.78097	2026-07-07 19:46:59.855096	2026-07-07 19:46:59.855096
a1af5c98-ea86-4352-82c5-5a3cec788f71	85173956-b502-439d-a285-0be667965271	Regular	Tiket reguler. Termasuk lunch, seminar kit, dan akses semua sesi.	500000.00	300	0	5	{Lunch,"Seminar Kit",E-Certificate}	available	2026-07-07 01:01:41.785176	2026-08-16 00:00:00	2026-07-07 01:01:41.785176	2026-07-07 19:46:59.855096	2026-07-07 19:46:59.855096
f3394073-aa60-4597-a017-93e863636dc4	b3c5f04d-2863-4a74-b9f2-765f163756e1	Workshop Pass	Akses penuh workshop, dataset, dan source code.	350000.00	50	1	1	{Dataset,"Source Code",E-Certificate}	available	2025-10-01 00:00:00	2025-12-19 00:00:00	2026-07-04 00:21:49.963762	2026-07-07 20:11:47.445707	\N
0d08ef1f-8136-42a7-b991-9f1bcb25e495	b759906a-6451-48af-8d3b-c001c3bd5a49	Full Package	Akomodasi 1 malam, 4 sesi yoga, meals, dan workshop mindfulness.	1200000.00	30	1	2	{Akomodasi,Meals,"Yoga Sessions",Workshop}	available	2025-10-01 00:00:00	2025-11-28 00:00:00	2026-07-04 00:21:49.963762	2026-07-07 20:11:47.445707	\N
d43f8abd-6028-4e5b-9013-3942594ac647	b759906a-6451-48af-8d3b-c001c3bd5a49	Day Pass	Akses 1 hari tanpa menginap. Termasuk 2 sesi yoga dan lunch.	400000.00	20	1	3	{"Day Access","2 Yoga Sessions",Lunch}	available	2025-10-01 00:00:00	2025-11-29 00:00:00	2026-07-04 00:21:49.963762	2026-07-07 20:11:47.445707	\N
a86dafed-038c-47a3-b963-f4490775487d	b3c5f04d-2863-4a74-b9f2-765f163756e1	Regular	\N	20000.00	10	0	5	\N	available	\N	\N	2026-07-08 02:58:01.903782	2026-07-08 03:31:19.552661	2026-07-08 03:31:19.552661
f380705a-84b4-4f58-a037-e50193b92950	93318dae-7097-46e4-afe0-4c78511b0429	Investor Pass	Akses khusus investor: private meeting room dan pitch session.	999000.00	100	0	2	{"3-Day Access","Private Meeting","Gala Dinner",E-Certificate}	available	2026-01-01 00:00:00	2026-01-09 00:00:00	2026-07-07 01:02:29.879933	2026-07-08 04:11:07.575699	2026-07-08 04:11:07.575699
4994cbe9-3ba5-4ef3-b62c-fca0b37d6b15	93318dae-7097-46e4-afe0-4c78511b0429	Startup Package	Paket startup: booth pameran + 3 tiket + slot pitching.	1500000.00	50	0	1	{Booth,"3 Tiket","Pitching Slot",E-Certificate}	available	2026-01-01 00:00:00	2026-01-09 00:00:00	2026-07-07 01:02:29.881637	2026-07-08 04:11:07.575699	2026-07-08 04:11:07.575699
c4df65fd-9dd5-42d5-a5c6-d26afe1ea929	93318dae-7097-46e4-afe0-4c78511b0429	General Pass	Akses 3 hari semua sesi dan networking.	499000.00	600	0	5	{"3-Day Access",E-Certificate}	available	2025-10-12 00:00:00	2026-01-09 00:00:00	2026-07-07 01:12:59.216391	2026-07-08 04:11:07.575699	2026-07-08 04:11:07.575699
eacb9102-3921-4ffd-af68-67356e427e22	93318dae-7097-46e4-afe0-4c78511b0429	Investor Pass	Akses khusus investor: private meeting room dan pitch session.	999000.00	100	0	2	{"3-Day Access","Private Meeting","Gala Dinner",E-Certificate}	available	2025-10-12 00:00:00	2026-01-09 00:00:00	2026-07-07 01:12:59.217594	2026-07-08 04:11:07.575699	2026-07-08 04:11:07.575699
9fcf280f-c1da-4e45-8eba-0281bd73171f	2f7c7417-5b21-4109-a42b-653ec7cb067b	Workshop Pass	Akses penuh workshop, dataset, source code, dan sertifikat.	350000.00	60	0	1	{Dataset,"Source Code",E-Certificate,Lunch}	available	2026-01-01 00:00:00	2026-08-21 00:00:00	2026-07-07 01:02:29.875822	2026-07-08 04:12:50.071728	2026-07-08 04:12:50.071728
7921e85a-6996-4647-a484-a46644d1a7d1	2f7c7417-5b21-4109-a42b-653ec7cb067b	Workshop + Mentoring	Workshop + 1 sesi mentoring pribadi setelah event.	500000.00	20	0	1	{Dataset,"Source Code",E-Certificate,Lunch,"1-on-1 Mentoring"}	available	2026-05-24 00:00:00	2026-08-21 00:00:00	2026-07-07 01:12:59.214785	2026-07-08 04:12:50.071728	2026-07-08 04:12:50.071728
c60ba50b-62fa-4acb-9abf-8e895364356a	2f7c7417-5b21-4109-a42b-653ec7cb067b	Workshop Pass	Akses penuh workshop, dataset, source code, dan sertifikat.	350000.00	60	0	1	{Dataset,"Source Code",E-Certificate,Lunch}	available	2026-05-24 00:00:00	2026-08-21 00:00:00	2026-07-07 01:12:59.213482	2026-07-08 04:12:50.071728	2026-07-08 04:12:50.071728
38904945-36db-4719-aa92-caa445d7a2fd	935b3682-2fdd-49f1-aa7c-a64aceef9bda	Bootcamp Pass	Akses 3 hari bootcamp + materi + sertifikat.	750000.00	50	0	1	{"3-Day Access","Materi PDF","Source Code",E-Certificate}	available	2026-05-30 00:00:00	2026-08-27 00:00:00	2026-07-07 01:12:59.225964	2026-07-07 01:12:59.225964	\N
2ad7e1c7-4d75-44d9-ba01-8162b44c7cf8	935b3682-2fdd-49f1-aa7c-a64aceef9bda	Bootcamp + Mentoring	Bootcamp + 2 sesi mentoring 1-on-1 pasca event.	1000000.00	10	0	1	{"3-Day Access",Materi,"Source Code","2x Mentoring",E-Certificate}	available	2026-05-30 00:00:00	2026-08-27 00:00:00	2026-07-07 01:12:59.227204	2026-07-07 01:12:59.227204	\N
efd1bf93-3f01-4d61-a93b-216730cd08ad	e9e2842e-8f47-403f-b6f8-00dba624e7cc	Workshop Pass	Akses 2 hari workshop Figma + materi.	450000.00	35	0	1	{"2-Day Access","Figma Assets",E-Certificate}	available	2026-06-22 00:00:00	2026-09-19 00:00:00	2026-07-07 01:12:59.228802	2026-07-07 01:12:59.228802	\N
ad6f95f4-db37-442d-a1e0-ccf477a260d3	e9e2842e-8f47-403f-b6f8-00dba624e7cc	Workshop + Portfolio Review	Workshop + review portfolio by senior designer.	650000.00	5	0	1	{"2-Day Access","Figma Assets","Portfolio Review",E-Certificate}	available	2026-06-22 00:00:00	2026-09-19 00:00:00	2026-07-07 01:12:59.230102	2026-07-07 01:12:59.230102	\N
9df395fa-bcf3-42bc-8427-e334887cdfb3	e86105ce-a7ee-4a00-8d13-8f562d1ba54a	Conference Pass	Akses 2 hari konferensi + lunch.	299000.00	200	0	3	{"2-Day Access",Lunch,E-Certificate}	available	2026-07-07 00:00:00	2026-10-04 00:00:00	2026-07-07 01:12:59.231751	2026-07-07 01:12:59.231751	\N
f376939e-c928-4b13-acd6-12980dfc38d2	e86105ce-a7ee-4a00-8d13-8f562d1ba54a	VIP Pass	Akses VIP + hands-on lab + networking dinner.	599000.00	30	0	1	{"2-Day Access","Hands-on Lab","Networking Dinner",E-Certificate}	available	2026-07-07 00:00:00	2026-10-04 00:00:00	2026-07-07 01:12:59.233119	2026-07-07 01:12:59.233119	\N
cb761609-ac74-4a43-b09c-f5ca6aa9ba56	e743f623-f41b-43c8-97d7-b6b048f0a86c	Free Pass	Gratis! Registrasi untuk konfirmasi kehadiran.	0.00	100	0	1	{"Akses Meetup",Snack,Networking}	available	2026-05-20 00:00:00	2026-08-17 00:00:00	2026-07-07 01:12:59.234798	2026-07-07 01:12:59.234798	\N
ddc5c90a-45cc-4c06-ad35-bd69f8b677d9	39a9ab59-029d-4048-99ad-3d7cb0c920fb	Penonton Harian	Tiket penonton 1 hari.	50000.00	300	0	5	{"Akses 1 Hari"}	available	2026-06-17 00:00:00	2026-09-14 00:00:00	2026-07-07 01:12:59.236741	2026-07-07 01:12:59.236741	\N
98cce4a6-fe79-4d29-8245-0c58e7789508	39a9ab59-029d-4048-99ad-3d7cb0c920fb	Penonton Full	Tiket penonton 3 hari + merchandise.	120000.00	150	0	3	{"Akses 3 Hari",Merchandise}	available	2026-06-17 00:00:00	2026-09-14 00:00:00	2026-07-07 01:12:59.238153	2026-07-07 01:12:59.238153	\N
a55f28d6-105c-4849-adc2-367935307f27	39a9ab59-029d-4048-99ad-3d7cb0c920fb	Tim Peserta	Pendaftaran tim (5 orang). Satu slot per tim.	250000.00	50	0	1	{"Slot Kompetisi","5 Player Pass",Bracket}	available	2026-06-17 00:00:00	2026-09-14 00:00:00	2026-07-07 01:12:59.239478	2026-07-07 01:12:59.239478	\N
7fe8d461-453d-4657-a803-072a1012127c	55e2a11f-b84c-4240-9c68-09fd14fb409b	Early Bird	Tiket early bird 2 hari harga spesial.	75000.00	500	0	4	{"2-Day Access"}	available	2026-06-29 00:00:00	2026-09-26 00:00:00	2026-07-07 01:12:59.241023	2026-07-07 01:12:59.241023	\N
2deb16c8-ac5d-4393-9e53-42967c07e432	55e2a11f-b84c-4240-9c68-09fd14fb409b	Regular	Tiket reguler 2 hari.	100000.00	2000	0	6	{"2-Day Access"}	available	2026-06-29 00:00:00	2026-09-26 00:00:00	2026-07-07 01:12:59.242302	2026-07-07 01:12:59.242302	\N
5dfb5956-d238-4d2c-ab6c-b1f230545c17	55e2a11f-b84c-4240-9c68-09fd14fb409b	VIP	Area VIP + merchandise + soundcheck access.	250000.00	200	0	2	{"VIP Area",Merchandise,"Soundcheck Access"}	available	2026-06-29 00:00:00	2026-09-26 00:00:00	2026-07-07 01:12:59.243587	2026-07-07 01:12:59.243587	\N
2b0dcf58-c476-4ccc-848b-10a9f727acb9	eda83126-377a-4b28-b44b-ef458f1eaae7	Bootcamp Pass	Akses 2 hari bootcamp + dataset + notebook.	500000.00	40	0	1	{"2-Day Access",Dataset,"Jupyter Notebook",E-Certificate}	available	2026-05-11 00:00:00	2026-08-08 00:00:00	2026-07-07 01:12:59.244988	2026-07-07 01:12:59.244988	\N
d5bee6d0-b036-4fc5-ae07-7b3246998501	eda83126-377a-4b28-b44b-ef458f1eaae7	Pelajar	Diskon 40% khusus pelajar/mahasiswa aktif.	300000.00	10	0	1	{"2-Day Access",Dataset,Notebook,E-Certificate}	available	2026-05-11 00:00:00	2026-08-08 00:00:00	2026-07-07 01:12:59.246333	2026-07-07 01:12:59.246333	\N
277929ad-fc74-46f7-b769-33279b8d1314	85173956-b502-439d-a285-0be667965271	Early Bird	Tiket early bird harga spesial. Termasuk lunch dan seminar kit.	350000.00	100	0	2	{Lunch,"Seminar Kit",E-Certificate,"Networking Session"}	available	2026-05-17 00:00:00	2026-08-14 00:00:00	2026-07-07 01:12:59.19766	2026-07-07 19:46:59.855096	2026-07-07 19:46:59.855096
e687f4ce-55d9-49c2-938f-64364b62dfcb	85173956-b502-439d-a285-0be667965271	Regular	Tiket reguler. Termasuk lunch, seminar kit, dan akses semua sesi.	500000.00	300	0	5	{Lunch,"Seminar Kit",E-Certificate}	available	2026-05-17 00:00:00	2026-08-14 00:00:00	2026-07-07 01:12:59.208418	2026-07-07 19:46:59.855096	2026-07-07 19:46:59.855096
565d5653-a1a5-458a-bd50-4c0ac1ab8ae5	b3c5f04d-2863-4a74-b9f2-765f163756e1	vip	\N	30000.00	10	0	5	\N	available	\N	\N	2026-07-08 03:21:28.92445	2026-07-08 03:31:52.103483	2026-07-08 03:31:52.103483
db668bc3-1320-40d7-94e6-8b6b84d09334	2f7c7417-5b21-4109-a42b-653ec7cb067b	Workshop + Mentoring	Workshop + 1 sesi mentoring pribadi setelah event.	500000.00	20	0	1	{Dataset,"Source Code",E-Certificate,Lunch,"1-on-1 Mentoring"}	available	2026-05-24 00:00:00	2026-08-21 00:00:00	2026-07-07 01:13:42.654474	2026-07-08 04:12:50.071728	2026-07-08 04:12:50.071728
08a181d9-2558-4b26-bffc-850eefb7789d	2f7c7417-5b21-4109-a42b-653ec7cb067b	Workshop Pass	Akses penuh workshop, dataset, source code, dan sertifikat.	350000.00	60	0	1	{Dataset,"Source Code",E-Certificate,Lunch}	available	2026-05-24 00:00:00	2026-08-21 00:00:00	2026-07-07 01:13:42.653165	2026-07-08 04:12:50.071728	2026-07-08 04:12:50.071728
312c4c4e-c548-4015-96bd-7800b076cbb9	b3c5f04d-2863-4a74-b9f2-765f163756e1	VIP	\N	150000.00	20	0	5	\N	available	\N	\N	2026-07-08 04:45:58.046396	2026-07-08 04:45:58.046396	\N
30c66966-56c1-4a53-b308-426b3ec6b9b4	0a019072-29ac-441c-8d3c-e52c71114f42	VIP Access	Akses VIP dengan seat priority, exclusive networking session, dan merchandise premium.	750000.00	30	0	2	{"Priority Seat","Networking Session","Premium Merchandise",Lunch,E-Certificate}	available	2025-10-01 00:00:00	2025-12-14 00:00:00	2026-07-04 00:21:49.963762	2026-07-07 19:46:32.542979	2026-07-07 19:46:32.542979
a45c271d-eb69-4f26-9332-b8b5b4cb1d14	31cb6533-5162-4799-90d7-65980692ebbb	Early Bird	Harga spesial + recording materi.	99000.00	100	0	3	{"Live Session",Recording,E-Certificate}	available	2025-08-27 00:00:00	2025-11-24 00:00:00	2026-07-07 01:13:42.65997	2026-07-07 19:46:43.841597	2026-07-07 19:46:43.841597
ea1adb35-2bc8-444a-b7c0-f4c70f1bef2f	85173956-b502-439d-a285-0be667965271	Early Bird	Tiket early bird harga spesial. Termasuk lunch dan seminar kit.	350000.00	100	0	2	{Lunch,"Seminar Kit",E-Certificate,"Networking Session"}	available	2026-05-17 00:00:00	2026-08-14 00:00:00	2026-07-07 01:13:42.644699	2026-07-07 19:46:59.855096	2026-07-07 19:46:59.855096
d6d04556-bd76-49ae-8129-fea0a9aaae87	85173956-b502-439d-a285-0be667965271	Regular	Tiket reguler. Termasuk lunch, seminar kit, dan akses semua sesi.	500000.00	300	0	5	{Lunch,"Seminar Kit",E-Certificate}	available	2026-05-17 00:00:00	2026-08-14 00:00:00	2026-07-07 01:13:42.648318	2026-07-07 19:46:59.855096	2026-07-07 19:46:59.855096
ca84a92a-57c3-4009-9022-a2d8ea73cb8a	e86105ce-a7ee-4a00-8d13-8f562d1ba54a	Conference Pass	Akses 2 hari konferensi + lunch.	299000.00	200	0	3	{"2-Day Access",Lunch,E-Certificate}	available	2026-07-07 00:00:00	2026-10-04 00:00:00	2026-07-07 01:13:42.671327	2026-07-08 01:58:28.252286	2026-07-08 01:58:28.252286
24b549f1-5762-4170-90ca-7069a7bd86a4	e86105ce-a7ee-4a00-8d13-8f562d1ba54a	VIP Pass	Akses VIP + hands-on lab + networking dinner.	599000.00	30	0	1	{"2-Day Access","Hands-on Lab","Networking Dinner",E-Certificate}	available	2026-07-07 00:00:00	2026-10-04 00:00:00	2026-07-07 01:13:42.672516	2026-07-08 01:58:28.252286	2026-07-08 01:58:28.252286
a7b25fea-2f16-474d-93ce-892dad7813d9	0a019072-29ac-441c-8d3c-e52c71114f42	Regular	Tiket reguler konferensi. Termasuk lunch dan seminar kit.	500000.00	150	1	5	{Lunch,"Seminar Kit",E-Certificate}	available	2025-10-01 00:00:00	2025-12-14 00:00:00	2026-07-04 00:21:49.963762	2026-07-07 19:46:32.542979	2026-07-07 19:46:32.542979
37464dc2-82ee-4407-8335-7f7869bc3e47	31cb6533-5162-4799-90d7-65980692ebbb	Early Bird	Harga spesial + recording materi.	99000.00	100	0	3	{"Live Session",Recording,E-Certificate}	available	2025-08-27 00:00:00	2025-11-24 00:00:00	2026-07-07 01:12:59.220316	2026-07-07 19:46:43.841597	2026-07-07 19:46:43.841597
43ab884d-7fb9-4886-81c2-26aa8a30eec0	31cb6533-5162-4799-90d7-65980692ebbb	Regular	Akses live session, recording, dan Q&A session.	150000.00	200	0	5	{"Live Session",Recording,Q&A,E-Certificate}	available	2025-08-27 00:00:00	2025-11-24 00:00:00	2026-07-07 01:12:59.221579	2026-07-07 19:46:43.841597	2026-07-07 19:46:43.841597
8734db77-f0b8-4a73-9b4f-ff2cd0755980	31cb6533-5162-4799-90d7-65980692ebbb	Regular	Akses live session, recording, dan Q&A session.	150000.00	200	0	5	{"Live Session",Recording,Q&A,E-Certificate}	available	2025-08-27 00:00:00	2025-11-24 00:00:00	2026-07-07 01:13:42.661205	2026-07-07 19:46:43.841597	2026-07-07 19:46:43.841597
80a348e7-6d65-432d-96c8-b65e71a34c37	85173956-b502-439d-a285-0be667965271	VIP Access	Akses VIP: priority seat, exclusive dinner, merchandise premium.	850000.00	50	0	2	{"Priority Seat","Exclusive Dinner",Merchandise,Lunch,E-Certificate}	available	2026-07-07 01:01:41.786626	2026-08-16 00:00:00	2026-07-07 01:01:41.786626	2026-07-07 19:46:59.855096	2026-07-07 19:46:59.855096
26578a7c-5fab-430a-93ef-28eff770cd45	85173956-b502-439d-a285-0be667965271	Pelajar	Tiket khusus pelajar/mahasiswa. Wajib tunjukkan KTM saat check-in.	150000.00	50	0	1	{"Seminar Kit",E-Certificate}	available	2026-07-07 01:01:41.787968	2026-08-16 00:00:00	2026-07-07 01:01:41.787968	2026-07-07 19:46:59.855096	2026-07-07 19:46:59.855096
1f915998-04f8-4ba8-a95a-537265ee10ab	85173956-b502-439d-a285-0be667965271	Early Bird	Tiket early bird harga spesial. Termasuk lunch dan seminar kit.	350000.00	100	0	2	{Lunch,"Seminar Kit",E-Certificate,"Networking Session"}	available	2026-07-07 01:02:06.556874	2026-08-14 00:00:00	2026-07-07 01:02:06.556874	2026-07-07 19:46:59.855096	2026-07-07 19:46:59.855096
6f15874a-042a-4dc4-ac32-0ea7514a6e5b	85173956-b502-439d-a285-0be667965271	Regular	Tiket reguler. Termasuk lunch, seminar kit, dan akses semua sesi.	500000.00	300	0	5	{Lunch,"Seminar Kit",E-Certificate}	available	2026-07-07 01:02:06.559813	2026-08-14 00:00:00	2026-07-07 01:02:06.559813	2026-07-07 19:46:59.855096	2026-07-07 19:46:59.855096
a63f7ad5-0f78-47f0-a99e-878378afae51	85173956-b502-439d-a285-0be667965271	VIP Access	Akses VIP: priority seat, exclusive dinner, merchandise premium.	850000.00	50	0	2	{"Priority Seat","Exclusive Dinner",Merchandise,Lunch,E-Certificate}	available	2026-07-07 01:02:06.56134	2026-08-14 00:00:00	2026-07-07 01:02:06.56134	2026-07-07 19:46:59.855096	2026-07-07 19:46:59.855096
a5331c30-e24c-4e33-a524-009cb920837f	85173956-b502-439d-a285-0be667965271	Pelajar	Tiket khusus pelajar/mahasiswa. Wajib tunjukkan KTM saat check-in.	150000.00	50	0	1	{"Seminar Kit",E-Certificate}	available	2026-07-07 01:02:06.562729	2026-08-14 00:00:00	2026-07-07 01:02:06.562729	2026-07-07 19:46:59.855096	2026-07-07 19:46:59.855096
b5367fbd-dbb6-449b-a535-f19a365d27cc	85173956-b502-439d-a285-0be667965271	Early Bird	Tiket early bird harga spesial. Termasuk lunch dan seminar kit.	350000.00	100	0	2	{Lunch,"Seminar Kit",E-Certificate,"Networking Session"}	available	2026-01-01 00:00:00	2026-08-14 00:00:00	2026-07-07 01:02:29.868928	2026-07-07 19:46:59.855096	2026-07-07 19:46:59.855096
01938ef4-301b-4b71-bd10-e2a655b167d2	85173956-b502-439d-a285-0be667965271	Regular	Tiket reguler. Termasuk lunch, seminar kit, dan akses semua sesi.	500000.00	300	0	5	{Lunch,"Seminar Kit",E-Certificate}	available	2026-01-01 00:00:00	2026-08-14 00:00:00	2026-07-07 01:02:29.871682	2026-07-07 19:46:59.855096	2026-07-07 19:46:59.855096
86313e34-9413-4dd7-a457-43a79c4cc5f1	85173956-b502-439d-a285-0be667965271	VIP Access	Akses VIP: priority seat, exclusive dinner, merchandise premium.	850000.00	50	0	2	{"Priority Seat","Exclusive Dinner",Merchandise,Lunch,E-Certificate}	available	2026-01-01 00:00:00	2026-08-14 00:00:00	2026-07-07 01:02:29.87305	2026-07-07 19:46:59.855096	2026-07-07 19:46:59.855096
4185dc88-24af-4ef6-aa04-2cf6f5114bd9	85173956-b502-439d-a285-0be667965271	Pelajar	Tiket khusus pelajar/mahasiswa. Wajib tunjukkan KTM saat check-in.	150000.00	50	0	1	{"Seminar Kit",E-Certificate}	available	2026-01-01 00:00:00	2026-08-14 00:00:00	2026-07-07 01:02:29.874223	2026-07-07 19:46:59.855096	2026-07-07 19:46:59.855096
c7f24c8d-7974-4dfe-a377-ef945611604f	85173956-b502-439d-a285-0be667965271	VIP Access	Akses VIP: priority seat, exclusive dinner, merchandise premium.	850000.00	50	0	2	{"Priority Seat","Exclusive Dinner",Merchandise,Lunch,E-Certificate}	available	2026-05-17 00:00:00	2026-08-14 00:00:00	2026-07-07 01:12:59.210196	2026-07-07 19:46:59.855096	2026-07-07 19:46:59.855096
f8d8ef98-ae77-42fc-ac6b-aad8511832c4	85173956-b502-439d-a285-0be667965271	Pelajar	Tiket khusus pelajar/mahasiswa. Wajib tunjukkan KTM saat check-in.	150000.00	50	0	1	{"Seminar Kit",E-Certificate}	available	2026-05-17 00:00:00	2026-08-14 00:00:00	2026-07-07 01:12:59.211785	2026-07-07 19:46:59.855096	2026-07-07 19:46:59.855096
f16655d4-dcb9-4458-89ab-4584336d76de	85173956-b502-439d-a285-0be667965271	VIP Access	Akses VIP: priority seat, exclusive dinner, merchandise premium.	850000.00	50	0	2	{"Priority Seat","Exclusive Dinner",Merchandise,Lunch,E-Certificate}	available	2026-05-17 00:00:00	2026-08-14 00:00:00	2026-07-07 01:13:42.649881	2026-07-07 19:46:59.855096	2026-07-07 19:46:59.855096
f291688a-e5a7-4465-9408-10dd00e759e2	85173956-b502-439d-a285-0be667965271	Pelajar	Tiket khusus pelajar/mahasiswa. Wajib tunjukkan KTM saat check-in.	150000.00	50	0	1	{"Seminar Kit",E-Certificate}	available	2026-05-17 00:00:00	2026-08-14 00:00:00	2026-07-07 01:13:42.651451	2026-07-07 19:46:59.855096	2026-07-07 19:46:59.855096
b3ee5010-721e-454e-9e05-f3678968d7cc	eda83126-377a-4b28-b44b-ef458f1eaae7	Pelajar	Diskon 40% khusus pelajar/mahasiswa aktif.	300000.00	10	0	1	{"2-Day Access",Dataset,Notebook,E-Certificate}	available	2026-05-11 00:00:00	2026-08-08 00:00:00	2026-07-07 01:13:42.685733	2026-07-08 01:58:28.252286	2026-07-08 01:58:28.252286
85b69a2b-61d7-443e-bc65-a618694d5452	39a9ab59-029d-4048-99ad-3d7cb0c920fb	Penonton Full	Tiket penonton 3 hari + merchandise.	120000.00	150	0	3	{"Akses 3 Hari",Merchandise}	available	2026-06-17 00:00:00	2026-09-14 00:00:00	2026-07-07 01:13:42.67727	2026-07-08 01:58:28.252286	2026-07-08 01:58:28.252286
c3bed2df-7217-4849-8bf7-945f3cfd483b	39a9ab59-029d-4048-99ad-3d7cb0c920fb	Penonton Harian	Tiket penonton 1 hari.	50000.00	300	0	5	{"Akses 1 Hari"}	available	2026-06-17 00:00:00	2026-09-14 00:00:00	2026-07-07 01:13:42.67608	2026-07-08 01:58:28.252286	2026-07-08 01:58:28.252286
f4f69bda-221d-4c94-adc0-cb32c890fbeb	39a9ab59-029d-4048-99ad-3d7cb0c920fb	Tim Peserta	Pendaftaran tim (5 orang). Satu slot per tim.	250000.00	50	0	1	{"Slot Kompetisi","5 Player Pass",Bracket}	available	2026-06-17 00:00:00	2026-09-14 00:00:00	2026-07-07 01:13:42.678476	2026-07-08 01:58:28.252286	2026-07-08 01:58:28.252286
d5b3f020-f808-42c4-acab-12fb6fd0068a	55e2a11f-b84c-4240-9c68-09fd14fb409b	Early Bird	Tiket early bird 2 hari harga spesial.	75000.00	500	0	4	{"2-Day Access"}	available	2026-06-29 00:00:00	2026-09-26 00:00:00	2026-07-07 01:13:42.680164	2026-07-08 01:58:28.252286	2026-07-08 01:58:28.252286
09852234-eab6-46a4-94c1-03e8365d72f9	427ba515-dfd7-41b7-ae5e-053002e15b49	Regular	\N	100000.00	20	1	5	\N	available	\N	\N	2026-07-07 20:07:47.52706	2026-07-07 20:43:33.370835	\N
8218dda5-c560-41f3-8242-32f219b9c1d0	427ba515-dfd7-41b7-ae5e-053002e15b49	VIP	\N	80000.00	50	0	5	\N	available	\N	\N	2026-07-07 20:44:19.114096	2026-07-07 21:04:09.852218	2026-07-07 21:04:09.852218
3d95d410-45e8-4b3f-9759-f577bb0486d2	eda83126-377a-4b28-b44b-ef458f1eaae7	Bootcamp Pass	Akses 2 hari bootcamp + dataset + notebook.	500000.00	40	0	1	{"2-Day Access",Dataset,"Jupyter Notebook",E-Certificate}	available	2026-05-11 00:00:00	2026-08-08 00:00:00	2026-07-07 01:13:42.684572	2026-07-08 01:58:28.252286	2026-07-08 01:58:28.252286
811fb304-656c-4e4d-93c2-14c4df30f5d3	55e2a11f-b84c-4240-9c68-09fd14fb409b	Regular	Tiket reguler 2 hari.	100000.00	2000	0	6	{"2-Day Access"}	available	2026-06-29 00:00:00	2026-09-26 00:00:00	2026-07-07 01:13:42.681725	2026-07-08 01:58:28.252286	2026-07-08 01:58:28.252286
40af307e-fb55-430b-83f6-668b5f9320bb	55e2a11f-b84c-4240-9c68-09fd14fb409b	VIP	Area VIP + merchandise + soundcheck access.	250000.00	200	0	2	{"VIP Area",Merchandise,"Soundcheck Access"}	available	2026-06-29 00:00:00	2026-09-26 00:00:00	2026-07-07 01:13:42.683043	2026-07-08 01:58:28.252286	2026-07-08 01:58:28.252286
602f6073-4c56-440c-877c-cb436a0c5114	e743f623-f41b-43c8-97d7-b6b048f0a86c	Free Pass	Gratis! Registrasi untuk konfirmasi kehadiran.	0.00	100	0	1	{"Akses Meetup",Snack,Networking}	available	2026-05-20 00:00:00	2026-08-17 00:00:00	2026-07-07 01:13:42.674429	2026-07-08 01:58:28.252286	2026-07-08 01:58:28.252286
e7efd7d3-db09-4600-82ff-a101dd976970	935b3682-2fdd-49f1-aa7c-a64aceef9bda	Bootcamp + Mentoring	Bootcamp + 2 sesi mentoring 1-on-1 pasca event.	1000000.00	10	0	1	{"3-Day Access",Materi,"Source Code","2x Mentoring",E-Certificate}	available	2026-05-30 00:00:00	2026-08-27 00:00:00	2026-07-07 01:13:42.666406	2026-07-08 01:58:28.252286	2026-07-08 01:58:28.252286
7ae6c5a2-74e0-4242-aaa0-9211767ad497	935b3682-2fdd-49f1-aa7c-a64aceef9bda	Bootcamp Pass	Akses 3 hari bootcamp + materi + sertifikat.	750000.00	50	0	1	{"3-Day Access","Materi PDF","Source Code",E-Certificate}	available	2026-05-30 00:00:00	2026-08-27 00:00:00	2026-07-07 01:13:42.665095	2026-07-08 01:58:28.252286	2026-07-08 01:58:28.252286
f7a04d4e-6768-4019-8bea-61488568dc6f	e9e2842e-8f47-403f-b6f8-00dba624e7cc	Workshop + Portfolio Review	Workshop + review portfolio by senior designer.	650000.00	5	0	1	{"2-Day Access","Figma Assets","Portfolio Review",E-Certificate}	available	2026-06-22 00:00:00	2026-09-19 00:00:00	2026-07-07 01:13:42.669592	2026-07-08 01:58:28.252286	2026-07-08 01:58:28.252286
c3d87026-b4bf-4e62-8dad-ab9cf77d35ec	e9e2842e-8f47-403f-b6f8-00dba624e7cc	Workshop Pass	Akses 2 hari workshop Figma + materi.	450000.00	35	0	1	{"2-Day Access","Figma Assets",E-Certificate}	available	2026-06-22 00:00:00	2026-09-19 00:00:00	2026-07-07 01:13:42.668056	2026-07-08 01:58:28.252286	2026-07-08 01:58:28.252286
9585c3dd-73eb-4a5f-b900-ce9b228972df	b759906a-6451-48af-8d3b-c001c3bd5a49	Day Pass	Akses 1 hari tanpa menginap. Termasuk 2 sesi yoga dan lunch.	400000.00	20	0	2	{"Day Access","2 Yoga Sessions",Lunch}	available	2025-09-01 00:00:00	2025-11-29 00:00:00	2026-07-07 01:12:59.224468	2026-07-08 01:58:28.252286	2026-07-08 01:58:28.252286
6e4a6507-0e58-4bfe-9f77-192c15af9f95	b759906a-6451-48af-8d3b-c001c3bd5a49	Day Pass	Akses 1 hari tanpa menginap. Termasuk 2 sesi yoga dan lunch.	400000.00	20	0	2	{"Day Access","2 Yoga Sessions",Lunch}	available	2025-09-01 00:00:00	2025-11-29 00:00:00	2026-07-07 01:13:42.663734	2026-07-08 01:58:28.252286	2026-07-08 01:58:28.252286
39ea7dee-74a8-4f86-8039-1b23e107ab09	b759906a-6451-48af-8d3b-c001c3bd5a49	Full Package	Akomodasi 1 malam, 4 sesi yoga, all meals, dan workshop.	1200000.00	30	0	2	{Akomodasi,"All Meals","4 Yoga Sessions","Mindfulness Workshop"}	available	2025-09-01 00:00:00	2025-11-29 00:00:00	2026-07-07 01:12:59.223152	2026-07-08 01:58:28.252286	2026-07-08 01:58:28.252286
65077aab-b07d-4075-bc4a-56264a13742e	b759906a-6451-48af-8d3b-c001c3bd5a49	Full Package	Akomodasi 1 malam, 4 sesi yoga, all meals, dan workshop.	1200000.00	30	0	2	{Akomodasi,"All Meals","4 Yoga Sessions","Mindfulness Workshop"}	available	2025-09-01 00:00:00	2025-11-29 00:00:00	2026-07-07 01:13:42.662586	2026-07-08 01:58:28.252286	2026-07-08 01:58:28.252286
bf1d669f-18fd-4b47-8b36-6bcd6cfa0b86	39a9ab59-029d-4048-99ad-3d7cb0c920fb	Regular	\N	12000.00	10	0	5	\N	available	\N	\N	2026-07-08 03:29:02.705549	2026-07-08 03:30:15.078364	2026-07-08 03:30:15.078364
29876d25-4cfb-45e3-83a3-355f5bee609b	93318dae-7097-46e4-afe0-4c78511b0429	General Pass	Akses 3 hari semua sesi dan networking.	499000.00	600	0	5	{"3-Day Access",E-Certificate}	available	2025-10-12 00:00:00	2026-01-09 00:00:00	2026-07-07 01:13:42.655973	2026-07-08 04:11:07.575699	2026-07-08 04:11:07.575699
7e1f2e5a-a8f1-406a-9082-abc834817c0b	93318dae-7097-46e4-afe0-4c78511b0429	Investor Pass	Akses khusus investor: private meeting room dan pitch session.	999000.00	100	0	2	{"3-Day Access","Private Meeting","Gala Dinner",E-Certificate}	available	2025-10-12 00:00:00	2026-01-09 00:00:00	2026-07-07 01:13:42.657205	2026-07-08 04:11:07.575699	2026-07-08 04:11:07.575699
49126773-ab6b-479c-83f8-b66b511947de	93318dae-7097-46e4-afe0-4c78511b0429	Startup Package	Paket startup: booth pameran + 3 tiket + slot pitching.	1500000.00	50	0	1	{Booth,"3 Tiket","Pitching Slot",E-Certificate}	available	2025-10-12 00:00:00	2026-01-09 00:00:00	2026-07-07 01:13:42.658424	2026-07-08 04:11:07.575699	2026-07-08 04:11:07.575699
5e88c196-3953-448c-ae02-3fb2f98a42ac	93318dae-7097-46e4-afe0-4c78511b0429	Startup Package	Paket startup: booth pameran + 3 tiket + slot pitching.	1500000.00	50	0	1	{Booth,"3 Tiket","Pitching Slot",E-Certificate}	available	2025-10-12 00:00:00	2026-01-09 00:00:00	2026-07-07 01:12:59.218761	2026-07-08 04:11:07.575699	2026-07-08 04:11:07.575699
\.


--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.users (id, name, email, password_hash, phone, avatar_url, role, status, email_verified_at, last_login_at, created_at, updated_at, deleted_at) FROM stdin;
de9e760f-abf0-4223-8fc0-7d867e517d16	Sari Peserta	sari@eventbot.com	$2b$12$eQm4jEJAt/91PYDIoKIXpuFzXo9jgfHK2T0fwR6urO1MN7Om84dAG	082345678901	\N	participant	active	2026-07-07 01:01:41.451059	\N	2026-07-07 01:01:41.451059	2026-07-07 01:01:41.451059	\N
965dbfb5-a4a1-4f6d-9721-12a1083648ef	Ahmad Rizki	ahmad@eventbot.com	$2b$12$eQm4jEJAt/91PYDIoKIXpuFzXo9jgfHK2T0fwR6urO1MN7Om84dAG	083456789012	\N	participant	active	2026-07-07 01:01:41.453958	\N	2026-07-07 01:01:41.453958	2026-07-07 01:01:41.453958	\N
38cd080b-abda-4d9b-b6e6-1180e5cb2292	Reza Pratama	reza@eventbot.com	$2b$12$eQm4jEJAt/91PYDIoKIXpuFzXo9jgfHK2T0fwR6urO1MN7Om84dAG	085678901234	\N	participant	active	2026-07-07 01:01:41.456764	\N	2026-07-07 01:01:41.456764	2026-07-07 01:01:41.456764	\N
7e54f2d6-d384-4f00-a50e-6dcd7418cade	Dewi Lestari	dewi@eventbot.com	$2b$12$eQm4jEJAt/91PYDIoKIXpuFzXo9jgfHK2T0fwR6urO1MN7Om84dAG	084567890123	\N	participant	active	2026-07-07 01:01:41.455388	\N	2026-07-07 01:01:41.455388	2026-07-08 02:04:21.240141	2026-07-08 02:04:21.240141
4dde6422-d264-40e1-b6dc-191a4717d912	Eko Susanto	eko@eventbot.com	$2b$12$eQm4jEJAt/91PYDIoKIXpuFzXo9jgfHK2T0fwR6urO1MN7Om84dAG	087890123456	\N	admin	active	2026-07-07 01:01:41.45948	\N	2026-07-07 01:01:41.45948	2026-07-08 02:08:45.814284	\N
d8cb7f23-0d86-4fca-a221-b4aca2b6a134	Ogi Bastian	example@eventbot.com	$2b$12$IwG5Lm2ObCfVqdcw8GBGJuiFIYdJaykLr0OCF.SF.jpK.4jxLQeAa	\N	\N	participant	active	\N	2026-07-08 02:28:23.171635	2026-07-08 02:10:08.62714	2026-07-08 03:33:42.86982	\N
55fbcee3-6fdc-474f-98ab-8939b8b7ae88	Budi Organizer	budi@eventbot.com	$2b$12$VRs7bZ8fsiDdaagDI2HFmukx83dQUrIOf44OTaj3tIAH6inZu33Ti	081234567890	\N	participant	active	2026-07-04 00:21:49.963762	2026-07-08 02:24:55.808867	2026-07-04 00:21:49.963762	2026-07-08 03:34:03.350453	2026-07-08 03:34:03.350453
96384a65-d4a5-46aa-89b0-33783e975314	John Doe	peserta@eventbot.com	$2b$12$XPJKINB7giY8pejcFwFSo.OLSqaZZCrGHaJ4nWVV3U2HWQdXRHOXK	\N	\N	participant	active	\N	2026-07-07 00:21:39.052103	2026-07-07 00:21:17.496042	2026-07-08 03:39:36.168959	2026-07-08 03:39:36.168959
97029625-6012-43ba-a474-b498aa453c85	John Doe	doe@eventbot.com	$2b$12$u2xGY7G0Wt7FiphlpfckqONmclAQjmd61gsJnNTNttx.sbXPrtccK	\N	\N	participant	active	\N	\N	2026-07-08 03:40:23.312955	2026-07-08 03:40:40.368753	2026-07-08 03:40:40.368753
af8764bc-db84-48eb-8196-3cbc53397abe	Rina Wulandari	rina@eventbot.com	$2b$12$eQm4jEJAt/91PYDIoKIXpuFzXo9jgfHK2T0fwR6urO1MN7Om84dAG	086789012345	\N	participant	active	2026-07-07 01:01:41.458187	2026-07-08 04:35:22.572007	2026-07-07 01:01:41.458187	2026-07-08 04:35:22.572007	\N
aed90366-01e7-448d-ac18-5827ee6e58f0	Admin EventBot	admin@eventbot.com	$2b$12$VRs7bZ8fsiDdaagDI2HFmukx83dQUrIOf44OTaj3tIAH6inZu33Ti	\N	\N	admin	active	2026-07-04 00:21:49.963762	2026-07-08 04:35:34.694987	2026-07-04 00:21:49.963762	2026-07-08 04:35:34.694987	\N
\.


--
-- Name: categories categories_name_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.categories
    ADD CONSTRAINT categories_name_key UNIQUE (name);


--
-- Name: categories categories_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.categories
    ADD CONSTRAINT categories_pkey PRIMARY KEY (id);


--
-- Name: categories categories_slug_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.categories
    ADD CONSTRAINT categories_slug_key UNIQUE (slug);


--
-- Name: chat_messages chat_messages_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.chat_messages
    ADD CONSTRAINT chat_messages_pkey PRIMARY KEY (id);


--
-- Name: chat_sessions chat_sessions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.chat_sessions
    ADD CONSTRAINT chat_sessions_pkey PRIMARY KEY (id);


--
-- Name: chat_sessions chat_sessions_session_token_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.chat_sessions
    ADD CONSTRAINT chat_sessions_session_token_key UNIQUE (session_token);


--
-- Name: event_categories event_categories_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.event_categories
    ADD CONSTRAINT event_categories_pkey PRIMARY KEY (event_id, category_id);


--
-- Name: events events_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.events
    ADD CONSTRAINT events_pkey PRIMARY KEY (id);


--
-- Name: events events_slug_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.events
    ADD CONSTRAINT events_slug_key UNIQUE (slug);


--
-- Name: knowledge_base knowledge_base_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.knowledge_base
    ADD CONSTRAINT knowledge_base_pkey PRIMARY KEY (id);


--
-- Name: registrations registrations_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.registrations
    ADD CONSTRAINT registrations_pkey PRIMARY KEY (id);


--
-- Name: system_settings system_settings_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.system_settings
    ADD CONSTRAINT system_settings_pkey PRIMARY KEY (key);


--
-- Name: tickets tickets_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tickets
    ADD CONSTRAINT tickets_pkey PRIMARY KEY (id);


--
-- Name: users users_email_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_email_key UNIQUE (email);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: idx_chat_messages_created; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_chat_messages_created ON public.chat_messages USING btree (created_at DESC);


--
-- Name: idx_chat_messages_session; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_chat_messages_session ON public.chat_messages USING btree (session_id);


--
-- Name: idx_chat_sessions_token; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_chat_sessions_token ON public.chat_sessions USING btree (session_token);


--
-- Name: idx_chat_sessions_user; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_chat_sessions_user ON public.chat_sessions USING btree (user_id);


--
-- Name: idx_events_dates; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_events_dates ON public.events USING btree (start_date, end_date) WHERE (deleted_at IS NULL);


--
-- Name: idx_events_organizer; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_events_organizer ON public.events USING btree (organizer_id) WHERE (deleted_at IS NULL);


--
-- Name: idx_events_published; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_events_published ON public.events USING btree (published_at DESC) WHERE ((is_published = true) AND (deleted_at IS NULL));


--
-- Name: idx_events_search; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_events_search ON public.events USING gin (to_tsvector('indonesian'::regconfig, (((((COALESCE(title, ''::character varying))::text || ' '::text) || COALESCE(description, ''::text)) || ' '::text) || (COALESCE(location, ''::character varying))::text)));


--
-- Name: idx_events_slug; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_events_slug ON public.events USING btree (slug) WHERE (deleted_at IS NULL);


--
-- Name: idx_events_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_events_status ON public.events USING btree (status) WHERE ((deleted_at IS NULL) AND (is_published = true));


--
-- Name: idx_kb_category; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_kb_category ON public.knowledge_base USING btree (category) WHERE (is_active = true);


--
-- Name: idx_kb_keywords; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_kb_keywords ON public.knowledge_base USING gin (keywords) WHERE (is_active = true);


--
-- Name: idx_registrations_created; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_registrations_created ON public.registrations USING btree (created_at DESC);


--
-- Name: idx_registrations_event; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_registrations_event ON public.registrations USING btree (event_id) WHERE (cancelled_at IS NULL);


--
-- Name: idx_registrations_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_registrations_status ON public.registrations USING btree (status);


--
-- Name: idx_registrations_ticket; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_registrations_ticket ON public.registrations USING btree (ticket_id) WHERE (cancelled_at IS NULL);


--
-- Name: idx_registrations_user; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_registrations_user ON public.registrations USING btree (user_id) WHERE (cancelled_at IS NULL);


--
-- Name: idx_tickets_event; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_tickets_event ON public.tickets USING btree (event_id) WHERE (deleted_at IS NULL);


--
-- Name: idx_tickets_price; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_tickets_price ON public.tickets USING btree (price) WHERE (deleted_at IS NULL);


--
-- Name: idx_tickets_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_tickets_status ON public.tickets USING btree (status) WHERE (deleted_at IS NULL);


--
-- Name: idx_users_created_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_users_created_at ON public.users USING btree (created_at DESC);


--
-- Name: idx_users_email; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_users_email ON public.users USING btree (email) WHERE (deleted_at IS NULL);


--
-- Name: idx_users_role; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_users_role ON public.users USING btree (role) WHERE (deleted_at IS NULL);


--
-- Name: idx_users_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_users_status ON public.users USING btree (status) WHERE (deleted_at IS NULL);


--
-- Name: chat_messages trg_chat_messages_activity; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_chat_messages_activity AFTER INSERT ON public.chat_messages FOR EACH ROW EXECUTE FUNCTION public.update_chat_session_activity();


--
-- Name: events trg_events_generate_slug; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_events_generate_slug BEFORE INSERT OR UPDATE OF title ON public.events FOR EACH ROW EXECUTE FUNCTION public.generate_slug();


--
-- Name: events trg_events_set_published; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_events_set_published BEFORE UPDATE ON public.events FOR EACH ROW EXECUTE FUNCTION public.set_published_at();


--
-- Name: events trg_events_updated_at; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_events_updated_at BEFORE UPDATE ON public.events FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- Name: knowledge_base trg_knowledge_base_updated_at; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_knowledge_base_updated_at BEFORE UPDATE ON public.knowledge_base FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- Name: registrations trg_registrations_update_sold; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_registrations_update_sold AFTER INSERT OR UPDATE ON public.registrations FOR EACH ROW EXECUTE FUNCTION public.update_ticket_sold_count();


--
-- Name: registrations trg_registrations_updated_at; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_registrations_updated_at BEFORE UPDATE ON public.registrations FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- Name: tickets trg_tickets_updated_at; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_tickets_updated_at BEFORE UPDATE ON public.tickets FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- Name: users trg_users_prevent_delete; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_users_prevent_delete BEFORE DELETE ON public.users FOR EACH ROW EXECUTE FUNCTION public.prevent_organizer_delete();


--
-- Name: users trg_users_updated_at; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_users_updated_at BEFORE UPDATE ON public.users FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- Name: registrations trg_validate_registration; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_validate_registration BEFORE INSERT ON public.registrations FOR EACH ROW EXECUTE FUNCTION public.validate_ticket_before_registration();


--
-- Name: chat_messages chat_messages_session_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.chat_messages
    ADD CONSTRAINT chat_messages_session_id_fkey FOREIGN KEY (session_id) REFERENCES public.chat_sessions(id) ON DELETE CASCADE;


--
-- Name: chat_sessions chat_sessions_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.chat_sessions
    ADD CONSTRAINT chat_sessions_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: event_categories event_categories_category_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.event_categories
    ADD CONSTRAINT event_categories_category_id_fkey FOREIGN KEY (category_id) REFERENCES public.categories(id) ON DELETE CASCADE;


--
-- Name: event_categories event_categories_event_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.event_categories
    ADD CONSTRAINT event_categories_event_id_fkey FOREIGN KEY (event_id) REFERENCES public.events(id) ON DELETE CASCADE;


--
-- Name: events events_organizer_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.events
    ADD CONSTRAINT events_organizer_id_fkey FOREIGN KEY (organizer_id) REFERENCES public.users(id) ON DELETE RESTRICT;


--
-- Name: registrations registrations_checked_in_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.registrations
    ADD CONSTRAINT registrations_checked_in_by_fkey FOREIGN KEY (checked_in_by) REFERENCES public.users(id);


--
-- Name: registrations registrations_event_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.registrations
    ADD CONSTRAINT registrations_event_id_fkey FOREIGN KEY (event_id) REFERENCES public.events(id) ON DELETE RESTRICT;


--
-- Name: registrations registrations_ticket_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.registrations
    ADD CONSTRAINT registrations_ticket_id_fkey FOREIGN KEY (ticket_id) REFERENCES public.tickets(id) ON DELETE RESTRICT;


--
-- Name: registrations registrations_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.registrations
    ADD CONSTRAINT registrations_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE RESTRICT;


--
-- Name: tickets tickets_event_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tickets
    ADD CONSTRAINT tickets_event_id_fkey FOREIGN KEY (event_id) REFERENCES public.events(id) ON DELETE CASCADE;


--
-- PostgreSQL database dump complete
--

\unrestrict ShPfWhUSwh3JeELSQ3d1zHd53AQGxKwCyTP9ZGOLp6Iry6DN6kk5FCRUVmf8EF2

