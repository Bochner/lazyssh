# Optimize SCP Command Execution

## Why

SCP mode currently executes excessive SSH commands, particularly during tab completion, where every keystroke triggers a new `find` or `ls` command to the remote server. Debug mode logging reveals this inefficiency and cannot be disabled at runtime, flooding the console with verbose output.

This creates performance issues and unnecessary network traffic, especially on high-latency connections or slow remote systems.

## What Changes

- **Add directory listing cache** with configurable TTL to reduce redundant SSH commands during completion
- **Implement completion throttling** to limit completion query frequency during rapid typing
- **Add debug command** to toggle debug mode on/off within SCP mode
- **Optimize file path resolution** to batch queries where possible
- **Add cache invalidation** on directory changes (cd, put, etc.)

## Impact

- **Affected specs**: `scp-mode`
- **Affected code**: 
  - `src/lazyssh/scp_mode.py` - Add caching mechanism, throttling, and debug command
  - `src/lazyssh/logging_module.py` - Expose debug mode toggle functionality
- **Performance improvement**: Reduce SSH command count by 80-90% during typical completion workflows
- **User experience**: More responsive completion, cleaner console output, runtime debug control

