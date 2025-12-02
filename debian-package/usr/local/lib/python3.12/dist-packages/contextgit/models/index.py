"""Index model for contextgit.

This module defines the Index class, which serves as the central container
for all nodes and links in the system. The index is serialized to
.contextgit/requirements_index.yaml and is the single source of truth for
the project's requirements traceability.
"""

from dataclasses import dataclass, field
from .node import Node
from .link import Link


@dataclass
class Index:
    """Container for all nodes and links in the system.

    The Index is the central data structure containing all requirements,
    context items, and their relationships. It is persisted to disk as
    .contextgit/requirements_index.yaml.

    Attributes:
        nodes: Dictionary mapping node IDs to Node instances
        links: List of Link instances representing traceability relationships
    """

    nodes: dict[str, Node] = field(default_factory=dict)
    links: list[Link] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to dictionary for YAML serialization.

        Nodes are sorted by ID and links are sorted by (from_id, to_id)
        to ensure deterministic YAML output for clean git diffs.

        Returns:
            Dictionary with sorted nodes and links for deterministic output.
        """
        return {
            'nodes': [node.to_dict() for node in sorted(
                self.nodes.values(), key=lambda n: n.id
            )],
            'links': [link.to_dict() for link in sorted(
                self.links, key=lambda l: (l.from_id, l.to_id)
            )],
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Index':
        """Create Index from dictionary (YAML deserialization).

        Args:
            data: Dictionary containing index data from YAML

        Returns:
            Index instance with nodes and links from dictionary.
        """
        nodes = {
            node_data['id']: Node.from_dict(node_data)
            for node_data in data.get('nodes', [])
        }
        links = [Link.from_dict(link_data) for link_data in data.get('links', [])]
        return cls(nodes=nodes, links=links)
