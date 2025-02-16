#!/usr/bin/env python

import subprocess
import argparse
import readline  # Added readline module

def create_ssh_command(socket_prefix):
    """
    Creates the SSH command with control socket option.
    """
    return ["ssh", "-S", socket_prefix, "localhost"]

def execute_ssh_command(ssh_command, command):
    """
    Executes the SSH command with the specified command.
    """
    try:
        output = subprocess.check_output(ssh_command + [f'"{command}"'], shell=False)
        return output.decode().strip()
    except subprocess.CalledProcessError as e:
        print(f"Error executing SSH command: {e}")
        return None

def main(socket_prefix):
    ssh_command = create_ssh_command(socket_prefix)

    survey_commands = ["w", "date", "date -u", "id"]

    try:
        while True:
            # Readline configuration
            readline.parse_and_bind('"\e[A": history-search-backward')  # Up arrow key

            try:
                cmd = input("sshtun> ").lower()
            except KeyboardInterrupt:
                print("\nCtrl + C detected. Use 'exit' to exit the program.")
                continue

            if cmd in survey_commands:
                output = execute_ssh_command(ssh_command, cmd)
                if output is not None:
                    print(output)
            elif cmd == "exit":
                print("Exiting...")
                break
            elif cmd == "help":
                print("""
Available commands:
  w: Display information about the users currently logged in
  date: Display the current date and time
  date -u: Display the current date and time in UTC
  id: Display the user and group IDs of the current user
  exit: Exit the program
""")
            else:
                print("Invalid command. Type 'help' for available commands.")

    except KeyboardInterrupt:
        print("\nCtrl + C detected. Use 'exit' to exit the program.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Linux Survey via SSH Control Socket")
    parser.add_argument("--socket", help="SSH control socket", required=True)
    args = parser.parse_args()
    main(args.socket)
