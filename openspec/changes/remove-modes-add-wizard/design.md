## Context

LazySSH currently operates in two distinct modes: "prompt mode" (menu-driven interface) and "command mode" (interactive shell). Over time, prompt mode has become obsolete and rarely used, while the mode-switching concept adds unnecessary complexity. Users would benefit from a unified interface with guided workflows for complex operations.

## Goals / Non-Goals

**Goals:**
- Eliminate the dual-mode system complexity
- Provide guided workflows for complex operations (SSH connections, tunnels)
- Maintain all existing functionality without mode switching
- Simplify the user experience with a single, consistent interface

**Non-Goals:**
- Changing the core SSH functionality
- Modifying the look and feel of existing commands
- Adding new SSH features or capabilities
- Changing the underlying architecture beyond mode removal

## Decisions

**Decision: Replace modes with wizard command**
- **Rationale**: Wizard provides guided workflows without the complexity of mode switching
- **Alternatives considered**: 
  - Keep both modes (rejected - prompt mode is obsolete)
  - Remove prompt mode only (rejected - still leaves mode concept)
  - Add wizard alongside modes (rejected - doesn't simplify the interface)

**Decision: Wizard supports lazyssh and tunnel workflows**
- **Rationale**: These are the most complex operations that benefit from guidance
- **Alternatives considered**:
  - Wizard for all commands (rejected - too complex)
  - Wizard for SCP only (rejected - SCP already has good UX)

## Risks / Trade-offs

**Risk: Users accustomed to prompt mode may be confused**
- **Mitigation**: Clear migration documentation and wizard provides similar guided experience

**Risk: Wizard implementation complexity**
- **Mitigation**: Start with simple workflows, expand based on user feedback

## Migration Plan

1. Remove mode system entirely
2. Default to command mode interface
3. Add wizard command with guided workflows
4. Update documentation and help text
5. Provide clear migration path for existing users

## Open Questions

- Should wizard support additional workflows beyond lazyssh and tunnel?
- How detailed should wizard guidance be (step-by-step vs. high-level)?
