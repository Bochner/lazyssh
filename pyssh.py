#!/usr/bin/env python3
import argparse
import subprocess

def ssh_to_target(target_ip, target_port, hostname, username, verbosity, dynamic_port):
    # Create control path
    control_path = f"/tmp/{hostname}"

    # SSH command with necessary options
    ssh_command = [
        "ssh",
        "-o", "StrictHostKeyChecking=no",  # Disable host key checking
        "-o", "UserKnownHostsFile=/dev/null",  # Ignore known hosts file
        "-M",  # Master mode
        "-S", control_path,  # Control socket
        "-p", str(target_port),  # Target port
    ]

    # Add verbosity option based on the verbosity level
    if verbosity == 1:
        ssh_command.append("-v")
    elif verbosity > 1:
        for _ in range(verbosity):
            ssh_command.append("-v")

    # Add dynamic port forwarding if specified
    if dynamic_port:
        ssh_command.extend(["-D", str(dynamic_port)])

    ssh_command.append(f"{username}@{target_ip}")  # Username and target IP

    # Show the full SSH command
    print("The SSH command to be run is:")
    print(" ".join(ssh_command))

    # Prompt for confirmation
    confirm = input("Do you want to run this command? (Y/N): ").strip().lower()
    if confirm == 'y':
        # Execute SSH command
        subprocess.run(ssh_command)
    else:
        print("Command not executed.")

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="SSH to a target with specified parameters")
    parser.add_argument("-ip", help="Target IP address", required=True)
    parser.add_argument("-port", help="Target port", type=int, required=True)
    parser.add_argument("-host", help="Hostname, will be used to create control socket at /tmp/<hostname>", required=True)
    parser.add_argument("-user", help="Username", required=True)
    parser.add_argument("-v", dest="verbosity", action="count", default=0, help="Increase verbosity level (-v, -vv, -vvv)")
    parser.add_argument("-D", dest="dynamic_port", type=int, help="Dynamic port forwarding")
    args = parser.parse_args()

    # SSH to target
    ssh_to_target(args.ip, args.port, args.host, args.user, args.verbosity, args.dynamic_port)

if __name__ == "__main__":
    main()
