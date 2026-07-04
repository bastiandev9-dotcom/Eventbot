"""
Context Manager
===============
Manajemen state percakapan chatbot.
"""

from typing import Dict, Optional
from collections import defaultdict


class ContextManager:
    """Manager untuk context/conversation state."""

    def __init__(self):
        # In-memory context storage (gunakan Redis untuk production)
        self._contexts = defaultdict(dict)

    def get_context(self, session_id: str) -> Dict:
        """Ambil context untuk session."""
        return self._contexts.get(session_id, {})

    def update_context(self, session_id: str, intent: str, 
                       entities: Dict, response: Dict) -> None:
        """Update context setelah interaksi."""
        context = self._contexts[session_id]

        # Update last intent
        context['last_intent'] = intent

        # Update last entities
        context['last_entities'] = entities

        # Track last event discussed
        if 'event_id' in entities:
            context['last_event_id'] = entities['event_id']

        # Track event from response
        if 'event' in response:
            context['last_event_id'] = response['event'].get('id')

        # Increment interaction count
        context['interaction_count'] = context.get('interaction_count', 0) + 1

        # Store last response type
        context['last_response_type'] = response.get('type', 'text')

    def clear_context(self, session_id: str) -> None:
        """Clear context untuk session."""
        if session_id in self._contexts:
            del self._contexts[session_id]

    def get_last_event(self, session_id: str) -> Optional[str]:
        """Ambil event ID terakhir yang dibahas."""
        context = self._contexts.get(session_id, {})
        return context.get('last_event_id')

    def get_conversation_turn(self, session_id: str) -> int:
        """Ambil jumlah turn percakapan."""
        context = self._contexts.get(session_id, {})
        return context.get('interaction_count', 0)