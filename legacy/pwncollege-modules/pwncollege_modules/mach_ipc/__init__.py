import pwn
import pwnshop

PWNSHOP_AUTOREGISTER = False

from pwnshop import Challenge, retry

class MachIpcBase(Challenge):
    COMPILER = "clang"
    LINK_LIBRARIES = []
    MASM_FLAG = None
    RELRO = None # Hack to not have any -z flag

    TEMPLATE_PATH = "mach_ipc/mach_ipc.c"

    read_size = 0x1000
    free_gadgets = []
    free_gadgets_asm = []

    our_register_port_name_prefix = "college.pwn.mac-ports"
    challenge_register_port_name_prefix = "college.pwn.mac-ports.challenge"

    listen_for_message = False
    send_a_message = False
    require_complex_message = False
    required_inline_message_value = None
    call_win_on_message = False
    send_back_flag_on_message = False
    random_bin_padding = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.input_size = self.random.randrange(16, 128)
        if self.random_bin_padding:
            self.bin_padding = self.random.randrange(0x10, 0x1000)
        else:
            self.bin_padding = 0x42
        if self.free_gadgets:
            self.free_gadgets = self.free_gadgets.copy()
            self.random.shuffle(self.free_gadgets)

        self.our_register_port_name = f"{self.our_register_port_name_prefix}.{self.random.randint(0x10,0xFF):02x}"
        self.challenge_register_port_name = f"{self.challenge_register_port_name_prefix}.{self.random.randint(0x10,0xFF):02x}"


class MachIpcSendAnyToPort(MachIpcBase):
    ""
    listen_for_message = True
    win_function = True
    call_win_on_message = True
    description = "For this level, just send any message to this port."

class MachIpcSendSpecificValue(MachIpcBase):
    ""
    listen_for_message = True
    win_function = True
    call_win_on_message = True
    description = "Now, send a specific inline message to this port."

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.required_inline_message_value = self.random.randrange(0x100000, 0xFFFFFFFFFFFFFFFF)

class MachIpcSendAnyOolToPort(MachIpcBase):
    ""
    listen_for_message = True
    win_function = True
    call_win_on_message = True
    require_complex_message = True
    require_descriptor_type = "MACH_MSG_OOL_DESCRIPTOR"
    description = "Now, send any OOL message to this port."

class MachIpcSendSpecificValueOolToPort(MachIpcBase):
    ""
    listen_for_message = True
    win_function = True
    call_win_on_message = True
    require_complex_message = True
    require_descriptor_type = "MACH_MSG_OOL_DESCRIPTOR"
    description = "Now, send an OOL message with a specific value to this port."

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.required_ool_message_value = self.random.randrange(0x100000, 0xFFFFFFFFFFFFFFFF)

class MachIpcReceiveInlineFlagToPort(MachIpcBase):
    ""
    send_a_message = True
    get_flag_function = True
    send_flag_inline_message = True
    description = "Let's focus on receiving messages, listen for an inline message with the flag."

class MachIpcReceiveOolFlagToPort(MachIpcBase):
    ""
    send_a_message = True
    get_flag_function = True
    send_flag_ool_message = True
    description = "Now, listen for an ool message for the flag."

class MachIpcSendFlagBackInlineToPort(MachIpcBase):
    ""
    listen_for_message = True
    get_flag_function = True
    send_flag_inline_message = True
    description = "Send a message and we'll send back the inline flag."

class MachIpcSendFlagBackOolToPort(MachIpcBase):
    ""
    listen_for_message = True
    get_flag_function = True
    send_flag_ool_message = True
    description = "Send a message and we'll send back the OOL flag."

class MachIpcOverflowViaInlinePayload(MachIpcBase):
    ""
    CANARY = False
    leak_challenge = True
    listen_for_message = True
    stack_overflow_on_message = True
    description = "Ok enough messing around, let's get to exploiting."

    free_gadgets_asm = [
        "ldp x0, x1, [sp], #0x10; br x1",
        "ldp x1, x2, [sp], #0x10; br x2",
        "ldp x2, x3, [sp], #0x10; br x3",
        "ldp x3, x4, [sp], #0x10; br x4",
        "ldp x4, x5, [sp], #0x10; br x5",
        "ldp x5, x6, [sp], #0x10; br x6",
        "ldp x6, x7, [sp], #0x10; br x7",
        "ldp x7, x8, [sp], #0x10; br x8",
        "ldp x8, x9, [sp], #0x10; br x9",
        "ldp x16, x17, [sp], #0x10; br x17",
        "ldp x29, x30, [sp], #0x10; br x30",
        "ldp x30, x29, [sp], #0x10; br x29",
        "svc #0; ret",
    ]

class MachIpcOverflowViaOolPayload(MachIpcBase):
    ""
    CANARY = False 
    leak_challenge = True
    listen_for_message = True
    stack_overflow_on_message = True
    require_complex_message = True
    require_descriptor_type = "MACH_MSG_OOL_DESCRIPTOR"
    description = "How about now?"

    free_gadgets_asm = [
        "ldp x0, x1, [sp], #0x10; br x1",
        "ldp x1, x2, [sp], #0x10; br x2",
        "ldp x2, x3, [sp], #0x10; br x3",
        "ldp x3, x4, [sp], #0x10; br x4",
        "ldp x4, x5, [sp], #0x10; br x5",
        "ldp x5, x6, [sp], #0x10; br x6",
        "ldp x6, x7, [sp], #0x10; br x7",
        "ldp x7, x8, [sp], #0x10; br x8",
        "ldp x8, x9, [sp], #0x10; br x9",
        "ldp x16, x17, [sp], #0x10; br x17",
        "ldp x29, x30, [sp], #0x10; br x30",
        "ldp x30, x29, [sp], #0x10; br x29",
        "svc #0; ret",
    ]


class MachIpcOverflowViaOolPayloadNoLeak(MachIpcBase):
    "Damn, couldn't get this to work (my original exploitation idea was wrong)"
    CANARY = False 
    listen_for_message = True
    stack_overflow_on_message = True
    require_complex_message = True
    random_bin_padding = False
    require_descriptor_type = "MACH_MSG_OOL_DESCRIPTOR"
    description = "How can you ROP when you can't leak?"

    gadgets_after_overflow_return = "br x0"







LEVELS = [
    MachIpcSendAnyToPort,
    MachIpcSendSpecificValue,
    MachIpcSendAnyOolToPort,
    MachIpcSendSpecificValueOolToPort,
    MachIpcReceiveInlineFlagToPort,
    MachIpcReceiveOolFlagToPort,
    MachIpcSendFlagBackInlineToPort,
    MachIpcSendFlagBackOolToPort,
    MachIpcOverflowViaInlinePayload,
    MachIpcOverflowViaOolPayload,
]
NUM_TESTING=1
DOJO_MODULE="mach_ipc"
pwnshop.register_challenges(LEVELS)
