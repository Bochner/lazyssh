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
from prompt_toolkit.styles import Style

from .models import SSHConnection
from .scp_mode import SCPMode
from .ssh import SSHManager
from .ui import (
    display_error,
    display_info,
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
            for cmd in self.command_mode.commands:
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

        elif command == "terminal" or command == "close" or command == "term":
            # For terminal, term and close commands, we only expect one argument: the SSH connection name
            arg_position = len(words) - 1

            # Only show completions if we're at the exact position to enter the connection name
            # and not if we've already typed something after the command
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
                for cmd in self.command_mode.commands:
                    if not word_before_cursor or cmd.startswith(word_before_cursor):
                        yield Completion(cmd, start_position=-len(word_before_cursor))

        # Handle completion for close command
        elif command == "close" and len(words) == 2:
            connections = self.command_mode._get_connection_completions()
            for conn_name in connections:
                if conn_name.startswith(word_before_cursor):
                    yield Completion(conn_name, start_position=-len(word_before_cursor))

        # Handle completion for scp command
        elif command == "scp" and (len(words) == 1 or len(words) == 2):
            # Check if we have a space after "scp" to show completions immediately
            if (len(words) == 1 and text.endswith(" ")) or len(words) == 2:
                connections = self.command_mode._get_connection_completions()
                for conn_name in connections:
                    if not word_before_cursor or conn_name.startswith(word_before_cursor):
                        yield Completion(conn_name, start_position=-len(word_before_cursor))


class CommandMode:
    def __init__(self, ssh_manager: SSHManager):
        self.ssh_manager = ssh_manager
        self.commands = {
            "help": self.cmd_help,
            "exit": self.cmd_exit,
            "quit": self.cmd_exit,
            "lazyssh": self.cmd_lazyssh,
            "tunc": self.cmd_tunc,  # Create tunnel command
            "tund": self.cmd_tund,  # Delete tunnel command
            "list": self.cmd_list,
            "close": self.cmd_close,
            "terminal": self.cmd_terminal,
            "term": self.cmd_terminal,  # Alias for terminal
            "mode": self.cmd_mode,
            "clear": self.cmd_clear,
            "scp": self.cmd_scp,  # New SCP mode command
        }

        # Initialize prompt_toolkit components
        self.completer = LazySSHCompleter(self)
        self.session: PromptSession = PromptSession()
        self.style = Style.from_dict(
            {
                "prompt": "ansicyan bold",
            }
        )

    def _get_connection_completions(self) -> list[str]:
        """Get list of connection names for completion"""
        conn_completions = []
        for socket_path in self.ssh_manager.connections:
            conn_name = Path(socket_path).name
            conn_completions.append(conn_name)
        return conn_completions

    def get_prompt_text(self) -> HTML:
        """Get the prompt text with HTML formatting"""
        return HTML("<prompt>lazyssh></prompt> ")

    def show_status(self) -> None:
        """Display current connections and tunnels"""
        if self.ssh_manager.connections:
            display_ssh_status(self.ssh_manager.connections)
            for socket_path, conn in self.ssh_manager.connections.items():
                if conn.tunnels:
                    display_tunnels(socket_path, conn)

    def run(self) -> None:
        """Run the command mode interface"""
        while True:
            try:
                # Show current status and mode before each prompt
                print()  # Empty line for better readability
                self.show_status()

                # Get command with prompt_toolkit
                command = self.session.prompt(
                    self.get_prompt_text(),
                    style=self.style,
                    completer=self.completer,
                    complete_while_typing=True,
                )

                if not command.strip():
                    continue

                try:
                    parts = shlex.split(command)
                except ValueError:
                    display_error("Error parsing command. Check your quotes.")
                    continue

                if not parts:
                    continue

                cmd, *args = parts

                if cmd not in self.commands:
                    display_error(f"Unknown command: {cmd}")
                    display_info("Type 'help' for available commands")
                    self.show_available_commands()
                    continue

                result = self.commands[cmd](args)
                if result == "mode":
                    return  # Return to let main program switch modes
                elif result is True and cmd == "exit":
                    # Exit handled by cmd_exit
                    continue

            except KeyboardInterrupt:
                display_warning("Use 'exit' command to exit LazySSH safely.")
                continue
            except EOFError:
                display_warning("Use 'exit' command to exit LazySSH safely.")
                continue
            except Exception as e:
                display_error(f"Error: {str(e)}")
                display_info("Type 'help' for command usage")

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
                return False

            # Check if the socket name already exists
            socket_path = f"/tmp/{params['socket']}"
            if socket_path in self.ssh_manager.connections:
                display_warning(f"Socket name '{params['socket']}' is already in use.")
                confirmation = input("Do you want to use a different name? (Y/n): ").lower()
                if confirmation == "n":
                    display_info("Proceeding with the existing socket name.")
                else:
                    new_socket = input("Enter a new socket name: ")
                    if not new_socket:
                        display_error("Socket name cannot be empty.")
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
                    conn.dynamic_port = 1080
                    display_info(f"Using default dynamic proxy port: {conn.dynamic_port}")
                else:
                    # Otherwise use the specified port
                    try:
                        conn.dynamic_port = int(params["proxy"])
                    except ValueError:
                        display_error("Proxy port must be a number")
                        return False

            # Create the connection
            if self.ssh_manager.create_connection(conn):
                display_success(f"Connection '{params['socket']}' established")
                if conn.dynamic_port:
                    display_success(f"Dynamic proxy created on port {conn.dynamic_port}")
                return True
            return False
        except ValueError as e:
            display_error(str(e))
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

    def cmd_help(self, args: list[str]) -> bool:
        """Handle help command"""
        if not args:
            display_info("\nLazySSH Command Mode - Available Commands:\n")
            display_info("SSH Connection:")
            display_info(
                "  lazyssh -ip <ip> -port <port> -user <username> -socket <n> "
                "[-proxy [port]] [-ssh-key <path>] [-shell <shell>] [-no-term]"
            )
            display_info("  close <ssh_id>")
            display_info(
                "  Example: lazyssh -ip 192.168.10.50 -port 22 -user ubuntu -socket ubuntu"
            )
            display_info(
                "  Example: lazyssh -ip 192.168.10.50 -port 22 -user ubuntu -socket ubuntu -proxy 8080 -shell /bin/sh"
            )
            display_info("  Example: close ubuntu\n")

            display_info("Tunnel Management:")
            display_info("  tunc <ssh_id> <l|r> <local_port> <remote_host> <remote_port>")
            display_info("  Example (forward): tunc ubuntu l 8080 localhost 80")
            display_info("  Example (reverse): tunc ubuntu r 3000 127.0.0.1 3000\n")

            display_info("  tund <tunnel_id>")
            display_info("  Example: tund 1\n")

            display_info("Terminal:")
            display_info("  term <ssh_id>")
            display_info("  Example: term ubuntu\n")

            display_info("File Transfer:")
            display_info("  scp [<ssh_id>]")
            display_info("  Example: scp ubuntu\n")

            display_info("System Commands:")
            display_info("  list    - Show all connections and tunnels")
            display_info("  mode    - Switch mode (command/prompt)")
            display_info("  help    - Show this help")
            display_info("  exit    - Exit the program")
            return True

        cmd = args[0]
        if cmd == "lazyssh":
            display_info("\nCreate new SSH connection:")
            display_info(
                "Usage: lazyssh -ip <ip> -port <port> -user <username> -socket <n> "
                "[-proxy [port]] [-ssh-key <identity_file>] [-shell <shell>] [-no-term]"
            )
            display_info("Required parameters:")
            display_info("  -ip     : IP address or hostname of the SSH server")
            display_info("  -port   : SSH port number")
            display_info("  -user   : SSH username")
            display_info("  -socket : Name for the connection (used as identifier)")
            display_info("Optional parameters:")
            display_info("  -proxy  : Create a dynamic SOCKS proxy (default port: 1080)")
            display_info("  -ssh-key: Path to an SSH identity file")
            display_info("  -shell  : Specify the shell to use (e.g., /bin/sh)")
            display_info("  -no-term: Do not automatically open a terminal")
            display_info("\nExamples:")
            display_info("  lazyssh -ip 192.168.10.50 -port 22 -user ubuntu -socket ubuntu")
            display_info("  lazyssh -ip 192.168.10.50 -port 22 -user ubuntu -socket ubuntu -proxy")
            display_info(
                "  lazyssh -ip 192.168.10.50 -port 22 -user ubuntu -socket ubuntu -proxy 8080"
            )
            display_info(
                "  lazyssh -ip 192.168.10.50 -port 22 -user ubuntu -socket ubuntu -shell /bin/sh"
            )
            display_info(
                "  lazyssh -ip 192.168.10.50 -port 22 -user ubuntu -socket ubuntu -shell /bin/sh -no-term"
            )
        elif cmd == "tunc":
            display_info("\nCreate a new tunnel:")
            display_info("Usage: tunc <ssh_id> <l|r> <local_port> <remote_host> <remote_port>")
            display_info("Parameters:")
            display_info("  ssh_id      : The identifier of the SSH connection")
            display_info(
                "  l|r         : 'l' for local (forward) tunnel, 'r' for remote (reverse) tunnel"
            )
            display_info("  local_port  : The local port to use for the tunnel")
            display_info("  remote_host : The remote host to connect to")
            display_info("  remote_port : The remote port to connect to")
            display_info("\nExamples:")
            display_info(
                "  tunc ubuntu l 8080 localhost 80    # Forward local port 8080 to "
                "localhost:80 on the remote server"
            )
            display_info(
                "  tunc ubuntu r 3000 127.0.0.1 3000  # Reverse tunnel from remote port 3000 "
                "to local 127.0.0.1:3000"
            )
        elif cmd == "tund":
            display_info("\nDelete a tunnel:")
            display_info("Usage: tund <tunnel_id>")
            display_info("Parameters:")
            display_info("  tunnel_id : The ID of the tunnel to delete (shown in the list command)")
            display_info("\nExample:")
            display_info("  tund 1")
        elif cmd == "term":
            display_info("\nOpen a terminal for an SSH connection:")
            display_info("Usage: term <ssh_id>")
            display_info("Parameters:")
            display_info("  ssh_id : The identifier of the SSH connection")
            display_info("\nExample:")
            display_info("  term ubuntu")
        elif cmd == "mode":
            display_info("\nSwitch between command and interactive modes:")
            display_info("Usage: mode")
        elif cmd == "clear":
            display_info("\nClear the terminal screen:")
            display_info("Usage: clear")
        elif cmd == "scp":
            display_info("\nEnter SCP mode for file transfers:")
            display_info("Usage: scp [<connection_name>]")
            display_info("Parameters:")
            display_info(
                "  connection_name : The identifier of the SSH connection to use (optional)"
            )
            display_info("\nSCP mode leverages your existing SSH connection's master socket")
            display_info(
                "to perform secure file transfers without requiring additional authentication."
            )
            display_info("\nSCP mode commands:")
            display_info("  put <local_file> [<remote_file>]  - Upload file to remote server")
            display_info("  get <remote_file> [<local_file>]  - Download file from remote server")
            display_info("  ls [<remote_path>]                - List files in remote directory")
            display_info("  cd <remote_path>                  - Change remote working directory")
            display_info("  pwd                               - Show current remote directory")
            display_info(
                "  mget <pattern>                    - Download multiple files matching pattern"
            )
            display_info(
                "  local [<path>]                    - Set or show local download directory"
            )
            display_info("  exit                              - Exit SCP mode")
            display_info("\nExamples:")
            display_info(
                "  scp ubuntu                        # Enter SCP mode with the 'ubuntu' connection"
            )
            display_info(
                "  scp                               # Enter SCP mode and select a connection interactively"
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
            # Prompt user for confirmation
            confirmation = input("You have active connections. Close them and exit? (y/N): ")
            if confirmation.lower() != "y":
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

    def cmd_mode(self, args: list[str]) -> str:
        """Switch mode (command/prompt)"""
        return "mode"

    def cmd_clear(self, args: list[str]) -> bool:
        """Clear the screen"""
        os.system("clear")
        return True

    def cmd_terminal(self, args: list[str]) -> bool:
        """Handle terminal command for opening a terminal"""
        if len(args) != 1:
            display_error("Usage: term <ssh_id>")
            display_info("Example: term ubuntu")
            return False

        conn_name = args[0]
        socket_path = f"/tmp/{conn_name}"

        if socket_path not in self.ssh_manager.connections:
            display_error(f"SSH connection '{conn_name}' not found")
            return False

        try:
            conn = self.ssh_manager.connections[socket_path]

            # Build the SSH command for display
            ssh_cmd = f"ssh -tt -S {socket_path} {conn.username}@{conn.host}"
            if conn.shell:
                ssh_cmd += f" {conn.shell}"

            # Display the command that will be executed
            display_info("Opening terminal with command:")
            display_info(ssh_cmd)

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
        display_info("Entering SCP mode...")
        scp_mode = SCPMode(self.ssh_manager, selected_connection)
        scp_mode.run()
        display_info("Exited SCP mode")
        return True
