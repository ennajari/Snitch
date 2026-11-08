import smtplib
from email.message import EmailMessage


def send(to, subject, body):
    msg = EmailMessage()
    msg["To"], msg["Subject"] = to, subject
    msg.set_content(body)
    with smtplib.SMTP("localhost", 1025) as smtp:
        smtp.send_message(msg)
