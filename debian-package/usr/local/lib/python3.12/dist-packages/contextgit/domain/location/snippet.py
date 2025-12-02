"""Snippet extraction from files.

This module provides functionality to extract text snippets from files based on
location specifications (heading paths or line ranges).
"""

from contextgit.models.location import HeadingLocation, LineLocation, Location
from contextgit.infra.filesystem import FileSystem
from contextgit.domain.location.markdown import MarkdownParser, Heading


class SnippetExtractor:
    """Extracts text snippets from files based on locations.

    This class supports two types of locations:
    - HeadingLocation: Extracts content from a heading to the next same-level heading
    - LineLocation: Extracts exact line ranges

    The extractor is designed to meet the performance target of < 100ms for
    extraction operations (FR-7.7 requirement).
    """

    def __init__(self, filesystem: FileSystem):
        """Initialize SnippetExtractor.

        Args:
            filesystem: File system abstraction for reading files
        """
        self.fs = filesystem
        self.md_parser = MarkdownParser()

    def extract_snippet(self, file_path: str, location: Location) -> str:
        """Extract text snippet from file based on location.

        For HeadingLocation: extracts from heading to next same-level heading
        For LineLocation: extracts exact line range

        Args:
            file_path: Path to the file
            location: Location specification (HeadingLocation or LineLocation)

        Returns:
            Extracted text content

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If heading not found or line range invalid

        Examples:
            >>> fs = FileSystem()
            >>> extractor = SnippetExtractor(fs)
            >>> loc = LineLocation(start=5, end=10)
            >>> snippet = extractor.extract_snippet("doc.md", loc)
        """
        content = self.fs.read_file(file_path)

        if isinstance(location, LineLocation):
            return self._extract_by_lines(content, location)
        elif isinstance(location, HeadingLocation):
            return self._extract_by_heading(content, location)
        else:
            raise ValueError(f"Unknown location type: {type(location)}")

    def _extract_by_lines(self, content: str, location: LineLocation) -> str:
        """Extract snippet by line range.

        Args:
            content: File content
            location: Line-based location specification

        Returns:
            Text from the specified line range

        Note:
            Line numbers are 1-indexed. The range is inclusive of start,
            exclusive of end (Python slice semantics).
        """
        lines = content.split('\n')
        # Line numbers are 1-indexed
        start_idx = location.start - 1
        end_idx = location.end
        return '\n'.join(lines[start_idx:end_idx])

    def _extract_by_heading(self, content: str, location: HeadingLocation) -> str:
        """Extract snippet by heading path.

        Finds the heading matching the path and extracts content from that
        heading to the next heading of the same or higher level.

        Args:
            content: File content
            location: Heading-based location specification

        Returns:
            Text from the heading to the next same-level heading

        Raises:
            ValueError: If heading path is not found
        """
        headings = self.md_parser.parse_headings(content)

        # Find the target heading
        target_heading = self._find_heading_by_path(headings, location.path)
        if not target_heading:
            raise ValueError(f"Heading not found: {location.path}")

        # Find the next same-level or higher-level heading
        end_line = None
        for heading in headings:
            if heading.line_number > target_heading.line_number:
                if heading.level <= target_heading.level:
                    end_line = heading.line_number - 1
                    break

        # Extract from target heading to end
        lines = content.split('\n')
        start_idx = target_heading.line_number - 1

        if end_line:
            end_idx = end_line
        else:
            end_idx = len(lines)

        return '\n'.join(lines[start_idx:end_idx])

    def _find_heading_by_path(
        self, headings: list[Heading], path: list[str]
    ) -> Heading | None:
        """Find a heading by its full path.

        Args:
            headings: List of all headings in the document
            path: Hierarchical path to the target heading

        Returns:
            The Heading object if found, None otherwise

        Example:
            For a document with structure:
                # Chapter
                ## Section
                ### Subsection

            Path ["Chapter", "Section", "Subsection"] would match the ### heading.
        """
        if not path:
            return None

        # Build heading paths for all headings
        for i, heading in enumerate(headings):
            heading_path = self._build_path_for_heading(headings[:i+1], heading)
            if heading_path == path:
                return heading

        return None

    def _build_path_for_heading(
        self, preceding_headings: list[Heading], target: Heading
    ) -> list[str]:
        """Build path for a heading based on preceding headings.

        Constructs the full hierarchical path by walking backwards through
        preceding headings to find all ancestors.

        Args:
            preceding_headings: All headings up to and including the target
            target: The heading to build the path for

        Returns:
            List of heading texts from top-level to target

        Example:
            For headings:
                # Chapter (level 1)
                ## Section (level 2)
                ### Subsection (level 3)

            Building path for "Subsection" returns:
                ["Chapter", "Section", "Subsection"]
        """
        path = []
        current_level = target.level

        # Add target
        path.append(target.text)

        # Walk backwards through preceding headings
        for heading in reversed(preceding_headings[:-1]):
            if heading.level < current_level:
                path.insert(0, heading.text)
                current_level = heading.level

        return path
