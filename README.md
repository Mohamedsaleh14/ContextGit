# contextgit

[![PyPI version](https://img.shields.io/pypi/v/contextgit.svg)](https://pypi.org/project/contextgit/)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](http://makeapullrequest.com)
[![Website](https://img.shields.io/badge/website-contextgit.com-blue)](https://contextgit.com)

**Requirements traceability for LLM-assisted software development**

🌐 **Official Website**: [contextgit.com](https://contextgit.com)

contextgit is a local-first, git-friendly CLI tool that maintains bidirectional traceability between business requirements, system specifications, architecture decisions, source code, and tests. Designed specifically for integration with Claude Code and similar LLM development assistants.

## Why contextgit?

Traditional requirement management is slow and manual. contextgit makes it **1,355× faster** with:

- 🔍 **Instant requirement searches** (12.5 min → 0.5 sec)
- 🔗 **Automatic staleness detection** (prevents $1,200-2,000 rework per incident)
- 📊 **94% context reduction** for LLM prompts (6,000 → 375 tokens)
- ⚡ **5-10× faster PR reviews** with structured metadata
- 💰 **Time savings**: Sub-second searches vs 12+ minutes manual ([see methodology](PERFORMANCE_EVALUATION.md#real-world-value-assessment))

> *Based on real-world measurements from dogfooding contextgit on itself.*

---

## Features

✨ **Core Capabilities**
- **Traceability Graph**: Track relationships from business needs → system specs → architecture → code → tests
- **Staleness Detection**: Automatically detect when upstream requirements change via checksum comparison
- **Precise Context Extraction**: Extract only relevant requirements for LLM consumption
- **Bidirectional Links**: Automatically maintain upstream/downstream relationships

🎯 **LLM-Optimized**
- JSON output for all commands (`--format json`)
- Sub-second requirement searches
- Extract command for precise context snippets
- Designed for Claude Code workflows

🛠️ **Developer-Friendly**
- **Git-Friendly**: Metadata in Markdown YAML frontmatter and HTML comments
- **Local-First**: All data in `.contextgit/requirements_index.yaml` - no network calls
- **Deterministic Output**: Sorted YAML for clean git diffs
- **Atomic Operations**: Never corrupts index file

---

## Installation

### Option 1: PyPI (Recommended)

```bash
pip install contextgit
```

### Option 2: From Source

```bash
git clone https://github.com/Mohamedsaleh14/ContextGit.git
cd ContextGit
pip install -e .
```

### Option 3: Ubuntu/Debian Package

```bash
# Download the .deb package from releases
wget https://github.com/Mohamedsaleh14/ContextGit/releases/download/v1.1.0/contextgit_1.1.0_all.deb

# Install
sudo dpkg -i contextgit_1.1.0_all.deb
```

### Verify Installation

```bash
contextgit --help
```

---

## Quick Start

```bash
# 1. Initialize a contextgit repository (with LLM integration)
contextgit init --setup-llm

# This creates:
# - .contextgit/config.yaml
# - .contextgit/requirements_index.yaml
# - .contextgit/LLM_INSTRUCTIONS.md  ← LLM reads this
# - .cursorrules                      ← Cursor auto-detects
# - CLAUDE.md                         ← Claude Code auto-detects

# 2. Add metadata to your Markdown files
cat > docs/requirements.md << 'EOF'
---
contextgit:
  id: auto
  type: business
  title: User authentication
  status: active
---

# User Authentication

Users must be able to log in with email and password.
EOF

# 3. Scan files to build the index
contextgit scan docs/ --recursive

# 4. Check repository status
contextgit status

# 5. View requirement details
contextgit show BR-001

# 6. Extract requirement text for LLM
contextgit extract BR-001
```

**Next Steps**: See the [User Guide](USER_GUIDE.md) for complete workflows and examples.

---

## Core Commands

### Initialization and Scanning

```bash
contextgit init                      # Initialize repository
contextgit init --setup-llm          # Initialize + create LLM integration files
contextgit scan docs/ --recursive    # Scan for metadata
contextgit scan --dry-run            # Preview changes
```

### Querying and Inspection

```bash
contextgit status                    # Show project health
contextgit status --stale            # Show stale requirements
contextgit show SR-010               # Show node details
contextgit extract SR-010            # Extract requirement text
contextgit relevant-for-file src/auth.py  # Find related requirements
```

### Linking and Synchronization

```bash
contextgit link BR-001 SR-010 --type refines  # Create manual link
contextgit confirm SR-010                     # Mark as synchronized
```

### Utilities

```bash
contextgit next-id system            # Generate next ID (SR-001)
contextgit fmt                       # Format index for git
contextgit show SR-010 --format json # JSON output for LLMs
```

---

## Metadata Format

contextgit supports two metadata formats in Markdown files:

### YAML Frontmatter (Recommended)

```markdown
---
contextgit:
  id: auto
  type: system
  title: User authentication system
  status: active
  upstream: [BR-001]
  downstream: [AR-005, C-020]
  tags: [security, auth]
---

# System Requirement: User Authentication

The system shall provide secure user authentication...
```

### HTML Comments (Inline)

```markdown
<!-- contextgit
id: auto
type: system
title: User authentication system
status: active
upstream: [BR-001]
-->

## User Authentication

The system shall provide secure user authentication...
```

---

## Node Types and Prefixes

| Type | Prefix | Purpose |
|------|--------|---------|
| `business` | BR- | Business requirements, user needs |
| `system` | SR- | System-level functional specs |
| `architecture` | AR- | Architecture decisions, ADRs |
| `code` | C- | Code implementation notes |
| `test` | T- | Test specifications |
| `decision` | ADR- | Design decisions |

---

## LLM Integration (Cursor & Claude Code)

contextgit is designed for seamless integration with LLM development tools.

### Automatic Setup (Recommended)

```bash
contextgit init --setup-llm
```

This creates all LLM integration files automatically:

| File | Purpose |
|------|---------|
| `.contextgit/LLM_INSTRUCTIONS.md` | Comprehensive guide for any LLM (~5KB) |
| `.cursorrules` | Cursor IDE auto-detection |
| `CLAUDE.md` | Claude Code auto-detection |

**How it works:**
1. Cursor reads `.cursorrules` → knows to use contextgit
2. Claude reads `CLAUDE.md` → knows to use contextgit
3. Both are directed to `LLM_INSTRUCTIONS.md` for full details

### Common Commands

```bash
# Get precise context for implementing a requirement
contextgit extract SR-010 --format json

# Find all requirements affecting a file
contextgit relevant-for-file src/auth.py --format json

# Check for stale requirements before making changes
contextgit status --stale

# After updating code, rescan and confirm synchronization
contextgit scan src/ --recursive
contextgit confirm SR-010
```

All commands support `--format json` for easy parsing by LLMs.

**See**: [User Guide - LLM Integration](USER_GUIDE.md#llm-integration) | [LLM Integration Guidelines](docs/07_llm_integration_guidelines.md)

---

## Real-World Performance

Based on [objective measurements](PERFORMANCE_EVALUATION.md#real-world-value-assessment) from dogfooding:

| Metric | Manual | With contextgit | Improvement |
|--------|--------|-----------------|-------------|
| Requirement search | 12.5 min | 0.55 sec | **1,355× faster** |
| Staleness detection | 30-60 min | <1 sec | **1,800-3,600× faster** |
| PR review time | 3-5 min | 30-60 sec | **5-10× faster** |
| Context extraction | Manual copy | Automated | **14-29 min saved/task** |

**Verified Benefits**: 87-90% token reduction, sub-second requirement searches

**See**: [Full Performance Evaluation](PERFORMANCE_EVALUATION.md) *(includes methodology and assumptions)*

---

## Documentation

### Getting Started
- 📖 [User Guide](USER_GUIDE.md) - Complete guide with workflows and examples
- 🚀 [Quick Start](#quick-start) - Get up and running in 5 minutes
- 💡 [LLM Integration](docs/07_llm_integration_guidelines.md) - Using with Claude Code

### Design Documents
- [Product Overview](docs/01_product_overview.md) - Vision and problem statement
- [User Stories](docs/02_user_stories.md) - Detailed usage scenarios
- [System Requirements](docs/03_system_requirements.md) - Functional requirements
- [Architecture](docs/04_architecture_overview.md) - System design
- [Data Model](docs/05_data_model_and_file_layout.md) - Schemas and file formats
- [CLI Specification](docs/06_cli_specification.md) - Command reference
- [MVP Scope](docs/08_mvp_scope_and_future_work.md) - Current and planned features

### Implementation
- [Performance Evaluation](PERFORMANCE_EVALUATION.md) - Real-world measurements and ROI
- [Implementation Complete](IMPLEMENTATION_COMPLETE.md) - Architecture and modules

---

## Requirements

- **Python**: 3.11 or higher
- **Dependencies**:
  - `typer` >= 0.9.0 (CLI framework)
  - `rich` >= 13.0.0 (terminal output)
  - `ruamel.yaml` >= 0.18.0 (YAML handling)

---

## Development

```bash
# Clone repository
git clone https://github.com/Mohamedsaleh14/ContextGit.git
cd ContextGit

# Install in development mode
pip install -e .

# Run import validation
python3 test_imports.py

# Run system verification
python3 verify_system.py

# Check CLI help
python3 -m contextgit --help
```

### Project Structure

```
contextgit/
├── cli/          # Typer command definitions
├── handlers/     # Command handlers (InitHandler, ScanHandler, etc.)
├── domain/       # Core domain (IndexManager, MetadataParser, LinkingEngine, etc.)
├── infra/        # Infrastructure (FileSystem, YAMLSerializer, OutputFormatter)
└── models/       # Data models (Node, Link, Index, Config)
```

**Architecture**: 4-layer design (CLI → Handlers → Domain → Infrastructure)

---

## Contributing

Contributions are welcome! This is an MVP with many opportunities for enhancement.

### How to Contribute

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes with clear commit messages
4. Push to your fork (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Areas for Contribution

- Performance optimization (daemon mode, lazy loading)
- Additional metadata formats (ReStructuredText, AsciiDoc)
- VS Code extension
- Watch mode for auto-scanning
- Code-level parsing (auto-link Python functions to requirements)
- CI/CD integrations

**See**: [MVP Scope and Future Work](docs/08_mvp_scope_and_future_work.md)

---

## Roadmap

### Phase 1: MVP ✅ (Complete)
- All 10 CLI commands
- Metadata parsing (YAML frontmatter + HTML comments)
- Traceability graph with staleness detection
- JSON output for LLM integration
- Git-friendly YAML output

### Phase 2: Enhanced Tooling (Planned)
- VS Code extension
- Daemon mode for performance
- Watch mode for auto-scanning
- Additional file format support
- Parallel file scanning

### Phase 3: Team Collaboration (Future)
- Git hooks for enforcement
- CI integration for blocking stale PRs
- Diff reports between branches
- Team analytics

**See**: [Full Roadmap](docs/08_mvp_scope_and_future_work.md)

---

## License

MIT License - see [LICENSE](LICENSE) file for details.

---

## Support This Project

If you find contextgit useful, consider supporting its development:

<a href="https://buymeacoffee.com/saleh_tawfik" target="_blank">
  <img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="Buy Me A Coffee" style="height: 60px !important;width: 217px !important;" >
</a>

Your support helps maintain and improve contextgit! ☕

---

## Author & More Projects

**Mohamed Saleh**

I build tools for developers. contextgit is one of several open-source projects I maintain.

🌐 **Visit my website**: [BySaleh.com](https://BySaleh.com)
- More open-source projects
- Technical blog posts
- Development tutorials
- Contact information

---

## Acknowledgments

- Built with [Typer](https://typer.tiangolo.com/) for CLI, [Rich](https://rich.readthedocs.io/) for terminal output
- Designed specifically for [Claude Code](https://claude.ai/code) integration
- Inspired by the need for better requirements traceability in LLM-assisted development

---

## Links

- **Official Website**: https://contextgit.com
- **PyPI**: https://pypi.org/project/contextgit/
- **Repository**: https://github.com/Mohamedsaleh14/ContextGit
- **Issues**: https://github.com/Mohamedsaleh14/ContextGit/issues
- **Releases**: https://github.com/Mohamedsaleh14/ContextGit/releases
- **User Guide**: [USER_GUIDE.md](USER_GUIDE.md)
- **Performance Evaluation**: [PERFORMANCE_EVALUATION.md](PERFORMANCE_EVALUATION.md)

---

## Star History

If you find this project useful, please consider giving it a ⭐ on GitHub!

[![Star History Chart](https://api.star-history.com/svg?repos=Mohamedsaleh14/ContextGit&type=Date)](https://star-history.com/#Mohamedsaleh14/ContextGit&Date)

---

<p align="center">Made with ❤️ by <a href="https://BySaleh.com">Mohamed Saleh</a></p>
<p align="center">
  <a href="https://BySaleh.com">Website</a> •
  <a href="https://github.com/Mohamedsaleh14">GitHub</a> •
  <a href="https://buymeacoffee.com/saleh_tawfik">Buy Me a Coffee</a>
</p>
