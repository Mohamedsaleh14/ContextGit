# RelevantHandler Implementation

## Overview

The `RelevantHandler` implements the `contextgit relevant-for-file` command, which finds all requirements relevant to a specific source file. This is a critical command for LLM integration, allowing Claude Code and similar tools to discover related requirements when working on code.

## Purpose

When implementing a feature or fixing a bug in a source file, developers and LLMs need to know:
- What requirements does this file implement?
- What are the upstream requirements that led to this code?
- What is the full traceability chain from business requirements to code?

The `relevant-for-file` command answers these questions by:
1. Finding all nodes (requirements, architecture, code, tests) that reference the file
2. Traversing upstream links to discover related requirements
3. Organizing results by distance for easy understanding

## Implementation Details

### Core Algorithm

The handler uses a breadth-first search (BFS) algorithm to traverse the traceability graph:

1. **File matching**: Find all nodes where `node.file == file_path`
2. **Distance calculation**: Use BFS to calculate the shortest distance from each file node to upstream requirements
3. **Deduplication**: Track nodes with their minimum distance (in case multiple paths exist)
4. **Sorting**: Sort results by distance (closest first) for clear presentation

### Key Features

- **Configurable depth**: Control how many levels upstream to traverse (default: 3)
- **Distance tracking**: Each node is tagged with its distance from the file
- **Dual format support**: Text (human-readable) and JSON (LLM-friendly) output
- **Path normalization**: Converts absolute paths to relative paths automatically
- **Multiple nodes per file**: Handles cases where multiple requirements reference the same file

### Performance

Per requirements in `docs/03_system_requirements.md`:
- **Target**: < 200ms for LLM-invoked commands (NFR-7.4)
- **Optimization**: BFS with early termination at max depth
- **Caching**: Index is loaded once and cached by IndexManager

## Usage Examples

### Command Line

```bash
# Find all relevant requirements for a file
contextgit relevant-for-file src/logging/api.py

# Limit depth to 1 level upstream
contextgit relevant-for-file src/logging/api.py --depth 1

# Get JSON output for LLM consumption
contextgit relevant-for-file src/logging/api.py --format json
```

### Text Output Format

```
Requirements relevant to src/logging/api.py:

Direct:
  C-120: "LoggingAPIHandler class" (code)

Upstream (1 level):
  AR-020: "REST API design for logging" (architecture)

Upstream (2 levels):
  SR-010: "System shall expose job execution logs via API" (system)

Upstream (3 levels):
  BR-001: "Scheduled jobs must be observable" (business)
```

### JSON Output Format

```json
{
  "file": "src/logging/api.py",
  "nodes": [
    {
      "id": "C-120",
      "type": "code",
      "title": "LoggingAPIHandler class",
      "file": "docs/03_architecture/api_design.md",
      "distance": 0
    },
    {
      "id": "AR-020",
      "type": "architecture",
      "title": "REST API design for logging",
      "file": "docs/03_architecture/api_design.md",
      "distance": 1
    },
    {
      "id": "SR-010",
      "type": "system",
      "title": "System shall expose job execution logs via API",
      "file": "docs/02_system/logging_api.md",
      "distance": 2
    },
    {
      "id": "BR-001",
      "type": "business",
      "title": "Scheduled jobs must be observable",
      "file": "docs/01_business/observability.md",
      "distance": 3
    }
  ]
}
```

## Integration with Claude Code

### Detection Pattern

Claude Code should use this command when:
1. User asks "what requirements apply to this file?"
2. Implementing a new feature in an existing file
3. Understanding the context before making changes
4. Generating documentation that needs requirement references

### Recommended Workflow

```python
# 1. Find relevant requirements
result = subprocess.run([
    "contextgit", "relevant-for-file", file_path,
    "--format", "json"
], capture_output=True, text=True)

data = json.loads(result.stdout)

# 2. Extract full context for each requirement
for node in data["nodes"]:
    extract_result = subprocess.run([
        "contextgit", "extract", node["id"],
        "--format", "json"
    ], capture_output=True, text=True)

    requirement_context = json.loads(extract_result.stdout)
    # Use requirement_context in prompt to LLM
```

## Error Handling

### Not in Repository

```
Error: Not in a contextgit repository. Run 'contextgit init' first.
Exit code: 1
```

### No Nodes Found

Text format:
```
Info: No requirements found for src/unknown/file.py
Exit code: 0
```

JSON format:
```json
{
  "file": "src/unknown/file.py",
  "nodes": []
}
Exit code: 0
```

Note: No nodes found is NOT an error - it exits with code 0.

## Implementation Classes

### RelevantHandler

Main handler class that:
- Inherits from `BaseHandler` for common functionality
- Loads the index via `IndexManager`
- Uses `LinkingEngine.get_upstream_nodes()` for graph traversal
- Implements custom BFS for accurate distance calculation
- Formats output in both text and JSON formats

### Key Methods

#### `handle(file_path, depth, format) -> str`
Main entry point that orchestrates the entire operation.

#### `_calculate_distances(index, start_node_id, max_depth, nodes_with_distance)`
BFS implementation to calculate shortest distance to each upstream node.

#### `_format_json(file_path, sorted_nodes) -> str`
Formats results as JSON with file, nodes array containing id, type, title, file, distance.

#### `_format_text(file_path, sorted_nodes) -> str`
Formats results as human-readable text grouped by distance levels.

## Testing

Comprehensive unit tests in `tests/unit/handlers/test_relevant_handler.py` cover:

- ✅ Finding requirements with full traceability chain
- ✅ Depth limiting (depth 0, 1, 2, 3, etc.)
- ✅ JSON output format validation
- ✅ Text output format and grouping
- ✅ No matches found scenarios
- ✅ Not in repository error handling
- ✅ Absolute path normalization
- ✅ Multiple nodes per file handling
- ✅ Distance calculation correctness

## Related Commands

- `contextgit show <ID>`: Display details for a specific node
- `contextgit extract <ID>`: Extract snippet for a node (use after relevant-for-file)
- `contextgit status --stale`: Find nodes with broken traceability
- `contextgit scan`: Update index after file changes

## Requirements Satisfied

This implementation satisfies:

- **FR-11**: Relevant requirements for source files
  - FR-11.1: Provides `contextgit relevant-for-file <path>` command
  - FR-11.2: Traverses upstream links with configurable depth
  - FR-11.3: Outputs sorted list by distance
  - FR-11.4: JSON output support

- **NFR-7**: LLM Integration
  - NFR-7.4: Performance target < 200ms
  - NFR-7.2: JSON output for all read operations

## Future Enhancements (Post-MVP)

The following features are deferred to Phase 2+:

- Downstream traversal option (`--direction downstream`)
- Filter by node type (`--type business,system`)
- Include sync status in output
- Show link relation types in output
- Graph visualization of relationships
