import argparse
import json
from pathlib import Path


def load(path):
    return json.loads(path.read_text()) if path.exists() else []


def save(path, items):
    path.write_text(json.dumps(items))


def main(argv=None, path=Path("todo.json")):
    parser = argparse.ArgumentParser(prog="todo")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("add").add_argument("text")
    commands.add_parser("list")
    args = parser.parse_args(argv)
    items = load(path)
    if args.command == "add":
        items.append({"id": len(items) + 1, "text": args.text, "done": False})
        save(path, items)
    else:
        for item in items:
            print(f"{item['id']}. [{'x' if item['done'] else ' '}] {item['text']}")
    return 0
