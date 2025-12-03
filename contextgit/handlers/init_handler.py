"""Handler for contextgit init command."""

import json
import os
from pathlib import Path
import typer

from contextgit.handlers.base import BaseHandler
from contextgit.infra.filesystem import FileSystem
from contextgit.infra.yaml_io import YAMLSerializer
from contextgit.infra.output import OutputFormatter
from contextgit.domain.config.manager import ConfigManager
from contextgit.domain.index.manager import IndexManager
from contextgit.models.config import Config
from contextgit.models.index import Index
from contextgit.constants import (
    CONTEXTGIT_DIR,
    LLM_INSTRUCTIONS_FILE,
    CURSORRULES_FILE,
    CLAUDE_MD_FILE,
)


# Comprehensive LLM instructions template
LLM_INSTRUCTIONS_TEMPLATE = '''# contextgit LLM Integration Guide

This project uses **contextgit** for requirements traceability in LLM-assisted development.

## What is contextgit?

contextgit is a CLI tool that:
- Tracks traceability from business requirements → system specs → architecture → code → tests
- Embeds metadata in Markdown files (YAML frontmatter or HTML comments)
- Maintains a central index (`.contextgit/requirements_index.yaml`)
- Detects staleness via checksums when upstream requirements change
- Extracts precise context snippets for LLM consumption
- Provides JSON output for programmatic access

## Detection

If `.contextgit/config.yaml` exists, this is a **contextgit-managed project**.

---

## Core Workflows

### Before Modifying Requirements or Documentation

```bash
# Find requirements related to a file
contextgit relevant-for-file <path> --format json

# Extract precise context for a specific requirement
contextgit extract <ID> --format json

# Show full details of a requirement
contextgit show <ID> --format json
```

### After Modifying Requirements or Documentation

```bash
# Update the index with changes
contextgit scan docs/ --recursive

# Check for broken or stale links
contextgit status --stale
```

### When Adding New Requirements

```bash
# 1. Generate the next ID for a type
contextgit next-id <type>
# Types: business, system, architecture, code, test, decision

# 2. Create the Markdown file with YAML frontmatter:
# ---
# contextgit:
#   id: <generated-id>
#   type: <type>
#   title: "Your requirement title"
#   status: active
#   upstream: []
#   downstream: []
# ---

# 3. Register in the index
contextgit scan docs/ --recursive
```

### When Upstream Requirements Change

```bash
# 1. Find stale/affected items
contextgit status --stale --format json

# 2. Review and update downstream items as needed

# 3. Mark as synchronized after updating
contextgit confirm <ID>
```

---

## Command Reference

| Command | Purpose | Example |
|---------|---------|---------|
| `contextgit init` | Initialize a project | `contextgit init` |
| `contextgit scan <path> -r` | Scan files and update index | `contextgit scan docs/ -r` |
| `contextgit status` | Show project health | `contextgit status --stale` |
| `contextgit show <ID>` | Display requirement details | `contextgit show SR-010 --format json` |
| `contextgit extract <ID>` | Extract requirement text | `contextgit extract SR-010` |
| `contextgit next-id <type>` | Generate next ID | `contextgit next-id system` |
| `contextgit relevant-for-file <path>` | Find related requirements | `contextgit relevant-for-file src/auth.py` |
| `contextgit link <FROM> <TO>` | Create manual link | `contextgit link BR-001 SR-010 --type refines` |
| `contextgit confirm <ID>` | Mark as synchronized | `contextgit confirm SR-010` |
| `contextgit fmt` | Format index for git | `contextgit fmt` |

**Always use `--format json` when parsing output programmatically.**

---

## Metadata Formats

### YAML Frontmatter (Recommended)

```markdown
---
contextgit:
  id: SR-001
  type: system
  title: "User authentication system"
  status: active
  upstream: [BR-001]
  downstream: [C-050, T-025]
  tags: [security, auth]
---

# System Requirement: User Authentication

The system shall provide secure user authentication...
```

### Inline HTML Comments

```markdown
<!-- contextgit
id: SR-002
type: system
title: "Password reset flow"
status: active
upstream: [BR-001]
-->

## Password Reset

The system shall provide a secure password reset mechanism...
```

---

## Node Types and ID Prefixes

| Type | Prefix | Purpose |
|------|--------|---------|
| `business` | BR- | Business requirements, user needs |
| `system` | SR- | System-level functional specs |
| `architecture` | AR- | Architecture decisions, ADRs |
| `code` | C- | Code implementation notes |
| `test` | T- | Test specifications |
| `decision` | ADR- | Design decisions |

---

## Link Sync Status

| Status | Meaning |
|--------|---------|
| `ok` | Link is synchronized |
| `upstream_changed` | Upstream requirement was modified |
| `downstream_changed` | Downstream requirement was modified |
| `broken` | Linked node no longer exists |

---

## Best Practices for LLMs

1. **Extract, don't load entire files**: Use `contextgit extract <ID>` to get only the relevant section.
2. **Check staleness before changes**: Run `contextgit status --stale` to understand current state.
3. **Scan after modifications**: Always run `contextgit scan` after editing requirement files.
4. **Use JSON output**: Add `--format json` for reliable parsing.
5. **Maintain traceability**: When creating new items, always specify `upstream` links.
6. **Confirm after updates**: Run `contextgit confirm <ID>` after updating downstream items.

---

## Example Workflow: Implementing a Feature

```bash
# 1. Find the requirement to implement
contextgit show SR-010 --format json

# 2. Extract the full context
contextgit extract SR-010

# 3. Implement the code...

# 4. After implementation, scan to update links
contextgit scan src/ --recursive

# 5. Verify traceability
contextgit status
```

---

## Files

- **Config**: `.contextgit/config.yaml`
- **Index**: `.contextgit/requirements_index.yaml`
- **This guide**: `.contextgit/LLM_INSTRUCTIONS.md`

For full documentation, see the project's `USER_GUIDE.md` and `README.md`.
'''

# Cursorrules template (concise, points to LLM_INSTRUCTIONS.md)
CURSORRULES_TEMPLATE = '''# Cursor Rules for contextgit Project

## This Project Uses contextgit for Requirements Traceability

**Read `.contextgit/LLM_INSTRUCTIONS.md` for full documentation.**

### Quick Reference

Before modifying `docs/`:
```bash
contextgit relevant-for-file <path>
contextgit extract <ID> --format json
```

After modifying `docs/`:
```bash
contextgit scan docs/ --recursive
contextgit status --stale
```

When adding new requirements:
```bash
contextgit next-id <type>  # Get ID
# Add YAML frontmatter with ID
contextgit scan docs/ --recursive
```

When upstream changes:
```bash
contextgit status --stale
# Update downstream items
contextgit confirm <ID>
```

### Detection
This is a contextgit project if `.contextgit/config.yaml` exists.
'''

# CLAUDE.md section template
CLAUDE_MD_SECTION = '''
## contextgit Integration

This project uses **contextgit** for requirements traceability.

**Read `.contextgit/LLM_INSTRUCTIONS.md` for full documentation.**

### Quick Workflow

1. **Before implementing features:**
   ```bash
   contextgit relevant-for-file <path>
   contextgit extract <ID> --format json
   ```

2. **After modifying docs:**
   ```bash
   contextgit scan docs/ --recursive
   contextgit status --stale
   ```

3. **When requirements change:**
   ```bash
   contextgit status --stale
   contextgit confirm <ID>  # After updating downstream
   ```

Always use `--format json` for parsing output.
'''


class InitHandler(BaseHandler):
    """Handler for contextgit init command.

    Initializes a contextgit project by creating:
    - .contextgit/ directory
    - .contextgit/config.yaml with default configuration
    - .contextgit/requirements_index.yaml with empty index
    - .contextgit/LLM_INSTRUCTIONS.md with LLM integration guide
    
    Optionally (with --setup-llm):
    - .cursorrules for Cursor IDE
    - CLAUDE.md section for Claude Code
    """

    def handle(
        self,
        directory: str | None = None,
        force: bool = False,
        setup_llm: bool = False,
        format: str = "text"
    ) -> str:
        """Initialize a contextgit project.

        Args:
            directory: Directory to initialize (default: current directory)
            force: Overwrite existing configuration if True
            setup_llm: Also create .cursorrules and CLAUDE.md
            format: Output format - "text" or "json"

        Returns:
            Success message formatted according to format parameter

        Raises:
            FileExistsError: If .contextgit/ already exists and force=False
            PermissionError: If directory cannot be created or written
        """
        # Determine target directory
        target_dir = Path(directory) if directory else Path(os.getcwd())
        target_dir = target_dir.resolve()

        # Check if already initialized
        contextgit_dir = target_dir / CONTEXTGIT_DIR
        if contextgit_dir.exists() and not force:
            raise FileExistsError(
                f"contextgit already initialized in {target_dir}. "
                "Use --force to reinitialize."
            )

        # Create .contextgit directory
        contextgit_dir.mkdir(parents=True, exist_ok=True)

        # Create default config
        config_mgr = ConfigManager(self.fs, self.yaml, str(target_dir))
        default_config = Config.get_default()
        config_mgr.save_config(default_config)

        # Create empty index
        index_mgr = IndexManager(self.fs, self.yaml, str(target_dir))
        empty_index = Index()
        index_mgr.save_index(empty_index)

        # Create LLM instructions (always)
        llm_instructions_path = contextgit_dir / LLM_INSTRUCTIONS_FILE
        llm_instructions_path.write_text(LLM_INSTRUCTIONS_TEMPLATE, encoding="utf-8")

        created_files = [
            contextgit_dir / "config.yaml",
            contextgit_dir / "requirements_index.yaml",
            llm_instructions_path,
        ]

        # Optionally create .cursorrules and CLAUDE.md
        if setup_llm:
            # Create .cursorrules (overwrite if exists)
            cursorrules_path = target_dir / CURSORRULES_FILE
            cursorrules_path.write_text(CURSORRULES_TEMPLATE, encoding="utf-8")
            created_files.append(cursorrules_path)

            # Create or append to CLAUDE.md
            claude_md_path = target_dir / CLAUDE_MD_FILE
            if claude_md_path.exists():
                # Append section if not already present
                existing_content = claude_md_path.read_text(encoding="utf-8")
                if "contextgit Integration" not in existing_content:
                    claude_md_path.write_text(
                        existing_content + "\n" + CLAUDE_MD_SECTION,
                        encoding="utf-8"
                    )
                    created_files.append(claude_md_path)
            else:
                # Create new CLAUDE.md
                claude_md_path.write_text(
                    "# CLAUDE.md\n\nThis file provides guidance to Claude Code when working with this repository.\n"
                    + CLAUDE_MD_SECTION,
                    encoding="utf-8"
                )
                created_files.append(claude_md_path)

        # Format output
        if format == "json":
            return json.dumps({
                "status": "success",
                "directory": str(target_dir),
                "files_created": [str(f) for f in created_files],
                "setup_llm": setup_llm,
                "message": "Initialized contextgit repository"
            }, indent=2)
        else:
            output_lines = [f"Created {f}" for f in created_files]
            output_lines.append("Repository initialized for contextgit.")
            if setup_llm:
                output_lines.append("")
                output_lines.append("LLM integration files created:")
                output_lines.append("  - .cursorrules (for Cursor)")
                output_lines.append("  - CLAUDE.md (for Claude Code)")
            else:
                output_lines.append("")
                output_lines.append("Tip: Run 'contextgit init --setup-llm' to also create")
                output_lines.append("     .cursorrules and CLAUDE.md for LLM integration.")
            return "\n".join(output_lines)


def init_command(
    directory: str = typer.Argument(
        None,
        help="Directory to initialize (default: current directory)"
    ),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Overwrite existing configuration"
    ),
    setup_llm: bool = typer.Option(
        False,
        "--setup-llm",
        help="Also create .cursorrules and CLAUDE.md for LLM integration"
    ),
    format: str = typer.Option(
        "text",
        "--format",
        help="Output format: text or json"
    ),
):
    """Initialize a contextgit project.

    Creates .contextgit/ directory with default configuration, empty index,
    and LLM integration guide.
    
    Use --setup-llm to also create .cursorrules (Cursor) and CLAUDE.md (Claude Code).
    """
    fs = FileSystem()
    yaml = YAMLSerializer()
    formatter = OutputFormatter()
    handler = InitHandler(fs, yaml, formatter)

    try:
        result = handler.handle(
            directory=directory,
            force=force,
            setup_llm=setup_llm,
            format=format
        )
        typer.echo(result)
    except FileExistsError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=1)
    except PermissionError as e:
        typer.echo(f"Error: Permission denied - {e}", err=True)
        raise typer.Exit(code=2)
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=1)
