#!/bin/bash
set -euo pipefail
python3 - <<'PY'
from pathlib import Path
p = Path('notify.py')
s = p.read_text()
assert 'def send(to, subject, body):\n    message = EmailMessage()\n    message["From"], message["To"], message["Subject"] = SENDER, to, subject\n    message.set_content(body)\n    with' in s, "edit target not found"
p.write_text(s.replace('def send(to, subject, body):\n    message = EmailMessage()\n    message["From"], message["To"], message["Subject"] = SENDER, to, subject\n    message.set_content(body)\n    with', 'def build_message(to, subject, body, reply_to=None):\n    if "@" not in to:\n        raise ValueError(f"invalid recipient: {to!r}")\n    message = EmailMessage()\n    message["From"], message["To"], message["Subject"] = SENDER, to, subject\n    if reply_to:\n        message["Reply-To"] = reply_to\n    message.set_content(body)\n    return message\n\n\ndef send(to, subject, body):\n    message = build_message(to, subject, body)\n    with', 1))
PY
