#!/bin/bash

# LazySSH Wrapper Script
# This wrapper allows you to run LazySSH even if PATH is not configured properly

# Display a banner
echo "╭─────────────────────────────────────────── LazySSH Wrapper ───────────────────────────────────────────╮"
echo "│ This is a convenience wrapper that starts LazySSH without requiring it to be in your PATH              │"
echo "╰──────────────────────────────────────────────────────────────────────────────────────────────────────╯"

# Determine the actual lazyssh installation location
if command -v lazyssh &> /dev/null; then
    # If lazyssh is in PATH, use it directly
    echo "Using LazySSH from PATH"
    LAZYSSH_CMD="lazyssh"
elif [ -f "$HOME/.local/bin/lazyssh" ]; then
    # Try the standard user installation location
    echo "Using LazySSH from $HOME/.local/bin/"
    LAZYSSH_CMD="$HOME/.local/bin/lazyssh"
else
    # Check if we're running from the git repository and try to find the entry point
    SCRIPT_DIR=$(dirname "$(readlink -f "$0")")
    if [ -d "$SCRIPT_DIR/lazyssh" ] && [ -f "$SCRIPT_DIR/lazyssh/__main__.py" ]; then
        echo "Running from LazySSH git repository"
        LAZYSSH_CMD="python3 -m lazyssh"
        # Make sure we're in the right directory
        cd "$SCRIPT_DIR"
    else
        echo "Error: Cannot find LazySSH installation. Please install LazySSH using the install.sh script."
        exit 1
    fi
fi

# Start lazyssh with no arguments
echo "Starting LazySSH..."
echo "-------------------"
echo ""

# Simply start LazySSH
$LAZYSSH_CMD
