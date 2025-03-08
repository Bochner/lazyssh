# LazySSH

A comprehensive SSH toolkit for managing connections, tunnels, and remote sessions with a modern CLI interface.

![LazySSH](./lazyssh.png)

## Features

- Dual interface modes:
  - Interactive menu mode
  - Command mode with smart tab completion
- Multiple SSH connection management
- Forward and reverse tunnel creation
- Dynamic port forwarding with SOCKS proxy support
- Control socket management
- Terminal session management with Terminator
- Automatic connection cleanup on exit
- Real-time status display of connections and tunnels
- Full visibility of SSH commands being executed

## Requirements

- Python 3.7+
- OpenSSH client
- Terminator terminal emulator
- Linux/Unix operating system

## Installation

### Method 1: Quick Install Script (Recommended)

```bash
# Download the installer
curl -O https://raw.githubusercontent.com/Bochner/lazyssh/main/install.sh

# Make it executable
chmod +x install.sh

# Run the installer
./install.sh
```

The installer will:
- Check for and install required dependencies
- Install LazySSH using pipx for isolated dependencies
- Add LazySSH to your PATH for the current session
- Provide instructions for permanent PATH configuration

### Method 2: Manual Installation with pipx

```bash
# Install pipx if not already installed
python3 -m pip install --user pipx
python3 -m pipx ensurepath

# Install LazySSH
pipx install git+https://github.com/Bochner/lazyssh.git

# Make sure ~/.local/bin is in your PATH
export PATH="$HOME/.local/bin:$PATH"
```

### Method 3: Development Installation

```bash
# Clone the repository
git clone https://github.com/Bochner/lazyssh.git
cd lazyssh

# Install in development mode
pip install -e .
```

## Usage

LazySSH has two interface modes:

### Command Mode (Default)

```bash
# Start LazySSH in command mode
lazyssh
```

In command mode, you can use the following commands:
- `lazyssh` - Create a new SSH connection
  - Basic usage: `lazyssh -ip <ip> -port <port> -socket <n> -user <username>`
  - With dynamic proxy: `lazyssh -ip <ip> -port <port> -socket <n> -user <username> -proxy [port]`
- `tunc` - Create a new tunnel (forward or reverse)
  - Example (forward): `tunc ubuntu l 8080 localhost 80`
  - Example (reverse): `tunc ubuntu r 3000 127.0.0.1 3000`
- `tund` - Delete a tunnel by ID
  - Example: `tund 1`
- `list` - List connections and tunnels
- `term` - Open a terminal for a connection
  - Example: `term ubuntu`
- `close` - Close a connection
- `mode` - Switch to prompt mode
- `help` - Show help
- `exit` - Exit LazySSH

#### Dynamic SOCKS Proxy

To create a dynamic SOCKS proxy when establishing an SSH connection:

```bash
# Create connection with dynamic proxy on default port (1080)
lazyssh -ip 192.168.1.100 -port 22 -socket myserver -user admin -proxy

# Create connection with dynamic proxy on custom port
lazyssh -ip 192.168.1.100 -port 22 -socket myserver -user admin -proxy 8080
```

You can then configure your applications to use the SOCKS proxy at `localhost:1080` (or your custom port).

### Prompt Mode

```bash
# Start LazySSH in prompt mode
lazyssh --prompt
```

In prompt mode, you'll see a menu with numbered options:
1. Create new SSH connection (with optional SOCKS proxy)
2. Destroy tunnel
3. Create tunnel
4. Open terminal
5. Close connection
6. Switch to command mode
7. Exit

## Troubleshooting

### Command Not Found

If you get "command not found" after installation:

```bash
# Add to your PATH manually
export PATH="$HOME/.local/bin:$PATH"

# To make it permanent, add this line to your ~/.bashrc file
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

### Missing Dependencies

If you're missing any dependencies:

```bash
# Install Terminator (Ubuntu/Debian)
sudo apt install terminator

# Install Terminator (Fedora/RHEL)
sudo dnf install terminator

# Install Terminator (Arch Linux)
sudo pacman -S terminator
```

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
