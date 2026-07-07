"""
Backend Test Script
===================
Test semua komponen backend sebelum lanjut ke frontend.

Usage:
    python backend/tests/test_backend.py

Requirements:
    pip install psycopg2-binary python-dotenv
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

print("=" * 60)
print("  🔧 EVENTBOT BACKEND TEST")
print("=" * 60)

# ── TEST 1: Config & Database Connection ───────────────────
print("\n📦 TEST 1: Config & Database Connection")
print("-" * 40)

try:
    from backend.config import test_connection as check_db_connection, get_table_count, table_exists
    if check_db_connection():
        print("   ✅ Database connected")
    else:
        print("   ❌ Database connection failed")
        sys.exit(1)
except Exception as e:
    print(f"   ❌ Error: {e}")
    sys.exit(1)

# ── TEST 2: Check Tables ────────────────────────────────────
print("\n📦 TEST 2: Check Tables")
print("-" * 40)

tables = ['users', 'categories', 'events', 'event_categories', 
          'tickets', 'registrations', 'chat_sessions', 'chat_messages',
          'knowledge_base', 'system_settings']

all_ok = True
for table in tables:
    exists = table_exists(table)
    count = get_table_count(table) if exists else 0
    status = "✅" if exists else "❌"
    print(f"   {status} {table}: {count} rows")
    if not exists:
        all_ok = False

if not all_ok:
    print("\n   ⚠️  Jalankan: python backend/scripts/init_db.py")
    sys.exit(1)

# ── TEST 3: Models ────────────────────────────────────────
print("\n📦 TEST 3: Models")
print("-" * 40)

try:
    from backend.models import UserModel, EventModel, TicketModel, RegistrationModel
    from backend.models import CategoryModel, ChatSessionModel, ChatMessageModel
    from backend.models import KnowledgeBaseModel, SystemSettingsModel
    print("   ✅ All models imported")
except Exception as e:
    print(f"   ❌ Model import error: {e}")
    sys.exit(1)

# ── TEST 4: User Operations ─────────────────────────────────
print("\n📦 TEST 4: User Operations")
print("-" * 40)

try:
    # Get admin user
    admin = UserModel.get_by_email('admin@eventbot.com')
    if admin:
        print(f"   ✅ Admin found: {admin['name']} ({admin['role']})")
    else:
        print("   ❌ Admin not found")

    # Get organizer
    org = UserModel.get_by_email('budi@eventbot.com')
    if org:
        print(f"   ✅ Organizer found: {org['name']} ({org['role']})")

    # Count users
    total = UserModel.count()
    print(f"   ✅ Total users: {total}")

except Exception as e:
    print(f"   ❌ User test error: {e}")

# ── TEST 5: Event Operations ────────────────────────────────
print("\n📦 TEST 5: Event Operations")
print("-" * 40)

try:
    # Search events
    events = EventModel.search(limit=3)
    print(f"   ✅ Found {len(events)} events")

    if events:
        first = events[0]
        print(f"   📌 First: {first['title']} @ {first['location']}")

        # Get detail
        detail = EventModel.get_by_id(first['id'])
        if detail:
            print(f"   ✅ Detail loaded: {detail.get('title', 'N/A')}")

except Exception as e:
    print(f"   ❌ Event test error: {e}")

# ── TEST 6: Ticket Operations ───────────────────────────────
print("\n📦 TEST 6: Ticket Operations")
print("-" * 40)

try:
    # Get event tickets
    if events:
        tickets = TicketModel.get_by_event(events[0]['id'])
        print(f"   ✅ Found {len(tickets)} tickets for first event")

        if tickets:
            avail = TicketModel.check_availability(tickets[0]['id'])
            if avail:
                print(f"   📌 Available: {avail['available']}, Remaining: {avail['remaining']}")

except Exception as e:
    print(f"   ❌ Ticket test error: {e}")

# ── TEST 7: NLP Engine ──────────────────────────────────────
print("\n📦 TEST 7: NLP Engine")
print("-" * 40)

try:
    from backend.nlp import match_intent, extract_entities

    # Test intents
    test_cases = [
        ("halo", "sapaan"),
        ("cari event di jakarta", "cari_event"),
        ("bantuan", "tanya_bantuan"),
        ("detail tech conference", "detail_event"),
        ("daftar tiket", "daftar_tiket"),
        ("jadwal saya", "lihat_jadwal"),
        ("profil", "profil"),
        ("bye", "keluar"),
    ]

    for text, expected in test_cases:
        intent = match_intent(text)
        status = "✅" if intent == expected else "⚠️"
        print(f"   {status} '{text}' -> {intent} (expected: {expected})")

    # Test entity extraction
    entities = extract_entities("cari event teknologi di jakarta")
    print(f"   ✅ Entities: {entities}")

except Exception as e:
    print(f"   ❌ NLP test error: {e}")

# ── TEST 8: Chatbot Service ─────────────────────────────────
print("\n📦 TEST 8: Chatbot Service")
print("-" * 40)

try:
    from backend.services import ChatbotService

    bot = ChatbotService()

    # Test greeting
    result = bot.process_message("halo")
    print(f"   ✅ Greeting response: {result['response'][:50]}...")
    print(f"   📌 Intent: {result['intent']}")
    print(f"   📌 Quick replies: {len(result['quick_replies'])} items")

    # Test search
    result2 = bot.process_message("cari event", session_token=result['session_token'])
    print(f"   ✅ Search response: {result2['response'][:50]}...")

    # Test help
    result3 = bot.process_message("bantuan", session_token=result['session_token'])
    print(f"   ✅ Help response: {result3['response'][:50]}...")

    # Get chat history
    history = bot.get_chat_history(result['session_token'])
    print(f"   ✅ Chat history: {len(history)} messages")

except Exception as e:
    print(f"   ❌ Chatbot test error: {e}")
    import traceback
    traceback.print_exc()

# ── TEST 9: Services ──────────────────────────────────────
print("\n📦 TEST 9: Services")
print("-" * 40)

try:
    from backend.services import AuthService, EventService, TicketService

    # Auth service
    login_result = AuthService.login('admin@eventbot.com', 'admin123')
    if login_result.get('success'):
        print(f"   ✅ AuthService.login: success")
    else:
        print(f"   ⚠️  AuthService.login: {login_result.get('message')}")

    # Event service
    search_result = EventService.search_events(location='Jakarta', limit=3)
    print(f"   ✅ EventService.search: {len(search_result)} events")

    # Ticket service
    if events:
        stats = TicketService.get_ticket_stats(events[0]['id'])
        if stats:
            print(f"   ✅ TicketService.stats: {stats}")

except Exception as e:
    print(f"   ❌ Service test error: {e}")

# ── TEST 10: Knowledge Base ─────────────────────────────────
print("\n📦 TEST 10: Knowledge Base")
print("-" * 40)

try:
    results = KnowledgeBaseModel.search("event gratis", limit=2)
    print(f"   ✅ KB search: {len(results)} results")

    if results:
        print(f"   📌 Q: {results[0]['question'][:50]}...")
        print(f"   📌 A: {results[0]['answer'][:50]}...")

except Exception as e:
    print(f"   ❌ KB test error: {e}")

# ── SUMMARY ─────────────────────────────────────────────────
print("\n" + "=" * 60)
print("  ✅ BACKEND TEST COMPLETE")
print("=" * 60)
print("\nJika semua test ✅, backend siap untuk frontend.")
print("Jika ada ❌, periksa error dan jalankan ulang init_db.py")