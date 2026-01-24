## Context

The project has 913 tests but only ~10% coverage. The `hatch test` command is not configured (uses hatch's test matrix feature). We need to integrate pytest-html for test reports and configure coverage HTML output alongside CLI output.

## Goals / Non-Goals

**Goals:**
- Achieve 100% test coverage across all modules
- Configure `hatch test` to produce CLI coverage output and HTML reports
- Output artifacts to `artifacts/coverage/` and `artifacts/unit/`

**Non-Goals:**
- Changing the test framework (pytest stays)
- Adding integration or E2E tests (unit tests only)
- Setting up CI/CD (existing GitHub Actions workflow is out of scope)

## Decisions

### Decision: Use hatch test environment matrix

Hatch's test feature uses a special `[tool.hatch.envs.hatch-test]` configuration rather than custom scripts. This is the idiomatic way to configure `hatch test`.

**Configuration approach:**
```toml
[tool.hatch.envs.hatch-test]
extra-dependencies = [
    "pytest-html",
]

[[tool.hatch.envs.hatch-test.matrix]]
python = ["3.11", "3.12", "3.13"]

[tool.hatch.envs.hatch-test.scripts]
run = "pytest{env:HATCH_TEST_ARGS:} {args}"
run-cov = "pytest --cov=src/lazyssh --cov-report=term-missing --cov-report=html:artifacts/coverage --html=artifacts/unit/report.html --self-contained-html{env:HATCH_TEST_ARGS:} {args}"
cov-combine = ""
```

### Decision: Artifact directory structure

```
artifacts/
├── coverage/          # coverage.py HTML output
│   └── index.html
└── unit/              # pytest-html output
    └── report.html
```

### Decision: Coverage enforcement

Use `--cov-fail-under=100` only after all tests are written. During development, allow lower coverage to enable incremental progress.

## Risks / Trade-offs

- **Risk**: Some code paths may be genuinely untestable (external SSH connections)
  - **Mitigation**: Use mocking extensively; mark truly untestable lines with `# pragma: no cover`

- **Trade-off**: 100% coverage vs. test maintenance burden
  - **Decision**: Accept higher maintenance cost for reliability guarantees

## Open Questions

- Should we add `artifacts/` to `.gitignore` or commit the reports?
  - **Recommendation**: Add to `.gitignore` - reports are build artifacts, not source
