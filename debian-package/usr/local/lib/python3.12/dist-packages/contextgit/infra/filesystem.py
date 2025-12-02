"""File system operations abstraction for contextgit.

This module provides atomic file operations, directory walking, and repository
root detection for the contextgit system.
"""

import os
from pathlib import Path
from typing import Iterator


class FileSystem:
    """File system operations abstraction.

    Provides safe file I/O operations including:
    - UTF-8 file reading/writing
    - Atomic file writes (temp + rename)
    - Directory traversal with pattern matching
    - Repository root detection
    """

    def read_file(self, path: str) -> str:
        """Read file as UTF-8 text.

        Args:
            path: Absolute or relative path to file

        Returns:
            File contents as string

        Raises:
            FileNotFoundError: If file does not exist
            PermissionError: If file cannot be read
            UnicodeDecodeError: If file is not valid UTF-8
        """
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()

    def write_file_atomic(self, path: str, content: str) -> None:
        """Write file atomically using temp file + rename.

        This ensures that the file is never left in a partially written state.
        Uses POSIX atomic rename semantics.

        Args:
            path: Absolute or relative path to target file
            content: String content to write

        Raises:
            PermissionError: If file or directory cannot be written
            OSError: If atomic rename fails
        """
        temp_path = path + '.tmp'

        try:
            # Write to temp file
            with open(temp_path, 'w', encoding='utf-8') as f:
                f.write(content)

            # Atomic rename (POSIX)
            os.rename(temp_path, path)

        except Exception as e:
            # Clean up temp file if it exists
            if os.path.exists(temp_path):
                os.remove(temp_path)
            raise

    def walk_files(
        self, root: str, pattern: str = "*.md", recursive: bool = False
    ) -> Iterator[str]:
        """Walk directory tree and yield matching files.

        Supports both file and directory inputs. If root is a file and matches
        the pattern, yields that file. If root is a directory, walks it according
        to the recursive flag.

        Args:
            root: Starting path (file or directory)
            pattern: Glob pattern for file matching (default: "*.md")
            recursive: If True, recursively walk subdirectories

        Yields:
            Absolute paths to matching files

        Raises:
            FileNotFoundError: If root path does not exist
        """
        root_path = Path(root)

        if root_path.is_file():
            yield str(root_path)
            return

        if recursive:
            for file_path in root_path.rglob(pattern):
                if file_path.is_file():
                    yield str(file_path)
        else:
            for file_path in root_path.glob(pattern):
                if file_path.is_file():
                    yield str(file_path)

    def find_repo_root(self, start_path: str) -> str:
        """Find repository root by looking for .contextgit/ or .git/.

        Walks up the directory tree from start_path until it finds a directory
        containing .contextgit/ (primary) or .git/ (fallback).

        Args:
            start_path: Path to start searching from (file or directory)

        Returns:
            Absolute path to repository root

        Raises:
            FileNotFoundError: If no repository root is found
        """
        current = Path(start_path).resolve()

        while current != current.parent:
            if (current / '.contextgit').exists():
                return str(current)
            if (current / '.git').exists():
                return str(current)
            current = current.parent

        raise FileNotFoundError("Not in a contextgit repository")
