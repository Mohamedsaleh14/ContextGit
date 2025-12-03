# contextgit User Guide

Complete guide to using contextgit for requirements traceability in LLM-assisted development.

## Table of Contents

1. [Introduction](#introduction)
2. [Installation](#installation)
3. [Core Concepts](#core-concepts)
4. [Getting Started](#getting-started)
5. [Command Reference](#command-reference)
6. [Workflows](#workflows)
7. [LLM Integration](#llm-integration)
8. [Best Practices](#best-practices)
9. [Troubleshooting](#troubleshooting)

## Introduction

### What is contextgit?

contextgit is a local-first, git-friendly CLI tool that helps you maintain requirements traceability in software projects, especially those developed with AI assistance (LLMs like Claude Code).

### Why Use contextgit?

- **Traceability**: Track the chain from business requirements → system specs → architecture → code → tests
- **Staleness Detection**: Automatically detect when upstream requirements change and downstream items need updates
- **LLM Integration**: Designed specifically for Claude Code and similar AI development tools
- **Git-Friendly**: All metadata stored in human-readable Markdown with YAML
- **Context Extraction**: Efficiently extract only the relevant context for AI consumption

### Key Features

- Embed metadata in Markdown files (YAML frontmatter or HTML comments)
- Maintain central index (`.contextgit/requirements_index.yaml`)
- Automatic link creation between requirements
- Checksum-based staleness detection
- JSON output for programmatic access
- Performance-optimized for large projects (< 100ms for extracts)

## Installation

### Option 1: Ubuntu/Debian Package (Recommended)

```bash
# Download the .deb package
wget https://github.com/your-org/contextgit/releases/download/v1.0.0/contextgit_1.0.0_all.deb

# Install dependencies
sudo apt update
sudo apt install python3 python3-typer python3-rich python3-ruamel.yaml

# Install contextgit
sudo dpkg -i contextgit_1.0.0_all.deb

# Verify installation
contextgit --help
```

### Option 2: From Source

```bash
# Clone repository
git clone https://github.com/your-org/contextgit.git
cd contextgit

# Install with pip (in virtual environment)
python3 -m venv venv
source venv/bin/activate
pip install -e .

# Verify installation
contextgit --help
```

### Option 3: Using pipx (Isolated Install)

```bash
# Install pipx if not already installed
sudo apt install pipx
pipx ensurepath

# Install contextgit
pipx install contextgit

# Verify installation
contextgit --help
```

## Core Concepts

### Nodes

A **node** represents a requirement or context item in your project. Each node has:

- **ID**: Unique identifier (e.g., `BR-001`, `SR-005`, `AC-012`)
- **Type**: business, system, architecture, code, test, decision, other
- **Title**: Human-readable description
- **File**: Path to the Markdown file containing this requirement
- **Location**: Where in the file (heading path or line range)
- **Status**: draft, active, deprecated
- **Checksum**: SHA-256 hash for change detection
- **Tags**: Optional categorization

### Links

A **link** represents a traceability relationship between two nodes:

- **From/To**: Source and target node IDs
- **Relation Type**: refines, implements, tests, derived_from, depends_on
- **Sync Status**: ok, upstream_changed, downstream_changed, broken

### Node Types

| Type | Prefix | Purpose |
|------|--------|---------|
| business | BR- | Business requirements, user needs |
| system | SR- | System-level functional/non-functional specs |
| architecture | AC- | Architectural decisions, design docs |
| code | CO- | Implementation files, modules |
| test | TS- | Test cases, test plans |
| decision | AD- | Architecture Decision Records |
| other | OT- | Miscellaneous items |

### Metadata Formats

#### Format 1: YAML Frontmatter

```markdown
---
contextgit:
  id: SR-001
  type: system
  title: User authentication system
  status: active
  upstream:
    - BR-003
  downstream:
    - AC-007
    - TS-015
  tags: [security, authentication]
---

# User Authentication System

Detailed system requirements...
```

#### Format 2: Inline HTML Comments

```markdown
# Feature: Password Reset

<!-- contextgit
id: SR-002
type: system
title: Password reset flow
status: active
upstream: [BR-004]
downstream: [CO-023, TS-018]
-->

The system shall provide a secure password reset mechanism...
```

### The Index File

The `.contextgit/requirements_index.yaml` file is the single source of truth:

```yaml
nodes:
  - id: BR-001
    type: business
    title: User login capability
    file: docs/requirements/business.md
    location:
      kind: heading
      path: ["Business Requirements", "Authentication"]
    status: active
    checksum: a3f2b8c...
    last_updated: "2025-12-02T10:30:00"

links:
  - from_id: BR-001
    to_id: SR-005
    relation_type: refines
    sync_status: ok
```

## Getting Started

### Step 1: Initialize a Project

```bash
cd your-project/
contextgit init
```

This creates:
- `.contextgit/config.yaml` - Configuration file
- `.contextgit/requirements_index.yaml` - Empty index
- `.contextgit/LLM_INSTRUCTIONS.md` - LLM integration guide

**For automatic LLM integration (Cursor/Claude):**
```bash
contextgit init --setup-llm
```

This also creates:
- `.cursorrules` - Cursor IDE integration
- `CLAUDE.md` - Claude Code integration

### Step 2: Create Your First Requirement

Create a Markdown file with metadata:

```bash
cat > docs/business-requirements.md << 'EOF'
---
contextgit:
  id: auto
  type: business
  title: User can log in with email and password
  status: draft
---

# User Authentication

## BR: Login Capability

Users must be able to authenticate using their email address and password.

**Acceptance Criteria:**
- Email validation
- Password strength requirements (min 8 chars, 1 uppercase, 1 number)
- Account lockout after 5 failed attempts
EOF
```

### Step 3: Scan the File

```bash
contextgit scan docs/business-requirements.md
```

Output:
```
Scanning: docs/business-requirements.md
✓ Found 1 requirement(s)
✓ Index updated

Summary:
  Nodes added: 1
  Nodes updated: 0
  Links created: 0
```

### Step 4: View the Requirement

```bash
contextgit show BR-001
```

Output displays:
- Node details (ID, type, title, status)
- Location in file
- Checksum
- Linked requirements (upstream/downstream)

### Step 5: Generate Next ID

```bash
contextgit next-id system
# Output: SR-001
```

Use this ID when creating your system requirements.

## Command Reference

### `contextgit init`

Initialize a contextgit project in the current directory.

```bash
contextgit init [--force] [--setup-llm] [--format FORMAT]
```

**Options:**
- `--force, -f`: Reinitialize existing project (overwrites existing config)
- `--setup-llm`: Also create `.cursorrules` and `CLAUDE.md` for LLM integration
- `--format`: Output format (text or json)

**Files Created:**
- `.contextgit/config.yaml` - Configuration
- `.contextgit/requirements_index.yaml` - Empty index
- `.contextgit/LLM_INSTRUCTIONS.md` - Comprehensive LLM integration guide

With `--setup-llm`:
- `.cursorrules` - Cursor IDE auto-detection rules
- `CLAUDE.md` - Claude Code integration guide

**Examples:**
```bash
# Basic initialization
cd my-project/
contextgit init

# With LLM integration files (recommended)
contextgit init --setup-llm

# Reinitialize with LLM integration
contextgit init --force --setup-llm
```

---

### `contextgit scan`

Scan Markdown files for metadata and update the index.

```bash
contextgit scan [PATH] [--recursive] [--dry-run] [--format FORMAT]
```

**Options:**
- `PATH`: File or directory to scan (default: current directory)
- `--recursive, -r`: Scan directories recursively
- `--dry-run`: Show what would be scanned without modifying index
- `--format`: Output format (text or json)

**Examples:**
```bash
# Scan single file
contextgit scan docs/requirements.md

# Scan directory recursively
contextgit scan docs/ --recursive

# Dry run to preview
contextgit scan docs/ -r --dry-run

# JSON output for automation
contextgit scan docs/ --format json
```

---

### `contextgit status`

Show project health status.

```bash
contextgit status [--stale] [--orphans] [--format FORMAT]
```

**Options:**
- `--stale`: Show only stale requirements (upstream changed)
- `--orphans`: Show only orphaned nodes (no links)
- `--format`: Output format (text or json)

**Examples:**
```bash
# Overall status
contextgit status

# Find stale requirements
contextgit status --stale

# Find orphans
contextgit status --orphans

# JSON output
contextgit status --format json
```

---

### `contextgit show`

Display detailed information about a requirement.

```bash
contextgit show <NODE_ID> [--format FORMAT]
```

**Examples:**
```bash
# Show requirement details
contextgit show BR-001

# JSON output
contextgit show SR-005 --format json
```

---

### `contextgit extract`

Extract the content snippet for a requirement (critical for LLM consumption).

```bash
contextgit extract <NODE_ID> [--format FORMAT]
```

**Examples:**
```bash
# Extract for manual review
contextgit extract BR-001

# Extract for LLM (JSON mode)
contextgit extract SR-003 --format json
```

**Use Case:** Feed to Claude Code for implementation context.

---

### `contextgit link`

Manually create a traceability link.

```bash
contextgit link <FROM_ID> <TO_ID> --type <RELATION_TYPE>
```

**Relation Types:**
- `refines`: From business → system requirement
- `implements`: From spec → code
- `tests`: From code → test
- `derived_from`: Generic derivation
- `depends_on`: Dependency relationship

**Examples:**
```bash
# Link business req to system req
contextgit link BR-001 SR-005 --type refines

# Link code to test
contextgit link CO-042 TS-089 --type tests
```

---

### `contextgit confirm`

Mark a requirement as synchronized after updating due to upstream changes.

```bash
contextgit confirm <NODE_ID>
```

**Example:**
```bash
# After updating SR-005 due to BR-001 changes
contextgit confirm SR-005
```

---

### `contextgit next-id`

Generate the next available ID for a node type.

```bash
contextgit next-id <TYPE>
```

**Examples:**
```bash
contextgit next-id business   # BR-001
contextgit next-id system     # SR-001
contextgit next-id test       # TS-001
```

---

### `contextgit relevant-for-file`

Find all requirements relevant to a source code file.

```bash
contextgit relevant-for-file <FILE_PATH> [--format FORMAT]
```

**Examples:**
```bash
# Find requirements for implementation file
contextgit relevant-for-file src/auth/login.py

# JSON output for LLM
contextgit relevant-for-file src/api/users.py --format json
```

---

### `contextgit fmt`

Format the index file for clean git diffs (sorts nodes and links deterministically).

```bash
contextgit fmt
```

**Example:**
```bash
# Before committing
contextgit fmt
git add .contextgit/requirements_index.yaml
git commit -m "Update requirements"
```

## Workflows

### Workflow 1: Creating Linked Requirements

**Scenario:** You have a business requirement and want to create system requirements that refine it.

```bash
# Step 1: Create business requirement
cat > docs/business.md << 'EOF'
---
contextgit:
  id: auto
  type: business
  title: Users can reset forgotten passwords
  status: active
---
# Password Reset Feature
...
EOF

# Step 2: Scan to generate ID
contextgit scan docs/business.md
# Note the generated ID (e.g., BR-002)

# Step 3: Create system requirement that refines it
cat > docs/system.md << 'EOF'
---
contextgit:
  id: auto
  type: system
  title: Password reset via email verification
  status: active
  upstream:
    - BR-002
---
# System Requirement: Password Reset
...
EOF

# Step 4: Scan to create link automatically
contextgit scan docs/system.md

# Step 5: Verify link created
contextgit show BR-002
# Shows downstream: SR-003

contextgit show SR-003
# Shows upstream: BR-002
```

---

### Workflow 2: Detecting Upstream Changes

**Scenario:** A business requirement changes, and you need to find affected items.

```bash
# Step 1: Edit the business requirement file
# (modify docs/business.md content)

# Step 2: Rescan to update checksum
contextgit scan docs/business.md

# Step 3: Check for stale requirements
contextgit status --stale

# Output shows:
# SR-003 (upstream_changed) - upstream BR-002 was modified

# Step 4: Extract the updated requirement
contextgit extract BR-002

# Step 5: Update the system requirement accordingly
# (edit docs/system.md)

# Step 6: Rescan to update checksum
contextgit scan docs/system.md

# Step 7: Confirm synchronization
contextgit confirm SR-003

# Step 8: Verify status
contextgit status --stale
# (no longer shows SR-003)
```

---

### Workflow 3: Implementing a Feature with Claude Code

**Scenario:** Use Claude Code to implement a system requirement.

```bash
# Step 1: Find the requirement to implement
contextgit show SR-005

# Step 2: Extract full context
contextgit extract SR-005 > requirement.txt

# Step 3: Ask Claude Code to implement
# "Claude, implement the requirement in requirement.txt"

# Step 4: After Claude creates the code, add metadata
cat >> src/auth/login.py << 'EOF'
"""
contextgit:
  id: auto
  type: code
  title: Login implementation
  status: active
  upstream:
    - SR-005
"""
EOF

# Step 5: Scan to link code to requirement
contextgit scan src/auth/login.py --recursive

# Step 6: Verify traceability
contextgit show SR-005
# Shows downstream: CO-012

# Step 7: Find requirements for this file (reverse lookup)
contextgit relevant-for-file src/auth/login.py
# Shows: SR-005, BR-001 (transitively)
```

---

### Workflow 4: Using in CI/CD

**Scenario:** Block PRs that have stale requirements.

Create `.github/workflows/contextgit-check.yml`:

```yaml
name: Requirements Traceability Check

on: [pull_request]

jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Install contextgit
        run: |
          wget https://releases.contextgit.dev/contextgit_1.0.0_all.deb
          sudo dpkg -i contextgit_1.0.0_all.deb

      - name: Check for stale requirements
        run: |
          contextgit status --stale --format json > stale.json
          if [ $(jq '.stale_count' stale.json) -gt 0 ]; then
            echo "ERROR: Found stale requirements"
            jq '.stale_nodes' stale.json
            exit 1
          fi

      - name: Check for orphans
        run: |
          contextgit status --orphans --format json > orphans.json
          if [ $(jq '.orphan_count' orphans.json) -gt 10 ]; then
            echo "WARNING: Too many orphaned requirements"
            jq '.orphan_nodes' orphans.json
          fi
```

## LLM Integration

contextgit is designed for seamless integration with LLM-assisted development tools like **Cursor** and **Claude Code**.

### Setting Up Automatic Detection

LLM assistants don't automatically know your project uses contextgit. You must tell them via a rules file:

#### For Cursor: Create `.cursorrules`

```bash
cat > .cursorrules << 'EOF'
# Cursor Rules for Your Project

## This Project Uses contextgit

Before modifying requirements or documentation:
1. Run `contextgit relevant-for-file <path>` to find related requirements
2. Run `contextgit extract <ID>` for precise context

After modifying requirements or documentation:
1. Run `contextgit scan docs/ --recursive` to update the index
2. Run `contextgit status --stale` to check for broken links

When adding new requirements:
1. Generate ID: `contextgit next-id <type>`
2. Add YAML frontmatter with the generated ID
3. Run `contextgit scan docs/ --recursive`

Always use `--format json` for parsing output.
EOF
```

#### For Claude Code: Create/Update `CLAUDE.md`

```bash
cat >> CLAUDE.md << 'EOF'

## contextgit Integration

This project uses contextgit for requirements traceability.

**Before implementing features:**
1. Run `contextgit relevant-for-file <path>` to find relevant requirements
2. Run `contextgit extract <ID>` for each requirement

**After modifying files:**
1. Run `contextgit scan <path>` to update traceability
2. Run `contextgit status --stale` to check for impacts

**When requirements change:**
1. Run `contextgit status --stale` to find affected items
2. Update downstream items accordingly
3. Run `contextgit confirm <ID>` after updates
EOF
```

### How Detection Works

| File | Read By | When |
|------|---------|------|
| `.cursorrules` | Cursor | Start of every conversation |
| `CLAUDE.md` | Claude Code | When working on the project |
| `.contextgit/config.yaml` | Both | Confirms contextgit is initialized |

**Important**: Without these rules files, the AI assistant will NOT automatically use contextgit commands. The rules file tells the AI:
1. This project uses contextgit
2. What commands to run before/after changes
3. The workflow to follow

### Using with Claude Code

contextgit is designed specifically for Claude Code integration.

#### Automatic Detection

Claude Code will automatically detect contextgit projects if `.contextgit/config.yaml` exists AND you have a `CLAUDE.md` with contextgit instructions.

#### Best Practices for Claude Code

1. **Always use JSON output** for programmatic parsing:
   ```bash
   contextgit extract BR-001 --format json | jq -r '.snippet'
   ```

2. **Extract before implementing**:
   ```
   User: Implement the login feature
   Claude: Let me check the requirements first
   [runs: contextgit relevant-for-file src/auth/login.py]
   [runs: contextgit extract SR-005]
   [implements with full context]
   ```

3. **Scan after modifications**:
   ```
   [Claude writes code]
   [runs: contextgit scan src/ --recursive]
   ```

4. **Check staleness before major work**:
   ```bash
   contextgit status --stale --format json
   ```

#### Claude Code CLAUDE.md Integration

Add to your `CLAUDE.md`:

```markdown
## contextgit Integration

This project uses contextgit for requirements traceability.

**Before implementing features:**
1. Run `contextgit relevant-for-file <path>` to find relevant requirements
2. Run `contextgit extract <ID>` for each requirement
3. Implement with full context awareness

**After modifying files:**
1. Run `contextgit scan <path>` to update traceability
2. Run `contextgit status --stale` to check for impacts

**When requirements change:**
1. Run `contextgit status --stale` to find affected items
2. Update downstream items accordingly
3. Run `contextgit confirm <ID>` after updates
```

### JSON Output Examples

#### Extract (JSON):
```json
{
  "node_id": "BR-001",
  "file": "docs/business.md",
  "location": {
    "kind": "heading",
    "path": ["Business Requirements", "Authentication"]
  },
  "snippet": "Users must be able to log in with email and password...",
  "checksum": "a3f2b8c9d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1"
}
```

#### Status (JSON):
```json
{
  "total_nodes": 47,
  "total_links": 83,
  "stale_count": 3,
  "orphan_count": 5,
  "stale_nodes": [
    {
      "id": "SR-003",
      "title": "Password reset system",
      "reason": "upstream_changed",
      "affected_by": ["BR-002"]
    }
  ],
  "orphan_nodes": ["AD-007", "TS-042"]
}
```

## Best Practices

### 1. Metadata Organization

**DO:**
- Use YAML frontmatter for requirement documents
- Use inline HTML comments for code files
- Keep one primary requirement per file/section

**DON'T:**
- Mix multiple unrelated requirements in one file
- Forget to specify `upstream` and `downstream` fields
- Use cryptic titles

### 2. ID Management

**DO:**
- Always use `contextgit next-id` to get the next ID
- Use `id: auto` when creating new requirements, then scan
- Keep ID prefixes consistent with node types

**DON'T:**
- Manually assign IDs (risk of duplicates)
- Change IDs after scanning (breaks links)
- Reuse deleted IDs

### 3. Scanning Discipline

**DO:**
- Run `contextgit scan` after creating/modifying requirements
- Use `--dry-run` to preview changes
- Scan entire directories with `-r` for consistency

**DON'T:**
- Forget to scan after editing metadata
- Scan too frequently (after every character typed)
- Ignore scan errors

### 4. Traceability

**DO:**
- Always link requirements explicitly via `upstream`/`downstream`
- Use appropriate relation types
- Check `contextgit status --stale` regularly

**DON'T:**
- Create isolated requirements (orphans)
- Leave stale requirements unaddressed
- Over-link (create unnecessary dependencies)

### 5. Git Integration

**DO:**
- Run `contextgit fmt` before committing
- Include `.contextgit/` in version control
- Review index diffs in PRs

**DON'T:**
- Edit `.contextgit/requirements_index.yaml` manually
- Commit `.contextgit/*.tmp` files
- Resolve merge conflicts by keeping both versions

### 6. Performance

**DO:**
- Use `--format json` for programmatic access (faster parsing)
- Extract only needed requirements (not entire trees)
- Use `contextgit relevant-for-file` instead of scanning all nodes

**DON'T:**
- Extract large subtrees unnecessarily
- Run full scans in tight loops
- Parse text output with regex (use JSON mode)

## Troubleshooting

### Issue: "Not a contextgit project"

**Cause:** `.contextgit/config.yaml` not found.

**Solution:**
```bash
contextgit init
```

---

### Issue: "Node ID already exists"

**Cause:** Duplicate ID in metadata.

**Solution:**
```bash
# Use auto-generated IDs
sed -i 's/id: BR-001/id: auto/' docs/file.md
contextgit scan docs/file.md
```

---

### Issue: "Checksum mismatch"

**Cause:** File content changed but index not updated.

**Solution:**
```bash
contextgit scan <file> --recursive
```

---

### Issue: "Broken link"

**Cause:** Referenced node doesn't exist.

**Solution:**
```bash
# Find broken links
contextgit status --format json | jq '.broken_links'

# Either create the missing node or remove the reference
```

---

### Issue: "Performance slow on large projects"

**Cause:** Scanning too many files or large file sizes.

**Solution:**
- Use `--format json` for faster programmatic access
- Scan only changed files, not entire directory
- Exclude non-documentation directories from scans
- Check `.gitignore` patterns apply to scans

---

### Issue: "Dependencies not found"

**Cause:** Python packages not installed.

**Solution:**
```bash
# Ubuntu/Debian
sudo apt install python3-typer python3-rich python3-ruamel.yaml

# Or use pipx
pipx install contextgit
```

---

### Issue: "Index corrupted"

**Cause:** Manual editing or merge conflict.

**Solution:**
```bash
# Backup current index
cp .contextgit/requirements_index.yaml .contextgit/requirements_index.yaml.backup

# Rebuild from scratch
rm .contextgit/requirements_index.yaml
contextgit init --force
contextgit scan . --recursive
```

---

### Issue: "Cannot resolve location"

**Cause:** Markdown heading structure changed.

**Solution:**
- Rescan the file to update location
- Use line-based location if heading structure is unstable

---

## Advanced Topics

### Custom Tag Prefixes

Edit `.contextgit/config.yaml`:

```yaml
tag_prefixes:
  business: "BIZ-"
  system: "SYS-"
  architecture: "ARCH-"
  code: "CODE-"
  test: "TEST-"
  decision: "DEC-"
  other: "MISC-"
```

Then regenerate IDs:
```bash
contextgit next-id business  # BIZ-001
```

### Multi-Repository Traceability

For monorepo or multi-repo setups, use relative paths and consistent ID namespaces:

```yaml
# Repo A: frontend
upstream:
  - ../backend-repo/docs/api-spec.md#SR-042
```

(Note: Cross-repo linking is experimental in MVP)

### Performance Tuning

For projects with 1000+ requirements:

1. Use `contextgit extract` instead of `show` (faster)
2. Scan only changed files in CI
3. Use `--format json` and parse with `jq`
4. Consider splitting large requirement documents

---

## Appendix

### File Structure

```
my-project/
├── .contextgit/
│   ├── config.yaml              # Configuration
│   └── requirements_index.yaml  # Central index
├── docs/
│   ├── business/
│   │   └── requirements.md      # Business requirements
│   ├── system/
│   │   └── specs.md             # System requirements
│   └── architecture/
│       └── decisions.md         # ADRs
└── src/
    └── module/
        └── code.py              # Implementation with metadata
```

### Checksums

contextgit uses SHA-256 checksums of normalized text:
- Strips leading/trailing whitespace
- Normalizes line endings to `\n`
- Uses UTF-8 encoding

This ensures consistent checksums across platforms.

### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | General error |
| 2 | Not a contextgit project |
| 3 | Node not found |
| 4 | Invalid input |
| 5 | File not found |

---

## Getting Help

- **Documentation**: https://docs.contextgit.dev
- **Issues**: https://github.com/your-org/contextgit/issues
- **Discussions**: https://github.com/your-org/contextgit/discussions

---

**Version**: 1.0.0
**Last Updated**: 2025-12-02
