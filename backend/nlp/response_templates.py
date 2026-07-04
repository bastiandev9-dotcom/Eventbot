"""
Response Templates
==================
Builder untuk respons chatbot yang dinamis & rich.
"""

from backend.models import SystemSettingsModel
from typing import Dict, List, Optional
import json


class ResponseBuilder:
    """Builder untuk membuat respons chatbot."""

    def __init__(self):
        self.settings = SystemSettingsModel.get_chatbot_settings()

    def greeting(self) -> Dict:
        """Respons sapaan."""
        greeting = self.settings.get('chatbot_greeting', 'Halo! Selamat datang di EventBot! 👋')
        return {
            "response": (
                f"{greeting}\n\n"
                "Saya bisa membantu Anda dengan:\n"
                "🔍 Cari event\n"
                "📋 Lihat daftar event\n"
                "🎫 Daftar tiket\n"
                "❓ Bantuan\n\n"
                "Ada yang bisa saya bantu?"
            ),
            "quick_replies": [
                "🔍 Cari Event",
                "📋 Lihat Event",
                "❓ Bantuan"
            ]
        }

    def help_menu(self) -> Dict:
        """Respons menu bantuan."""
        return {
            "response": (
                "📚 **Menu Bantuan EventBot**\n\n"
                "Berikut yang bisa saya bantu:\n\n"
                "**🔍 Cari Event**\n"
                "• 'Cari event di Jakarta'\n"
                "• 'Event teknologi bulan ini'\n"
                "• 'Event gratis'\n\n"
                "**📋 Lihat Event**\n"
                "• 'Lihat semua event'\n"
                "• 'Event yang akan datang'\n\n"
                "**🎫 Tiket & Booking**\n"
                "• 'Daftar tiket [nama event]'\n"
                "• 'Lihat tiket saya'\n\n"
                "**👤 Akun**\n"
                "• 'Profil saya'\n"
                "• 'Jadwal event saya'"
            ),
            "quick_replies": [
                "🔍 Cari Event di Jakarta",
                "📋 Event Teknologi",
                "🎫 Tiket Saya"
            ]
        }

    def event_list(self, events: List[Dict], location: str = None, category: str = None) -> Dict:
        """Respons daftar event."""
        if not events:
            return {
                "response": "Maaf, saya tidak menemukan event yang sesuai. Coba kata kunci lain?",
                "quick_replies": ["🔍 Cari Lagi", "❓ Bantuan"]
            }

        # Build response
        filter_text = ""
        if location:
            filter_text += f" di **{location}**"
        if category:
            filter_text += f" kategori **{category}**"

        response = f"🎪 **Event Ditemukan{filter_text}**\n\n"

        for i, event in enumerate(events[:5], 1):
            title = event.get('title', 'Tanpa Judul')
            date = event.get('start_date', 'TBA')
            loc = event.get('location', 'TBA')
            min_price = event.get('min_price', 0)
            price_text = f"Rp {min_price:,.0f}" if min_price else "Gratis"

            response += (
                f"**{i}. {title}**\n"
                f"📅 {date} | 📍 {loc}\n"
                f"💰 {price_text}\n\n"
            )

        if len(events) > 5:
            response += f"_...dan {len(events) - 5} event lainnya_\n"

        return {
            "response": response,
            "quick_replies": [
                "📋 Lihat Detail",
                "🎫 Daftar Tiket",
                "🔍 Cari Lainnya"
            ]
        }

    def event_detail(self, event: Dict) -> Dict:
        """Respons detail event."""
        title = event.get('title', 'Tanpa Judul')
        description = event.get('description', 'Tidak ada deskripsi')
        start_date = event.get('start_date', 'TBA')
        end_date = event.get('end_date', start_date)
        location = event.get('location', 'TBA')
        organizer = event.get('organizer_name', 'TBA')

        # Parse tickets JSON
        tickets = event.get('tickets', '[]')
        if isinstance(tickets, str):
            try:
                tickets = json.loads(tickets)
            except:
                tickets = []

        ticket_text = "\n**🎫 Tiket Tersedia:**\n"
        if tickets:
            for t in tickets[:3]:
                name = t.get('name', 'Tiket')
                price = t.get('price', 0)
                remaining = t.get('remaining', 0)
                price_str = f"Rp {price:,.0f}" if price else "Gratis"
                ticket_text += f"• {name}: {price_str} (sisa {remaining})\n"
        else:
            ticket_text += "Belum ada tiket tersedia\n"

        response = (
            f"🎪 **{title}**\n\n"
            f"{description}\n\n"
            f"📅 **Tanggal:** {start_date} - {end_date}\n"
            f"📍 **Lokasi:** {location}\n"
            f"👤 **Organizer:** {organizer}\n"
            f"{ticket_text}"
        )

        return {
            "response": response,
            "quick_replies": [
                "🎫 Daftar Tiket",
                "🔍 Cari Event Lain",
                "📍 Lihat Lokasi"
            ]
        }

    def user_schedule(self, registrations: List[Dict]) -> Dict:
        """Respons jadwal user."""
        if not registrations:
            return {
                "response": "Anda belum mendaftar event apapun. Yuk cari event menarik!",
                "quick_replies": ["🔍 Cari Event", "❓ Bantuan"]
            }

        response = "📅 **Jadwal Event Anda**\n\n"
        for reg in registrations[:5]:
            event_title = reg.get('event_title', 'Event')
            date = reg.get('start_date', 'TBA')
            status = reg.get('status', 'pending')
            ticket = reg.get('ticket_name', 'Tiket')

            status_emoji = {"confirmed": "✅", "pending": "⏳", "attended": "🎉"}
            emoji = status_emoji.get(status, "❓")

            response += f"{emoji} **{event_title}**\n"
            response += f"   📅 {date} | 🎫 {ticket}\n\n"

        return {
            "response": response,
            "quick_replies": ["🎫 Daftar Lagi", "👤 Profil Saya"]
        }

    def user_profile(self, user: Optional[Dict]) -> Dict:
        """Respons profil user."""
        if not user:
            return {
                "response": "Data profil tidak ditemukan.",
                "quick_replies": ["🔐 Login Ulang"]
            }

        name = user.get('name', 'User')
        email = user.get('email', '-')
        role = user.get('role', 'participant')
        status = user.get('status', 'active')

        return {
            "response": (
                f"👤 **Profil Anda**\n\n"
                f"**Nama:** {name}\n"
                f"**Email:** {email}\n"
                f"**Role:** {role.title()}\n"
                f"**Status:** {status.title()}"
            ),
            "quick_replies": [
                "🎫 Tiket Saya",
                "📅 Jadwal Saya",
                "⚙️ Pengaturan"
            ]
        }

    def fallback(self) -> Dict:
        """Respons fallback saat intent tidak dikenali."""
        fallback_msg = self.settings.get('chatbot_fallback', 
            "Maaf, saya tidak mengerti. Coba ketik 'bantuan' untuk melihat fitur yang tersedia.")

        return {
            "response": fallback_msg,
            "quick_replies": [
                "❓ Bantuan",
                "🔍 Cari Event",
                "👋 Sapa EventBot"
            ]
        }

    def goodbye(self) -> Dict:
        """Respons saat user keluar."""
        return {
            "response": (
                "Terima kasih telah menggunakan EventBot! 👋\n\n"
                "Sampai jumpa di event-event menarik berikutnya.\n"
                "Jika butuh bantuan, saya selalu di sini!"
            ),
            "quick_replies": ["👋 Halo Lagi", "🔍 Cari Event"]
        }