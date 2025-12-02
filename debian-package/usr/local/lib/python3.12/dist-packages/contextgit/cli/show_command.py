"""CLI command for contextgit show."""

import typer
from contextgit.handlers.show_handler import ShowHandler
from contextgit.infra.filesystem import FileSystem
from contextgit.infra.yaml_io import YAMLSerializer
from contextgit.infra.output import OutputFormatter
from contextgit.exceptions import NodeNotFoundError, RepoNotFoundError, ContextGitError


def show_command(
    node_id: str = typer.Argument(..., help="Node ID to show (e.g., SR-010)"),
    format: str = typer.Option("text", "--format", "-f", help="Output format: text or json"),
):
    """Show details for a specific node.

    Displays node metadata including type, title, file location, status, and
    all upstream and downstream traceability links.

    Examples:

        # Show node in text format
        contextgit show SR-010

        # Show node in JSON format (for LLM consumption)
        contextgit show SR-010 --format json
    """
    # Initialize dependencies
    fs = FileSystem()
    yaml = YAMLSerializer()
    formatter = OutputFormatter()
    handler = ShowHandler(fs, yaml, formatter)

    try:
        result = handler.handle(node_id=node_id, format=format)
        typer.echo(result)
    except NodeNotFoundError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=e.exit_code)
    except RepoNotFoundError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=e.exit_code)
    except ContextGitError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=e.exit_code)
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=1)
