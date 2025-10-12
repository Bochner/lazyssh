## 1. Remove Mode System
- [x] 1.1 Remove `--prompt` command-line flag from main() function
- [x] 1.2 Remove mode switching logic from main() function
- [x] 1.3 Remove `prompt_mode_main()` function
- [x] 1.4 Remove `handle_menu_action()` function
- [x] 1.5 Remove `main_menu()` function
- [x] 1.6 Remove all prompt mode menu functions from ui.py
- [x] 1.7 Remove mode-related imports and dependencies

## 2. Update Command Mode
- [x] 2.1 Remove `cmd_mode()` method from CommandMode class
- [x] 2.2 Remove "mode" from commands dictionary
- [x] 2.3 Remove mode-related help text and UI messages
- [x] 2.4 Update help command to remove mode references
- [x] 2.5 Remove mode switching return values and logic

## 3. Implement Wizard Command
- [x] 3.1 Add `cmd_wizard()` method to CommandMode class
- [x] 3.2 Add "wizard" to commands dictionary
- [x] 3.3 Implement wizard argument parsing (lazyssh, tunnel)
- [x] 3.4 Create wizard workflow for SSH connection creation
- [x] 3.5 Create wizard workflow for tunnel creation
- [x] 3.6 Add wizard command to help text and completions

## 4. Update Documentation and Help
- [x] 4.1 Update main help text to remove mode references
- [x] 4.2 Add wizard command documentation
- [x] 4.3 Update command completion to include wizard
- [x] 4.4 Remove mode-related logging messages
- [x] 4.5 Update error messages to remove mode references

## 5. Testing and Validation
- [x] 5.1 Test wizard lazyssh workflow
- [x] 5.2 Test wizard tunnel workflow
- [x] 5.3 Verify all existing commands still work
- [x] 5.4 Test command completion includes wizard
- [x] 5.5 Verify no mode-related code remains
