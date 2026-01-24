## 1. Specification Updates

- [x] 1.1 Add test isolation requirements to build-system spec
- [x] 1.2 Add pytest-timeout requirement to build-system spec

## 2. Implementation (Already Completed)

- [x] 2.1 Add pytest-timeout to pyproject.toml dependencies
- [x] 2.2 Configure 30-second timeout in pytest.ini_options
- [x] 2.3 Fix test_scp_with_connection - add subprocess.run mock
- [x] 2.4 Fix test_wizard_lazyssh_existing_connection - add create_connection mock
- [x] 2.5 Fix test_plugin_run_executes - add execute_plugin mock

## 3. Documentation Updates

- [x] 3.1 Update CONTRIBUTING.md with test mocking guidelines
- [x] 3.2 Update openspec/project.md Testing Strategy section

## 4. Validation

- [x] 4.1 Run full test suite locally
- [x] 4.2 Run openspec validate
- [x] 4.3 Verify CI/CD pipeline passes (requires push to trigger)
