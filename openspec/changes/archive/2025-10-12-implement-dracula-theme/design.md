## Context

LazySSH currently uses a basic color theme defined in `ui.py` with standard terminal colors. The application has multiple UI components (tables, panels, progress bars, status messages) that need consistent styling. The Dracula theme provides a modern, professional color palette that enhances readability and visual appeal.

## Goals / Non-Goals

**Goals:**
- Implement comprehensive Dracula color theme across entire codebase
- Maintain visual consistency across all UI components
- Preserve accessibility features (high contrast, colorblind-friendly themes)
- Ensure all syntax highlighting and status indicators use appropriate Dracula colors
- Keep existing functionality while improving visual appearance

**Non-Goals:**
- Changing UI layout or component structure
- Adding new UI components
- Modifying functionality beyond visual styling
- Breaking existing accessibility features

## Decisions

**Decision: Use Dracula color palette with semantic mapping**
- Map Dracula colors to semantic theme keys (info, success, error, warning, etc.)
- Use #8be9fd (cyan) for info messages and function names
- Use #50fa7b (green) for success messages and strings
- Use #ff5555 (red) for errors and danger messages
- Use #f1fa8c (yellow) for warnings and variables
- Use #ff79c6 (pink) for keywords and special commands
- Use #bd93f9 (purple) for operators and special symbols
- Use #ffb86c (orange) for numbers and constants
- Use #6272a4 (comment) for muted text and secondary info
- Use #f8f8f2 (foreground) for default text
- Use #282a36 (background) for main background (though Rich handles this)

**Decision: Maintain accessibility themes with Dracula colors**
- Update high contrast theme to use Dracula colors with enhanced contrast
- Update colorblind-friendly theme to use Dracula colors with better differentiation
- Ensure all accessibility themes maintain WCAG compliance

**Decision: Centralized theme management**
- Keep centralized theme definition in `ui.py`
- Update all modules to use theme-based styling instead of hardcoded colors
- Ensure consistent console instance usage across all modules

## Risks / Trade-offs

**Risk: Color contrast issues** → Mitigation: Test all color combinations and maintain accessibility standards
**Risk: Breaking existing functionality** → Mitigation: Comprehensive testing and gradual rollout
**Risk: Performance impact** → Mitigation: Rich themes are lightweight, minimal performance impact expected

## Migration Plan

1. **Phase 1**: Update core theme definition in `ui.py`
2. **Phase 2**: Update all UI components to use new theme
3. **Phase 3**: Update all modules to use theme-based styling
4. **Phase 4**: Test and validate across all functionality
5. **Phase 5**: Update accessibility themes

## Open Questions

- Should we provide theme switching capability for users?
- Are there any specific color combinations that need special attention?
- Should we maintain backward compatibility with old theme keys?
