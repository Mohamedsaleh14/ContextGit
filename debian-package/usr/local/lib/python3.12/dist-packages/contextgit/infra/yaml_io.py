"""YAML serialization with deterministic output for git-friendliness.

This module provides a YAMLSerializer class that ensures consistent,
deterministic YAML output for the requirements index and config files.
This is critical for clean git diffs and merge conflict prevention.
"""

from io import StringIO
from typing import Any

from ruamel.yaml import YAML


class YAMLSerializer:
    """YAML serialization with deterministic output.

    This class configures ruamel.yaml to produce consistent, human-readable
    YAML output that is git-friendly:
    - Consistent indentation (2 spaces)
    - No flow style (always block style)
    - Preserved quotes where appropriate
    - Deterministic ordering (when combined with sorted data structures)

    The YAMLSerializer is used by the Index Manager to ensure that the
    requirements index file has minimal diffs when changes are made.
    """

    def __init__(self):
        """Initialize YAML serializer with deterministic settings."""
        self.yaml = YAML()

        # Use block style (not flow style) for readability
        self.yaml.default_flow_style = False

        # Consistent indentation: 2 spaces for mappings and sequences
        self.yaml.indent(mapping=2, sequence=2, offset=0)

        # Reasonable line width for readability
        self.yaml.width = 120

        # Preserve quotes to maintain consistency
        self.yaml.preserve_quotes = True

    def load_yaml(self, content: str) -> Any:
        """Parse YAML content safely.

        Args:
            content: YAML string to parse

        Returns:
            Parsed YAML data structure (typically dict or list)

        Raises:
            ruamel.yaml.YAMLError: If YAML parsing fails
        """
        return self.yaml.load(content)

    def dump_yaml(self, data: Any) -> str:
        """Dump data structure to YAML with deterministic formatting.

        Args:
            data: Data structure to serialize (typically dict or list)

        Returns:
            YAML string with consistent formatting

        Note:
            For truly deterministic output, ensure that the input data
            structure has sorted keys (e.g., use sorted dictionaries or
            ensure nodes and links are pre-sorted).
        """
        stream = StringIO()
        self.yaml.dump(data, stream)
        return stream.getvalue()
