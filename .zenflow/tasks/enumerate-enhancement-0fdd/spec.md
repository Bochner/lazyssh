# Technical Specification: Enumerate Enhancement & Autopwn UX Hardening

## Technical Context

- **Language**: Python 3.11+
- **UI Framework**: Rich (panels, tables, text, spinners, prompts)
- **Console Singleton**: `lazyssh.console_instance.console` with theme system (Dracula default, high-contrast, colorblind, plain-text variants)
- **Theme Styles Available**: `error`, `warning`, `success`, `info`, `header`, `accent`, `dim`, `highlight`, `border`, `panel.title`, `foreground`, `comment`
- **Accessibility**: `LAZYSSH_PLAIN_TEXT`, `LAZYSSH_HIGH_CONTRAST`, `LAZYSSH_COLORBLIND_MODE` environment variables; all styles use semantic theme keys
- **UI Factories**: `lazyssh.ui` provides `create_standard_table()`, `create_info_panel()`, `create_error_panel()`, `create_warning_panel()`, `create_success_panel()`, `create_live_progress()`
- **Testing**: pytest with `monkeypatch`, `mock.patch`, pytest-timeout (30s). All subprocess and prompt calls mocked.
- **Lint/Type**: `ruff` + `mypy` via `make check`

## Files to Modify

| File | Changes |
|------|---------|
| `src/lazyssh/plugins/enumerate.py` | R1: Rendering overhaul (render_rich, render_plain, new constants) |
| `src/lazyssh/plugins/_autopwn.py` | R2: stdin isolation, interactive detection, docker sanitization, progress, summary, banner, timeout flag |
| `src/lazyssh/plugins/_gtfobins_data.py` | Strip `-it`/`-ti` from stored docker commands |
| `tests/test_enumerate_summary.py` | New tests for R1 rendering changes |
| `tests/test_autopwn.py` | New tests for R2 safety/UX changes |

No new files are required. All changes fit within existing modules.

---

## Part 1: Enumerate Output Colorization (R1)

### R1.1 Summary Statistics Header

**Location**: `enumerate.py`, new function `_render_stats_header()` called at the top of `render_rich()` (after the rule, before Quick Wins).

**Implementation**:
- Count findings by severity: `collections.Counter(f.severity for f in findings)`
- Count total probes and failures from `snapshot.probes`
- Render as a single `Text` object with pipe-separated severity counts, each styled with its `SEVERITY_STYLES` mapping
- Rich: `Text` composed with `.append()` calls, displayed via `console.print()`
- Plain text: append line `Findings: N critical, N high, N medium, N info | Probes: N total, N failed`

**Data flow**: `findings: Sequence[PriorityFinding]` + `snapshot.probes` dict → counts → styled text

### R1.2 Enhanced Severity Badges

**Location**: `enumerate.py`, new helper `_severity_badge(severity: str) -> Text` (Rich) / `_severity_badge_plain(severity: str) -> str`.

**Implementation**:
- CRITICAL: `Text(f" {sev} ", style="bold reverse error")` (bold white-on-red)
- HIGH: `Text(f" {sev} ", style="bold reverse error")` (same visual weight, distinguishable by label)
- MEDIUM: `Text(sev, style="bold warning")`
- INFO: `Text(sev, style="info")`
- Plain text: `[CRITICAL]`, `[HIGH]`, `[MEDIUM]`, `[INFO]`
- Replace inline `f"[{style}]{finding.severity.upper()}[/]"` in Quick Wins and Priority Findings tables with `_severity_badge()` calls

**Rationale for CRITICAL=HIGH visual weight**: Both are "error" in the theme. The label text itself (`CRITICAL` vs `HIGH`) provides the differentiation. Using `reverse` (inverse video) makes both stand out from surrounding text far more than plain colored text.

### R1.3 Exploit Command Styling

**Location**: `enumerate.py`, in `render_rich()` Quick Wins and Priority Findings sections.

**Current**: Commands styled `"foreground"`, comments `"dim"`.

**Change**:
- Executable commands (not starting with `#`): prefix `$ `, style `"highlight"` (pink in Dracula theme)
- Comment lines (starting with `#`): keep `"dim"` style, no prefix change
- This makes commands visually distinct from detail/narrative text and easy to spot for copy-paste

### R1.4 Category Panel Visual Differentiation

**Location**: `enumerate.py`, category panel loop in `render_rich()`.

**Implementation**:
- Before building each category's panel, scan its probes for failures and cross-reference with `findings`
- Determine `border_style`:
  1. If any finding in `findings` has `category == current_category` and `severity == "critical"` → `border_style="error"` (red border)
  2. Else if any probe in the category has `status != 0` → `border_style="warning"` (yellow border)
  3. Else → `border_style="success"` (green border)
- Build a `set[str]` of categories-with-criticals and categories-with-failures before the loop to avoid repeated iteration

### R1.5 Quick Wins Tier Improvements

**Location**: `enumerate.py`, Quick Wins table construction in `render_rich()`.

**Implementation**:
- Add a `Section` separator row between tiers using `qw_table.add_section()` (Rich table method that inserts a divider)
- Before each tier's rows, insert a header row spanning the full table: `qw_table.add_row(f"[bold]{tier.upper()} ({count} findings)[/bold]", "", "", end_section=False)` — or use `add_section()` + a merged-column row
- Simpler approach: call `qw_table.add_section()` before each new tier (except the first) and add a tier label row with `style="bold"` on the difficulty column

### R1.6 Human-Friendly Check Labels

**Location**: `enumerate.py`, new module-level constant `PROBE_DISPLAY_NAMES: dict[str, str]`.

**Implementation**:
```python
PROBE_DISPLAY_NAMES: dict[str, str] = {
    "suid_files": "SUID Binaries",
    "sgid_files": "SGID Binaries",
    "world_writable_dirs": "World-Writable Directories",
    "docker_group": "Docker Group Membership",
    "docker_socket": "Docker Socket Access",
    "ssh_config": "SSH Configuration",
    "kernel_version": "Kernel Version",
    "os_release": "OS Release",
    "current_user": "Current User",
    "sudo_rules": "Sudo Rules",
    "passwd_writable": "Passwd File Permissions",
    "shadow_readable": "Shadow File Access",
    "cron_files": "Cron Files",
    "systemd_timers": "Systemd Timers",
    "listening_services": "Listening Services",
    "nfs_exports": "NFS Exports",
    "capabilities": "Linux Capabilities",
    "env_vars": "Environment Variables",
    "ld_preload": "LD_PRELOAD",
    # ... extend as probe keys are added
}
```
- In the category table: show `PROBE_DISPLAY_NAMES.get(key, key)` as the primary label
- Append raw key in dim: `f"[accent]{display_name}[/accent] [dim]({key})[/dim]"` only when display_name != key
- Plain text: `display_name` (raw key as-is when no mapping)

### R1.7 Evidence Styling

**Location**: `enumerate.py`, Priority Findings detail column in `render_rich()`.

**Current**: Evidence not shown in Rich rendering (only in plain text).

**Implementation**:
- After appending exploit commands to `detail_text`, also append evidence items
- Format: `detail_text.append(f"\n  * {ev}", style="accent")` for each evidence item (up to 4)
- Use `*` bullet in accent color to distinguish from narrative text
- Plain text: already renders evidence with `•` bullets — no change needed

### R1.8 Plain Text Parity

**Location**: `enumerate.py`, `render_plain()` function.

**Changes**:
- Add summary stats line at the top (after the header): `Findings: N critical, N high, N medium, N info | Probes: N total, N failed`
- Severity badges already use `[SEVERITY]` format — no change
- Evidence already uses `•` bullets — no change
- Check labels: use `PROBE_DISPLAY_NAMES.get(key, key)` in category output

---

## Part 2: Autopwn Interactive-Command Safety (R2)

### R2.1 Stdin Isolation

**Location**: `_autopwn.py`, `_ssh_exec()` function (line 90).

**Implementation**:
- Add `stdin=subprocess.DEVNULL` to the `subprocess.run()` call
- This replaces the implicit stdin inheritance. Commands that require input receive EOF immediately and exit non-zero rather than blocking

**Change**:
```python
result = subprocess.run(
    ssh_cmd,
    text=True,
    capture_output=True,
    stdin=subprocess.DEVNULL,  # NEW: prevent interactive hangs
    timeout=timeout,
)
```

Note: `capture_output=True` sets `stdout=PIPE, stderr=PIPE` but does NOT set `stdin`. Adding `stdin=DEVNULL` is compatible with `capture_output=True`.

### R2.2 Interactive Command Detection

**Location**: `_autopwn.py`, new module-level function `_classify_interactive(command: str) -> str | None`.

**Implementation**:
```python
_INTERACTIVE_PATTERNS: list[tuple[str, str]] = [
    (r"\bpkexec\b", "pkexec requires a polkit agent / password prompt"),
    (r"\b(docker|podman)\b.*\s-[a-z]*[it][a-z]*\b", "docker -it flags require a TTY"),
    (r"\b(vim|vi|less|more|man|ed|nano)\b", "editor/pager requires terminal interaction"),
    (r"\bsu\s", "su requires password input"),
]
```
- Returns the reason string if the command matches any pattern, `None` if safe
- Uses `re.search()` for each pattern
- Called before execution in `_try_finding()` dispatch or within individual exploit methods

**Behavior**:
- **Dry-run**: Append `[INTERACTIVE]` badge to the command display line. Still show the command normally
- **Live mode**: Print warning with reason. Proceed with execution anyway (stdin isolation from R2.1 ensures it won't hang). No additional confirmation beyond the existing per-exploit confirmation

### R2.3 Docker Command Sanitization

**Location**: `_autopwn.py`, new function `_sanitize_docker_command(command: str) -> str`.

**Implementation**:
- Parse command string for docker/podman invocations
- Use regex to strip `-it`, `-ti`, `--interactive`, `--tty` flags
- Add `--rm` if not already present
- Log original vs sanitized via `APP_LOGGER.debug()` if logger available
- Called in `_exploit_docker_escape()` before execution

**Also update source data**:
- `_gtfobins_data.py`: Change stored docker commands to remove `-it` flags (4 occurrences across 2 entries)
- `enumerate.py` line 766: Update hardcoded docker escape command

This is a source-level fix that prevents the flags from propagating. The runtime sanitizer in `_autopwn.py` acts as a safety net for any dynamically generated commands.

### R2.4 Execution Progress Feedback

**Location**: `_autopwn.py`, modify `_ssh_exec()` callers (not the function itself, to keep it pure).

**Implementation**:
- Import `Status` from Rich: `from rich.status import Status`
- Wrap `_ssh_exec()` calls in a Rich `Status` context manager:
  ```python
  with Status(f"Executing: {cmd_summary}... (timeout: {timeout}s)", console=console):
      exit_code, stdout, stderr = _ssh_exec(command, timeout=timeout)
  ```
- `cmd_summary`: first 60 chars of command, truncated with `...`
- After execution, print elapsed time: `console.print(f"  [dim]Completed in {elapsed:.1f}s[/dim]")`
- Use `time.monotonic()` for timing

**Helper**: New method `_exec_with_progress(command: str, timeout: int = 30) -> tuple[int, str, str, float]` on `AutopwnEngine` that wraps `_ssh_exec()` with status display and timing. Returns `(exit_code, stdout, stderr, elapsed)`. All exploit methods call this instead of `_ssh_exec()` directly.

### R2.5 Enhanced Summary Table

**Location**: `_autopwn.py`, replace `_render_summary()`.

**Implementation**:
- Build a Rich `Table` with columns: `#`, `Technique`, `Target`, `Command`, `Status`, `Duration`
- Iterate `self.result.attempts` and add rows:
  - `#`: 1-indexed counter
  - `Technique`: `attempt.technique`
  - `Target`: `attempt.target`
  - `Command`: first 50 chars of `attempt.command`, truncated
  - `Status`: styled badge — `[success]SUCCESS[/]`, `[error]FAILED[/]`, `[warning]DRY-RUN[/]`, `[dim]SKIPPED[/]`
  - `Duration`: `f"{attempt.duration:.1f}s"` (requires adding `duration: float = 0.0` field to `ExploitAttempt`)
- Row styling: `style="success"` for success, `style="error"` for failure, no row style for dry-run
- Wrap in Panel with title `"Autopwn Summary"`
- If rollback commands exist, render a separate sub-table below:
  - Columns: `Technique`, `Rollback Command`
  - Border style: `"warning"`
  - Panel title: `"Rollback Commands"`

**Data model change**: Add `duration: float = 0.0` field to `ExploitAttempt` dataclass.

### R2.6 Mode Banner

**Location**: `_autopwn.py`, at the start of `run()` method, after filtering exploitable findings.

**Implementation**:
- **DRY-RUN**: `Panel("NO COMMANDS WILL BE EXECUTED\nReview the commands below. Re-run without --dry-run to execute.", title="DRY-RUN MODE", border_style="warning", box=box.HEAVY)`
- **LIVE**: `Panel("LIVE EXPLOITATION MODE\nCommands will be executed on the remote host. Each requires confirmation.", title="LIVE MODE", border_style="error", box=box.HEAVY)` followed by a top-level confirmation: `_confirm("Proceed with live exploitation?")`
- If the live-mode confirmation is declined, return early with empty result

**Import**: Add `from rich import box` and `from rich.panel import Panel` to the Rich try-import block.

### R2.7 Timeout Configuration

**Location**: `_autopwn.py`, `AutopwnEngine.__init__()` and `enumerate.py` argv parsing.

**Implementation**:
- Parse `--timeout N` from `sys.argv` in `enumerate.py` (alongside `--autopwn` and `--dry-run`)
- Pass `timeout` parameter to `AutopwnEngine.__init__()`
- Add `self.timeout: int` field (default 30, clamped to range 5-120)
- In `_exec_with_progress()`, use `min(self.timeout, per_exploit_timeout)` — the global timeout caps per-exploit defaults but doesn't increase them
- Docker escape currently uses 60s timeout. With `--timeout 30`, it would use 30s. With `--timeout 90`, it would keep 60s (min of 90 and 60)

---

## Data Model Changes

### ExploitAttempt (modified)

```python
@dataclass
class ExploitAttempt:
    technique: str
    target: str
    dry_run: bool
    command: str
    success: bool
    output: str
    rollback_command: str | None = None
    duration: float = 0.0           # NEW: elapsed execution time in seconds
    interactive_warning: str = ""   # NEW: reason if classified as interactive
```

### No new dataclasses needed

All other data structures (ProbeOutput, PriorityFinding, EnumerationSnapshot, AutopwnResult) remain unchanged.

---

## Delivery Phases

### Phase 1: Enumerate Output Polish (R1)
**Scope**: R1.1 through R1.8, fully self-contained within `enumerate.py`.

**Milestones**:
1. Add `PROBE_DISPLAY_NAMES` constant and `_severity_badge()` / `_render_stats_header()` helpers
2. Update `render_rich()`: stats header, severity badges, exploit command styling, category borders, quick wins tiers, evidence, human labels
3. Update `render_plain()`: stats header, human labels
4. Add/update tests in `test_enumerate_summary.py`

**Verification**: `make check && make test`

### Phase 2: Autopwn Safety & UX (R2)
**Scope**: R2.1 through R2.7, primarily in `_autopwn.py` with minor changes to `enumerate.py` (argv parsing) and `_gtfobins_data.py` (docker flag cleanup).

**Milestones**:
1. `stdin=DEVNULL` in `_ssh_exec()` + docker command source fixes
2. Interactive detection + docker sanitization functions
3. `_exec_with_progress()` wrapper with spinner + timing
4. Mode banner in `run()`
5. Enhanced `_render_summary()` with Rich table
6. `--timeout` flag support
7. Add/update tests in `test_autopwn.py`

**Verification**: `make check && make test`

---

## Verification Approach

1. **Linting**: `make lint` (ruff check) — must pass clean
2. **Type checking**: `make check` (ruff + mypy) — must pass clean
3. **Unit tests**: `make test` — all existing tests pass, new tests added for:
   - `_severity_badge()` returns correct Rich Text/plain string per severity
   - `_render_stats_header()` counts match input findings
   - Category border logic: critical findings → error, failures → warning, all-pass → success
   - Quick Wins tier separators render correctly
   - `PROBE_DISPLAY_NAMES` lookup in render output
   - `_classify_interactive()` detects pkexec, docker -it, vim, su
   - `_sanitize_docker_command()` strips flags correctly
   - `_ssh_exec()` now uses `stdin=DEVNULL` (check mock call kwargs)
   - `_exec_with_progress()` returns timing data
   - Enhanced summary renders Rich table with correct columns
   - Mode banner displays for dry-run and live modes
   - `--timeout` parsing and clamping
4. **Full build**: `make verify` (check + test + build)
