"""Constants for contextgit."""

# File paths
CONTEXTGIT_DIR = ".contextgit"
INDEX_FILE = "requirements_index.yaml"
CONFIG_FILE = "config.yaml"
LLM_INSTRUCTIONS_FILE = "LLM_INSTRUCTIONS.md"

# LLM integration files (in project root)
CURSORRULES_FILE = ".cursorrules"
CLAUDE_MD_FILE = "CLAUDE.md"

# Performance limits
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
MAX_SNIPPET_SIZE = 1 * 1024 * 1024  # 1 MB

# Default values
DEFAULT_ID_PADDING = 3  # Zero-pad IDs to 3 digits (001, 002, etc.)
