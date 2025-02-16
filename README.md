# LazySSH

A comprehensive SSH toolkit for managing connections, tunnels, and remote sessions with a modern CLI interface.

## Features

- Interactive CLI with color-coded interface
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

```bash
# Clone the repository
git clone https://github.com/yourusername/lazyssh.git
cd lazyssh

# Install the package
pip install -e .
```

## Usage

After installation, run the tool using:

```bash
lazyssh
```

### Main Menu Options

1. Create new SSH connection
2. Manage tunnels
3. Create tunnel
4. Open terminal session
5. Close connection
q. Quit

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
git clone https://github.com/yourusername/lazyssh.git
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

### Connection Status
- Active connections and their tunnels are always visible in the main menu
- Real-time updates when creating/removing connections or tunnels
- Detailed error messages and suggestions for troubleshooting

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.