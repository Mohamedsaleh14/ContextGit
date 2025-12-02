# Test Strategy Document

## 1. Introduction

### 1.1 Purpose
This document defines the comprehensive testing strategy for the contextgit project. It outlines testing principles, methodologies, tools, and quality assurance processes to ensure the system meets all functional and non-functional requirements.

### 1.2 Scope
This strategy covers:
- Unit testing (individual modules and classes)
- Integration testing (module interactions)
- End-to-end testing (complete user workflows)
- Performance testing (speed and scalability)
- Reliability testing (error handling and data integrity)
- Security testing (input validation and path traversal)

### 1.3 Testing Objectives
1. **Correctness**: Verify all functional requirements (FR-1 through FR-13)
2. **Reliability**: Ensure NFR-2 compliance (never corrupt index, atomic operations)
3. **Performance**: Meet NFR-1 targets (extract < 100ms, scan < 5s for 1000 files)
4. **Usability**: Validate clear error messages and CLI conventions
5. **Compatibility**: Test on Python 3.11, 3.12, 3.13 and primary platforms

---

## 2. Testing Levels

### 2.1 Unit Testing

**Definition**: Test individual modules, classes, and functions in isolation.

**Scope**:
- All domain layer modules (IndexManager, MetadataParser, LocationResolver, etc.)
- All infrastructure layer modules (FileSystem, YAMLSerializer, OutputFormatter)
- Data model validation (Node, Link, Index, Config)

**Approach**:
- Use pytest as testing framework
- Mock external dependencies (filesystem, YAML I/O)
- Test both happy paths and error conditions
- Achieve minimum 90% code coverage

**Mock Strategy**:
```python
# Example: Test IndexManager with mocked filesystem
def test_index_manager_load(tmp_path, mock_yaml):
    # Mock filesystem
    mock_fs = MockFileSystem(tmp_path)

    # Create test index file
    test_data = {...}
    mock_yaml.dump_yaml(test_data)

    # Test
    manager = IndexManager(mock_fs, mock_yaml, str(tmp_path))
    index = manager.load_index()

    assert len(index.nodes) == 3
```

**Coverage Requirements**:
- Domain modules: ≥ 95% coverage
- Infrastructure modules: ≥ 90% coverage
- Handlers: ≥ 85% coverage
- Data models: 100% coverage

---

### 2.2 Integration Testing

**Definition**: Test interactions between multiple modules.

**Scope**:
- Handler workflows (ScanHandler orchestrating multiple domain modules)
- Domain module interactions (MetadataParser → LocationResolver → SnippetExtractor)
- Infrastructure integration (FileSystem + YAMLSerializer)

**Approach**:
- Use real filesystem with temporary directories (pytest tmp_path fixture)
- Test complete workflows end-to-end within application layer
- Verify data flows correctly between modules
- Test error propagation and handling

**Key Integration Test Scenarios**:
1. **Scan Workflow**: Parse metadata → resolve location → extract snippet → calculate checksum → update index
2. **Extract Workflow**: Load index → get node → extract snippet → format output
3. **Linking Workflow**: Parse metadata → build links → update sync status
4. **Status Workflow**: Load index → analyze graph → detect orphans → format output

**Example**:
```python
def test_scan_integration(sample_repo):
    """Test complete scan workflow with real files."""
    # Setup
    repo_root = sample_repo  # Fixture creates temp repo with sample files

    # Execute scan
    handler = ScanHandler(FileSystem(), YAMLSerializer(), OutputFormatter())
    result = handler.handle(
        path=str(repo_root / "docs"),
        recursive=True,
        dry_run=False,
        format="json"
    )

    # Verify
    data = json.loads(result)
    assert data['files_scanned'] > 0
    assert len(data['nodes']['added']) > 0

    # Verify index was actually saved
    index_path = repo_root / ".contextgit" / "requirements_index.yaml"
    assert index_path.exists()
```

---

### 2.3 End-to-End Testing

**Definition**: Test complete user workflows via CLI interface.

**Scope**:
- All CLI commands (init, scan, status, show, extract, link, confirm, next-id, relevant-for-file, fmt)
- Multi-command workflows
- Error scenarios and edge cases

**Approach**:
- Use Typer's CliRunner for CLI testing
- Create realistic test repositories with sample files
- Verify command output, exit codes, and file system changes
- Test both text and JSON output formats

**Key E2E Test Scenarios**:
1. **Initialize new project**: `contextgit init` → verify .contextgit/ created
2. **First scan**: `contextgit scan docs/ --recursive` → verify nodes/links created
3. **Extract requirement**: `contextgit extract SR-010` → verify correct snippet
4. **Detect staleness**: Modify file → scan → verify sync status updated
5. **Confirm sync**: `contextgit confirm SR-010` → verify links marked OK
6. **Full workflow**: init → scan → show → extract → link → status

**Example**:
```python
def test_cli_full_workflow(cli_runner, sample_repo):
    """Test complete user workflow from init to extract."""
    os.chdir(sample_repo)

    # Init
    result = cli_runner.invoke(app, ["init"])
    assert result.exit_code == 0
    assert ".contextgit/config.yaml exists"

    # Scan
    result = cli_runner.invoke(app, ["scan", "docs", "--recursive"])
    assert result.exit_code == 0
    assert "Scanned" in result.stdout

    # Show
    result = cli_runner.invoke(app, ["show", "SR-010"])
    assert result.exit_code == 0
    assert "SR-010" in result.stdout

    # Extract
    result = cli_runner.invoke(app, ["extract", "SR-010"])
    assert result.exit_code == 0
    assert len(result.stdout) > 0
```

---

### 2.4 Performance Testing

**Definition**: Verify system meets performance requirements (NFR-1).

**Scope**:
- Command execution times
- Scalability with large datasets
- Memory usage

**Approach**:
- Use pytest-benchmark for timing measurements
- Create test datasets of varying sizes (100, 1000, 5000 nodes)
- Measure key operations against requirements
- Profile code to identify bottlenecks

**Performance Requirements** (from NFR-1):
| Operation | Target | Requirement |
|-----------|--------|-------------|
| Extract | < 100ms | NFR-1.3, FR-7.7 |
| Show | < 500ms | NFR-1.4 |
| Status | < 500ms | NFR-1.4 |
| Scan (1000 files) | < 5s | NFR-1.2 |
| Init | < 1s | FR-1.6 |

**Performance Test Template**:
```python
def test_extract_performance(benchmark, large_index):
    """Verify extract meets < 100ms requirement."""
    handler = ExtractHandler(...)

    def extract():
        return handler.handle(id="SR-010", format="text")

    result = benchmark(extract)

    # Verify < 100ms requirement
    assert result.stats.mean < 0.1  # 100ms
```

**Scalability Tests**:
```python
@pytest.mark.parametrize("num_nodes", [100, 1000, 5000])
def test_scan_scalability(num_nodes, benchmark):
    """Test scan performance with varying dataset sizes."""
    # Create test repo with num_nodes files
    repo = create_test_repo(num_nodes)

    handler = ScanHandler(...)

    def scan():
        return handler.handle(path=repo, recursive=True, ...)

    result = benchmark(scan)

    # Should scale linearly
    # 1000 nodes in < 5s means ~5ms per file
    expected_time = (num_nodes / 1000) * 5.0
    assert result.stats.mean < expected_time
```

---

### 2.5 Reliability Testing

**Definition**: Verify system reliability and data integrity (NFR-2).

**Scope**:
- Atomic file operations
- Error recovery
- Index corruption prevention
- Graceful degradation

**Approach**:
- Test atomic write behavior (simulate crashes)
- Test error handling for all exception types
- Verify index is never corrupted
- Test recovery from partial failures

**Key Reliability Test Scenarios**:
1. **Atomic Write**: Interrupt write operation → verify original index intact
2. **Corrupted Index**: Load malformed index → verify clear error message
3. **Missing Files**: Reference non-existent file → verify graceful handling
4. **Invalid Metadata**: Parse malformed metadata → verify warning, continue processing
5. **Concurrent Access**: Simulate conflicting changes → verify git merge resolution

**Example**:
```python
def test_atomic_write_crash_recovery(tmp_path):
    """Verify index not corrupted if write fails mid-operation."""
    # Setup: Create valid index
    index_path = tmp_path / ".contextgit" / "requirements_index.yaml"
    original_content = "nodes: []\nlinks: []\n"
    index_path.write_text(original_content)

    # Simulate write failure
    manager = IndexManager(fs, yaml, str(tmp_path))
    index = manager.load_index()
    index.nodes["SR-001"] = Node(...)

    # Mock filesystem to fail during write
    with patch.object(fs, 'write_file_atomic', side_effect=IOError("Disk full")):
        with pytest.raises(IOError):
            manager.save_index(index)

    # Verify original index intact
    content = index_path.read_text()
    assert content == original_content
```

---

### 2.6 Security Testing

**Definition**: Verify input validation and security constraints (NFR-8, C-2, C-3).

**Scope**:
- Path traversal prevention
- YAML injection prevention
- Input validation
- File access controls

**Approach**:
- Test malicious inputs (path traversal, YAML bombs)
- Verify all paths are validated
- Test input sanitization
- Verify safe YAML parsing

**Key Security Test Scenarios**:
1. **Path Traversal**: Attempt to access files outside repo → verify blocked
2. **YAML Injection**: Parse malicious YAML → verify safe_load prevents code execution
3. **Large Files**: Parse extremely large files → verify resource limits
4. **Special Characters**: Test IDs with special chars → verify validation

**Example**:
```python
def test_path_traversal_prevention(tmp_path):
    """Verify paths outside repo root are rejected."""
    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    fs = FileSystem()

    # Attempt to read file outside repo
    malicious_path = "../../../etc/passwd"

    with pytest.raises(SecurityError):
        fs.read_file(malicious_path)

def test_yaml_injection_prevention():
    """Verify YAML safe_load prevents code execution."""
    malicious_yaml = """
    !!python/object/apply:os.system
    args: ['rm -rf /']
    """

    yaml = YAMLSerializer()

    # Should raise error, not execute code
    with pytest.raises(yaml.YAMLError):
        yaml.load_yaml(malicious_yaml)
```

---

## 3. Testing Tools and Framework

### 3.1 Testing Framework

**Primary Framework**: pytest

**Rationale**:
- Industry standard for Python testing
- Rich plugin ecosystem
- Excellent fixture support
- Clear, readable test syntax
- Parameterized testing support

**Key Plugins**:
- `pytest-cov`: Code coverage reporting
- `pytest-benchmark`: Performance testing
- `pytest-xdist`: Parallel test execution
- `pytest-mock`: Mocking support
- `pytest-timeout`: Test timeout enforcement

### 3.2 Mocking and Fixtures

**Mocking Library**: unittest.mock (standard library)

**Common Fixtures**:
```python
@pytest.fixture
def tmp_repo(tmp_path):
    """Create temporary repository structure."""
    repo = tmp_path / "test_repo"
    repo.mkdir()
    (repo / ".contextgit").mkdir()
    (repo / "docs").mkdir()
    return repo

@pytest.fixture
def sample_index():
    """Create sample index with test data."""
    return Index(
        nodes={
            "SR-001": Node(...),
            "SR-002": Node(...),
        },
        links=[
            Link(from_id="SR-001", to_id="SR-002", ...),
        ]
    )

@pytest.fixture
def mock_filesystem():
    """Mock filesystem for unit tests."""
    return MockFileSystem()
```

### 3.3 Code Coverage

**Tool**: pytest-cov with coverage.py

**Target Coverage**:
- Overall project: ≥ 90%
- Critical modules (IndexManager, ChecksumCalculator): ≥ 95%
- CLI and handlers: ≥ 85%

**Coverage Report Format**:
- HTML report for local development
- XML report for CI/CD integration
- Terminal summary for quick checks

**Coverage Configuration** (`.coveragerc`):
```ini
[run]
source = contextgit
omit =
    */tests/*
    */test_*.py
    */__main__.py

[report]
precision = 2
show_missing = True
exclude_lines =
    pragma: no cover
    def __repr__
    raise AssertionError
    raise NotImplementedError
    if __name__ == .__main__.:
```

### 3.4 Performance Benchmarking

**Tool**: pytest-benchmark

**Metrics Tracked**:
- Mean execution time
- Standard deviation
- Min/max times
- Iterations per second

**Benchmark Configuration**:
```python
# pytest.ini
[tool:pytest]
benchmark_min_rounds = 5
benchmark_warmup = True
benchmark_disable_gc = True
```

---

## 4. Test Data Strategy

### 4.1 Test Fixtures and Sample Data

**Approach**:
- Create realistic sample repositories
- Use fixtures for reusable test data
- Separate fixture data from test logic

**Sample Repository Structure**:
```
tests/fixtures/sample_repo/
├── .contextgit/
│   ├── config.yaml
│   └── requirements_index.yaml
├── docs/
│   ├── 01_business/
│   │   └── observability.md
│   ├── 02_system/
│   │   └── logging_api.md
│   └── 03_architecture/
│       └── api_design.md
└── src/
    └── logging/
        └── api.py
```

**Fixture Categories**:
1. **Empty Repositories**: For init and first-scan tests
2. **Small Repositories**: 5-10 nodes, for quick integration tests
3. **Medium Repositories**: 100 nodes, for realistic scenarios
4. **Large Repositories**: 1000+ nodes, for performance/scalability tests

### 4.2 Test Data Generation

**Approach**:
- Create data generators for large datasets
- Use factories for creating test objects
- Parameterize tests with varying data sizes

**Example Factory**:
```python
class NodeFactory:
    """Factory for creating test nodes."""

    @staticmethod
    def create(
        id: str = "SR-001",
        type: NodeType = NodeType.SYSTEM,
        **kwargs
    ) -> Node:
        defaults = {
            'title': f"Test requirement {id}",
            'file': "docs/test.md",
            'location': HeadingLocation(path=["Section"]),
            'status': NodeStatus.ACTIVE,
            'last_updated': "2025-12-02T10:00:00Z",
            'checksum': "abc123" * 10 + "abcd",
        }
        defaults.update(kwargs)
        return Node(id=id, type=type, **defaults)

class IndexGenerator:
    """Generate large test indexes."""

    @staticmethod
    def generate(num_nodes: int) -> Index:
        nodes = {}
        links = []

        for i in range(num_nodes):
            node_id = f"SR-{i:03d}"
            nodes[node_id] = NodeFactory.create(id=node_id)

            # Create links to previous nodes
            if i > 0:
                prev_id = f"SR-{i-1:03d}"
                links.append(Link(
                    from_id=prev_id,
                    to_id=node_id,
                    relation_type=RelationType.REFINES,
                    sync_status=SyncStatus.OK,
                    last_checked="2025-12-02T10:00:00Z",
                ))

        return Index(nodes=nodes, links=links)
```

---

## 5. Test Organization

### 5.1 Directory Structure

```
tests/
├── unit/                       # Unit tests
│   ├── domain/
│   │   ├── test_index_manager.py
│   │   ├── test_metadata_parser.py
│   │   ├── test_location_resolver.py
│   │   ├── test_snippet_extractor.py
│   │   ├── test_linking_engine.py
│   │   ├── test_checksum_calculator.py
│   │   ├── test_id_generator.py
│   │   └── test_config_manager.py
│   ├── infra/
│   │   ├── test_filesystem.py
│   │   ├── test_yaml_io.py
│   │   └── test_output_formatter.py
│   └── models/
│       ├── test_node.py
│       ├── test_link.py
│       └── test_index.py
│
├── integration/                # Integration tests
│   ├── test_scan_workflow.py
│   ├── test_extract_workflow.py
│   ├── test_linking_workflow.py
│   └── test_status_workflow.py
│
├── e2e/                       # End-to-end CLI tests
│   ├── test_cli_init.py
│   ├── test_cli_scan.py
│   ├── test_cli_status.py
│   ├── test_cli_show.py
│   ├── test_cli_extract.py
│   ├── test_cli_link.py
│   ├── test_cli_confirm.py
│   ├── test_cli_next_id.py
│   ├── test_cli_relevant.py
│   ├── test_cli_fmt.py
│   └── test_full_workflows.py
│
├── performance/               # Performance tests
│   ├── test_extract_perf.py
│   ├── test_scan_perf.py
│   └── test_scalability.py
│
├── security/                  # Security tests
│   ├── test_path_validation.py
│   ├── test_yaml_safety.py
│   └── test_input_validation.py
│
├── fixtures/                  # Test fixtures
│   ├── sample_repo/
│   ├── factories.py
│   └── generators.py
│
└── conftest.py               # Shared fixtures and configuration
```

### 5.2 Test Naming Conventions

**Format**: `test_<unit>_<scenario>_<expected_result>`

**Examples**:
- `test_index_manager_load_empty_index_returns_empty_dict`
- `test_metadata_parser_parse_frontmatter_extracts_correct_fields`
- `test_checksum_calculator_normalize_text_removes_whitespace`
- `test_scan_handler_dry_run_does_not_modify_index`

---

## 6. Continuous Integration Strategy

### 6.1 CI/CD Pipeline

**Platform**: GitHub Actions (recommended) or GitLab CI

**Pipeline Stages**:
1. **Lint and Format**: Run ruff/black/mypy
2. **Unit Tests**: Run all unit tests with coverage
3. **Integration Tests**: Run integration tests
4. **E2E Tests**: Run end-to-end CLI tests
5. **Performance Tests**: Run performance benchmarks
6. **Coverage Report**: Generate and upload coverage report
7. **Build Package**: Build wheel and source distribution

**Example GitHub Actions Workflow**:
```yaml
name: Test Suite

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.11", "3.12", "3.13"]

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: ${{ matrix.python-version }}

      - name: Install dependencies
        run: |
          pip install -e ".[dev]"

      - name: Lint with ruff
        run: ruff check .

      - name: Type check with mypy
        run: mypy contextgit

      - name: Run unit tests
        run: pytest tests/unit/ -v --cov=contextgit --cov-report=xml

      - name: Run integration tests
        run: pytest tests/integration/ -v

      - name: Run E2E tests
        run: pytest tests/e2e/ -v

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
```

### 6.2 Pre-commit Hooks

**Tool**: pre-commit framework

**Hooks**:
- `ruff`: Linting
- `black`: Code formatting
- `mypy`: Type checking
- `pytest`: Run fast unit tests (< 5s)

**Configuration** (`.pre-commit-config.yaml`):
```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.0
    hooks:
      - id: ruff
        args: [--fix]

  - repo: https://github.com/psf/black
    rev: 23.11.0
    hooks:
      - id: black

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.7.0
    hooks:
      - id: mypy
        additional_dependencies: [types-all]

  - repo: local
    hooks:
      - id: pytest-quick
        name: pytest-quick
        entry: pytest tests/unit/ -m "not slow"
        language: system
        pass_filenames: false
```

---

## 7. Quality Metrics and Acceptance Criteria

### 7.1 Code Coverage Targets

| Component | Target Coverage |
|-----------|----------------|
| Overall Project | ≥ 90% |
| Domain Layer | ≥ 95% |
| Infrastructure Layer | ≥ 90% |
| Handlers | ≥ 85% |
| Data Models | 100% |
| CLI Commands | ≥ 80% |

### 7.2 Test Execution Time Targets

| Test Suite | Max Duration |
|------------|--------------|
| Unit Tests | < 30 seconds |
| Integration Tests | < 2 minutes |
| E2E Tests | < 5 minutes |
| Full Suite | < 10 minutes |

### 7.3 Quality Gates

**Before merging to main**:
- ✅ All tests pass (100% pass rate)
- ✅ Coverage ≥ 90%
- ✅ No critical or high-severity linting errors
- ✅ Type checking passes (mypy)
- ✅ Performance tests meet requirements
- ✅ All user stories have corresponding E2E tests

---

## 8. Testing Best Practices

### 8.1 Test Design Principles

1. **Arrange-Act-Assert (AAA) Pattern**:
   ```python
   def test_example():
       # Arrange: Set up test data and conditions
       index = Index()
       node = Node(...)

       # Act: Execute the code under test
       index.nodes[node.id] = node

       # Assert: Verify the expected outcome
       assert node.id in index.nodes
   ```

2. **One Assertion Per Test** (when practical):
   - Focus on single behavior
   - Make failures easy to diagnose

3. **Test Independence**:
   - Tests should not depend on each other
   - Use fixtures for setup, not previous test results

4. **Descriptive Test Names**:
   - Names should describe what is being tested
   - Include expected behavior
   - Easy to understand from test report

5. **Avoid Test Duplication**:
   - Use parameterized tests for similar scenarios
   - Extract common setup to fixtures

### 8.2 Common Patterns

**Parameterized Testing**:
```python
@pytest.mark.parametrize("node_type,expected_prefix", [
    ("business", "BR-"),
    ("system", "SR-"),
    ("architecture", "AR-"),
])
def test_id_generator_prefixes(node_type, expected_prefix):
    config = Config.get_default()
    assert config.tag_prefixes[node_type] == expected_prefix
```

**Exception Testing**:
```python
def test_index_manager_get_nonexistent_node_raises_error():
    manager = IndexManager(...)

    with pytest.raises(NodeNotFoundError) as exc_info:
        manager.get_node("INVALID-001")

    assert "Node not found" in str(exc_info.value)
```

**Fixture Composition**:
```python
@pytest.fixture
def filesystem():
    return FileSystem()

@pytest.fixture
def yaml_io():
    return YAMLSerializer()

@pytest.fixture
def index_manager(filesystem, yaml_io, tmp_path):
    return IndexManager(filesystem, yaml_io, str(tmp_path))
```

---

## 9. Test Maintenance

### 9.1 Test Review Process

**Review Criteria**:
- Tests are clear and well-documented
- Tests follow naming conventions
- Tests are independent and repeatable
- Tests cover both happy paths and edge cases
- No flaky tests (intermittent failures)

### 9.2 Test Refactoring

**When to Refactor**:
- Test code is duplicated
- Tests are hard to understand
- Tests are slow (can be optimized)
- Tests are flaky (need better isolation)

**Refactoring Techniques**:
- Extract common setup to fixtures
- Use helper functions for complex assertions
- Parameterize similar tests
- Mock expensive operations

### 9.3 Dealing with Flaky Tests

**Identification**:
- Tests that pass/fail intermittently
- Tests that depend on timing or external state

**Resolution**:
- Add better isolation (reset state between tests)
- Mock time-dependent operations
- Increase timeouts if needed
- Fix race conditions

---

## 10. Acceptance Testing

### 10.1 User Story Validation

**Approach**: Each user story in `docs/02_user_stories.md` must have corresponding E2E tests.

**Mapping**:
- Story 1 (Initialize project) → `test_cli_init.py`
- Story 4 (Create linked requirements) → `test_full_workflows.py::test_create_linked_requirements`
- Story 6 (Detect upstream changes) → `test_full_workflows.py::test_detect_upstream_changes`
- Story 7 (Find requirements for file) → `test_cli_relevant.py`
- Story 10 (CI staleness check) → `test_full_workflows.py::test_ci_staleness_check`

### 10.2 Requirements Traceability

**Approach**: Map test cases to requirements (FR/NFR).

**Traceability Matrix** (sample):
| Requirement | Test Case(s) |
|-------------|-------------|
| FR-1: Project Init | `test_cli_init_creates_files` |
| FR-3: File Scanning | `test_scan_workflow_*` |
| FR-7: Context Extraction | `test_extract_workflow_*`, `test_extract_perf` |
| NFR-1.3: Extract < 100ms | `test_extract_performance` |
| NFR-2.1: Never corrupt index | `test_atomic_write_crash_recovery` |

---

## 11. Summary

This test strategy provides:

1. **Comprehensive Coverage**: Unit, integration, E2E, performance, security tests
2. **Clear Metrics**: Coverage targets, performance requirements, quality gates
3. **Proven Tools**: pytest, pytest-cov, pytest-benchmark
4. **Best Practices**: AAA pattern, test independence, descriptive names
5. **CI/CD Integration**: Automated testing in pipeline
6. **Traceability**: Tests mapped to requirements and user stories

The strategy ensures contextgit meets all functional and non-functional requirements with high quality, reliability, and maintainability.
