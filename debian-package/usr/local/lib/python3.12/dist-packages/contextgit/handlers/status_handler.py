"""Handler for contextgit status command."""

import json
from pathlib import Path
from contextgit.domain.index.manager import IndexManager
from contextgit.domain.linking.engine import LinkingEngine
from contextgit.infra.filesystem import FileSystem
from contextgit.infra.yaml_io import YAMLSerializer
from contextgit.infra.output import OutputFormatter
from contextgit.models.enums import SyncStatus
from contextgit.exceptions import RepoNotFoundError


class StatusHandler:
    """Handler for contextgit status command.

    Displays project health information including node counts,
    link status, and orphan detection.
    """

    def __init__(self, filesystem: FileSystem, yaml_io: YAMLSerializer, formatter: OutputFormatter):
        """Initialize StatusHandler.

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

    def handle(
        self,
        stale: bool = False,
        orphans: bool = False,
        format: str = "text"
    ) -> str:
        """Show repository status.

        Args:
            stale: Show only stale links
            orphans: Show only orphan nodes
            format: Output format (text or json)

        Returns:
            Status information

        Raises:
            RepoNotFoundError: If not in a contextgit repository
        """
        # Find repo root
        repo_root = self.find_repo_root()

        # Load index
        index_mgr = IndexManager(self.fs, self.yaml, repo_root)
        index = index_mgr.load_index()

        # Handle --stale flag
        if stale:
            return self._handle_stale(index, format)

        # Handle --orphans flag
        if orphans:
            return self._handle_orphans(index, format)

        # Default: show overall status
        return self.formatter.format_status(index, format)

    def _handle_stale(self, index, format: str) -> str:
        """Handle --stale flag to show only stale links.

        Args:
            index: Index to analyze
            format: Output format (text or json)

        Returns:
            Formatted stale links output
        """
        # Find all stale links (not OK status)
        stale_links = [
            link for link in index.links
            if link.sync_status != SyncStatus.OK
        ]

        if format == "json":
            return json.dumps({
                'stale_links': [link.to_dict() for link in stale_links]
            }, indent=2)
        else:
            if not stale_links:
                return "No stale links"

            # Group by sync status
            upstream_changed = []
            downstream_changed = []
            broken = []

            for link in stale_links:
                if link.sync_status == SyncStatus.UPSTREAM_CHANGED:
                    upstream_changed.append(link)
                elif link.sync_status == SyncStatus.DOWNSTREAM_CHANGED:
                    downstream_changed.append(link)
                elif link.sync_status == SyncStatus.BROKEN:
                    broken.append(link)

            lines = ["Stale links (need review):", ""]

            if upstream_changed:
                lines.append("Upstream changed:")
                for link in upstream_changed:
                    lines.append(
                        f"  {link.from_id} \u2192 {link.to_id} "
                        f"(last checked: {link.last_checked})"
                    )
                lines.append("")

            if downstream_changed:
                lines.append("Downstream changed:")
                for link in downstream_changed:
                    lines.append(
                        f"  {link.from_id} \u2192 {link.to_id} "
                        f"(last checked: {link.last_checked})"
                    )
                lines.append("")

            if broken:
                lines.append("Broken:")
                for link in broken:
                    lines.append(
                        f"  {link.from_id} \u2192 {link.to_id} "
                        f"(last checked: {link.last_checked})"
                    )
                lines.append("")

            lines.append("Run 'contextgit confirm <ID>' to mark as synchronized.")

            return '\n'.join(lines)

    def _handle_orphans(self, index, format: str) -> str:
        """Handle --orphans flag to show orphan nodes.

        Args:
            index: Index to analyze
            format: Output format (text or json)

        Returns:
            Formatted orphan nodes output
        """
        linking_engine = LinkingEngine()
        no_upstream, no_downstream = linking_engine.detect_orphans(index)

        if format == "json":
            return json.dumps({
                'orphan_nodes': {
                    'no_upstream': no_upstream,
                    'no_downstream': no_downstream
                }
            }, indent=2)
        else:
            if not no_upstream and not no_downstream:
                return "No orphan nodes"

            lines = ["Orphan nodes:", ""]

            if no_upstream:
                lines.append(f"No upstream:")
                for node_id in no_upstream:
                    node = index.nodes.get(node_id)
                    if node:
                        lines.append(
                            f'  {node_id}: "{node.title}" ({node.type.value})'
                        )
                lines.append("")

            if no_downstream:
                lines.append(f"No downstream:")
                for node_id in no_downstream:
                    node = index.nodes.get(node_id)
                    if node:
                        lines.append(
                            f'  {node_id}: "{node.title}" ({node.type.value})'
                        )

            return '\n'.join(lines).rstrip()


# CLI command function (can be imported by main CLI module)
def status_command(
    stale: bool = False,
    orphans: bool = False,
    format: str = "text",
):
    """Show project status and health.

    Args:
        stale: Show only stale links
        orphans: Show only orphan nodes
        format: Output format (text or json)

    This function is designed to be called from a Typer CLI command.
    It creates the necessary dependencies and calls the handler.
    """
    from contextgit.infra.filesystem import FileSystem
    from contextgit.infra.yaml_io import YAMLSerializer
    from contextgit.infra.output import OutputFormatter

    fs = FileSystem()
    yaml = YAMLSerializer()
    formatter = OutputFormatter()
    handler = StatusHandler(fs, yaml, formatter)

    try:
        result = handler.handle(stale=stale, orphans=orphans, format=format)
        print(result)
    except Exception as e:
        print(f"Error: {e}", file=__import__('sys').stderr)
        raise SystemExit(1)
