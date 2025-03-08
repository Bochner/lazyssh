#!/bin/bash

echo "LazySSH Installer"
echo "----------------"

# Function to print colored output
print_status() {
    echo -e "\033[1;34m[*]\033[0m $1"
}

print_success() {
    echo -e "\033[1;32m[+]\033[0m $1"
}

print_error() {
    echo -e "\033[1;31m[!]\033[0m $1"
}

print_warning() {
    echo -e "\033[1;33m[!]\033[0m $1"
}

# Function to detect package manager (only apt, dnf, and yum)
detect_package_manager() {
    if command -v apt &> /dev/null; then
        PKG_MANAGER="apt"
        PKG_INSTALL="sudo apt install -y"
    elif command -v dnf &> /dev/null; then
        PKG_MANAGER="dnf"
        PKG_INSTALL="sudo dnf install -y"
    elif command -v yum &> /dev/null; then
        PKG_MANAGER="yum"
        PKG_INSTALL="sudo yum install -y"
    else
        PKG_MANAGER="unknown"
        PKG_INSTALL=""
    fi
}

# Function to update PATH for the current session
update_path() {
    if [[ -d "$HOME/.local/bin" && ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
        export PATH="$HOME/.local/bin:$PATH"
        print_status "Added $HOME/.local/bin to PATH for current session"
    fi
}

# Check if Python3 is installed
print_status "Checking for Python3..."
if ! command -v python3 &> /dev/null; then
    print_error "Python3 is not installed. Please install Python3 first."
    exit 1
else
    print_success "Python3 is installed."
fi

# Check if pip is installed
print_status "Checking for pip3..."
if ! command -v pip3 &> /dev/null; then
    print_warning "pip3 is not installed. Attempting to install..."
    detect_package_manager
    
    if [ "$PKG_MANAGER" != "unknown" ]; then
        $PKG_INSTALL python3-pip || {
            print_error "Failed to install pip3. Please install it manually."
            exit 1
        }
    else
        print_error "Unsupported package manager. This script only supports apt, dnf, and yum."
        exit 1
    fi
else
    print_success "pip3 is installed."
fi

# Install pipx if not present
print_status "Checking for pipx..."
if ! command -v pipx &> /dev/null; then
    print_status "Installing pipx..."
    
    # First try to install pipx using the system package manager
    detect_package_manager
    if [ "$PKG_MANAGER" != "unknown" ]; then
        case $PKG_MANAGER in
            apt)
                $PKG_INSTALL pipx
                ;;
            dnf)
                $PKG_INSTALL python3-pipx
                ;;
            yum)
                $PKG_INSTALL python3-pipx
                ;;
        esac
    fi
    
    # Check if pipx is now installed
    if ! command -v pipx &> /dev/null; then
        print_warning "Could not install pipx using package manager. Trying with pip..."
        
        # Try to install with pip as a fallback
        python3 -m pip install --user pipx || {
            print_error "Failed to install pipx. Please install it manually."
            print_error "For Debian/Ubuntu: sudo apt install pipx"
            print_error "For Fedora: sudo dnf install python3-pipx"
            print_error "For RHEL/CentOS: sudo yum install python3-pipx"
            exit 1
        }
        
        # Run ensurepath to add pipx to PATH in shell config files
        python3 -m pipx ensurepath || {
            print_warning "Failed to add pipx to PATH automatically."
        }
    fi
    
    # Update PATH for current session
    update_path
    
    # Check if pipx is now in PATH
    if ! command -v pipx &> /dev/null; then
        print_warning "pipx is installed but not in PATH."
        print_warning "Please run: source ~/.bashrc"
        print_warning "Then run this script again."
        exit 1
    fi
else
    print_success "pipx is installed."
fi

# Check for SSH client
print_status "Checking for SSH client..."
if ! command -v ssh &> /dev/null; then
    print_warning "SSH client not found. Attempting to install..."
    detect_package_manager
    
    if [ "$PKG_MANAGER" != "unknown" ]; then
        $PKG_INSTALL openssh-client || {
            print_error "Failed to install SSH client. Please install it manually."
            exit 1
        }
    else
        print_error "Unsupported package manager. This script only supports apt, dnf, and yum."
        exit 1
    fi
else
    print_success "SSH client is installed."
fi

# Check if terminator is installed
print_status "Checking for terminator..."
if ! command -v terminator &> /dev/null; then
    print_warning "Terminator is not installed. This is required for LazySSH."
    detect_package_manager
    
    if [ -n "$PKG_INSTALL" ]; then
        $PKG_INSTALL terminator || {
            print_error "Failed to install terminator. Please install it manually."
            exit 1
        }
    else
        print_error "Unsupported package manager. This script only supports apt, dnf, and yum."
        exit 1
    fi
else
    print_success "Terminator is installed."
fi

# Install LazySSH
print_status "Installing LazySSH..."
pipx install git+https://github.com/Bochner/lazyssh.git --force || {
    print_error "Failed to install LazySSH. Please check your internet connection and try again."
    exit 1
}

# Update PATH again to ensure lazyssh is available
update_path

print_success "Installation complete!"
print_warning "To make sure LazySSH is in your PATH permanently, add this line to your ~/.bashrc file:"
print_warning "  export PATH=\"$HOME/.local/bin:\$PATH\""
print_warning "Then run: source ~/.bashrc"
print_success "You can now run 'lazyssh' to start the program."