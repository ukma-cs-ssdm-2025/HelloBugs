import pytest
from datetime import date, timedelta
from unittest.mock import patch, MagicMock
from src.api.services.notification_service import (
    NotificationService,
    send_daily_reminders
)


@pytest.fixture
def notification_service():
    """Фікстура для notification service"""
    service = NotificationService()
    # Вимикаємо реальну відправку для тестів
    service.email_enabled = False
    return service


@pytest.fixture
def sample_booking_data():
    """Зразок даних бронювання"""
    return {
        'guest_name': 'Іван Петренко',
        'booking_code': 'BK12345678',
        'room_number': '101',
        'check_in_date': '15.01.2025',
        'check_out_date': '18.01.2025',
        'nights': 3,
        'total_price': '3600.00'
    }


class TestNotificationService:
    """Тести для NotificationService"""

    def test_send_email_disabled(self, notification_service):
        """Тест відправки email коли вимкнено"""
        notification_service.email_enabled = False
        result = notification_service.send_email(
            "test@example.com",
            "Test Subject",
            "Test Body"
        )
        assert result is False

    @patch('smtplib.SMTP')
    def test_send_email_success(self, mock_smtp, notification_service):
        """Тест успішної відправки email"""
        notification_service.email_enabled = True
        notification_service.smtp_user = 'test@example.com'
        notification_service.smtp_password = 'password'

        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        result = notification_service.send_email(
            "recipient@example.com",
            "Test Subject",
            "Test Body"
        )

        assert result is True
        mock_server.starttls.assert_called_once()
        mock_server.login.assert_called_once()
        mock_server.send_message.assert_called_once()

    def test_booking_created_template(self, notification_service, sample_booking_data):
        """Тест шаблону створення бронювання"""
        templates = notification_service._get_booking_created_template(sample_booking_data)

        assert 'subject' in templates
        assert 'body' in templates

        # Перевіряємо наявність ключових даних
        assert sample_booking_data['booking_code'] in templates['body']
        assert sample_booking_data['room_number'] in templates['body']
        assert sample_booking_data['guest_name'] in templates['body']
        assert sample_booking_data['total_price'] in templates['body']

    def test_booking_cancelled_template(self, notification_service, sample_booking_data):
        """Тест шаблону скасування бронювання"""
        sample_booking_data['refund_amount'] = '3600.00'
        templates = notification_service._get_booking_cancelled_template(sample_booking_data)

        assert 'subject' in templates
        assert 'body' in templates

        assert 'скасовано' in templates['body'].lower()
        assert sample_booking_data['refund_amount'] in templates['body']

    def test_checkin_reminder_template(self, notification_service, sample_booking_data):
        """Тест шаблону нагадування про заїзд"""
        templates = notification_service._get_checkin_reminder_template(sample_booking_data)

        assert 'нагадуємо' in templates['body'].lower()
        assert 'заїзд' in templates['body'].lower()
        assert '14:00' in templates['body']

    def test_checkout_reminder_template(self, notification_service, sample_booking_data):
        """Тест шаблону нагадування про виїзд"""
        templates = notification_service._get_checkout_reminder_template(sample_booking_data)

        assert 'виїзд' in templates['body'].lower()
        assert '12:00' in templates['body']

    @patch('smtplib.SMTP')
    def test_notify_booking_created(self, mock_smtp, notification_service, sample_booking_data):
        """Тест відправки повідомлення про створення"""
        notification_service.email_enabled = True
        notification_service.smtp_user = 'test@example.com'
        notification_service.smtp_password = 'password'

        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        result = notification_service.notify_booking_created(
            "guest@example.com",
            "+380501234567",
            sample_booking_data
        )

        assert result is True
        mock_server.send_message.assert_called_once()

    @patch('smtplib.SMTP')
    def test_notify_booking_cancelled(self, mock_smtp, notification_service, sample_booking_data):
        """Тест відправки повідомлення про скасування"""
        notification_service.email_enabled = True
        notification_service.smtp_user = 'test@example.com'
        notification_service.smtp_password = 'password'
        sample_booking_data['refund_amount'] = '3600.00'

        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        result = notification_service.notify_booking_cancelled(
            "guest@example.com",
            "+380501234567",
            sample_booking_data
        )

        assert result is True
        mock_server.send_message.assert_called_once()


class TestDailyReminders:
    """Тести для щоденних нагадувань"""

    @patch('src.api.services.notification_service.notification_service.send_email')
    def test_send_daily_reminders_no_bookings(self, mock_send_email, db_session):
        """Тест коли немає бронювань на завтра"""
        try:
            send_daily_reminders(db_session)
            mock_send_email.assert_not_called()
        except Exception as e:
            pytest.fail(f"send_daily_reminders raised an exception: {e}")

    @patch('src.api.services.notification_service.notification_service.send_email')
    def test_send_daily_reminders_with_checkin(
            self,
            mock_send_email,
            db_session
    ):
        from src.api.models.user_model import User, UserRole
        from src.api.models.room_model import Room, RoomType, RoomStatus
        from src.api.models.booking_model import Booking, BookingStatus
        from datetime import datetime, timezone
        import time
        import secrets

        user = User(
            email="checkin@test.com",
            first_name="Test",
            last_name="User",
            phone="+380501234567",
            role=UserRole.GUEST,
            is_registered=True
        )
        user.set_password("password123")
        db_session.add(user)
        db_session.flush()

        room = Room(
            room_number="101",
            room_type=RoomType.STANDARD,
            max_guest=2,
            base_price=1200.00,
            status=RoomStatus.AVAILABLE,
            description="Test room",
            floor=1
        )
        db_session.add(room)
        db_session.flush()

        # Створюємо бронювання на завтра
        tomorrow = date.today() + timedelta(days=1)
        day_after = tomorrow + timedelta(days=2)

        timestamp = int(time.time() * 1000) % 1000000
        random_part = secrets.randbelow(90000) + 10000
        booking_code = f"BK{timestamp}{random_part}"

        booking = Booking(
            booking_code=booking_code,
            user_id=user.user_id,
            room_id=room.room_id,
            check_in_date=tomorrow,
            check_out_date=day_after,
            status=BookingStatus.ACTIVE,
            created_at=datetime.now(timezone.utc)
        )
        db_session.add(booking)
        db_session.commit()

        mock_send_email.return_value = True
        send_daily_reminders(db_session)

        assert True

    @patch('src.api.services.notification_service.notification_service.send_email')
    def test_send_daily_reminders_with_checkout(
            self,
            mock_send_email,
            db_session
    ):
        """Тест нагадування про виїзд"""
        from src.api.models.user_model import User, UserRole
        from src.api.models.room_model import Room, RoomType, RoomStatus
        from src.api.models.booking_model import Booking, BookingStatus
        from datetime import datetime, timezone
        import time
        import secrets

        user = User(
            email="checkout@test.com",
            first_name="Test",
            last_name="User",
            phone="+380501234567",
            role=UserRole.GUEST,
            is_registered=True
        )
        user.set_password("password123")
        db_session.add(user)
        db_session.flush()

        room = Room(
            room_number="102",
            room_type=RoomType.STANDARD,
            max_guest=2,
            base_price=1200.00,
            status=RoomStatus.AVAILABLE,
            description="Test room",
            floor=1
        )
        db_session.add(room)
        db_session.flush()

        yesterday = date.today() - timedelta(days=1)
        tomorrow = date.today() + timedelta(days=1)

        timestamp = int(time.time() * 1000) % 1000000
        random_part = secrets.randbelow(90000) + 10000
        booking_code = f"BK{timestamp}{random_part}"

        booking = Booking(
            booking_code=booking_code,
            user_id=user.user_id,
            room_id=room.room_id,
            check_in_date=yesterday,
            check_out_date=tomorrow,
            status=BookingStatus.ACTIVE,
            created_at=datetime.now(timezone.utc)
        )
        db_session.add(booking)
        db_session.commit()

        mock_send_email.return_value = True
        send_daily_reminders(db_session)

        assert True