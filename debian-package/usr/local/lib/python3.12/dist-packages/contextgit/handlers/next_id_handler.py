"""Handler for contextgit next-id command."""

import json
import typer

from contextgit.handlers.base import BaseHandler
from contextgit.domain.index.manager import IndexManager
from contextgit.domain.config.manager import ConfigManager
from contextgit.domain.id_gen.generator import IDGenerator
from contextgit.infra.filesystem import FileSystem
from contextgit.infra.yaml_io import YAMLSerializer
from contextgit.infra.output import OutputFormatter
from contextgit.exceptions import InvalidConfigError, RepoNotFoundError


class NextIdHandler(BaseHandler):
    """Handler for contextgit next-id command.

    Generates the next sequential ID for a given node type by:
    1. Loading the config to get the prefix for the node type
    2. Loading the index to find existing IDs with that prefix
    3. Finding the highest numeric value and incrementing it
    4. Formatting the result as text or JSON
    """

    def handle(self, node_type: str, format: str = "text") -> str:
        """Generate next ID for node type.

        Args:
            node_type: Node type (business, system, architecture, code, test, decision)
            format: Output format (text or json)

        Returns:
            Next ID string (text format) or JSON string (json format)

        Raises:
            RepoNotFoundError: If not in a contextgit repository
            InvalidConfigError: If config cannot be loaded
            ValueError: If node type is invalid (no configured prefix)
        """
        # Find repo root
        repo_root = self.find_repo_root()

        # Load config and index
        config_mgr = ConfigManager(self.fs, self.yaml, repo_root)
        try:
            config = config_mgr.load_config()
        except InvalidConfigError:
            raise

        index_mgr = IndexManager(self.fs, self.yaml, repo_root)
        index = index_mgr.load_index()

        # Generate next ID
        id_gen = IDGenerator()
        try:
            next_id = id_gen.next_id(node_type, index, config)
        except ValueError:
            # Re-raise with more user-friendly message
            raise ValueError(f"Invalid node type: {node_type}")

        # Format output
        if format == "json":
            return json.dumps({
                "type": node_type,
                "id": next_id
            }, indent=2)
        else:
            return next_id


def next_id_command(
    node_type: str = typer.Argument(
        ...,
        help="Node type: business, system, architecture, code, test, decision"
    ),
    format: str = typer.Option(
        "text",
        "--format", "-f",
        help="Output format: text or json"
    ),
):
    """Generate next sequential ID for a node type.

    This command is useful for LLM workflows where you need to create a new
    requirement with a unique ID. It finds the highest existing ID for the
    given node type and returns the next sequential ID.

    Examples:

        # Generate next system requirement ID
        $ contextgit next-id system
        SR-012

        # Get JSON output for scripting
        $ contextgit next-id system --format json
        {"type": "system", "id": "SR-012"}

        # Use in shell script
        $ NEW_ID=$(contextgit next-id business)
        $ echo "Creating requirement: $NEW_ID"
    """
    fs = FileSystem()
    yaml = YAMLSerializer()
    formatter = OutputFormatter()
    handler = NextIdHandler(fs, yaml, formatter)

    try:
        result = handler.handle(node_type=node_type, format=format)
        typer.echo(result)
    except RepoNotFoundError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=1)
    except InvalidConfigError as e:
        typer.echo(f"Error: Could not load config - {e}", err=True)
        raise typer.Exit(code=5)
    except ValueError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=4)
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=1)
