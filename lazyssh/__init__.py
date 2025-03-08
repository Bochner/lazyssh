"""
LazySSH - A comprehensive SSH toolkit for managing connections and tunnels
"""
import subprocess

def check_dependencies():
    """Check if required system dependencies are installed"""
    # Check for SSH and Terminator
    dependencies = {
        "ssh": "OpenSSH client (openssh-client package)",
        "terminator": "Terminator terminal emulator (terminator package)"
    }
    
    missing = []
    for cmd, desc in dependencies.items():
        try:
            if subprocess.run(["which", cmd], capture_output=True).returncode != 0:
                missing.append(f"{desc}")
        except subprocess.SubprocessError:
            missing.append(f"{desc}")
            
    return missing

__version__ = "1.0.0"