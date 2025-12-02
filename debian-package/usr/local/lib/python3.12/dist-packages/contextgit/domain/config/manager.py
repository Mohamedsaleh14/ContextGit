"""Configuration management."""

from pathlib import Path

from contextgit.models.config import Config
from contextgit.infra.filesystem import FileSystem
from contextgit.infra.yaml_io import YAMLSerializer
from contextgit.exceptions import InvalidConfigError
from contextgit.constants import CONTEXTGIT_DIR, CONFIG_FILE


class ConfigManager:
    """Manages configuration loading and saving."""

    def __init__(
        self,
        filesystem: FileSystem,
        yaml_io: YAMLSerializer,
        repo_root: str
    ):
        """Initialize ConfigManager.

        Args:
            filesystem: File system abstraction
            yaml_io: YAML serialization handler
            repo_root: Repository root path
        """
        self.fs = filesystem
        self.yaml = yaml_io
        self.repo_root = Path(repo_root)
        self.config_path = self.repo_root / CONTEXTGIT_DIR / CONFIG_FILE

    def load_config(self) -> Config:
        """Load configuration from .contextgit/config.yaml.

        Returns default config if file doesn't exist.

        Returns:
            Config object

        Raises:
            InvalidConfigError: If config file is malformed
        """
        if not self.config_path.exists():
            # Return default config if file doesn't exist
            return Config.get_default()

        try:
            content = self.fs.read_file(str(self.config_path))
            data = self.yaml.load_yaml(content)
            return Config.from_dict(data)
        except Exception as e:
            raise InvalidConfigError(f"Failed to load config: {e}")

    def save_config(self, config: Config) -> None:
        """Save configuration to .contextgit/config.yaml.

        Args:
            config: Config to save

        Raises:
            IOError: If file write fails
        """
        # Convert to dict and serialize
        data = config.to_dict()
        content = self.yaml.dump_yaml(data)

        # Ensure .contextgit directory exists
        self.config_path.parent.mkdir(parents=True, exist_ok=True)

        # Write atomically
        self.fs.write_file_atomic(str(self.config_path), content)

    @staticmethod
    def get_default_config() -> Config:
        """Get default configuration.

        Returns:
            Config with default values
        """
        return Config.get_default()
