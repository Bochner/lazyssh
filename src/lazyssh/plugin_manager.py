"""Plugin manager for LazySSH - Discover, validate and execute plugins"""

import os
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path

from .logging_module import APP_LOGGER
from .models import SSHConnection


@dataclass
class PluginMetadata:
    """Metadata extracted from a plugin file"""

    name: str
    description: str
    version: str
    requirements: str
    file_path: Path
    plugin_type: str  # 'python' or 'shell'
    is_valid: bool
    validation_errors: list[str]


class PluginManager:
    """Manages plugin discovery, validation and execution"""

    def __init__(self, plugins_dir: Path | None = None):
        """Initialize the plugin manager

        Args:
            plugins_dir: Path to plugins directory. Defaults to src/lazyssh/plugins/
        """
        if plugins_dir is None:
            # Default to the plugins directory in the package
            self.plugins_dir = Path(__file__).parent / "plugins"
        else:
            self.plugins_dir = Path(plugins_dir)

        self._plugins_cache: dict[str, PluginMetadata] | None = None

        if APP_LOGGER:
            APP_LOGGER.debug(f"PluginManager initialized with directory: {self.plugins_dir}")

    def discover_plugins(self, force_refresh: bool = False) -> dict[str, PluginMetadata]:
        """Discover all plugins in the plugins directory

        Args:
            force_refresh: If True, bypass cache and re-scan directory

        Returns:
            Dictionary mapping plugin names to their metadata
        """
        if not force_refresh and self._plugins_cache is not None:
            return self._plugins_cache

        plugins: dict[str, PluginMetadata] = {}

        if not self.plugins_dir.exists():
            if APP_LOGGER:
                APP_LOGGER.warning(f"Plugins directory does not exist: {self.plugins_dir}")
            self._plugins_cache = plugins
            return plugins

        # Scan for .py and .sh files
        for plugin_file in self.plugins_dir.iterdir():
            if plugin_file.name.startswith("_") or plugin_file.name.startswith("."):
                # Skip private files, __init__.py, and hidden files
                continue

            if plugin_file.suffix in [".py", ".sh"]:
                metadata = self._extract_metadata(plugin_file)
                if metadata:
                    plugins[metadata.name] = metadata

        self._plugins_cache = plugins

        if APP_LOGGER:
            APP_LOGGER.debug(f"Discovered {len(plugins)} plugins")

        return plugins

    def _extract_metadata(self, plugin_file: Path) -> PluginMetadata | None:
        """Extract metadata from a plugin file

        Args:
            plugin_file: Path to the plugin file

        Returns:
            PluginMetadata object or None if file cannot be read
        """
        validation_errors = []
        plugin_type = "python" if plugin_file.suffix == ".py" else "shell"

        # Default values
        name = plugin_file.stem
        description = "No description available"
        version = "1.0.0"
        requirements = "python3" if plugin_type == "python" else "bash"

        # Try to read metadata from file
        try:
            with open(plugin_file, "r", encoding="utf-8") as f:
                # Read first 50 lines to find metadata
                for _ in range(50):
                    line = f.readline()
                    if not line:
                        break

                    line = line.strip()

                    # Parse metadata comments
                    if line.startswith("#"):
                        if "PLUGIN_NAME:" in line:
                            name = line.split("PLUGIN_NAME:", 1)[1].strip()
                        elif "PLUGIN_DESCRIPTION:" in line:
                            description = line.split("PLUGIN_DESCRIPTION:", 1)[1].strip()
                        elif "PLUGIN_VERSION:" in line:
                            version = line.split("PLUGIN_VERSION:", 1)[1].strip()
                        elif "PLUGIN_REQUIREMENTS:" in line:
                            requirements = line.split("PLUGIN_REQUIREMENTS:", 1)[1].strip()
        except Exception as e:
            validation_errors.append(f"Failed to read file: {e}")

        # Validate plugin
        is_valid = self._validate_plugin(plugin_file, validation_errors)

        return PluginMetadata(
            name=name,
            description=description,
            version=version,
            requirements=requirements,
            file_path=plugin_file,
            plugin_type=plugin_type,
            is_valid=is_valid,
            validation_errors=validation_errors,
        )

    def _validate_plugin(self, plugin_file: Path, validation_errors: list[str]) -> bool:
        """Validate a plugin file

        Args:
            plugin_file: Path to the plugin file
            validation_errors: List to append validation errors to

        Returns:
            True if plugin is valid, False otherwise
        """
        # Check if file exists
        if not plugin_file.exists():
            validation_errors.append("File does not exist")
            return False

        # Check if file is executable
        if not os.access(plugin_file, os.X_OK):
            validation_errors.append("File is not executable")
            return False

        # Check for shebang
        try:
            with open(plugin_file, "rb") as f:
                first_bytes = f.read(2)
                if first_bytes != b"#!":
                    validation_errors.append("Missing shebang (#!)")
                    return False
        except Exception as e:
            validation_errors.append(f"Failed to check shebang: {e}")
            return False

        return True

    def get_plugin(self, plugin_name: str) -> PluginMetadata | None:
        """Get metadata for a specific plugin

        Args:
            plugin_name: Name of the plugin

        Returns:
            PluginMetadata object or None if plugin not found
        """
        plugins = self.discover_plugins()
        return plugins.get(plugin_name)

    def execute_plugin(
        self, plugin_name: str, connection: SSHConnection, args: list[str] | None = None
    ) -> tuple[bool, str, float]:
        """Execute a plugin with the given SSH connection context

        Args:
            plugin_name: Name of the plugin to execute
            connection: SSHConnection object with connection details
            args: Optional additional arguments to pass to plugin

        Returns:
            Tuple of (success: bool, output: str, execution_time: float)
        """
        # Get plugin metadata
        plugin = self.get_plugin(plugin_name)
        if not plugin:
            return False, f"Plugin '{plugin_name}' not found", 0.0

        if not plugin.is_valid:
            errors = "\n".join(plugin.validation_errors)
            return False, f"Plugin '{plugin_name}' is invalid:\n{errors}", 0.0

        # Prepare environment variables
        env = os.environ.copy()
        env.update(self._prepare_plugin_env(connection))

        # Prepare command
        cmd = [str(plugin.file_path)]
        if args:
            cmd.extend(args)

        if APP_LOGGER:
            APP_LOGGER.debug(f"Executing plugin: {plugin_name} with command: {' '.join(cmd)}")

        # Execute plugin
        start_time = time.time()
        try:
            result = subprocess.run(
                cmd,
                env=env,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
            )
            execution_time = time.time() - start_time

            # Combine stdout and stderr
            output = result.stdout
            if result.stderr:
                output += "\n" + result.stderr

            success = result.returncode == 0

            if APP_LOGGER:
                APP_LOGGER.debug(
                    f"Plugin {plugin_name} completed with exit code {result.returncode} in {execution_time:.2f}s"
                )

            return success, output, execution_time

        except subprocess.TimeoutExpired:
            execution_time = time.time() - start_time
            error_msg = f"Plugin '{plugin_name}' timed out after {execution_time:.0f} seconds"
            if APP_LOGGER:
                APP_LOGGER.error(error_msg)
            return False, error_msg, execution_time

        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"Failed to execute plugin '{plugin_name}': {e}"
            if APP_LOGGER:
                APP_LOGGER.error(error_msg)
            return False, error_msg, execution_time

    def _prepare_plugin_env(self, connection: SSHConnection) -> dict[str, str]:
        """Prepare environment variables for plugin execution

        Args:
            connection: SSHConnection object

        Returns:
            Dictionary of environment variables
        """
        # Get socket name from socket path
        socket_name = Path(connection.socket_path).name

        env = {
            "LAZYSSH_SOCKET": socket_name,
            "LAZYSSH_HOST": connection.host,
            "LAZYSSH_PORT": str(connection.port),
            "LAZYSSH_USER": connection.username,
            "LAZYSSH_SOCKET_PATH": connection.socket_path,
            "LAZYSSH_PLUGIN_API_VERSION": "1",
        }

        # Add optional fields
        if connection.identity_file:
            env["LAZYSSH_SSH_KEY"] = connection.identity_file

        if connection.shell:
            env["LAZYSSH_SHELL"] = connection.shell

        return env
