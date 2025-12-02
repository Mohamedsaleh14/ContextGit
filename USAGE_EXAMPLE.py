#!/usr/bin/env python3
"""Example usage of RelevantHandler.

This demonstrates how to programmatically use the RelevantHandler
to find requirements relevant to a source file.
"""

import json
from pathlib import Path

from contextgit.handlers.relevant_handler import RelevantHandler
from contextgit.infra.filesystem import FileSystem
from contextgit.infra.yaml_io import YAMLSerializer
from contextgit.infra.output import OutputFormatter


def example_text_output():
    """Example: Get text output for human consumption."""
    print("=" * 60)
    print("EXAMPLE 1: Text Output")
    print("=" * 60)

    # Initialize handler
    fs = FileSystem()
    yaml = YAMLSerializer()
    formatter = OutputFormatter()
    handler = RelevantHandler(fs, yaml, formatter)

    try:
        # Find relevant requirements (assumes you're in a contextgit repo)
        result = handler.handle(
            file_path="src/logging/api.py",
            depth=3,
            format="text"
        )
        print(result)
    except Exception as e:
        print(f"Error: {e}")


def example_json_output():
    """Example: Get JSON output for LLM consumption."""
    print("\n" + "=" * 60)
    print("EXAMPLE 2: JSON Output for LLMs")
    print("=" * 60)

    # Initialize handler
    fs = FileSystem()
    yaml = YAMLSerializer()
    formatter = OutputFormatter()
    handler = RelevantHandler(fs, yaml, formatter)

    try:
        # Find relevant requirements
        result = handler.handle(
            file_path="src/logging/api.py",
            depth=3,
            format="json"
        )

        # Parse JSON
        data = json.loads(result)

        print(f"File: {data['file']}")
        print(f"Found {len(data['nodes'])} relevant nodes:\n")

        # Display each node
        for node in data['nodes']:
            print(f"  [{node['distance']}] {node['id']}: {node['title']}")
            print(f"      Type: {node['type']}")
            print(f"      File: {node['file']}\n")

    except Exception as e:
        print(f"Error: {e}")


def example_limited_depth():
    """Example: Limit traversal depth."""
    print("=" * 60)
    print("EXAMPLE 3: Limited Depth (depth=1)")
    print("=" * 60)

    # Initialize handler
    fs = FileSystem()
    yaml = YAMLSerializer()
    formatter = OutputFormatter()
    handler = RelevantHandler(fs, yaml, formatter)

    try:
        # Only traverse 1 level upstream
        result = handler.handle(
            file_path="src/logging/api.py",
            depth=1,
            format="text"
        )
        print(result)
    except Exception as e:
        print(f"Error: {e}")


def example_llm_workflow():
    """Example: Complete LLM workflow."""
    print("\n" + "=" * 60)
    print("EXAMPLE 4: Complete LLM Workflow")
    print("=" * 60)

    # Initialize handler
    fs = FileSystem()
    yaml = YAMLSerializer()
    formatter = OutputFormatter()
    handler = RelevantHandler(fs, yaml, formatter)

    try:
        # Step 1: Find relevant requirements
        print("Step 1: Finding relevant requirements...")
        result = handler.handle(
            file_path="src/logging/api.py",
            depth=3,
            format="json"
        )

        data = json.loads(result)
        print(f"Found {len(data['nodes'])} nodes\n")

        # Step 2: For each requirement, you would typically:
        # - Use ExtractHandler to get the full text
        # - Build context for LLM
        # - Include in prompt
        print("Step 2: Next steps for LLM integration:")
        for node in data['nodes'][:3]:  # Show first 3
            print(f"  - Extract {node['id']}: contextgit extract {node['id']}")

        print("\nStep 3: Use extracted context in LLM prompt")

    except Exception as e:
        print(f"Error: {e}")


def example_error_handling():
    """Example: Error handling."""
    print("\n" + "=" * 60)
    print("EXAMPLE 5: Error Handling")
    print("=" * 60)

    # Initialize handler
    fs = FileSystem()
    yaml = YAMLSerializer()
    formatter = OutputFormatter()
    handler = RelevantHandler(fs, yaml, formatter)

    # Example 1: File with no nodes
    try:
        print("Case 1: File with no requirements...")
        result = handler.handle(
            file_path="src/unknown/file.py",
            depth=3,
            format="text"
        )
        print(result)
    except Exception as e:
        print(f"Error: {e}")

    # Example 2: Not in repository
    print("\nCase 2: Not in repository...")
    print("(Would raise RepoNotFoundError if not in a contextgit repo)")


if __name__ == "__main__":
    """
    Run examples (requires being in a contextgit repository with data).

    To test:
    1. Initialize a contextgit repo: contextgit init
    2. Create some requirements with file references
    3. Run: python3 USAGE_EXAMPLE.py
    """
    print("\n" + "=" * 60)
    print("RelevantHandler Usage Examples")
    print("=" * 60)
    print("\nNOTE: These examples require a contextgit repository with data.")
    print("Initialize with: contextgit init")
    print("=" * 60 + "\n")

    # Run examples
    example_text_output()
    example_json_output()
    example_limited_depth()
    example_llm_workflow()
    example_error_handling()

    print("\n" + "=" * 60)
    print("Examples Complete")
    print("=" * 60)
