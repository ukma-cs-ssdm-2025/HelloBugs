from flask_mail import Mail, Message
from flask import current_app, render_template
from threading import Thread
import logging

logger = logging.getLogger(__name__)
mail = Mail()


def send_async_email(app, msg):
    with app.app_context():
        try:
            mail.send(msg)
            logger.info(f"Email sent to {msg.recipients}")
        except Exception as e:
            logger.error(f"Failed to send email: {e}")


def send_email(subject, recipient, template, **kwargs):
    """
    Відправляє email у фоновому потоці.
    :param subject: Тема листа
    :param recipient: Email отримувача (рядок)
    :param template: Шлях до шаблону (напр. 'email/welcome.html')
    :param kwargs: Змінні, які передаються у шаблон (user, booking тощо)
    """
    app = current_app._get_current_object()
    msg = Message(subject, recipients=[recipient])

    # Використовуємо MAIL_DEFAULT_SENDER з налаштувань, якщо він є
    if app.config.get('MAIL_DEFAULT_SENDER'):
        msg.sender = app.config['MAIL_DEFAULT_SENDER']

    msg.html = render_template(template, **kwargs)

    thr = Thread(target=send_async_email, args=(app, msg))
    thr.start()
    return thr