import pwn
import pwnshop

PWNSHOP_AUTOREGISTER = False

from pwnshop import Challenge, retry

class MachTaskPortsBase(Challenge):
    COMPILER = "clang"
    LINK_LIBRARIES = []
    MASM_FLAG = None
    RELRO = None # Hack to not have any -z flag

    TEMPLATE_PATH = "mach_task_ports/mach_task_ports.c"

    our_register_port_name_prefix = "college.pwn.mac-ports"

    give_task_port = False
    give_host_priv_port = False
    give_task_exception_port = False
    give_kernel_task_port = False
    
    get_flag_function = False
    leak_flag_address = False
    leak_win_variable = False
    require_win_variable_for_flag = False


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.bin_padding = self.random.randrange(0x10, 0x1000)
        self.our_register_port_name = f"{self.our_register_port_name_prefix}"


class MachTaskPortsReadMemory(MachTaskPortsBase):
    ""
    give_task_port = True
    get_flag_function = True
    leak_flag_address = True

    description = "To start, use the task port to read the flag from memory knowing the flag's address."

        
class MachTaskPortsWriteMemory(MachTaskPortsBase):
    ""
    give_task_port = True
    get_flag_function = True
    leak_win_variable = True

    description = "Now, use the task port to overwrite a variable in memory to get the flag."


class MachTaskPortsFlagInMemory(MachTaskPortsBase):
    ""
    give_task_port = True
    get_flag_function = True

    description = "Now, the flag is somewhere in memory, use the task port to get the flag."

class MachTaskPorts(MachTaskPortsBase):
    ""
    give_task_port = True

    description = "Use the task port to get your own flag."


class MachTaskPortsHostPriv(MachTaskPortsBase):
    ""
    give_host_priv_port = True

    description = "Use the host_priv port to get the flag."

class MachTaskPortsExceptionPort(MachTaskPortsBase):
    ""
    give_task_exception_port = True

    description = "Use the task's exception port to get the flag."

class MachTaskPortsKernelTaskPort(MachTaskPortsBase):
    ""
    give_kernel_task_port = True

    description = "Use the kernel_task port to get the flag."

LEVELS = [
    MachTaskPortsReadMemory,
    MachTaskPortsWriteMemory,
    MachTaskPortsFlagInMemory,
    MachTaskPorts,
    MachTaskPortsHostPriv,
    MachTaskPortsExceptionPort,
]
DOJO_MODULE="mach_task_ports"
pwnshop.register_challenges(LEVELS)
