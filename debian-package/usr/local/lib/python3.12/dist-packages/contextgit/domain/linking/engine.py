"""Traceability linking and graph operations.

This module implements the LinkingEngine class, which manages the creation
and maintenance of traceability links between nodes. It provides functionality
for building links from metadata, updating sync status, traversing the
traceability graph, and detecting orphan nodes.
"""

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from contextgit.models.index import Index
from contextgit.models.link import Link
from contextgit.models.node import Node
from contextgit.models.enums import NodeType, RelationType, SyncStatus

if TYPE_CHECKING:
    # Forward reference to avoid circular import with metadata parser
    from typing import Any
    RawMetadata = Any


class LinkingEngine:
    """Manages traceability links and graph operations.

    The LinkingEngine is responsible for:
    - Building links from upstream/downstream metadata fields
    - Inferring relation types based on node types
    - Updating sync status when nodes change
    - Traversing the traceability graph (upstream/downstream)
    - Detecting orphan nodes without proper linkage
    """

    def build_links_from_metadata(
        self,
        nodes: dict[str, Node],
        metadata_map: dict[str, 'RawMetadata']
    ) -> list[Link]:
        """
        Build links based on upstream/downstream in metadata.

        Infers relation types based on node types.

        Args:
            nodes: All nodes in index
            metadata_map: Metadata for each node (with upstream/downstream fields)

        Returns:
            List of links to add to index
        """
        links = []
        now = datetime.now(timezone.utc).isoformat()

        for node_id, metadata in metadata_map.items():
            # Create links from upstream
            for upstream_id in metadata.upstream:
                if upstream_id in nodes:
                    relation = self._infer_relation_type(
                        nodes[upstream_id].type,
                        nodes[node_id].type
                    )
                    links.append(Link(
                        from_id=upstream_id,
                        to_id=node_id,
                        relation_type=relation,
                        sync_status=SyncStatus.OK,
                        last_checked=now,
                    ))

            # Create links from downstream
            for downstream_id in metadata.downstream:
                if downstream_id in nodes:
                    relation = self._infer_relation_type(
                        nodes[node_id].type,
                        nodes[downstream_id].type
                    )
                    links.append(Link(
                        from_id=node_id,
                        to_id=downstream_id,
                        relation_type=relation,
                        sync_status=SyncStatus.OK,
                        last_checked=now,
                    ))

        return links

    def _infer_relation_type(
        self, from_type: NodeType, to_type: NodeType
    ) -> RelationType:
        """Infer relation type based on node types."""
        # code -> test: tests
        if to_type == NodeType.TEST:
            return RelationType.TESTS

        # business -> *: refines
        if from_type == NodeType.BUSINESS:
            return RelationType.REFINES

        # system -> code: implements
        # system -> architecture: refines
        if from_type == NodeType.SYSTEM:
            if to_type == NodeType.CODE:
                return RelationType.IMPLEMENTS
            return RelationType.REFINES

        # architecture -> code: implements
        if from_type == NodeType.ARCHITECTURE:
            return RelationType.IMPLEMENTS

        # Default
        return RelationType.REFINES

    def update_sync_status(
        self, index: Index, changed_node_ids: set[str]
    ) -> None:
        """
        Update sync status for links affected by changed nodes.

        Sets UPSTREAM_CHANGED or DOWNSTREAM_CHANGED as appropriate.

        Args:
            index: Index to update (modified in place)
            changed_node_ids: Set of node IDs that changed
        """
        now = datetime.now(timezone.utc).isoformat()

        for link in index.links:
            # If upstream node changed
            if link.from_id in changed_node_ids:
                link.sync_status = SyncStatus.UPSTREAM_CHANGED
                link.last_checked = now

            # If downstream node changed
            if link.to_id in changed_node_ids:
                link.sync_status = SyncStatus.DOWNSTREAM_CHANGED
                link.last_checked = now

    def get_upstream_nodes(
        self, index: Index, node_id: str, depth: int = 1
    ) -> list[Node]:
        """
        Get all upstream nodes up to specified depth.

        Uses breadth-first traversal.

        Args:
            index: Index to search
            node_id: Starting node
            depth: How many levels to traverse (default: 1)

        Returns:
            List of upstream nodes
        """
        visited = set()
        result = []

        def traverse(current_id: str, current_depth: int):
            if current_depth > depth or current_id in visited:
                return

            visited.add(current_id)

            # Find incoming links
            for link in index.links:
                if link.to_id == current_id and link.from_id not in visited:
                    upstream_node = index.nodes.get(link.from_id)
                    if upstream_node:
                        result.append(upstream_node)
                        traverse(link.from_id, current_depth + 1)

        traverse(node_id, 0)
        return result

    def get_downstream_nodes(
        self, index: Index, node_id: str, depth: int = 1
    ) -> list[Node]:
        """
        Get all downstream nodes up to specified depth.

        Uses breadth-first traversal.

        Args:
            index: Index to search
            node_id: Starting node
            depth: How many levels to traverse (default: 1)

        Returns:
            List of downstream nodes
        """
        visited = set()
        result = []

        def traverse(current_id: str, current_depth: int):
            if current_depth > depth or current_id in visited:
                return

            visited.add(current_id)

            # Find outgoing links
            for link in index.links:
                if link.from_id == current_id and link.to_id not in visited:
                    downstream_node = index.nodes.get(link.to_id)
                    if downstream_node:
                        result.append(downstream_node)
                        traverse(link.to_id, current_depth + 1)

        traverse(node_id, 0)
        return result

    def detect_orphans(
        self, index: Index
    ) -> tuple[list[str], list[str]]:
        """
        Detect orphan nodes (no upstream or no downstream).

        Business nodes don't need upstream.
        Code/test nodes don't need downstream.

        Args:
            index: Index to analyze

        Returns:
            Tuple of (nodes_without_upstream, nodes_without_downstream)
        """
        no_upstream = []
        no_downstream = []

        # Build sets of nodes with links
        has_upstream = set()
        has_downstream = set()

        for link in index.links:
            has_downstream.add(link.from_id)
            has_upstream.add(link.to_id)

        # Check each node
        for node_id, node in index.nodes.items():
            # Business requirements don't need upstream
            if node.type != NodeType.BUSINESS and node_id not in has_upstream:
                no_upstream.append(node_id)

            # Code and test don't need downstream
            if node.type not in (NodeType.CODE, NodeType.TEST) and node_id not in has_downstream:
                no_downstream.append(node_id)

        return no_upstream, no_downstream
