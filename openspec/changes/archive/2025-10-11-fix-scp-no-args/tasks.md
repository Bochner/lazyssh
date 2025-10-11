# Implementation Tasks

## 1. Fix Socket Path Assignment
- [x] 1.1 In `SCPMode.run()`, after `_select_connection()` succeeds, set `self.socket_path` from `self.connection_name`
- [x] 1.2 Ensure socket path follows the pattern `/tmp/{connection_name}`
- [x] 1.3 Verify the fix doesn't break existing behavior when connection is provided as argument

## 2. Testing
- [x] 2.1 Test `scp` with no arguments - should prompt for connection and enter SCP mode
- [x] 2.2 Test `scp <connection_name>` - should directly enter SCP mode for that connection
- [x] 2.3 Test canceling connection selection (Ctrl+C, EOF) - should exit gracefully
- [x] 2.4 Test with invalid connection selection - should show error and return to prompt

## 3. Documentation
- [x] 3.1 Update CHANGELOG.md with bug fix entry

