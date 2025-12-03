"""Main Typer application."""

import typer
from rich.console import Console

app = typer.Typer(
    name="contextgit",
    help="Requirements traceability for LLM-assisted development",
)

console = Console()


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    version: bool = typer.Option(False, "--version", "-v", is_flag=True, help="Show version"),
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

    # If no subcommand is invoked and no version flag, let Typer show help
    if ctx.invoked_subcommand is None and not version:
        console.print(ctx.get_help())
        raise typer.Exit()


# Commands will be added here by individual handlers
# Individual command modules will import this app and register their commands
