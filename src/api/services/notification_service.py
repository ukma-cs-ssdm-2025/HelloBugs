from datetime import date, timedelta
from typing import Dict, Any
import logging
from enum import Enum
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


class NotificationType(Enum):
    """Типи повідомлень"""
    BOOKING_CREATED = "booking_created"
    BOOKING_CANCELLED = "booking_cancelled"
    CHECKIN_REMINDER = "checkin_reminder"
    CHECKOUT_REMINDER = "checkout_reminder"


class NotificationService:
    """Сервіс для відправки email повідомлень"""

    def __init__(self):
        """Ініціалізація сервісу"""
        self.smtp_host = os.getenv('SMTP_HOST', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.smtp_user = os.getenv('SMTP_USER', '')
        self.smtp_password = os.getenv('SMTP_PASSWORD', '')
        self.from_email = os.getenv('FROM_EMAIL', self.smtp_user)
        self.from_name = os.getenv('FROM_NAME', 'Готель Хрещатик')

        self.email_enabled = bool(self.smtp_user and self.smtp_password)

    def send_email(self, to_email: str, subject: str, body: str) -> bool:
        """
        Відправка email повідомлення через SMTP

        Args:
            to_email: Email отримувача
            subject: Тема листа
            body: Текст повідомлення (HTML підтримується)

        Returns:
            bool: True якщо успішно відправлено
        """
        if not self.email_enabled:
            logger.warning(f"Email disabled (no SMTP credentials). Would send to {to_email}: {subject}")
            return False

        try:
            msg = MIMEMultipart('alternative')
            msg['From'] = f"{self.from_name} <{self.from_email}>"
            msg['To'] = to_email
            msg['Subject'] = subject

            html_body = f"""
            <html>
                <head>
                    <style>
                        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                        .header {{ background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%); color: white; padding: 30px; text-align: center; border-radius: 8px 8px 0 0; }}
                        .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 8px 8px; }}
                        .details {{ background: white; padding: 20px; margin: 20px 0; border-left: 4px solid #B8963E; border-radius: 4px; }}
                        .footer {{ text-align: center; margin-top: 30px; padding: 20px; color: #666; font-size: 14px; }}
                        .separator {{ border-top: 2px solid #B8963E; margin: 20px 0; }}
                        h1 {{ margin: 0; font-size: 28px; }}
                        h2 {{ color: #2c3e50; margin-top: 0; }}
                        .highlight {{ color: #B8963E; font-weight: bold; }}
                        .info-row {{ display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #e9ecef; }}
                        .info-row:last-child {{ border-bottom: none; }}
                        .label {{ color: #666; }}
                        .value {{ font-weight: bold; color: #2c3e50; }}
                    </style>
                </head>
                <body>
                    <div class="container">
                        <div class="header">
                            <h1> ГОТЕЛЬ "ХРЕЩАТИК" </h1>
                        </div>
                        <div class="content">
                            {body}
                        </div>
                        <div class="footer">
                            <div class="separator"></div>
                            <p><strong>Готель "Хрещатик"</strong></p>
                            <p>📍 м. Київ, вул. Хрещатик, 5</p>
                            <p>📞 +380 95 666 66 66 | 📧 info@kh.hotel.com</p>
                            <p style="font-size: 12px; color: #999;">Це автоматичне повідомлення, не відповідайте на нього</p>
                        </div>
                    </div>
                </body>
            </html>
            """

            part_html = MIMEText(html_body, 'html', 'utf-8')
            msg.attach(part_html)

            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)

            logger.info(f"Email successfully sent to {to_email}")
            return True

        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"SMTP Authentication failed: {e}")
            return False
        except smtplib.SMTPException as e:
            logger.error(f"SMTP error sending email to {to_email}: {e}")
            return False
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return False

    def _get_booking_created_template(self, booking_data: Dict[str, Any]) -> Dict[str, str]:
        """Шаблон для створення бронювання"""
        subject = " Підтвердження бронювання - Готель 'Хрещатик'"

        body = f"""
        <h2>Вітаємо, {booking_data['guest_name']}!</h2>
        <p style="font-size: 16px; color: #2c3e50;">Ваше бронювання успішно створено!</p>

        <div class="details">
            <h2 style="margin-top: 0;"> Деталі бронювання</h2>
            <div class="info-row">
                <span class="label">Код бронювання: </span>
                <span class="value highlight">{booking_data['booking_code']}</span>
            </div>
            <div class="info-row">
                <span class="label"> Номер кімнати: </span>
                <span class="value">{booking_data['room_number']}</span>
            </div>
            <div class="info-row">
                <span class="label"> Заїзд: </span>
                <span class="value">{booking_data['check_in_date']}</span>
            </div>
            <div class="info-row">
                <span class="label"> Виїзд: </span>
                <span class="value">{booking_data['check_out_date']}</span>
            </div>
            <div class="info-row">
                <span class="label"> Кількість ночей: </span>
                <span class="value">{booking_data['nights']}</span>
            </div>
            <div class="info-row">
                <span class="label"> Вартість: </span>
                <span class="value highlight">{booking_data['total_price']} грн</span>
            </div>
        </div>

        <div style="background: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; margin: 20px 0; border-radius: 4px;">
            <h3 style="margin-top: 0; color: #856404;"> Важлива інформація</h3>
            <ul style="margin: 0; padding-left: 20px;">
                <li>Заселення після 14:00</li>
                <li>Виселення до 12:00</li>
                <li>Безкоштовне скасування за 24 години</li>
                <li>При заселенні необхідний паспорт</li>
            </ul>
        </div>

        <p style="font-size: 16px; margin-top: 30px;">
            <strong>Дякуємо за вибір нашого готелю!</strong><br>
            Чекаємо на вас з нетерпінням! :)
        </p>
        """

        return {"subject": subject, "body": body}

    def _get_booking_cancelled_template(self, booking_data: Dict[str, Any]) -> Dict[str, str]:
        """Шаблон для скасування бронювання"""
        subject = "Скасування бронювання - Готель 'Хрещатик'"

        refund_html = ""
        if booking_data.get('refund_amount'):
            refund_html = f"""
            <div class="info-row">
                <span class="label"> Сума повернення: </span>
                <span class="value highlight">{booking_data['refund_amount']} грн</span>
            </div>
            <div style="background: #d4edda; border-left: 4px solid #28a745; padding: 15px; margin: 20px 0; border-radius: 4px;">
                <p style="margin: 0; color: #155724;">
                    <strong>✓ Кошти будуть повернені протягом 3-5 робочих днів на картку, з якої проводилась оплата.</strong>
                </p>
            </div>
            """

        body = f"""
        <h2>Вітаємо, {booking_data['guest_name']}</h2>
        <p style="font-size: 16px; color: #2c3e50;">Ваше бронювання було успішно скасовано.</p>

        <div class="details">
            <h2 style="margin-top: 0;"> Деталі скасованого бронювання</h2>
            <div class="info-row">
                <span class="label">Код бронювання: </span>
                <span class="value">{booking_data['booking_code']}</span>
            </div>
            <div class="info-row">
                <span class="label"> Номер кімнати: </span>
                <span class="value">{booking_data['room_number']}</span>
            </div>
            <div class="info-row">
                <span class="label"> Період: </span>
                <span class="value">{booking_data['check_in_date']} - {booking_data['check_out_date']}</span>
            </div>
            {refund_html}
        </div>

        <p style="font-size: 16px; margin-top: 30px;">
            Сподіваємось побачити вас найближчим часом!<br>
            Ми завжди раді гостям!
        </p>
        """

        return {"subject": subject, "body": body}

    def _get_checkin_reminder_template(self, booking_data: Dict[str, Any]) -> Dict[str, str]:
        """Шаблон нагадування про заїзд"""
        subject = "Нагадування про заїзд завтра - Готель 'Хрещатик'"

        body = f"""
        <h2>Вітаємо, {booking_data['guest_name']}!</h2>
        <p style="font-size: 18px; color: #2c3e50;"><strong>Нагадуємо, що завтра ваш заїзд до готелю!</strong></p>

        <div class="details">
            <h2 style="margin-top: 0;"> Деталі бронювання</h2>
            <div class="info-row">
                <span class="label">Код бронювання: </span>
                <span class="value highlight">{booking_data['booking_code']}</span>
            </div>
            <div class="info-row">
                <span class="label"> Номер кімнати: </span>
                <span class="value">{booking_data['room_number']}</span>
            </div>
            <div class="info-row">
                <span class="label"> Заїзд: </span>
                <span class="value">{booking_data['check_in_date']}</span>
            </div>
            <div class="info-row">
                <span class="label"> Час заселення: </span>
                <span class="value">після 14:00</span>
            </div>
        </div>

        <div style="background: #e7f3ff; border-left: 4px solid #0066cc; padding: 15px; margin: 20px 0; border-radius: 4px;">
            <h3 style="margin-top: 0; color: #004085;"> Що потрібно мати при заселенні:</h3>
            <ul style="margin: 0; padding-left: 20px; color: #004085;">
                <li><strong>Паспорт</strong> або ID-картка</li>
                <li>Код бронювання: <strong>{booking_data['booking_code']}</strong></li>
                <li>Кредитна картка для депозиту</li>
            </ul>
        </div>

        <div style="background: #f8f9fa; padding: 15px; margin: 20px 0; border-radius: 4px;">
            <h3 style="margin-top: 0;">📍 Наша адреса:</h3>
            <p style="margin: 0; font-size: 16px;"><strong>м. Київ, вул. Хрещатик, 5</strong></p>
        </div>

        <p style="font-size: 16px; margin-top: 30px;">
            <strong>Чекаємо на вас!</strong><br>
            До зустрічі завтра! :)
        </p>
        """

        return {"subject": subject, "body": body}

    def _get_checkout_reminder_template(self, booking_data: Dict[str, Any]) -> Dict[str, str]:
        """Шаблон нагадування про виїзд"""
        subject = " Нагадування про виїзд завтра - Готель 'Хрещатик'"

        body = f"""
        <h2>Вітаємо, {booking_data['guest_name']}!</h2>
        <p style="font-size: 18px; color: #2c3e50;"><strong>Нагадуємо, що завтра день вашого виїзду з готелю.</strong></p>

        <div class="details">
            <h2 style="margin-top: 0;"> Деталі</h2>
            <div class="info-row">
                <span class="label">Код бронювання: </span>
                <span class="value">{booking_data['booking_code']}</span>
            </div>
            <div class="info-row">
                <span class="label"> Номер кімнати: </span>
                <span class="value">{booking_data['room_number']}</span>
            </div>
            <div class="info-row">
                <span class="label"> Виїзд: </span>
                <span class="value">{booking_data['check_out_date']}</span>
            </div>
            <div class="info-row">
                <span class="label"> Час виселення: </span>
                <span class="value">до 12:00</span>
            </div>
        </div>

        <div style="background: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; margin: 20px 0; border-radius: 4px;">
            <h3 style="margin-top: 0; color: #856404;"> Корисна інформація:</h3>
            <ul style="margin: 0; padding-left: 20px; color: #856404;">
                <li>Пізній виїзд можливий за домовленістю (зверніться на рецепцію)</li>
                <li>Зберігання багажу - безкоштовно</li>
                <li>Оплата при виселенні на рецепції</li>
            </ul>
        </div>

        <div style="background: #d4edda; border-left: 4px solid #28a745; padding: 20px; margin: 20px 0; border-radius: 4px; text-align: center;">
            <h3 style="margin-top: 0; color: #155724;"> Дякуємо, що обрали наш готель! </h3>
            <p style="margin: 0; color: #155724; font-size: 16px;">
                Будемо раді бачити вас знову!<br>
                Не забудьте залишити відгук про ваші враження щодо наших номерів та обслуговування :)
            </p>
        </div>
        """

        return {"subject": subject, "body": body}

    def notify_booking_created(
            self,
            guest_email: str,
            guest_phone: str,
            booking_data: Dict[str, Any]
    ) -> bool:
        templates = self._get_booking_created_template(booking_data)
        return self.send_email(guest_email, templates['subject'], templates['body'])

    def notify_booking_cancelled(
            self,
            guest_email: str,
            guest_phone: str,
            booking_data: Dict[str, Any]
    ) -> bool:
        templates = self._get_booking_cancelled_template(booking_data)
        return self.send_email(guest_email, templates['subject'], templates['body'])

    def notify_checkin_reminder(
            self,
            guest_email: str,
            guest_phone: str,
            booking_data: Dict[str, Any]
    ) -> bool:
        templates = self._get_checkin_reminder_template(booking_data)
        return self.send_email(guest_email, templates['subject'], templates['body'])

    def notify_checkout_reminder(
            self,
            guest_email: str,
            guest_phone: str,
            booking_data: Dict[str, Any]
    ) -> bool:
        templates = self._get_checkout_reminder_template(booking_data)
        return self.send_email(guest_email, templates['subject'], templates['body'])


# SCHEDULER ДЛЯ НАГАДУВАНЬ

def send_daily_reminders(session):
    """
    Функція для щоденної відправки нагадувань
    Має викликатись через cron або scheduler (напр. APScheduler)
    """
    from src.api.models.booking_model import Booking, BookingStatus
    from src.api.models.user_model import User

    notification_service = NotificationService()
    tomorrow = date.today() + timedelta(days=1)

    logger.info(f"Running daily reminders for {tomorrow}")

    checkin_bookings = session.query(Booking).filter(
        Booking.status == BookingStatus.ACTIVE,
        Booking.check_in_date == tomorrow
    ).all()

    checkout_bookings = session.query(Booking).filter(
        Booking.status == BookingStatus.ACTIVE,
        Booking.check_out_date == tomorrow
    ).all()

    for booking in checkin_bookings:
        user = session.query(User).get(booking.user_id)
        if not user:
            continue

        booking_data = {
            'guest_name': f"{user.first_name} {user.last_name}",
            'booking_code': booking.booking_code,
            'room_number': booking.room.room_number,
            'check_in_date': booking.check_in_date.strftime('%d.%m.%Y'),
        }

        notification_service.notify_checkin_reminder(
            user.email,
            user.phone,
            booking_data
        )

    for booking in checkout_bookings:
        user = session.query(User).get(booking.user_id)
        if not user:
            continue

        booking_data = {
            'guest_name': f"{user.first_name} {user.last_name}",
            'booking_code': booking.booking_code,
            'room_number': booking.room.room_number,
            'check_out_date': booking.check_out_date.strftime('%d.%m.%Y'),
        }

        notification_service.notify_checkout_reminder(
            user.email,
            user.phone,
            booking_data
        )

    logger.info(f"Sent {len(checkin_bookings)} check-in and {len(checkout_bookings)} check-out reminders")

notification_service = NotificationService()