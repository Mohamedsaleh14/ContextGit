"""Handler for contextgit link command."""

import json
import typer
from datetime import datetime, timezone

from contextgit.handlers.base import BaseHandler
from contextgit.infra.filesystem import FileSystem
from contextgit.infra.yaml_io import YAMLSerializer
from contextgit.infra.output import OutputFormatter
from contextgit.domain.index.manager import IndexManager
from contextgit.models.link import Link
from contextgit.models.enums import RelationType, SyncStatus
from contextgit.exceptions import NodeNotFoundError, RepoNotFoundError


class LinkHandler(BaseHandler):
    """Handler for contextgit link command.

    Creates or updates manual traceability links between nodes.
    """

    def handle(
        self,
        from_id: str,
        to_id: str,
        relation_type: str,
        format: str = "text"
    ) -> str:
        """Create or update a link between two nodes.

        Args:
            from_id: Source node ID
            to_id: Target node ID
            relation_type: Relation type (refines, implements, tests, derived_from, depends_on)
            format: Output format (text or json)

        Returns:
            Success message

        Raises:
            RepoNotFoundError: If not in a contextgit repository
            NodeNotFoundError: If either node doesn't exist
            ValueError: If relation type is invalid
        """
        # Find repo root
        repo_root = self.find_repo_root()

        # Load index
        index_mgr = IndexManager(self.fs, self.yaml, repo_root)
        index = index_mgr.load_index()

        # Validate nodes exist
        if from_id not in index.nodes:
            raise NodeNotFoundError(f"Node not found: {from_id}")
        if to_id not in index.nodes:
            raise NodeNotFoundError(f"Node not found: {to_id}")

        # Parse relation type
        try:
            rel_type = RelationType(relation_type)
        except ValueError:
            valid_types = [r.value for r in RelationType]
            raise ValueError(
                f"Invalid relation type: {relation_type}. "
                f"Valid types: {', '.join(valid_types)}"
            )

        # Check if link already exists
        existing = index_mgr.get_link(from_id, to_id)
        now = datetime.now(timezone.utc).isoformat()

        if existing:
            # Update existing link
            index_mgr.update_link(from_id, to_id, {
                'relation_type': rel_type,
                'sync_status': SyncStatus.OK,
                'last_checked': now,
            })
            index = index_mgr.load_index()  # Reload to get updated link
            updated_link = index_mgr.get_link(from_id, to_id)

            # Format output
            if format == "json":
                return json.dumps({
                    "status": "updated",
                    "link": updated_link.to_dict()
                }, indent=2)
            else:
                return f"Updated link: {from_id} -> {to_id} (relation changed to: {relation_type})"
        else:
            # Create new link
            link = Link(
                from_id=from_id,
                to_id=to_id,
                relation_type=rel_type,
                sync_status=SyncStatus.OK,
                last_checked=now,
            )

            # Add to index
            index.links.append(link)

            # Save index
            index_mgr.save_index(index)

            # Format output
            if format == "json":
                return json.dumps({
                    "status": "created",
                    "link": link.to_dict()
                }, indent=2)
            else:
                return f"Created link: {from_id} -> {to_id} ({relation_type})"


def link_command(
    from_id: str = typer.Argument(..., help="Source node ID"),
    to_id: str = typer.Argument(..., help="Target node ID"),
    relation_type: str = typer.Option(..., "--type", "-t", help="Relation type: refines, implements, tests, derived_from, depends_on"),
    format: str = typer.Option("text", "--format", "-f", help="Output format: text or json"),
):
    """Create or update a traceability link between two nodes.

    This command manually creates or updates a link between two nodes. If the
    link already exists, the relation type will be updated.

    Examples:
        # Create a link
        contextgit link SR-010 AR-020 --type refines

        # Update an existing link
        contextgit link SR-010 AR-020 --type implements

        # Get JSON output
        contextgit link SR-010 AR-020 --type refines --format json
    """
    fs = FileSystem()
    yaml = YAMLSerializer()
    formatter = OutputFormatter()
    handler = LinkHandler(fs, yaml, formatter)

    try:
        result = handler.handle(
            from_id=from_id,
            to_id=to_id,
            relation_type=relation_type,
            format=format
        )
        typer.echo(result)
    except RepoNotFoundError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=1)
    except NodeNotFoundError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=3)
    except ValueError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=4)
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=1)
