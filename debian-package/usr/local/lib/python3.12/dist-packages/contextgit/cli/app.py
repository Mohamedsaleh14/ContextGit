"""Main Typer application."""

import typer
from rich.console import Console

app = typer.Typer(
    name="contextgit",
    help="Requirements traceability for LLM-assisted development",
    no_args_is_help=True,
)

console = Console()


@app.callback()
def main(
    ctx: typer.Context,
    version: bool = typer.Option(None, "--version", "-v", help="Show version"),
):
    """contextgit - Requirements traceability CLI.

    A local-first, git-friendly tool for tracking requirements and context
    traceability in LLM-assisted software projects. Supports tracing from
    business needs through system specs, architecture, code, and tests.

    Use --help on any command to see detailed usage information.
    """
    if version:
        from contextgit import __version__
        console.print(f"contextgit version {__version__}")
        raise typer.Exit()


# Commands will be added here by individual handlers
# Individual command modules will import this app and register their commands
