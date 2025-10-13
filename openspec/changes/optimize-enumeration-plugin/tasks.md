## 1. Implementation
- [x] 1.1 Inventory current enumeration commands and design the batched remote script, cataloguing summary heuristics (sudo/passwordless sudo, writable paths, SUID counts, exposed services, weak SSH configs, suspicious cron/systemd timers, kernel drift, etc.).
- [x] 1.2 Refactor `enumerate.py` to execute the batched script once, parse structured output into reusable data structures, and cache expensive results.
- [x] 1.3 Emit JSON plus Rich-rendered sections that align with Dracula theming, highlighting priority findings via standardized panels/badges and ensuring the summary is persisted with log artifacts.
- [x] 1.4 Update plugin validation/execution so packaged Python plugins run correctly when lacking the executable bit by repairing permissions or invoking them via the interpreter.

## 2. Validation
- [x] 2.1 Add automated coverage (unit or integration) for the parsing/summary pipeline and the permissive validation path.
- [x] 2.2 Run the full test suite plus a targeted enumerate plugin smoke test to confirm output formatting and logging.

## 3. Documentation
- [x] 3.1 Refresh user-facing documentation or inline help to describe the new summary behavior and plugin readiness assurances.
