"""Node model for contextgit.

This module defines the Node class, representing a requirement or context item.
Nodes are the primary entities tracked in the contextgit system, containing
metadata about requirements, architecture decisions, code, tests, etc.
"""

from dataclasses import dataclass, field
from .enums import NodeType, NodeStatus
from .location import Location, location_from_dict


@dataclass
class Node:
    """Represents a requirement or context item in the system.

    Attributes:
        id: Unique identifier (e.g., 'BR-001', 'SR-012')
        type: Type of node (business, system, architecture, code, test, decision)
        title: Human-readable title
        file: Relative path from repository root to the file containing this node
        location: Location within the file (heading path or line range)
        status: Lifecycle status (draft, active, deprecated, superseded)
        last_updated: ISO 8601 timestamp of last update
        checksum: SHA-256 hex digest of the content
        llm_generated: Whether this node was created by an LLM
        tags: List of tags for additional categorization
    """

    id: str
    type: NodeType
    title: str
    file: str  # Relative path from repo root
    location: Location
    status: NodeStatus
    last_updated: str  # ISO 8601 timestamp
    checksum: str  # SHA-256 hex digest
    llm_generated: bool = False
    tags: list[str] = field(default_factory=list)

    def __post_init__(self):
        """Validate node data."""
        if not self.id or not self.id.strip():
            raise ValueError("Node ID cannot be empty")
        if not self.title or not self.title.strip():
            raise ValueError("Node title cannot be empty")
        if len(self.checksum) != 64:
            raise ValueError(f"Invalid checksum length: {len(self.checksum)}")

    def to_dict(self) -> dict:
        """Convert to dictionary for YAML serialization.

        Returns:
            Dictionary with sorted tags for deterministic YAML output.
        """
        return {
            'id': self.id,
            'type': self.type.value,
            'title': self.title,
            'file': self.file,
            'location': self.location.to_dict(),
            'status': self.status.value,
            'last_updated': self.last_updated,
            'checksum': self.checksum,
            'llm_generated': self.llm_generated,
            'tags': sorted(self.tags),
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Node':
        """Create Node from dictionary (YAML deserialization).

        Args:
            data: Dictionary containing node data from YAML

        Returns:
            Node instance with data from dictionary.
        """
        return cls(
            id=data['id'],
            type=NodeType(data['type']),
            title=data['title'],
            file=data['file'],
            location=location_from_dict(data['location']),
            status=NodeStatus(data.get('status', 'active')),
            last_updated=data['last_updated'],
            checksum=data['checksum'],
            llm_generated=data.get('llm_generated', False),
            tags=data.get('tags', []),
        )
