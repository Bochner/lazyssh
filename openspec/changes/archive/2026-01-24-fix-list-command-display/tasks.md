## 1. Implementation
- [x] 1.1 Update `cmd_list()` in `src/lazyssh/command_mode.py` to call `self.show_status()` when connections exist
- [x] 1.2 Remove misleading comment about status already being shown

## 2. Validation
- [x] 2.1 Run `make check` to verify lint and type checking pass
- [x] 2.2 Run `make test` to verify no test regressions
- [ ] 2.3 Manual test: start lazyssh, establish connection, run `list` command, verify display
