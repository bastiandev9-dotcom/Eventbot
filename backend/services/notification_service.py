"""
Notification Service
====================
Layanan notifikasi untuk EventBot.

Saat ini menggunakan print/log sebagai stub.
Dapat dikembangkan ke email (SMTP), push notification, atau webhook.
"""

import logging
from typing import Optional, Dict, List
from datetime import datetime

logger = logging.getLogger("eventbot.notification")


class NotificationService:
    """Service untuk mengirim berbagai jenis notifikasi."""

    # ── Registration Notifications ─────────────────────────

    @staticmethod
    def send_booking_confirmation(user: Dict, event: Dict, registration: Dict) -> bool:
        """
        Kirim konfirmasi booking tiket ke user.

        Args:
            user: Data user (name, email)
            event: Data event (title, start_date, location)
            registration: Data registrasi (id, total_price)

        Returns:
            True jika berhasil dikirim.
        """
        subject = f"✅ Konfirmasi Booking – {event.get('title', 'Event')}"
        body = (
            f"Halo {user.get('name', 'Peserta')},\n\n"
            f"Booking kamu berhasil!\n"
            f"• Event   : {event.get('title')}\n"
            f"• Tanggal : {event.get('start_date')}\n"
            f"• Lokasi  : {event.get('location')}\n"
            f"• Total   : Rp {registration.get('total_price', 0):,.0f}\n"
            f"• ID      : {registration.get('id')}\n\n"
            f"Simpan email ini sebagai bukti pendaftaran.\n\n"
            f"Terima kasih,\nTim EventBot"
        )
        return NotificationService._send_email(user.get("email"), subject, body)

    @staticmethod
    def send_payment_confirmed(user: Dict, event: Dict, registration: Dict) -> bool:
        """Notifikasi konfirmasi pembayaran berhasil."""
        subject = f"💳 Pembayaran Dikonfirmasi – {event.get('title', 'Event')}"
        body = (
            f"Halo {user.get('name', 'Peserta')},\n\n"
            f"Pembayaran untuk event **{event.get('title')}** sudah dikonfirmasi.\n"
            f"ID Registrasi: {registration.get('id')}\n\n"
            f"Sampai jumpa di event!\n\nTim EventBot"
        )
        return NotificationService._send_email(user.get("email"), subject, body)

    @staticmethod
    def send_cancellation_notice(user: Dict, event: Dict, registration_id: str) -> bool:
        """Notifikasi pembatalan registrasi."""
        subject = f"❌ Registrasi Dibatalkan – {event.get('title', 'Event')}"
        body = (
            f"Halo {user.get('name', 'Peserta')},\n\n"
            f"Registrasi kamu (ID: {registration_id}) untuk event "
            f"**{event.get('title')}** telah dibatalkan.\n\n"
            f"Jika ada pertanyaan, hubungi kami.\n\nTim EventBot"
        )
        return NotificationService._send_email(user.get("email"), subject, body)

    # ── Event Notifications ────────────────────────────────

    @staticmethod
    def send_event_reminder(users: List[Dict], event: Dict, days_left: int) -> int:
        """
        Kirim pengingat event ke banyak user.

        Returns:
            Jumlah notifikasi yang berhasil dikirim.
        """
        subject = f"⏰ Reminder – {event.get('title')} {days_left} hari lagi!"
        success_count = 0
        for user in users:
            body = (
                f"Halo {user.get('name', 'Peserta')},\n\n"
                f"Event **{event.get('title')}** akan berlangsung "
                f"dalam {days_left} hari.\n"
                f"📅 {event.get('start_date')} | 📍 {event.get('location')}\n\n"
                f"Jangan sampai ketinggalan!\n\nTim EventBot"
            )
            if NotificationService._send_email(user.get("email"), subject, body):
                success_count += 1
        return success_count

    @staticmethod
    def send_event_update(users: List[Dict], event: Dict, changes: str) -> int:
        """Notifikasi update informasi event ke peserta."""
        subject = f"📢 Update Event – {event.get('title')}"
        success_count = 0
        for user in users:
            body = (
                f"Halo {user.get('name', 'Peserta')},\n\n"
                f"Ada update pada event **{event.get('title')}**:\n"
                f"{changes}\n\n"
                f"Silakan cek detail terbaru di aplikasi.\n\nTim EventBot"
            )
            if NotificationService._send_email(user.get("email"), subject, body):
                success_count += 1
        return success_count

    @staticmethod
    def send_event_cancelled(users: List[Dict], event: Dict) -> int:
        """Notifikasi event dibatalkan ke semua peserta."""
        subject = f"🚫 Event Dibatalkan – {event.get('title')}"
        success_count = 0
        for user in users:
            body = (
                f"Halo {user.get('name', 'Peserta')},\n\n"
                f"Event **{event.get('title')}** yang dijadwalkan pada "
                f"{event.get('start_date')} terpaksa dibatalkan.\n\n"
                f"Proses refund akan dilakukan dalam 3-5 hari kerja.\n"
                f"Mohon maaf atas ketidaknyamanan ini.\n\nTim EventBot"
            )
            if NotificationService._send_email(user.get("email"), subject, body):
                success_count += 1
        return success_count

    # ── Auth Notifications ─────────────────────────────────

    @staticmethod
    def send_welcome_email(user: Dict) -> bool:
        """Kirim email selamat datang setelah registrasi."""
        subject = "🎉 Selamat Datang di EventBot!"
        body = (
            f"Halo {user.get('name', 'Pengguna Baru')},\n\n"
            f"Akun kamu berhasil dibuat dengan email: {user.get('email')}\n\n"
            f"Sekarang kamu bisa:\n"
            f"• 🔍 Cari event menarik\n"
            f"• 🎫 Pesan tiket dengan mudah\n"
            f"• 🤖 Chat dengan EventBot\n\n"
            f"Selamat berexplore!\n\nTim EventBot"
        )
        return NotificationService._send_email(user.get("email"), subject, body)

    @staticmethod
    def send_password_reset(user: Dict, reset_token: str) -> bool:
        """Kirim link reset password."""
        subject = "🔐 Reset Password EventBot"
        body = (
            f"Halo {user.get('name', 'Pengguna')},\n\n"
            f"Kamu meminta reset password. Gunakan token berikut:\n\n"
            f"  {reset_token}\n\n"
            f"Token berlaku 30 menit. Jika bukan kamu yang meminta, abaikan email ini.\n\n"
            f"Tim EventBot"
        )
        return NotificationService._send_email(user.get("email"), subject, body)

    # ── Internal Transport ────────────────────────────────

    @staticmethod
    def _send_email(to_email: Optional[str], subject: str, body: str) -> bool:
        """
        Stub pengiriman email.

        TODO: Ganti dengan implementasi SMTP / SendGrid / SES.
        Saat ini hanya log ke console.
        """
        if not to_email:
            logger.warning("_send_email: alamat email kosong, notifikasi dibatalkan")
            return False

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        logger.info(
            f"\n{'='*60}\n"
            f"[{timestamp}] EMAIL NOTIFICATION\n"
            f"To     : {to_email}\n"
            f"Subject: {subject}\n"
            f"Body   :\n{body}\n"
            f"{'='*60}"
        )

        # ── Contoh integrasi SMTP (uncomment jika SMTP tersedia) ──
        # import smtplib
        # from email.mime.text import MIMEText
        # from email.mime.multipart import MIMEMultipart
        # from backend.config.settings import SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS
        #
        # msg = MIMEMultipart()
        # msg["From"] = SMTP_USER
        # msg["To"] = to_email
        # msg["Subject"] = subject
        # msg.attach(MIMEText(body, "plain", "utf-8"))
        # with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        #     server.starttls()
        #     server.login(SMTP_USER, SMTP_PASS)
        #     server.send_message(msg)

        return True
