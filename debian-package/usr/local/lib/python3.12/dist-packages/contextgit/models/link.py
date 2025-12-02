"""Link model for contextgit.

This module defines the Link class, representing a traceability relationship
between two nodes. Links track upstream/downstream relationships and their
synchronization status.
"""

from dataclasses import dataclass
from .enums import RelationType, SyncStatus


@dataclass
class Link:
    """Represents a traceability relationship between two nodes.

    Links are directed relationships from a source (upstream) node to a
    target (downstream) node. They track the relationship type and whether
    the link is still synchronized (i.e., whether either node has changed
    since the link was established).

    Attributes:
        from_id: Source node ID (upstream)
        to_id: Target node ID (downstream)
        relation_type: Type of relationship (refines, implements, tests, etc.)
        sync_status: Synchronization status (ok, upstream_changed, etc.)
        last_checked: ISO 8601 timestamp of last synchronization check
    """

    from_id: str  # Source node ID (upstream)
    to_id: str    # Target node ID (downstream)
    relation_type: RelationType
    sync_status: SyncStatus
    last_checked: str  # ISO 8601 timestamp

    def __post_init__(self):
        """Validate link data."""
        if not self.from_id or not self.to_id:
            raise ValueError("Link IDs cannot be empty")
        if self.from_id == self.to_id:
            raise ValueError("Self-referential link not allowed")

    def to_dict(self) -> dict:
        """Convert to dictionary for YAML serialization.

        Returns:
            Dictionary representation of the link.
        """
        return {
            'from': self.from_id,
            'to': self.to_id,
            'relation_type': self.relation_type.value,
            'sync_status': self.sync_status.value,
            'last_checked': self.last_checked,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Link':
        """Create Link from dictionary (YAML deserialization).

        Args:
            data: Dictionary containing link data from YAML

        Returns:
            Link instance with data from dictionary.
        """
        return cls(
            from_id=data['from'],
            to_id=data['to'],
            relation_type=RelationType(data['relation_type']),
            sync_status=SyncStatus(data['sync_status']),
            last_checked=data['last_checked'],
        )
