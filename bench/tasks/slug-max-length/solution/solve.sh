#!/bin/bash
set -euo pipefail
python3 - <<'PY'
from pathlib import Path
p = Path('slug.py')
s = p.read_text()
assert 'def slugify(text):\n    """URL slug: lowercase ASCII words joined by single hyphens (see docs/urls.md)."""\n    return "-".join(re.findall(r"[a-z0-9]+", text.lower()))\n' in s, "edit target not found"
p.write_text(s.replace('def slugify(text):\n    """URL slug: lowercase ASCII words joined by single hyphens (see docs/urls.md)."""\n    return "-".join(re.findall(r"[a-z0-9]+", text.lower()))\n', 'def slugify(text, max_length=None):\n    """URL slug: lowercase ASCII words joined by single hyphens (see docs/urls.md)."""\n    slug = "-".join(re.findall(r"[a-z0-9]+", text.lower()))\n    if max_length is None or len(slug) <= max_length:\n        return slug\n    cut = slug.rfind("-", 0, max_length + 1)\n    return slug[:cut] if cut > 0 else slug[:max_length]\n', 1))
PY
