"""Configuration model for contextgit."""

from dataclasses import dataclass, field


@dataclass
class Config:
    """Configuration for contextgit project.

    Attributes:
        tag_prefixes: Mapping of node type to ID prefix (e.g., 'business' -> 'BR-')
        directories: Mapping of node type to suggested directory path
    """

    tag_prefixes: dict[str, str] = field(default_factory=dict)
    directories: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Convert to dictionary for YAML serialization.

        Returns:
            Dictionary with sorted keys for deterministic YAML output.
        """
        return {
            'tag_prefixes': dict(sorted(self.tag_prefixes.items())),
            'directories': dict(sorted(self.directories.items())),
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Config':
        """Create Config from dictionary (YAML deserialization).

        Args:
            data: Dictionary containing config data from YAML

        Returns:
            Config instance with data from dictionary.
        """
        return cls(
            tag_prefixes=data.get('tag_prefixes', {}),
            directories=data.get('directories', {}),
        )

    @classmethod
    def get_default(cls) -> 'Config':
        """Get default configuration with standard prefixes and directory layout.

        Returns:
            Config instance with default values for all node types.
        """
        return cls(
            tag_prefixes={
                'business': 'BR-',
                'system': 'SR-',
                'architecture': 'AR-',
                'code': 'C-',
                'test': 'T-',
                'decision': 'ADR-',
            },
            directories={
                'business': 'docs/01_business',
                'system': 'docs/02_system',
                'architecture': 'docs/03_architecture',
                'code': 'src',
                'test': 'tests',
            },
        )
