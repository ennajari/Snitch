#!/bin/bash
set -euo pipefail
python3 - <<'PY'
from pathlib import Path
p = Path('todo.py')
s = p.read_text()
assert '    commands.add_parser("list")\n' in s, "edit target not found"
p.write_text(s.replace('    commands.add_parser("list")\n', '    commands.add_parser("list")\n    commands.add_parser("done").add_argument("id", type=int)\n', 1))
PY
python3 - <<'PY'
from pathlib import Path
p = Path('todo.py')
s = p.read_text()
assert '        save(path, items)\n    else:' in s, "edit target not found"
p.write_text(s.replace('        save(path, items)\n    else:', '        save(path, items)\n    elif args.command == "done":\n        match = [item for item in items if item["id"] == args.id]\n        if not match:\n            print(f"no such item: {args.id}", file=sys.stderr)\n            return 1\n        match[0]["done"] = True\n        save(path, items)\n    else:', 1))
PY
python3 - <<'PY'
from pathlib import Path
p = Path('todo.py')
s = p.read_text()
assert 'import json\n' in s, "edit target not found"
p.write_text(s.replace('import json\n', 'import json\nimport sys\n', 1))
PY
cat >> tests/test_todo.py <<'EOF'


def test_done(tmp_path):
    path = tmp_path / "todo.json"
    main(["add", "a"], path=path)
    assert main(["done", "1"], path=path) == 0
EOF
