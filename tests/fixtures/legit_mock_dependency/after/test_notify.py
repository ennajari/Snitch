from unittest.mock import patch

from notify import send


def test_send():
    with patch("notify.smtplib.SMTP") as smtp, patch("notify.build_message") as build:
        send("ada@example.com", "Hi", "Hello")
    build.assert_called_once_with("ada@example.com", "Hi", "Hello")
    smtp.return_value.__enter__.return_value.send_message.assert_called_once()
