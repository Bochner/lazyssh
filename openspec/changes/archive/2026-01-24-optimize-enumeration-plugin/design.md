## Goals
- Reduce end-to-end runtime for the enumerate plugin by minimizing SSH round trips while keeping output coverage intact.
- Present high-signal findings immediately with Dracula-themed Rich components and keep JSON/plain-text parity.
- Eliminate "file is not executable" failures for packaged Python plugins without loosening validation for arbitrary shell plugins.

## Non-Goals
- Adding new remote dependencies beyond standard GNU/Linux utilities already probed today.
- Implementing privileged operations or automatic exploitation; focus remains on enumeration and highlighting risk indicators.
- Replacing the existing `plugin run` UX outside of plugin-rendered output.

## Approach
### Batched Remote Execution
- Build a single heredoc-driven shell script that runs once via the control socket and prints JSON segments per category (`system`, `users`, `network`, etc.).
- For commands that may hang, wrap them with timeouts (e.g., `timeout 5s`) and consistent fallbacks, mirroring current graceful degradation behavior.
- Parse the combined JSON locally into a dataclass; cache the raw payload for logging to avoid recomputation when writing artifacts.

### Priority Findings Heuristics
- Derive quick checks after parsing (e.g., detect membership in `sudo`/`wheel`, passwordless sudo rules, count SUID/SGID files, flag world-writable directories outside `/tmp`, highlight listening services bound to 0.0.0.0, identify weak SSH daemon settings, surface suspicious cron/systemd timers, and note kernel or package manager anomalies).
- Surface the findings as a concise list with severity tagging (`high`, `medium`, `info`) and expose the same structure inside the JSON output.

### Rich/Dracula Rendering
- Import the shared `console_instance` helpers to render panels, tables, and highlight text using the Draco theme tokens.
- Provide a plain-text fallback for environments that disable Rich (`LAZYSSH_NO_RICH`, `plain_text`) so the plugin remains usable over narrow terminals.
- Keep section dumps collapsible by summarizing first, then offer `console.print` expanders (or clear headings) before streaming large raw results.

### Plugin Validation Resilience
- During discovery/validation, detect Python plugins missing execute permissions and emit a warning while marking them valid when callable via `sys.executable`.
- For built-in assets, attempt a one-time chmod on installation paths when the filesystem is writable, but fall back gracefully if it is not.
- Preserve strict validation for shell plugins to avoid running non-executable scripts accidentally.

## Risks & Mitigations
- **Large payloads**: Combined JSON may be sizeable; mitigate by streaming to stdout as chunks or compressing whitespace, and continue to write artifacts asynchronously.
- **Remote command compatibility**: Some utilities differ across distros; reuse existing fallback logic and guard heuristics to skip when data is missing.
- **Permission repairs**: Attempts to chmod in site-packages could fail; handle exceptions and ensure validation still passes when interpreter execution is possible.
