# Add Connection Configuration Management

## Why

Users currently must manually re-enter SSH connection details every time they start LazySSH. This is inefficient for frequently-used connections and error-prone when dealing with complex configurations involving multiple parameters (SSH keys, custom shells, proxy ports, etc.). Adding persistent configuration management will improve user experience by allowing users to save, load, and quickly connect to frequently-used SSH hosts.

## What Changes

- Add TOML-based configuration file storage in `/tmp/lazyssh/connections.conf`
- Implement configuration save/load/delete operations with file-based persistence
- Display saved configurations in a Rich-formatted table similar to active connections table
- Add prompt to save connection parameters after successful connection establishment
- Extend command mode with new commands: `config`, `connect`, `save-config`, `delete-config`
- Add `--config` CLI flag to load a configuration file on launch (displays configs without auto-connecting)
- Store all connection parameters: host, port, username, socket name, SSH key, shell, no-term, proxy settings
- Validate configuration integrity on load and provide helpful error messages

## Impact

- **Affected specs**: New capability `connection-config`
- **Affected code**:
  - `src/lazyssh/config.py` - Add config file management functions
  - `src/lazyssh/__main__.py` - Add `--config` CLI option, integrate save prompt
  - `src/lazyssh/command_mode.py` - Add new commands for config management
  - `src/lazyssh/ui.py` - Add `display_saved_configs()` function for table rendering
  - `src/lazyssh/models.py` - May add `ConfigEntry` model or extend existing models
- **Breaking changes**: None - purely additive feature
- **Dependencies**: Add `toml` or `tomli`/`tomli-w` to requirements.txt for TOML parsing

