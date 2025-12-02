---
contextgit:
  id: auto
  type: business
  title: contextgit product vision and requirements
  status: active
  tags: [mvp, planning, product]
---

# Product Overview

## Problem Statement

When building software products with Large Language Models (LLMs) such as Claude Code, development teams face a critical challenge: **context chaos**. As LLMs generate requirements documents, system specifications, architectural designs, and code, the volume of context artifacts grows rapidly. Without proper management, these artifacts become:

- **Scattered and disconnected**: Requirements live in separate documents with no clear relationships between business needs, system specs, architecture decisions, and actual code.
- **Stale and outdated**: When upstream requirements change, downstream artifacts (designs, code, tests) don't get updated, leading to inconsistencies.
- **Hard to trace**: It's difficult to answer questions like "Which code implements this business requirement?" or "Which requirements are affected by this architectural change?"
- **Overwhelming for LLMs**: Without selective context extraction, LLMs consume entire documents, wasting tokens and diluting focus on relevant information.

This context chaos leads to:
- LLMs using outdated information to generate incorrect code
- Requirements drift where implementation diverges from original intent
- Wasted time manually tracking what needs updating
- Loss of traceability from business goals to code

## Target Users

### Primary Persona: Solo Developer with LLM CLI
- Uses Claude Code or similar LLM CLI tools for development
- Works on personal or small open-source projects
- Needs to maintain clear requirements and design docs
- Wants git-friendly, text-based workflow
- Values automation and CLI efficiency

### Secondary Persona: Small Development Team
- 2-5 developers collaborating via git
- Uses LLMs to accelerate development
- Needs shared understanding of requirements and traceability
- Wants CI integration for detecting stale docs
- Values code review and documentation discipline

### Non-Target (for MVP)
- Enterprise teams with complex compliance requirements
- Teams requiring web-based dashboards or SaaS platforms
- Organizations needing integration with JIRA, Azure DevOps, etc.
- Teams requiring role-based access control or audit trails

## Goals

The `contextgit` tool aims to:

1. **Establish traceability as a first-class citizen**: Make it easy to track relationships between business requirements, system specs, architecture, code, and tests.

2. **Detect staleness automatically**: Alert developers when upstream requirements change and downstream artifacts need updating.

3. **Enable LLM-focused workflows**: Provide commands that let LLMs extract only relevant context snippets instead of reading entire documents.

4. **Stay git-friendly**: Store all state in plain-text YAML and Markdown files that produce clean, reviewable diffs.

5. **Remain local-first**: Work entirely on the developer's machine without requiring cloud services or network connectivity.

6. **Minimize friction**: Integrate naturally with existing git workflows, requiring minimal ceremony or tool-specific syntax.

## Non-Goals (MVP)

The MVP explicitly does NOT aim to:

- Provide a web UI or SaaS dashboard
- Integrate with issue tracking systems (JIRA, Linear, GitHub Issues)
- Offer real-time collaboration features
- Support multiple programming languages for code parsing (Python only initially)
- Provide advanced graph visualization (basic text output only)
- Handle large-scale enterprise requirements (thousands of complex nodes)
- Support workflows outside of LLM-assisted development
- Manage access control, permissions, or audit logging
- Generate requirements automatically (it manages existing requirements)

## High-Level Feature List (MVP)

### Core Features

1. **Project Initialization**
   - Initialize a repository to use contextgit
   - Create configuration and index files
   - Set up default directory structure

2. **Metadata Embedding**
   - Support inline metadata blocks in Markdown files
   - Support YAML frontmatter for file-level requirements
   - Define ID conventions per requirement type (BR-, SR-, AR-, etc.)

3. **Scanning and Indexing**
   - Scan files for contextgit metadata blocks
   - Build/update central index of all nodes and links
   - Calculate checksums for change detection
   - Track file locations (heading paths or line ranges)

4. **Traceability Management**
   - Create links between requirements (upstream/downstream)
   - Track link sync status (ok, upstream_changed, downstream_changed, broken)
   - Support multiple relation types (refines, implements, tests, depends_on)

5. **Status and Health Checks**
   - Show overall project health (node counts, link counts, stale links)
   - Identify orphan nodes (no upstream or downstream)
   - Filter by file, type, or staleness

6. **Context Extraction**
   - Extract specific requirement snippets by ID
   - Output in human-readable or JSON format
   - Enable LLMs to work with targeted context

7. **LLM Integration**
   - Generate next available ID for new requirements
   - Find requirements relevant to a specific source file
   - Support JSON output for all commands
   - Provide clear conventions for LLM workflows

8. **Index Management**
   - Format and normalize index file for clean git diffs
   - Manually create/update links
   - Confirm synchronization after updates

### CLI Commands (MVP)

- `contextgit init`: Initialize project
- `contextgit scan`: Scan files and update index
- `contextgit status`: Show project health
- `contextgit show <ID>`: Display node details
- `contextgit extract <ID>`: Extract requirement snippet
- `contextgit link <FROM> <TO>`: Create manual link
- `contextgit confirm <ID>`: Mark as synchronized
- `contextgit next-id <TYPE>`: Generate new ID
- `contextgit relevant-for-file <PATH>`: Find related requirements
- `contextgit fmt`: Format index file

All commands support `--format json` for machine consumption.

## Future Extensions (Beyond MVP)

These features are explicitly out of scope for the MVP but may be considered for future versions:

### Phase 2: Enhanced Tooling
- VS Code extension with side panel and visualization
- Support for more file formats (ReStructuredText, AsciiDoc)
- Code-level parsing to auto-link Python functions/classes to requirements
- Watch mode for continuous index updates

### Phase 3: Team Collaboration
- Git hooks for enforcing requirement metadata on commits
- CI integration for blocking PRs with stale requirements
- Diff reports showing what changed between branches
- Team analytics (coverage, staleness trends)

### Phase 4: Advanced Features
- Interactive graph visualization (web-based)
- Integration with issue trackers (GitHub Issues, JIRA)
- Requirements coverage metrics per code file
- Automatic propagation of status changes (deprecation, supersession)
- Multi-repository support for microservices

### Phase 5: Enterprise
- SaaS platform for centralized requirement tracking
- Real-time collaboration features
- Role-based access control
- Advanced compliance and audit trails
- Custom requirement types and workflows

## Success Criteria (MVP)

The MVP will be considered successful if:

1. **It works locally**: A developer can install via pip and use all commands on Linux without any external services.

2. **It integrates with LLMs**: Claude Code can detect `.contextgit/config.yaml` and use CLI commands to manage requirements.

3. **It detects staleness**: The tool correctly identifies when requirements change and marks downstream artifacts as needing updates.

4. **It stays git-friendly**: The index file produces clean, reviewable diffs when committed.

5. **It extracts context efficiently**: LLMs can extract specific requirement snippets without loading entire documents.

6. **It's usable by developers**: Documentation is clear enough that a developer can set up and use the tool in under 15 minutes.

7. **It's open-source ready**: The project has a clear license, README, and example demonstrating the workflow.
