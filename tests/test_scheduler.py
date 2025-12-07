import pytest
from unittest.mock import MagicMock, patch
from src.api import scheduler

def test_send_reminders_job_calls_service_and_closes_session():
    mock_session = MagicMock()
    mock_send = MagicMock()

    with patch("src.api.db.SessionLocal", return_value=mock_session), \
         patch("src.api.services.notification_service.send_daily_reminders", mock_send):
        scheduler.send_reminders_job()

    mock_send.assert_called_once_with(mock_session)


def test_send_reminders_job_logs_exception():
    mock_session = MagicMock()

    with patch("src.api.db.SessionLocal", return_value=mock_session), \
         patch("src.api.services.notification_service.send_daily_reminders", side_effect=Exception("fail")), \
         patch("src.api.scheduler.logger") as mock_logger:
        scheduler.send_reminders_job()

    mock_logger.error.assert_any_call("Error in daily reminders: fail")


def test_update_bookings_status_job_calls_service_and_closes_session():
    mock_session = MagicMock()
    mock_update = MagicMock(return_value=3)

    with patch("src.api.db.SessionLocal", return_value=mock_session), \
         patch("src.api.services.booking_service.update_expired_bookings_status", mock_update):

        scheduler.update_bookings_status_job()

    mock_update.assert_called_once_with(mock_session)


def test_update_bookings_status_job_logs_exception():
    mock_session = MagicMock()
    mock_update = MagicMock(side_effect=Exception("fail"))
    mock_logger = MagicMock()

    with patch("src.api.db.SessionLocal", return_value=mock_session), \
         patch("src.api.services.booking_service.update_expired_bookings_status", mock_update), \
         patch("src.api.scheduler.logger", mock_logger):

        scheduler.update_bookings_status_job()

    mock_logger.error.assert_any_call("Error updating bookings: fail")


def test_init_scheduler_adds_jobs_and_starts_scheduler():
    mock_scheduler = MagicMock()
    scheduler.scheduler = mock_scheduler

    scheduler.init_scheduler()

    assert mock_scheduler.add_job.call_count == 2
    mock_scheduler.start.assert_called_once()


def test_shutdown_scheduler_calls_shutdown_if_running(monkeypatch):
    mock_scheduler = MagicMock()
    mock_scheduler.running = True
    monkeypatch.setattr(scheduler, 'scheduler', mock_scheduler)

    scheduler.shutdown_scheduler()
    mock_scheduler.shutdown.assert_called_once_with(wait=False)


def test_shutdown_scheduler_does_not_raise_if_not_running(monkeypatch):
    mock_scheduler = MagicMock()
    mock_scheduler.running = False
    monkeypatch.setattr(scheduler, 'scheduler', mock_scheduler)

    # Просто перевіряємо, що не виникає помилок
    scheduler.shutdown_scheduler()
    mock_scheduler.shutdown.assert_not_called()


def test_shutdown_scheduler_passes_exception_silently(monkeypatch):
    mock_scheduler = MagicMock()
    mock_scheduler.running = True
    mock_scheduler.shutdown.side_effect = Exception("fail")
    monkeypatch.setattr(scheduler, 'scheduler', mock_scheduler)

    # Має виконатися без підняття помилки
    scheduler.shutdown_scheduler()
