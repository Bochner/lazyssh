## Why

The LazySSH application currently uses the Rich library inconsistently across different modules, with varying patterns for console output, styling, and UI components. While Rich is already integrated and provides excellent terminal UI capabilities, the codebase lacks standardized patterns for:

- Consistent console instance usage
- Standardized color schemes and styling
- Unified progress bar implementations
- Consistent table formatting and layouts
- Standardized panel and banner designs
- Proper error/success/info message formatting

This inconsistency leads to:
- Inconsistent visual appearance across different modes
- Duplicated styling code
- Missed opportunities to leverage Rich's advanced features
- Maintenance overhead when updating UI elements
- Suboptimal user experience due to visual inconsistencies

## What Changes

- **Standardize Rich Console Usage**: Establish a centralized console instance and consistent usage patterns across all modules
- **Create UI Style Standards**: Define consistent color schemes, typography, and visual patterns using Rich's styling capabilities
- **Implement Rich Progress Bars**: Replace basic progress indicators with Rich's advanced progress bar system for file transfers and operations
- **Standardize Table Layouts**: Create consistent table formatting patterns for status displays, connection lists, and data presentation
- **Enhance Panel and Banner Design**: Improve visual consistency of panels, banners, and informational displays
- **Implement Rich Status Indicators**: Add animated spinners and status indicators for better user feedback
- **Create Rich Layout System**: Implement consistent layout patterns using Rich's layout capabilities
- **Standardize Error/Success Messages**: Create consistent formatting patterns for all user feedback messages

## Impact

- Affected specs: user-interface, scp-mode, terminal-integration
- Affected code: 
  - `src/lazyssh/ui.py` - Core UI utilities and styling
  - `src/lazyssh/scp_mode.py` - SCP mode interface and progress bars
  - `src/lazyssh/command_mode.py` - Command mode interface and prompts
  - `src/lazyssh/logging_module.py` - Logging and console output
  - `src/lazyssh/ssh.py` - SSH status displays and feedback
  - `src/lazyssh/__main__.py` - Main application interface
- **BREAKING**: No breaking changes - this is purely internal standardization that maintains existing functionality
- Enhanced user experience through consistent, professional visual design
- Improved maintainability through centralized styling and UI patterns
- Better utilization of Rich library's advanced features
