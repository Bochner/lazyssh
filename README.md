# LazySSH

A comprehensive SSH toolkit for managing connections, tunnels, and remote sessions with a modern CLI interface.

![LazySSH](https://raw.githubusercontent.com/Bochner/lazyssh/main/lazyssh.png)

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

## Installation

LazySSH can be installed using standard Python packaging tools:

### Option 1: Install with pip (Recommended)

```bash
# Install globally
pip install lazyssh

# Or install for the current user only
pip install --user lazyssh
```

### Option 2: Install from repository

```bash
# Clone the repository
git clone https://github.com/Bochner/lazyssh.git
cd lazyssh

# Install
pip install .

# Or for development mode
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
  - Basic usage: `lazyssh -ip <ip> -port <port> -user <username> -socket <n>`
  - With dynamic proxy: `lazyssh -ip <ip> -port <port> -user <username> -socket <n> -proxy [port]`
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
lazyssh -ip 192.168.1.100 -port 22 -user admin -socket myserver -proxy

# Create connection with dynamic proxy on custom port
lazyssh -ip 192.168.1.100 -port 22 -user admin -socket myserver -proxy 8080
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

If you installed with `pip install --user` and get "command not found":

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

# Install Terminator (Fedora)
sudo dnf install terminator

# Install Terminator (RHEL/CentOS)
sudo yum install terminator
```

## Development

### Project Structure

```
lazyssh/
├── src/             # Source code
│   └── lazyssh/     # Main package
├── tests/           # Test suite
├── docs/            # Documentation
├── pyproject.toml   # Project configuration
├── setup.py         # Package installation
├── Makefile         # Development tasks
├── pre-commit-check.sh  # Script to run all CI checks locally
└── .pre-commit-config.yaml  # Code quality hooks
```

### Setup Development Environment

```bash
# Clone the repository
git clone https://github.com/Bochner/lazyssh.git
cd lazyssh

# Install dev dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pip install pre-commit
pre-commit install
```

### Running CI Checks Locally

Before committing your code, you can run all the CI checks locally using the provided script:

```bash
# Make the script executable (first time only)
chmod +x pre-commit-check.sh

# Run all checks in a virtual environment
./pre-commit-check.sh
```

This script:
- Creates a temporary virtual environment (`.pre-commit-venv`)
- Installs all development dependencies
- Runs the following checks:
  - Black formatting
  - isort import sorting
  - flake8 linting
  - mypy type checking
  - pytest (if test files exist)
- Cleans up the repository by removing:
  - The temporary virtual environment
  - Python cache files
  - Build artifacts
  - Test artifacts

The script is designed to be robust and will clean up after itself even if errors occur. It requires Python 3 to be installed on your system.

This ensures your code passes all CI checks and your repository is clean before committing.

### Common Development Tasks

We provide a Makefile for common tasks:

```bash
# Install in development mode
make install

# Run tests
make test

# Format code (black and isort)
make fmt

# Lint code
make lint

# Build package
make build

# Create distribution
make dist
```

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
