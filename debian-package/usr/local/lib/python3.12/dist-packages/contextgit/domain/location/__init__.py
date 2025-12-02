"""Location domain module for contextgit.

This module provides functionality for:
- Parsing Markdown structure (headings)
- Extracting text snippets based on locations
- Resolving metadata locations in files
"""

from contextgit.domain.location.markdown import Heading, MarkdownParser
from contextgit.domain.location.resolver import LocationResolver
from contextgit.domain.location.snippet import SnippetExtractor

__all__ = [
    'Heading',
    'MarkdownParser',
    'LocationResolver',
    'SnippetExtractor',
]
