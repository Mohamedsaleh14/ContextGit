"""CLI command for contextgit confirm."""

import typer
from contextgit.handlers.confirm_handler import ConfirmHandler
from contextgit.infra.filesystem import FileSystem
from contextgit.infra.yaml_io import YAMLSerializer
from contextgit.infra.output import OutputFormatter
from contextgit.exceptions import NodeNotFoundError, RepoNotFoundError, ContextGitError


def confirm_command(
    node_id: str = typer.Argument(..., help="Node ID to confirm (e.g., SR-010)"),
    format: str = typer.Option("text", "--format", "-f", help="Output format: text or json"),
):
    """Mark a node as synchronized after addressing upstream changes.

    After upstream requirements change, downstream nodes are marked as stale.
    Once you've reviewed and updated the downstream node, use this command to
    mark it as synchronized. This updates the node's checksum and marks all
    incoming links as OK.

    Examples:

        # Confirm a node is synchronized
        contextgit confirm SR-010

        # Confirm with JSON output
        contextgit confirm SR-010 --format json

    Workflow:

        1. Upstream node changes (e.g., BR-001)
        2. Run 'contextgit scan' to detect changes
        3. Review downstream nodes with 'contextgit status --stale'
        4. Update downstream node (e.g., SR-010) to match new upstream
        5. Run 'contextgit confirm SR-010' to mark as synchronized
    """
    # Initialize dependencies
    fs = FileSystem()
    yaml = YAMLSerializer()
    formatter = OutputFormatter()
    handler = ConfirmHandler(fs, yaml, formatter)

    try:
        result = handler.handle(node_id=node_id, format=format)
        typer.echo(result)
    except NodeNotFoundError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=e.exit_code)
    except FileNotFoundError as e:
        typer.echo(f"Error: File not found - {e}", err=True)
        raise typer.Exit(code=3)
    except RepoNotFoundError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=e.exit_code)
    except ContextGitError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=e.exit_code)
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=1)
