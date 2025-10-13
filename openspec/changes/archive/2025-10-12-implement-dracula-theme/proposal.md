## Why

The current LazySSH application uses a basic color theme that doesn't provide the visual consistency and professional appearance that users expect from modern CLI tools. Implementing the Dracula color theme will provide:

- **Visual Consistency**: A cohesive color palette that enhances readability and user experience
- **Professional Appearance**: Modern, well-designed color scheme that makes the application more appealing
- **Better Syntax Highlighting**: Colors that make different types of information (errors, success, info) more distinguishable
- **Accessibility**: Dracula theme provides good contrast ratios for better readability

## What Changes

- **BREAKING**: Replace the current `LAZYSSH_THEME` with a comprehensive Dracula-based theme
- Update all color mappings to use Dracula color palette (#282a36, #f8f8f2, #8be9fd, #50fa7b, #ffb86c, #ff79c6, #bd93f9, #ff5555, #f1fa8c, #6272a4)
- Ensure all UI components (tables, panels, progress bars, status messages) use consistent Dracula colors
- Maintain existing accessibility themes (high contrast, colorblind-friendly) but update them to use Dracula colors
- Update all hardcoded color references throughout the codebase to use theme-based styling

## Impact

- Affected specs: user-interface
- Affected code:
  - `src/lazyssh/ui.py` - Main theme definition and UI components
  - `src/lazyssh/ssh.py` - SSH command display and status messages
  - `src/lazyssh/scp_mode.py` - File transfer interface styling
  - `src/lazyssh/command_mode.py` - Command mode interface styling
  - `src/lazyssh/__main__.py` - Application startup messages
- All console output will have a consistent Dracula color scheme
- Improved visual hierarchy and information distinction
