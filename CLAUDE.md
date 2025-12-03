# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) and Cursor when working with code in this repository.

## IMPORTANT: This Project Uses contextgit

**This repository is managed with contextgit.** Before making changes to requirements or documentation:

### Automatic Workflow for AI Assistants

1. **Before modifying requirements/docs:**
   ```bash
   contextgit relevant-for-file <path>  # Find related requirements
   contextgit extract <ID>              # Get precise context
   ```

2. **After modifying requirements/docs:**
   ```bash
   contextgit scan docs/ --recursive    # Update the index
   contextgit status --stale            # Check for broken links
   ```

3. **When adding new requirements:**
   ```bash
   contextgit next-id <type>            # Generate ID (business, system, architecture, code, test)
   # Add YAML frontmatter with the generated ID
   contextgit scan docs/ --recursive    # Register in index
   ```

4. **When upstream requirements change:**
   ```bash
   contextgit status --stale            # Find affected downstream items
   # Update downstream items as needed
   contextgit confirm <ID>              # Mark as synchronized
   ```

### Detection
Check for `.contextgit/config.yaml` to confirm this is a contextgit-managed project.

---

## Project Overview

**contextgit** is a local-first, git-friendly CLI tool for managing requirements and context traceability in LLM-assisted software projects.

**Current Status**: v1.1.0 - Production ready, all 10 CLI commands implemented.

## What contextgit Is

contextgit is a local-first, git-friendly CLI tool that:
- Tracks requirements traceability from business needs → system specs → architecture → code → tests
- Embeds metadata in Markdown files (YAML frontmatter or HTML comments)
- Maintains a central YAML index (`.contextgit/requirements_index.yaml`)
- Detects staleness via checksums when upstream requirements change
- Extracts precise context snippets for LLM consumption
- Provides JSON output for all read operations to support Claude Code workflows

**Key Design Principle**: Designed specifically for integration with Claude Code and similar LLM CLIs.

## Documentation Structure

All planning documents are in `docs/`:

1. **01_product_overview.md** - Problem, users, goals, features
2. **02_user_stories.md** - 11 detailed workflows with personas
3. **03_system_requirements.md** - Functional (FR-1 to FR-13) and non-functional requirements
4. **04_architecture_overview.md** - **START HERE for architecture understanding**
5. **05_data_model_and_file_layout.md** - Complete schemas for nodes, links, index, config
6. **06_cli_specification.md** - Detailed specs for all 10 CLI commands
7. **07_llm_integration_guidelines.md** - How Claude Code should interact with contextgit
8. **08_mvp_scope_and_future_work.md** - What's in/out of MVP scope

## Architecture Overview (Read docs/04_architecture_overview.md for details)

**Layered Design**:
```
CLI Layer (Typer/Click)
    ↓
Application Layer (Command Handlers)
    ↓
Core Domain Layer:
  - Index Manager (CRUD for nodes/links, atomic writes)
  - Metadata Parser (YAML frontmatter & HTML comments)
  - Location Resolver & Snippet Extractor
  - Linking Engine (graph traversal, staleness detection)
  - Checksum Calculator (SHA-256)
  - ID Generator (sequential with prefixes)
  - Config Manager
    ↓
Infrastructure Layer:
  - File System Access (UTF-8, atomic writes)
  - YAML Serialization (deterministic, sorted)
  - Output Formatter (text/JSON)
```

**Key Components**:
- **Index Manager**: Never corrupts index; uses temp file + atomic rename
- **Metadata Parser**: Supports two formats in Markdown files:
  - YAML frontmatter at file start
  - Inline `<!-- contextgit ... -->` HTML comments
- **Linking Engine**: Auto-creates links from `upstream`/`downstream` fields; tracks sync status
- **Checksum Calculator**: Detects content changes to mark downstream items stale

## Data Model (Read docs/05_data_model_and_file_layout.md for schemas)

**Node**: Requirement/context item with id, type, title, file, location, status, checksum
**Link**: Traceability relationship with from/to IDs, relation_type, sync_status
**Index File**: `.contextgit/requirements_index.yaml` with sorted nodes and links
**Config File**: `.contextgit/config.yaml` with tag prefixes and directory suggestions

**Node Types**: business, system, architecture, code, test, decision
**Relation Types**: refines, implements, tests, derived_from, depends_on
**Sync Status**: ok, upstream_changed, downstream_changed, broken

## MVP Commands (Read docs/06_cli_specification.md for full specs)

All commands support `--format json` for LLM consumption:

- `contextgit init` - Initialize project
- `contextgit scan [PATH] [--recursive]` - Scan files, update index
- `contextgit status [--stale] [--orphans]` - Show project health
- `contextgit show <ID>` - Display node details with links
- `contextgit extract <ID>` - Extract requirement snippet (critical for LLMs)
- `contextgit link <FROM> <TO> --type <RELATION>` - Manual link creation
- `contextgit confirm <ID>` - Mark as synchronized after updates
- `contextgit next-id <TYPE>` - Generate next ID (e.g., BR-001, SR-012)
- `contextgit relevant-for-file <PATH>` - Find requirements for source file
- `contextgit fmt` - Format index for clean git diffs

## When Implementing Code

**Technology Stack** (from docs/04_architecture_overview.md):
- Python 3.11+ with type hints, dataclasses
- CLI framework: Typer (recommended) or Click
- YAML: ruamel.yaml for deterministic output
- Markdown parsing: Python-Markdown or markdown-it-py
- Testing: pytest with coverage

**Critical Implementation Requirements**:
1. **Atomic writes**: Always write to temp file, then rename (never corrupt index)
2. **Deterministic YAML**: Sort nodes by ID, links by (from, to) for git-friendliness
3. **Performance targets**:
   - Extract: < 100ms
   - Show/Status: < 500ms
   - Scan 1000 files: < 5 seconds
4. **Checksum**: SHA-256 of normalized text (strip whitespace, normalize line endings)
5. **Location tracking**: Heading paths (e.g., `["Section", "Subsection"]`) or line ranges

**File Organization** (when implementing):
```
contextgit/
├── cli/          # Typer command definitions
├── handlers/     # Command handlers (InitHandler, ScanHandler, etc.)
├── domain/       # Core domain (IndexManager, MetadataParser, etc.)
├── infra/        # File system, YAML, output formatting
└── models/       # Node, Link, Index, Config dataclasses
```

## LLM Integration (Read docs/07_llm_integration_guidelines.md)

**Detection**: Claude Code detects contextgit projects by checking for `.contextgit/config.yaml`

**Core Workflows**:
1. **Create requirement**: `next-id` → create file with metadata → `scan`
2. **Implement feature**: `extract <ID>` for context → implement → `scan` to link code
3. **Handle upstream changes**: `status --stale` → update downstream → `confirm <ID>`
4. **Find requirements for file**: `relevant-for-file <path>` → `extract` each ID

**Best Practices**:
- Always use `--format json` for parsing
- Extract only needed context (not entire files)
- Run `scan` after any file modifications
- Use `confirm` after updating downstream items

## MVP Scope (Read docs/08_mvp_scope_and_future_work.md)

**IN SCOPE**:
- All 10 CLI commands
- Markdown-only support
- Local-first (no network/cloud)
- Python 3.11+, Linux-first
- JSON output for LLM integration

**OUT OF SCOPE** (deferred to Phase 2+):
- VS Code extension
- Code parsing (auto-extract functions/classes)
- Watch mode
- ReStructuredText/AsciiDoc
- Web dashboard
- Issue tracker integration

## Development Milestones (from docs/08_mvp_scope_and_future_work.md)

1. Core CLI (Weeks 1-2): init, config, index management
2. Scanning & Indexing (Weeks 2-3): parse metadata, calculate checksums, create links
3. Querying & Extraction (Week 3-4): show, extract, status, relevant-for-file
4. Traceability (Week 4): sync status, link, confirm, staleness detection
5. Utilities (Week 5): next-id, fmt, error handling, JSON output
6. Docs & Packaging (Week 6): README, examples, PyPI packaging

## Important Constraints

1. **Never corrupt index**: Use atomic writes (temp + rename)
2. **Git-friendly**: Deterministic YAML ordering, relative paths only
3. **No state beyond index**: Index file is single source of truth
4. **Markdown-only for MVP**: Don't add RST, AsciiDoc, or code parsing yet
5. **Single-repo for MVP**: Don't implement multi-repo support yet

## When Working on User Stories

See docs/02_user_stories.md for 11 complete workflows including:
- Story 1: Initialize project
- Story 4: Create linked requirements
- Story 6: Detect upstream changes
- Story 7: Find requirements for source file
- Story 10: Use in CI to block PRs with stale requirements

Each story includes acceptance criteria and full flow.

## Key Files to Reference During Implementation

- **For CLI design**: docs/06_cli_specification.md (exact argument syntax, exit codes, examples)
- **For data structures**: docs/05_data_model_and_file_layout.md (Node/Link schemas, YAML format)
- **For architecture**: docs/04_architecture_overview.md (component responsibilities, algorithms)
- **For requirements validation**: docs/03_system_requirements.md (FR-1 through FR-13)
