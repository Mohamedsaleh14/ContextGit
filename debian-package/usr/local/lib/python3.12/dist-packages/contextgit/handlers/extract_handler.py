"""Handler for contextgit extract command."""

from pathlib import Path
import typer

from contextgit.handlers.base import BaseHandler
from contextgit.infra.filesystem import FileSystem
from contextgit.infra.yaml_io import YAMLSerializer
from contextgit.infra.output import OutputFormatter
from contextgit.domain.index.manager import IndexManager
from contextgit.domain.location.snippet import SnippetExtractor
from contextgit.exceptions import NodeNotFoundError, RepoNotFoundError


class ExtractHandler(BaseHandler):
    """Handler for contextgit extract command.

    Extracts text snippets for requirements from their source files.
    This is the primary command for LLMs to get precise context, with a
    performance target of < 100ms (FR-7.7 requirement).
    """

    def handle(self, node_id: str, format: str = "text") -> str:
        """Extract snippet for a node.

        Args:
            node_id: Node ID to extract (e.g., "SR-010")
            format: Output format - "text" or "json"

        Returns:
            Extracted snippet formatted according to format parameter

        Raises:
            RepoNotFoundError: If not in a contextgit repository
            NodeNotFoundError: If node ID doesn't exist in index
            FileNotFoundError: If node's source file doesn't exist
            ValueError: If location specification is invalid
        """
        # Find repo root
        repo_root = self.find_repo_root()

        # Load index
        index_mgr = IndexManager(self.fs, self.yaml, repo_root)

        # Get node
        node = index_mgr.get_node(node_id)

        # Resolve absolute file path
        file_path = Path(repo_root) / node.file

        # Extract snippet
        extractor = SnippetExtractor(self.fs)
        snippet = extractor.extract_snippet(str(file_path), node.location)

        # Format output using the OutputFormatter
        return self.formatter.format_extract_result(node, snippet, format)


def extract_command(
    node_id: str = typer.Argument(..., help="Node ID to extract (e.g., SR-010)"),
    format: str = typer.Option(
        "text",
        "--format",
        "-f",
        help="Output format: text or json"
    ),
):
    """Extract text snippet for a requirement (optimized for LLM consumption).

    This command extracts the precise text content for a requirement from its
    source file. In text mode, only the snippet is returned (ideal for piping
    to LLMs). In JSON mode, both node metadata and snippet are included.

    Examples:
        # Extract snippet as text
        contextgit extract SR-010

        # Extract with metadata as JSON
        contextgit extract SR-010 --format json

        # Pipe to file for LLM consumption
        contextgit extract SR-010 > /tmp/requirement.txt
    """
    fs = FileSystem()
    yaml = YAMLSerializer()
    formatter = OutputFormatter()
    handler = ExtractHandler(fs, yaml, formatter)

    try:
        result = handler.handle(node_id=node_id, format=format)
        typer.echo(result)
    except RepoNotFoundError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=1)
    except NodeNotFoundError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=3)
    except FileNotFoundError as e:
        typer.echo(f"Error: File not found - {e}", err=True)
        raise typer.Exit(code=3)
    except ValueError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=4)
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=1)
