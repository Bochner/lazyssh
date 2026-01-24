# Build System Spec Delta

## MODIFIED Requirements

### Requirement: Makefile Compatibility Layer

The project SHALL maintain Makefile targets that delegate to Hatch commands for backward compatibility.

#### Scenario: Make test
- **WHEN** developer runs `make test`
- **THEN** tests are executed via `hatch run test`

#### Scenario: Make lint
- **WHEN** developer runs `make lint`
- **THEN** linting is executed via `hatch run lint`

#### Scenario: Make check
- **WHEN** developer runs `make check`
- **THEN** all quality checks are executed via `hatch run check`

#### Scenario: Make build
- **WHEN** developer runs `make build`
- **THEN** package is built via `hatch build`
- **AND** package is verified with `hatch run verify-pkg`

#### Scenario: Make clean
- **WHEN** developer runs `make clean`
- **THEN** all build artifacts are removed
- **AND** Hatch environments are removed

#### Scenario: Make version
- **WHEN** developer runs `make version`
- **THEN** current version is displayed via `hatch version`

## REMOVED Requirements

### ~~Requirement: Make Release Target~~

_Removed: The `make release` target is redundant since `hatch version` provides the same functionality natively. Developers should use `hatch version X.Y.Z` directly to update versions._

---

## Rationale

The `make release` target was a convenience wrapper that:
1. Displayed the current version
2. Prompted for a new version
3. Called `hatch version` with the input
4. Echoed next steps

All of this is better served by:
- `hatch version` (show current)
- `hatch version X.Y.Z` (update)
- Documented release process in `docs/maintainers.md`

Removing the target simplifies the Makefile and eliminates a layer of indirection.
