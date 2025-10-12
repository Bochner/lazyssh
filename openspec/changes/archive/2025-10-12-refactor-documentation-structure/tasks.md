# Documentation Refactor Tasks

## 1. Audit and Analysis
- [x] 1.1 Create content inventory of all documentation files
- [x] 1.2 Identify all outdated command references and environment variable names
- [x] 1.3 Map features from recent CHANGELOG entries to documentation gaps
- [x] 1.4 List all redundant content across multiple files

## 2. Update README.md
- [x] 2.1 Simplify feature list to 5-7 core capabilities
- [x] 2.2 Update Quick Start section with modern command examples
- [x] 2.3 Update Terminal Methods section with correct defaults and options
- [x] 2.4 Verify all command examples use current syntax (`open` not `terminal`)
- [x] 2.5 Add version 1.3.4+ features (runtime terminal switching, native as default)
- [x] 2.6 Clarify platform support (Linux/macOS full, Windows requires WSL)

## 3. Restructure User Guide
- [x] 3.1 Reorganize into clear journey: Install → First Connection → Core Workflows → Advanced
- [x] 3.2 Remove duplicate command reference content (belongs in commands.md)
- [x] 3.3 Update Prerequisites section (Terminator optional, not required)
- [x] 3.4 Replace all `terminal <connection>` with `open <connection>`
- [x] 3.5 Update environment variable documentation (LAZYSSH_TERMINAL_METHOD)
- [x] 3.6 Add section on runtime terminal method switching
- [x] 3.7 Simplify Advanced Usage section (move detail to specialized guides)
- [x] 3.8 Reduce overall length by 30-40% while maintaining completeness

## 4. Update Command Reference
- [x] 4.1 Update `open` command documentation (formerly `terminal <connection>`)
- [x] 4.2 Update `terminal` command documentation (now only for method switching)
- [x] 4.3 Remove tutorial/workflow content (belongs in user guide)
- [x] 4.4 Verify all command syntax and examples are accurate
- [x] 4.5 Add missing commands or parameters introduced in recent versions
- [x] 4.6 Standardize parameter descriptions and example formats

## 5. Simplify SCP Mode Guide
- [x] 5.1 Focus on practical usage patterns, remove excessive detail
- [x] 5.2 Update with recent SCP optimizations from v1.3.4+
- [x] 5.3 Consolidate "Tips and Best Practices" into main sections
- [x] 5.4 Add visual examples of common workflows
- [x] 5.5 Verify all commands work as documented

## 6. Simplify Tunneling Guide
- [x] 6.1 Reduce technical explanations, focus on use cases
- [x] 6.2 Add 2-3 more real-world scenarios
- [x] 6.3 Streamline troubleshooting section
- [x] 6.4 Verify proxy setup instructions are current

## 7. Update Troubleshooting Guide
- [x] 7.1 Remove obsolete Windows-specific issues (now requires WSL)
- [x] 7.2 Update Terminator section to reflect it being optional
- [x] 7.3 Add troubleshooting for native terminal mode
- [x] 7.4 Update platform-specific notes for current architecture
- [x] 7.5 Add common issues from recent releases
- [x] 7.6 Remove or update sections that no longer apply

## 8. Review Development Documentation
- [x] 8.1 Verify development.md is accurate and complete
- [x] 8.2 Ensure publishing.md reflects current release process
- [x] 8.3 Add note at top of development docs indicating they are for contributors

## 9. Quality Assurance
- [x] 9.1 Verify all command examples can be copy-pasted and work
- [x] 9.2 Check all internal doc links are valid
- [x] 9.3 Ensure consistent terminology across all docs
- [x] 9.4 Verify each doc has a clear table of contents
- [x] 9.5 Check for spelling and grammar issues
- [x] 9.6 Validate code blocks have proper syntax highlighting markers

## 10. Final Review
- [x] 10.1 Read through each doc from a new user perspective
- [x] 10.2 Confirm README can be understood in 5 minutes
- [x] 10.3 Confirm user guide provides clear 15-minute journey
- [x] 10.4 Verify command reference is concise and accurate
- [x] 10.5 Ensure no outdated references remain

