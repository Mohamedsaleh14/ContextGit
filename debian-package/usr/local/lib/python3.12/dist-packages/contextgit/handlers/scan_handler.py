"""Handler for contextgit scan command.

This module implements the ScanHandler, which is the most complex command handler.
It discovers metadata in Markdown files, creates/updates nodes, builds links, and
updates sync status.

Key Design Decisions:
--------------------
1. **ID Generation for 'auto' nodes**: When a metadata block has `id: auto`, we first
   check if a node with the same file and location already exists. If so, we reuse
   that ID. Otherwise, we generate a new sequential ID. This ensures that rescanning
   the same file doesn't create duplicate nodes.

2. **Link Preservation**: When doing partial scans (not --recursive), we preserve
   existing links that don't involve any of the scanned nodes. However, links
   involving scanned nodes are rebuilt from scratch based on the metadata.

   **Important**: Partial scans may lose some links if the referenced nodes aren't
   scanned. For example, if node A references node B in its upstream field, but you
   only scan file B (not A), the link A→B will be lost. Best practice is to always
   use `--recursive` for full project scans.

3. **Checksum Change Detection**: We calculate checksums of the extracted snippets
   (not the entire file) to detect content changes. When a checksum changes, we
   mark the node as updated and trigger sync status updates for all related links.

4. **Atomic Operations**: All index modifications are done in-memory and saved
   atomically at the end. If scanning fails partway through, the index is left
   unchanged (unless --dry-run is used, in which case nothing is saved anyway).
"""

import json
from pathlib import Path
from datetime import datetime, timezone
import typer

from contextgit.handlers.base import BaseHandler
from contextgit.infra.filesystem import FileSystem
from contextgit.infra.yaml_io import YAMLSerializer
from contextgit.infra.output import OutputFormatter
from contextgit.domain.index.manager import IndexManager
from contextgit.domain.config.manager import ConfigManager
from contextgit.domain.metadata.parser import MetadataParser
from contextgit.domain.location.resolver import LocationResolver
from contextgit.domain.location.snippet import SnippetExtractor
from contextgit.domain.checksum.calculator import ChecksumCalculator
from contextgit.domain.linking.engine import LinkingEngine
from contextgit.domain.id_gen.generator import IDGenerator
from contextgit.models.node import Node
from contextgit.models.enums import NodeType, NodeStatus
from contextgit.exceptions import InvalidMetadataError


class ScanHandler(BaseHandler):
    """Handler for contextgit scan command.

    The scan command discovers metadata blocks in Markdown files and updates
    the index accordingly. It performs the following operations:
    1. Scans specified files/directories for Markdown files
    2. Parses metadata blocks (frontmatter and inline HTML comments)
    3. Creates or updates nodes in the index
    4. Generates IDs for nodes marked with 'id: auto'
    5. Extracts content snippets and calculates checksums
    6. Builds traceability links from upstream/downstream fields
    7. Updates sync status for changed nodes
    """

    def handle(
        self,
        path: str | None = None,
        recursive: bool = False,
        dry_run: bool = False,
        format: str = "text"
    ) -> str:
        """
        Scan files for metadata and update index.

        Args:
            path: Path to scan (default: current directory)
            recursive: Scan recursively through subdirectories
            dry_run: Don't save changes to index
            format: Output format (text or json)

        Returns:
            Summary of scan results formatted according to format parameter

        Raises:
            RepoNotFoundError: If not in a contextgit repository
            InvalidMetadataError: If metadata is malformed
        """
        # Find repo root
        repo_root = self.find_repo_root()

        # Load config and index
        config_mgr = ConfigManager(self.fs, self.yaml, repo_root)
        config = config_mgr.load_config()

        index_mgr = IndexManager(self.fs, self.yaml, repo_root)
        index = index_mgr.load_index()

        # Determine scan path (default to repo root)
        if path:
            scan_path = Path(path).resolve()
            # Validate that path is within repo
            try:
                scan_path.relative_to(repo_root)
            except ValueError:
                # Path is outside repo, scan it anyway but warn
                pass
        else:
            scan_path = Path(repo_root)

        # Find all Markdown files
        files = list(self.fs.walk_files(str(scan_path), "*.md", recursive))

        # Initialize domain components
        metadata_parser = MetadataParser(self.fs)
        location_resolver = LocationResolver(self.fs)
        snippet_extractor = SnippetExtractor(self.fs)
        checksum_calc = ChecksumCalculator()
        linking_engine = LinkingEngine()
        id_gen = IDGenerator()

        # Track statistics
        nodes_added = []
        nodes_updated = []
        changed_nodes = set()
        metadata_map = {}  # node_id -> RawMetadata
        errors = []

        # Process each file
        for file_path in files:
            # Calculate relative path from repo root
            try:
                rel_path = str(Path(file_path).relative_to(repo_root))
            except ValueError:
                # File is outside repo, use absolute path
                rel_path = str(file_path)

            try:
                metadata_blocks = metadata_parser.parse_file(file_path)
            except InvalidMetadataError as e:
                errors.append(f"{rel_path}: {e}")
                continue
            except Exception as e:
                errors.append(f"{rel_path}: Unexpected error - {e}")
                continue

            # Process each metadata block in the file
            for metadata in metadata_blocks:
                try:
                    # Resolve location first (needed for finding existing nodes)
                    location = location_resolver.resolve_location(
                        file_path, metadata.line_number
                    )

                    # Extract snippet and calculate checksum
                    snippet = snippet_extractor.extract_snippet(file_path, location)
                    checksum = checksum_calc.calculate_checksum(snippet)

                    # Generate ID if auto
                    # If auto, first check if a node with same file+location exists
                    node_id = metadata.id
                    if node_id == "auto":
                        # Look for existing node with same file and location
                        existing_id = None
                        for existing_node_id, existing_node in index.nodes.items():
                            if (existing_node.file == rel_path and
                                existing_node.location == location):
                                existing_id = existing_node_id
                                break

                        if existing_id:
                            # Reuse existing ID
                            node_id = existing_id
                        else:
                            # Generate new ID
                            node_id = id_gen.next_id(metadata.type, index, config)

                    # Create timestamp
                    now = datetime.now(timezone.utc).isoformat()

                    # Create or update node
                    node = Node(
                        id=node_id,
                        type=NodeType(metadata.type),
                        title=metadata.title,
                        file=rel_path,
                        location=location,
                        status=NodeStatus(metadata.status),
                        last_updated=now,
                        checksum=checksum,
                        llm_generated=metadata.llm_generated,
                        tags=metadata.tags,
                    )

                    # Check if node exists
                    existing_node = index.nodes.get(node_id)
                    if existing_node:
                        # Check if checksum changed
                        if existing_node.checksum != checksum:
                            changed_nodes.add(node_id)
                            nodes_updated.append(node_id)
                        # Update node (even if checksum unchanged, other fields may have changed)
                        index.nodes[node_id] = node
                    else:
                        # New node
                        index.nodes[node_id] = node
                        nodes_added.append(node_id)

                    # Store metadata for linking phase
                    metadata_map[node_id] = metadata

                except Exception as e:
                    errors.append(f"{rel_path} (node {metadata.id}): {e}")
                    continue

        # Build links from metadata
        # Note: Link building requires scanning all files because links are bidirectional:
        # - A node can specify its upstream dependencies
        # - A node can specify its downstream dependencies
        # If we only scan a subset of files, we can't properly rebuild all links.
        #
        # For MVP simplicity, we rebuild ALL links from ALL scanned nodes.
        # This means partial scans will only update links for scanned nodes,
        # and may lose links from unscanned nodes.
        #
        # Best practice: Always use --recursive for full project scans.

        # Build new links from scanned nodes
        new_links = linking_engine.build_links_from_metadata(
            index.nodes, metadata_map
        )

        # Get node IDs that were scanned
        scanned_node_ids = set(metadata_map.keys())

        # Preserve existing links that don't involve any scanned nodes
        preserved_links = [
            link for link in index.links
            if link.from_id not in scanned_node_ids and link.to_id not in scanned_node_ids
        ]

        # Combine preserved and new links
        index.links = preserved_links + new_links

        # Update sync status for changed nodes
        linking_engine.update_sync_status(index, changed_nodes)

        # Save index (unless dry run)
        if not dry_run:
            index_mgr.save_index(index)

        # Format output
        summary = {
            'files_scanned': len(files),
            'nodes_added': len(nodes_added),
            'nodes_updated': len(nodes_updated),
            'errors': errors,
            'dry_run': dry_run,
        }

        if format == "json":
            return json.dumps(summary, indent=2)
        else:
            lines = [
                f"Scanned {len(files)} files",
                f"Added: {len(nodes_added)} nodes",
                f"Updated: {len(nodes_updated)} nodes",
            ]
            if errors:
                lines.append(f"Errors: {len(errors)}")
                for error in errors[:5]:  # Show first 5 errors
                    lines.append(f"  - {error}")
                if len(errors) > 5:
                    lines.append(f"  ... and {len(errors) - 5} more errors")
            if dry_run:
                lines.append("(dry run - no changes saved)")
            return '\n'.join(lines)


def scan_command(
    path: str = typer.Argument(
        None,
        help="Path to scan (default: current directory)"
    ),
    recursive: bool = typer.Option(
        False,
        "--recursive",
        "-r",
        help="Scan recursively through subdirectories"
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Don't save changes to index"
    ),
    format: str = typer.Option(
        "text",
        "--format",
        help="Output format: text or json"
    ),
):
    """Scan files for contextgit metadata and update index.

    Discovers metadata blocks in Markdown files, creates/updates nodes,
    generates IDs for 'auto' nodes, builds links, and updates sync status.

    Examples:
        # Scan current directory (non-recursive)
        contextgit scan

        # Scan specific directory recursively
        contextgit scan docs/ --recursive

        # Preview changes without saving
        contextgit scan --dry-run

        # Get JSON output for LLM consumption
        contextgit scan --format json
    """
    fs = FileSystem()
    yaml = YAMLSerializer()
    formatter = OutputFormatter()
    handler = ScanHandler(fs, yaml, formatter)

    try:
        result = handler.handle(
            path=path,
            recursive=recursive,
            dry_run=dry_run,
            format=format
        )
        typer.echo(result)
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=1)
