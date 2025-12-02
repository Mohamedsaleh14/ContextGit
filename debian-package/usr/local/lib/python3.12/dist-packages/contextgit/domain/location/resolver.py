"""Location resolution for metadata blocks.

This module provides functionality for resolving the location of metadata blocks
within Markdown files, determining whether they should be identified by heading
path or line range.
"""

from contextgit.models.location import HeadingLocation, LineLocation, Location
from contextgit.infra.filesystem import FileSystem
from contextgit.domain.location.markdown import MarkdownParser, Heading


class LocationResolver:
    """Resolves metadata block locations in Markdown files.

    The LocationResolver determines the appropriate Location object for a metadata
    block by analyzing the Markdown structure. If a heading follows the metadata,
    it creates a HeadingLocation with the full heading path. Otherwise, it creates
    a LineLocation with the line range.
    """

    def __init__(self, filesystem: FileSystem):
        """
        Initialize LocationResolver.

        Args:
            filesystem: File system abstraction for reading files
        """
        self.fs = filesystem
        self.md_parser = MarkdownParser()

    def resolve_location(self, file_path: str, metadata_line: int) -> Location:
        """
        Resolve location for a metadata block.

        Finds the heading immediately after the metadata block
        and builds the full heading path.

        Args:
            file_path: Path to the Markdown file
            metadata_line: Line number where metadata block starts (1-indexed)

        Returns:
            Location object (HeadingLocation or LineLocation)

        Raises:
            FileNotFoundError: If file doesn't exist
        """
        content = self.fs.read_file(file_path)
        headings = self.md_parser.parse_headings(content)

        # Find the heading immediately after the metadata block
        next_heading = None
        for heading in headings:
            if heading.line_number > metadata_line:
                next_heading = heading
                break

        if next_heading is None:
            # No heading after metadata, use line-based location
            lines = content.split('\n')
            return LineLocation(start=metadata_line, end=len(lines))

        # Build heading path
        path = self._build_heading_path(headings, next_heading)
        return HeadingLocation(path=path)

    def _build_heading_path(self, all_headings: list[Heading], target: Heading) -> list[str]:
        """Build the full heading path for a target heading.

        Constructs the hierarchical path by walking backwards through the headings
        to find all parent headings (headings with lower level numbers that appear
        before the target).

        Args:
            all_headings: All headings in the document
            target: The target heading to build path for

        Returns:
            List of heading texts from root to target
            Example: ["Introduction", "Getting Started", "Installation"]

        Examples:
            >>> # Document structure:
            >>> # # Chapter 1
            >>> # ## Section A
            >>> # ### Subsection
            >>> # Returns: ["Chapter 1", "Section A", "Subsection"]
        """
        path = []
        current_level = target.level

        # Add target heading
        path.append(target.text)

        # Walk backwards to find parent headings
        for heading in reversed(all_headings):
            if heading.line_number >= target.line_number:
                continue

            if heading.level < current_level:
                path.insert(0, heading.text)
                current_level = heading.level

            if current_level == 1:
                break

        return path
