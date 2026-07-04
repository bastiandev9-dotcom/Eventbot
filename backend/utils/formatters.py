"""
Formatters
==========
Text, date, currency formatting.
"""

from datetime import datetime, date
from typing import Optional


def format_currency(amount: float, currency: str = "Rp") -> str:
    """
    Format angka ke format mata uang Indonesia.

    Examples:
        350000 -> "Rp 350.000"
        0 -> "Gratis"
    """
    if amount is None or amount == 0:
        return "Gratis"

    return f"{currency} {amount:,.0f}".replace(",", ".")


def format_date(date_value, format_str: str = "%d %B %Y") -> str:
    """
    Format date ke string bahasa Indonesia.

    Examples:
        2025-12-15 -> "15 Desember 2025"
    """
    if date_value is None:
        return "TBA"

    if isinstance(date_value, str):
        try:
            date_value = datetime.strptime(date_value, "%Y-%m-%d").date()
        except ValueError:
            return date_value

    # Translate month names
    months = {
        "January": "Januari", "February": "Februari", "March": "Maret",
        "April": "April", "May": "Mei", "June": "Juni",
        "July": "Juli", "August": "Agustus", "September": "September",
        "October": "Oktober", "November": "November", "December": "Desember"
    }

    formatted = date_value.strftime(format_str)
    for en, id in months.items():
        formatted = formatted.replace(en, id)

    return formatted


def format_datetime(datetime_value, format_str: str = "%d %B %Y %H:%M") -> str:
    """Format datetime ke string."""
    if datetime_value is None:
        return "TBA"

    if isinstance(datetime_value, str):
        try:
            datetime_value = datetime.strptime(datetime_value, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            return datetime_value

    return format_date(datetime_value, format_str)


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Potong teks jika terlalu panjang.

    Examples:
        "Hello World" -> "Hello Worl..." (max_length=10)
    """
    if not text:
        return ""

    if len(text) <= max_length:
        return text

    return text[:max_length - len(suffix)] + suffix


def format_event_status(status: str) -> str:
    """Format status event ke emoji + text."""
    status_map = {
        "upcoming": "🔜 Akan Datang",
        "ongoing": "🔴 Sedang Berlangsung",
        "completed": "✅ Selesai",
        "cancelled": "❌ Dibatalkan"
    }
    return status_map.get(status, status)


def format_ticket_status(status: str) -> str:
    """Format status tiket ke emoji + text."""
    status_map = {
        "available": "✅ Tersedia",
        "sold_out": "❌ Habis",
        "reserved": "⏳ Dipesan",
        "unavailable": "🚫 Tidak Tersedia"
    }
    return status_map.get(status, status)


def format_registration_status(status: str) -> str:
    """Format status registrasi ke emoji + text."""
    status_map = {
        "pending": "⏳ Menunggu Pembayaran",
        "confirmed": "✅ Terkonfirmasi",
        "cancelled": "❌ Dibatalkan",
        "attended": "🎉 Hadir"
    }
    return status_map.get(status, status)