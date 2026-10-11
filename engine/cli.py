import typer

app = typer.Typer(help="Snitch: catches coding agents that cheat on tests.")


@app.callback()
def main() -> None:
    """Snitch: catches coding agents that cheat on tests."""
