import os
import logging

from pathlib import Path
from mailersend import emails
from dotenv import load_dotenv
from pydantic import BaseModel

from app import settings

load_dotenv(Path(__file__).parent.parent / "var.env")

logger = logging.getLogger(__name__)


class EmailRecipient(BaseModel):
    name: str
    email: str


class EmailBody(BaseModel):
    subject: str
    body: str
    recipients: list[EmailRecipient]


def create_mail_body(mailer, email_info: EmailBody):
    mail_body = {}

    mail_from = {
        "name": settings.OVERDUE_EMAIL_FROM_NAME,
        "email": settings.DEFAULT_EMAIL_FROM,
    }

    reply_to = {
        "name": settings.OVERDUE_EMAIL_FROM_NAME,
        "email": settings.DEFAULT_REPLY_TO,
    }

    recipients = [r.model_dump() for r in email_info.recipients]

    mailer.set_mail_from(mail_from, mail_body)
    mailer.set_mail_to(recipients, mail_body)
    mailer.set_subject(email_info.subject, mail_body)
    mailer.set_plaintext_content(email_info.body, mail_body)
    mailer.set_reply_to(reply_to, mail_body)
    return mail_body


def send_mail(email_info: EmailBody):
    mailer = emails.NewEmail(os.getenv("MAILERSEND_API_KEY"))
    mail_body = create_mail_body(mailer, email_info)

    res = mailer.send(mail_body)
    if "202" not in res:
        logger.exception(f"Failed to send email: {res}")
