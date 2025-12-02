"""Handler for contextgit confirm command."""

import json
from datetime import datetime, timezone
from pathlib import Path

from contextgit.handlers.base import BaseHandler
from contextgit.domain.index.manager import IndexManager
from contextgit.domain.checksum.calculator import ChecksumCalculator
from contextgit.domain.location.snippet import SnippetExtractor
from contextgit.models.enums import SyncStatus
from contextgit.exceptions import NodeNotFoundError, RepoNotFoundError


class ConfirmHandler(BaseHandler):
    """Handler for contextgit confirm command.

    Marks a node as synchronized with its upstream dependencies after the user
    has reviewed and addressed any upstream changes. Updates the node's checksum
    to reflect the current file content and marks all incoming links as OK.
    """

    def handle(self, node_id: str, format: str = "text") -> str:
        """
        Confirm node is synchronized after updates.

        Args:
            node_id: Node ID to confirm
            format: Output format (text or json)

        Returns:
            Success message with details of updated links

        Raises:
            RepoNotFoundError: If not in a contextgit repository
            NodeNotFoundError: If node doesn't exist
            FileNotFoundError: If node's source file doesn't exist
        """
        # Find repo root
        repo_root = self.find_repo_root()

        # Load index
        index_mgr = IndexManager(self.fs, self.yaml, repo_root)
        index = index_mgr.load_index()

        # Validate node exists
        node = index_mgr.get_node(node_id)

        # Get current timestamp
        now = datetime.now(timezone.utc).isoformat()

        # Update all incoming links (where this node is downstream/to)
        incoming_links = index_mgr.get_links_to(node_id)
        updated_count = 0

        for link in incoming_links:
            if link.sync_status != SyncStatus.OK:
                # Update the link in place
                index_mgr.update_link(
                    link.from_id,
                    link.to_id,
                    {
                        'sync_status': SyncStatus.OK,
                        'last_checked': now
                    }
                )
                updated_count += 1
            else:
                # Still update last_checked even if already OK
                index_mgr.update_link(
                    link.from_id,
                    link.to_id,
                    {'last_checked': now}
                )

        # Update node's checksum to current file content
        file_path = Path(repo_root) / node.file
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {node.file}")

        # Read file content and calculate new checksum
        file_content = self.fs.read_file(str(file_path))
        checksum_calc = ChecksumCalculator()

        # Extract the snippet for this node's location to calculate checksum
        snippet_extractor = SnippetExtractor(self.fs)
        snippet = snippet_extractor.extract_snippet(str(file_path), node.location)
        new_checksum = checksum_calc.calculate_checksum(snippet)

        # Update node's checksum
        index_mgr.update_node(node_id, {
            'checksum': new_checksum,
            'last_updated': now
        })

        # Save index
        index_mgr.save_index(index)

        # Format output
        if format == "json":
            # Reload links to get updated data
            updated_links = index_mgr.get_links_to(node_id)
            upstream_data = []
            for link in updated_links:
                from_node = index_mgr.get_node(link.from_id)
                upstream_data.append({
                    "from_id": link.from_id,
                    "from_title": from_node.title,
                    "relation": link.relation_type.value,
                    "sync_status": link.sync_status.value
                })

            return json.dumps({
                "status": "success",
                "node_id": node_id,
                "links_updated": updated_count,
                "upstream_links": upstream_data
            }, indent=2)
        else:
            # Text format output
            lines = [f"Confirmed sync for {node_id}"]

            if incoming_links:
                lines.append(f"Updated {len(incoming_links)} upstream link{'s' if len(incoming_links) != 1 else ''}:")
                # Reload to get updated sync status
                updated_links = index_mgr.get_links_to(node_id)
                for link in updated_links:
                    from_node = index_mgr.get_node(link.from_id)
                    lines.append(f"  {link.from_id} \u2192 {node_id} ({link.sync_status.value})")
            else:
                lines.append("No upstream links to update.")

            return '\n'.join(lines)
