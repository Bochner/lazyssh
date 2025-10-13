# Design: Optimize SCP Command Execution

## Context

The SCP mode's tab completion system executes SSH commands on every keystroke to provide file and directory suggestions. With no caching or throttling, this generates hundreds of unnecessary commands during typical usage. Debug logging is currently a compile-time/startup configuration with no runtime control, making it difficult to troubleshoot issues without restarting with different settings.

Key pain points:
- Every keystroke in completion triggers `ls -a` or `find` commands (lines 87, 143-144 in scp_mode.py)
- No caching means identical queries execute repeatedly
- Debug mode floods console with logs but cannot be disabled without restart
- High-latency connections suffer from poor responsiveness

## Goals / Non-Goals

**Goals:**
- Reduce SSH command count by 80-90% through intelligent caching
- Provide responsive completion without sacrificing accuracy
- Enable runtime debug mode control for troubleshooting
- Maintain correctness when remote filesystem changes

**Non-Goals:**
- Implementing file watching or notification-based cache updates
- Complex cache synchronization mechanisms
- Predictive prefetching of directory contents

## Decisions

### 1. Cache Structure

**Decision:** Use simple dict-based cache with TTL

```python
{
    "path": {
        "data": ["file1", "file2", ...],
        "timestamp": datetime,
        "type": "ls" | "find"  # Track command type
    }
}
```

**Rationale:**
- Simple to implement and understand
- No external dependencies
- Memory usage minimal for typical directory sizes
- TTL handles stale data gracefully

**Alternatives considered:**
- LRU cache: More complex, not needed for typical usage patterns
- File watching: Requires remote inotify support, overly complex
- No expiration: Risk of stale data on remote changes

### 2. Cache TTL

**Decision:** Default 30 seconds, configurable via constant

**Rationale:**
- Balance between performance and freshness
- Most operations complete within 30 seconds
- Long enough to cover rapid completion queries
- Short enough to catch external changes reasonably quickly

**Trade-offs:**
- May show stale data if remote system changes externally
- Mitigation: Invalidate on known-modifying operations (put, cd)

### 3. Completion Throttling

**Decision:** 300ms minimum delay between automatic completions, no delay on explicit tab

**Rationale:**
- Most users type slower than 300ms per character
- Explicit tab indicates user wants completion now
- Reduces queries during rapid typing
- Still feels responsive

**Implementation:**
```python
# In SCPModeCompleter
if time_since_last_query < 0.3 and not explicit_tab:
    return cached_results_or_empty
```

### 4. Debug Command

**Decision:** Add 'debug' command that toggles logging_module.DEBUG_MODE

**Rationale:**
- Consistent with other SCP commands (simple keyword)
- Direct control without restart
- Shows current state on toggle

**Command behavior:**
```
scp> debug
Debug mode: ON
scp> debug
Debug mode: OFF
```

### 5. Cache Invalidation Strategy

**Decision:** Invalidate on write operations and directory changes

Invalidation triggers:
- `cd`: Clear all cache (new working directory context)
- `put`: Clear cache for target directory
- `local upload/download`: Clear cache for relevant directories

**Rationale:**
- Conservative approach ensures correctness
- Write operations are infrequent vs. reads
- User-initiated changes known to the system

## Risks / Trade-offs

### Risk: Stale cache on external changes

**Scenario:** User A modifies remote files while user B has cached listing

**Mitigation:**
- 30-second TTL limits staleness window
- Cache invalidation on cd provides fresh view when navigating
- Users can manually cd to force refresh

**Trade-off:** Accept minor staleness for major performance gain

### Risk: Memory usage for large directories

**Scenario:** Caching thousands of files

**Mitigation:**
- Typical directories have <1000 entries
- 1000 filenames × 50 chars × 2 bytes = ~100KB per directory
- Reasonable for modern systems

**Monitoring:** Add debug logging for cache size

### Risk: Throttling delays wanted completions

**Scenario:** User types slowly but still faster than 300ms

**Mitigation:**
- Explicit tab always triggers immediate completion
- Cache provides instant results even when throttled
- 300ms is imperceptible to most users

## Migration Plan

1. **Phase 1: Add cache infrastructure** (non-breaking)
   - Add cache data structures
   - Implement cache methods
   - Keep existing behavior as fallback

2. **Phase 2: Integrate caching** (optimization)
   - Update completion to use cache
   - Add invalidation on write ops
   - Monitor cache hit rate

3. **Phase 3: Add throttling** (refinement)
   - Implement throttle logic
   - Test on various connection speeds

4. **Phase 4: Debug command** (feature)
   - Add debug command
   - Update help text

**Rollback:** Each phase is additive and can be disabled by removing cache lookups

## Open Questions

1. **Should cache TTL be user-configurable?**
   - Start with constant, make configurable if users request it

2. **Should we show cache status in prompt?**
   - No, keep prompt clean. Show in debug mode only.

3. **Should throttling be configurable?**
   - Start with constant, evaluate based on user feedback
