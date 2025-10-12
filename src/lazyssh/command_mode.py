"""Command mode interface for LazySSH using prompt_toolkit"""

import os
import shlex
import sys
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from prompt_toolkit import PromptSession
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.document import Document
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.history import FileHistory
from prompt_toolkit.styles import Style

from . import logging_module
from .config import (
    backup_config,
    config_exists,
    delete_config,
    get_config,
    load_configs,
    save_config,
    validate_config_name,
)
from .logging_module import (  # noqa: F401
    APP_LOGGER,
    CMD_LOGGER,
    log_ssh_command,
    set_debug_mode,
)
from .models import SSHConnection
from .scp_mode import SCPMode
from .ssh import SSHManager
from .ui import (
    console,
    display_error,
    display_info,
    display_saved_configs,
    display_ssh_status,
    display_success,
    display_tunnels,
    display_warning,
)


class LazySSHCompleter(Completer):
    """Completer for prompt_toolkit with LazySSH commands"""

    def __init__(self, command_mode: "CommandMode") -> None:
        self.command_mode = command_mode

    def get_completions(self, document: Document, complete_event: Any) -> Iterable[Completion]:
        text = document.text
        word_before_cursor = document.get_word_before_cursor()

        # Split the input into words
        try:
            words = shlex.split(text[: document.cursor_position])
        except ValueError:
            words = text[: document.cursor_position].split()

        if not words or (len(words) == 1 and not text.endswith(" ")):
            # Show base commands if at start
            for cmd in self.command_mode.commands.keys():
                if not word_before_cursor or cmd.startswith(word_before_cursor):
                    yield Completion(cmd, start_position=-len(word_before_cursor))
            return

        command = words[0].lower()

        if command == "lazyssh":
            # Get used arguments and their positions
            used_args: dict[str, int] = {}
            expecting_value = False
            last_arg: str | None = None

            for i, word in enumerate(words[1:], 1):  # Start from 1 to skip the command
                if expecting_value and last_arg is not None:
                    # This word is a value for the previous argument
                    used_args[last_arg] = i
                    expecting_value = False
                    last_arg = None
                elif word.startswith("-"):
                    # This is an argument
                    if word in ["-proxy", "-no-term"]:
                        # -proxy and -no-term don't need a value
                        used_args[word] = i
                    else:
                        # Other arguments expect a value
                        expecting_value = True
                        last_arg = word
                else:
                    i += 1

            # Available arguments for lazyssh
            all_args = {
                "-ip",
                "-port",
                "-user",
                "-socket",
                "-proxy",
                "-ssh-key",
                "-shell",
                "-no-term",
            }
            remaining_args = all_args - set(used_args.keys())

            # Separate required and optional parameters
            required_args = ["-ip", "-port", "-user", "-socket"]
            optional_args = ["-proxy", "-ssh-key", "-shell", "-no-term"]

            # Check which required args are still needed
            required_remaining = [arg for arg in required_args if arg in remaining_args]
            optional_remaining = [arg for arg in optional_args if arg in remaining_args]

            # If we're expecting a value for an argument, don't suggest new arguments
            if expecting_value:
                return

            # If the last word is a partial argument, complete it
            if words[-1].startswith("-") and not text.endswith(" "):
                # Complete partial argument based on what the user has typed so far
                partial_arg = words[-1]

                # First prioritize required arguments
                for arg in required_remaining:
                    if arg.startswith(partial_arg):
                        yield Completion(arg, start_position=-len(partial_arg))

                # Then suggest optional arguments if all required ones are used
                if not required_remaining:
                    for arg in optional_remaining:
                        if arg.startswith(partial_arg):
                            yield Completion(arg, start_position=-len(partial_arg))

            # Otherwise suggest next argument if we're not in the middle of entering a value
            elif text.endswith(" ") and not expecting_value:
                # If we still have required arguments, suggest them first
                if required_remaining:
                    # Suggest the first remaining required argument
                    yield Completion(required_remaining[0], start_position=-len(word_before_cursor))
                # If all required arguments are provided, suggest all remaining optional arguments
                elif optional_remaining:
                    # Suggest all remaining optional arguments
                    for arg in optional_remaining:
                        yield Completion(arg, start_position=-len(word_before_cursor))

        elif command == "tunc":
            # For tunc command, we expect a specific sequence of arguments:
            # 1. SSH connection name
            # 2. Tunnel type (l/r)
            # 3. Local port
            # 4. Remote host
            # 5. Remote port

            # Determine which argument we're currently expecting
            arg_position = (
                len(words) - 1
            )  # -1 because we're 0-indexed and first word is the command

            # If we're at the end of a word, we're expecting the next argument
            if text.endswith(" "):
                arg_position += 1

            if arg_position == 1:  # First argument: SSH connection name
                # Show available connections
                for conn_name in self.command_mode._get_connection_completions():
                    if not word_before_cursor or conn_name.startswith(word_before_cursor):
                        yield Completion(conn_name, start_position=-len(word_before_cursor))
            elif arg_position == 2:  # Second argument: Tunnel type (l/r)
                # Suggest tunnel type
                for type_option in ["l", "r"]:
                    if not word_before_cursor or type_option.startswith(word_before_cursor):
                        yield Completion(type_option, start_position=-len(word_before_cursor))
            # For other positions (local port, remote host, remote port), no completions provided

        elif command == "tund":
            # For tund command, we only expect one argument: the tunnel ID
            arg_position = len(words) - 1

            # If we're at the end of a word, we're expecting the next argument
            if text.endswith(" ") or (len(words) == 2 and arg_position == 1):
                # Show available tunnel IDs
                for socket_path, conn in self.command_mode.ssh_manager.connections.items():
                    for tunnel in conn.tunnels:
                        if not word_before_cursor or tunnel.id.startswith(word_before_cursor):
                            yield Completion(tunnel.id, start_position=-len(word_before_cursor))

        elif command == "terminal":
            # For terminal command, suggest only terminal methods
            arg_position = len(words) - 1

            # Only show completions if we're at the exact position to enter the argument
            if (len(words) == 1 and text.endswith(" ")) or (
                len(words) == 2 and not text.endswith(" ")
            ):
                # Show terminal method options only
                for method in ["auto", "native", "terminator"]:
                    if not word_before_cursor or method.startswith(word_before_cursor):
                        yield Completion(method, start_position=-len(word_before_cursor))

        elif command == "open":
            # For open command, suggest only SSH connection names
            arg_position = len(words) - 1

            # Only show completions if we're at the exact position to enter the argument
            if (len(words) == 1 and text.endswith(" ")) or (
                len(words) == 2 and not text.endswith(" ")
            ):
                # Show available connections
                for conn_name in self.command_mode._get_connection_completions():
                    if not word_before_cursor or conn_name.startswith(word_before_cursor):
                        yield Completion(conn_name, start_position=-len(word_before_cursor))

        elif command == "close":
            # For close command, we only expect one argument: the SSH connection name
            arg_position = len(words) - 1

            # Only show completions if we're at the exact position to enter the connection name
            if (len(words) == 1 and text.endswith(" ")) or (
                len(words) == 2 and not text.endswith(" ")
            ):
                # Show available connections
                for conn_name in self.command_mode._get_connection_completions():
                    if not word_before_cursor or conn_name.startswith(word_before_cursor):
                        yield Completion(conn_name, start_position=-len(word_before_cursor))

        elif command == "help":
            # For help command, we only expect one optional argument: the command to get help for
            arg_position = len(words) - 1

            # If we're at the end of a word, we're expecting the next argument
            # Or if we've just typed the command and a space, show completions
            if text.endswith(" ") or (len(words) == 2 and arg_position == 1):
                # Show available commands for help
                for cmd in self.command_mode.commands.keys():
                    if not word_before_cursor or cmd.startswith(word_before_cursor):
                        yield Completion(cmd, start_position=-len(word_before_cursor))

        # Handle completion for close command
        elif command == "close" and len(words) == 2:
            connections = self.command_mode._get_connection_completions()
            for conn_name in connections:
                if conn_name.startswith(word_before_cursor):
                    yield Completion(conn_name, start_position=-len(word_before_cursor))

        # Handle completion for scp command
        elif command == "scp":
            # Only suggest connection names if we either:
            # 1. Just typed "scp " and need the first connection name
            # 2. Are in the middle of typing the first connection name
            # Don't suggest anything if we already have a complete connection name
            if (len(words) == 1 and text.endswith(" ")) or (
                len(words) == 2 and not text.endswith(" ")
            ):
                connections = self.command_mode._get_connection_completions()
                for conn_name in connections:
                    if not word_before_cursor or conn_name.startswith(word_before_cursor):
                        yield Completion(conn_name, start_position=-len(word_before_cursor))

        # Handle completion for connect command (saved configs)
        elif command == "connect":
            if (len(words) == 1 and text.endswith(" ")) or (
                len(words) == 2 and not text.endswith(" ")
            ):
                config_names = self.command_mode._get_config_name_completions()
                for config_name in config_names:
                    if not word_before_cursor or config_name.startswith(word_before_cursor):
                        yield Completion(config_name, start_position=-len(word_before_cursor))

        # Handle completion for save-config command (suggest established connection names)
        elif command == "save-config":
            if (len(words) == 1 and text.endswith(" ")) or (
                len(words) == 2 and not text.endswith(" ")
            ):
                connection_names = self.command_mode._get_connection_name_completions()
                for connection_name in connection_names:
                    if not word_before_cursor or connection_name.startswith(word_before_cursor):
                        yield Completion(connection_name, start_position=-len(word_before_cursor))

        # Handle completion for delete-config command (suggest saved config names)
        elif command == "delete-config":
            if (len(words) == 1 and text.endswith(" ")) or (
                len(words) == 2 and not text.endswith(" ")
            ):
                config_names = self.command_mode._get_config_name_completions()
                for config_name in config_names:
                    if not word_before_cursor or config_name.startswith(word_before_cursor):
                        yield Completion(config_name, start_position=-len(word_before_cursor))

        # Handle completion for wizard command (suggest workflow names)
        elif command == "wizard":
            if (len(words) == 1 and text.endswith(" ")) or (
                len(words) == 2 and not text.endswith(" ")
            ):
                workflows = ["lazyssh", "tunnel"]
                for workflow in workflows:
                    if not word_before_cursor or workflow.startswith(word_before_cursor):
                        yield Completion(workflow, start_position=-len(word_before_cursor))


class CommandMode:
    def __init__(self, ssh_manager: SSHManager) -> None:
        """Initialize Command Mode interface"""
        # Initialize the SSH Manager
        self.ssh_manager = ssh_manager

        # Define available commands
        self.commands = {
            "config": self.cmd_config,  # Display saved configurations
            "configs": self.cmd_config,  # Alias for config
            "connect": self.cmd_connect,  # Connect using saved config
            "save-config": self.cmd_save_config,  # Save connection configuration
            "delete-config": self.cmd_delete_config,  # Delete saved configuration
            "backup-config": self.cmd_backup_config,  # Backup connections configuration file
            "list": self.cmd_list,
            "lazyssh": self.cmd_lazyssh,
            "help": self.cmd_help,
            "terminal": self.cmd_terminal,
            "open": self.cmd_open,
            "debug": self.cmd_debug,
            "scp": self.cmd_scp,
            "exit": self.cmd_exit,
            "quit": self.cmd_exit,
            "tunc": self.cmd_tunc,
            "tund": self.cmd_tund,
            "close": self.cmd_close,
            "clear": self.cmd_clear,
            "wizard": self.cmd_wizard,
        }

        # Initialize history
        self.history_dir = Path.home() / ".lazyssh"
        if not self.history_dir.exists():
            self.history_dir.mkdir(parents=True, exist_ok=True)
        self.history_file = self.history_dir / "command_history"

        # Log initialization
        if CMD_LOGGER:
            CMD_LOGGER.debug("CommandMode initialized")

    def _get_connection_completions(self) -> list[str]:
        """Get list of connection names for completion"""
        conn_completions = []
        for socket_path in self.ssh_manager.connections:
            conn_name = Path(socket_path).name
            conn_completions.append(conn_name)
        return conn_completions

    def _get_config_name_completions(self) -> list[str]:
        """Get list of saved configuration names for completion"""
        configs = load_configs()
        return list(configs.keys())

    def _get_connection_name_completions(self) -> list[str]:
        """Get list of established connection socket names for completion"""
        connection_names = []
        for socket_path in self.ssh_manager.connections.keys():
            # Extract the socket name from the full path
            connection_name = Path(socket_path).name
            connection_names.append(connection_name)
        return connection_names

    def get_prompt_text(self) -> HTML:
        """Get the prompt text with HTML formatting"""
        return HTML("<prompt>lazyssh></prompt> ")

    def show_status(self) -> None:
        """Display loaded configurations, current connections and tunnels"""
        # Display loaded configurations (if any exist)
        configs = load_configs()
        if configs:
            display_saved_configs(configs)

        # Display active SSH connections
        if self.ssh_manager.connections:
            display_ssh_status(
                self.ssh_manager.connections, self.ssh_manager.get_current_terminal_method()
            )
            # Display tunnels for each connection
            for socket_path, conn in self.ssh_manager.connections.items():
                if conn.tunnels:
                    display_tunnels(socket_path, conn)

    def run(self) -> str | None:
        """Run the command mode interface"""
        # Create the session
        try:
            session: PromptSession = PromptSession(
                history=FileHistory(str(self.history_file)),
                completer=LazySSHCompleter(self),
                style=Style.from_dict(
                    {
                        "prompt": "ansicyan bold",
                    }
                ),
            )

            if CMD_LOGGER:
                CMD_LOGGER.info("Starting command mode interface")

            # Display the banner and help
            # self.show_available_commands()  # Remove this line to prevent auto-showing commands

            # Display initial status (configs, connections, tunnels)
            self.show_status()

            # Main loop
            while True:
                try:
                    # Get user input
                    text = session.prompt(lambda: self.get_prompt_text())

                    # Skip if empty
                    if not text.strip():
                        continue

                    # Parse the command and arguments
                    try:
                        parts = shlex.split(text)
                    except ValueError as e:
                        display_error(f"Invalid command syntax: {e}")
                        if CMD_LOGGER:
                            CMD_LOGGER.error(f"Invalid command syntax: {e}")
                        continue

                    # Get the command and arguments
                    cmd = parts[0].lower() if parts else ""
                    args = parts[1:] if len(parts) > 1 else []

                    # Check if the command exists
                    if cmd not in self.commands:
                        display_error(f"Unknown command: {cmd}")
                        display_info("Type 'help' to see available commands")
                        if CMD_LOGGER:
                            CMD_LOGGER.warning(f"Unknown command attempted: {cmd}")
                        continue

                    # Log the command
                    if CMD_LOGGER:
                        CMD_LOGGER.info(f"Executing command: {cmd} {' '.join(args)}")

                    # Execute the command
                    result = self.commands[cmd](args)

                    # Handle the result
                    if result:
                        # Success
                        if not cmd == "list":  # Don't show status after list command
                            self.show_status()
                    # else handled by the command method

                except (KeyboardInterrupt, EOFError):
                    # Handle Ctrl+C and Ctrl+D
                    if CMD_LOGGER:
                        CMD_LOGGER.info("User interrupted command mode (Ctrl+C or Ctrl+D)")
                    break

        except Exception as e:
            display_error(f"Error in command mode: {str(e)}")
            if CMD_LOGGER:
                CMD_LOGGER.exception(f"Unhandled error in command mode: {str(e)}")
            return None

        return None

    def show_available_commands(self) -> None:
        """Show available commands when user enters an unknown command"""
        display_info("Available commands:")
        for cmd in sorted(self.commands.keys()):
            display_info(f"  {cmd}")

        display_info("  exit    : Exit lazyssh")
        display_info("  quit    : Alias for exit")
        display_info("  scp     : Enter SCP mode for file transfers")

    # Command implementations
    def cmd_lazyssh(self, args: list[str]) -> bool:
        """Handle lazyssh command for creating new connections"""
        try:
            # Parse arguments into dictionary
            params = {}
            i = 0
            while i < len(args):
                if args[i].startswith("-"):
                    param_name = args[i][1:]  # Remove the dash

                    # Handle flag parameters that don't need a value
                    if param_name == "proxy" or param_name == "no-term":
                        if i + 1 < len(args) and not args[i + 1].startswith("-"):
                            # If there's a value after the flag, use it
                            params[param_name] = args[i + 1]
                            i += 2
                        else:
                            # Otherwise, just set it to True to indicate it's present
                            params[param_name] = "true"  # Use string "true" instead of boolean
                            i += 1
                    elif i + 1 < len(args):
                        params[param_name] = args[i + 1]
                        i += 2
                    else:
                        raise ValueError(f"Missing value for argument {args[i]}")
                else:
                    i += 1

            # Check required parameters
            required = ["ip", "port", "user", "socket"]
            missing = [f"-{param}" for param in required if param not in params]
            if missing:
                display_error(f"Missing required parameters: {', '.join(missing)}")
                display_info(
                    "Usage: lazyssh -ip <ip> -port <port> -user <username> -socket <n> "
                    "[-proxy [port]] [-ssh-key <identity_file>] [-shell <shell>] [-no-term]"
                )
                if CMD_LOGGER:
                    CMD_LOGGER.error(f"Missing required parameters: {', '.join(missing)}")
                return False

            # Validate socket name before use
            if not validate_config_name(params["socket"]):
                display_error(
                    "Invalid socket name. Use alphanumeric characters, dashes, and underscores only"
                )
                return False

            # Check if the socket name already exists
            socket_path = f"/tmp/{params['socket']}"
            if socket_path in self.ssh_manager.connections:
                display_warning(f"Socket name '{params['socket']}' is already in use.")
                # Use Rich's Confirm.ask for a color-coded prompt (same as prompt mode)
                from rich.prompt import Confirm, Prompt

                if not Confirm.ask("Do you want to use a different name?", default=True):
                    display_info("Proceeding with the existing socket name.")
                else:
                    new_socket = Prompt.ask("Enter a new socket name")
                    if not new_socket or not validate_config_name(new_socket):
                        display_error(
                            "Invalid socket name. Use alphanumeric characters, dashes, and underscores only"
                        )
                        return False
                    params["socket"] = new_socket
                    socket_path = f"/tmp/{params['socket']}"

            # Create the connection object
            conn = SSHConnection(
                host=params["ip"],
                port=int(params["port"]),
                username=params["user"],
                socket_path=socket_path,
            )

            # Set identity file if provided
            if "ssh-key" in params:
                conn.identity_file = params["ssh-key"]

            # Set shell if provided
            if "shell" in params:
                conn.shell = params["shell"]

            # Set no-term flag if provided
            if "no-term" in params:
                conn.no_term = True

            # Handle dynamic proxy port if specified
            if "proxy" in params:
                if params["proxy"] == "true":
                    # If -proxy was specified without a value, use a default port
                    conn.dynamic_port = 9050
                    display_info(f"Using default dynamic proxy port: {conn.dynamic_port}")
                else:
                    # Otherwise use the specified port
                    try:
                        conn.dynamic_port = int(params["proxy"])
                    except ValueError:
                        display_error("Proxy port must be a number")
                        if CMD_LOGGER:
                            CMD_LOGGER.error(f"Invalid proxy port: {params['proxy']}")
                        return False

            # Log connection attempt
            if CMD_LOGGER:
                CMD_LOGGER.info(
                    f"Creating SSH connection: {conn.username}@{conn.host}:{conn.port} "
                    f"(socket: {params['socket']})"
                )

            # Create the connection
            if self.ssh_manager.create_connection(conn):
                display_success(f"Connection '{params['socket']}' established")
                if conn.dynamic_port:
                    display_success(f"Dynamic proxy created on port {conn.dynamic_port}")
                return True
            return False
        except ValueError as e:
            display_error(str(e))
            if CMD_LOGGER:
                CMD_LOGGER.error(f"Error in lazyssh command: {str(e)}")
            return False

    def cmd_tunc(self, args: list[str]) -> bool:
        """Handle tunnel command for creating tunnels"""
        if len(args) != 5:
            display_error("Usage: tunc <ssh_id> <l|r> <local_port> <remote_host> <remote_port>")
            display_info("Example: tunc ubuntu l 8080 localhost 80")
            return False

        ssh_id, tunnel_type, local_port, remote_host, remote_port = args
        socket_path = f"/tmp/{ssh_id}"

        try:
            local_port_int = int(local_port)
            remote_port_int = int(remote_port)
            is_reverse = tunnel_type.lower() == "r"

            # Build the command for display
            if is_reverse:
                tunnel_args = f"-O forward -R {local_port}:{remote_host}:{remote_port}"
                tunnel_type_str = "reverse"
            else:
                tunnel_args = f"-O forward -L {local_port}:{remote_host}:{remote_port}"
                tunnel_type_str = "forward"

            cmd = f"ssh -S {socket_path} {tunnel_args} dummy"

            # Display the command that will be executed
            display_info("The following SSH command will be executed:")
            display_info(cmd)

            if self.ssh_manager.create_tunnel(
                socket_path, local_port_int, remote_host, remote_port_int, is_reverse
            ):
                display_success(
                    f"{tunnel_type_str.capitalize()} tunnel created: "
                    f"{local_port} -> {remote_host}:{remote_port}"
                )
                return True
            return False
        except ValueError:
            display_error("Port numbers must be integers")
            return False

    def cmd_tund(self, args: list[str]) -> bool:
        """Handle tunnel delete command for removing tunnels"""
        if len(args) != 1:
            display_error("Usage: tund <tunnel_id>")
            display_info("Example: tund 1")
            return False

        tunnel_id = args[0]

        # Find the connection that has this tunnel
        for socket_path, conn in self.ssh_manager.connections.items():
            for tunnel in conn.tunnels:
                if tunnel.id == tunnel_id:
                    # Build the command for display
                    if tunnel.type == "reverse":
                        tunnel_args = (
                            f"-O cancel -R {tunnel.local_port}:"
                            f"{tunnel.remote_host}:{tunnel.remote_port}"
                        )
                    else:
                        tunnel_args = (
                            f"-O cancel -L {tunnel.local_port}:"
                            f"{tunnel.remote_host}:{tunnel.remote_port}"
                        )

                    cmd = f"ssh -S {socket_path} {tunnel_args} dummy"

                    # Display the command that will be executed
                    display_info("The following SSH command will be executed:")
                    display_info(cmd)

                    if self.ssh_manager.close_tunnel(socket_path, tunnel_id):
                        display_success(f"Tunnel {tunnel_id} closed")
                        return True
                    return False

        display_error(f"Tunnel with ID {tunnel_id} not found")
        return False

    def cmd_list(self, args: list[str]) -> bool:
        """Handle list command for showing connections"""
        if not self.ssh_manager.connections:
            display_info("No active connections")
            return True

        # Connections are already shown by show_status() before each prompt
        return True

    def cmd_config(self, args: list[str]) -> bool:
        """Handle config command for displaying saved configurations"""
        configs = load_configs()
        display_saved_configs(configs)
        return True

    def cmd_connect(self, args: list[str]) -> bool:
        """Handle connect command for connecting using a saved configuration"""
        if not args:
            display_error("Usage: connect <config-name>")
            configs = load_configs()
            if configs:
                display_info("Available configurations:")
                for name in configs.keys():
                    display_info(f"  {name}")
            else:
                display_info("No saved configurations available")
            return False

        config_name = args[0]
        config_data = get_config(config_name)

        if not config_data:
            display_error(f"Configuration '{config_name}' not found")
            configs = load_configs()
            if configs:
                display_info("Available configurations:")
                for name in configs.keys():
                    display_info(f"  {name}")
            return False

        # Validate required fields
        required_fields = ["host", "port", "username", "socket_name"]
        missing_fields = [field for field in required_fields if field not in config_data]
        if missing_fields:
            display_error(
                f"Invalid configuration '{config_name}': missing required field(s): "
                f"{', '.join(missing_fields)}"
            )
            return False

        # Validate and expand SSH key if provided
        expanded_ssh_key = None
        if "ssh_key" in config_data and config_data["ssh_key"]:
            ssh_key_path = Path(config_data["ssh_key"]).expanduser()
            if not ssh_key_path.exists():
                display_warning(f"SSH key file not found: {config_data['ssh_key']}")
                display_info("Continuing with configuration (key might exist at connection time)")
            expanded_ssh_key = str(ssh_key_path)

        # Create connection object from config
        try:
            # Normalize and validate socket_name before using it
            socket_name = os.path.basename(config_data.get("socket_name", ""))
            if not socket_name or not validate_config_name(socket_name):
                display_error(
                    "Invalid socket name. Use alphanumeric characters, dashes, and underscores only"
                )
                return False

            # Update config_data with normalized socket_name
            config_data["socket_name"] = socket_name
            socket_path = f"/tmp/{socket_name}"

            # Check if socket name is already in use
            if socket_path in self.ssh_manager.connections:
                display_warning(f"Socket name '{config_data['socket_name']}' is already in use.")
                from rich.prompt import Confirm, Prompt

                if not Confirm.ask("Do you want to use a different name?", default=True):
                    display_info("Connection aborted")
                    return False
                new_socket = Prompt.ask("Enter a new socket name")
                if not new_socket or not validate_config_name(new_socket):
                    display_error(
                        "Invalid socket name. Use alphanumeric characters, dashes, and underscores only"
                    )
                    return False
                config_data["socket_name"] = new_socket
                socket_path = f"/tmp/{new_socket}"

            conn = SSHConnection(
                host=config_data["host"],
                port=int(config_data["port"]),
                username=config_data["username"],
                socket_path=socket_path,
                dynamic_port=config_data.get("proxy_port"),
                identity_file=expanded_ssh_key or config_data.get("ssh_key"),
                shell=config_data.get("shell"),
                no_term=config_data.get("no_term", False),
            )

            if CMD_LOGGER:
                CMD_LOGGER.info(
                    f"Connecting using saved config '{config_name}': "
                    f"{conn.username}@{conn.host}:{conn.port}"
                )

            # Create the connection
            if self.ssh_manager.create_connection(conn):
                display_success(f"Connection '{config_data['socket_name']}' established")
                if conn.dynamic_port:
                    display_success(f"Dynamic proxy created on port {conn.dynamic_port}")
                return True
            return False

        except (ValueError, KeyError) as e:
            display_error(f"Error creating connection from config: {str(e)}")
            if CMD_LOGGER:
                CMD_LOGGER.error(f"Error in connect command: {str(e)}")
            return False

    def cmd_save_config(self, args: list[str]) -> bool:
        """Handle save-config command for saving a connection configuration"""
        if not args:
            display_error("Usage: save-config <config-name>")
            return False

        config_name = args[0]

        # Validate config name
        if not validate_config_name(config_name):
            display_error(
                "Invalid configuration name. Use alphanumeric characters, dashes, and underscores only"
            )
            return False

        # Check if we have any active connections to save from
        if not self.ssh_manager.connections:
            display_error("No active connections to save")
            display_info("First create a connection using the 'lazyssh' command")
            return False

        # If there's only one connection, use it
        if len(self.ssh_manager.connections) == 1:
            socket_path = list(self.ssh_manager.connections.keys())[0]
            conn = self.ssh_manager.connections[socket_path]
        else:
            # Multiple connections - ask user to select
            display_info("Multiple connections available. Select one:")
            conn_list = list(self.ssh_manager.connections.items())
            for i, (sock_path, c) in enumerate(conn_list, 1):
                conn_name = Path(sock_path).name
                console.print(
                    f"  [info]{i}.[/info] [bold green]{conn_name}[/bold green] [dim]([/dim][bold cyan]{c.username}[/bold cyan][bold]@[/bold][bold magenta]{c.host}[/bold magenta][dim]:[/dim][yellow]{c.port}[/yellow][dim])[/dim]"
                )

            try:
                from rich.prompt import IntPrompt

                choice = IntPrompt.ask("Enter connection number", default=1) - 1
                if 0 <= choice < len(conn_list):
                    socket_path, conn = conn_list[choice]
                else:
                    display_error("Invalid connection number")
                    return False
            except (ValueError, KeyboardInterrupt):
                display_error("Invalid input")
                return False

        # Check if config already exists
        if config_exists(config_name):
            from rich.prompt import Confirm

            if not Confirm.ask(f"Configuration '{config_name}' already exists. Overwrite?"):
                display_info("Save cancelled")
                return False

        # Build config parameters dictionary
        config_params = {
            "host": conn.host,
            "port": conn.port,
            "username": conn.username,
            "socket_name": Path(conn.socket_path).name,
        }

        # Add optional parameters if present
        if conn.identity_file:
            config_params["ssh_key"] = conn.identity_file
        if conn.shell:
            config_params["shell"] = conn.shell
        if conn.no_term:
            config_params["no_term"] = conn.no_term
        if conn.dynamic_port:
            config_params["proxy_port"] = conn.dynamic_port

        # Save the configuration
        if save_config(config_name, config_params):
            display_success(f"Configuration '{config_name}' saved")
            if CMD_LOGGER:
                CMD_LOGGER.info(f"Configuration '{config_name}' saved successfully")
            return True
        else:
            display_error(f"Failed to save configuration '{config_name}'")
            return False

    def cmd_delete_config(self, args: list[str]) -> bool:
        """Handle delete-config command for deleting a saved configuration"""
        if not args:
            display_error("Usage: delete-config <config-name>")
            configs = load_configs()
            if configs:
                display_info("Available configurations:")
                for name in configs.keys():
                    display_info(f"  {name}")
            return False

        config_name = args[0]

        if not config_exists(config_name):
            display_error(f"Configuration '{config_name}' not found")
            return False

        # Confirm deletion
        from rich.prompt import Confirm

        if not Confirm.ask(f"Delete configuration '{config_name}'?"):
            display_info("Deletion cancelled")
            return False

        if delete_config(config_name):
            display_success(f"Configuration '{config_name}' deleted")
            if CMD_LOGGER:
                CMD_LOGGER.info(f"Configuration '{config_name}' deleted successfully")
            return True
        else:
            display_error(f"Failed to delete configuration '{config_name}'")
            return False

    def cmd_backup_config(self, args: list[str]) -> bool:
        """Handle backup-config command for backing up the connections configuration file"""
        success, message = backup_config()

        if success:
            display_success(message)
            if CMD_LOGGER:
                CMD_LOGGER.info("Configuration backup created successfully")
            return True
        else:
            display_error(message)
            if CMD_LOGGER:
                CMD_LOGGER.warning(f"Configuration backup failed: {message}")
            return False

    def cmd_help(self, args: list[str]) -> bool:
        """Handle help command"""
        if not args:
            display_info("[bold cyan]\nLazySSH Command Mode - Available Commands:[/bold cyan]\n")
            display_info("[magenta bold]SSH Connection:[/magenta bold]")
            display_info(
                "  [cyan]lazyssh[/cyan] -ip [yellow]<ip>[/yellow] -port [yellow]<port>[/yellow] -user [yellow]<username>[/yellow] -socket [yellow]<n>[/yellow] "
                "[-proxy [yellow]<port>[/yellow]] [-ssh-key [yellow]<path>[/yellow]] [-shell [yellow]<shell>[/yellow]] [-no-term]"
            )
            display_info("  [cyan]close[/cyan] [yellow]<ssh_id>[/yellow]")
            display_info(
                "  [dim]Example:[/dim] [green]lazyssh -ip 192.168.10.50 -port 22 -user ubuntu -socket ubuntu[/green]"
            )
            display_info(
                "  [dim]Example:[/dim] [green]lazyssh -ip 192.168.10.50 -port 22 -user ubuntu -socket ubuntu -proxy 8080 -shell /bin/sh[/green]"
            )
            display_info("  [dim]Example:[/dim] [green]close ubuntu[/green]\n")

            display_info("[magenta bold]Tunnel Management:[/magenta bold]")
            display_info(
                "  [cyan]tunc[/cyan] [yellow]<ssh_id>[/yellow] [yellow]<l|r>[/yellow] [yellow]<local_port>[/yellow] [yellow]<remote_host>[/yellow] [yellow]<remote_port>[/yellow]"
            )
            display_info(
                "  [dim]Example (forward):[/dim] [green]tunc ubuntu l 8080 localhost 80[/green]"
            )
            display_info(
                "  [dim]Example (reverse):[/dim] [green]tunc ubuntu r 3000 127.0.0.1 3000[/green]\n"
            )

            display_info("  [cyan]tund[/cyan] [yellow]<tunnel_id>[/yellow]")
            display_info("  [dim]Example:[/dim] [green]tund 1[/green]\n")

            display_info("[magenta bold]Terminal:[/magenta bold]")
            display_info(
                "  [cyan]open[/cyan] [yellow]<ssh_id>[/yellow]          - Open a terminal session"
            )
            display_info(
                "  [cyan]terminal[/cyan] [yellow]<method>[/yellow]      - Change terminal method (auto, native, terminator)"
            )
            display_info(
                "  [dim]Example:[/dim] [green]open ubuntu[/green]      [dim]# Open terminal for ubuntu connection[/dim]"
            )
            display_info(
                "  [dim]Example:[/dim] [green]terminal native[/green]  [dim]# Use native terminal method[/dim]\n"
            )

            display_info("[magenta bold]File Transfer:[/magenta bold]")
            display_info("  [cyan]scp[/cyan] [[yellow]<ssh_id>[/yellow]]")
            display_info("  [dim]Example:[/dim] [green]scp ubuntu[/green]\n")

            display_info("[magenta bold]Configuration Management:[/magenta bold]")
            display_info(
                "  [cyan]config[/cyan] / [cyan]configs[/cyan]              - Display saved configurations"
            )
            display_info(
                "  [cyan]connect[/cyan] [yellow]<config-name>[/yellow]          - Connect using saved configuration"
            )
            display_info(
                "  [cyan]save-config[/cyan] [yellow]<config-name>[/yellow]     - Save current connection as configuration"
            )
            display_info(
                "  [cyan]delete-config[/cyan] [yellow]<config-name>[/yellow]   - Delete saved configuration"
            )
            display_info(
                "  [cyan]backup-config[/cyan]                    - Backup the connections configuration file"
            )
            display_info("  [dim]Example:[/dim] [green]config[/green]")
            display_info("  [dim]Example:[/dim] [green]connect my-server[/green]")
            display_info("  [dim]Example:[/dim] [green]save-config my-server[/green]")
            display_info("  [dim]Example:[/dim] [green]backup-config[/green]\n")

            display_info("[magenta bold]System Commands:[/magenta bold]")
            display_info("  [cyan]list[/cyan]    - Show all connections and tunnels")
            display_info("  [cyan]wizard[/cyan]  - Guided workflows for complex operations")
            display_info("  [cyan]debug[/cyan]   - Toggle debug logging to console")
            display_info("  [cyan]help[/cyan]    - Show this help")
            display_info("  [cyan]exit[/cyan]    - Exit the program")
            return True

        cmd = args[0]
        if cmd == "lazyssh":
            display_info("[bold cyan]\nCreate new SSH connection:[/bold cyan]")
            display_info(
                "[yellow]Usage:[/yellow] [cyan]lazyssh[/cyan] -ip [yellow]<ip>[/yellow] -port [yellow]<port>[/yellow] -user [yellow]<username>[/yellow] -socket [yellow]<n>[/yellow] "
                "[-proxy [port]] [-ssh-key [yellow]<identity_file>[/yellow]] [-shell [yellow]<shell>[/yellow]] [-no-term]"
            )
            display_info("[magenta bold]Required parameters:[/magenta bold]")
            display_info("  [cyan]-ip[/cyan]     : IP address or hostname of the SSH server")
            display_info("  [cyan]-port[/cyan]   : SSH port number")
            display_info("  [cyan]-user[/cyan]   : SSH username")
            display_info("  [cyan]-socket[/cyan] : Name for the connection (used as identifier)")
            display_info("[magenta bold]Optional parameters:[/magenta bold]")
            display_info(
                "  [cyan]-proxy[/cyan]  : Create a dynamic SOCKS proxy (default port: 9050)"
            )
            display_info("  [cyan]-ssh-key[/cyan]: Path to an SSH identity file")
            display_info("  [cyan]-shell[/cyan]  : Specify the shell to use (e.g., /bin/sh)")
            display_info("  [cyan]-no-term[/cyan]: Do not automatically open a terminal")
            display_info("\n[magenta bold]Examples:[/magenta bold]")
            display_info(
                "  [green]lazyssh -ip 192.168.10.50 -port 22 -user ubuntu -socket ubuntu[/green]"
            )
            display_info(
                "  [green]lazyssh -ip 192.168.10.50 -port 22 -user ubuntu -socket ubuntu -proxy[/green]"
            )
            display_info(
                "  [green]lazyssh -ip 192.168.10.50 -port 22 -user ubuntu -socket ubuntu -proxy 8080[/green]"
            )
            display_info(
                "  [green]lazyssh -ip 192.168.10.50 -port 22 -user ubuntu -socket ubuntu -shell /bin/sh[/green]"
            )
            display_info(
                "  [green]lazyssh -ip 192.168.10.50 -port 22 -user ubuntu -socket ubuntu -shell /bin/sh -no-term[/green]"
            )
        elif cmd == "tunc":
            display_info("[bold cyan]\nCreate a new tunnel:[/bold cyan]")
            display_info(
                "[yellow]Usage:[/yellow] [cyan]tunc[/cyan] [yellow]<ssh_id>[/yellow] [yellow]<l|r>[/yellow] [yellow]<local_port>[/yellow] [yellow]<remote_host>[/yellow] [yellow]<remote_port>[/yellow]"
            )
            display_info("[magenta bold]Parameters:[/magenta bold]")
            display_info("  [cyan]ssh_id[/cyan]      : The identifier of the SSH connection")
            display_info(
                "  [cyan]l|r[/cyan]         : 'l' for local (forward) tunnel, 'r' for remote (reverse) tunnel"
            )
            display_info("  [cyan]local_port[/cyan]  : The local port to use for the tunnel")
            display_info("  [cyan]remote_host[/cyan] : The remote host to connect to")
            display_info("  [cyan]remote_port[/cyan] : The remote port to connect to")
            display_info("\n[magenta bold]Examples:[/magenta bold]")
            display_info(
                "  [green]tunc ubuntu l 8080 localhost 80[/green]    [dim]# Forward local port 8080 to "
                "localhost:80 on the remote server[/dim]"
            )
            display_info(
                "  [green]tunc ubuntu r 3000 127.0.0.1 3000[/green]  [dim]# Reverse tunnel from remote port 3000 "
                "to local 127.0.0.1:3000[/dim]"
            )
        elif cmd == "tund":
            display_info("[bold cyan]\nDelete a tunnel:[/bold cyan]")
            display_info("[yellow]Usage:[/yellow] [cyan]tund[/cyan] [yellow]<tunnel_id>[/yellow]")
            display_info("[magenta bold]Parameters:[/magenta bold]")
            display_info(
                "  [cyan]tunnel_id[/cyan] : The ID of the tunnel to delete (shown in the list command)"
            )
            display_info("\n[magenta bold]Example:[/magenta bold]")
            display_info("  [green]tund 1[/green]")
        elif cmd == "terminal":
            display_info("[bold cyan]\nChange terminal method:[/bold cyan]")
            display_info("[yellow]Usage:[/yellow] [cyan]terminal[/cyan] [yellow]<method>[/yellow]")
            display_info("[magenta bold]Parameters:[/magenta bold]")
            display_info(
                "  [cyan]method[/cyan] : Terminal method to set (auto, native, terminator)"
            )
            display_info("\n[magenta bold]Terminal methods:[/magenta bold]")
            display_info(
                "  [cyan]auto[/cyan]       : Try terminator first, fallback to native (default)"
            )
            display_info(
                "  [cyan]native[/cyan]     : Use native terminal (subprocess, allows returning to LazySSH)"
            )
            display_info("  [cyan]terminator[/cyan] : Use terminator terminal emulator only")
            display_info("\n[magenta bold]Examples:[/magenta bold]")
            display_info(
                "  [green]terminal native[/green]  [dim]# Set terminal method to native[/dim]"
            )
            display_info(
                "  [green]terminal auto[/green]    [dim]# Set terminal method to auto[/dim]"
            )
            display_info("\n[dim]Note: To open a terminal session, use the 'open' command[/dim]")
        elif cmd == "open":
            display_info("[bold cyan]\nOpen a terminal session:[/bold cyan]")
            display_info("[yellow]Usage:[/yellow] [cyan]open[/cyan] [yellow]<ssh_id>[/yellow]")
            display_info("[magenta bold]Parameters:[/magenta bold]")
            display_info(
                "  [cyan]ssh_id[/cyan] : The identifier of the SSH connection to open a terminal for"
            )
            display_info("\n[magenta bold]Examples:[/magenta bold]")
            display_info(
                "  [green]open ubuntu[/green]  [dim]# Open terminal for connection 'ubuntu'[/dim]"
            )
            display_info(
                "  [green]open web[/green]     [dim]# Open terminal for connection 'web'[/dim]"
            )
            display_info("\n[dim]Note: Use 'close <ssh_id>' to close the connection[/dim]")
        elif cmd == "clear":
            display_info("[bold cyan]\nClear the terminal screen:[/bold cyan]")
            display_info("[yellow]Usage:[/yellow] [cyan]clear[/cyan]")
        elif cmd == "scp":
            display_info("[bold cyan]\nEnter SCP mode for file transfers:[/bold cyan]")
            display_info(
                "[yellow]Usage:[/yellow] [cyan]scp[/cyan] [[yellow]<connection_name>[/yellow]]"
            )
            display_info("[magenta bold]Parameters:[/magenta bold]")
            display_info(
                "  [cyan]connection_name[/cyan] : The identifier of the SSH connection to use (optional)"
            )
            display_info("\nSCP mode leverages your existing SSH connection's master socket")
            display_info(
                "to perform secure file transfers without requiring additional authentication."
            )
            display_info("\n[magenta bold]SCP mode commands:[/magenta bold]")
            display_info(
                "  [cyan]put[/cyan] [yellow]<local_file>[/yellow] [[yellow]<remote_file>[/yellow]]  - Upload file to remote server"
            )
            display_info(
                "  [cyan]get[/cyan] [yellow]<remote_file>[/yellow] [[yellow]<local_file>[/yellow]]  - Download file from remote server"
            )
            display_info(
                "  [cyan]ls[/cyan] [[yellow]<remote_path>[/yellow]]                - List files in remote directory"
            )
            display_info(
                "  [cyan]cd[/cyan] [yellow]<remote_path>[/yellow]                  - Change remote working directory"
            )
            display_info(
                "  [cyan]pwd[/cyan]                               - Show current remote directory"
            )
            display_info(
                "  [cyan]mget[/cyan] [yellow]<pattern>[/yellow]                    - Download multiple files matching pattern"
            )
            display_info(
                "  [cyan]local[/cyan] [[yellow]<path>[/yellow]]                    - Set or show local download directory"
            )
            display_info("  [cyan]exit[/cyan]                              - Exit SCP mode")
            display_info("\n[magenta bold]Examples:[/magenta bold]")
            display_info(
                "  [green]scp ubuntu[/green]                        [dim]# Enter SCP mode with the 'ubuntu' connection[/dim]"
            )
            display_info(
                "  [green]scp[/green]                               [dim]# Enter SCP mode and select a connection interactively[/dim]"
            )
        elif cmd == "debug":
            display_info("[bold cyan]\nToggle debug logging to console:[/bold cyan]")
            display_info(
                "[yellow]Usage:[/yellow] [cyan]debug[/cyan] [[yellow]on|off|enable|disable|true|false|1|0[/yellow]]"
            )
            display_info("\n[magenta bold]Description:[/magenta bold]")
            display_info("  Toggles debug logging output to the console.")
            display_info("  Logs are always saved to /tmp/lazyssh/logs regardless of this setting.")
            display_info("  When enabled, all log messages will be displayed in the console.")
            display_info("\n[magenta bold]Examples:[/magenta bold]")
            display_info(
                "  [green]debug[/green]      [dim]# Toggle debug mode (on if off, off if on)[/dim]"
            )
            display_info("  [green]debug on[/green]   [dim]# Explicitly enable debug mode[/dim]")
            display_info("  [green]debug off[/green]  [dim]# Explicitly disable debug mode[/dim]")
        elif cmd == "wizard":
            display_info("[bold cyan]\nGuided workflows for complex operations:[/bold cyan]")
            display_info("[yellow]Usage:[/yellow] [cyan]wizard[/cyan] [yellow]<workflow>[/yellow]")
            display_info("[magenta bold]Available workflows:[/magenta bold]")
            display_info("  [cyan]lazyssh[/cyan] - Guided SSH connection creation")
            display_info("  [cyan]tunnel[/cyan]  - Guided tunnel creation")
            display_info("\n[magenta bold]Description:[/magenta bold]")
            display_info("  The wizard provides step-by-step guidance for complex operations")
            display_info("  that benefit from interactive configuration.")
            display_info("\n[magenta bold]Examples:[/magenta bold]")
            display_info(
                "  [green]wizard lazyssh[/green]  [dim]# Start guided SSH connection creation[/dim]"
            )
            display_info(
                "  [green]wizard tunnel[/green]   [dim]# Start guided tunnel creation[/dim]"
            )
        else:
            display_error(f"Unknown command: {cmd}")
            self.cmd_help([])
        return True

    def cmd_exit(self, args: list[str]) -> bool:
        """Exit lazyssh and close all connections"""
        display_info("Exiting lazyssh...")

        # Check if there are active connections and prompt for confirmation
        if self.ssh_manager.connections:
            # Use Rich's Confirm.ask for a color-coded prompt (same as prompt mode)
            from rich.prompt import Confirm

            if not Confirm.ask("You have active connections. Close them and exit?"):
                display_info("Exit cancelled")
                return True

            # User confirmed, proceed with closing connections
            display_info("Closing all connections...")
            successful_closures = 0
            total_connections = len(self.ssh_manager.connections)

            # Create a copy of the connections to avoid modification during iteration
            for socket_path in list(self.ssh_manager.connections.keys()):
                try:
                    if self.ssh_manager.close_connection(socket_path):
                        successful_closures += 1
                except Exception as e:
                    display_warning(f"Failed to close connection for {socket_path}: {str(e)}")

            # Report closure results
            if successful_closures == total_connections:
                display_success(f"Successfully closed all {total_connections} connections")
            else:
                display_warning(
                    f"Closed {successful_closures} out of {total_connections} connections"
                )
                display_info("Some connections may require manual cleanup")

        # Now exit
        display_success("Goodbye!")
        sys.exit(0)

    def cmd_clear(self, args: list[str]) -> bool:
        """Clear the terminal screen"""
        # Implementation for clearing the screen
        os.system("clear")
        return True

    def cmd_terminal(self, args: list[str]) -> bool:
        """Handle terminal command for changing terminal method"""
        if len(args) != 1:
            display_error("Usage: terminal <method>")
            display_info("  terminal <method>  : Change terminal method (auto, native, terminator)")
            display_info("Example: terminal native")
            return False

        raw_arg = args[0]
        arg = raw_arg.lower()

        # Check if the argument is a terminal method
        if arg in ["auto", "native", "terminator"]:
            if self.ssh_manager.set_terminal_method(arg):
                if CMD_LOGGER:
                    CMD_LOGGER.info(f"Terminal method changed to: {arg}")
                return True
            else:
                if CMD_LOGGER:
                    CMD_LOGGER.error(f"Failed to set terminal method: {arg}")
                return False

        # Check if user provided an SSH connection name (common mistake)
        socket_path = f"/tmp/{raw_arg}"
        if socket_path in self.ssh_manager.connections:
            display_error(f"To open a terminal, use: open {raw_arg}")
            display_info("The 'terminal' command is only for changing terminal methods.")
            if CMD_LOGGER:
                CMD_LOGGER.warning(
                    f"User tried to open terminal using old syntax: terminal {raw_arg}"
                )
            return False

        # Invalid terminal method
        display_error(f"Invalid terminal method: {arg}")
        display_info("Valid options: auto, native, terminator")
        return False

    def cmd_open(self, args: list[str]) -> bool:
        """Handle open command for opening a terminal session"""
        if len(args) != 1:
            display_error("Usage: open <ssh_id>")
            display_info("Example: open ubuntu")
            return False

        # Treat it as an SSH connection name
        conn_name = args[0]
        socket_path = f"/tmp/{conn_name}"

        # First check if the connection exists
        if socket_path not in self.ssh_manager.connections:
            # If not found, check if user provided a terminal method name (common mistake)
            arg = args[0].lower()
            if arg in ["auto", "native", "terminator"]:
                display_error(f"To change terminal method, use: terminal {arg}")
                display_info("The 'open' command is for opening terminal sessions.")
                if CMD_LOGGER:
                    CMD_LOGGER.warning(
                        f"User tried to change terminal method using wrong command: open {arg}"
                    )
                return False

            # Connection not found and not a terminal method name
            display_error(f"SSH connection '{conn_name}' not found")
            if CMD_LOGGER:
                CMD_LOGGER.error(f"Connection not found for open command: {conn_name}")
            return False

        try:
            if CMD_LOGGER:
                CMD_LOGGER.info(f"Opening terminal for connection: {conn_name}")

            self.ssh_manager.open_terminal(socket_path)
            display_success(f"Terminal opened for connection '{conn_name}'")
            return True
        except ValueError:
            display_error("Invalid SSH ID")
            return False

    def cmd_close(self, args: list[str]) -> bool:
        """Handle close command for closing an SSH connection"""
        if len(args) != 1:
            display_error("Usage: close <ssh_id>")
            display_info("Example: close ubuntu")
            return False

        conn_name = args[0]
        socket_path = f"/tmp/{conn_name}"

        if socket_path not in self.ssh_manager.connections:
            display_error(f"SSH connection '{conn_name}' not found")
            return False

        try:
            if self.ssh_manager.close_connection(socket_path):
                display_success(f"Connection '{conn_name}' closed")
                return True
            return False
        except ValueError:
            display_error("Invalid SSH ID")
            return False

    def cmd_scp(self, args: list[str]) -> bool:
        """Enter SCP mode for file transfers"""
        selected_connection = None

        # If a connection name is provided, use it
        if args:
            selected_connection = args[0]

            # Validate the connection exists
            socket_path = f"/tmp/{selected_connection}"
            if socket_path not in self.ssh_manager.connections:
                display_error(f"Connection '{selected_connection}' not found")
                return False

        # Start SCP mode
        console.print("\n[bold cyan]Entering SCP mode...[/bold cyan]")
        scp_mode = SCPMode(self.ssh_manager, selected_connection)
        scp_mode.run()
        console.print("\n[bold green]Exited SCP mode[/bold green]")
        return True

    def cmd_debug(self, args: list[str]) -> bool:
        """Enable or disable debug logging"""
        if args and args[0].lower() in ("off", "disable", "false", "0"):
            # Explicitly disable
            set_debug_mode(False)
            display_info("Debug logging disabled")
            if CMD_LOGGER:
                CMD_LOGGER.info("Debug logging disabled")
        elif args and args[0].lower() in ("on", "enable", "true", "1"):
            # Explicitly enable
            set_debug_mode(True)
            display_info("Debug logging enabled")
            if CMD_LOGGER:
                CMD_LOGGER.info("Debug logging enabled")
        else:
            # Toggle current state
            new_mode = not logging_module.DEBUG_MODE
            set_debug_mode(new_mode)
            status = "enabled" if new_mode else "disabled"
            display_info(f"Debug logging {status}")
            if CMD_LOGGER:
                CMD_LOGGER.info(f"Debug logging {status}")
        return True

    def cmd_disconnectall(self, args: list[str]) -> bool:
        """Close all connections"""
        # Implementation for disconnecting all connections
        if not self.ssh_manager.connections:
            display_info("No active connections to close")
            return True

        display_info(f"Closing {len(self.ssh_manager.connections)} connections...")

        # Make a copy of the connections to avoid modification during iteration
        connections = self.ssh_manager.connections.copy()
        for socket_path in list(connections.keys()):
            self.ssh_manager.close_connection(socket_path)

        display_success("All connections closed")
        return True

    def cmd_wizard(self, args: list[str]) -> bool:
        """Handle wizard command for guided workflows"""
        if not args:
            display_error("Usage: wizard <workflow>")
            display_info("Available workflows:")
            display_info("  [cyan]lazyssh[/cyan] - Guided SSH connection creation")
            display_info("  [cyan]tunnel[/cyan]  - Guided tunnel creation")
            display_info("Example: wizard lazyssh")
            return False

        workflow = args[0].lower()

        if workflow == "lazyssh":
            return self._wizard_lazyssh()
        elif workflow == "tunnel":
            return self._wizard_tunnel()
        else:
            display_error(f"Unknown workflow: {workflow}")
            display_info("Available workflows: lazyssh, tunnel")
            return False

    def _wizard_lazyssh(self) -> bool:
        """Guided workflow for SSH connection creation"""
        display_info("[bold cyan]\n🔮 SSH Connection Wizard[/bold cyan]")
        display_info("This wizard will guide you through creating a new SSH connection.\n")

        try:
            from rich.prompt import Confirm, Prompt

            # Get basic connection details
            host = Prompt.ask("[cyan]Enter hostname or IP address[/cyan]")
            if not host:
                display_error("Hostname is required")
                return False

            port = Prompt.ask("[cyan]Enter SSH port[/cyan]", default="22")
            try:
                port_int = int(port)
            except ValueError:
                display_error("Port must be a number")
                return False

            username = Prompt.ask("[cyan]Enter username[/cyan]")
            if not username:
                display_error("Username is required")
                return False

            socket_name = Prompt.ask("[cyan]Enter connection name (used as identifier)[/cyan]")
            if not socket_name:
                display_error("Connection name is required")
                return False

            # Validate socket name
            if not validate_config_name(socket_name):
                display_error(
                    "Invalid connection name. Use alphanumeric characters, dashes, and underscores only"
                )
                return False

            # Check if socket name already exists
            socket_path = f"/tmp/{socket_name}"
            if socket_path in self.ssh_manager.connections:
                display_warning(f"Connection name '{socket_name}' is already in use.")
                if not Confirm.ask("Do you want to use a different name?", default=True):
                    display_info("Proceeding with the existing connection name.")
                else:
                    new_socket = Prompt.ask("Enter a new connection name")
                    if not new_socket or not validate_config_name(new_socket):
                        display_error(
                            "Invalid connection name. Use alphanumeric characters, dashes, and underscores only"
                        )
                        return False
                    socket_name = new_socket
                    socket_path = f"/tmp/{socket_name}"

            # Ask about optional settings
            display_info("\n[bold yellow]Optional Settings:[/bold yellow]")

            # SSH Key
            use_ssh_key = Confirm.ask("Use specific SSH key?", default=False)
            identity_file = None
            if use_ssh_key:
                identity_file = Prompt.ask("Enter path to SSH key (e.g. ~/.ssh/id_rsa)")
                if not identity_file:
                    display_warning("No SSH key specified, using default SSH key")

            # Shell
            use_custom_shell = Confirm.ask("Use custom shell?", default=False)
            shell = None
            if use_custom_shell:
                shell = Prompt.ask("Enter shell to use", default="bash")
                if not shell:
                    display_warning("No shell specified, using default shell")

            # Terminal preference
            no_term = Confirm.ask("Disable terminal?", default=False)

            # Dynamic proxy
            use_proxy = Confirm.ask("Create dynamic SOCKS proxy?", default=False)
            dynamic_port = None
            if use_proxy:
                proxy_port = Prompt.ask("Enter proxy port", default="9050")
                try:
                    dynamic_port = int(proxy_port)
                except ValueError:
                    display_error("Port must be a number")
                    return False

            # Create the connection
            display_info(f"\n[bold green]Creating connection '{socket_name}'...[/bold green]")

            conn = SSHConnection(
                host=host,
                port=port_int,
                username=username,
                socket_path=socket_path,
                dynamic_port=dynamic_port,
                identity_file=identity_file,
                shell=shell,
                no_term=no_term,
            )

            if self.ssh_manager.create_connection(conn):
                display_success(f"Connection '{socket_name}' established successfully!")
                if dynamic_port:
                    display_success(f"Dynamic proxy created on port {dynamic_port}")

                # Ask about saving configuration
                if Confirm.ask("Save this connection configuration?", default=True):
                    config_name = Prompt.ask("Enter configuration name", default=socket_name)

                    if validate_config_name(config_name):
                        # Build config parameters
                        config_params = {
                            "host": host,
                            "port": port_int,
                            "username": username,
                            "socket_name": socket_name,
                        }

                        # Add optional parameters
                        if identity_file:
                            config_params["ssh_key"] = identity_file
                        if shell:
                            config_params["shell"] = shell
                        if no_term:
                            config_params["no_term"] = no_term
                        if dynamic_port:
                            config_params["proxy_port"] = dynamic_port

                        # Check if config already exists
                        if config_exists(config_name):
                            if not Confirm.ask(
                                f"Configuration '{config_name}' already exists. Overwrite?"
                            ):
                                display_info("Configuration not saved")
                                return True

                        # Save the configuration
                        if save_config(config_name, config_params):
                            display_success(f"Configuration '{config_name}' saved")
                        else:
                            display_error(f"Failed to save configuration '{config_name}'")
                    else:
                        display_error(
                            "Invalid configuration name. Use alphanumeric characters, dashes, and underscores only"
                        )

                return True
            else:
                display_error("Failed to create connection")
                return False

        except (KeyboardInterrupt, EOFError):
            display_info("\nWizard cancelled")
            return False
        except Exception as e:
            display_error(f"Error in wizard: {str(e)}")
            if CMD_LOGGER:
                CMD_LOGGER.error(f"Error in wizard lazyssh: {str(e)}")
            return False

    def _wizard_tunnel(self) -> bool:
        """Guided workflow for tunnel creation"""
        display_info("[bold cyan]\n🔮 Tunnel Creation Wizard[/bold cyan]")
        display_info("This wizard will guide you through creating a new tunnel.\n")

        if not self.ssh_manager.connections:
            display_error("No active connections available")
            display_info("First create a connection using 'wizard lazyssh' or 'lazyssh' command")
            return False

        try:
            from rich.prompt import Confirm, IntPrompt, Prompt

            # Select connection
            display_info("[bold yellow]Select SSH Connection:[/bold yellow]")
            conn_list = list(self.ssh_manager.connections.items())
            for i, (socket_path, conn) in enumerate(conn_list, 1):
                conn_name = Path(socket_path).name
                console.print(
                    f"  [info]{i}.[/info] [bold green]{conn_name}[/bold green] [dim]([/dim][bold cyan]{conn.username}[/bold cyan][bold]@[/bold][bold magenta]{conn.host}[/bold magenta][dim]:[/dim][yellow]{conn.port}[/yellow][dim])[/dim]"
                )

            choice = IntPrompt.ask("Enter connection number", default=1) - 1
            if not (0 <= choice < len(conn_list)):
                display_error("Invalid connection number")
                return False

            socket_path, conn = conn_list[choice]
            conn_name = Path(socket_path).name

            # Select tunnel type
            display_info(f"\n[bold yellow]Tunnel Type for '{conn_name}':[/bold yellow]")
            display_info("1. Forward tunnel (local port -> remote host:port)")
            display_info("2. Reverse tunnel (remote port -> local host:port)")

            tunnel_choice = IntPrompt.ask("Choose tunnel type (1-2)", default=1)
            if tunnel_choice not in [1, 2]:
                display_error("Invalid choice")
                return False

            is_reverse = tunnel_choice == 2

            # Get tunnel parameters
            if is_reverse:
                display_info("\n[bold yellow]Reverse Tunnel Parameters:[/bold yellow]")
                display_info("This will forward a remote port to your local machine")
                local_port = IntPrompt.ask("Enter local port to bind to")
                remote_host = Prompt.ask("Enter remote host to connect to", default="127.0.0.1")
                remote_port = IntPrompt.ask("Enter remote port to connect to")
                tunnel_type_str = "reverse"
            else:
                display_info("\n[bold yellow]Forward Tunnel Parameters:[/bold yellow]")
                display_info("This will forward a local port to a remote host")
                local_port = IntPrompt.ask("Enter local port to bind to")
                remote_host = Prompt.ask("Enter remote host to connect to")
                remote_port = IntPrompt.ask("Enter remote port to connect to")
                tunnel_type_str = "forward"

            # Confirm tunnel creation
            if is_reverse:
                tunnel_desc = f"Remote port {remote_port} -> Local {local_port}"
            else:
                tunnel_desc = f"Local port {local_port} -> Remote {remote_host}:{remote_port}"

            display_info("\n[bold green]Tunnel Summary:[/bold green]")
            display_info(f"Connection: {conn_name}")
            display_info(f"Type: {tunnel_type_str}")
            display_info(f"Mapping: {tunnel_desc}")

            if not Confirm.ask("Create this tunnel?", default=True):
                display_info("Tunnel creation cancelled")
                return False

            # Create the tunnel
            display_info(f"\n[bold green]Creating {tunnel_type_str} tunnel...[/bold green]")

            if self.ssh_manager.create_tunnel(
                socket_path, local_port, remote_host, remote_port, is_reverse
            ):
                display_success(f"{tunnel_type_str.capitalize()} tunnel created successfully!")
                display_info(f"Tunnel mapping: {tunnel_desc}")
                return True
            else:
                display_error("Failed to create tunnel")
                return False

        except (KeyboardInterrupt, EOFError):
            display_info("\nWizard cancelled")
            return False
        except Exception as e:
            display_error(f"Error in wizard: {str(e)}")
            if CMD_LOGGER:
                CMD_LOGGER.error(f"Error in wizard tunnel: {str(e)}")
            return False
