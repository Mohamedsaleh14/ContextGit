---
contextgit:
  id: auto
  type: system
  title: Functional and non-functional requirements for contextgit MVP
  status: active
  upstream:
    - BR-001
  tags: [mvp, requirements, specifications]
---

# System Requirements

## Overview

This document specifies the functional and non-functional requirements for the `contextgit` MVP. Requirements are numbered for easy reference and use "shall" language to indicate mandatory capabilities.

## Functional Requirements

### FR-1: Project Initialization

**FR-1.1**: The system shall provide a `contextgit init` command that initializes a repository for contextgit usage.

**FR-1.2**: The initialization command shall create a `.contextgit/config.yaml` file with default configuration if it doesn't exist.

**FR-1.3**: The initialization command shall create an empty `.contextgit/requirements_index.yaml` file if it doesn't exist.

**FR-1.4**: The configuration file shall include default tag prefixes for at least the following node types:
- business_requirement (default: "BR-")
- system_requirement (default: "SR-")
- software_requirement (default: "AR-")
- code_item (default: "C-")
- test_item (default: "T-")
- decision (default: "ADR-")

**FR-1.5**: The initialization command shall not overwrite existing `.contextgit/` files unless explicitly forced by a `--force` flag.

**FR-1.6**: The initialization command shall complete in under 1 second on typical hardware.

---

### FR-2: Metadata Format Support

**FR-2.1**: The system shall support contextgit metadata embedded in Markdown files via YAML frontmatter at the beginning of the file.

**FR-2.2**: The system shall support contextgit metadata embedded in Markdown files via inline HTML comment blocks with YAML content:
```markdown
<!-- contextgit
id: SR-010
type: system
title: "Example title"
upstream: [BR-001]
downstream: []
-->
```

**FR-2.3**: The metadata block shall support the following required fields:
- `id`: unique string identifier
- `type`: node type (business, system, architecture, code, test, decision, other)
- `title`: short string describing the requirement

**FR-2.4**: The metadata block shall support the following optional fields:
- `upstream`: list of node IDs that this node refines or depends on
- `downstream`: list of node IDs that implement or extend this node
- `status`: one of (draft, active, deprecated, superseded)
- `tags`: list of arbitrary string tags
- `llm_generated`: boolean indicating if this was created by an LLM

**FR-2.5**: The system shall support the special placeholder `id: auto` to indicate that the ID should be auto-assigned during scanning.

**FR-2.6**: If no `status` field is provided, the system shall default to `active`.

---

### FR-3: File Scanning and Index Update

**FR-3.1**: The system shall provide a `contextgit scan` command that accepts a file path or directory path.

**FR-3.2**: When given a directory path with `--recursive` flag, the system shall scan all Markdown files (*.md, *.markdown) in that directory and subdirectories.

**FR-3.3**: The scan command shall parse all contextgit metadata blocks found in the scanned files.

**FR-3.4**: For each metadata block found, the system shall create or update a corresponding node in `.contextgit/requirements_index.yaml`.

**FR-3.5**: For each node, the system shall calculate a checksum of the text content in the section containing the metadata block.

**FR-3.6**: The checksum shall be based on the normalized text content (ignoring leading/trailing whitespace and normalizing line endings).

**FR-3.7**: The system shall record the file path (relative to repository root) and location (heading path or line range) for each node.

**FR-3.8**: The scan command shall create or update links based on the `upstream` and `downstream` fields in metadata blocks.

**FR-3.9**: When a node's checksum changes from the last scan, the system shall mark all links involving that node with appropriate sync status:
- If the node is upstream in a link: set `sync_status: upstream_changed`
- If the node is downstream in a link: set `sync_status: downstream_changed`

**FR-3.10**: The scan command shall support `--dry-run` flag that reports what would change without modifying the index file.

**FR-3.11**: The scan command shall support `--format json` to output a machine-readable summary of changes.

**FR-3.12**: The scan command shall detect and warn about duplicate node IDs across different files.

**FR-3.13**: The scan command shall detect and auto-assign IDs for any metadata blocks with `id: auto`.

**FR-3.14**: The scan command shall be idempotent: scanning the same files multiple times without changes shall produce the same index.

**FR-3.15**: The scan command shall update the `last_updated` timestamp for each modified node to the current ISO 8601 UTC time.

---

### FR-4: Index File Structure

**FR-4.1**: The index file shall be located at `.contextgit/requirements_index.yaml` relative to the repository root.

**FR-4.2**: The index file shall be valid YAML that can be parsed by standard YAML libraries.

**FR-4.3**: The index file shall have two top-level keys: `nodes` and `links`.

**FR-4.4**: Each node entry shall include:
- `id`: string
- `type`: string (enum)
- `title`: string
- `file`: string (relative path)
- `location`: object with `kind` and location details
- `status`: string (enum)
- `last_updated`: ISO 8601 timestamp string
- `checksum`: string

**FR-4.5**: Each node entry may optionally include:
- `llm_generated`: boolean
- `tags`: list of strings

**FR-4.6**: Each link entry shall include:
- `from`: string (node ID)
- `to`: string (node ID)
- `relation_type`: string (refines, implements, tests, derived_from, depends_on)
- `sync_status`: string (ok, upstream_changed, downstream_changed, broken)
- `last_checked`: ISO 8601 timestamp string

**FR-4.7**: The system shall maintain location information in one of two formats:
- Heading path: `{ kind: "heading", path: ["Section", "Subsection"] }`
- Line range: `{ kind: "lines", start: 10, end: 25 }`

---

### FR-5: Status and Health Reporting

**FR-5.1**: The system shall provide a `contextgit status` command that displays project health information.

**FR-5.2**: The status command shall report the total number of nodes, grouped by type.

**FR-5.3**: The status command shall report the total number of links.

**FR-5.4**: The status command shall report the count of stale links (sync_status is not "ok").

**FR-5.5**: The status command shall report the count of broken links (referenced nodes don't exist).

**FR-5.6**: The status command shall identify orphan nodes:
- Nodes with no upstream links (except for top-level business requirements)
- Nodes with no downstream links (except for leaf-level code or test nodes)

**FR-5.7**: The status command shall support `--orphans` flag to list only orphan nodes.

**FR-5.8**: The status command shall support `--stale` flag to list only stale or broken links.

**FR-5.9**: The status command shall support `--file <path>` flag to filter results to a specific file.

**FR-5.10**: The status command shall support `--type <type>` flag to filter results to a specific node type.

**FR-5.11**: The status command shall support `--format json` for machine-readable output.

---

### FR-6: Node Details Display

**FR-6.1**: The system shall provide a `contextgit show <ID>` command that displays detailed information about a specific node.

**FR-6.2**: The show command shall display all node metadata fields.

**FR-6.3**: The show command shall list all upstream links (nodes that this node refines or depends on).

**FR-6.4**: The show command shall list all downstream links (nodes that implement or extend this node).

**FR-6.5**: For each link, the show command shall display the relation type and sync status.

**FR-6.6**: The show command shall support `--format json` for machine-readable output.

**FR-6.7**: The show command shall support `--graph` flag to display a simple text-based adjacency representation of the node and its immediate neighbors.

---

### FR-7: Context Extraction

**FR-7.1**: The system shall provide a `contextgit extract <ID>` command that outputs the text content associated with a specific node.

**FR-7.2**: The extract command shall use the stored `location` information to identify the relevant text snippet in the source file.

**FR-7.3**: For heading-based locations, the system shall extract from the heading line through the content until the next heading of the same or higher level.

**FR-7.4**: For line-based locations, the system shall extract the exact line range specified.

**FR-7.5**: The extract command shall output the snippet to stdout in plain text by default.

**FR-7.6**: The extract command shall support `--format json` to output structured data including:
- `id`: node ID
- `file`: source file path
- `location`: location object
- `snippet`: extracted text content

**FR-7.7**: The extract command shall complete in under 100ms for typical files.

---

### FR-8: Manual Link Management

**FR-8.1**: The system shall provide a `contextgit link <FROM_ID> <TO_ID>` command to manually create or update a link.

**FR-8.2**: The link command shall require a `--type <relation_type>` flag specifying the relation type.

**FR-8.3**: Supported relation types shall include: refines, implements, tests, derived_from, depends_on.

**FR-8.4**: The link command shall create a new link if one doesn't exist between the two nodes.

**FR-8.5**: The link command shall update the relation type if a link already exists.

**FR-8.6**: The link command shall set `sync_status: ok` and `last_checked` to the current time when creating or updating a link.

**FR-8.7**: The link command shall validate that both node IDs exist in the index and report an error if not.

---

### FR-9: Synchronization Confirmation

**FR-9.1**: The system shall provide a `contextgit confirm <ID>` command to mark a node as synchronized with its upstream dependencies.

**FR-9.2**: The confirm command shall set `sync_status: ok` for all links where the specified ID is the downstream node.

**FR-9.3**: The confirm command shall update `last_checked` timestamp for all affected links.

**FR-9.4**: The confirm command shall update the stored checksum for the specified node to the current checksum from the file.

**FR-9.5**: The confirm command shall report how many links were updated.

---

### FR-10: ID Generation

**FR-10.1**: The system shall provide a `contextgit next-id <type>` command that generates the next available ID for a given node type.

**FR-10.2**: The next-id command shall look up the prefix for the given type from `.contextgit/config.yaml`.

**FR-10.3**: The next-id command shall scan all existing node IDs in the index that match the prefix.

**FR-10.4**: The next-id command shall return the prefix followed by the next sequential number (e.g., "SR-012" if "SR-011" exists).

**FR-10.5**: The next-id command shall zero-pad the numeric portion to at least 3 digits (e.g., "SR-001" not "SR-1").

**FR-10.6**: The next-id command shall output just the ID string to stdout by default.

**FR-10.7**: The next-id command shall support `--format json` to output `{"type": "system", "id": "SR-012"}`.

---

### FR-11: File-Based Relevance Query

**FR-11.1**: The system shall provide a `contextgit relevant-for-file <path>` command that finds nodes related to a specific source file.

**FR-11.2**: The command shall return nodes that have their `file` field matching the given path.

**FR-11.3**: The command shall return nodes that are directly upstream from any nodes in the given file (following links up to 3 levels).

**FR-11.4**: The command shall support `--depth <N>` flag to control how many link levels to traverse (default: 3).

**FR-11.5**: The command shall support `--format json` to output a structured list of relevant nodes with their metadata.

**FR-11.6**: The command shall deduplicate results (each node ID appears only once).

---

### FR-12: Index Formatting

**FR-12.1**: The system shall provide a `contextgit fmt` command that normalizes the index file format.

**FR-12.2**: The fmt command shall sort nodes alphabetically by ID.

**FR-12.3**: The fmt command shall sort links alphabetically by (`from`, `to`) tuple.

**FR-12.4**: The fmt command shall use deterministic YAML formatting:
- 2-space indentation
- Consistent key ordering within objects
- Flow style for short lists, block style for long lists

**FR-12.5**: The fmt command shall preserve all data without loss.

**FR-12.6**: The fmt command shall be idempotent: running twice shall produce identical output.

**FR-12.7**: The fmt command shall report how many nodes and links were formatted.

---

### FR-13: Error Handling

**FR-13.1**: All commands shall exit with status code 0 on success.

**FR-13.2**: All commands shall exit with non-zero status code on error.

**FR-13.3**: Error messages shall be written to stderr.

**FR-13.4**: Error messages shall be clear and actionable, indicating what went wrong and how to fix it.

**FR-13.5**: The system shall validate the index file format on load and report specific YAML parsing errors if invalid.

**FR-13.6**: The system shall detect and report missing required fields in metadata blocks with file and line number.

**FR-13.7**: The system shall detect and report file-not-found errors with the specific path.

---

## Non-Functional Requirements

### NFR-1: Performance

**NFR-1.1**: The system shall handle projects with up to 5,000 nodes and 10,000 links without noticeable performance degradation.

**NFR-1.2**: The `contextgit scan` command shall process up to 1,000 files in under 5 seconds on typical hardware (quad-core, SSD).

**NFR-1.3**: The `contextgit extract` command shall complete in under 100ms for files up to 10,000 lines.

**NFR-1.4**: The `contextgit show` and `contextgit status` commands shall complete in under 500ms for typical project sizes.

**NFR-1.5**: The system shall use O(N log N) or better algorithms for sorting and indexing operations.

**NFR-1.6**: The system shall load the index file only once per command invocation and cache it in memory.

---

### NFR-2: Reliability

**NFR-2.1**: The system shall never corrupt the index file. All writes shall use atomic file operations (write to temp file, then rename).

**NFR-2.2**: If an error occurs during scanning or updating, the system shall leave the index file in its previous valid state.

**NFR-2.3**: The system shall validate the index file structure before writing and refuse to write invalid YAML.

**NFR-2.4**: The system shall handle missing or moved files gracefully, marking affected links as broken rather than crashing.

**NFR-2.5**: The system shall handle malformed metadata blocks gracefully, logging warnings but continuing to process other valid blocks.

---

### NFR-3: Usability

**NFR-3.1**: All commands shall provide helpful usage information when invoked with `--help`.

**NFR-3.2**: Error messages shall be human-readable and suggest corrective actions where possible.

**NFR-3.3**: The system shall provide clear progress indication for long-running operations (scanning many files).

**NFR-3.4**: The system shall use consistent terminology across all commands and documentation.

**NFR-3.5**: The system shall follow standard Unix conventions for exit codes, stdout/stderr, and flag syntax.

---

### NFR-4: Git-Friendliness

**NFR-4.1**: The index file shall be human-readable YAML suitable for code review.

**NFR-4.2**: The index file shall use deterministic ordering (sorted by ID) to minimize git diff noise.

**NFR-4.3**: The index file shall use consistent formatting (indentation, line breaks) across all operations.

**NFR-4.4**: The system shall not store absolute file paths; all paths shall be relative to the repository root.

**NFR-4.5**: The system shall not include machine-specific or user-specific information in any stored files.

---

### NFR-5: Platform Support

**NFR-5.1**: The system shall run on Linux (Ubuntu 20.04+, Debian 11+, Fedora 35+).

**NFR-5.2**: The system should also run on macOS 11+ and Windows 10+ with Python 3.11+, but this is not the primary target.

**NFR-5.3**: The system shall work with Python 3.11, 3.12, and 3.13.

**NFR-5.4**: The system shall use only cross-platform Python libraries in the standard library or widely available via pip.

**NFR-5.5**: The system shall use UTF-8 encoding for all file I/O.

---

### NFR-6: Packaging and Distribution

**NFR-6.1**: The system shall be installable via `pip install contextgit`.

**NFR-6.2**: The package shall include all dependencies in `requirements.txt` or `pyproject.toml`.

**NFR-6.3**: The package shall provide a `contextgit` command-line entry point after installation.

**NFR-6.4**: The system shall have minimal dependencies (prefer standard library where possible).

**NFR-6.5**: Total installed size shall be under 5 MB (excluding Python runtime).

---

### NFR-7: LLM Integration

**NFR-7.1**: All read-oriented commands shall support `--format json` output for programmatic consumption by LLM tools.

**NFR-7.2**: JSON output shall be valid, well-structured, and consistent across commands.

**NFR-7.3**: The system shall be detectable by LLM tools via the presence of `.contextgit/config.yaml` in the repository root.

**NFR-7.4**: The system shall complete common LLM-invoked commands (next-id, extract, relevant-for-file) in under 200ms to avoid slowing LLM workflows.

**NFR-7.5**: The system shall be invocable from any directory within the repository (auto-detect repo root by looking for `.contextgit/` or `.git/`).

---

### NFR-8: Open Source Readiness

**NFR-8.1**: The project shall include a LICENSE file (MIT or Apache 2.0 recommended).

**NFR-8.2**: The project shall include a comprehensive README.md with:
- Installation instructions
- Quick start guide
- Core concepts explanation
- Example workflow

**NFR-8.3**: The project shall include an example project demonstrating contextgit usage.

**NFR-8.4**: The project shall include contributing guidelines (CONTRIBUTING.md).

**NFR-8.5**: The code shall follow PEP 8 Python style guidelines.

**NFR-8.6**: The code shall include docstrings for all public functions and classes.

---

## Constraints

### C-1: Local-First Architecture

**C-1.1**: The system shall not require network connectivity to function.

**C-1.2**: The system shall not transmit any data to external services.

**C-1.3**: All data shall be stored locally in the repository.

---

### C-2: Text-Based Storage

**C-2.1**: All persistent state shall be stored in human-readable text formats (YAML, Markdown).

**C-2.2**: The system shall not use binary databases (SQLite, etc.) for MVP.

**C-2.3**: The system shall not require external database services.

---

### C-3: Single-User Focus (MVP)

**C-3.1**: The MVP shall not handle concurrent access or file locking (rely on git for merge conflict resolution).

**C-3.2**: The MVP shall not include user authentication or authorization.

**C-3.3**: The MVP shall assume a trusted local development environment.

---

### C-4: Markdown-Only Support (MVP)

**C-4.1**: The MVP shall only parse Markdown files (*.md, *.markdown).

**C-4.2**: The MVP shall not parse source code files (Python, JavaScript, etc.) for embedded metadata.

**C-4.3**: Support for additional file formats is explicitly deferred to future versions.

---

## Acceptance Criteria

The MVP shall be considered complete when:

1. All functional requirements (FR-1 through FR-13) are implemented and tested.
2. All non-functional requirements (NFR-1 through NFR-8) are met.
3. All constraints (C-1 through C-4) are satisfied.
4. The system passes end-to-end testing with the user stories in `02_user_stories.md`.
5. Documentation is complete and reviewed.
6. An example project demonstrating the workflow is available.
