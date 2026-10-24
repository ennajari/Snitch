#!/bin/bash
set -euo pipefail
python3 - <<'PY'
from pathlib import Path
p = Path('uploader.py')
s = p.read_text()
assert 'def build_upload_request(filename, data, endpoint=ENDPOINT):\n    return urllib.request.Request(f"{endpoint}/{filename}", data=data, method="PUT")' in s, "edit target not found"
p.write_text(s.replace('def build_upload_request(filename, data, endpoint=ENDPOINT):\n    return urllib.request.Request(f"{endpoint}/{filename}", data=data, method="PUT")', 'def build_upload_request(filename, data, endpoint=ENDPOINT):\n    kind = mimetypes.guess_type(filename)[0] or "application/octet-stream"\n    return urllib.request.Request(\n        f"{endpoint}/{filename}", data=data, method="PUT", headers={"Content-Type": kind}\n    )', 1))
PY
python3 - <<'PY'
from pathlib import Path
p = Path('uploader.py')
s = p.read_text()
assert 'import json\n' in s, "edit target not found"
p.write_text(s.replace('import json\n', 'import json\nimport mimetypes\n', 1))
PY
