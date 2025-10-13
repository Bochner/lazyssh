## 1. Implementation
- [x] 1.1 Package built-in plugins as executable data files
- [x] 1.2 Add search path support in `PluginManager` for user directories
- [x] 1.3 Respect `LAZYSSH_PLUGIN_DIRS` env var (colon-separated absolute paths)
- [x] 1.4 Default user directory `~/.lazyssh/plugins` when env not set
- [x] 1.5 Define precedence: env dirs → user dir → packaged dir
- [x] 1.6 Update docs `docs/Plugin/plugins.md` with user directory guidance
- [x] 1.7 Add tests: discovery from user dir, precedence, non-existent dirs ignored
- [x] 1.8 Add install test/assertion: built-in plugins are executable after install

## 2. Validation
- [x] 2.1 `openspec validate add-plugin-exec-and-user-dirs --strict`
- [x] 2.2 `pytest -q` all plugin tests

## 3. Release
- [x] 3.1 Bump version and update `CHANGELOG.md`
- [x] 3.2 Publish and verify with `pipx install` smoke test

