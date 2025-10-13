# Design: Runtime plugin directory under `/tmp/lazyssh/plugins`

We extend the plugin search paths with a tmpfs-backed directory to allow easy, ephemeral plugin deployment without mutating installed package contents.

## Directory
- Path: `/tmp/lazyssh/plugins`
- Created on startup with `0700` permissions
- Not required to persist across reboots

## Discovery Order
1. `LAZYSSH_PLUGIN_DIRS` (user override)
2. `~/.lazyssh/plugins` (user home)
3. `/tmp/lazyssh/plugins` (runtime)
4. Packaged `lazyssh/plugins/` (built-ins)

## Safety
- Ignore non-existent directories silently
- Do not follow symlinks outside the base dir; skip broken symlinks
- Validate executable bit and shebang as today

## Alternatives Considered
- Using XDG directories; chosen `/tmp` to align with existing runtime paths in LazySSH
- Managing installation via CLI; out of scope for minimal change

## Impact
- Backwards compatible
- Minimal runtime overhead to create directory and add one path to search list
