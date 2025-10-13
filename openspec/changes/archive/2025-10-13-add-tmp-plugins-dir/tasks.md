## 1. Implementation
- [x] 1.1 Ensure `/tmp/lazyssh/plugins` is created on startup with `0700` permissions
- [x] 1.2 Include `/tmp/lazyssh/plugins` in plugin discovery precedence
- [x] 1.3 Update docs (`docs/Plugin/plugins.md`, `docs/commands.md`) to reflect location and order

## 2. Testing & Validation
- [x] 2.1 Add tests: startup creates directory; discovery prefers `/tmp/lazyssh/plugins` over built-ins
- [x] 2.2 Verify warnings are logged on creation failures without crashing (unit test)
- [x] 2.3 Validate spec with `openspec validate add-tmp-plugins-dir --strict`
