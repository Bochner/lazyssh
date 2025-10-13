# Plugin System Design

## Context

LazySSH manages SSH connections with control sockets, enabling connection multiplexing and persistence. The plugin system needs to leverage these existing connections to run user-defined scripts without requiring separate authentication or connection establishment. Plugins should be simple drop-in scripts that can access connection information and execute commands through the SSH channel.

## Goals / Non-Goals

### Goals
- Enable users to run custom Python or shell scripts through established SSH connections
- Provide simple, file-based plugin discovery (no complex registration)
- Pass connection context to plugins securely
- Support both Python and shell script plugins
- Create reusable plugin infrastructure for future expansion
- Provide first-party enumerate plugin as reference implementation
- Maintain LazySSH's simplicity and CLI-focused design

### Non-Goals
- Complex plugin packaging or distribution system
- Plugin versioning or dependency management beyond Python stdlib
- GUI plugin configuration
- Plugin sandboxing or advanced security isolation
- Plugin marketplace or centralized repository
- Supporting languages beyond Python and Shell initially
- Hot-reloading or plugin updates without restart

## Decisions

### Plugin Discovery
**Decision:** Scan `src/lazyssh/plugins/` directory for executable files with `.py` or `.sh` extensions.

**Rationale:** Simple file-based discovery is easy to understand and requires no registration. Users just drop files in the folder. Follows Unix philosophy of simplicity.

**Alternatives Considered:**
- Plugin registry file: Adds complexity and maintenance burden
- Entry points (setuptools): Too complex for simple scripts
- Config-based registration: Unnecessary overhead

### Plugin Interface
**Decision:** Pass connection information via environment variables that plugins can read.

Environment variables provided:
- `LAZYSSH_SOCKET` - Control socket name
- `LAZYSSH_HOST` - Remote host address
- `LAZYSSH_PORT` - SSH port
- `LAZYSSH_USER` - Username
- `LAZYSSH_SOCKET_PATH` - Full path to control socket file
- `LAZYSSH_SSH_KEY` - SSH key path (if used)

**Rationale:** Environment variables are language-agnostic and work for both Python and shell scripts. No need to parse arguments or import specific libraries.

**Alternatives Considered:**
- Command-line arguments: More verbose, harder to extend
- Config file: Temporary files are messy and can leak data
- Import LazySSH API: Creates tight coupling and limits shell support

### Plugin Execution
**Decision:** Execute plugins as subprocess from LazySSH, capturing stdout/stderr. Plugins are responsible for executing remote commands using the provided socket information.

**Execution Flow:**
1. User runs `plugin run <plugin_name> <socket_name>`
2. Plugin manager validates plugin exists and is executable
3. Plugin manager sets environment variables with connection info
4. Plugin manager spawns subprocess to run plugin
5. Plugin uses SSH control socket to execute remote commands
6. Plugin output streamed back to user
7. Exit code determines success/failure

**Rationale:** Simple subprocess model keeps plugins independent. Plugins use standard SSH commands with control socket, leveraging existing SSH infrastructure.

**Alternatives Considered:**
- Python import system: Only works for Python, creates coupling
- RPC/IPC: Overengineered for script execution
- Direct paramiko integration: Duplicates SSH setup logic

### Plugin Metadata
**Decision:** Use structured comments at the top of plugin files for metadata.

Format:
```python
# PLUGIN_NAME: enumerate
# PLUGIN_DESCRIPTION: Comprehensive system enumeration and reconnaissance
# PLUGIN_REQUIREMENTS: python3
# PLUGIN_VERSION: 1.0.0
```

**Rationale:** Simple to parse, visible in text editors, no external files needed. Uses common pattern from shell scripts.

**Alternatives Considered:**
- Separate `.json` metadata files: More files to manage
- Python decorators/docstrings: Only works for Python
- Filename conventions: Too limiting for descriptions

### Enumerate Plugin Architecture
**Decision:** Implement enumerate plugin as pure Python script that executes remote shell commands over SSH and aggregates results into structured output.

**Components:**
1. Command execution layer (uses SSH with control socket)
2. Information gatherers (modular functions for each category)
3. Output formatters (JSON and human-readable)
4. Error handling (graceful degradation if commands unavailable)

**Categories to enumerate:**
- System: OS, kernel, uptime, hostname
- Users: Local users, groups, sudo access
- Network: Interfaces, IPs, routes, connections, listening ports
- Processes: Running processes, systemd services
- Packages: apt/yum/pacman package list
- Filesystem: Mounts, disk usage, home directories
- Security: Firewall rules, SELinux/AppArmor, fail2ban
- Scheduled: Cron jobs, systemd timers
- Logs: Recent auth logs, system logs
- Environment: env vars, PATH

**Rationale:** Comprehensive survey useful for security audits, troubleshooting, and system documentation. Pure Python avoids requiring remote dependencies.

### Plugin Directory Structure
**Decision:**
```
src/lazyssh/plugins/
├── __init__.py           # Makes it a package
├── README.md             # Plugin development guide
├── enumerate.py          # Built-in enumeration plugin
└── example_template.py   # Template for users to copy
```

Users can add their own plugins alongside built-in ones.

**Rationale:** Simple flat structure. Built-in plugins shipped with package. Users can add custom plugins by dropping files in directory.

### Security Considerations
**Decision:** Plugins run with same privileges as LazySSH process. No sandboxing initially.

**Safety Measures:**
- Display warning when running plugins
- Recommend users review plugin code before execution
- Plugins only have access to already-established connections
- Document security best practices
- Built-in plugins vetted and maintained by project

**Rationale:** Full sandboxing is complex and may not be necessary for user's own scripts running on their machine. Users already trust LazySSH with SSH credentials. Focus on transparency and documentation.

**Future Consideration:** Could add plugin signing or approval system if community grows.

## Risks / Trade-offs

### Risk: Malicious Plugins
**Impact:** Users could run untrusted plugins that execute malicious code.

**Mitigation:**
- Clear documentation about plugin safety
- Warning message when running non-built-in plugins
- Recommend code review before execution
- Built-in plugins are trusted baseline
- No automatic plugin installation from internet

### Risk: Plugin Compatibility
**Impact:** Plugins may break if LazySSH internals change or environment variables format changes.

**Mitigation:**
- Document stable plugin interface contract
- Version plugin API in environment variables (e.g., `LAZYSSH_PLUGIN_API_VERSION=1`)
- Maintain backward compatibility for environment variables
- Deprecation warnings if interface changes

### Risk: Performance
**Impact:** Large or slow plugins could block command mode.

**Mitigation:**
- Run plugins in subprocess (already decided)
- Show progress indicator during execution
- Consider timeout mechanism for hung plugins
- Document best practices for plugin performance

### Trade-off: Simplicity vs Features
We're choosing simplicity (file-based, subprocess execution) over advanced features (plugin package manager, API imports). This may limit some use cases but keeps barrier to entry low.

### Trade-off: Security vs Usability
No sandboxing means plugins have full access, but enables simple implementation. Users already trust SSH access, so this seems acceptable for v1.

## Migration Plan

### Implementation Steps
1. Implement plugin manager core (discovery, validation, execution)
2. Add plugin command to command mode
3. Create enumerate plugin
4. Add UI components for plugin listing and execution
5. Write documentation and examples
6. Test on various systems

### Rollout
- Feature is additive, no breaking changes
- Users opt-in by using `plugin` command
- Built-in enumerate plugin available immediately
- Document in release notes as new feature

### Rollback
If issues found:
- Remove `plugin` command from command mode
- Keep plugin code but make it experimental/disabled by default
- No data loss risk since plugins don't persist state

## Open Questions

1. **Should plugins support configuration files?**
   - Initial answer: No, keep it simple. Plugins can handle their own config if needed.
   - Future: Could add `~/.config/lazyssh/plugins/<plugin_name>.conf` support

2. **Should plugins be able to call LazySSH commands?**
   - Initial answer: No, plugins are independent scripts
   - Future: Could provide helper library importable by Python plugins

3. **How to handle plugin output formats?**
   - Initial answer: Plugins control their own output, use stdout
   - Enumerate plugin provides both JSON and human-readable as example
   - Future: Could standardize on JSON schema for structured data

4. **Should there be plugin lifecycle hooks (setup/teardown)?**
   - Initial answer: No, plugins are stateless scripts
   - Future: Could add if compelling use cases emerge

5. **How to handle plugins requiring remote dependencies?**
   - Initial answer: Document that plugins should check for dependencies and gracefully fail
   - Enumerate plugin handles missing commands gracefully
   - Future: Could add dependency checking mechanism
