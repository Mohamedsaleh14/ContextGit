"""Output formatting for contextgit.

This module provides the OutputFormatter class for formatting command outputs
as either human-readable text or JSON. All read commands support --format json
for LLM integration via Claude Code.
"""

import json
from contextgit.models.index import Index
from contextgit.models.node import Node
from contextgit.models.enums import SyncStatus


class OutputFormatter:
    """Format output as text or JSON.

    The OutputFormatter provides consistent formatting for all contextgit
    command outputs. It supports two output modes:
    - text: Human-readable output for terminal display
    - json: Machine-readable JSON for LLM consumption

    Text mode uses plain text formatting (no colors/tables in MVP) for
    simplicity and reliability. Rich terminal features can be added post-MVP.
    """

    def format_status(self, index: Index, format: str) -> str:
        """Format status command output.

        Args:
            index: Index containing nodes and links to summarize
            format: Output format - "text" or "json"

        Returns:
            Formatted status output as string.
        """
        if format == 'json':
            return self._format_status_json(index)
        else:
            return self._format_status_text(index)

    def _format_status_text(self, index: Index) -> str:
        """Format status as human-readable text.

        Args:
            index: Index to format

        Returns:
            Plain text status summary.
        """
        # Count nodes by type
        type_counts = {}
        for node in index.nodes.values():
            type_name = node.type.value
            type_counts[type_name] = type_counts.get(type_name, 0) + 1

        # Count links by status
        total_links = len(index.links)
        stale_links = sum(
            1 for link in index.links
            if link.sync_status != SyncStatus.OK
        )

        lines = []
        lines.append("contextgit status:\n")
        lines.append("Nodes:")
        for type_name, count in sorted(type_counts.items()):
            lines.append(f"  {type_name}: {count}")

        lines.append(f"\nLinks: {total_links}")
        lines.append(f"\nHealth:")
        lines.append(f"  Stale links: {stale_links}")

        return '\n'.join(lines)

    def _format_status_json(self, index: Index) -> str:
        """Format status as JSON.

        Args:
            index: Index to format

        Returns:
            JSON string with status data.
        """
        # Count nodes by type
        type_counts = {}
        for node in index.nodes.values():
            type_name = node.type.value
            type_counts[type_name] = type_counts.get(type_name, 0) + 1

        # Count links by status
        stale_links = sum(
            1 for link in index.links
            if link.sync_status != SyncStatus.OK
        )

        data = {
            'nodes': type_counts,
            'links': {
                'total': len(index.links),
                'stale': stale_links,
            },
        }

        return json.dumps(data, indent=2)

    def format_node(self, node: Node, format: str) -> str:
        """Format node details.

        Args:
            node: Node to format
            format: Output format - "text" or "json"

        Returns:
            Formatted node details as string.
        """
        if format == 'json':
            return json.dumps(node.to_dict(), indent=2)
        else:
            lines = [
                f"ID: {node.id}",
                f"Type: {node.type.value}",
                f"Title: {node.title}",
                f"File: {node.file}",
                f"Status: {node.status.value}",
                f"Last Updated: {node.last_updated}",
                f"Checksum: {node.checksum}",
            ]
            if node.tags:
                lines.append(f"Tags: {', '.join(node.tags)}")
            return '\n'.join(lines)

    def format_extract_result(
        self,
        node: Node,
        snippet: str,
        format: str
    ) -> str:
        """Format extract command result.

        The extract command returns both the node metadata and the extracted
        content snippet. In JSON mode, both are included. In text mode,
        only the snippet is returned (for easy piping to LLMs).

        Args:
            node: Node metadata
            snippet: Extracted text content
            format: Output format - "text" or "json"

        Returns:
            Formatted extract result.
        """
        if format == 'json':
            return json.dumps({
                'node': node.to_dict(),
                'snippet': snippet,
            }, indent=2)
        else:
            return snippet

    def format_scan_result(self, summary: dict, format: str) -> str:
        """Format scan command result.

        Args:
            summary: Scan summary data with keys:
                - files_scanned: Number of files scanned
                - nodes_added: List of new node IDs (optional)
                - nodes_updated: List of updated node IDs (optional)
                - dry_run: Whether this was a dry run (optional)
            format: Output format - "text" or "json"

        Returns:
            Formatted scan result.
        """
        if format == 'json':
            return json.dumps(summary, indent=2)
        else:
            lines = [
                f"Scanned {summary['files_scanned']} files",
                f"Added: {len(summary.get('nodes_added', []))} nodes",
                f"Updated: {len(summary.get('nodes_updated', []))} nodes",
            ]
            if summary.get('dry_run'):
                lines.append("(dry run - no changes saved)")
            return '\n'.join(lines)
