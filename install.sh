#!/bin/bash

echo "LazySSH Installer"
echo "----------------"

# Check if Python3 is installed
if ! command -v python3 &> /dev/null; then
    echo "Python3 is not installed. Please install Python3 first."
    exit 1
fi

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo "pip3 is not installed. Please install pip3 first."
    exit 1
fi

# Install pypy3-venv on Kali Linux if needed
if [ -f "/etc/os-release" ] && grep -q "Kali" "/etc/os-release"; then
    if ! dpkg -l | grep -q "pypy3-venv"; then
        echo "Installing pypy3-venv (required for Kali Linux)..."
        sudo apt install -y pypy3-venv
    fi
fi

# Install pipx if not present
if ! command -v pipx &> /dev/null; then
    echo "Installing pipx..."
    python3 -m pip install --user pipx
    python3 -m pipx ensurepath
    
    # Source the updated PATH to use pipx immediately
    source ~/.bashrc 2>/dev/null || source ~/.bash_profile 2>/dev/null || true
fi

# Ensure pipx is in PATH
if ! command -v pipx &> /dev/null; then
    echo "Please restart your terminal or run: source ~/.bashrc"
    echo "Then run this script again."
    exit 1
fi

# Check if terminator is installed
if ! command -v terminator &> /dev/null; then
    echo "Installing terminator..."
    if command -v apt &> /dev/null; then
        sudo apt install -y terminator
    elif command -v dnf &> /dev/null; then
        sudo dnf install -y terminator
    elif command -v pacman &> /dev/null; then
        sudo pacman -S --noconfirm terminator
    else
        echo "Could not install terminator automatically. Please install it manually."
        exit 1
    fi
fi

# Install LazySSH
echo "Installing LazySSH..."
pipx install git+https://github.com/Bochner/lazyssh.git

echo "Installation complete! You can now run 'lazyssh' to start the program."