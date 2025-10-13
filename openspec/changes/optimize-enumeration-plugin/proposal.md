## Why
- Current enumerate plugin spawns dozens of short SSH commands which adds round-trip latency even with control sockets, making triage slow during engagements.
- Users report the built-in plugin failing validation because the packaged file lacks the executable bit after installation.
- Enumeration output leans on ad-hoc ANSI formatting and large raw dumps, which does not align with the Dracula-themed UI or highlight risky findings for quick decision making.

## What Changes
- Collect remote telemetry through a single batched script execution, cache expensive results, and surface a concise "priority findings" summary (covering sudo access, passwordless sudo, SUID binaries, world-writable directories, exposed services, weak SSH settings, suspicious cron timers, and similar quick wins) alongside full data.
- Render plugin output with the shared Rich console/theme, including section panels and color-coded callouts that draw attention to misconfigurations.
- Make plugin validation resilient when Python plugins lack the executable bit by either repairing permissions for installed assets or executing them via the interpreter.

## Impact
- Improves reconnaissance speed and increases signal-to-noise for penetration testers using LazySSH.
- Requires updates to the enumerate plugin and plugin manager validation logic; dependent CLI commands remain unchanged.
- Adds new spec coverage for enumeration performance expectations and built-in plugin readiness.
