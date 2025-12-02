"""Custom exceptions for contextgit."""


class ContextGitError(Exception):
    """Base exception for all contextgit errors."""

    exit_code = 1


class RepoNotFoundError(ContextGitError):
    """Raised when not in a contextgit repository."""

    exit_code = 1


class NodeNotFoundError(ContextGitError):
    """Raised when a node ID is not found."""

    exit_code = 3


class InvalidMetadataError(ContextGitError):
    """Raised when metadata is malformed."""

    exit_code = 4


class IndexCorruptedError(ContextGitError):
    """Raised when index file is corrupted."""

    exit_code = 5


class InvalidConfigError(ContextGitError):
    """Raised when config file is malformed."""

    exit_code = 6


class SecurityError(ContextGitError):
    """Raised for security violations (path traversal, etc.)."""

    exit_code = 7
