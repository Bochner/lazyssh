# Full SDD workflow

## Configuration
- **Artifacts Path**: {@artifacts_path} → `.zenflow/tasks/{task_id}`

---

## Agent Instructions

If you are blocked and need user clarification, mark the current step with `[!]` in plan.md before stopping.

---

## Workflow Steps

### [x] Step: Requirements
<!-- chat-id: 70f623ff-a078-4bcf-bdb6-cdc5787abcbc -->

Create a Product Requirements Document (PRD) based on the feature description.

1. Review existing codebase to understand current architecture and patterns
2. Analyze the feature definition and identify unclear aspects
3. Ask the user for clarifications on aspects that significantly impact scope or user experience
4. Make reasonable decisions for minor details based on context and conventions
5. If user can't clarify, make a decision, state the assumption, and continue

Save the PRD to `{@artifacts_path}/requirements.md`.

### [x] Step: Technical Specification
<!-- chat-id: b401c749-0487-4025-a515-584d5f35bdeb -->

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
<!-- chat-id: 6c370874-82e2-4e83-98b0-326de4ce726a -->

Create a detailed implementation plan based on `{@artifacts_path}/spec.md`.

1. Break down the work into concrete tasks
2. Each task should reference relevant contracts and include verification steps
3. Replace the Implementation step below with the planned tasks

### [x] Step 1: Enumeration Probe Expansion and New Heuristics
<!-- chat-id: e4f7d579-1b24-4bb8-94fd-fdb9280bbe4c -->

Expand `_enumeration_plan.py` with ~40 new probes across 7 new categories and ~15 new heuristic definitions. Update `enumerate.py` with new evaluator functions, extended `PriorityFinding` dataclass, and updated category ordering. Add tests for all new evaluators.

**Files to modify:**
- `src/lazyssh/plugins/_enumeration_plan.py` — Add new `RemoteProbe` entries and `PriorityHeuristic` entries
- `src/lazyssh/plugins/enumerate.py` — Extend `PriorityFinding` dataclass (add `exploitation_difficulty: str = ""` and `exploit_commands: list[str] = field(default_factory=list)`), update `SELECTED_CATEGORY_ORDER`, add ~15 new evaluator functions, register in `HEURISTIC_EVALUATORS` dict
- `tests/test_enumerate_summary.py` — Add tests for new evaluators using synthetic `ProbeOutput` data

**Substeps:**
- [ ] Add new probe categories to `_enumeration_plan.py`: `capabilities` (2 probes), `container` (4 probes), `credentials` (7 probes), `writable` (8 probes), `library_hijack` (4 probes), `interesting_files` (5 probes)
- [ ] Add expanded probes to existing categories: `filesystem` (+2: nfs_exports, mounted_nfs), `users` (+3: doas_conf, polkit_rules, pkexec_version)
- [ ] Add ~15 new `PriorityHeuristic` entries to `PRIORITY_HEURISTICS`
- [ ] Extend `PriorityFinding` dataclass with `exploitation_difficulty` and `exploit_commands` fields (backward-compatible defaults)
- [ ] Update `SELECTED_CATEGORY_ORDER` to include new categories
- [ ] Implement all new evaluator functions in `enumerate.py` following the existing `_evaluate_*` pattern (signature: `(snapshot: EnumerationSnapshot, meta: PriorityHeuristic) -> PriorityFinding | None`)
- [ ] Register new evaluators in `HEURISTIC_EVALUATORS` dict
- [ ] Add unit tests for each new evaluator in `test_enumerate_summary.py`
- [ ] Run `make check` to verify ruff + mypy pass

**Spec references:** Sections 1.1, 1.2, 1.6 (PriorityFinding extension)

### [x] Step 2: GTFOBins Database and Lookup Functions
<!-- chat-id: 4a6203e4-99f6-45ee-bbd9-20dcb10682af -->

Create the embedded GTFOBins database covering ~100 common exploitable binaries with SUID, sudo, and capabilities exploitation techniques. Implement lookup functions and unit tests.

**Files to create:**
- `src/lazyssh/plugins/_gtfobins_data.py` — `GTFOBinsEntry` frozen dataclass, `GTFOBINS_DB` tuple (~300-400 entries), `lookup_suid()`, `lookup_sudo()`, `lookup_capabilities()` functions
- `tests/test_gtfobins_data.py` — Data integrity tests (all entries have non-empty fields, valid capabilities), lookup correctness tests for known binaries

**Substeps:**
- [ ] Create `_gtfobins_data.py` with `GTFOBinsEntry` dataclass: `binary: str`, `capability: str` ("suid"/"sudo"/"capabilities"/"file-read"/"file-write"/"shell"), `command_template: str`, `description: str`
- [ ] Populate `GTFOBINS_DB` tuple with entries for ~100 binaries (awk, bash, cat, chmod, cp, curl, docker, env, find, gcc, gdb, git, less, more, mount, nano, nmap, node, openssl, perl, php, pip, python, python3, ruby, rsync, scp, screen, sed, socat, ssh, strace, tar, tee, tmux, vi, vim, watch, wget, zip, zsh, etc.)
- [ ] Implement `lookup_suid(binary_name)`, `lookup_sudo(binary_name)`, `lookup_capabilities(binary_name)` returning `list[GTFOBinsEntry]`
- [ ] Write unit tests validating data integrity and lookup correctness
- [ ] Run `make check`

**Spec references:** Section 1.3

### [ ] Step 3: Kernel Exploit Suggester

Create the kernel exploit database with version-range matching and a lookup function. Wire it into the enumeration evaluator system.

**Files to create:**
- `src/lazyssh/plugins/_kernel_exploits.py` — `KernelExploit` frozen dataclass, `KERNEL_EXPLOITS` tuple (~15-20 CVEs), `suggest_exploits(kernel_version: str)` function with version parsing
- `tests/test_kernel_exploits.py` — Version parsing tests (various kernel version string formats), range matching tests, edge cases

**Files to modify:**
- `src/lazyssh/plugins/enumerate.py` — Add `_evaluate_kernel_exploits` evaluator that calls `suggest_exploits()` and produces findings
- `src/lazyssh/plugins/_enumeration_plan.py` — Add `kernel_exploits` heuristic entry
- `tests/test_enumerate_summary.py` — Add test for kernel exploit evaluator

**Substeps:**
- [ ] Create `_kernel_exploits.py` with `KernelExploit` dataclass: `cve: str`, `name: str`, `min_version: tuple[int, ...]`, `max_version: tuple[int, ...]`, `description: str`, `reference_url: str`
- [ ] Populate `KERNEL_EXPLOITS` with DirtyPipe, DirtyCOW, PwnKit, Overlayfs, Netfilter, Baron Samedit, Polkit, Sequoia, GameOver(lay), Looney Tunables, nf_tables, Dirty Cred, etc.
- [ ] Implement `suggest_exploits()` with robust version string parsing (handles `5.10.100-generic`, `4.15.0-213-generic`, etc.)
- [ ] Wire into `enumerate.py` as a new evaluator + heuristic entry
- [ ] Write unit tests for version parsing and matching
- [ ] Run `make check`

**Spec references:** Section 1.4

### [ ] Step 4: GTFOBins Cross-Reference Integration

Wire the GTFOBins database into the existing SUID and sudo evaluators so they produce actionable exploit commands in findings.

**Files to modify:**
- `src/lazyssh/plugins/enumerate.py` — Update `_evaluate_gtfobins_suid` and `_evaluate_gtfobins_sudo` evaluators (created in Step 1) to import and use `lookup_suid()`/`lookup_sudo()` from `_gtfobins_data.py`. Populate `exploit_commands` and `exploitation_difficulty` fields on `PriorityFinding`.
- `tests/test_enumerate_summary.py` — Add/update tests verifying GTFOBins cross-references produce exploit commands for synthetic SUID/sudo probe output

**Substeps:**
- [ ] Update `_evaluate_gtfobins_suid` to extract binary names from `suid_files` probe, cross-reference with `lookup_suid()`, include matched commands in `exploit_commands` field
- [ ] Update `_evaluate_gtfobins_sudo` to parse sudo-allowed commands from `sudo_check` probe, cross-reference with `lookup_sudo()`, include matched commands in `exploit_commands` field
- [ ] Update `_evaluate_dangerous_capabilities` to use `lookup_capabilities()` where applicable
- [ ] Set `exploitation_difficulty` ("instant", "easy", "moderate") on all findings that have exploit commands
- [ ] Add/update tests with synthetic data that triggers GTFOBins matches
- [ ] Run `make check`

**Spec references:** Sections 1.2, 1.3, 1.6

### [ ] Step 5: Autopwn Engine

Create the autopwn exploitation engine that takes enumeration findings and attempts automated exploitation with user confirmation and dry-run support.

**Files to create:**
- `src/lazyssh/plugins/_autopwn.py` — `ExploitAttempt` dataclass, `AutopwnResult` dataclass, `AutopwnEngine` class with methods: `run()`, `_exploit_writable_passwd()`, `_exploit_gtfobins_suid()`, `_exploit_gtfobins_sudo()`, `_exploit_docker_escape()`, `_exploit_writable_cron()`, `_exploit_writable_service()`
- `tests/test_autopwn.py` — Tests with mocked `subprocess.run` and `Confirm.ask`: dry-run output, command construction, rollback logic, user confirmation flow

**Files to modify:**
- `src/lazyssh/plugins/enumerate.py` — Add `--autopwn` and `--dry-run` flag parsing to `main()`, integrate `AutopwnEngine` invocation after finding generation

**Substeps:**
- [ ] Create `_autopwn.py` with `ExploitAttempt` and `AutopwnResult` dataclasses
- [ ] Implement `AutopwnEngine.__init__()` accepting `EnumerationSnapshot`, findings list, and `dry_run` flag
- [ ] Implement `_exploit_writable_passwd()` — generate password hash, append root user, verify
- [ ] Implement `_exploit_gtfobins_suid()` — execute GTFOBins command for SUID binaries
- [ ] Implement `_exploit_gtfobins_sudo()` — execute GTFOBins command for sudo-allowed binaries
- [ ] Implement `_exploit_docker_escape()` — mount host fs via docker
- [ ] Implement `_exploit_writable_cron()` — inject command into writable cron file
- [ ] Implement `_exploit_writable_service()` — modify writable systemd service
- [ ] Implement `run()` orchestrator: iterate findings, match to exploit methods, confirm with user, execute, collect results
- [ ] Integrate into `enumerate.py` `main()`: parse `--autopwn`/`--dry-run` flags, invoke engine after findings
- [ ] Write tests with mocked subprocess and Confirm.ask
- [ ] Run `make check`

**Spec references:** Section 1.5

### [ ] Step 6: Output Enhancements — Quick Wins and Severity

Add the Quick Wins summary section to Rich and plain-text output, add `critical` severity level, and display exploit commands in findings output.

**Files to modify:**
- `src/lazyssh/plugins/enumerate.py` — Add `"critical"` to `SEVERITY_STYLES`, implement Quick Wins summary section in `render_rich()` and `render_plain()`, display `exploit_commands` in finding detail output, update `build_json_payload()` to include new fields
- `tests/test_enumerate_summary.py` — Test Quick Wins rendering, test new severity in output, test JSON includes new fields

**Substeps:**
- [ ] Add `"critical": "error"` to `SEVERITY_STYLES`
- [ ] Implement Quick Wins summary in `render_rich()`: filter findings by `exploitation_difficulty`, group into "Instant" / "Easy" / "Moderate" sections, display at top of output
- [ ] Implement Quick Wins summary in `render_plain()` with same logic
- [ ] Display `exploit_commands` inline with finding evidence when present
- [ ] Update `build_json_payload()` / `PriorityFinding.to_dict()` to include `exploitation_difficulty` and `exploit_commands`
- [ ] Add rendering tests
- [ ] Run `make check`

**Spec references:** Section 1.6

### [ ] Step 7: Architecture Detection and Upload-Exec Plugin

Create the remote architecture detection module and the complete upload-and-execute plugin with CLI, interactive mode, and msfvenom integration.

**Files to create:**
- `src/lazyssh/plugins/_arch_detection.py` — `RemoteArch` frozen dataclass, `ARCH_MAP` dict, `detect_remote_arch()` function using SSH control socket
- `src/lazyssh/plugins/upload_exec.py` — Full plugin with metadata headers, argparse CLI, interactive menu (Rich prompts), upload via SCP, remote execution, msfvenom integration (`MsfvenomConfig`, `PAYLOAD_PRESETS`, `generate_msfvenom_payload()`, `get_handler_command()`), cleanup logic
- `tests/test_upload_exec.py` — Tests for: argument parsing, architecture detection/mapping, SCP upload command construction, msfvenom command construction, interactive mode flow (mocked prompts), cleanup logic, dry-run mode

**Files to modify:**
- `src/lazyssh/plugin_manager.py` — Add `LAZYSSH_CONNECTION_DIR` to `_prepare_plugin_env()`: `env["LAZYSSH_CONNECTION_DIR"] = connection.connection_dir`

**Substeps:**
- [ ] Create `_arch_detection.py` with `RemoteArch` dataclass and `ARCH_MAP`
- [ ] Implement `detect_remote_arch()` using `subprocess.run` with SSH control socket (reads `uname -m` and `uname -s`)
- [ ] Create `upload_exec.py` with plugin metadata headers
- [ ] Implement argument parsing (argparse): positional FILE_PATH, --args, --no-cleanup, --background, --timeout, --output-file, --msfvenom, --payload, --lhost, --lport, --encoder, --iterations, --format, --dry-run
- [ ] Implement `_scp_upload()` using `LAZYSSH_SOCKET_PATH` control socket
- [ ] Implement core upload-and-execute flow: validate file, create remote staging dir, upload, chmod +x, execute, stream output, cleanup
- [ ] Implement msfvenom integration: `MsfvenomConfig` dataclass, `PAYLOAD_PRESETS`, `generate_msfvenom_payload()`, `get_handler_command()`
- [ ] Implement interactive mode with Rich prompts: menu (upload/msfvenom/upload-only), payload selection, LHOST/LPORT prompts
- [ ] Add `LAZYSSH_CONNECTION_DIR` to `_prepare_plugin_env()` in `plugin_manager.py`
- [ ] Write comprehensive tests with mocked subprocess, shutil.which, and prompts
- [ ] Run `make check`

**Spec references:** Sections 2.1-2.7, 3.1

### [ ] Step 8: Final Integration, CHANGELOG, and Verification

End-to-end integration verification, CHANGELOG update, and full `make verify` pass.

**Files to modify:**
- `CHANGELOG.md` — Add entries under `[Unreleased]` for: expanded enumeration probes, GTFOBins integration, kernel exploit suggester, autopwn engine, Quick Wins output, upload-exec plugin, msfvenom integration, new `LAZYSSH_CONNECTION_DIR` env var

**Substeps:**
- [ ] Run `make verify` (check + test + build) and fix any failures
- [ ] Update CHANGELOG.md with all user-facing changes
- [ ] Verify plugin discovery: both `enumerate` and `upload-exec` appear in packaged plugins
- [ ] Verify `--json` output includes new `exploitation_difficulty` and `exploit_commands` fields
- [ ] Final `make verify` pass — record results in plan.md

**Spec references:** Section 3.3, Phase 6
