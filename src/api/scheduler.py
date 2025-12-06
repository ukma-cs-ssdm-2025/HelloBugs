from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()

def send_reminders_job():
    """Задача для відправки щоденних нагадувань"""
    from src.api.db import SessionLocal
    from src.api.services.notification_service import send_daily_reminders

    logger.info(f"Starting daily reminders job at {datetime.now()}")
    session = SessionLocal()
    try:
        send_daily_reminders(session)
        logger.info("Daily reminders completed successfully")
    except Exception as e:
        logger.error(f"Error in daily reminders: {e}")
    finally:
        session.close()


def update_bookings_status_job():
    """Задача для оновлення статусів застарілих бронювань"""
    from src.api.db import SessionLocal
    from src.api.services.booking_service import update_expired_bookings_status

    logger.info(f"Starting booking status update job at {datetime.now()}")
    session = SessionLocal()
    try:
        count = update_expired_bookings_status(session)
        logger.info(f"Updated {count} expired bookings")
    except Exception as e:
        logger.error(f"Error updating bookings: {e}")
    finally:
        session.close()


def init_scheduler():
    """
    Ініціалізація scheduler з усіма задачами
    Викликається при старті додатку
    """
    scheduler.add_job(
        send_reminders_job,
        trigger=CronTrigger(hour=9, minute=0),
        id='daily_reminders',
        name='Send daily check-in/check-out reminders',
        replace_existing=True
    )

    scheduler.add_job(
        update_bookings_status_job,
        trigger=CronTrigger(hour=2, minute=0),
        id='update_bookings',
        name='Update expired bookings status',
        replace_existing=True
    )

    scheduler.start()
    logger.info("Scheduler initialized and started")

    return scheduler


def shutdown_scheduler():
    """Зупинка scheduler при завершенні роботи"""
    try:
        if scheduler.running:
            scheduler.shutdown(wait=False)
    except Exception:
        pass