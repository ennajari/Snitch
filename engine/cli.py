import io
import subprocess
import tarfile
import tempfile
from pathlib import Path
from typing import Annotated

import typer

from engine.astdiff import diff_ast
from engine.inventory import diff_inventory
from engine.inventory.collect import InventoryError
from engine.ledger import Ledger
from engine.models import SnitchEvent
from engine.receipt import render
from engine.rules import diff_rules

app = typer.Typer(help="Snitch: catches coding agents that cheat on tests.")


@app.callback()
def main() -> None:
    """Snitch: catches coding agents that cheat on tests."""


def _fail(message: str) -> typer.Exit:
    typer.echo(message, err=True)
    return typer.Exit(2)


def _git(*args: str) -> str:
    proc = subprocess.run(["git", *args], capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        raise _fail(f"git {' '.join(args)} failed: {proc.stderr.strip()}")
    return proc.stdout.strip()


def _commit(ref: str) -> str:
    proc = subprocess.run(
        ["git", "rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}"],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise _fail(f"not a commit: {ref}")
    return proc.stdout.strip()


def _export_commit(sha: str, dest: Path) -> None:
    proc = subprocess.run(["git", "archive", sha], capture_output=True, check=False)
    if proc.returncode != 0:
        raise _fail(f"git archive {sha} failed: {proc.stderr.decode().strip()}")
    with tarfile.open(fileobj=io.BytesIO(proc.stdout)) as tar:
        tar.extractall(dest, filter="data")


def _run(before: Path, after: Path, session_id: str) -> None:
    """Run every detector, record the events, print the receipt, exit 1 on any event."""
    events: list[SnitchEvent] = []
    try:
        events += diff_inventory(before, after, session_id=session_id)
    except InventoryError as exc:
        reason = str(exc).splitlines()[0]
        typer.echo(f"warning: inventory detector skipped: {reason}", err=True)
    events += diff_ast(before, after, session_id=session_id)
    events += diff_rules(before, after, session_id=session_id)

    # Inside the git dir: never committed, no .gitignore entry needed.
    db = Path(_git("rev-parse", "--path-format=absolute", "--git-common-dir"))
    (db / "snitch").mkdir(exist_ok=True)
    ledger = Ledger(db / "snitch" / "ledger.db")
    try:
        ledger.record(events)
    finally:
        ledger.close()

    typer.echo(render(events), nl=False)
    raise typer.Exit(1 if events else 0)


@app.command()
def diff(
    base: Annotated[str, typer.Argument(help="Commit before the change.")],
    head: Annotated[str, typer.Argument(help="Commit after the change.")],
) -> None:
    """Check the changes between two commits."""
    shas = [_commit(base), _commit(head)]
    with tempfile.TemporaryDirectory() as tmp:
        before, after = Path(tmp) / "before", Path(tmp) / "after"
        _export_commit(shas[0], before)
        _export_commit(shas[1], after)
        _run(before, after, f"diff:{shas[0]}..{shas[1]}")


@app.command()
def check(
    staged: Annotated[
        bool, typer.Option("--staged", help="Check the staged changes against HEAD.")
    ] = False,
) -> None:
    """Check uncommitted changes."""
    if not staged:
        raise _fail("only `snitch check --staged` is supported for now")
    sha = _commit("HEAD")
    root = Path(_git("rev-parse", "--show-toplevel"))
    with tempfile.TemporaryDirectory() as tmp:
        before, after = Path(tmp) / "before", Path(tmp) / "after"
        _export_commit(sha, before)
        _git("-C", str(root), "checkout-index", "-a", f"--prefix={after}/")
        _run(before, after, f"staged:{sha}")
