# PRD: Enumerate Plugin Enhancement & Autopwn UX Hardening

## Overview

Two distinct improvements to the LazySSH enumeration subsystem:

1. **Enumerate Output Polish** - Improve visual hierarchy and colorization of the enumerate plugin's Rich output so that critical findings, exploit commands, and status indicators "pop" for the operator.
2. **Autopwn Interactive-Command Safety** - Prevent the autopwn engine from hanging LazySSH when it encounters commands that require interactive input (e.g., `pkexec`, password prompts, `-it` docker flags) and provide clear UI feedback throughout the exploitation flow.

---

## Problem Statement

### Enumerate Output

The current `render_rich()` output is functional but flat. Specific issues:

- **Severity badges lack visual weight.** Severity labels (CRITICAL, HIGH, MEDIUM, INFO) use theme styles but don't stand out against the surrounding table text. They need stronger differentiation (e.g., bold + inverse/background color for CRITICAL).
- **Exploit commands blend into detail text.** Commands embedded in findings use `dim` style, making them harder to spot. Operators need to quickly copy/paste these.
- **Category sections are uniform.** All category panels use the same `border` style regardless of whether they contain failures. A category with all-green checks looks identical to one with multiple failures.
- **Quick Wins section could be more scannable.** The difficulty tiers (INSTANT/EASY/MODERATE) need clearer visual separation (e.g., section dividers or tier-grouped sub-headers).
- **No summary statistics header.** There's no at-a-glance count of findings by severity at the top of the output.
- **Evidence items in findings are plain.** Evidence bullets in the Priority Findings detail column aren't visually distinct from the detail narrative.
- **Check names in category tables aren't descriptive enough.** Raw probe keys like `suid_files` are shown directly; a human-friendly label would improve readability.

### Autopwn Engine

The autopwn engine has a critical hang issue and several UX gaps:

- **Interactive commands hang the process.** `_ssh_exec()` uses `subprocess.run()` with `capture_output=True` but no `stdin` control. Commands that prompt for passwords (e.g., `pkexec /bin/sh`, `sudo` without NOPASSWD) inherit stdin and block indefinitely until the 30s timeout. During this period, LazySSH is completely unresponsive.
- **Docker `-it` flags cause hangs.** The default docker escape command includes `-it` (interactive + TTY) flags, but SSH is executed without `-t` (no PTY allocation), so the command hangs.
- **GTFOBins commands may open interactive editors/shells.** Commands like `vim -c ':!/bin/sh'` or `less` expect terminal interaction that isn't available.
- **No progress feedback during exploit execution.** When `_ssh_exec()` is running (up to 30-60s), the operator sees nothing - no spinner, no status indicator.
- **Summary output is minimal.** The `_render_summary()` shows only counts and rollback commands. It should use a Rich table with technique, target, status, and timing.
- **No pre-flight validation.** The engine doesn't check whether a command is likely to hang (interactive) before attempting execution.
- **Dry-run output lacks visual distinction from live mode.** Only a small yellow label differentiates the two modes.

---

## Requirements

### R1: Enumerate Output Colorization & Visual Hierarchy

#### R1.1 Summary Statistics Header
- Display a severity count bar at the top of the output (before Quick Wins) showing: `N Critical | N High | N Medium | N Info` with corresponding colors.
- Include total probe count and failure count.

#### R1.2 Enhanced Severity Badges
- CRITICAL/HIGH: Bold text on colored background (reverse video) for maximum visibility.
- MEDIUM: Bold yellow text.
- INFO: Standard cyan/info style.
- Apply consistently in both Quick Wins and Priority Findings tables.

#### R1.3 Exploit Command Styling
- Render exploit commands in a distinct monospace style with a visible prefix (`$` for executable commands, `#` for comments/references).
- Use `highlight` (pink) style for executable commands instead of `dim`.
- Keep comment lines in `dim` style for contrast.

#### R1.4 Category Panel Visual Differentiation
- Panels containing any failed probes (exit code != 0): use `warning` border style.
- Panels where all probes succeeded: use `success` border style (subtle green).
- Panels with critical findings related to that category: use `error` border style.

#### R1.5 Quick Wins Section Improvements
- Add a visual separator (rule or divider row) between difficulty tiers.
- Add a tier count indicator: e.g., `INSTANT (3 findings)`.

#### R1.6 Human-Friendly Check Labels
- Add a display name mapping for common probe keys (e.g., `suid_files` -> `SUID Binaries`, `world_writable_dirs` -> `World-Writable Directories`).
- Show the display name in the Check column, with the raw key available in dim text or on hover (plain text fallback shows raw key).

#### R1.7 Evidence Styling
- Prefix evidence items with a bullet character (`*`) in `accent` style.
- Indent evidence under the detail text with a left margin.

#### R1.8 Plain Text Parity
- All visual improvements must have plain-text equivalents that render correctly when `LAZYSSH_PLAIN_TEXT=1` or Rich is unavailable.
- Severity badges in plain text: `[CRITICAL]`, `[HIGH]`, `[MEDIUM]`, `[INFO]`.
- Summary stats in plain text: `Findings: 2 critical, 3 high, 1 medium, 5 info`.

### R2: Autopwn Interactive-Command Safety

#### R2.1 Stdin Isolation
- Modify `_ssh_exec()` to explicitly set `stdin=subprocess.DEVNULL` to prevent commands from reading stdin.
- This causes interactive commands to receive EOF immediately and fail fast rather than hang.

#### R2.2 Interactive Command Detection
- Before execution, classify commands as potentially interactive:
  - Contains `pkexec` (requires polkit agent / password prompt).
  - Contains `-it` or `-ti` docker flags.
  - GTFOBins commands that launch editors (`vim`, `vi`, `less`, `more`, `man`, `ed`).
  - Commands containing `su ` (password prompt expected).
- For detected interactive commands:
  - In **dry-run mode**: display normally with an `[INTERACTIVE]` warning badge.
  - In **live mode**: display a warning that the command is interactive and will likely fail non-interactively. Still allow execution if user confirms (the stdin isolation from R2.1 prevents hangs).

#### R2.3 Docker Command Sanitization
- Strip `-it`, `-ti`, `--interactive`, `--tty` flags from docker commands before execution.
- Replace with `--rm` if not already present.
- Log the original vs. sanitized command for transparency.

#### R2.4 Execution Progress Feedback
- Show a Rich spinner/status indicator while `_ssh_exec()` is running.
- Display: `Executing: <command_summary>... (timeout: Ns)`.
- On completion, show elapsed time.

#### R2.5 Enhanced Summary Table
- Replace the current text-based summary with a Rich table:
  - Columns: `#`, `Technique`, `Target`, `Command`, `Status`, `Duration`.
  - Color-code rows: green for success, red for failure, yellow for dry-run, dim for skipped.
  - Show rollback commands in a separate sub-table below if any exist.

#### R2.6 Mode Banner
- Display a prominent banner at the start of autopwn execution:
  - **DRY-RUN**: Yellow-bordered panel with clear "NO COMMANDS WILL BE EXECUTED" message.
  - **LIVE**: Red-bordered panel with "LIVE EXPLOITATION MODE" warning and confirmation prompt.

#### R2.7 Timeout Configuration
- Add a `--timeout` flag for autopwn (default: 30s, max: 120s).
- Apply the configured timeout to all `_ssh_exec()` calls (override the per-exploit defaults only if lower).

---

## Out of Scope

- New exploit techniques or GTFOBins entries.
- Changes to the enumeration probe catalog (`_enumeration_plan.py`).
- Changes to the heuristic evaluator logic (what gets flagged as critical/high/etc.).
- Plugin system architecture changes.
- New CLI flags beyond `--timeout` for autopwn.
- Remote-side changes (probe scripts, payloads).

---

## Assumptions

1. **Rich is the primary rendering target.** Plain text is a fallback, not the primary design surface. We optimize for Rich output and ensure plain text is functional but not pixel-perfect.
2. **`stdin=DEVNULL` is safe.** Commands that require stdin interaction are expected to fail fast (exit non-zero) when stdin is `/dev/null`. This is the correct behavior - the operator is informed and can run the command manually.
3. **Existing test suite covers autopwn.** The 1,500+ line test file (`test_autopwn.py`) mocks `subprocess.run`. New tests will follow the same mocking pattern.
4. **Human-friendly probe labels are additive.** Adding a display-name mapping doesn't change probe keys or break JSON output. The raw key remains the canonical identifier.
5. **Accessibility themes are preserved.** All colorization changes must respect `LAZYSSH_HIGH_CONTRAST`, `LAZYSSH_COLORBLIND_MODE`, and `LAZYSSH_PLAIN_TEXT` environment variables by using semantic theme styles (e.g., `error`, `warning`) rather than hardcoded colors.

---

## Success Criteria

1. Enumerate output renders with clear visual hierarchy - an operator can identify critical findings within 2 seconds of seeing the output.
2. Autopwn never hangs LazySSH regardless of what commands are attempted.
3. Dry-run mode is visually unambiguous - an operator cannot mistake it for live execution.
4. All existing tests continue to pass.
5. New behavior is covered by tests (interactive detection, stdin isolation, docker sanitization, summary rendering).
6. `make check` passes clean (ruff + mypy).
