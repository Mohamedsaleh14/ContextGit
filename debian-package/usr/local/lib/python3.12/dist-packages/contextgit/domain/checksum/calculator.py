"""Checksum calculation for content change detection."""

import hashlib


class ChecksumCalculator:
    """Calculates and compares content checksums."""

    def calculate_checksum(self, text: str) -> str:
        """
        Calculate SHA-256 checksum of normalized text.

        Normalization:
        - Convert line endings to \n
        - Strip whitespace from each line
        - Remove empty lines at start/end

        Args:
            text: Input text

        Returns:
            Hex digest (64 characters)
        """
        normalized = self._normalize_text(text)
        hash_obj = hashlib.sha256(normalized.encode('utf-8'))
        return hash_obj.hexdigest()

    def compare_checksums(self, old: str, new: str) -> bool:
        """
        Compare two checksums.

        Args:
            old: First checksum
            new: Second checksum

        Returns:
            True if identical, False otherwise
        """
        return old == new

    def _normalize_text(self, text: str) -> str:
        """
        Normalize text for consistent checksumming.

        - Convert line endings to \n
        - Strip leading/trailing whitespace from each line
        - Remove empty lines at start/end
        """
        # Convert line endings
        text = text.replace('\r\n', '\n').replace('\r', '\n')

        # Strip each line
        lines = text.split('\n')
        stripped_lines = [line.strip() for line in lines]

        # Remove empty lines at start/end
        while stripped_lines and not stripped_lines[0]:
            stripped_lines.pop(0)
        while stripped_lines and not stripped_lines[-1]:
            stripped_lines.pop()

        return '\n'.join(stripped_lines)
