# LazySSH

A comprehensive SSH toolkit for managing connections, tunnels, and remote sessions with a modern CLI interface.

## Features

- Dual interface modes:
  - Interactive menu mode
  - Command mode with tab completion
- Smart command completion for all operations
- Multiple SSH connection management
- Forward and reverse tunnel creation
- Dynamic port forwarding
- Control socket management
- Terminal session management in Terminator
- Automatic connection cleanup on exit
- Real-time status display of connections and tunnels

## Requirements

- Python 3.7+
- OpenSSH client
- Terminator terminal emulator
- Linux/Unix operating system

### Installing Dependencies

On Fedora/RHEL:
```bash
sudo dnf install terminator
```

On Ubuntu/Debian:
```bash
sudo apt install terminator
```

On Arch Linux:
```bash
sudo pacman -S terminator
```

## Installation

There are several ways to install LazySSH depending on your system:

### Method 1: Quick Install Script (Recommended)
```bash
# Clone the repository
git clone https://github.com/Bochner/lazyssh.git
cd lazyssh

# Run the installer script
./install.sh
```
The install script will automatically:
- Install pipx if not present
- Install terminator if not present
- Install LazySSH using pipx
- Set up all required paths

### Method 2: Manual Installation Using pipx
```bash
# Install pipx if not already installed
python3 -m pip install --user pipx
python3 -m pipx ensurepath

# Install LazySSH
pipx install git+https://github.com/Bochner/lazyssh.git
```

### Method 3: Using Virtual Environment (Recommended for Development)
```bash
# Clone the repository
git clone https://github.com/Bochner/lazyssh.git
cd lazyssh

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Unix/Linux
# or
.\venv\Scripts\activate  # On Windows

# Install the package
pip install -e .
```

### Method 4: System Python (Not recommended on some distributions)
Some Linux distributions (like Kali Linux) use externally-managed environments and prevent direct pip installations. Use Method 1 or 2 instead.

If you still want to install system-wide (not recommended):
```bash
pip install -e . --break-system-packages  # Use with caution
```

## Usage

After installation, run the tool using:

```bash
lazyssh
```

The tool supports two interaction modes:
1. Menu Mode (Default) - Interactive menu-driven interface
2. Command Mode - Command-line interface with smart completion

### Menu Mode

1. Create new SSH connection
2. Manage tunnels
3. Create tunnel
4. Open terminal session
5. Close connection
q. Quit

### Command Mode

Command mode provides a powerful command-line interface with smart tab completion. Available commands:

```
lazyssh -ip <ip> -port <port> -socket <name> -user <username>  # Create new SSH connection
close <ssh_id>                                                 # Close an SSH connection
tunc <ssh_id> <l|r> <local_port> <remote_host> <remote_port>  # Create tunnel
tund <tunnel_id>                                              # Destroy tunnel
term <ssh_id>                                                 # Open terminal
list                                                          # Show all connections
mode                                                          # Switch between modes
help                                                          # Show help
exit                                                          # Exit program
```

#### Command Mode Features
- Tab completion for all commands
- Context-aware argument suggestions
- Real-time parameter completion
- Command history support
- Detailed help system (use 'help <command>' for specific command help)

Example usage:
```bash
# Create SSH connection
lazyssh -ip 192.168.1.100 -port 22 -socket dev-server -user admin

# Create forward tunnel
tunc dev-server l 8080 localhost 80

# Create reverse tunnel
tunc dev-server r 3000 127.0.0.1 3000

# Open terminal
term dev-server

# Close connection
close dev-server
```

### SSH Connection Features

- Custom port support
- Identity file support
- Dynamic port forwarding
- Persistent connections with auto-cleanup
- Control socket management
- Seamless Terminator integration

### Tunnel Management

- Forward tunnel creation (local to remote)
- Reverse tunnel creation (remote to local)
- Multiple tunnels per connection
- Real-time tunnel status monitoring
- Easy tunnel creation and cleanup

## Dependencies

- click: Command line interface
- rich: Terminal formatting and colors
- pexpect: Terminal interaction
- colorama: Cross-platform colored terminal text
- python-dotenv: Environment variable management
- terminator: Terminal emulation (system package)

## Development

```bash
# Clone the repository
git clone https://github.com/Bochner/lazyssh.git
cd lazyssh

# Create a virtual environment
python -m venv venv
source venv/bin/activate

# Install development dependencies
pip install -r requirements.txt

# Install terminator
# On Fedora/RHEL:
sudo dnf install terminator
# On Ubuntu/Debian:
sudo apt install terminator
# On Arch Linux:
sudo pacman -S terminator
```

## Troubleshooting

### Terminal Issues
If you encounter any issues:
1. Ensure Terminator is installed and available in your PATH
2. Try running `terminator` directly to check for any configuration issues
3. Check the terminal output for specific error messages

### Command Mode Issues
1. Command Completion
   - Press Tab or Space to see available commands and arguments
   - For `lazyssh` command, arguments will be suggested as you type
   - If completions don't appear, press Space or Tab again
   - Command history can be accessed with Up/Down arrows

2. Connection Management
   - Use `list` command to see all active connections and their IDs
   - Connection names (socket) must be unique
   - Use `help <command>` for detailed usage of any command

3. Common Command Mode Errors
   - "Unknown command": Make sure to use the exact command name (case-sensitive)
   - "Missing required parameters": All parameters marked with '-' are required
   - "Connection not found": Use `list` to verify the connection name

### Connection Status
- Active connections and their tunnels are always visible in the main menu
- Real-time updates when creating/removing connections or tunnels
- Detailed error messages and suggestions for troubleshooting

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.