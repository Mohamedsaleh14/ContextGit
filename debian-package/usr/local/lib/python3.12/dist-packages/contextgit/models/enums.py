"""Enumerations for contextgit data models.

This module defines the core enumerations used throughout the contextgit system:
- NodeType: Types of requirement/context nodes
- NodeStatus: Lifecycle status of nodes
- RelationType: Types of traceability relationships between nodes
- SyncStatus: Synchronization status of linked nodes
"""

from enum import Enum


class NodeType(Enum):
    """Node type enumeration.

    Defines the types of requirements and context items that can be tracked:
    - BUSINESS: Business requirements and user needs
    - SYSTEM: System-level specifications
    - ARCHITECTURE: Architectural decisions and designs
    - CODE: Implementation artifacts
    - TEST: Test cases and scenarios
    - DECISION: Architecture decision records
    - OTHER: Miscellaneous context items
    """

    BUSINESS = "business"
    SYSTEM = "system"
    ARCHITECTURE = "architecture"
    CODE = "code"
    TEST = "test"
    DECISION = "decision"
    OTHER = "other"


class NodeStatus(Enum):
    """Node status enumeration.

    Defines the lifecycle status of a node:
    - DRAFT: Work in progress, not yet finalized
    - ACTIVE: Current and valid
    - DEPRECATED: No longer recommended but still valid
    - SUPERSEDED: Replaced by another node
    """

    DRAFT = "draft"
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    SUPERSEDED = "superseded"


class RelationType(Enum):
    """Relation type enumeration.

    Defines the types of traceability relationships between nodes:
    - REFINES: Target provides more detail about source
    - IMPLEMENTS: Target implements the requirements in source
    - TESTS: Target tests the functionality in source
    - DERIVED_FROM: Target is derived from source
    - DEPENDS_ON: Target depends on source
    """

    REFINES = "refines"
    IMPLEMENTS = "implements"
    TESTS = "tests"
    DERIVED_FROM = "derived_from"
    DEPENDS_ON = "depends_on"


class SyncStatus(Enum):
    """Sync status enumeration.

    Defines the synchronization status of linked nodes:
    - OK: Source and target are in sync
    - UPSTREAM_CHANGED: Source node has changed since link was created
    - DOWNSTREAM_CHANGED: Target node has changed since link was created
    - BROKEN: Link is broken (referenced node no longer exists)
    """

    OK = "ok"
    UPSTREAM_CHANGED = "upstream_changed"
    DOWNSTREAM_CHANGED = "downstream_changed"
    BROKEN = "broken"
