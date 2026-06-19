import pwnshop
import signal
import os

PWNSHOP_AUTOREGISTER = False

from pwnshop import Challenge


class EmbryoGDBBase(Challenge):
    TEMPLATE_PATH = "embryogdb/embryogdb.c"

    win_function = True
    win_function_broken = False

    info_breakpoint = True
    challenge_iterations = 1


class EmbryoGDBLevel1(EmbryoGDBBase):
    lesson = "continue"
    challenge_iterations = 0


class EmbryoGDBLevel2(EmbryoGDBBase):
    lesson = "registers"
    use_register = True
    info_breakpoint = False
    prompt_breakpoint = True


class EmbryoGDBLevel3(EmbryoGDBBase):
    lesson = "memory"
    prompt_breakpoint = True


class EmbryoGDBLevel4(EmbryoGDBBase):
    lesson = "step"
    challenge_iterations = 4


class EmbryoGDBLevel5(EmbryoGDBBase):
    lesson = "scripting"
    challenge_iterations = 8


class EmbryoGDBLevel6(EmbryoGDBBase):
    lesson = "modifying"
    challenge_iterations = 64


class EmbryoGDBLevel7(EmbryoGDBBase):
    lesson = "call"
    win_function = True

class EmbryoGDBLevel8(EmbryoGDBBase):
    lesson = "call"
    win_function = True
    win_function_broken = True

LEVELS = [
    EmbryoGDBLevel1,
    EmbryoGDBLevel2,
    EmbryoGDBLevel3,
    EmbryoGDBLevel4,
    EmbryoGDBLevel5,
    EmbryoGDBLevel6,
    EmbryoGDBLevel7,
    EmbryoGDBLevel8,
]
NUM_TESTING=0
DOJO_MODULE="gdb"
pwnshop.register_challenges(LEVELS)
