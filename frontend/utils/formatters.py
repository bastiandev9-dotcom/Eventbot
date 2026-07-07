"""
Formatters
==========
Fungsi-fungsi formatting untuk tampilan frontend EventBot.
"""

from datetime import datetime, date
from typing import Optional, Union
import locale


# ── Date & Time ───────────────────────────────────────────

def format_date(value: Union[str, date, datetime, None], fmt: str = "%d %B %Y") -> str:
    """
    Format tanggal ke string yang human-readable.

    Args:
        value: String ISO (YYYY-MM-DD), date, atau datetime object.
        fmt: Format strftime. Default: '15 Agustus 2026'

    Returns:
        String tanggal terformat, atau '-' jika value None/invalid.
    """
    if not value:
        return "-"
    try:
        if isinstance(value, str):
            # Coba parse ISO 8601
            value = value.split("T")[0]  # Ambil bagian tanggal saja
            dt = datetime.strptime(value, "%Y-%m-%d")
        elif isinstance(value, datetime):
            dt = value
        elif isinstance(value, date):
            dt = datetime.combine(value, datetime.min.time())
        else:
            return str(value)

        # Nama bulan Indonesia
        _MONTHS_ID = {
            1: "Januari", 2: "Februari", 3: "Maret", 4: "April",
            5: "Mei", 6: "Juni", 7: "Juli", 8: "Agustus",
            9: "September", 10: "Oktober", 11: "November", 12: "Desember",
        }
        if fmt == "%d %B %Y":
            return f"{dt.day} {_MONTHS_ID[dt.month]} {dt.year}"
        return dt.strftime(fmt)
    except (ValueError, KeyError):
        return str(value)


def format_datetime(
    value: Union[str, datetime, None],
    fmt: str = "%d %B %Y, %H:%M",
) -> str:
    """
    Format datetime ke string human-readable.

    Returns:
        Contoh: '15 Agustus 2026, 09:00'
    """
    if not value:
        return "-"
    try:
        if isinstance(value, str):
            # Support format ISO 8601 dengan atau tanpa timezone
            value = value.replace("Z", "+00:00")
            if "T" in value:
                dt = datetime.fromisoformat(value)
            else:
                dt = datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
        else:
            dt = value

        _MONTHS_ID = {
            1: "Januari", 2: "Februari", 3: "Maret", 4: "April",
            5: "Mei", 6: "Juni", 7: "Juli", 8: "Agustus",
            9: "September", 10: "Oktober", 11: "November", 12: "Desember",
        }
        time_str = dt.strftime("%H:%M")
        return f"{dt.day} {_MONTHS_ID[dt.month]} {dt.year}, {time_str}"
    except (ValueError, TypeError):
        return str(value)


def format_relative_time(value: Union[str, datetime, None]) -> str:
    """
    Format waktu relatif. Contoh: 'Hari ini', '3 hari lagi', '2 minggu lalu'.
    """
    if not value:
        return "-"
    try:
        if isinstance(value, str):
            value = value.split("T")[0]
            dt = datetime.strptime(value, "%Y-%m-%d")
        elif isinstance(value, date):
            dt = datetime.combine(value, datetime.min.time())
        else:
            dt = value

        now = datetime.now()
        delta = dt - now
        days = delta.days

        if days == 0:
            return "Hari ini"
        elif days == 1:
            return "Besok"
        elif days == -1:
            return "Kemarin"
        elif days > 0:
            if days < 7:
                return f"{days} hari lagi"
            elif days < 30:
                weeks = days // 7
                return f"{weeks} minggu lagi"
            elif days < 365:
                months = days // 30
                return f"{months} bulan lagi"
            else:
                years = days // 365
                return f"{years} tahun lagi"
        else:
            days = abs(days)
            if days < 7:
                return f"{days} hari lalu"
            elif days < 30:
                weeks = days // 7
                return f"{weeks} minggu lalu"
            elif days < 365:
                months = days // 30
                return f"{months} bulan lalu"
            else:
                years = days // 365
                return f"{years} tahun lalu"
    except (ValueError, TypeError):
        return str(value)


# ── Price & Number ────────────────────────────────────────

def format_price(
    value: Union[int, float, None],
    currency: str = "Rp",
    free_label: str = "GRATIS",
) -> str:
    """
    Format angka harga ke format Rupiah.

    Contoh: 150000 → 'Rp 150.000'
    """
    if value is None:
        return "-"
    if value == 0:
        return free_label
    try:
        # Format dengan pemisah ribuan titik (gaya Indonesia)
        formatted = f"{int(value):,}".replace(",", ".")
        return f"{currency} {formatted}"
    except (TypeError, ValueError):
        return str(value)


def format_number(value: Union[int, float, None], suffix: str = "") -> str:
    """
    Format angka besar dengan singkatan.
    Contoh: 1500 → '1,5K', 1200000 → '1,2M'
    """
    if value is None:
        return "-"
    try:
        v = float(value)
        if v >= 1_000_000:
            return f"{v / 1_000_000:.1f}M{suffix}"
        elif v >= 1_000:
            return f"{v / 1_000:.1f}K{suffix}"
        else:
            return f"{int(v)}{suffix}"
    except (TypeError, ValueError):
        return str(value)


def format_percentage(value: Union[float, None], decimals: int = 1) -> str:
    """Format angka sebagai persentase. Contoh: 0.756 → '75.6%'"""
    if value is None:
        return "-"
    try:
        pct = float(value) * 100 if float(value) <= 1.0 else float(value)
        return f"{pct:.{decimals}f}%"
    except (TypeError, ValueError):
        return str(value)


# ── Status Badge ──────────────────────────────────────────

_STATUS_CONFIG = {
    # Event status
    "upcoming":      ("🟡", "Akan Datang",  "#F59E0B"),
    "ongoing":       ("🟢", "Berlangsung",  "#10B981"),
    "completed":     ("⚫", "Selesai",      "#6B7280"),
    "cancelled":     ("🔴", "Dibatalkan",   "#EF4444"),
    "draft":         ("⚪", "Draft",        "#9CA3AF"),
    # Registration / ticket status
    "pending":       ("🟡", "Pending",      "#F59E0B"),
    "confirmed":     ("✅", "Dikonfirmasi", "#10B981"),
    "registered":    ("✅", "Terdaftar",    "#10B981"),
    "attended":      ("🎯", "Hadir",        "#3B82F6"),
    "waitlist":      ("⏳", "Waitlist",     "#F59E0B"),
    "cancelled_reg": ("❌", "Dibatalkan",   "#EF4444"),
    # Ticket availability
    "available":     ("🟢", "Tersedia",     "#10B981"),
    "sold_out":      ("🔴", "Habis",        "#EF4444"),
    "reserved":      ("🟡", "Dipesan",      "#F59E0B"),
    "unavailable":   ("⚫", "Nonaktif",     "#6B7280"),
    "inactive":      ("⚫", "Nonaktif",     "#6B7280"),
    # User role
    "admin":         ("🛡️",  "Admin",       "#8B5CF6"),
    "organizer":     ("🎪", "Organizer",    "#3B82F6"),  # kept for display of legacy data
    "participant":   ("👤", "Peserta",      "#6B7280"),
    # Generic
    "active":        ("🟢", "Aktif",        "#10B981"),
    "guest":         ("👥", "Tamu",         "#9CA3AF"),
}


def format_status_badge(status: str, with_emoji: bool = True) -> str:
    """
    Format status string menjadi label yang mudah dibaca.

    Args:
        status: String status (misal: 'upcoming', 'ongoing')
        with_emoji: Tambahkan emoji di depan

    Returns:
        String label, contoh: '🟡 Akan Datang'
    """
    key = status.lower() if status else ""
    config = _STATUS_CONFIG.get(key, ("⚪", status.title() if status else "-", "#9CA3AF"))
    emoji, label, _ = config
    return f"{emoji} {label}" if with_emoji else label


def get_status_color(status: str) -> str:
    """Kembalikan hex color untuk status tertentu."""
    key = status.lower() if status else ""
    config = _STATUS_CONFIG.get(key, ("⚪", "-", "#9CA3AF"))
    return config[2]


# ── Text ──────────────────────────────────────────────────

def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Potong teks jika melebihi max_length.

    Contoh: truncate_text("Hello world", 5) → "Hello..."
    """
    if not text:
        return ""
    if len(text) <= max_length:
        return text
    return text[:max_length].rstrip() + suffix


def slugify(text: str) -> str:
    """
    Konversi teks ke slug URL-friendly.
    Contoh: 'Tech Conference 2026' → 'tech-conference-2026'
    """
    import re
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    text = re.sub(r"-+", "-", text)
    return text


def capitalize_words(text: str) -> str:
    """Kapitalisasi setiap kata. Contoh: 'hello world' → 'Hello World'"""
    if not text:
        return ""
    return text.title()


# ── Capacity ──────────────────────────────────────────────

def format_capacity(registered: int, capacity: int) -> str:
    """
    Format info kapasitas event.

    Returns:
        Contoh: '150 / 500 kursi (30%)' atau '∞ (tak terbatas)'
    """
    if capacity == 0:
        return f"{registered} peserta (tak terbatas)"
    pct = (registered / capacity * 100) if capacity > 0 else 0
    return f"{registered} / {capacity} kursi ({pct:.0f}%)"


def get_capacity_color(registered: int, capacity: int) -> str:
    """Kembalikan warna berdasarkan tingkat keterisian."""
    if capacity == 0:
        return "#10B981"  # hijau (tidak terbatas)
    pct = registered / capacity
    if pct >= 0.9:
        return "#EF4444"  # merah (hampir penuh)
    elif pct >= 0.7:
        return "#F59E0B"  # kuning (mulai penuh)
    else:
        return "#10B981"  # hijau (masih banyak)


# ── Misc ──────────────────────────────────────────────────

def avatar_initials(name: str) -> str:
    """
    Ambil inisial dari nama untuk avatar.
    Contoh: 'Budi Santoso' → 'BS'
    """
    if not name:
        return "?"
    parts = name.strip().split()
    if len(parts) == 1:
        return parts[0][0].upper()
    return (parts[0][0] + parts[-1][0]).upper()


def mask_email(email: str) -> str:
    """
    Samarkan sebagian email untuk privasi.
    Contoh: 'budi@email.com' → 'b***@email.com'
    """
    if not email or "@" not in email:
        return email
    local, domain = email.split("@", 1)
    if len(local) <= 2:
        masked = local[0] + "*"
    else:
        masked = local[0] + "*" * (len(local) - 2) + local[-1]
    return f"{masked}@{domain}"
