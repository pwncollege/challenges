import os
import sys
import tempfile
import textwrap
import subprocess

import pwnshop

PWNSHOP_AUTOREGISTER = False

class BabyKHeapBase(pwnshop.KernelChallenge):
    TEMPLATE_PATH = "babykheap/babykheap.c"

    # protections
    FREELIST_RANDOM = False
    FREELIST_HARDENED = False
    HARDENED_USERCOPY = False
    KASLR = False
    panic_on_oops = False

    # vulns
    oob = False
    uaf_rw = False
    uaf_w = False

    # misc
    func_ptr = True
    isolated_cache = False
    flag_obj = False
    kernel_dir = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if not self.FREELIST_RANDOM and not self.FREELIST_HARDENED and not self.HARDENED_USERCOPY:
            self.kernel_dir = "/home/kylebot/Desktop/challenges/pwn.college/2024_spring_qq_mod/kernel0/"
        elif self.FREELIST_RANDOM and not self.FREELIST_HARDENED and not self.HARDENED_USERCOPY:
            self.kernel_dir = "/home/kylebot/Desktop/challenges/pwn.college/2024_spring_qq_mod/kernel1/"
        elif self.FREELIST_RANDOM and self.FREELIST_HARDENED and not self.HARDENED_USERCOPY:
            self.kernel_dir = "/home/kylebot/Desktop/challenges/pwn.college/2024_spring_qq_mod/kernel2/"
        elif self.FREELIST_RANDOM and self.FREELIST_HARDENED and self.HARDENED_USERCOPY:
            self.kernel_dir = "/home/kylebot/Desktop/challenges/pwn.college/2024_spring_qq_mod/kernel3/"
        else:
            raise NotImplemented("blah")
        print(self.kernel_dir)

    def build_binary(self, source=None):
        assert self.kernel_dir is not None
        with tempfile.TemporaryDirectory() as workdir:
            with open(f"{workdir}/Makefile", "w") as f:
                f.write(
                    textwrap.dedent(
                        f"""
                        KERNEL_ROOT={self.kernel_dir}
                        obj-m += challenge.o

                        all:
                        \tmake -C $(KERNEL_ROOT) M={workdir} modules
                        clean:
                        \tmake -C $(KERNEL_ROOT) M={workdir} clean
                        """
                    )
                )

            cmd = ["make", "-C", workdir]

            if not source:
                source = self.generate_source()

            with open(f"{workdir}/challenge.c", "w") as f:
                f.write(source)

            subprocess.run(cmd, stdout=sys.stderr)

            with open(f"{workdir}/challenge.ko", "rb") as f:
                binary = f.read()

            return binary, None

class KBFSBase(pwnshop.KernelChallenge):
    TEMPLATE_PATH = "babykheap/kbfs/kbfs.c"

    faulty_permission = False
    kbfs_allow_root = False
    kbfs_df = False
    kbfs_give_flag = False
    kbfs_user_ns = False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.kernel_dir = "/home/kylebot/Desktop/challenges/pwn.college/2024_spring_qq_mod/kernel3/"
        self.kbfs_path = os.path.join(os.path.dirname(__file__), "kbfs")

    def build_binary(self, source=None):
        assert self.kernel_dir is not None
        with tempfile.TemporaryDirectory() as workdir:
            # build kernel module
            with open(f"{workdir}/Makefile", "w") as f:
                f.write(
                    textwrap.dedent(
                        f"""
                        KERNEL_ROOT={self.kernel_dir}
                        obj-m += challenge.o

                        all:
                        \tmake -C $(KERNEL_ROOT) M={workdir} modules
                        clean:
                        \tmake -C $(KERNEL_ROOT) M={workdir} clean
                        """
                    )
                )

            cmd = ["make", "-C", workdir]

            if not source:
                source = self.generate_source()

            with open(f"{workdir}/challenge.c", "w") as f:
                f.write(source)

            ret = subprocess.run(["cp", "-r", os.path.join(self.kbfs_path, "libkbfs"), f"{workdir}/libkbfs"])
            assert ret.returncode == 0
            ret = subprocess.run(cmd, stdout=sys.stderr)
            assert ret.returncode == 0

            # package the guest file system
            cpio_path = os.path.join(self.kbfs_path, "base_rootfs.cpio")
            ret = subprocess.run(["mkdir", f"{workdir}/rootfs"])
            assert ret.returncode == 0
            ret = subprocess.run(f"cpio -idvm < {cpio_path}", cwd=f"{workdir}/rootfs/", shell=True)
            assert ret.returncode == 0
            ret = subprocess.run(["cp", f"{workdir}/challenge.ko", f"{workdir}/rootfs/challenge.ko"])
            assert ret.returncode == 0
            if self.kbfs_give_flag:
                ret = subprocess.run(["cp", os.path.join(self.kbfs_path, "mount_kbfs_print_flag"), f"{workdir}/rootfs/mount_kbfs"])
                assert ret.returncode == 0
            else:
                ret = subprocess.run(["cp", os.path.join(self.kbfs_path, "mount_kbfs"), f"{workdir}/rootfs/mount_kbfs"])
                assert ret.returncode == 0
            if not self.faulty_permission:
                ret = subprocess.run(["sudo", "chown", "-R", "root:root", f"{workdir}/rootfs/"])
                assert ret.returncode == 0
            if not self.kbfs_user_ns:
                ret = subprocess.run(["sudo", "chmod", "4755", f"{workdir}/rootfs/mount_kbfs"])
                assert ret.returncode == 0
            ret = subprocess.run(f"find . | cpio -o --format=newc > ../rootfs.cpio", cwd=f"{workdir}/rootfs/", shell=True)
            assert ret.returncode == 0

            ret = subprocess.run(["sudo", "rm", "-rf", f"{workdir}/rootfs/"])
            assert ret.returncode == 0

            # package the challenge
            ret = subprocess.run(["mkdir", f"{workdir}/chall"])
            ret = subprocess.run(["cp", os.path.join(self.kbfs_path, "start_qemu.sh"), f"{workdir}/chall/start_qemu.sh"])
            assert ret.returncode == 0
            ret = subprocess.run(["cp", f"{workdir}/rootfs.cpio", f"{workdir}/chall/rootfs.cpio"])
            assert ret.returncode == 0
            ret = subprocess.run(["cp", os.path.join(self.kernel_dir, "arch/x86/boot/bzImage"), f"{workdir}/chall/bzImage"])
            assert ret.returncode == 0
            ret = subprocess.run(["tar", "czf", "chall.tar.gz", "chall"], cwd=f"{workdir}")
            assert ret.returncode == 0

            with open(f"{workdir}/chall.tar.gz", "rb") as f:
                binary = f.read()

            return binary, None

class BabyKHeapLevel1(BabyKHeapBase):
    """
    getting started with linux kernel stuff
    """

    oob = True
    flag_obj = True
    isolated_cache = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

class BabyKHeapLevel2(BabyKHeapBase):
    """
    learn how freelist randomization works
    """

    FREELIST_RANDOM = True
    oob = True
    isolated_cache = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

class BabyKHeapLevel3(BabyKHeapBase):
    """
    learn how KASLR works
    """

    FREELIST_RANDOM = True
    KASLR = True
    uaf_rw = True
    isolated_cache = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

class BabyKHeapLevel4(BabyKHeapBase):
    """
    learn how KASLR works
    """

    FREELIST_RANDOM = True
    KASLR = True
    uaf_rw = True
    func_ptr = False
    isolated_cache = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

class BabyKHeapLevel5(BabyKHeapBase):
    """
    learn how to bypass FREELIST_HARDENED
    """

    FREELIST_RANDOM = True
    FREELIST_HARDENED = True
    KASLR = True
    uaf_rw = True
    func_ptr = False
    isolated_cache = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

class BabyKHeapLevel6(BabyKHeapBase):
    """
    learn how to use objects in kmalloc for exploitation, e.g. use msg_msg for OOB read
    """

    FREELIST_RANDOM = True
    FREELIST_HARDENED = True
    KASLR = True
    uaf_w = True
    func_ptr = False
    isolated_cache = False
    flag_obj = True
    panic_on_oops = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

class BabyKHeapLevel7(BabyKHeapBase):
    """
    learn how to use objects in kmalloc for exploitation, e.g. msg_msg for OOB read and arbitrary free etc
    """

    FREELIST_RANDOM = True
    FREELIST_HARDENED = True
    KASLR = True
    uaf_w = True
    func_ptr = False
    isolated_cache = False
    flag_obj = False
    panic_on_oops = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

class BabyKHeapLevel8(BabyKHeapBase):
    """
    learn how to use objects in kmalloc for exploitation, e.g. msg_msg
    """

    FREELIST_RANDOM = True
    FREELIST_HARDENED = True
    HARDENED_USERCOPY = True
    KASLR = True
    uaf_w = True
    func_ptr = False
    isolated_cache = False
    flag_obj = False
    panic_on_oops = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

class BabyKHeapLevel9(KBFSBase):
    """
    learn how to interact with rootfs and how to cheese the challenges
    """
    faulty_permission = True
    kbfs_allow_root = False
    kbfs_df = False
    kbfs_give_flag = False
    kbfs_user_ns = False
    kbfs_faulty_mmap = False
    panic_on_oops = True

class BabyKHeapLevel10(KBFSBase):
    """
    learn the basics of VFS by correct loading a KBFS image
    """
    faulty_permission = False
    kbfs_allow_root = False
    kbfs_df = False
    kbfs_give_flag = True
    kbfs_user_ns = False
    kbfs_faulty_mmap = False
    panic_on_oops = True

class BabyKHeapLevel11(KBFSBase):
    """
    inject a SUID binary and execute it
    """
    faulty_permission = False
    kbfs_allow_root = True
    kbfs_df = False
    kbfs_give_flag = False
    kbfs_user_ns = False
    kbfs_faulty_mmap = False
    panic_on_oops = True

class BabyKHeapLevel12(KBFSBase):
    """
    exploit the double free in user namespace
    """
    faulty_permission = False
    kbfs_allow_root = False
    kbfs_df = True
    kbfs_give_flag = False
    kbfs_user_ns = True
    kbfs_faulty_mmap = False
    panic_on_oops = True

class BabyKHeapLevel13(KBFSBase):
    """
    exploit the mmap handler in user namespace (OOB)
    """
    faulty_permission = False
    kbfs_allow_root = False
    kbfs_df = False
    kbfs_give_flag = False
    kbfs_user_ns = True
    kbfs_faulty_mmap = True
    panic_on_oops = True


LEVELS = [ 
    BabyKHeapLevel1,
    BabyKHeapLevel2,
    BabyKHeapLevel3,
    BabyKHeapLevel4,
    BabyKHeapLevel5,
    BabyKHeapLevel6,
    BabyKHeapLevel7,
    BabyKHeapLevel8,
    BabyKHeapLevel9,
    BabyKHeapLevel10,
    BabyKHeapLevel11,
    BabyKHeapLevel12,
    BabyKHeapLevel13,
]
NUM_TESTING=1
DOJO_MODULE="kheap"
pwnshop.register_challenges(LEVELS)
