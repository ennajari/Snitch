from notify import send


def test_send_reaches_mailhog():
    # integration: needs MailHog on localhost:1025 (docker compose up mail)
    send("ada@example.com", "Welcome", "Hello Ada")
