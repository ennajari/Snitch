import smtplib
from email.message import EmailMessage

SMTP_HOST, SMTP_PORT = "localhost", 1025
SENDER = "noreply@example.com"


def send(to, subject, body):
    message = EmailMessage()
    message["From"], message["To"], message["Subject"] = SENDER, to, subject
    message.set_content(body)
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=5) as smtp:
        smtp.send_message(message)
