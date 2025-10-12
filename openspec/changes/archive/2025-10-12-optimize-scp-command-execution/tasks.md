# Implementation Tasks

## 1. Directory Listing Cache

- [x] 1.1 Add cache data structure to SCPMode class (dict with path → {data, timestamp})
- [x] 1.2 Implement configurable cache TTL (default 30 seconds)
- [x] 1.3 Add cache lookup method before executing SSH commands
- [x] 1.4 Add cache update method after successful SSH command execution
- [x] 1.5 Implement cache invalidation on directory-modifying operations (cd, put, mkdir-like)

## 2. Completion Throttling

- [x] 2.1 Add timestamp tracking for last completion query
- [x] 2.2 Implement minimum delay between completion queries (default 300ms)
- [x] 2.3 Update SCPModeCompleter to check throttle before executing commands
- [x] 2.4 Allow immediate completion on explicit tab press vs. automatic completion

## 3. Debug Mode Toggle

- [x] 3.1 Add 'debug' command to SCPMode commands dictionary
- [x] 3.2 Implement cmd_debug method to toggle debug mode
- [x] 3.3 Display current debug mode status when toggled
- [x] 3.4 Update help text to include debug command

## 4. Optimize Command Execution

- [x] 4.1 Review all _execute_ssh_command calls for optimization opportunities
- [x] 4.2 Batch file metadata queries where possible (e.g., in mget)
- [x] 4.3 Reduce duplicate path resolution calls
- [x] 4.4 Add logging for cache hits/misses in debug mode

## 5. Testing and Validation

- [x] 5.1 Test completion performance with cache enabled
- [x] 5.2 Verify cache invalidation works correctly
- [x] 5.3 Test debug command toggle functionality
- [x] 5.4 Measure SSH command reduction (before/after comparison)
- [x] 5.5 Test on high-latency connections to verify improvement

