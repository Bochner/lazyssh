"""Configuration management for LazySSH"""
import os
from pathlib import Path
import json

CONFIG_DIR = os.path.expanduser("~/.config/lazyssh")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")

def ensure_config_dir():
    """Ensure configuration directory exists"""
    os.makedirs(CONFIG_DIR, exist_ok=True)

def load_config():
    """Load configuration from file"""
    ensure_config_dir()
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}
    return {}

def save_config(config):
    """Save configuration to file"""
    ensure_config_dir()
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)