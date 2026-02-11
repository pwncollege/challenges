#!/usr/bin/exec-suid -- /bin/python3 -I

import os
import sys
import re
import random
import string
import socket
import subprocess
import multiprocessing
import struct
import signal
import fcntl
import ctypes
import tempfile
import pathlib
import contextlib
import shutil
import atexit

import requests


config = (pathlib.Path(__file__).parent / ".config").read_text()
level = int(config)

strace_expected_parent = r"""
1..10   execve(<execve_args>) = 0
2..10   socket(AF_INET, SOCK_STREAM, IPPROTO_IP) = 3
3..10   bind(3, {sa_family=AF_INET, sin_port=htons(<bind_port>), sin_addr=inet_addr("<bind_address>")}, 16) = 0
4..10   listen(3, 0) = 0
5..10   accept(3, NULL, NULL) = 4
6..8    read(4, <read_request>, <read_request_count>) = <read_request_result>
7..8    open("<open_path>", O_RDONLY) = 5
7..8    read(5, <read_file>, <read_file_count>) = <read_file_result>
7..8    close(5) = 0
6..8    write(4, "HTTP/1.0 200 OK\r\n\r\n", 19) = 19
7..8    write(4, <write_file>, <write_file_count>) = <write_file_result>
9..10   fork() = <fork_result>
6..10   close(4) = 0
8..10   accept(3, NULL, NULL) = ?
1..7    exit(0) = ?
"""

strace_expected_child = r"""
9..10   close(3) = 0
9..10   read(4, <read_request>, <read_request_count>) = <read_request_result>
9..9    open("<open_path>", O_RDONLY) = 3
9..9    read(3, <read_file>, <read_file_count>) = <read_file_result>
10..10  open("<open_path>", O_WRONLY|O_CREAT, 0777) = 3
10..10  write(3, <write_file>, <write_file_count>) = <write_file_result>
9..10   close(3) = 0
9..10   write(4, "HTTP/1.0 200 OK\r\n\r\n", 19) = 19
9..9    write(4, <write_file>, <write_file_count>) = <write_file_result>
9..10   exit(0) = ?
"""


def run_sandbox(target, *, privileged=True):
    CLONE_NEWNS       = 0x00020000 # New mount namespace group
    CLONE_NEWCGROUP   = 0x02000000 # New cgroup namespace
    CLONE_NEWUTS      = 0x04000000 # New utsname namespace
    CLONE_NEWIPC      = 0x08000000 # New ipc namespace
    CLONE_NEWUSER     = 0x10000000 # New user namespace
    CLONE_NEWPID      = 0x20000000 # New pid namespace
    CLONE_NEWNET      = 0x40000000 # New network namespace

    PR_SET_PDEATHSIG  = 1
    PR_SET_DUMPABLE   = 4

    result = multiprocessing.Value("B", False)

    pid = os.fork()
    if pid:
        os.wait()
        return result.value

    libc = ctypes.CDLL("libc.so.6")

    suid = os.geteuid() != os.getuid()
    os.setpgrp()
    os.seteuid(os.getuid())
    # TODO:
    # libc.prctl(PR_SET_DUMPABLE, not suid)
    libc.prctl(PR_SET_DUMPABLE, True)
    libc.prctl(PR_SET_PDEATHSIG, signal.SIGKILL)

    sandbox_euid = os.geteuid()
    sandbox_egid = os.getegid()

    unshare_result = libc.unshare(
        CLONE_NEWUSER |
        CLONE_NEWNS |
        CLONE_NEWCGROUP |
        CLONE_NEWUTS |
        CLONE_NEWIPC |
        CLONE_NEWPID |
        CLONE_NEWNET
    )
    assert unshare_result == 0

    pid = os.fork()
    if pid:
        os.wait()
        os._exit(0)

    proc_values = {
        f"/proc/self/setgroups": "deny",
        f"/proc/self/uid_map": f"0 {sandbox_euid} 1",
        f"/proc/self/gid_map": f"0 {sandbox_egid} 1",
    }
    for path, value in proc_values.items():
        with open(path, "w") as f:
            f.write(value)

    libc.prctl(PR_SET_PDEATHSIG, signal.SIGKILL)

    socket.sethostname("sandbox")
    subprocess.run(["/sbin/ip", "link", "set", "dev", "lo", "up"])

    # if not privileged:
    #     unshare_result = libc.unshare(
    #         CLONE_NEWUSER
    #     )
    #     assert unshare_result == 0

    #     proc_values = {
    #         "/proc/self/setgroups": "deny",
    #         "/proc/self/uid_map": f"{sandbox_euid} 0 1",
    #         "/proc/self/gid_map": f"{sandbox_egid} 0 1",
    #     }
    #     for path, value in proc_values.items():
    #         with open(path, "w") as f:
    #             f.write(value)

    result.value = target()
    os._exit(0)


@contextlib.contextmanager
def strace(argv, *args, results_dir, timeout=None):
    sem_start_strace = multiprocessing.Semaphore(0)
    sem_start_target = multiprocessing.Semaphore(0)

    pid = os.fork()
    if not pid:
        PR_SET_DUMPABLE     = 4
        libc = ctypes.CDLL("libc.so.6")
        libc.prctl(PR_SET_DUMPABLE, True)
        dev_null_fd = os.open("/dev/null", os.O_RDWR)
        for std_fd in [0, 1, 2]:
            os.dup2(dev_null_fd, std_fd)
        if timeout:
            signal.alarm(timeout)
        sem_start_strace.release()
        sem_start_target.acquire()
        os.execve(argv[0], argv, {})

    args = [
        "/usr/bin/strace",
        "-o", f"{results_dir}/strace",
        "-ff",
        "-s", "512",
        "-A",
        "-e", "trace=!futex",  # Ignore `sem_start_target.acquire()`
        *args,
        "-p",
        str(pid),
    ]

    sem_start_strace.acquire()
    strace_proc = subprocess.Popen(args,
                                   stdin=subprocess.DEVNULL,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
    strace_proc.stderr.readline()  # TODO: risk of stderr filling up
    sem_start_target.release()

    results = {}
    try:
        yield results
    finally:
        os.waitpid(pid, 0)
        # TODO: capture stdout/stderr (pipes)
        stdout = b""
        stderr = b""
        results["stdout"] = stdout
        results["stderr"] = stderr
        log = {}
        for path in results_dir.iterdir():
            pid = int(path.suffix[1:])
            log[pid] = path.read_text()
        results["log"] = log


def immutable_file_copy(path):
    memfd = os.memfd_create(path, os.MFD_CLOEXEC|os.MFD_ALLOW_SEALING)
    os.write(memfd, path.read_bytes())
    seals = (
        fcntl.F_SEAL_WRITE |
        fcntl.F_SEAL_GROW |
        fcntl.F_SEAL_SHRINK |
        fcntl.F_SEAL_SEAL
    )
    fcntl.fcntl(memfd, fcntl.F_ADD_SEALS, seals)
    return memfd


def create_secret_dir():
    pid = os.getpid()

    prev_umask = os.umask(0)
    tmp = pathlib.Path("/tmp")
    tmp_dir = tmp / pathlib.Path(os.urandom(16).hex())
    tmp_dir.mkdir(0o711)
    secret_dir = tmp_dir / os.urandom(16).hex()
    secret_dir.mkdir(0o777)
    os.umask(prev_umask)

    def cleanup():
        if os.getpid() == pid:
            shutil.rmtree(tmp_dir)
    atexit.register(cleanup)

    return secret_dir


def validate_strace(level, results, requirements):
    stdout = results["stdout"].decode("latin")
    stderr = results["stderr"].decode("latin")

    def strace_validate(validate_name, expected_strace, result_strace, requirements):
        expected = []
        for line in expected_strace.strip().splitlines():
            levels, expect = line.split(None, 1)
            start, stop = levels.split("..")
            if ((not start or level >= int(start)) and
                (not stop or level <= int(stop))):
                expected.append(expect)

        result = result_strace.strip().splitlines()

        captured = {}

        requirements = {
            "bind_port": (lambda port: port == "80", "Bind to port 80"),
            "bind_address": (lambda addr: addr == "0.0.0.0", "Bind to address 0.0.0.0"),
            **requirements
        }

        print(f"===== Expected: {validate_name} =====")
        for expect in expected:
            print(f"[ ] {expect}")
            for name, (requirement, message) in requirements.items():
                if f"<{name}>" in expect:
                    print(f"    - {message}")
        print()

        print(f"===== Trace: {validate_name} =====")
        # print(f"stdout: {stdout!r}")
        # print(f"stderr: {stderr!r}")
        errors = []
        while result:
            current = result.pop(0)
            match = None
            if expected:
                re_expect = ("^" +
                             re.sub(r"<(\w+)>", r"(?P<\1>.*)",
                                    re.escape(expected[0]).replace(r"\ =\ ", r"\s*=\s*")) +
                             "$")
                match = re.match(re_expect, current)
            if match:
                match_captured = match.groupdict()
                match = True
                for name, capture in match_captured.items():
                    if name in requirements:
                        requirement, message = requirements[name]
                        if not requirement(capture):
                            errors.append(f"{validate_name}: {message}")
                            match = False
                captured.update(match_captured)
                expected.pop(0)
            if match:
                print("[✓]", current)
            elif match is False:
                print("[x]", current)
                success = False
            else:
                print("[?]", current)
        print()

        for expect in expected:
            errors.append(f"{validate_name}: Missing `{expect}`")

        return captured, errors

    errors = []

    parent_pid, parent_result = min(results["log"].items())
    parent_captured, parent_errors = strace_validate("Parent Process", strace_expected_parent, parent_result, requirements)
    errors.extend(parent_errors)

    child_pid = int(parent_captured.get("fork_result", 0))
    if child_pid:
        child_result = results["log"][child_pid]
        child_captured, child_errors = strace_validate("Child Process", strace_expected_child, child_result, requirements)
        errors.extend(child_errors)

    return errors


def retry_session():
    session = requests.Session()
    retries = requests.adapters.Retry(total=4, backoff_factor=0.1)
    session.mount("http://", requests.adapters.HTTPAdapter(max_retries=retries))
    return session


def random_data():
    return ''.join(random.choices(string.ascii_letters + string.digits,
                                  k=random.randrange(32, 256))).encode()


def connect():
    session = retry_session()
    try:
        session.get("http://localhost", timeout=1)
    except requests.exceptions.ConnectionError:
        pass


def validate_connect():
    session = retry_session()
    try:
        session.get("http://localhost", timeout=1)
    except requests.exceptions.ConnectionError:
        return "Connect: Failed to connect"


def validate_get(data=None):
    if data is None:
        data = random_data()
    session = retry_session()
    with tempfile.NamedTemporaryFile() as f:
        f.write(data)
        f.flush()
        try:
            response = session.get("http://localhost" + f.name, timeout=1)
        except requests.exceptions.ConnectionError:
            return "GET: Failed to connect"
        if response.text.encode() != data:
            return "GET: File contents not correct"


def validate_post(data=None):
    if data is None:
        data = random_data()
    session = retry_session()
    with tempfile.NamedTemporaryFile() as f:
        pass
    try:
        session.post("http://localhost" + f.name, data=data, timeout=1)
    except requests.exceptions.ConnectionError:
        return "POST: Failed to connect"
    try:
        if open(f.name, "rb").read() != data:
            return "POST: File contents not correct"
    except FileNotFoundError:
        return "POST: File does not exist"


def challenge():
    description = {
        1: "exit a program",
        2: "create a socket",
        3: "bind an address to a socket",
        4: "listen on a socket",
        5: "accept a connection",
        6: "respond to an http request",
        7: "respond to a GET request for the contents of a specified file",
        8: "accept multiple requests",
        9: "concurrently accept multiple requests",
        10: "respond to a POST request with a specified file and update its contents",
        11: "respond to multiple concurrent GET and POST requests",
    }.get(level, "")
    description = f"In this challenge you will {description}."

    print("===== Welcome to Building a Web Server! =====")
    print("In this series of challenges, you will be writing assembly to interact with your environment, and ultimately build a web server")
    print(description)
    print()

    if len(sys.argv) != 2:
        print(f"Usage: `{sys.argv[0]} <path_to_web_server>`", file=sys.stderr)
        print(f"""
$ cat server.s
.intel_syntax noprefix
.globl _start

.section .text

_start:
    mov rdi, 0
    mov rax, 60     # SYS_exit
    syscall

.section .data

$ as -o server.o server.s && ld -o server server.o

$ strace ./server
execve("./server", ["./server"], 0x7ffccb8c6480 /* 17 vars */) = 0
exit(0)                                 = ?
+++ exited with 0 +++

$ {sys.argv[0]} ./server
""", file=sys.stderr)
        exit(1)

    target_path = pathlib.Path(sys.argv[1])
    target_memfd = immutable_file_copy(target_path)
    results_dir = create_secret_dir()

    def target():
        target_memfd_path = pathlib.Path(f"/proc/self/fd/{target_memfd}")

        operation_names = {
            connect: "connect",
            validate_connect: "validated connect",
            validate_get: "HTTP GET request",
            validate_post: "HTTP POST request",
        }

        operations = {
            5: [connect],
            6: [validate_connect],
            7: [validate_get],
            8: [validate_get, connect],
            9: [validate_get, connect],
            10: [validate_post, connect],
            11: [*random.choices([validate_get, validate_post], k=32), connect],
        }.get(level, [])

        requirements = {}

        timeout = 10

        if level == 11:
            accept_kill = 100  # TODO: SIGCHLD
        elif level  >= 5:
            accept_kill = 2
        else:
            accept_kill = 1

        errors = []

        with strace([target_memfd_path],
                    "-e", "signal=SIGKILL,SIGALRM",
                    "-e", f"inject=accept:signal=SIGKILL:when={accept_kill}",
                    "-e", "inject=brk:signal=SIGKILL",
                    results_dir=results_dir,
                    timeout=timeout) as results:
            for operation in operations:
                print(f"Performing operation: {operation_names[operation]}")
                try:
                    error = operation()
                    if error:
                        errors.append(error)
                except Exception as e:
                    errors.append(f"Exception: {str(e)}")
        print()

        strace_errors = validate_strace(level, results, requirements)
        errors.extend(strace_errors)

        print("===== Result =====")
        if not errors:
            print("[✓] Success")
        else:
            print("[x] Fail")
            for error in errors:
                print(f"[x] {error}")

        return not errors

    success = run_sandbox(target)
    if success:
        print()
        print(open("/flag", "r").read())


challenge()
