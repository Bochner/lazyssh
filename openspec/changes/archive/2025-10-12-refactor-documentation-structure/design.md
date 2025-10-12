# Documentation Refactor Design

## Context

LazySSH documentation has grown organically through multiple releases (1.0.0 → 1.3.4), accumulating:
- Outdated references (Terminator as required, old command syntax)
- Verbose explanations mixing tutorial and reference content
- Feature gaps (v1.3.3+ terminal improvements not documented)
- Structural overlap (user-guide.md duplicates commands.md)

This refactor establishes clear documentation structure and quality standards while updating all content to match current behavior.

## Goals / Non-Goals

**Goals:**
- Update all outdated command references (`terminal` → `open` for connections)
- Correct environment variable names and prerequisite statements
- Document all features from v1.3.0-1.3.4 releases
- Establish clear documentation layers (overview → journey → reference → specialized)
- Reduce user-facing doc verbosity by 30-40% while maintaining completeness
- Eliminate redundant content across multiple files

**Non-Goals:**
- Adding new features or changing application behavior
- Modifying developer documentation structure (development.md remains comprehensive)
- Changing documentation format (staying with Markdown)
- Creating new documentation types (e.g., video tutorials, interactive guides)

## Decisions

### Decision: Four-Layer Documentation Structure
Organize documentation into distinct layers with clear purposes:
1. **README.md** - 5-minute overview for all audiences
2. **docs/user-guide.md** - 15-minute guided journey for new users
3. **docs/commands.md** - Reference lookup for experienced users
4. **docs/[specialized].md** - Deep dives into specific features (SCP, tunneling, troubleshooting)

**Rationale:** Users at different stages need different information density. Mixing quick-start with comprehensive reference creates poor experience for both audiences.

**Alternatives considered:**
- Single comprehensive doc: Too long, poor scannability
- Wiki-style with many small pages: Harder to maintain, requires navigation system
- Keep current structure: Perpetuates existing problems

### Decision: Remove Tutorial Content from Command Reference
Move all workflow examples and explanations from commands.md to user-guide.md, keeping only syntax, parameters, and minimal examples in the reference.

**Rationale:** Command reference should be for lookup, not learning. Users following tutorials should not have to skip through syntax tables.

**Alternatives considered:**
- Combine tutorial and reference: Creates lengthy, hard-to-scan document
- Separate page per command: Overhead for maintenance, harder to search

### Decision: Mark Terminator as Optional Throughout
Update all documentation to present native terminal as default, Terminator as optional enhancement.

**Rationale:** Current behavior (as of v1.3.2+) uses native terminal by default with auto-fallback. Documentation should match reality.

**Alternatives considered:**
- Keep Terminator as "recommended": Misleading, implies required for full functionality
- Remove Terminator mentions entirely: Loses information about available enhancement

### Decision: Create user-documentation Capability Spec
Establish formal requirements for documentation quality, structure, accuracy, and completeness.

**Rationale:** Documentation is a user-facing deliverable that impacts product quality. Tracking it through OpenSpec ensures quality standards are maintained.

**Alternatives considered:**
- No spec tracking: Documentation quality becomes informal, harder to maintain standards
- Add to existing specs: Documentation concerns cross-cut multiple capabilities

## Risks / Trade-offs

**Risk:** Aggressive verbosity reduction may remove useful detail
- **Mitigation:** Review each section for essential vs nice-to-have information; move detail to specialized guides rather than deleting

**Risk:** Documentation updates may introduce new errors
- **Mitigation:** Validate all command examples by running them; cross-reference with source code and CHANGELOG

**Risk:** Restructuring may break user bookmarks or external links
- **Mitigation:** Keep file names and major section headings consistent; add redirects/notices if significant structure changes

**Trade-off:** Time investment vs incremental updates
- Comprehensive refactor ensures consistency but requires more upfront work than incremental fixes
- Justification: Current state has systemic issues that incremental fixes won't resolve

## Migration Plan

1. **Audit phase** (no user impact)
   - Inventory all outdated references
   - Map CHANGELOG features to documentation gaps
   - Identify redundant content

2. **Update phase** (minimal risk)
   - Update one doc at a time
   - Validate command examples after each update
   - Cross-check for consistency

3. **Quality assurance** (final verification)
   - End-to-end review of documentation flow
   - External review by non-author if possible
   - Validate all links and command examples

4. **Release**
   - Deploy with minor or patch version bump
   - Note documentation improvements in CHANGELOG
   - No rollback needed (docs-only change)

## Open Questions

None - this is a straightforward documentation update with no technical ambiguities.

