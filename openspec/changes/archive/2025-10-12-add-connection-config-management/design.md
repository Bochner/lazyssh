# Connection Configuration Management Design

## Context

LazySSH currently requires users to manually enter connection details for each session. Users have requested the ability to save connection configurations for quick reuse. This feature should integrate seamlessly with the existing command-line interface while maintaining the application's focus on simplicity and clarity.

## Goals / Non-Goals

**Goals:**
- Allow users to save frequently-used SSH connection configurations
- Display saved configurations in a clear, scannable table format
- Enable quick connection via saved config name
- Prompt users to save configurations after successful connections
- Support all existing connection parameters (host, port, user, key, shell, proxy, etc.)
- Maintain configuration file in a human-editable format

**Non-Goals:**
- Automatic connection on startup (configs are displayed, user chooses with `connect`)
- Encryption of credentials (SSH keys are referenced by path, not stored)
- Syncing configs across machines
- Migration from other SSH config formats
- GUI-based config editor

## Decisions

### File Format: TOML

**Decision:** Use TOML format for configuration storage.

**Rationale:**
- Human-readable and editable
- Well-supported in Python ecosystem (`tomli` for reading, `tomli-w` for writing in Python <3.11)
- Native support in Python 3.11+ via `tomllib` (read-only)
- Better structured than INI, simpler than JSON/YAML
- Industry standard for Python project configs (pyproject.toml)

**Alternatives considered:**
- JSON: Less human-friendly, no comments support
- YAML: More complex, potential security issues with unsafe loading
- INI: Limited structure, harder to represent complex nested data

### File Location: `/tmp/lazyssh/connections.conf`

**Decision:** Store configuration in `/tmp/lazyssh/connections.conf`

**Rationale:**
- Consistent with existing `/tmp/lazyssh/` directory structure used for connection artifacts
- Easy to discover and manage
- No permission issues (user owns /tmp/lazyssh)
- Follows project convention of using /tmp for runtime data

**Alternatives considered:**
- `~/.config/lazyssh/`: More permanent, but requires XDG directory setup
- `~/.lazyssh.conf`: Simple but pollutes home directory
- `/etc/lazyssh/`: System-wide but requires root permissions

### Configuration Structure

**Decision:** Store each connection as a TOML table with flat key-value pairs:

```toml
[production-web]
host = "192.168.1.100"
port = 22
username = "admin"
socket_name = "prod-web"
ssh_key = "~/.ssh/prod_key"
shell = "bash"
no_term = false
proxy_port = 9050

[dev-database]
host = "dev-db.example.com"
port = 2222
username = "dbadmin"
socket_name = "dev-db"
```

**Rationale:**
- Clear, self-documenting structure
- Easy to manually edit
- Direct mapping to SSHConnection model fields
- Optional fields can be omitted

### Save Prompt Workflow

**Decision:** After successful connection, prompt user: "Save this connection configuration? (y/N)"

**Rationale:**
- Opt-in approach respects user privacy for one-off connections
- Natural point in workflow (connection just succeeded)
- Default to 'No' for security-conscious users

**Implementation:**
- Show prompt immediately after "Connection established" success message
- If yes, prompt for config name (default: socket name)
- Check for conflicts and confirm overwrite if name exists

### Command Integration

**Decision:** Add the following commands:

1. `config` or `configs` - Display all saved configurations in a table
2. `connect <name>` - Connect using a saved configuration
3. `save-config <name>` - Save the current/last connection as a config
4. `delete-config <name>` - Remove a saved configuration

**Rationale:**
- Intuitive command names matching user mental model
- `config` as display-only follows pattern of `status`, `tunnels`
- `connect` is action-oriented, clearly different from `lazyssh` connection creation
- Separate `save-config` allows saving after the fact

**Tab Completion:**
- `config` commands should tab-complete with saved config names
- `connect` should tab-complete with available config names

### CLI Flag: `--config`

**Decision:** Add `--config <path>` flag that loads a configuration file on startup

**Behavior:**
- Loads and displays configurations in table format
- Does NOT automatically connect
- User must use `connect <name>` command to establish connection
- If file doesn't exist, show warning and continue normal operation

**Rationale:**
- Explicit is better than implicit (no auto-connect surprise)
- Allows user to review configs before connecting
- Supports alternative config file locations for testing/environments

## Risks / Trade-offs

### Risk: Plain-text credential storage

**Risk:** SSH private key paths stored in plain text config file

**Mitigation:** 
- Only store paths to keys, not the keys themselves
- Document security best practices in user guide
- File permissions set to 600 (owner read/write only)
- Consider future encryption feature if users request it

### Risk: Config file corruption

**Risk:** Manual editing could corrupt TOML syntax

**Mitigation:**
- Validate TOML parsing on load with clear error messages
- Atomic writes (write to temp file, then rename)
- Backup previous config on overwrite
- Show specific line number and error from TOML parser

### Trade-off: File location in /tmp

**Consideration:** `/tmp/lazyssh/` may be cleared on reboot

**Decision:** Accept this trade-off

**Rationale:**
- Consistent with project's existing use of /tmp
- SSH sessions are ephemeral by nature
- Users can manually backup if needed
- Future enhancement: add `--config-dir` flag for alternative location

## Migration Plan

### Phase 1: Core Implementation
1. Add TOML parsing library dependency
2. Implement config file read/write functions with error handling
3. Add ConfigEntry model or use dict-based approach
4. Implement save/load/delete operations

### Phase 2: UI Integration
5. Add `display_saved_configs()` table rendering function
6. Integrate save prompt into connection creation flow
7. Add `config` command to display configs

### Phase 3: Connect Command
8. Implement `connect <name>` command
9. Add tab completion for config names
10. Add validation and error handling

### Phase 4: Additional Commands
11. Implement `save-config` and `delete-config` commands
12. Add `--config` CLI flag
13. Add config management to menu mode

### Testing & Documentation
14. Add unit tests for config operations
15. Add integration tests for command flow
16. Update user documentation with config examples
17. Add troubleshooting section for config issues

### Rollback Plan

If issues arise, feature can be disabled by:
1. Remove `--config` flag usage from user invocations
2. Skip save prompt by always answering 'No'
3. Commands fail gracefully if config file missing
4. No data loss - existing connections unaffected

## Open Questions

1. Should we support config file comments to annotate saved connections?
   - **Answer:** Yes, TOML supports comments naturally. Preserve comments on config updates.

2. Should we validate that SSH keys exist before saving config?
   - **Answer:** Yes, but with warning not error. File might exist at connection time.

3. Should tunnel configurations be saved with connections?
   - **Answer:** No in MVP. Tunnels are session-specific. Consider for future enhancement.

4. Should we support config encryption?
   - **Answer:** Not in MVP. Monitor user feedback.

5. Should config name be case-sensitive?
   - **Answer:** Yes, maintain case sensitivity for consistency with Unix conventions.

