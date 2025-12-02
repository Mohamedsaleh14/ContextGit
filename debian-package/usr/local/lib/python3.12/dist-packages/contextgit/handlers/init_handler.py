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
from contextgit.constants import CONTEXTGIT_DIR


class InitHandler(BaseHandler):
    """Handler for contextgit init command.

    Initializes a contextgit project by creating:
    - .contextgit/ directory
    - .contextgit/config.yaml with default configuration
    - .contextgit/requirements_index.yaml with empty index
    """

    def handle(
        self,
        directory: str | None = None,
        force: bool = False,
        format: str = "text"
    ) -> str:
        """Initialize a contextgit project.

        Args:
            directory: Directory to initialize (default: current directory)
            force: Overwrite existing configuration if True
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

        # Format output
        if format == "json":
            return json.dumps({
                "status": "success",
                "directory": str(target_dir),
                "message": "Initialized contextgit repository"
            }, indent=2)
        else:
            config_path = contextgit_dir / "config.yaml"
            index_path = contextgit_dir / "requirements_index.yaml"
            return (
                f"Created {config_path}\n"
                f"Created {index_path}\n"
                f"Repository initialized for contextgit."
            )


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
    format: str = typer.Option(
        "text",
        "--format",
        help="Output format: text or json"
    ),
):
    """Initialize a contextgit project.

    Creates .contextgit/ directory with default configuration and empty index.
    """
    fs = FileSystem()
    yaml = YAMLSerializer()
    formatter = OutputFormatter()
    handler = InitHandler(fs, yaml, formatter)

    try:
        result = handler.handle(directory=directory, force=force, format=format)
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
