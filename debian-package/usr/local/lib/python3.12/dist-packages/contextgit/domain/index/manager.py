"""Index management with atomic operations.

This module implements the IndexManager class, which provides CRUD operations
for the requirements index. It ensures atomic writes to prevent index corruption
and maintains an in-memory cache for performance.
"""

import dataclasses
from pathlib import Path
from contextgit.models.index import Index
from contextgit.models.node import Node
from contextgit.models.link import Link
from contextgit.infra.filesystem import FileSystem
from contextgit.infra.yaml_io import YAMLSerializer
from contextgit.exceptions import IndexCorruptedError, NodeNotFoundError
from contextgit.constants import CONTEXTGIT_DIR, INDEX_FILE


class IndexManager:
    """Manages CRUD operations for the requirements index.

    The IndexManager is responsible for:
    - Loading and caching the index from disk
    - Saving the index atomically to prevent corruption
    - Adding, updating, and deleting nodes
    - Adding, updating, and querying links
    - Validating index integrity before saving

    All write operations use atomic file writes (temp + rename) to ensure
    that the index is never left in a corrupted state.
    """

    def __init__(self, filesystem: FileSystem, yaml_io: YAMLSerializer, repo_root: str):
        """Initialize IndexManager.

        Args:
            filesystem: File system abstraction
            yaml_io: YAML serialization handler
            repo_root: Repository root path
        """
        self.fs = filesystem
        self.yaml = yaml_io
        self.repo_root = Path(repo_root)
        self.index_path = self.repo_root / CONTEXTGIT_DIR / INDEX_FILE
        self._index: Index | None = None

    def load_index(self) -> Index:
        """Load index from disk. Results are cached in memory.

        Returns:
            Index object with nodes and links

        Raises:
            IndexCorruptedError: If index file is malformed
        """
        if self._index is not None:
            return self._index

        if not self.index_path.exists():
            # Return empty index if file doesn't exist
            self._index = Index()
            return self._index

        try:
            content = self.fs.read_file(str(self.index_path))
            data = self.yaml.load_yaml(content)
            self._index = Index.from_dict(data)
            return self._index
        except Exception as e:
            raise IndexCorruptedError(f"Failed to load index: {e}")

    def save_index(self, index: Index) -> None:
        """Save index to disk atomically.

        Validates index before saving. Uses atomic write (temp + rename).

        Args:
            index: Index to save

        Raises:
            ValueError: If index validation fails
            IOError: If file write fails
        """
        # Validate before saving
        self._validate_index(index)

        # Ensure .contextgit directory exists
        self.index_path.parent.mkdir(parents=True, exist_ok=True)

        # Convert to dict and serialize
        data = index.to_dict()
        content = self.yaml.dump_yaml(data)

        # Write atomically
        self.fs.write_file_atomic(str(self.index_path), content)

        # Update cache
        self._index = index

    def get_node(self, node_id: str) -> Node:
        """Get node by ID.

        Args:
            node_id: Node identifier

        Returns:
            Node object

        Raises:
            NodeNotFoundError: If node doesn't exist
        """
        index = self.load_index()
        if node_id not in index.nodes:
            raise NodeNotFoundError(f"Node not found: {node_id}")
        return index.nodes[node_id]

    def add_node(self, node: Node) -> None:
        """Add a new node to the index.

        Args:
            node: Node to add

        Raises:
            ValueError: If node ID already exists
        """
        index = self.load_index()
        if node.id in index.nodes:
            raise ValueError(f"Node {node.id} already exists")
        index.nodes[node.id] = node

    def update_node(self, node_id: str, updates: dict) -> None:
        """Update an existing node.

        Args:
            node_id: Node to update
            updates: Fields to update (partial)

        Raises:
            NodeNotFoundError: If node doesn't exist
        """
        index = self.load_index()
        if node_id not in index.nodes:
            raise NodeNotFoundError(f"Node not found: {node_id}")

        node = index.nodes[node_id]
        # Create updated node (dataclasses are immutable-ish)
        updated_node = dataclasses.replace(node, **updates)
        index.nodes[node_id] = updated_node

    def delete_node(self, node_id: str) -> None:
        """Delete a node from the index.

        Args:
            node_id: Node to delete

        Raises:
            NodeNotFoundError: If node doesn't exist
        """
        index = self.load_index()
        if node_id not in index.nodes:
            raise NodeNotFoundError(f"Node not found: {node_id}")
        del index.nodes[node_id]

    def add_link(self, link: Link) -> None:
        """Add a new link to the index.

        Validates that both nodes exist.

        Args:
            link: Link to add

        Raises:
            NodeNotFoundError: If either node doesn't exist
            ValueError: If link already exists
        """
        index = self.load_index()

        # Validate that both nodes exist
        if link.from_id not in index.nodes:
            raise NodeNotFoundError(f"Source node not found: {link.from_id}")
        if link.to_id not in index.nodes:
            raise NodeNotFoundError(f"Target node not found: {link.to_id}")

        # Check if link already exists
        existing = self.get_link(link.from_id, link.to_id)
        if existing:
            raise ValueError(f"Link already exists: {link.from_id} -> {link.to_id}")

        index.links.append(link)

    def update_link(self, from_id: str, to_id: str, updates: dict) -> None:
        """Update an existing link.

        Args:
            from_id: Source node ID
            to_id: Target node ID
            updates: Fields to update (partial)

        Raises:
            ValueError: If link doesn't exist
        """
        index = self.load_index()
        link = self.get_link(from_id, to_id)
        if not link:
            raise ValueError(f"Link not found: {from_id} -> {to_id}")

        # Find and update
        for i, l in enumerate(index.links):
            if l.from_id == from_id and l.to_id == to_id:
                updated_link = dataclasses.replace(l, **updates)
                index.links[i] = updated_link
                break

    def get_link(self, from_id: str, to_id: str) -> Link | None:
        """Get a specific link.

        Args:
            from_id: Source node ID
            to_id: Target node ID

        Returns:
            Link object or None if not found
        """
        index = self.load_index()
        for link in index.links:
            if link.from_id == from_id and link.to_id == to_id:
                return link
        return None

    def get_links_from(self, node_id: str) -> list[Link]:
        """Get all outgoing links from a node.

        Args:
            node_id: Source node ID

        Returns:
            List of outgoing links
        """
        index = self.load_index()
        return [link for link in index.links if link.from_id == node_id]

    def get_links_to(self, node_id: str) -> list[Link]:
        """Get all incoming links to a node.

        Args:
            node_id: Target node ID

        Returns:
            List of incoming links
        """
        index = self.load_index()
        return [link for link in index.links if link.to_id == node_id]

    def _validate_index(self, index: Index) -> None:
        """Validate index structure before saving.

        Args:
            index: Index to validate

        Raises:
            ValueError: If index structure is invalid
        """
        # Check for duplicate node IDs (should not happen with dict)
        node_ids = set()
        for node_id in index.nodes:
            if node_id in node_ids:
                raise ValueError(f"Duplicate node ID: {node_id}")
            node_ids.add(node_id)

        # Check that all links reference existing nodes
        for link in index.links:
            if link.from_id not in index.nodes:
                raise ValueError(f"Link references non-existent node: {link.from_id}")
            if link.to_id not in index.nodes:
                raise ValueError(f"Link references non-existent node: {link.to_id}")
