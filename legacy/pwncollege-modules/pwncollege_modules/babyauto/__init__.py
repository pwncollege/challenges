import pwnshop
import string
import pwn
import os

PWNSHOP_AUTOREGISTER = False

from pwnshop import Challenge
from ..babyrev import BabyKeyBase, BabyVMKeygenBase, assembler


class BabyAutoTest(Challenge):
    template_path = "babyauto/verifier.c"
    crashes_needed = 1
    programs_to_crash = ["/usr/bin/setsid"]
    program_args = ["-w", "kill", "-11", "0"]

    def verify(self, **kwargs):
        """
        TBD
        """
        with self.run_challenge(**kwargs) as p:
            p.sendline("/usr/bin/setsid")
            p.sendline("/etc/passwd")
            o = p.readall()
            print(o)
            assert self.flag in o


class BabyAutoCrasher1(Challenge):
    template_path = "babyauto/babycrash.c"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.solution_string = "".join(
            self.random.choice(string.ascii_letters) for _ in range(16)
        )

    def verify(self, **kwargs):
        """
        TBD
        """
        with self.run_challenge(**kwargs) as p:
            p.sendline("aaaabbbb")
            p.wait()
            assert p.poll() == 0
        with self.run_challenge(**kwargs) as p:
            p.sendline(self.solution_string)
            p.wait()
            assert p.poll() == -11


class BabyAutoCrasher2(Challenge):
    template_path = "babyauto/babycrash.c"
    solution_type = "unsigned long long"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.solution_num = self.random.randrange(0, 2 ** 64)

    def verify(self, **kwargs):
        """
        TBD
        """
        with self.run_challenge(**kwargs) as p:
            p.sendline(str(self.solution_num + 1))
            p.wait()
            assert p.poll() == 0
        with self.run_challenge(**kwargs) as p:
            p.sendline(str(self.solution_num))
            p.wait()
            assert p.poll() == -11


class BabyAutoCrasher3(Challenge):
    template_path = "babyauto/babycrash.c"
    solution_type = "unsigned long long"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.solution_num = self.random.randrange(0, 2 ** 64)
        self.solution_offsets = [
            self.random.randrange(0, 2 ** 64)
            for _ in range(self.random.randrange(2, 16))
        ]
        self.to_send = self.solution_num - (sum(self.solution_offsets) % (2 ** 64))

    def verify(self, **kwargs):
        """
        TBD
        """
        with self.run_challenge(**kwargs) as p:
            p.sendline(str(self.to_send + 1))
            p.wait()
            assert p.poll() == 0
        with self.run_challenge(**kwargs) as p:
            p.sendline(str(self.to_send))
            p.wait()
            assert p.poll() == -11


class BabyAutoCrasher7(BabyKeyBase):
    crash_correct = True
    difficulty = 50
    input_method = "fd"
    input_fd = 0
    input_size = 100
    comparators = ["memcmp"]
    no_sort = True

    def verify(self, **kwargs):
        """
        TBD
        """
        with super(BabyKeyBase, self).verify(**kwargs) as process:
            import angr

            project = angr.Project(process.executable, auto_load_libs=False)
            initial_state = project.factory.full_init_state(
                add_options=angr.options.unicorn
            )
            simgr = project.factory.simgr(initial_state)
            simgr.explore(find=lambda s: b"Success. Crashing!" in s.posix.dumps(1))
            assert hasattr(simgr, "found")
            print(simgr.found[0].posix.dumps(0))


class BabyAutoCrasher8(BabyVMKeygenBase):
    crash_correct = True
    difficulty = 2

    def gen_asm(self):
        return (
            assembler.generalized(
                self.padding + self.input_solution,
                self.key_location,
                padding_size=self.padding_size,
                r=self.random,
            ),
            b"\0" * 256,
        )

    def verify(self, **kwargs):
        """
        TBD
        """
        with super(BabyVMKeygenBase, self).verify(**kwargs) as process:
            import angr

            project = angr.Project(process.executable, auto_load_libs=False)
            initial_state = project.factory.full_init_state(
                add_options=angr.options.unicorn
            )
            simgr = project.factory.simgr(initial_state)
            simgr.explore(find=lambda s: b"Success. Crashing!" in s.posix.dumps(1))
            assert hasattr(simgr, "found")
            print(simgr.found[0].posix.dumps(0))


class BabyAutoCrasherBase(Challenge):
    template_path = "babyauto/verifier.c"

    def init_target(self, *args, **kwargs):
        super(self.__class__, self).__init__(*args, **kwargs)

    @staticmethod
    def make_answer(crasher):
        e = pwn.ELF(crasher)
        movs = [
            int(line.split()[-1], 0)
            for line in e.functions["main"].disasm().splitlines()
            if "movabs" in line
        ]
        if len(movs) == 0:
            answer = e.section(".rodata")[4:].split(b"\0")[0].decode("latin1")
        elif len(movs) == 1:
            answer = str(movs[0])
        else:
            answer = str((movs[-1] - sum(movs[:-1])) % 2 ** 64)
        with open("/tmp/answer", "w") as o:
            o.write(str(answer))

    def verify(self, **kwargs):
        """
        TBD
        """
        with self.run_challenge(**kwargs) as process:
            for i in range(self.crashes_needed):
                process.readuntil("CURRENT")
                process.readuntil("NOT CRASHED: ")
                target = process.readline().strip()
                self.make_answer(target)
                process.sendline(target)
                process.sendline("/tmp/answer")
            o = process.readall()
            assert self.flag in o


class BabyAutoLevel1(BabyAutoCrasherBase):
    ""
    crashes_needed = 42
    suggested_method = "strings or pwntools"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.programs_to_crash = [
            f"/opt/babyauto-crackmes/level1/crash1-{i}"
            for i in self.random.sample(range(1000), 50)
        ]


class BabyAutoLevel2(BabyAutoCrasherBase):
    ""
    crashes_needed = 42
    suggested_method = "objdump/pwntools/grep/sed"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.programs_to_crash = [
            f"/opt/babyauto-crackmes/level2/crash2-{i}"
            for i in self.random.sample(range(1000), 50)
        ]


class BabyAutoLevel3(BabyAutoCrasherBase):
    ""
    crashes_needed = 42
    suggested_method = "objdump/pwntools/grep/sed"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.programs_to_crash = [
            f"/opt/babyauto-crackmes/level3/crash3-{i}"
            for i in self.random.sample(range(1000), 50)
        ]


class BabyAutoLevel4(BabyAutoCrasherBase):
    ""
    crashes_needed = 1337
    suggested_method = "strings/objdump/pwntools/grep/sed"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.programs_to_crash = [
            f"/opt/babyauto-crackmes/level4/crash4-{i}"
            for i in self.random.sample(range(3000), self.crashes_needed)
        ]


class BabyAutoLevel5(Challenge):
    ""
    template_path = "babyauto/verifier.c"
    suggested_method = "fuzzing"
    crashes_needed = 1
    programs_to_crash = ["/opt/all-binutils/inst/2.11/readelf"]
    program_args = ["-a", "INPUT_FILE"]
    input_arg_index = 2

    def verify(self, **kwargs):
        """
        TBD
        """
        with self.run_challenge(**kwargs) as p:
            p.sendline("/opt/all-binutils/inst/2.11/readelf")
            p.sendline(
                os.path.join(os.path.dirname(__file__), "readelf_crashes", "2.11")
            )
            o = p.readall()
            print(o)
            assert self.flag in o


class BabyAutoLevel6(Challenge):
    ""
    template_path = "babyauto/verifier.c"
    suggested_method = "fuzzing"
    crashes_needed = 60
    versions = [
        "2.11",
        "2.11.2",
        "2.11.94",
        "2.12",
        "2.12.1",
        "2.12.90",
        "2.12.91",
        "2.13",
        "2.13.1",
        "2.13.2",
        "2.13.91",
        "2.13.92",
        "2.14",
        "2.14.91",
        "2.14.92",
        "2.15",
        "2.15.96",
        "2.15.97",
        "2.16",
        "2.16.1",
        "2.16.92",
        "2.16.93",
        "2.16.94",
        "2.17",
        "2.17.50",
        "2.17.90",
        "2.18",
        "2.18.50",
        "2.18.90",
        "2.18.91",
        "2.18.92",
        "2.18.93",
        "2.19",
        "2.19.1",
        "2.19.50",
        "2.19.51",
        "2.19.90",
        "2.19.91",
        "2.19.92",
        "2.20",
        "2.20.1",
        "2.20.51",
        "2.20.90",
        "2.21",
        "2.21.1",
        "2.21.51",
        "2.21.52",
        "2.21.53",
        "2.21.90",
        "2.22",
        "2.22.51",
        "2.22.52",
        "2.22.90",
        "2.23",
        "2.23.0",
        "2.23.1",
        "2.23.2",
        "2.23.52",
        "2.23.90",
        "2.23.91",
        "2.24",
        "2.24.51",
        "2 24.90",
        "2.25",
        "2.25.1",
        "2.26",
        "2.26.1",
        "2.26.51",
        "2.27",
        "2.27.90",
        "2.28",
        "2.28.1",
        "2.28.90",
        "2.29",
        "2.29.1",
        "2.30",
        "2.31",
        "2.31.1",
        "2.32",
        "2 33.1",
        "2.34",
        "2.35",
        "2.35.1",
    ]
    crashed_versions = [
        "2.11",
        "2.11.2",
        "2.11.94",
        "2.12",
        "2.12.1",
        "2.12.90",
        "2.12.91",
        "2.13",
        "2.13.1",
        "2.13.2",
        "2.13.91",
        "2.13.92",
        "2.14",
        "2.14.91",
        "2.14.92",
        "2.15",
        "2.15.96",
        "2.15.97",
        "2.16",
        "2.16.1",
        "2.16.92",
        "2.16.93",
        "2.16.94",
        "2.17",
        "2.17.50",
        "2.17.90",
        "2.18",
        "2.18.50",
        "2.18.90",
        "2.18.91",
        "2.18.92",
        "2.18.93",
        "2.19",
        "2.19.1",
        "2.19.50",
        "2.19.51",
        "2.19.90",
        "2.19.91",
        "2.19.92",
        "2.20",
        "2.20.1",
        "2.20.51",
        "2.20.90",
        "2.21",
        "2.21.1",
        "2.21.51",
        "2.21.52",
        "2.21.53",
        "2.21.90",
        "2.22",
        "2.22.51",
        "2.22.52",
        "2.22.90",
        "2.23",
        "2.23.1",
        "2.23.2",
        "2.23.52",
        "2.23.90",
        "2.23.91",
        "2.24",
        "2.24.51",
        "2.24.90",
        "2.30",
    ]
    programs_to_crash = [
        f"/opt/all-binutils/inst/{version}/readelf" for version in versions
    ]
    solutions = [
        (
            f"/opt/all-binutils/inst/{version}/readelf",
            os.path.join(os.path.dirname(__file__), "readelf_crashes", version),
        )
        for version in crashed_versions
    ]
    program_args = ["-a", "INPUT_FILE"]
    input_arg_index = 2

    def verify(self, **kwargs):
        """
        TBD
        """
        with self.run_challenge(**kwargs) as p:
            for i in range(60):
                p.sendline("/opt/all-binutils/inst/2.11/readelf")
                p.sendline(
                    os.path.join(os.path.dirname(__file__), "readelf_crashes", "2.11")
                )
                o = p.clean()
                assert self.flag not in o

        with self.run_challenge(**kwargs) as p:
            for b, i in self.solutions[:59]:
                p.sendline(b)
                p.sendline(i)
                o = p.clean()
                assert self.flag not in o

        with self.run_challenge(**kwargs) as p:
            for b, i in self.solutions[:60]:
                p.sendline(b)
                p.sendline(i)
            o = p.readall()
            assert self.flag in o


class BabyAutoLevel7(Challenge):
    ""
    template_path = "babyauto/verifier.c"
    suggested_method = "angr"
    crashes_needed = 42
    program_args = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.programs_to_crash = [
            f"/opt/babyauto-crackmes/level7/crash7-{i}"
            for i in self.random.sample(range(10000), 50)
        ]

    def verify(self, **kwargs):
        """
        TBD
        """
        with self.run_challenge(**kwargs) as process:
            for i in range(self.crashes_needed):
                process.readuntil("CURRENT")
                process.readuntil("NOT CRASHED: ")
                target = process.readline().strip().decode()
                process.clean()

                import angr

                project = angr.Project(target, auto_load_libs=False)
                initial_state = project.factory.full_init_state(
                    add_options=angr.options.unicorn
                )
                simgr = project.factory.simgr(initial_state)
                simgr.explore(find=lambda s: b"Success. Crashing!" in s.posix.dumps(1))
                assert hasattr(simgr, "found")
                solution = simgr.found[0].posix.dumps(0)
                print(solution)

                with open("/tmp/answer", "wb") as f:
                    f.write(solution)

                process.sendline(target)
                process.sendline("/tmp/answer")
            o = process.readall()
            assert self.flag in o


class BabyAutoLevel8(Challenge):
    ""
    template_path = "babyauto/verifier.c"
    suggested_method = "angr"
    crashes_needed = 42
    program_args = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.programs_to_crash = [
            f"/opt/babyauto-crackmes/level8/crash8-{i}"
            for i in self.random.sample(range(10000), 50)
        ]

    def verify(self, **kwargs):
        """
        TBD
        """
        with self.run_challenge(**kwargs) as process:
            for i in range(self.crashes_needed):
                process.readuntil("CURRENT")
                process.readuntil("NOT CRASHED: ")
                target = process.readline().strip().decode()
                process.clean()

                import angr

                project = angr.Project(target, auto_load_libs=False)
                initial_state = project.factory.full_init_state(
                    add_options=angr.options.unicorn
                )
                simgr = project.factory.simgr(initial_state)
                simgr.explore(find=lambda s: b"Success. Crashing!" in s.posix.dumps(1))
                assert hasattr(simgr, "found")
                solution = simgr.found[0].posix.dumps(0)
                print(solution)

                with open("/tmp/answer", "wb") as f:
                    f.write(solution)

                process.sendline(target)
                process.sendline("/tmp/answer")
            o = process.readall()
            assert self.flag in o

LEVELS = [
    BabyAutoLevel1,
    BabyAutoLevel2,
    BabyAutoLevel3,
    BabyAutoLevel4,
    BabyAutoLevel5,
    BabyAutoLevel6,
    BabyAutoLevel7,
    BabyAutoLevel8,
]
NUM_TESTING=0
DOJO_MODULE="auto"
pwnshop.register_challenges(LEVELS)
