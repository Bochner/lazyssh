# Plugin System Proposal

## Why

LazySSH currently provides core SSH operations (connections, tunnels, file transfers) but lacks extensibility for custom automation scripts and workflows. Users often need to perform common tasks like system enumeration, security audits, batch operations, or custom diagnostics on remote machines through established SSH connections. Currently, there's no structured way to run such scripts through LazySSH's existing socket infrastructure, forcing users to write ad-hoc solutions or switch to other tools.

A modular plugin system would enable users to drop Python or shell scripts into a plugins folder and execute them through established SSH connections using a simple `plugin` command, leveraging LazySSH's connection management and providing a framework for extensible remote automation.

## What Changes

- Add a plugin system that allows users to run Python or shell scripts through established SSH connections
- Create a `plugins/` directory where users can drop executable scripts
- Implement a `plugin` command in command mode to discover and execute plugins
- Define a plugin interface/contract for how plugins receive connection information
- Pass connection details (socket name, host, user, etc.) to plugins via environment variables or arguments
- Provide built-in utility functions/helpers for plugin authors
- Create the first official plugin: `enumerate.py` - performs comprehensive system enumeration on the target machine
- Document plugin development guidelines for users to create their own plugins

### Enumeration Plugin Features

The `enumerate.py` plugin will perform a full system survey including:
- OS information (distro, version, kernel)
- User and group information
- Network configuration (interfaces, routes, listening ports)
- Running processes and services
- Installed software and packages
- File system information and mounts
- Environment variables
- Cron jobs and scheduled tasks
- Security configurations (firewall rules, SELinux status)
- System logs summary
- Hardware information
- SSH configurations
- Output formatted as structured JSON or human-readable report

## Impact

### Affected Specs
- **NEW**: `plugin-system` - New capability for plugin infrastructure
- **MODIFIED**: `user-interface` - Add `plugin` command to command mode
- **MODIFIED**: `user-documentation` - Document plugin system and enumeration plugin

### Affected Code
- **NEW**: `src/lazyssh/plugin_manager.py` - Plugin discovery, validation, and execution
- **NEW**: `src/lazyssh/plugins/` - Plugin directory with built-in plugins
- **NEW**: `src/lazyssh/plugins/enumerate.py` - System enumeration plugin
- **NEW**: `src/lazyssh/plugins/README.md` - Plugin development guide
- **MODIFIED**: `src/lazyssh/command_mode.py` - Add `plugin` command handler
- **MODIFIED**: `src/lazyssh/ui.py` - Add plugin listing/execution UI components
- **MODIFIED**: `README.md` - Add plugin system overview

### Benefits
- Extends LazySSH functionality without modifying core code
- Enables community contributions of useful automation scripts
- Provides structured way to run remote automation tasks
- Maintains LazySSH's connection management advantages
- Creates foundation for growing plugin ecosystem

### Risks
- Plugin execution security considerations (arbitrary code execution)
- Need clear documentation on plugin safety and trust
- Plugin errors could confuse users if not handled properly
- Need to establish clear plugin API to avoid breaking changes

### Migration Path
- Fully backward compatible - no existing functionality changes
- Plugin system is opt-in - users only interact with it if they use the `plugin` command
- Built-in plugins are included by default but can be removed by users
