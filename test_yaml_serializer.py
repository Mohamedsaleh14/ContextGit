#!/usr/bin/env python3
"""Quick test script for YAMLSerializer to verify deterministic output."""

import sys
from contextgit.infra.yaml_io import YAMLSerializer


def test_yaml_serializer():
    """Test YAMLSerializer with sample data."""
    serializer = YAMLSerializer()

    # Test data similar to contextgit index structure
    test_data = {
        "nodes": [
            {
                "id": "BR-001",
                "type": "business",
                "title": "User authentication",
                "file": "docs/requirements.md",
                "location": ["Requirements", "Authentication"],
                "status": "active",
                "checksum": "abc123def456",
            },
            {
                "id": "SR-001",
                "type": "system",
                "title": "JWT token implementation",
                "file": "docs/system-spec.md",
                "location": ["System Design", "Auth"],
                "status": "active",
                "checksum": "def456ghi789",
            },
        ],
        "links": [
            {
                "from": "SR-001",
                "to": "BR-001",
                "relation_type": "refines",
                "sync_status": "ok",
            }
        ],
    }

    # Test dump
    print("Testing dump_yaml()...")
    yaml_output = serializer.dump_yaml(test_data)
    print(yaml_output)
    print("-" * 80)

    # Test load
    print("Testing load_yaml()...")
    loaded_data = serializer.load_yaml(yaml_output)
    print(f"Loaded data keys: {loaded_data.keys()}")
    print(f"Number of nodes: {len(loaded_data['nodes'])}")
    print(f"Number of links: {len(loaded_data['links'])}")
    print("-" * 80)

    # Test determinism: dump twice and compare
    print("Testing determinism...")
    yaml_output_2 = serializer.dump_yaml(test_data)
    if yaml_output == yaml_output_2:
        print("✓ Output is deterministic (two dumps are identical)")
    else:
        print("✗ Output is NOT deterministic")
        return False

    # Verify key formatting properties
    print("\nVerifying formatting properties...")
    lines = yaml_output.split("\n")

    # Check no flow style (should have block style)
    has_flow_style = any("[" in line or "{" in line for line in lines if line.strip())
    if not has_flow_style:
        print("✓ Using block style (no flow style detected)")
    else:
        print("✗ Flow style detected (should use block style)")

    # Check indentation consistency
    indented_lines = [line for line in lines if line.startswith("  ") and line.strip()]
    if indented_lines:
        print(f"✓ Indentation detected in {len(indented_lines)} lines")
    else:
        print("✗ No indentation detected")

    print("\n" + "=" * 80)
    print("YAMLSerializer test completed successfully!")
    return True


if __name__ == "__main__":
    try:
        success = test_yaml_serializer()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
