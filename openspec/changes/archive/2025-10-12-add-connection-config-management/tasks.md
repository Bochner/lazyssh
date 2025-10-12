# Implementation Tasks

## 1. Dependencies and Models
- [x] 1.1 Add `tomli` and `tomli-w` to requirements.txt (Python 3.11+ can use built-in `tomllib` for reading)
- [x] 1.2 Update pyproject.toml with new dependencies
- [x] 1.3 Add type definitions for config operations in models.py (if needed)

## 2. Core Configuration Management (config.py)
- [x] 2.1 Implement `get_config_file_path()` function returning `/tmp/lazyssh/connections.conf`
- [x] 2.2 Implement `ensure_config_directory()` to create `/tmp/lazyssh/` with proper permissions
- [x] 2.3 Implement `load_configs()` function to parse TOML and return dict of connections
- [x] 2.4 Implement `save_config(name, connection_params)` to write/update a single config entry
- [x] 2.5 Implement `delete_config(name)` to remove a config entry
- [x] 2.6 Implement `config_exists(name)` to check if a config name exists
- [x] 2.7 Add error handling with clear messages for TOML parsing errors
- [x] 2.8 Add atomic file write operations (write to temp, then rename)
- [x] 2.9 Set config file permissions to 600 (owner read/write only)

## 3. UI Components (ui.py)
- [x] 3.1 Implement `display_saved_configs(configs)` function using Rich Table
- [x] 3.2 Use similar styling to `display_ssh_status()` for consistency
- [x] 3.3 Display columns: Name, Host, Username, Port, SSH Key, Shell, Proxy, No-Term
- [x] 3.4 Handle empty configs gracefully with "No saved configurations" message
- [x] 3.5 Add color coding (cyan for names, magenta for hosts, etc.)

## 4. Connection Save Prompt (__main__.py)
- [x] 4.1 Add save prompt after successful connection in `create_connection_menu()`
- [x] 4.2 Prompt user: "Save this connection configuration? (y/N)"
- [x] 4.3 If yes, prompt for config name (default: socket name)
- [x] 4.4 Check if config name already exists
- [x] 4.5 If exists, prompt for confirmation to overwrite
- [x] 4.6 Call `save_config()` with connection parameters
- [x] 4.7 Display success/error message

## 5. Config Display Command (command_mode.py)
- [x] 5.1 Add `config` command (alias: `configs`) to display saved configurations
- [x] 5.2 Load configurations using `load_configs()`
- [x] 5.3 Call `display_saved_configs()` to render table
- [x] 5.4 Handle file not found gracefully
- [x] 5.5 Add `config` to command help text
- [x] 5.6 Add `config` to tab completion

## 6. Connect Command (command_mode.py)
- [x] 6.1 Implement `cmd_connect(args)` function
- [x] 6.2 Parse config name from args
- [x] 6.3 Load config by name from configs file
- [x] 6.4 Create SSHConnection object from config parameters
- [x] 6.5 Call `ssh_manager.create_connection()` with loaded connection
- [x] 6.6 Handle missing config name error
- [x] 6.7 Handle invalid config data errors
- [x] 6.8 Add `connect` to tab completion with config name suggestions
- [x] 6.9 Add `connect` to command help text

## 7. Save Config Command (command_mode.py)
- [x] 7.1 Implement `cmd_save_config(args)` function
- [x] 7.2 Parse config name from args
- [x] 7.3 Get last/current connection details from context
- [x] 7.4 Validate connection parameters exist
- [x] 7.5 Call `save_config()` with name and parameters
- [x] 7.6 Handle overwrites with confirmation prompt
- [x] 7.7 Add `save-config` to tab completion
- [x] 7.8 Add `save-config` to command help text

## 8. Delete Config Command (command_mode.py)
- [x] 8.1 Implement `cmd_delete_config(args)` function
- [x] 8.2 Parse config name from args
- [x] 8.3 Confirm deletion with user prompt
- [x] 8.4 Call `delete_config()` to remove entry
- [x] 8.5 Display success/error message
- [x] 8.6 Add `delete-config` to tab completion with config name suggestions
- [x] 8.7 Add `delete-config` to command help text

## 9. CLI Flag Integration (__main__.py)
- [x] 9.1 Add `--config` option to Click command decorator
- [x] 9.2 Accept optional path parameter (default: `/tmp/lazyssh/connections.conf`)
- [x] 9.3 Load and display configs on startup if flag provided
- [x] 9.4 Show warning if config file doesn't exist
- [x] 9.5 Continue normal operation without blocking startup

## 10. Menu Mode Integration (__main__.py)
- [x] 10.1 Add "View saved configurations" menu option
- [x] 10.2 Add "Connect from saved config" menu option with selection
- [x] 10.3 Add "Save current connection" menu option
- [x] 10.4 Add "Delete saved config" menu option with selection

## 11. Tab Completion Enhancement (command_mode.py)
- [x] 11.1 Update `LazySSHCompleter` to suggest config names for `connect` command
- [x] 11.2 Update `LazySSHCompleter` to suggest config names for `delete-config` command
- [x] 11.3 Cache loaded config names for completion performance
- [x] 11.4 Reload config names cache when configs are modified

## 12. Error Handling and Validation
- [x] 12.1 Add validation for config name format (alphanumeric, dash, underscore)
- [x] 12.2 Handle TOML parsing errors with line number and error message
- [x] 12.3 Handle missing SSH key file with warning (not error)
- [x] 12.4 Handle invalid port numbers in config
- [x] 12.5 Handle file permission errors gracefully
- [x] 12.6 Add logging for all config operations

## 13. Testing
- [x] 13.1 Add unit tests for `load_configs()` function
- [x] 13.2 Add unit tests for `save_config()` function
- [x] 13.3 Add unit tests for `delete_config()` function
- [x] 13.4 Add unit tests for config validation
- [x] 13.5 Add integration tests for connect command flow
- [x] 13.6 Test TOML parsing error scenarios
- [x] 13.7 Test file permission scenarios
- [x] 13.8 Test config overwrite scenarios

## 14. Documentation
- [x] 14.1 Update README.md with config management section ✓ Added comprehensive section
- [x] 14.2 Add config file format example ✓ Added TOML examples in README and user-guide
- [x] 14.3 Document all config-related commands ✓ Added config, connect, save-config, delete-config to docs
- [x] 14.4 Add troubleshooting section for config issues ✓ Added full section in troubleshooting.md
- [x] 14.5 Update user-guide.md with config workflow examples ✓ Added workflows and examples
- [x] 14.6 Document `--config` CLI flag ✓ Documented in README and user-guide
- [x] 14.7 Add security considerations for config files ✓ Added security notes in both README and user-guide

