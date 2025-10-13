# Remove Windows Support

## Why

Windows OpenSSH client does not support the `-M` (master mode) flag for SSH control sockets because it relies on Unix domain sockets which are not fully compatible on Windows. This limitation makes LazySSH's core functionality—persistent SSH connections via control sockets—unreliable or non-functional on Windows. Rather than maintain partial or broken Windows support, we will remove Windows support entirely and direct users to use WSL (Windows Subsystem for Linux) if they are on Windows.

## What Changes

- **BREAKING**: Remove Windows as a supported platform
- Remove Windows-specific documentation and troubleshooting sections
- Update platform requirements to only list Linux/Unix and macOS
- Simplify documentation by removing platform-specific notes about Windows
- Add clear guidance that Windows users should use WSL
- Update project.md to reflect the removal of Windows support
- Simplify the codebase by removing Windows-specific workarounds if any exist

## Impact

- Affected specs: `platform-compatibility`
- Affected code:
  - `src/lazyssh/ssh.py` (uses `-M` flag that doesn't work on Windows)
  - Documentation files: README.md, docs/troubleshooting.md, docs/user-guide.md
  - `openspec/project.md` (platform requirements section)
- Users: Windows users will need to use WSL to run LazySSH
- Benefits: Simpler documentation, clearer platform requirements, no need to maintain Windows-specific code paths
