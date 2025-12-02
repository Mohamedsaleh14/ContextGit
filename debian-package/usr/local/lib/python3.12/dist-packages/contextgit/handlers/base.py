"""Base handler with common functionality."""

import os

from contextgit.exceptions import RepoNotFoundError
from contextgit.infra.filesystem import FileSystem
from contextgit.infra.output import OutputFormatter
from contextgit.infra.yaml_io import YAMLSerializer


class BaseHandler:
    """Base class for command handlers.

    Provides common functionality for all command handlers including:
    - Access to infrastructure services (filesystem, YAML, output)
    - Repository root detection
    - Shared utilities for path resolution

    All concrete command handlers should inherit from this base class.
    """

    def __init__(
        self,
        filesystem: FileSystem,
        yaml_io: YAMLSerializer,
        output_formatter: OutputFormatter,
    ):
        """Initialize base handler.

        Args:
            filesystem: File system abstraction
            yaml_io: YAML serialization
            output_formatter: Output formatting
        """
        self.fs = filesystem
        self.yaml = yaml_io
        self.formatter = output_formatter

    def find_repo_root(self, start_path: str | None = None) -> str:
        """Find repository root.

        Walks up the directory tree from start_path to find a directory
        containing .contextgit/ (primary marker) or .git/ (fallback marker).

        Args:
            start_path: Starting path (default: current directory)

        Returns:
            Repository root path

        Raises:
            RepoNotFoundError: If not in a repository
        """
        if start_path is None:
            start_path = os.getcwd()

        try:
            return self.fs.find_repo_root(start_path)
        except FileNotFoundError as e:
            raise RepoNotFoundError(str(e)) from e
