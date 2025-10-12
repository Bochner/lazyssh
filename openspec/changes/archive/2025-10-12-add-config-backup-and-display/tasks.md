# Implementation Tasks

## 1. Add Backup Functionality
- [x] 1.1 Implement `backup_config()` function in `src/lazyssh/config.py`
- [x] 1.2 Add logic to create `connections.conf.backup` file with same permissions (600)
- [x] 1.3 Handle cases where original config doesn't exist
- [x] 1.4 Handle file I/O errors gracefully

## 2. Add backup-config Command
- [x] 2.1 Implement `cmd_backup_config()` method in `CommandMode` class
- [x] 2.2 Register command in commands dictionary
- [x] 2.3 Add tab completion for the command
- [x] 2.4 Display success/error messages appropriately

## 3. Modify Status Display
- [x] 3.1 Update `show_status()` method in `CommandMode` to always display loaded configs
- [x] 3.2 Ensure configs are displayed on startup (if any exist)
- [x] 3.3 Ensure configs are displayed after every command (like connections)
- [x] 3.4 Maintain consistent ordering (configs → connections → tunnels)

## 4. Update Help and Documentation
- [x] 4.1 Add backup-config to help command output
- [x] 4.2 Update command documentation in docs/commands.md
- [x] 4.3 Update user guide if necessary

## 5. Testing and Validation
- [x] 5.1 Test backup-config with existing config file
- [x] 5.2 Test backup-config with no config file
- [x] 5.3 Test backup-config with permission errors
- [x] 5.4 Verify configs display on startup
- [x] 5.5 Verify configs display after commands
- [x] 5.6 Test with empty config file
- [x] 5.7 Run pre-commit checks

