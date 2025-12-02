"""Location models for contextgit.

This module defines location types for identifying content within files:
- HeadingLocation: identifies content by heading path (e.g., ["Section", "Subsection"])
- LineLocation: identifies content by line range (start, end)
"""

from dataclasses import dataclass, field
from typing import Literal


@dataclass
class HeadingLocation:
    """Location identified by heading path."""

    kind: Literal["heading"] = "heading"
    path: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {'kind': 'heading', 'path': self.path}

    @classmethod
    def from_dict(cls, data: dict) -> 'HeadingLocation':
        return cls(path=data['path'])


@dataclass
class LineLocation:
    """Location identified by line range."""

    kind: Literal["lines"] = "lines"
    start: int = 1
    end: int = 1

    def __post_init__(self):
        if self.start < 1 or self.end < 1:
            raise ValueError("Line numbers must be >= 1")
        if self.start > self.end:
            raise ValueError(f"Invalid range: {self.start}-{self.end}")

    def to_dict(self) -> dict:
        return {'kind': 'lines', 'start': self.start, 'end': self.end}

    @classmethod
    def from_dict(cls, data: dict) -> 'LineLocation':
        return cls(start=data['start'], end=data['end'])


# Union type for all location types
Location = HeadingLocation | LineLocation


def location_from_dict(data: dict) -> Location:
    """Factory function to create Location from dictionary.

    Args:
        data: Dictionary with 'kind' key and location-specific fields

    Returns:
        HeadingLocation or LineLocation instance

    Raises:
        ValueError: If kind is unknown
    """
    if data['kind'] == 'heading':
        return HeadingLocation.from_dict(data)
    elif data['kind'] == 'lines':
        return LineLocation.from_dict(data)
    else:
        raise ValueError(f"Unknown location kind: {data['kind']}")
