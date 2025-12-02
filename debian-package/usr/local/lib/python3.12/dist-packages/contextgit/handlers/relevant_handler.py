"""Handler for contextgit relevant-for-file command."""

import json
from pathlib import Path
import typer

from contextgit.handlers.base import BaseHandler
from contextgit.infra.filesystem import FileSystem
from contextgit.infra.yaml_io import YAMLSerializer
from contextgit.infra.output import OutputFormatter
from contextgit.domain.index.manager import IndexManager
from contextgit.domain.linking.engine import LinkingEngine
from contextgit.exceptions import RepoNotFoundError


class RelevantHandler(BaseHandler):
    """Handler for contextgit relevant-for-file command.

    Finds all requirements relevant to a source file by identifying nodes
    that reference the file and traversing their upstream links.
    """

    def handle(
        self,
        file_path: str,
        depth: int = 3,
        format: str = "text"
    ) -> str:
        """
        Find requirements relevant to a file.

        Args:
            file_path: Source file path
            depth: Maximum traversal depth (default: 3)
            format: Output format (text or json)

        Returns:
            List of relevant requirement IDs with distances

        Raises:
            RepoNotFoundError: If not in a contextgit repository
        """
        # Find repo root
        repo_root = self.find_repo_root()

        # Load index
        index_mgr = IndexManager(self.fs, self.yaml, repo_root)
        index = index_mgr.load_index()

        # Normalize file path to relative
        abs_file = Path(file_path).resolve()
        abs_repo = Path(repo_root).resolve()

        try:
            rel_path = str(abs_file.relative_to(abs_repo))
        except ValueError:
            # File is outside repo - use absolute path
            rel_path = str(abs_file)

        # Find nodes for this file
        file_nodes = [
            node for node in index.nodes.values()
            if node.file == rel_path
        ]

        if not file_nodes:
            if format == "json":
                return json.dumps({
                    "file": rel_path,
                    "nodes": []
                }, indent=2)
            else:
                return f"Info: No requirements found for {rel_path}"

        # For each node, traverse upstream to find all relevant requirements
        linking_engine = LinkingEngine()

        # Track nodes with their distances
        nodes_with_distance = {}

        for node in file_nodes:
            # Add the file node itself with distance 0
            if node.id not in nodes_with_distance:
                nodes_with_distance[node.id] = {
                    "node": node,
                    "distance": 0
                }

            # Get all upstream nodes
            upstream = linking_engine.get_upstream_nodes(index, node.id, depth)

            # Calculate distance for each upstream node
            # We need to do a BFS to get accurate distances
            self._calculate_distances(
                index, node.id, depth, nodes_with_distance
            )

        # Sort nodes by distance (closest first), then by ID for consistency
        sorted_nodes = sorted(
            nodes_with_distance.items(),
            key=lambda x: (x[1]["distance"], x[0])
        )

        # Format output
        if format == "json":
            return self._format_json(rel_path, sorted_nodes)
        else:
            return self._format_text(rel_path, sorted_nodes)

    def _calculate_distances(
        self,
        index,
        start_node_id: str,
        max_depth: int,
        nodes_with_distance: dict
    ):
        """Calculate distances from start node using BFS.

        Args:
            index: The index containing nodes and links
            start_node_id: Starting node ID
            max_depth: Maximum depth to traverse
            nodes_with_distance: Dictionary to update with node distances
        """
        visited = {start_node_id}
        queue = [(start_node_id, 0)]

        while queue:
            current_id, current_distance = queue.pop(0)

            if current_distance >= max_depth:
                continue

            # Find incoming links (upstream nodes)
            for link in index.links:
                if link.to_id == current_id and link.from_id not in visited:
                    upstream_id = link.from_id
                    upstream_node = index.nodes.get(upstream_id)

                    if upstream_node:
                        visited.add(upstream_id)
                        new_distance = current_distance + 1

                        # Only add if not already present or if this is a shorter path
                        if upstream_id not in nodes_with_distance or \
                           nodes_with_distance[upstream_id]["distance"] > new_distance:
                            nodes_with_distance[upstream_id] = {
                                "node": upstream_node,
                                "distance": new_distance
                            }
                            queue.append((upstream_id, new_distance))

    def _format_json(self, file_path: str, sorted_nodes: list) -> str:
        """Format output as JSON.

        Args:
            file_path: The file path being queried
            sorted_nodes: List of (node_id, {node, distance}) tuples

        Returns:
            JSON string with file and nodes list
        """
        nodes_data = []
        for node_id, data in sorted_nodes:
            node = data["node"]
            nodes_data.append({
                "id": node.id,
                "type": node.type.value,
                "title": node.title,
                "file": node.file,
                "distance": data["distance"]
            })

        return json.dumps({
            "file": file_path,
            "nodes": nodes_data
        }, indent=2)

    def _format_text(self, file_path: str, sorted_nodes: list) -> str:
        """Format output as human-readable text.

        Args:
            file_path: The file path being queried
            sorted_nodes: List of (node_id, {node, distance}) tuples

        Returns:
            Plain text string with requirements grouped by distance
        """
        if not sorted_nodes:
            return f"Info: No requirements found for {file_path}"

        lines = [f"Requirements relevant to {file_path}:", ""]

        # Group by distance
        by_distance = {}
        for node_id, data in sorted_nodes:
            distance = data["distance"]
            if distance not in by_distance:
                by_distance[distance] = []
            by_distance[distance].append((node_id, data["node"]))

        # Output grouped by distance
        for distance in sorted(by_distance.keys()):
            if distance == 0:
                lines.append("Direct:")
            else:
                level_label = "level" if distance == 1 else "levels"
                lines.append(f"Upstream ({distance} {level_label}):")

            for node_id, node in by_distance[distance]:
                lines.append(f'  {node_id}: "{node.title}" ({node.type.value})')

            lines.append("")

        # Remove trailing empty line
        if lines and lines[-1] == "":
            lines.pop()

        return '\n'.join(lines)


def relevant_command(
    file_path: str = typer.Argument(..., help="Source file path"),
    depth: int = typer.Option(3, "--depth", "-d", help="Maximum traversal depth"),
    format: str = typer.Option(
        "text",
        "--format",
        "-f",
        help="Output format: text or json"
    ),
):
    """Find requirements relevant to a source file.

    This command identifies all requirements that are related to a specific
    source file by finding nodes that reference the file and traversing
    their upstream traceability links.

    Examples:
        # Find requirements for a file
        contextgit relevant-for-file src/api.py

        # Limit to 1 level upstream
        contextgit relevant-for-file src/api.py --depth 1

        # Get JSON output
        contextgit relevant-for-file src/api.py --format json
    """
    fs = FileSystem()
    yaml = YAMLSerializer()
    formatter = OutputFormatter()
    handler = RelevantHandler(fs, yaml, formatter)

    try:
        result = handler.handle(file_path=file_path, depth=depth, format=format)
        typer.echo(result)
    except RepoNotFoundError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=1)
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=1)
