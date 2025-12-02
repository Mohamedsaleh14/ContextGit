"""Handler for contextgit fmt command."""

import json
from contextgit.handlers.base import BaseHandler
from contextgit.domain.index.manager import IndexManager


class FmtHandler(BaseHandler):
    """Handler for contextgit fmt command.

    The fmt command formats the index file for clean git diffs by sorting
    nodes and links deterministically. This ensures consistent YAML output
    that minimizes merge conflicts and produces readable diffs.
    """

    def handle(self, check: bool = False, format: str = "text") -> str:
        """Format index file for clean git diffs.

        Loads the index, then saves it back to disk. The save operation
        automatically formats the index through Index.to_dict(), which
        sorts nodes by ID and links by (from_id, to_id).

        Args:
            check: Only check if formatting is needed, don't write
            format: Output format (text or json)

        Returns:
            Status message

        Raises:
            IndexCorruptedError: If index cannot be loaded
            FileNotFoundError: If repository root cannot be found
        """
        # Find repo root
        repo_root = self.find_repo_root()

        # Load index
        index_mgr = IndexManager(self.fs, self.yaml, repo_root)
        index = index_mgr.load_index()

        # Count nodes and links for reporting
        node_count = len(index.nodes)
        link_count = len(index.links)

        if check:
            # Just report if formatting is needed
            # Index.to_dict() already sorts, so we can check by re-serializing
            original_content = self.fs.read_file(str(index_mgr.index_path))
            formatted_content = self.yaml.dump_yaml(index.to_dict())

            needs_formatting = original_content.strip() != formatted_content.strip()

            if format == "json":
                return json.dumps({
                    "needs_formatting": needs_formatting,
                    "node_count": node_count,
                    "link_count": link_count
                }, indent=2)
            else:
                if needs_formatting:
                    return "Index needs formatting"
                else:
                    return "Index is already formatted"
        else:
            # Save index (this automatically formats it due to Index.to_dict() sorting)
            index_mgr.save_index(index)

            if format == "json":
                return json.dumps({
                    "status": "success",
                    "message": "Index formatted",
                    "node_count": node_count,
                    "link_count": link_count
                }, indent=2)
            else:
                return f"Formatted .contextgit/requirements_index.yaml\nSorted {node_count} nodes, {link_count} links"
