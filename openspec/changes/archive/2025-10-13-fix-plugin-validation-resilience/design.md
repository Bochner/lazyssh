## Design Considerations

### Validation Resilience
The plugin validation currently fails if it cannot open the file to check for a shebang. For Python plugins executed via `sys.executable`, the shebang is not strictly required, so failures to read the file should not invalidate Python plugins.

### Backwards Compatibility
Shell plugins retain strict validation (executable bit and shebang required). Python plugins become more permissive while maintaining the same execution behavior.

### Error Handling
Change shebang read failures from validation errors to warnings for Python plugins, ensuring they remain valid and executable via interpreter.