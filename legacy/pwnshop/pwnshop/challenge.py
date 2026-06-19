import os
import re
import sys
import time
import string
import random
import shutil
import socket
import inspect
import logging
import tempfile
import textwrap
import contextlib
import subprocess

import black
import pyastyle
import pwnlib.tubes
import pwnlib.context
from jinja2 import Environment, PackageLoader, ChoiceLoader, contextfilter

from .register import register_challenge
from .util import retry
from .environments import BareEnvironment, DockerEnvironment

pwnlib.context.context.arch = "x86_64"
pwnlib.context.context.encoding = "latin"

_LOG = logging.getLogger(__name__)

def hex_str_repr(s):
    hex_s = s.encode("latin").hex()
    return "".join("\\x" + hex_s[i : i + 2] for i in range(0, len(hex_s), 2))


def layout_text(text):
    lines = textwrap.wrap(textwrap.dedent(text), width=120)
    if lines:
        lines[-1] += "\\n"
    else:
        lines = [""]
    return "\n".join(f'puts("{line}");' for line in lines)

class BuildError(Exception):
    pass

@contextfilter
def layout_text_walkthrough(context, text):
    if not context.get("walkthrough"):
        return "\n"
    return layout_text(text)

class BaseChallenge:
    IMAGE = None
    APT_DEPENDENCIES = []

    def __init__(
        self, seed=None,
        env=None, work_dir=None, walkthrough=False, basename=None,
        **kwargs #pylint:disable=unused-argument
    ):

        if env:
            self.env = env
        elif self.IMAGE:
            self.env = DockerEnvironment(self.IMAGE)
        else:
            self.env = BareEnvironment()
        self.work_dir = work_dir or self.env.work_dir or tempfile.mkdtemp(prefix='pwnshop-')

        if os.path.exists(self.work_dir):
            self._owns_workdir = False
        else:
            self._owns_workdir = True
            os.makedirs(self.work_dir)

        self.seed = seed or random.randrange(13371337)
        self.random = random.Random(seed)
        self.walkthrough = walkthrough

        self.basename = basename or self.default_basename()

    @classmethod
    def default_basename(cls):
        return cls.__name__.lower().replace("_", "-")

    def __init_subclass__(cls, register=True):
        cls_module = inspect.getmodule(cls)
        if register and getattr(cls_module, "PWNSHOP_AUTOREGISTER", True):
            register_challenge(cls)

    @classmethod
    def duplicate_class(cls, name=None, attributes=None, register=False):
        return type(
            name or cls.__name__, (cls,),
            dict(attributes) or {},
            register=register
        )

    @property
    def flag(self):
        with open("/flag", "rb") as f:
            return f.read()

    def random_word(
        self, length,
        start_vocabulary=string.ascii_lowercase,
        vocabulary=string.ascii_lowercase
    ):
        return (
            self.random.choice(start_vocabulary) +
            "".join(self.random.choice(vocabulary) for _ in range(length-1))
        )

    def cleanup(self):
        if self._owns_workdir:
            shutil.rmtree(self.work_dir)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, value, tb):
        self.cleanup()

    def render(self):
        pass

    def build(self):
        self.env.install(self.APT_DEPENDENCIES)

    def flaky_verify(self, num_attempts=4, timeout=300, **kwargs):
        retry(num_attempts, timeout=timeout)(self.verify)(**kwargs)

    def verify(self, **kwargs):
        raise NotImplementedError()

    @contextlib.contextmanager
    def run_challenge(self, *, close_stdin=False, flag_symlink=None, **kwargs):
        if flag_symlink:
            self.run_sh(f"ln -s /flag {flag_symlink}")

        self.env.write_file("/flag", self.flag, "root:root", user=0)

        # stdout_fds = kwargs.pop("stdout_fds", ())
        # def preexec_fn():
        #   for i in stdout_fds:
        #       os.dup2(1, i)

        process = self.env.process(user=0, **kwargs)

        if close_stdin:
            process.stdin.close()

        try:
            yield process
        finally:
            process.kill()
            self.env.system(
                f'chown {os.getuid()}:{os.getgid()} {self.work_dir}/core',
                user="root"
            )

    def run_sh(self, command, user="hacker", **kwargs):
        return self.env.process(
            argv=command,
            shell=type(command) in (str, bytes),
            user=user,
            **kwargs
        )

    @contextlib.contextmanager
    def proxy_local_connection(self, port, protocol="tcp"):
        with self.proxy_local_port(port, protocol=protocol) as pp:
            with pwnlib.tubes.remote.remote(self.hostname, pp) as rr:
                yield rr

    @contextlib.contextmanager
    def proxy_local_port(self, port, proxy_port=None, protocol="tcp"):
        if not proxy_port:
            with socket.socket() as s:
                s.bind(('', 0))
                proxy_port = s.getsockname()[1]
        with self.run_sh(f"socat tcp-listen:{proxy_port},fork,reuseaddr {protocol}-connect:localhost:{port}"):
            time.sleep(0.1)
            yield proxy_port

    @property
    def hostname(self):
        return self.env.hostname

    def deploy(self, dst_dir, *, bin=True, src=True, libs=True): #pylint:disable=redefined-builtin
        pass

class TemplatedChallenge(BaseChallenge, register=False):
    context = { }

    def __init__(self, style=True, **kwargs):
        super().__init__(**kwargs)
        self.source = None

        self.src_path = f"{self.work_dir}/{self.basename}"
        self._style = style

    @property
    def TEMPLATE_PATH(self):
        raise NotImplementedError()

    def style(self, src):
        return src

    def make_jinja_env(self):
        loader_list = [
            PackageLoader(__name__, ""),
            PackageLoader(__name__, "templates"),
        ]
        for cls in self.__class__.__mro__:
            if not issubclass(cls, BaseChallenge):
                continue
            loader_list.append(PackageLoader(inspect.getmodule(cls).__name__, ""))
            loader_list.append(PackageLoader(inspect.getmodule(cls).__name__, ".."))

        env = Environment(loader=ChoiceLoader(loader_list), trim_blocks=True)
        env.filters["layout_text"] = layout_text
        env.filters["layout_text_walkthrough"] = layout_text_walkthrough
        return env

    def render(self):
        env = self.make_jinja_env()
        template = env.get_template(self.TEMPLATE_PATH)
        result = template.render(
            challenge=self,
            walkthrough=self.walkthrough,
            **self.context,
            **self.local_context,
        )
        if self._style:
            result = self.style(result)

        self.source = result
        with open(self.src_path, "w") as o:
            o.write(self.source)

        return result

    @property
    def local_context(self):
        return {
            e: getattr(self, e)
            for e in dir(self)
            if not e.startswith("_") and e == e.upper()
        }

    def deploy(self, dst_dir, *, src=False, **kwargs):
        super().deploy(dst_dir, **kwargs)
        if src:
            shutil.copy2(self.src_path, os.path.join(dst_dir, os.path.basename(self.src_path)))


class PythonChallenge(TemplatedChallenge, register=False):
    @property
    def bin_path(self):
        return self.src_path

    def build(self):
        super().build()

        if not self.source:
            self.render()
        os.chmod(self.src_path, 0o4755)

    def style(self, src):
        try:
            return black.format_file_contents(
                src, fast=False, mode=black.FileMode(line_length=120)
            )
        except black.parsing.InvalidInput:
            print(src, file=sys.stderr)
            raise
        except black.report.NothingChanged:
            return src

    @contextlib.contextmanager
    def run_challenge(self, argv=(), **kwargs):
        kwargs.pop("strace", None)
        if not self.source:
            self.render()

        with super().run_challenge(argv=[ "python3", self.src_path ] + list(argv), **kwargs) as y:
            yield y

    def deploy(self, dst_dir, *, src=False, **kwargs): #pylint:disable=useless-parent-delegation
        super().deploy(dst_dir, src=src or bin, **kwargs)

class Challenge(TemplatedChallenge, register=False):
    COMPILER = "gcc"
    PIE = None
    RELRO = "full"
    OPTIMIZATION_FLAG = "-O0"
    CANARY = None
    FRAME_POINTER = None
    STATIC = False
    EXEC_STACK = False
    STRIP = False
    DEBUG_SYMBOLS = False

    LINK_LIBRARIES = []
    PIN_LIBRARIES = False
    DEPLOYMENT_LIB_PATH = "/challenge/lib"

    vbuf_in_main = True
    vbuf_in_constructor = False
    print_greeting = True
    constant_goodbye = True
    win_message = "You win! Here is your flag:"
    static_win_function_variables = True

    context = {
        "min": min,
        "max": max,
        "hex": hex,
        "hex_str_repr": hex_str_repr,
        "layout_text": layout_text,
        "layout_text_walkthrough": layout_text,
    }

    def __init__(self, src_extension=".c", bin_extension="", **kwargs):
        super().__init__(**kwargs)

        self.binary = None
        self.libraries = None

        self.src_path = f"{self.work_dir}/{self.basename}{src_extension}"
        self.bin_path = f"{self.work_dir}/{self.basename}{bin_extension}"
        self.lib_path = f"{self.work_dir}/lib"

    def style(self, src):
        src = pyastyle.format(src, "--style=allman")
        src = re.sub("\n{2,}", "\n\n", src)
        return src

    def build_compiler_cmd(self):
        cmd = [self.COMPILER]

        if self.RELRO == "full":
            cmd.append("-Wl,-z,relro,-z,now")
        elif self.RELRO  == "partial":
            cmd.append("-Wl,-z,relro,-z,lazy")
        elif self.RELRO == "none":
            cmd.append("-Wl,-z,norelro")

        if self.PIE is True:
            cmd.append("-pie")
        elif self.PIE is False:
            cmd.append("-no-pie")

        if self.CANARY is True:
            cmd.append("-fstack-protector")
        elif self.CANARY is False:
            cmd.append("-fno-stack-protector")

        if self.FRAME_POINTER is True:
            cmd.append("-fno-omit-frame-pointer")
        elif self.FRAME_POINTER is False:
            cmd.append("-fomit-frame-pointer")

        if self.STATIC and self.PIE:
            cmd.append("-static-pie")
        elif self.STATIC:
            cmd.append("-static")

        if self.EXEC_STACK:
            cmd.append("-z")
            cmd.append("execstack")

        if self.DEBUG_SYMBOLS:
            cmd.append("-g")

        if self.STRIP:
            cmd.append("-s")

        if "-" not in self.COMPILER or "x86" in self.COMPILER:
            cmd.append("-masm=intel")
        if self.OPTIMIZATION_FLAG:
            cmd.append(self.OPTIMIZATION_FLAG)

        cmd.append(f"-ffile-prefix-map={self.work_dir}=/challenge")

        cmd.append("-w")

        cmd.append(self.src_path)

        for lib in self.LINK_LIBRARIES:
            cmd.append("-l" + lib)

        cmd.append("-o")
        cmd.append(self.bin_path)

        return cmd

    def build(self):
        super().build()

        self.env.install([ "gcc", "patchelf" ])

        if not self.source:
            self.render()
        cmd = self.build_compiler_cmd()

        build_process = self.env.process(cmd)
        build_process.wait()
        if build_process.poll() != 0:
            print(f"BUILD ERROR ({self.env=}):")
            error = build_process.readall().decode('latin1')
            print(error)
            raise BuildError(error)

        self.libraries = self.pin_libraries() if self.PIN_LIBRARIES else []
        self.binary = self.env.read_file(self.bin_path)

        return self.binary, self.libraries, None

    @contextlib.contextmanager
    def run_challenge(
        self,
        *,
        cmd_args=None,
        argv=None,
        strace=False,
        **kwargs,
    ):
        if argv is None:
            argv = [self.bin_path]
            if cmd_args:
                argv += cmd_args
            if strace:
                argv = ["strace"] + argv
                kwargs["stderr"] = 2
        else:
            assert not strace

        if not self.binary:
            self.build()

        with super().run_challenge(argv=argv, **kwargs) as y:
            yield y

    def pin_libraries(self):
        ldd = self.env.process("ldd " + self.bin_path, shell=True)
        ldd.wait()
        assert ldd.poll() == 0
        lib_paths = filter(lambda x: '/' in x, ldd.read().decode().split())

        libs = [ ]
        os.makedirs(f"{self.lib_path}", exist_ok=True)
        for p in lib_paths:
            lib_name = os.path.basename(p)
            self.env.system(f'cp {p} {self.lib_path}/{lib_name}')

            self.env.system(f'chmod 0766 {self.lib_path}/{lib_name}')
            self.env.system(f'chown {os.getuid()}:{os.getgid()} {self.lib_path}/{lib_name}')

            with open(f'{self.lib_path}/{lib_name}', 'rb') as f:
                libs.append((lib_name, f.read()))
            if self.DEPLOYMENT_LIB_PATH and "ld-linux" in lib_name:
                self.env.finished_process(
                    f'patchelf --set-interpreter {self.DEPLOYMENT_LIB_PATH}/{lib_name} ' + self.bin_path,
                    shell=True,
                    check=True
                )
            elif self.DEPLOYMENT_LIB_PATH:
                self.env.finished_process(
                    f'patchelf --replace-needed {lib_name} {self.DEPLOYMENT_LIB_PATH}/{lib_name} ' + self.bin_path,
                    shell=True,
                    check=True
                )

        # the interpreter is set to */challenge*/lib/ld-blah
        if os.path.exists(self.DEPLOYMENT_LIB_PATH):
            os.unlink(self.DEPLOYMENT_LIB_PATH)
        if not os.path.exists(os.path.dirname(self.DEPLOYMENT_LIB_PATH)):
            os.makedirs(os.path.dirname(self.DEPLOYMENT_LIB_PATH))
        if os.path.islink(self.DEPLOYMENT_LIB_PATH):
            os.unlink(self.DEPLOYMENT_LIB_PATH)
        os.symlink(self.work_dir+"/lib", self.DEPLOYMENT_LIB_PATH)

        return libs

    def deploy(self, dst_dir, *, bin=True, libs=True, **kwargs): #pylint:disable=redefined-builtin
        super().deploy(dst_dir, **kwargs)
        if bin:
            shutil.copy2(self.bin_path, os.path.join(dst_dir, os.path.basename(self.bin_path)))

        if libs and os.path.exists(self.lib_path):
            shutil.copytree(self.lib_path, os.path.join(dst_dir, os.path.basename(self.lib_path)), dirs_exist_ok=True)



class WindowsChallenge(Challenge, register=False):
    COMPILER = "cl"
    CANARY = None
    FRAME_POINTER = True
    PDB = True
    CFG = True
    DYNAMIC_BASE = True
    ASLR_HIGH_ENTROPY = True
    MAKE_DLL = False

    def build_compiler_cmd(self):
        cmd = [self.COMPILER]

        if self.CANARY is True:
            cmd.append("/GS")
        else:
            cmd.append("/GS-")

        if self.FRAME_POINTER is False:
            cmd.append("/0y")

        if self.PDB:
            cmd.append("/Zi")

        if self.CFG:
            cmd.append("/guard:cf")
        else:
            cmd.append("/guard:cf-")

        if self.MAKE_DLL:
            cmd.append("/LD")

        return cmd
        # Linker options

        #pylint:disable=unreachable
        cmd.append('/LINK')
        if self.DYNAMIC_BASE is True:
            cmd.append('/DYNAMICBASE')
        else:
            cmd.append('/DYNAMICBASE:NO')

        if self.ASLR_HIGH_ENTROPY is True:
            cmd.append('/HIGHENTROPYVA')

        for lib in self.LINK_LIBRARIES:
            cmd.append(lib)

        return cmd

    def build(self, source=None):
        if not source:
            source = self.render()

        cmd = self.build_compiler_cmd()

        if not isinstance(self.env, DockerEnvironment):
            with tempfile.TemporaryDirectory(prefix='pwnshop-') as workdir:
                src_path = f"{workdir}/{self.__class__.__name__.lower()}.c"

                if self.MAKE_DLL:
                    bin_path = f"{workdir}/{self.__class__.__name__.lower()}.dll"
                else:
                    bin_path = f"{workdir}/{self.__class__.__name__.lower()}.exe"
                pdb_path = f"{workdir}/{self.__class__.__name__.lower()}.pdb"
                with open(src_path, 'w') as f:
                    f.write(source)

                cmd.append(src_path)
                subprocess.check_output(cmd, cwd=workdir)
                with open(bin_path, 'rb') as f:
                    binary = f.read()

                if self.PDB:
                    with open(pdb_path, 'rb') as f:
                        pdb = f.read()
                else:
                    pdb = None
                return binary, None, pdb

        else:
            raise NotImplementedError("Containerized Windows build not supported")

class KernelChallenge(Challenge, register=False):
    def __init__(self, bin_extension=".ko", **kwargs):
        super().__init__(bin_extension=bin_extension, **kwargs)

    def build(self):
        with tempfile.TemporaryDirectory() as workdir:
            with open(f"{workdir}/Makefile", "w") as f:
                f.write(
                    textwrap.dedent(
                        f"""
                        obj-m += challenge.o

                        all:
                        \tmake -C /opt/linux/linux-5.4 M={workdir} modules
                        clean:
                        \tmake -C /opt/linux/linux-5.4 M={workdir} clean
                        """
                    )
                )

            cmd = ["make", "-C", workdir]

            if not self.source:
                self.render()

            with open(f"{workdir}/challenge.c", "w") as f:
                f.write(self.source)

            subprocess.run(cmd, stdout=sys.stderr, check=True)
            shutil.copy2(f"{workdir}/challenge.ko", self.bin_path)
            return self.binary, None, None

    @contextlib.contextmanager
    def run_challenge( #pylint:disable=arguments-differ
        self,
        *,
        flag_symlink=None,
        **kwargs,
    ):
        if flag_symlink:
            os.symlink("/flag", f"{flag_symlink}")

        # ./run.sh ./generate.py -m BabyKernel -i1 -v -l1 -vvv
        subprocess.run(["passwd", "-d", "root"], check=True)
        subprocess.run(["vm", "restart"], check=True)
        subprocess.run(["ln", "-sf", self.bin_path, "/challenge/challenge.ko"], check=True)

        yield

    def run_sh(self, command, user=None, **kwargs): #pylint:disable=unused-argument
        return pwnlib.tubes.process.process(["vm", "exec", command], **kwargs)

    def run_c(self, src, *, user=None, flags=()):
        with open("/tmp/program.c", "w") as f:
            f.write(textwrap.dedent(src))
        subprocess.run(
            ["gcc", "-static", "/tmp/program.c", "-o", "/tmp/program"] + list(flags),
            check=True
        )
        command = "/tmp/program"
        if user:
            command = f"su {user} -c {command}"
        return self.run_sh(command)

    def symbol_address(self, symbol):
        data = self.run_sh(f"grep -P '^[0-9a-f]+\\ .\\ {symbol}(\\t|$)' /proc/kallsyms | grep -oP '^[0-9a-f]+'").readall().strip()
        assert len(data.split()) == 1
        return int(data, 16)


class ChallengeGroup(BaseChallenge, register=False):
    challenges = { }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        kwargs.pop("basename", None)
        kwargs.pop("work_dir", None)
        kwargs.pop("env", None)

        self.challenge_instances = {
            name: cls(
                env=self.env, work_dir=self.work_dir, basename=name, **kwargs
            ) for name,cls in self.challenges.items()
        }

        for n,c in self.challenge_instances.items():
            setattr(self, n, c)

    def render(self):
        return { n: c.render() for n,c in self.challenge_instances.items() }

    def build(self):
        return { n: c.build() for n,c in self.challenge_instances.items() }

    def run_challenge(self, **kwargs): #pylint:disable=arguments-differ
        pass

    def deploy(self, dst_dir, **kwargs):
        for c in self.challenge_instances.values():
            c.deploy(dst_dir, **kwargs)

    def verify(self, **kwargs):
        for c in self.challenge_instances.values():
            c.verify(**kwargs)
