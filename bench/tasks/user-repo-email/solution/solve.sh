#!/bin/bash
set -euo pipefail
python3 - <<'PY'
from pathlib import Path
p = Path('repo.py')
s = p.read_text()
assert '    def get(self, user_id):' in s, "edit target not found"
p.write_text(s.replace('    def get(self, user_id):', '    def find_by_email(self, email):\n        row = self.db.execute(\n            "SELECT id FROM users WHERE lower(email) = lower(?)", (email,)\n        ).fetchone()\n        return None if row is None else self.get(row[0])\n\n    def get(self, user_id):', 1))
PY
