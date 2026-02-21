# Full SDD workflow

## Configuration
- **Artifacts Path**: {@artifacts_path} → `.zenflow/tasks/{task_id}`

---

## Agent Instructions

If you are blocked and need user clarification, mark the current step with `[!]` in plan.md before stopping.

---

## Workflow Steps

### [x] Step: Requirements
<!-- chat-id: fd617e29-8dbc-41f0-8d81-1942f9395820 -->

Create a Product Requirements Document (PRD) based on the feature description.

1. Review existing codebase to understand current architecture and patterns
2. Analyze the feature definition and identify unclear aspects
3. Ask the user for clarifications on aspects that significantly impact scope or user experience
4. Make reasonable decisions for minor details based on context and conventions
5. If user can't clarify, make a decision, state the assumption, and continue

Save the PRD to `{@artifacts_path}/requirements.md`.

### [x] Step: Technical Specification
<!-- chat-id: fa07f564-20bb-4006-b3f7-d7f50091883a -->

Create a technical specification based on the PRD in `{@artifacts_path}/requirements.md`.

1. Review existing codebase architecture and identify reusable components
2. Define the implementation approach

Save to `{@artifacts_path}/spec.md` with:
- Technical context (language, dependencies)
- Implementation approach referencing existing code patterns
- Source code structure changes
- Data model / API / interface changes
- Delivery phases (incremental, testable milestones)
- Verification approach using project lint/test commands

### [x] Step: Planning
<!-- chat-id: 0f2ddee7-dac1-4e7a-bf5c-29a0d45fd8f1 -->

Create a detailed implementation plan based on `{@artifacts_path}/spec.md`.

1. Break down the work into concrete tasks
2. Each task should reference relevant contracts and include verification steps
3. Replace the Implementation step below with the planned tasks

### [x] Step 1: Enumerate output helpers and stats header (R1.1, R1.2, R1.6)
<!-- chat-id: 00683c59-7399-4f73-b80b-59c7f0bad3bc -->

Add foundational rendering helpers and the summary statistics header to `enumerate.py`. The `PROBE_DISPLAY_NAMES` constant and `_severity_badge()` / `_severity_badge_plain()` helpers already exist. This step focuses on wiring them into the rendering pipeline and adding tests.

**Changes to `src/lazyssh/plugins/enumerate.py`:**
- In `render_rich()` (line 1437): After `console.rule(...)`, print `_render_stats_header(findings, snapshot)` before the Quick Wins section
- In category table loop (line 1531): Replace `f"[accent]{key}[/accent]"` with human-friendly display names using `PROBE_DISPLAY_NAMES.get(key, key)`. Show raw key in dim when display name differs: `f"[accent]{display_name}[/accent] [dim]({key})[/dim]"` when `display_name != key`, otherwise just `f"[accent]{key}[/accent]"`
- In Priority Findings table (line 1497): Replace `f"[{style}]{finding.severity.upper()}[/]"` with `_severity_badge(finding.severity)` call
- In Quick Wins table (line 1461): Replace `f"[{style}]{tier.upper()}[/]"` with styled badge using `_severity_badge()` for severity-based coloring (keep tier text but use `_severity_badge_plain` pattern for tier styling)

**Changes to `tests/test_enumerate_summary.py`:**
- Add `TestSeverityBadge` class: test `_severity_badge()` returns correct `Text` with correct style for each severity level (critical, high, medium, info)
- Add `TestSeverityBadgePlain` class: test `_severity_badge_plain()` returns `[CRITICAL]`, `[HIGH]`, etc.
- Add `TestRenderStatsHeader` class: test `_render_stats_header()` counts match input findings; test with zero findings; test probe failure counting
- Add `TestRenderStatsHeaderPlain` class: test plain-text output format

**Verification:** `make check && make test`

### [x] Step 2: Enumerate exploit command styling, evidence, and Quick Wins tiers (R1.3, R1.5, R1.7)
<!-- chat-id: 68c12589-8665-498c-871f-8cb4f681c76a -->

Enhance visual differentiation for exploit commands, add tier separators to Quick Wins, and show evidence in Priority Findings.

**Changes to `src/lazyssh/plugins/enumerate.py`:**
- In Quick Wins section (lines 1449-1464):
  - Before each new tier's rows (except the first), call `qw_table.add_section()` to insert a visual divider
  - Add a tier label row: `qw_table.add_row(f"[bold]{tier.upper()} ({len(tier_findings)} findings)[/bold]", "", "")` before the tier's findings
- In Quick Wins exploit commands styling (line 1459): Change executable command style from `"foreground"` to `"highlight"` and prefix with `"$ "`
- In Priority Findings detail_text (lines 1488-1495): Change executable command style from `"foreground"` to `"highlight"`
- After exploit commands in Priority Findings (after line 1495): Append evidence items to `detail_text`:
  ```python
  if finding.evidence:
      detail_text.append("\n")
      for ev in finding.evidence[:4]:
          detail_text.append(f"\n  * {ev}", style="accent")
  ```

**Changes to `tests/test_enumerate_summary.py`:**
- Add `TestQuickWinsTiers` class: test that `_group_quick_wins()` groups findings correctly by tier; verify tier ordering
- Add test for render_rich Quick Wins with multiple tiers (mock console, verify `add_section` is called)
- Add test for evidence rendering in Priority Findings rich output

**Verification:** `make check && make test`

### [x] Step 3: Category panel border differentiation (R1.4) and plain-text parity (R1.8)
<!-- chat-id: bbde8588-d5d4-44ff-a568-a761a010c4c5 -->

Color-code category panel borders based on finding severity and probe failures. Ensure plain-text rendering has full parity.

**Changes to `src/lazyssh/plugins/enumerate.py`:**
- Before the category panel loop (before line 1517), build lookup sets:
  ```python
  categories_with_criticals: set[str] = {f.category for f in findings if f.severity == "critical"}
  categories_with_failures: set[str] = set()
  for cat, mapping in snapshot.probes.items():
      if any(p.status != 0 for p in mapping.values()):
          categories_with_failures.add(cat)
  ```
- In the category panel (line 1549): Replace `border_style="border"` with:
  - `border_style="error"` if `category in categories_with_criticals`
  - `border_style="warning"` if `category in categories_with_failures`
  - `border_style="success"` otherwise
- In `render_plain()` category section (line 1403): Use `PROBE_DISPLAY_NAMES.get(key, key)` (already done at line 1404, verified)
- Verify plain text already has stats header (line 1354) and severity badges (lines 1380, 1365) - already implemented

**Changes to `tests/test_enumerate_summary.py`:**
- Add `TestCategoryBorderLogic` class: test that category with critical finding gets "error" border; category with probe failure gets "warning"; all-pass gets "success"
- Add test for `render_plain()` output: verify stats header line format, verify display names used

**Verification:** `make check && make test`

### [x] Step 4: Autopwn stdin isolation and docker command sanitization (R2.1, R2.3)
<!-- chat-id: a2d27d6a-a1e0-48a8-b717-bace34badb62 -->

Fix the critical hang issue by isolating stdin and sanitizing docker commands at both source and runtime level.

**Changes to `src/lazyssh/plugins/_autopwn.py`:**
- In `_ssh_exec()` (line 90): Add `stdin=subprocess.DEVNULL` to the `subprocess.run()` call:
  ```python
  result = subprocess.run(
      ssh_cmd,
      text=True,
      capture_output=True,
      stdin=subprocess.DEVNULL,
      timeout=timeout,
  )
  ```
- Add new module-level function `_sanitize_docker_command(command: str) -> str`:
  - Use regex to strip `-it`, `-ti`, `--interactive`, `--tty` flags from docker/podman commands
  - Add `--rm` if not already present
  - Return sanitized command
- In `_exploit_docker_escape()` (line 393-396): Call `_sanitize_docker_command(cmd)` on the command before display/execution

**Changes to `src/lazyssh/plugins/_gtfobins_data.py`:**
- Line 175: Change `"sudo docker run -v /:/hostfs -it alpine chroot /hostfs /bin/bash"` to `"sudo docker run -v /:/hostfs --rm alpine chroot /hostfs /bin/bash"`
- Line 181: Change `"docker run -v /:/hostfs -it alpine chroot /hostfs /bin/bash"` to `"docker run -v /:/hostfs --rm alpine chroot /hostfs /bin/bash"`

**Changes to `src/lazyssh/plugins/enumerate.py`:**
- Line 817: Change `"docker run -v /:/hostfs -it alpine chroot /hostfs /bin/bash"` to `"docker run -v /:/hostfs --rm alpine chroot /hostfs /bin/bash"`

**Changes to `tests/test_autopwn.py`:**
- Add `TestSshExecStdinIsolation` class: test that `subprocess.run` is called with `stdin=subprocess.DEVNULL` by inspecting mock call kwargs
- Add `TestSanitizeDockerCommand` class: test stripping `-it`, `-ti`, `--interactive`, `--tty`; test `--rm` insertion; test passthrough for non-docker commands; test idempotency
- Update `TestAutopwnEngineDockerEscape` tests: update expected commands in assertions to not contain `-it`

**Verification:** `make check && make test`

### [x] Step 5: Autopwn interactive command detection (R2.2)
<!-- chat-id: 812b0237-3763-4ed4-ba57-ce0e4901d261 -->

Add pre-flight classification of interactive commands with appropriate warnings.

**Changes to `src/lazyssh/plugins/_autopwn.py`:**
- Add module-level constant `_INTERACTIVE_PATTERNS`:
  ```python
  _INTERACTIVE_PATTERNS: list[tuple[str, str]] = [
      (r"\bpkexec\b", "pkexec requires a polkit agent / password prompt"),
      (r"\b(docker|podman)\b.*\s-[a-z]*[it][a-z]*\b", "docker -it flags require a TTY"),
      (r"\b(vim|vi|less|more|man|ed|nano)\b", "editor/pager requires terminal interaction"),
      (r"\bsu\s", "su requires password input"),
  ]
  ```
- Add function `_classify_interactive(command: str) -> str | None`: iterate `_INTERACTIVE_PATTERNS`, return first matching reason or `None`
- Add `interactive_warning: str = ""` field to `ExploitAttempt` dataclass
- In each exploit method (writable_passwd, gtfobins_suid, gtfobins_sudo, docker_escape, writable_cron, writable_service):
  - Call `_classify_interactive(cmd)` before display
  - If interactive and dry_run: append `[INTERACTIVE]` badge to console output
  - If interactive and live: print warning with reason before execution
  - Store warning in `ExploitAttempt.interactive_warning`

**Changes to `tests/test_autopwn.py`:**
- Add `TestClassifyInteractive` class: test pkexec detected, docker -it detected, vim/less/nano detected, su detected, safe commands return None
- Add test for interactive warning display in dry-run mode
- Add test for interactive warning in live mode

**Verification:** `make check && make test`

### [x] Step 6: Autopwn execution progress and timing (R2.4)
<!-- chat-id: 1f3b24f3-375b-4ef1-a5f4-9f59664d71f5 -->

Add Rich spinner during command execution and timing data to exploit attempts.

**Changes to `src/lazyssh/plugins/_autopwn.py`:**
- Add imports: `import time` and `from rich.status import Status` (inside try/except Rich block)
- Add `duration: float = 0.0` field to `ExploitAttempt` dataclass
- Add method `_exec_with_progress(self, command: str, timeout: int = 30) -> tuple[int, str, str, float]` to `AutopwnEngine`:
  - Wrap `_ssh_exec()` call with Rich `Status` context manager showing `f"Executing: {command[:60]}... (timeout: {timeout}s)"`
  - Use `time.monotonic()` for timing
  - Print elapsed time after completion: `console.print(f"  [dim]Completed in {elapsed:.1f}s[/dim]")`
  - Return `(exit_code, stdout, stderr, elapsed)`
- Replace all direct `_ssh_exec()` calls in exploit methods with `self._exec_with_progress()`:
  - `_exploit_writable_passwd` (line 220)
  - `_exploit_gtfobins_suid` (line 286)
  - `_exploit_gtfobins_sudo` (line 365)
  - `_exploit_docker_escape` (line 419)
  - `_exploit_writable_cron` (line 481)
  - `_exploit_writable_service` (line 559)
- Store `elapsed` in `ExploitAttempt.duration` field

**Changes to `tests/test_autopwn.py`:**
- Add `TestExecWithProgress` class: test that `_exec_with_progress` returns timing data > 0; test it wraps `_ssh_exec` correctly
- Update existing live execution tests to verify `duration` field is populated on attempts

**Verification:** `make check && make test`

### [x] Step 7: Autopwn mode banner and enhanced summary (R2.5, R2.6)
<!-- chat-id: f8373caa-089c-4f8f-9b42-8b8b5a072a60 -->

Add prominent mode banners and replace the summary with a Rich table.

**Changes to `src/lazyssh/plugins/_autopwn.py`:**
- Add imports: `from rich import box` and `from rich.panel import Panel` and `from rich.table import Table` (inside try/except Rich block)
- In `run()` method (after line 134, after sorting exploitable findings):
  - **DRY-RUN banner**: `Panel("NO COMMANDS WILL BE EXECUTED\nReview the commands below. Re-run without --dry-run to execute.", title="DRY-RUN MODE", border_style="warning", box=box.HEAVY)`
  - **LIVE banner**: `Panel("LIVE EXPLOITATION MODE\nCommands will be executed on the remote host. Each requires confirmation.", title="LIVE MODE", border_style="error", box=box.HEAVY)` followed by `_confirm("Proceed with live exploitation?")` — return early if declined
- Replace `_render_summary()` body (lines 599-617):
  - Build a Rich `Table` with columns: `#`, `Technique`, `Target`, `Command` (truncated to 50 chars), `Status` (styled badge), `Duration`
  - Iterate `self.result.attempts`, add rows with appropriate styling
  - Wrap in Panel with title "Autopwn Summary"
  - If any rollback commands, render a separate sub-table with `border_style="warning"`

**Changes to `tests/test_autopwn.py`:**
- Add `TestModeBanner` class: test dry-run banner displays (mock console.print, check Panel); test live banner displays and confirmation
- Add `TestLiveBannerDeclined` class: test that declining live banner returns empty result
- Add `TestEnhancedSummary` class: test summary table renders with correct columns; test rollback sub-table renders when present

**Verification:** `make check && make test`

### [x] Step 8: Autopwn timeout configuration (R2.7)
<!-- chat-id: 82287172-fb82-437b-9b62-d7e35d6b21a8 -->

Add `--timeout` CLI flag support.

**Changes to `src/lazyssh/plugins/enumerate.py`:**
- In `main()` (around line 1628): Parse `--timeout N` from `sys.argv`:
  ```python
  timeout_val = 30
  if "--timeout" in sys.argv:
      idx = sys.argv.index("--timeout")
      if idx + 1 < len(sys.argv):
          try:
              timeout_val = max(5, min(120, int(sys.argv[idx + 1])))
          except ValueError:
              pass
  ```
- Pass `timeout=timeout_val` to `AutopwnEngine(snapshot, findings, dry_run=is_dry_run, timeout=timeout_val)`

**Changes to `src/lazyssh/plugins/_autopwn.py`:**
- In `AutopwnEngine.__init__()`: Add `timeout: int = 30` parameter, store as `self.timeout = max(5, min(120, timeout))`
- In `_exec_with_progress()`: Use `min(self.timeout, timeout)` as the effective timeout passed to `_ssh_exec()`

**Changes to `tests/test_autopwn.py`:**
- Add `TestTimeoutConfiguration` class: test default timeout is 30; test clamping to 5-120 range; test timeout passed through to `_ssh_exec`
- Test that per-exploit timeouts are capped by global timeout

**Verification:** `make check && make test`

### [x] Step 9: Final verification and CHANGELOG
<!-- chat-id: 794fe2db-26d3-450c-a7e4-2859845f64b7 -->

Run full verification suite and update CHANGELOG.

- Run `make verify` (check + test + build)
- Fix any remaining lint, type, or test failures
- Update `CHANGELOG.md` under `## [Unreleased]`:
  - **Added**: Summary statistics header for enumerate output
  - **Added**: Enhanced severity badges with bold/reverse styling for critical and high findings
  - **Added**: Exploit command highlighting with `$` prefix and distinct color
  - **Added**: Category panel border color coding (red for critical findings, yellow for failures, green for clean)
  - **Added**: Quick Wins tier separators and count headers
  - **Added**: Human-friendly probe display names in category tables
  - **Added**: Evidence items in Priority Findings detail column
  - **Added**: Autopwn mode banners (dry-run and live)
  - **Added**: Rich table summary for autopwn results with timing and rollback info
  - **Added**: `--timeout` flag for autopwn execution
  - **Fixed**: Autopwn engine hanging on interactive commands (pkexec, docker -it) by isolating stdin with `subprocess.DEVNULL`
  - **Fixed**: Docker escape commands using `-it` flags that require TTY allocation
  - **Changed**: Docker commands in GTFOBins database stripped of `-it` flags, replaced with `--rm`
  - **Changed**: Autopwn execution now shows Rich spinner with progress feedback

### [x] Step: remove autopwn and ensure updated documentation
<!-- chat-id: eac58c0c-012e-4f44-95ae-b6e8cb77fc2d -->

lets remove autopwn, but keep the "dry run" feature to always give suggestions at the bottom. It shouldnt require any additional flags, just part of the enumerate plugin.

Lets also ensure all these new features are properly documentes in our user docs
