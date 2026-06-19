import pwnshop
import pwn
import os
from subprocess import Popen

PWNSHOP_AUTOREGISTER = False

from pwnshop import WindowsChallenge


class BabyWinBase(WindowsChallenge):
    TEMPLATE_PATH = "babywin/babywin.c"
    COMPILER = "cl"

    EXEC_STACK = True
    CANARY = True
    DYNAMIC_BASE = True

    smoketest = False
    win_func = False
    windll = False
    leak_win = False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bof_buf_sz = self.random.randrange(0x80, 0x400, 0x8)

class BabyWinSmokeTest(BabyWinBase):
    '''
    Connect to challenge to obtain flag.
    '''
    smoketest = True
    win_func = True
    def verify(self, **kwargs):
        '''
        Connect to challenge from linux env
        '''
        return True

class BabyWinSimpleOverflowNoASLR(BabyWinBase):
    '''
    BOF to overwrite saved return address.
    DYNAMIC_BASE (ASLR) disabled
    '''
    CANARY = False
    DYNAMIC_BASE = False

    intro_text = "This Challenge is vulnerable to a buffer overflow!\\n"
    intro_text += "ASLR is disabled!\\n"
    intro_text += "Use this to call the win() function!\\n"

    win_func = True
    leak_win = True

    def verify(self, **kwargs):
        '''
        BOF -> write win address
        '''
        return True

class BabyWinSimpleOverflow(BabyWinBase):
    '''
    BOF to overwrite saved return address.
    DYNAMIC_BASE (ASLR) enabled
    '''
    CANARY = False

    intro_text = "This Challenge is vulnerable to a buffer overflow!\\n"
    intro_text += "ASLR is enabled!\\n"
    intro_text += "Use this to call the win() function!\\n"
      
    win_func = True
    leak_win = True

    def verify(self, **kwargs):
        return True

class BabyWinAslrWinInDll(BabyWinBase):
    '''
    Win Function is in win.dll
    '''
    CANARY = False

    intro_text = "This Challenge is vulnerable to a buffer overflow!\\n"
    intro_text += "ASLR is enabled!\\n"
    intro_text += "This challenge loads a DLL with a win() function!\\n"
      
    windll = True
    leak_win = True

    def verify(self, **kwargs):
        '''
        Repeated runs will show the randomized 
        addresses repeats.  
        '''
        return True

class BabyWinDllLib(BabyWinBase):
    '''
    Lib for Above chal
    '''
    TEMPLATE_PATH = "babywin/winlib.c"
    MAKE_DLL = True

class BabyWinSCCallWriteFile(BabyWinBase):
    '''
    Write Shellcode to call WriteFile
    '''
    TEMPLATE_PATH = "babywin/babywin.c"

    intro_text = "This Challenge will execute shellcode you provide\\n"
    
    shellcode_runner = True
    read_flag = True
    leak_flag_addr = True
    leak_WriteFile = True
    leak_stdout = True

class BabyWinSCCallWriteFileNoLeak(BabyWinBase):
    '''
    Write Shellcode to call WriteFile
    Challenge does not leak address of WriteFile
    '''
    TEMPLATE_PATH = "babywin/babywin.c"

    intro_text = "This Challenge will execute shellcode you provide\\n"

    shellcode_runner = True
    read_flag = True
    leak_flag_addr = True
    leak_stdout = True

class BabyWinSC(BabyWinBase):
    '''
    Write Shellcode to call Open, Read, Write
    No Leaks
    '''
    TEMPLATE_PATH = "babywin/babywin.c"

    intro_text = "This Challenge will execute shellcode you provide\\n"

    shellcode_runner = True

LEVELS = [
  BabyWinSmokeTest,
  BabyWinSimpleOverflowNoASLR,
  BabyWinSimpleOverflow,
  BabyWinAslrWinInDll,
  BabyWinSCCallWriteFile,
  BabyWinSCCallWriteFileNoLeak,
  BabyWinSC
]
pwnshop.register_challenges(LEVELS)

# DLL for WinInDll Level
pwnshop.register_challenge(BabyWinDllLib)
