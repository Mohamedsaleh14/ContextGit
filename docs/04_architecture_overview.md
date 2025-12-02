---
contextgit:
  id: auto
  type: architecture
  title: High-level architecture and design for contextgit
  status: active
  upstream:
    - SR-001
  tags: [mvp, architecture, design]
---

# Architecture Overview

## Introduction

This document describes the high-level architecture of `contextgit`, a CLI tool for managing requirements and context traceability in LLM-assisted software projects. The architecture follows a layered design with clear separation of concerns.

## Design Principles

1. **Local-first**: All operations happen on the local filesystem; no network dependencies.
2. **Text-based**: All persistent state is stored in human-readable YAML and Markdown.
3. **Git-friendly**: Deterministic output and clean diffs for version control.
4. **Fast feedback**: Most commands complete in under 500ms.
5. **LLM-optimized**: Designed for consumption by Claude Code and similar tools.
6. **Fail-safe**: Never corrupt the index; use atomic operations.

## System Context

```
┌─────────────────────────────────────────────────────────────┐
│                    Developer Environment                     │
│                                                              │
│  ┌─────────────┐                                            │
│  │   Human     │                                            │
│  │  Developer  │───────┐                                    │
│  └─────────────┘       │                                    │
│                        │                                    │
│  ┌─────────────┐       │      ┌──────────────┐             │
│  │ Claude Code │       ├─────▶│   contextgit    │             │
│  │  (or other  │       │      │   CLI Tool   │             │
│  │  LLM CLI)   │───────┘      └──────┬───────┘             │
│  └─────────────┘                     │                      │
│                                      │                      │
│                            ┌─────────▼─────────┐            │
│                            │   Repository      │            │
│                            │   ├── .contextgit/   │            │
│                            │   ├── docs/       │            │
│                            │   └── src/        │            │
│                            └───────────────────┘            │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

Both humans and LLM CLIs invoke `contextgit` commands. The tool reads and writes to the local git repository, manipulating `.contextgit/` state files and scanning `docs/` for requirement metadata.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        CLI Layer (Typer/Click)                   │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐          │
│  │  init    │ │  scan    │ │  show    │ │ extract  │ ...      │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘          │
└───────┼────────────┼────────────┼────────────┼─────────────────┘
        │            │            │            │
        │            │            │            │
┌───────▼────────────▼────────────▼────────────▼─────────────────┐
│                    Application Layer                            │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              Command Handlers / Controllers             │   │
│  │   - InitHandler                                         │   │
│  │   - ScanHandler                                         │   │
│  │   - StatusHandler                                       │   │
│  │   - ShowHandler                                         │   │
│  │   - ExtractHandler                                      │   │
│  │   - LinkHandler                                         │   │
│  │   - ConfirmHandler                                      │   │
│  │   - NextIdHandler                                       │   │
│  │   - RelevanceHandler                                    │   │
│  │   - FormatHandler                                       │   │
│  └────────────────────┬────────────────────────────────────┘   │
└─────────────────────────┼──────────────────────────────────────┘
                          │
                          │
┌─────────────────────────▼──────────────────────────────────────┐
│                       Core Domain Layer                         │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Index Manager                                          │   │
│  │    - Load/save index YAML                              │   │
│  │    - Atomic writes (temp + rename)                     │   │
│  │    - Node CRUD operations                              │   │
│  │    - Link CRUD operations                              │   │
│  │    - Checksum management                               │   │
│  │    - Validation                                        │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Metadata Parser                                        │   │
│  │    - Parse YAML frontmatter                            │   │
│  │    - Parse inline HTML comment blocks                  │   │
│  │    - Extract node metadata                             │   │
│  │    - Normalize and validate fields                     │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Location Resolver & Snippet Extractor                 │   │
│  │    - Parse Markdown structure (headings)               │   │
│  │    - Map heading paths to line ranges                  │   │
│  │    - Extract snippets by location                      │   │
│  │    - Handle line-based locations                       │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Linking Engine                                         │   │
│  │    - Build link graph from upstream/downstream         │   │
│  │    - Detect checksum changes                           │   │
│  │    - Update sync status                                │   │
│  │    - Traverse graph (upstream/downstream queries)      │   │
│  │    - Detect circular dependencies                      │   │
│  │    - Identify orphans                                  │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Checksum Calculator                                    │   │
│  │    - Normalize text (whitespace, line endings)         │   │
│  │    - Compute SHA-256 hash                              │   │
│  │    - Compare checksums for drift detection             │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  ID Generator                                           │   │
│  │    - Read config for prefixes                          │   │
│  │    - Scan existing IDs                                 │   │
│  │    - Generate next sequential ID                       │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Config Manager                                         │   │
│  │    - Load/save .contextgit/config.yaml                    │   │
│  │    - Provide defaults                                  │   │
│  │    - Validate config structure                         │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                          │
                          │
┌─────────────────────────▼──────────────────────────────────────┐
│                    Infrastructure Layer                         │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  File System Access                                     │   │
│  │    - Read files (UTF-8)                                │   │
│  │    - Write files atomically                            │   │
│  │    - Walk directory trees                              │   │
│  │    - Detect repository root (.git, .contextgit)           │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  YAML Serialization                                     │   │
│  │    - Parse YAML safely                                 │   │
│  │    - Dump YAML deterministically                       │   │
│  │    - Sort keys and lists for git-friendliness          │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Output Formatter                                       │   │
│  │    - Format output for terminal (colors, tables)       │   │
│  │    - Format output as JSON                             │   │
│  │    - Handle --format flag                              │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

## Component Descriptions

### CLI Layer

**Purpose**: Parse command-line arguments and route to appropriate handlers.

**Technology**: Typer (recommended) or Click for argument parsing and help text.

**Responsibilities**:
- Define all CLI commands and their arguments
- Parse flags (--format, --recursive, --dry-run, etc.)
- Provide --help documentation
- Handle top-level exceptions and format error messages
- Set exit codes

**Key Commands**:
- `contextgit init`
- `contextgit scan [PATH] [--recursive] [--dry-run] [--format json]`
- `contextgit status [--orphans] [--stale] [--file PATH] [--type TYPE] [--format json]`
- `contextgit show <ID> [--format json] [--graph]`
- `contextgit extract <ID> [--format json]`
- `contextgit link <FROM> <TO> --type <RELATION>`
- `contextgit confirm <ID>`
- `contextgit next-id <TYPE> [--format json]`
- `contextgit relevant-for-file <PATH> [--depth N] [--format json]`
- `contextgit fmt`

---

### Application Layer (Command Handlers)

**Purpose**: Implement business logic for each CLI command.

**Responsibilities**:
- Coordinate calls to core domain components
- Handle command-specific validation
- Format output (plain text or JSON)
- Manage transactions (read index → modify → write index)
- Report progress for long operations

**Example: ScanHandler**
1. Detect repository root
2. Load config to get directory patterns and prefixes
3. Walk directory tree to find Markdown files
4. For each file:
   - Parse metadata blocks using MetadataParser
   - Extract location using LocationResolver
   - Calculate checksum using ChecksumCalculator
5. Load index using IndexManager
6. Update/create nodes
7. Create/update links based on upstream/downstream
8. Update sync status using LinkingEngine
9. Save index atomically
10. Output summary

---

### Core Domain Layer

#### Index Manager

**Purpose**: Manage the central index file (`.contextgit/requirements_index.yaml`).

**Responsibilities**:
- Load index from disk (validate YAML structure)
- Provide CRUD operations for nodes and links
- Save index to disk atomically (write temp file, rename)
- Sort nodes and links deterministically
- Validate node and link structure

**Key Operations**:
- `load_index() -> Index`
- `save_index(index: Index) -> None`
- `get_node(id: str) -> Node | None`
- `add_node(node: Node) -> None`
- `update_node(id: str, updates: dict) -> None`
- `delete_node(id: str) -> None`
- `get_link(from_id: str, to_id: str) -> Link | None`
- `add_link(link: Link) -> None`
- `update_link(from_id: str, to_id: str, updates: dict) -> None`
- `delete_link(from_id: str, to_id: str) -> None`

**Data Structures**:
```python
@dataclass
class Node:
    id: str
    type: str  # business | system | architecture | code | test | decision | other
    title: str
    file: str  # relative path
    location: Location
    status: str  # draft | active | deprecated | superseded
    last_updated: str  # ISO 8601
    checksum: str
    llm_generated: bool = False
    tags: list[str] = field(default_factory=list)

@dataclass
class Link:
    from_id: str
    to_id: str
    relation_type: str  # refines | implements | tests | derived_from | depends_on
    sync_status: str  # ok | upstream_changed | downstream_changed | broken
    last_checked: str  # ISO 8601

@dataclass
class Index:
    nodes: dict[str, Node]  # keyed by id
    links: list[Link]
```

---

#### Metadata Parser

**Purpose**: Extract contextgit metadata from Markdown files.

**Responsibilities**:
- Parse YAML frontmatter at the beginning of files
- Parse inline HTML comment blocks (`<!-- contextgit ... -->`)
- Normalize and validate metadata fields
- Handle `id: auto` placeholder
- Report errors for malformed metadata

**Key Operations**:
- `parse_file(file_path: str) -> list[RawMetadata]`
- `parse_frontmatter(content: str) -> RawMetadata | None`
- `parse_inline_blocks(content: str) -> list[RawMetadata]`
- `validate_metadata(raw: RawMetadata) -> Metadata`

**Algorithm for Inline Blocks**:
1. Use regex to find `<!-- contextgit\n...\n-->` patterns
2. Extract YAML content between delimiters
3. Parse YAML
4. Record line number of the comment block
5. Return list of metadata objects with locations

**Algorithm for Frontmatter**:
1. Check if file starts with `---`
2. Extract content until closing `---`
3. Parse YAML
4. Check for `contextgit` key at top level
5. Return metadata if found

---

#### Location Resolver & Snippet Extractor

**Purpose**: Map metadata blocks to precise locations in files and extract text snippets.

**Responsibilities**:
- Parse Markdown structure (identify headings and their hierarchy)
- Map metadata blocks to heading paths
- Extract snippets by heading path or line range
- Handle multi-level headings (`#`, `##`, `###`, etc.)

**Key Operations**:
- `resolve_location(file_path: str, metadata_line: int) -> Location`
- `extract_snippet(file_path: str, location: Location) -> str`
- `parse_markdown_structure(content: str) -> list[Heading]`

**Location Types**:
```python
@dataclass
class HeadingLocation:
    kind: str = "heading"
    path: list[str]  # e.g., ["Requirements", "Logging", "API Endpoint"]

@dataclass
class LineLocation:
    kind: str = "lines"
    start: int
    end: int

Location = HeadingLocation | LineLocation
```

**Algorithm for Heading Path**:
1. Parse file to identify all headings and their levels
2. Find the heading immediately after the metadata block
3. Build the heading path from root to that heading
4. Return `HeadingLocation` with path

**Algorithm for Snippet Extraction (Heading)**:
1. Parse file to identify all headings
2. Find the heading matching the path
3. Extract from that heading line through all content until:
   - Next heading of same or higher level
   - End of file
4. Return extracted text

**Algorithm for Snippet Extraction (Lines)**:
1. Read file
2. Extract lines from `start` to `end` (inclusive)
3. Return extracted text

---

#### Linking Engine

**Purpose**: Build and maintain the traceability graph; detect staleness and orphans.

**Responsibilities**:
- Build link graph from node upstream/downstream declarations
- Compare checksums to detect changes
- Update link sync status based on checksum changes
- Traverse graph to find upstream/downstream nodes
- Detect circular dependencies
- Identify orphan nodes

**Key Operations**:
- `build_links_from_metadata(nodes: dict[str, Node]) -> list[Link]`
- `update_sync_status(index: Index, changed_nodes: set[str]) -> None`
- `get_upstream_nodes(node_id: str, depth: int = 1) -> list[Node]`
- `get_downstream_nodes(node_id: str, depth: int = 1) -> list[Node]`
- `detect_orphans(index: Index) -> list[str]`
- `detect_circular_dependencies(index: Index) -> list[list[str]]`

**Algorithm for Sync Status Update**:
1. For each node whose checksum changed:
   - Find all links where this node is `from_id` (outgoing)
     - Mark those links as `sync_status: downstream_changed`
   - Find all links where this node is `to_id` (incoming)
     - Mark those links as `sync_status: upstream_changed`
2. User must manually review and run `contextgit confirm` to mark as `ok`

**Algorithm for Orphan Detection**:
1. Identify top-level node types (business requirements) that don't need upstream
2. For all other nodes, flag if no incoming links (no upstream)
3. Identify leaf-level node types (code, test) that don't need downstream
4. For all other nodes, flag if no outgoing links (no downstream)

---

#### Checksum Calculator

**Purpose**: Compute and compare content checksums for change detection.

**Responsibilities**:
- Normalize text (strip leading/trailing whitespace, normalize line endings)
- Compute SHA-256 hash of normalized text
- Compare checksums to detect changes

**Key Operations**:
- `calculate_checksum(text: str) -> str`
- `compare_checksums(old: str, new: str) -> bool`

**Algorithm**:
1. Normalize text:
   - Convert all line endings to `\n`
   - Strip leading/trailing whitespace from each line
   - Remove completely empty lines at start/end
2. Encode to UTF-8 bytes
3. Compute SHA-256 hash
4. Return hex digest

---

#### ID Generator

**Purpose**: Generate unique sequential IDs for new requirements.

**Responsibilities**:
- Read config to get prefix for each node type
- Scan existing node IDs matching that prefix
- Return next sequential ID with zero-padding

**Key Operations**:
- `next_id(node_type: str, index: Index, config: Config) -> str`

**Algorithm**:
1. Load config to get prefix (e.g., "SR-" for system requirements)
2. Get all node IDs from index
3. Filter to those starting with the prefix
4. Extract numeric portion and parse as integers
5. Find max number
6. Return `prefix + str(max + 1).zfill(3)`

---

#### Config Manager

**Purpose**: Load and manage `.contextgit/config.yaml`.

**Responsibilities**:
- Load config file
- Provide defaults if file doesn't exist or fields are missing
- Validate config structure

**Key Operations**:
- `load_config() -> Config`
- `save_config(config: Config) -> None`
- `get_default_config() -> Config`

**Default Config**:
```yaml
tag_prefixes:
  business: "BR-"
  system: "SR-"
  architecture: "AR-"
  code: "C-"
  test: "T-"
  decision: "ADR-"

directories:
  business: "docs/01_business"
  system: "docs/02_system"
  architecture: "docs/03_architecture"
  code: "src"
  test: "tests"
```

---

### Infrastructure Layer

#### File System Access

**Purpose**: Abstract file I/O operations.

**Responsibilities**:
- Read files as UTF-8 text
- Write files atomically (write to temp, rename)
- Walk directory trees
- Detect repository root by looking for `.git/` or `.contextgit/`

**Key Operations**:
- `read_file(path: str) -> str`
- `write_file_atomic(path: str, content: str) -> None`
- `walk_files(root: str, pattern: str = "*.md") -> Iterator[str]`
- `find_repo_root(start_path: str) -> str`

---

#### YAML Serialization

**Purpose**: Parse and serialize YAML with deterministic formatting.

**Responsibilities**:
- Parse YAML safely (using `yaml.safe_load`)
- Dump YAML with sorted keys and deterministic formatting
- Use 2-space indentation
- Use block style for readability

**Key Operations**:
- `load_yaml(content: str) -> dict`
- `dump_yaml(data: dict) -> str`

**Configuration for ruamel.yaml**:
```python
yaml = YAML()
yaml.default_flow_style = False
yaml.indent(mapping=2, sequence=2, offset=0)
yaml.width = 120
```

---

#### Output Formatter

**Purpose**: Format command output for terminal or JSON.

**Responsibilities**:
- Format plain-text output with colors and tables (using `rich` or similar)
- Format JSON output with proper structure
- Respect `--format json` flag

**Key Operations**:
- `format_status(index: Index, format: str) -> str`
- `format_node(node: Node, format: str) -> str`
- `format_links(links: list[Link], format: str) -> str`

---

## Data Flow: Typical Scan Operation

```
1. User runs: contextgit scan docs/ --recursive

2. CLI layer parses arguments
   └─> ScanHandler invoked

3. ScanHandler:
   ├─> ConfigManager: load config
   ├─> FileSystem: walk docs/ to find *.md files
   ├─> For each file:
   │   ├─> FileSystem: read file content
   │   ├─> MetadataParser: parse metadata blocks
   │   ├─> LocationResolver: resolve location for each block
   │   ├─> ChecksumCalculator: calculate checksum of snippet
   │   └─> Store parsed nodes
   │
   ├─> IndexManager: load existing index
   │
   ├─> For each parsed node:
   │   ├─> Compare checksums with existing node
   │   ├─> If different: mark as changed
   │   ├─> IndexManager: update or add node
   │   └─> LinkingEngine: update sync status
   │
   ├─> IndexManager: save index atomically
   └─> OutputFormatter: display summary

4. Output: "Scanned 10 files, added 3 nodes, updated 2 nodes, created 5 links"
```

## Data Flow: Extract Operation

```
1. User (or LLM) runs: contextgit extract SR-010 --format json

2. CLI layer parses arguments
   └─> ExtractHandler invoked

3. ExtractHandler:
   ├─> IndexManager: load index
   ├─> IndexManager: get_node("SR-010")
   ├─> Check node exists
   ├─> LocationResolver: extract_snippet(node.file, node.location)
   └─> OutputFormatter: format as JSON

4. Output: {"id": "SR-010", "file": "docs/...", "snippet": "..."}
```

## Integration with LLM Workflows

### Detection

LLM tools (Claude Code) detect contextgit-enabled projects by checking for `.contextgit/config.yaml` at the repository root.

### Workflow Example: "Implement SR-010"

1. **LLM receives task**: "Implement the logging API (SR-010)"
2. **LLM extracts requirement**:
   - Runs `contextgit extract SR-010 --format json`
   - Receives snippet with requirement details
3. **LLM finds related items**:
   - Runs `contextgit show SR-010 --format json`
   - Sees upstream (BR-001) and downstream (AR-020, C-120)
   - Optionally extracts those as well for context
4. **LLM implements code**:
   - Writes implementation to `src/logging/api.py`
5. **LLM updates traceability**:
   - Creates metadata block for code item C-121
   - Adds `upstream: [SR-010]` to metadata
6. **LLM scans**:
   - Runs `contextgit scan src/`
   - Index updated with new code node C-121
   - Link created: SR-010 → C-121

### Workflow Example: "Update BR-001"

1. **LLM modifies** `docs/01_business/observability.md` (contains BR-001)
2. **LLM scans**:
   - Runs `contextgit scan docs/01_business/`
   - Checksum of BR-001 changes
   - All downstream links marked `upstream_changed`
3. **LLM notifies user**:
   - Runs `contextgit status --stale --format json`
   - Reports: "Downstream items need review: SR-010, SR-011"
4. **User reviews and updates** SR-010, SR-011
5. **User confirms sync**:
   - Runs `contextgit confirm SR-010`
   - Runs `contextgit confirm SR-011`
   - Links marked `sync_status: ok`

---

## Technology Stack (Recommendations)

### Core Language
- **Python 3.11+**: Modern Python with type hints, dataclasses, pattern matching

### CLI Framework
- **Typer**: Modern, type-hint-based CLI framework with great help text and validation
- Alternative: Click (more mature, slightly more verbose)

### YAML Processing
- **ruamel.yaml**: Preserves formatting, supports deterministic output, round-trip editing
- Alternative: PyYAML (simpler but less control over formatting)

### Markdown Parsing
- **Python-Markdown** or **markdown-it-py**: For parsing Markdown structure (headings)
- Alternative: Simple regex (lightweight but less robust)

### File System
- **pathlib** (stdlib): Modern path handling
- **os** and **shutil** (stdlib): File operations

### Hashing
- **hashlib** (stdlib): SHA-256 for checksums

### Output Formatting
- **rich**: Beautiful terminal output with colors, tables, progress bars
- Alternative: Plain text with ANSI codes

### Testing
- **pytest**: Test framework
- **pytest-cov**: Coverage reporting

### Type Checking
- **mypy**: Static type checker for type hints

### Linting & Formatting
- **ruff**: Fast linter and formatter (replaces flake8, black, isort)
- Alternative: black + flake8 + isort

---

## Error Handling Strategy

### Graceful Degradation
- Malformed metadata blocks: Log warning, skip block, continue processing
- Missing files: Mark links as broken, continue processing
- Invalid YAML in index: Refuse to start, report specific error

### Atomic Operations
- Always write to temp file first, then rename (POSIX atomic)
- If any error during write, temp file is discarded, original index unchanged

### Clear Error Messages
- Include file path and line number for parsing errors
- Include node IDs for link errors
- Suggest corrective actions

### Exit Codes
- 0: Success
- 1: General error
- 2: Invalid arguments
- 3: File not found
- 4: Invalid metadata
- 5: Index corrupted

---

## Performance Considerations

### Index Loading
- Load index once per command, cache in memory
- Use dict for O(1) node lookup by ID
- Build link adjacency maps for O(1) upstream/downstream queries

### Scanning
- Process files in parallel for large directories (using `concurrent.futures`)
- Stream file reading (don't load entire files into memory at once)
- Short-circuit checksum calculation if file timestamp unchanged (future optimization)

### Checksums
- Use SHA-256 (fast, standard, collision-resistant)
- Cache checksums in index (only recalculate on content change)

### Output
- For JSON output, use `json.dumps` with `ensure_ascii=False` for speed
- For large status outputs, paginate or limit results by default

---

## Security Considerations

### Local-Only
- No network access
- No data transmission

### Input Validation
- Validate all user input (IDs, paths, flags)
- Sanitize file paths (prevent path traversal)
- Use safe YAML parsing (no arbitrary code execution)

### File Access
- Only read/write within repository root
- Validate that file paths are under repo root (prevent escapes)

---

## Extensibility (Future)

While the MVP focuses on Markdown files and YAML storage, the architecture is designed to be extensible:

### Additional File Formats
- Add parsers for ReStructuredText, AsciiDoc
- Add parsers for source code comments (Python docstrings, JSDoc)

### Advanced Linking
- Support weighted links (importance, confidence)
- Support link attributes (date range, conditional)

### Graph Algorithms
- Shortest path between requirements
- Impact analysis (transitive closure of changes)
- Coverage analysis (requirements without tests)

### Integration Points
- Git hooks for automatic scanning
- CI/CD plugins
- VS Code extension (already planned)
- GitHub Action for PR checks

---

## Summary

The architecture of `contextgit` is layered, modular, and designed for:
- **Simplicity**: Text-based storage, no database
- **Speed**: Most operations under 500ms
- **Reliability**: Atomic writes, clear error handling
- **LLM-friendliness**: JSON output, precise context extraction
- **Git-friendliness**: Deterministic output, clean diffs

This design supports the MVP requirements while providing a foundation for future enhancements.
