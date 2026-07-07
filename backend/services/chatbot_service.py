"""
Chatbot Service
===============
Business logic untuk chatbot - integrasi NLP + Database.
"""

from backend.nlp.regex_rules import match_intent, extract_entities
from backend.nlp.response_templates import ResponseBuilder
from backend.nlp.context_manager import ContextManager
from backend.models import ChatSessionModel, ChatMessageModel, KnowledgeBaseModel, EventModel, SystemSettingsModel
from backend.config import generate_session_token
from typing import Dict, List, Optional


class ChatbotService:
    """Service utama chatbot - mengorkestrasi NLP + Database + Context."""

    def __init__(self):
        self.response_builder = ResponseBuilder()
        self.context_manager = ContextManager()

    def process_message(self, message: str, session_token: str = None, 
                        user_id: str = None) -> Dict:
        """
        Proses pesan user dan kembalikan respons.

        Returns:
            {
                "response": str,
                "intent": str,
                "entities": dict,
                "session_token": str,
                "quick_replies": list
            }
        """
        # 1. Get atau buat session
        if session_token:
            session = ChatSessionModel.get_by_token(session_token)
        else:
            session = None

        if not session:
            session = ChatSessionModel.create(user_id=user_id)
            session_token = session['session_token'] if session else generate_session_token()
        else:
            session_token = session['session_token']

        session_id = session['id'] if session else None

        # 2. Detect intent
        intent = match_intent(message)

        # 3. Extract entities
        entities = extract_entities(message)

        # 4. Get context (conversation history)
        context = self.context_manager.get_context(session_id) if session_id else {}

        # 5. Build response berdasarkan intent
        response_data = self._build_response(intent, entities, context, user_id, message)

        # 6. Save chat history
        if session_id:
            ChatMessageModel.create(session_id, 'user', message, intent, entities)
            ChatMessageModel.create(session_id, 'assistant', response_data['response'], intent, None)

            # Update context
            self.context_manager.update_context(session_id, intent, entities, response_data)

        return {
            "response": response_data['response'],
            "intent": intent,
            "entities": entities,
            "session_token": session_token,
            "quick_replies": response_data.get('quick_replies', [])
        }

    def _build_response(self, intent: str, entities: Dict, context: Dict, 
                        user_id: str = None, message: str = None) -> Dict:
        """Build response berdasarkan intent."""

        if intent == 'sapaan':
            return self.response_builder.greeting()

        elif intent == 'tanya_bantuan':
            return self.response_builder.help_menu()

        elif intent == 'cari_event':
            return self._handle_search_event(entities, context)

        elif intent == 'detail_event':
            return self._handle_event_detail(entities, context)

        elif intent == 'daftar_tiket':
            return self._handle_booking(entities, context, user_id)

        elif intent == 'lihat_jadwal':
            return self._handle_user_schedule(user_id)

        elif intent == 'profil':
            return self._handle_user_profile(user_id)

        elif intent == 'keluar':
            return self.response_builder.goodbye()

        else:
            # Fallback: coba cari di knowledge base
            kb_results = KnowledgeBaseModel.search(message, limit=1)
            if kb_results:
                return {"response": kb_results[0]['answer'], "quick_replies": []}

            return self.response_builder.fallback()

    def _handle_search_event(self, entities: Dict, context: Dict) -> Dict:
        """Handle pencarian event."""
        location = entities.get('location')
        category = entities.get('category')
        date = entities.get('date')

        # entities.get() mengembalikan list — ambil elemen pertama jika ada
        location_str = location[0] if isinstance(location, list) and location else location
        category_str = category[0] if isinstance(category, list) and category else category
        date_str = date[0] if isinstance(date, list) and date else date
        query_list = entities.get('query')
        query_str = query_list[0] if isinstance(query_list, list) and query_list else query_list

        # Search via database
        events = EventModel.search(
            query=query_str,
            location=location_str,
            category_slug=category_str,
            start_date=date_str,
            limit=5
        )

        return self.response_builder.event_list(events, location_str, category_str)

    def _handle_event_detail(self, entities: Dict, context: Dict) -> Dict:
        """Handle detail event."""
        event_name_raw = entities.get('event_name')
        # entities.get() mengembalikan list — ambil elemen pertama jika ada
        event_name = (
            event_name_raw[0]
            if isinstance(event_name_raw, list) and event_name_raw
            else event_name_raw
        )

        if not event_name and context.get('last_event_id'):
            # Ambil dari context (event yang baru dibahas)
            event = EventModel.get_by_id(context['last_event_id'])
        elif event_name:
            # Search by name
            events = EventModel.search(query=event_name, limit=1)
            event = events[0] if events else None
        else:
            event = None

        if event:
            return self.response_builder.event_detail(event)

        return {"response": "Maaf, saya tidak menemukan event tersebut. Coba ketik nama event dengan benar.", "quick_replies": ["🔍 Cari Event", "❓ Bantuan"]}

    def _handle_booking(self, entities: Dict, context: Dict, user_id: str) -> Dict:
        """Handle booking tiket."""
        if not user_id:
            return {"response": "Silakan login terlebih dahulu untuk mendaftar event. Klik menu Login di atas.", "quick_replies": ["🔐 Login", "🔍 Cari Event"]}

        # Logic booking...
        return {"response": "Fitur booking sedang dalam pengembangan. Silakan hubungi admin.", "quick_replies": []}

    def _handle_user_schedule(self, user_id: str) -> Dict:
        """Handle lihat jadwal user."""
        if not user_id:
            return {"response": "Silakan login untuk melihat jadwal event Anda.", "quick_replies": ["🔐 Login"]}

        from backend.models import RegistrationModel
        regs = RegistrationModel.get_by_user(user_id, status='confirmed')
        return self.response_builder.user_schedule(regs)

    def _handle_user_profile(self, user_id: str) -> Dict:
        """Handle profil user."""
        if not user_id:
            return {"response": "Silakan login untuk melihat profil.", "quick_replies": ["🔐 Login"]}

        from backend.models import UserModel
        user = UserModel.get_by_id(user_id)
        return self.response_builder.user_profile(user)

    def get_chat_history(self, session_token: str) -> List[Dict]:
        """Ambil history chat."""
        session = ChatSessionModel.get_by_token(session_token)
        if session:
            return ChatMessageModel.get_history(session['id'])
        return []