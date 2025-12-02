"""Handler for contextgit show command."""

import json
from pathlib import Path
from contextgit.domain.index.manager import IndexManager
from contextgit.infra.filesystem import FileSystem
from contextgit.infra.yaml_io import YAMLSerializer
from contextgit.infra.output import OutputFormatter
from contextgit.exceptions import NodeNotFoundError, RepoNotFoundError


class ShowHandler:
    """Handler for contextgit show command.

    Displays detailed information about a specific node including its
    upstream and downstream traceability links.
    """

    def __init__(self, filesystem: FileSystem, yaml_io: YAMLSerializer, formatter: OutputFormatter):
        """Initialize ShowHandler.

        Args:
            filesystem: File system abstraction
            yaml_io: YAML serialization handler
            formatter: Output formatter
        """
        self.fs = filesystem
        self.yaml = yaml_io
        self.formatter = formatter

    def find_repo_root(self) -> str:
        """Find repository root starting from current directory.

        Returns:
            Absolute path to repository root

        Raises:
            RepoNotFoundError: If not in a contextgit repository
        """
        try:
            return self.fs.find_repo_root(str(Path.cwd()))
        except FileNotFoundError:
            raise RepoNotFoundError("Not in a contextgit repository. Run 'contextgit init' first.")

    def handle(self, node_id: str, format: str = "text") -> str:
        """Show details for a node.

        Args:
            node_id: Node ID to show
            format: Output format (text or json)

        Returns:
            Node details with links formatted as requested

        Raises:
            NodeNotFoundError: If node doesn't exist
            RepoNotFoundError: If not in a contextgit repository
        """
        # Find repo root
        repo_root = self.find_repo_root()

        # Load index
        index_mgr = IndexManager(self.fs, self.yaml, repo_root)
        index = index_mgr.load_index()

        # Get node
        node = index_mgr.get_node(node_id)

        # Get links
        upstream_links = index_mgr.get_links_to(node_id)
        downstream_links = index_mgr.get_links_from(node_id)

        # Format output
        if format == "json":
            return self._format_json(node, upstream_links, downstream_links, index_mgr)
        else:
            return self._format_text(node, upstream_links, downstream_links, index_mgr)

    def _format_json(self, node, upstream_links, downstream_links, index_mgr):
        """Format output as JSON.

        Args:
            node: The node to display
            upstream_links: List of incoming links
            downstream_links: List of outgoing links
            index_mgr: Index manager for looking up linked nodes

        Returns:
            JSON string with node and link details
        """
        upstream_data = []
        for link in upstream_links:
            from_node = index_mgr.get_node(link.from_id)
            upstream_data.append({
                "id": link.from_id,
                "title": from_node.title,
                "relation": link.relation_type.value,
                "sync_status": link.sync_status.value
            })

        downstream_data = []
        for link in downstream_links:
            to_node = index_mgr.get_node(link.to_id)
            downstream_data.append({
                "id": link.to_id,
                "title": to_node.title,
                "relation": link.relation_type.value,
                "sync_status": link.sync_status.value
            })

        return json.dumps({
            "node": node.to_dict(),
            "upstream": upstream_data,
            "downstream": downstream_data
        }, indent=2)

    def _format_text(self, node, upstream_links, downstream_links, index_mgr):
        """Format output as human-readable text.

        Args:
            node: The node to display
            upstream_links: List of incoming links
            downstream_links: List of outgoing links
            index_mgr: Index manager for looking up linked nodes

        Returns:
            Plain text string with node and link details
        """
        lines = []
        lines.append(f"Node: {node.id}")
        lines.append("")
        lines.append(f"Type: {node.type.value}")
        lines.append(f"Title: {node.title}")
        lines.append(f"File: {node.file}")

        # Format location
        location_str = self._format_location(node.location)
        lines.append(f"Location: {location_str}")

        lines.append(f"Status: {node.status.value}")
        lines.append(f"Last updated: {node.last_updated}")
        lines.append(f"Checksum: {node.checksum}")

        if node.tags:
            lines.append(f"Tags: {', '.join(node.tags)}")

        # Format upstream links
        if upstream_links:
            lines.append("")
            lines.append(f"Upstream ({len(upstream_links)}):")
            for link in upstream_links:
                from_node = index_mgr.get_node(link.from_id)
                lines.append(
                    f'  {link.from_id}: "{from_node.title}" '
                    f'[{link.relation_type.value}] ({link.sync_status.value})'
                )

        # Format downstream links
        if downstream_links:
            lines.append("")
            lines.append(f"Downstream ({len(downstream_links)}):")
            for link in downstream_links:
                to_node = index_mgr.get_node(link.to_id)
                lines.append(
                    f'  {link.to_id}: "{to_node.title}" '
                    f'[{link.relation_type.value}] ({link.sync_status.value})'
                )

        return '\n'.join(lines)

    def _format_location(self, location):
        """Format location for text output.

        Args:
            location: Location object (HeadingLocation or LineLocation)

        Returns:
            Formatted location string
        """
        if hasattr(location, 'path') and location.kind == 'heading':
            # HeadingLocation
            path_str = ', '.join(f'"{h}"' for h in location.path)
            return f"heading \u2192 [{path_str}]"
        elif hasattr(location, 'start') and location.kind == 'lines':
            # LineLocation
            return f"lines {location.start}-{location.end}"
        else:
            return str(location)
