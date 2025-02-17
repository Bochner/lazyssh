"""Command mode interface for LazySSH using prompt_toolkit"""
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter, NestedCompleter, Completer, Completion
from prompt_toolkit.document import Document
from prompt_toolkit.styles import Style
from prompt_toolkit.formatted_text import HTML
import shlex
import os
from typing import List, Dict, Set, Iterable

from .ssh import SSHManager
from .models import SSHConnection
from .ui import (
    display_error, display_info, display_success,
    display_ssh_status, display_tunnels
)

class LazySSHCompleter(Completer):
    def __init__(self, command_mode):
        self.command_mode = command_mode
        
    def get_completions(self, document: Document, complete_event) -> Iterable[Completion]:
        text = document.text
        word_before_cursor = document.get_word_before_cursor()
        
        # Split the input into words
        try:
            words = shlex.split(text[:document.cursor_position])
        except ValueError:
            words = text[:document.cursor_position].split()
        
        if not words or (len(words) == 1 and not text.endswith(' ')):
            # Show base commands if at start
            for cmd in self.command_mode.commands:
                if not word_before_cursor or cmd.startswith(word_before_cursor):
                    yield Completion(cmd, start_position=-len(word_before_cursor))
            return
            
        command = words[0].lower()
        
        if command == 'lazyssh':
            # Get used arguments
            used_args = set()
            for i, word in enumerate(words[:-1]):  # Exclude last word if it's incomplete
                if word.startswith('-'):
                    used_args.add(word)
            
            # Available arguments for lazyssh
            all_args = {'-ip', '-port', '-socket', '-user'}
            remaining_args = all_args - used_args
            
            # If typing a new argument or after a space
            if word_before_cursor.startswith('-') or text.endswith(' '):
                for arg in remaining_args:
                    if word_before_cursor.startswith('-'):
                        if arg.startswith(word_before_cursor):
                            yield Completion(arg, start_position=-len(word_before_cursor))
                    else:
                        yield Completion(arg, start_position=0)
                        
        elif command == 'tunc':
            if len(words) == 1:
                # Show available connections
                for conn_name in self.command_mode._get_connection_completions():
                    yield Completion(conn_name, start_position=-len(word_before_cursor))
            elif len(words) == 2:
                # Show l/r options
                for option in ['l', 'r']:
                    if option.startswith(word_before_cursor.lower()):
                        yield Completion(option, start_position=-len(word_before_cursor))
                        
        elif command == 'term' or command == 'close':
            if len(words) == 1:
                # Show available connections
                for conn_name in self.command_mode._get_connection_completions():
                    yield Completion(conn_name, start_position=-len(word_before_cursor))
                    
        elif command == 'tund':
            if len(words) == 1:
                # Show available tunnel IDs
                for tunnel_id in self.command_mode._get_tunnel_id_completions():
                    yield Completion(tunnel_id, start_position=-len(word_before_cursor))
                    
        elif command == 'help':
            if len(words) == 1:
                # Show available commands for help
                for cmd in self.command_mode.commands:
                    yield Completion(cmd, start_position=-len(word_before_cursor))

class CommandMode:
    def __init__(self, ssh_manager: SSHManager):
        self.ssh_manager = ssh_manager
        self.session = PromptSession(
            complete_while_typing=True,
            complete_in_thread=True,
            enable_history_search=True
        )
        self.commands = {
            'lazyssh': self.cmd_create_connection,
            'tunc': self.cmd_create_tunnel,
            'tund': self.cmd_destroy_tunnel,
            'term': self.cmd_open_terminal,
            'help': self.cmd_help,
            'exit': self.cmd_exit,
            'mode': self.cmd_switch_mode,
            'list': self.cmd_list,
            'close': self.cmd_close_connection,
        }

        # Dynamic command completion
        self.style = Style.from_dict({
            'prompt': 'ansicyan bold',
        })
        self.completer = LazySSHCompleter(self)

    def _get_connection_completions(self):
        """Get completion dict for connection names"""
        return {os.path.basename(socket_path): None 
                for socket_path in self.ssh_manager.connections}

    def _get_tunnel_id_completions(self):
        """Get completion dict for tunnel IDs"""
        tunnel_ids = {}
        for conn in self.ssh_manager.connections.values():
            for tunnel in conn.tunnels:
                tunnel_ids[tunnel.id] = None
        return tunnel_ids

    def _get_tunc_completions(self):
        """Get completion dict for tunc command"""
        conn_completions = {}
        for socket_path in self.ssh_manager.connections:
            name = os.path.basename(socket_path)
            conn_completions[name] = {
                'l': None,
                'r': None
            }
        return conn_completions

    def get_prompt_text(self) -> HTML:
        """Get the prompt text with proper formatting"""
        return HTML('<prompt>lazyssh></prompt> ')

    def cmd_create_connection(self, args: List[str]) -> bool:
        """Handle lazyssh command for creating new connections"""
        try:
            # Parse arguments into dictionary
            params = {}
            i = 0
            while i < len(args):
                if args[i].startswith('-'):
                    if i + 1 < len(args):
                        params[args[i][1:]] = args[i + 1]
                        i += 2
                    else:
                        raise ValueError(f"Missing value for argument {args[i]}")
                else:
                    i += 1

            # Check required parameters
            required = ['ip', 'port', 'socket', 'user']
            missing = [f"-{param}" for param in required if param not in params]
            if missing:
                display_error(f"Missing required parameters: {', '.join(missing)}")
                display_info("Usage: lazyssh -ip <ip> -port <port> -socket <name> -user <username>")
                return False

            conn = SSHConnection(
                host=params['ip'],
                port=int(params['port']),
                username=params['user'],
                socket_path=f"/tmp/lazyssh/{params['socket']}"
            )

            if self.ssh_manager.create_connection(conn):
                display_success(f"Connection '{params['socket']}' established")
                return True
            return False
        except ValueError as e:
            display_error(str(e))
            return False

    def cmd_create_tunnel(self, args: List[str]) -> bool:
        """Handle tunc command for creating tunnels"""
        if len(args) != 5:
            display_error("Usage: tunc <ssh_id> <l|r> <local_port> <remote_host> <remote_port>")
            display_info("Example: tunc ubuntu l 8080 localhost 80")
            return False

        ssh_id, tunnel_type, local_port, remote_host, remote_port = args
        socket_path = f"/tmp/lazyssh/{ssh_id}"

        try:
            local_port = int(local_port)
            remote_port = int(remote_port)
            is_reverse = tunnel_type.lower() == 'r'

            if self.ssh_manager.create_tunnel(socket_path, local_port, remote_host, remote_port, is_reverse):
                return True
            return False
        except ValueError:
            display_error("Port numbers must be integers")
            return False

    def cmd_destroy_tunnel(self, args: List[str]) -> bool:
        """Handle tund command for destroying tunnels"""
        if len(args) != 1:
            display_error("Usage: tund <tunnel_id>")
            return False

        tunnel_id = args[0]
        # Search through all connections for the tunnel
        for socket_path, conn in self.ssh_manager.connections.items():
            tunnel = conn.get_tunnel(tunnel_id)
            if tunnel:
                if self.ssh_manager.close_tunnel(socket_path, tunnel_id):
                    return True
                break

        display_error(f"Tunnel {tunnel_id} not found")
        return False

    def cmd_open_terminal(self, args: List[str]) -> bool:
        """Handle term command for opening terminals"""
        if len(args) != 1:
            display_error("Usage: term <ssh_id>")
            display_info("Example: term ubuntu")
            return False

        ssh_id = args[0]
        socket_path = f"/tmp/lazyssh/{ssh_id}"
        self.ssh_manager.open_terminal(socket_path)
        return True

    def cmd_close_connection(self, args: List[str]) -> bool:
        """Handle close command for closing SSH connections"""
        if len(args) != 1:
            display_error("Usage: close <ssh_id>")
            display_info("Example: close ubuntu")
            return False

        ssh_id = args[0]
        socket_path = f"/tmp/lazyssh/{ssh_id}"

        if socket_path not in self.ssh_manager.connections:
            display_error(f"Connection '{ssh_id}' not found")
            return False

        if self.ssh_manager.close_connection(socket_path):
            display_success(f"Connection '{ssh_id}' closed")
            return True
        return False

    def cmd_list(self, args: List[str]) -> bool:
        """List all connections and their tunnels"""
        if not self.ssh_manager.connections:
            display_info("No active connections")
            return True

        display_info("\nActive SSH Connections:\n")
        for socket_path, conn in self.ssh_manager.connections.items():
            name = os.path.basename(socket_path)
            display_info(f"Connection: {name}")
            display_info(f"  Host    : {conn.username}@{conn.host}:{conn.port}")
            if conn.dynamic_port:
                display_info(f"  Dynamic : SOCKS proxy on port {conn.dynamic_port}")
            if conn.tunnels:
                display_info("  Tunnels :")
                for tunnel in conn.tunnels:
                    tunnel_type = "reverse" if tunnel.type == "reverse" else "forward"
                    display_info(f"    {tunnel.id}: {tunnel_type} {tunnel.local_port} -> {tunnel.remote_host}:{tunnel.remote_port}")
            display_info("")  # Empty line between connections
        return True

    def cmd_help(self, args: List[str]) -> bool:
        """Display help information"""
        if not args:
            display_info("\nLazySSH Command Mode - Available Commands:\n")
            display_info("SSH Connection:")
            display_info("  lazyssh -ip <ip> -port <port> -socket <name> -user <username>")
            display_info("  close <ssh_id>")
            display_info("  Example: lazyssh -ip 192.168.10.50 -port 22 -socket ubuntu -user ubuntu")
            display_info("  Example: close ubuntu\n")
            
            display_info("Tunnel Management:")
            display_info("  tunc <ssh_id> <l|r> <local_port> <remote_host> <remote_port>")
            display_info("  Example (forward): tunc ubuntu l 8080 localhost 80")
            display_info("  Example (reverse): tunc ubuntu r 3000 127.0.0.1 3000\n")
            
            display_info("  tund <tunnel_id>")
            display_info("  Example: tund abc123ef\n")
            
            display_info("Terminal:")
            display_info("  term <ssh_id>")
            display_info("  Example: term ubuntu\n")
            
            display_info("System Commands:")
            display_info("  list    - Show all connections and tunnels")
            display_info("  mode    - Switch mode (command/prompt)")
            display_info("  help    - Show this help")
            display_info("  exit    - Exit the program")
            return True

        cmd = args[0]
        if cmd == 'lazyssh':
            display_info("\nCreate new SSH connection:")
            display_info("Usage: lazyssh -ip <ip_address> -port <port> -socket <name> -user <username>")
            display_info("All parameters are required.")
            display_info("\nExample:")
            display_info("  lazyssh -ip 192.168.10.50 -port 22 -socket ubuntu -user ubuntu")
        elif cmd == 'close':
            display_info("\nClose SSH connection:")
            display_info("Usage: close <ssh_id>")
            display_info("  <ssh_id> : Name of the SSH connection to close")
            display_info("\nExample:")
            display_info("  close ubuntu")
        elif cmd == 'tunc':
            display_info("\nCreate tunnel:")
            display_info("Usage: tunc <ssh_id> <l|r> <local_port> <remote_host> <remote_port>")
            display_info("  <ssh_id>      : Name of the SSH connection (from socket name)")
            display_info("  <l|r>         : 'l' for local (forward) tunnel, 'r' for reverse tunnel")
            display_info("  <local_port>  : Local port number")
            display_info("  <remote_host> : Remote host to connect to")
            display_info("  <remote_port> : Remote port number")
            display_info("\nExamples:")
            display_info("  Forward tunnel : tunc ubuntu l 8080 localhost 80")
            display_info("  Reverse tunnel : tunc ubuntu r 3000 127.0.0.1 3000")
        elif cmd == 'tund':
            display_info("\nDestroy tunnel:")
            display_info("Usage: tund <tunnel_id>")
            display_info("  <tunnel_id> : ID of the tunnel to destroy (shown in 'list' output)")
            display_info("\nExample:")
            display_info("  tund 1")
        elif cmd == 'term':
            display_info("\nOpen terminal:")
            display_info("Usage: term <ssh_id>")
            display_info("  <ssh_id> : Name of the SSH connection (from socket name)")
            display_info("\nExample:")
            display_info("  term ubuntu")
        elif cmd == 'list':
            display_info("\nList connections and tunnels:")
            display_info("Usage: list")
            display_info("Shows all active SSH connections and their tunnels")
        else:
            display_error(f"Unknown command: {cmd}")
            return False
        return True

    def cmd_exit(self, args: List[str]) -> bool:
        """Exit the program"""
        from lazyssh.__main__ import safe_exit
        safe_exit()
        return True  # Will only reach here if user cancels exit

    def cmd_switch_mode(self, args: List[str]) -> bool:
        """Switch mode (command/prompt)"""
        return "mode"  # Return special value to indicate mode switch

    def show_status(self):
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
                
                command = self.session.prompt(
                    self.get_prompt_text(),
                    style=self.style,
                    completer=self.completer,
                    complete_while_typing=True
                )

                if not command.strip():
                    continue

                parts = shlex.split(command)
                cmd, *args = parts

                if cmd not in self.commands:
                    display_error(f"Unknown command: {cmd}")
                    display_info("Type 'help' for available commands")
                    continue

                result = self.commands[cmd](args)
                if result == "mode":
                    return  # Return to let main program switch modes
                elif result is True and cmd == "exit":
                    # Exit handled by cmd_exit
                    continue

            except KeyboardInterrupt:
                continue
            except EOFError:
                from lazyssh.__main__ import safe_exit
                safe_exit()
            except Exception as e:
                display_error(f"Error: {str(e)}")
                display_info("Type 'help' for command usage")