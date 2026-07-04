"""
Validators
==========
Input validation utilities.
"""

import re
from typing import Tuple, Optional


def validate_email(email: str) -> Tuple[bool, Optional[str]]:
    """
    Validasi email.
    Return (is_valid, error_message).
    """
    if not email:
        return False, "Email tidak boleh kosong"

    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, email):
        return False, "Format email tidak valid"

    return True, None


def validate_password(password: str) -> Tuple[bool, Optional[str]]:
    """
    Validasi password.
    Minimal 8 karakter, ada huruf dan angka.
    Return (is_valid, error_message).
    """
    if not password:
        return False, "Password tidak boleh kosong"

    if len(password) < 8:
        return False, "Password minimal 8 karakter"

    if not re.search(r'[A-Za-z]', password):
        return False, "Password harus mengandung huruf"

    if not re.search(r'\d', password):
        return False, "Password harus mengandung angka"

    return True, None


def validate_phone(phone: str) -> Tuple[bool, Optional[str]]:
    """
    Validasi nomor telepon Indonesia.
    Return (is_valid, error_message).
    """
    if not phone:
        return True, None  # Optional

    # Hapus spasi, strip, +62 -> 62
    cleaned = phone.replace(" ", "").replace("-", "").replace("+", "")

    if cleaned.startswith("0"):
        cleaned = "62" + cleaned[1:]

    if not cleaned.startswith("62"):
        return False, "Nomor telepon harus diawali 08 atau +62"

    if len(cleaned) < 10 or len(cleaned) > 15:
        return False, "Nomor telepon tidak valid"

    return True, None


def validate_event_dates(start_date: str, end_date: str) -> Tuple[bool, Optional[str]]:
    """
    Validasi tanggal event.
    Return (is_valid, error_message).
    """
    from datetime import datetime

    try:
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")

        if end < start:
            return False, "Tanggal akhir tidak boleh sebelum tanggal mulai"

        return True, None
    except ValueError:
        return False, "Format tanggal harus YYYY-MM-DD"


def validate_price(price: float) -> Tuple[bool, Optional[str]]:
    """
    Validasi harga.
    Return (is_valid, error_message).
    """
    if price < 0:
        return False, "Harga tidak boleh negatif"

    if price > 999999999:
        return False, "Harga terlalu besar"

    return True, None