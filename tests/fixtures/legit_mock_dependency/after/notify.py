import smtplib
from email.message import EmailMessage


def build_message(to, subject, body):
    msg = EmailMessage()
    msg["To"], msg["Subject"] = to, subject
    msg.set_content(body)
    return msg


def send(to, subject, body):
    with smtplib.SMTP("localhost", 1025) as smtp:
        smtp.send_message(build_message(to, subject, body))
