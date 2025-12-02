"""Markdown structure parser for contextgit.

This module provides parsing of Markdown structure, specifically for identifying
headings and their hierarchical relationships within documents.
"""

from dataclasses import dataclass


@dataclass
class Heading:
    """Represents a Markdown heading.

    Attributes:
        level: Heading level (1-6, where 1 is # and 6 is ######)
        text: The heading text content (without the # markers)
        line_number: Line number in the file (1-indexed)
    """
    level: int  # 1-6 (# = 1, ## = 2, etc.)
    text: str
    line_number: int


class MarkdownParser:
    """Parses Markdown structure to identify headings.

    This parser identifies ATX-style headings (# Heading) in Markdown files.
    Setext-style headings (underlined with = or -) are not supported in the MVP.
    """

    def parse_headings(self, content: str) -> list[Heading]:
        """Parse all headings in Markdown content.

        Identifies ATX-style headings (lines starting with 1-6 # characters).

        Args:
            content: The Markdown file content

        Returns:
            List of Heading objects in document order

        Examples:
            >>> parser = MarkdownParser()
            >>> content = "# Title\\n## Section\\nText\\n### Subsection"
            >>> headings = parser.parse_headings(content)
            >>> len(headings)
            3
            >>> headings[0].level
            1
            >>> headings[0].text
            'Title'
        """
        headings = []
        lines = content.split('\n')

        for i, line in enumerate(lines, start=1):
            # Check for ATX-style headings (# Heading)
            if line.startswith('#'):
                # Count leading #
                level = 0
                for char in line:
                    if char == '#':
                        level += 1
                    else:
                        break

                # Valid heading levels are 1-6
                if level > 0 and level <= 6:
                    text = line[level:].strip()
                    headings.append(Heading(level=level, text=text, line_number=i))

        return headings
