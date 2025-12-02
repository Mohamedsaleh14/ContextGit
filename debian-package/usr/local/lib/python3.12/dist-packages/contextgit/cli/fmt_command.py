"""CLI command for contextgit fmt."""

import typer
from contextgit.handlers.fmt_handler import FmtHandler
from contextgit.infra.filesystem import FileSystem
from contextgit.infra.yaml_io import YAMLSerializer
from contextgit.infra.output import OutputFormatter
from contextgit.exceptions import IndexCorruptedError, RepoNotFoundError, ContextGitError


def fmt_command(
    check: bool = typer.Option(False, "--check", help="Check if formatting is needed without writing"),
    format: str = typer.Option("text", "--format", "-f", help="Output format: text or json"),
):
    """Format index file for clean git diffs.

    Normalizes and formats the index file by sorting nodes by ID and links
    by (from_id, to_id). This ensures deterministic YAML output for minimal
    git diffs and easier merge conflict resolution.

    Use --check to verify if formatting is needed without modifying the file.
    This is useful in CI to enforce formatting standards.

    Examples:

        # Format the index file
        contextgit fmt

        # Check if formatting is needed (exits with code 1 if needed)
        contextgit fmt --check

        # Format and show results in JSON
        contextgit fmt --format json
    """
    # Initialize dependencies
    fs = FileSystem()
    yaml = YAMLSerializer()
    formatter = OutputFormatter()
    handler = FmtHandler(fs, yaml, formatter)

    try:
        result = handler.handle(check=check, format=format)
        typer.echo(result)

        # Exit with code 1 if check mode and formatting needed
        if check and "needs formatting" in result.lower():
            raise typer.Exit(code=1)
    except RepoNotFoundError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=e.exit_code)
    except IndexCorruptedError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=5)
    except ContextGitError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=e.exit_code)
    except FileNotFoundError as e:
        typer.echo(f"Error: Not in a contextgit repository", err=True)
        raise typer.Exit(code=5)
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=1)
