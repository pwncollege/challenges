#!/usr/bin/env python3
import os
import pty
import select
import subprocess
import time
from pathlib import Path

assert Path("/challenge/flag.c").is_file()
master, slave = pty.openpty()
vm = subprocess.Popen(["/challenge/run"], stdin=slave, stdout=slave, stderr=slave)
os.close(slave)


def prompt():
    output = b""
    deadline = time.monotonic() + 15
    while b"vm:~# " not in output:
        assert time.monotonic() < deadline, output.decode(errors="replace")
        if select.select([master], [], [], 1)[0]:
            chunk = os.read(master, 65536)
            output += chunk
            print(chunk.decode(errors="replace"), end="", flush=True)
    return output.replace(b"\r", b"")


try:
    boot = prompt()
    tasks = list(Path(f"/proc/{vm.pid}/task").glob("*/status"))
    assert tasks
    for task in tasks:
        status = dict(line.split(":", 1) for line in task.read_text().splitlines())
        assert status["Uid"].split() == ["65534"] * 4
        assert status["Gid"].split() == ["65534"] * 4
        assert set(status["Groups"].split()) <= {"65534"}
        assert int(status["CapEff"], 16) == 0
    command = (
        "test $(id -u) = 0 && test ! -e /dev/flag && "
        "test ! -e /dev/tty0 && test ! -e /dev/tty63 && test -c /dev/ttyS0 && "
        'test "$(cut -f1 /proc/sys/kernel/printk)" = 5 && '
        "test ! -e /flag && test ! -e /challenge/flag.c && "
        "test -r /lib/modules/$(uname -r)/updates/flag.ko && "
        "modprobe flag && test -c /dev/flag && "
        "lsmod | grep -q '^flag ' && "
        "! cat /dev/flag && ! sh -c 'echo wrong > /dev/flag' && "
        "! cat /dev/flag && modprobe -r flag && test ! -e /dev/flag && echo DEVICE_PASS\n"
    )
    os.write(master, command.encode())
    output = prompt()
    assert b"DEVICE_PASS" in output.splitlines()
    assert b"pwn.college{" not in boot + output
    os.write(master, b"exit\n")
    assert vm.wait(timeout=10) == 0
finally:
    if vm.poll() is None:
        try:
            vm.kill()
            vm.wait()
        except PermissionError:
            pass
    os.close(master)
