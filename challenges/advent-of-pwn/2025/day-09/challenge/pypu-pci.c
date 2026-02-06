#include "qemu/osdep.h"

#include <Python.h>
#include <errno.h>
#include <fcntl.h>
#include <inttypes.h>
#include <linux/landlock.h>
#include <marshal.h>
#include <stdbool.h>
#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/prctl.h>
#include <sys/syscall.h>
#include <sys/types.h>
#include <unistd.h>

#include "glib.h"
#include "hw/pci/pci.h"
#include "hw/pci/pci_device.h"
#include "hw/pci/pcie.h"
#include "hw/pci/pci_ids.h"
#include "hw/qdev-properties.h"
#include "qemu/cutils.h"
#include "qemu/module.h"
#include "qemu/thread.h"
#include "system/memory.h"

#include "pypu-capture.h"
#include "pypu-privileged.h"

#define TYPE_PYPU_PCI "pypu-pci"
#define PYPU_PCI(obj) OBJECT_CHECK(PypuPCIState, (obj), TYPE_PYPU_PCI)
#define CODE_BUF_SIZE 2048

typedef struct PypuPCIState {
    PCIDevice parent_obj;

    MemoryRegion mmio;
    MemoryRegion stdout_mmio;
    MemoryRegion stderr_mmio;

    uint8_t code[CODE_BUF_SIZE];
    char stdout_capture[0x1000];
    char stderr_capture[0x1000];
    char flag[128];

    uint32_t scratch;
    uint32_t greet_count;
    uint32_t code_len;
    uint32_t work_gen;
    uint32_t done_gen;
    bool py_thread_alive;

    QemuThread py_thread;
    QemuMutex py_mutex;
    QemuCond py_cond;

    PyObject *globals_dict;
    PyObject *gifts_module;
} PypuPCIState;

static uint32_t load_le32(const uint8_t *p)
{
    return (uint32_t)p[0] | ((uint32_t)p[1] << 8) |
           ((uint32_t)p[2] << 16) | ((uint32_t)p[3] << 24);
}

static uint64_t load_le64(const uint8_t *p)
{
    return (uint64_t)load_le32(p) | ((uint64_t)load_le32(p + 4) << 32);
}

static void debug_log(const char *fmt, ...)
{
    static int initialized;
    static int enabled;

    if (!initialized) {
        const char *env = getenv("PYPU_DEBUG");
        enabled = env && env[0];
        initialized = 1;
    }
    if (!enabled) {
        return;
    }

    va_list ap;
    va_start(ap, fmt);
    vfprintf(stderr, fmt, ap);
    va_end(ap);
}

static PyObject *pypu_get_globals(PypuPCIState *state, bool privileged)
{
    if (!state) {
        return NULL;
    }

    if (!state->globals_dict) {
        PyObject *main_module = PyImport_AddModule("__main__");
        if (!main_module) {
            PyErr_Print();
            return NULL;
        }
        PyObject *globals_dict = PyModule_GetDict(main_module);
        if (!globals_dict) {
            PyErr_Print();
            return NULL;
        }

        if (PyDict_SetItemString(globals_dict, "__builtins__", PyEval_GetBuiltins()) < 0) {
            PyErr_Print();
            return NULL;
        }

        PyObject *sys_module = PyImport_ImportModule("sys");
        if (!sys_module) {
            PyErr_Print();
            return NULL;
        }

        PyObject *stdout = pypu_capture_new(state->stdout_capture, sizeof(state->stdout_capture));
        if (!stdout || PyObject_SetAttrString(sys_module, "stdout", stdout) < 0) {
            PyErr_Print();
            Py_XDECREF(stdout);
            Py_DECREF(sys_module);
            return NULL;
        }
        Py_DECREF(stdout);

        PyObject *stderr = pypu_capture_new(state->stderr_capture, sizeof(state->stderr_capture));
        if (!stderr || PyObject_SetAttrString(sys_module, "stderr", stderr) < 0) {
            PyErr_Print();
            Py_XDECREF(stderr);
            Py_DECREF(sys_module);
            return NULL;
        }
        Py_DECREF(stderr);

        Py_DECREF(sys_module);
        Py_INCREF(globals_dict);
        state->globals_dict = globals_dict;
    }

    if (!state->gifts_module) {
        PyObject *gifts_module = PyModule_New("gifts");
        if (!gifts_module) {
            PyErr_Print();
            return NULL;
        }
        PyObject *flag_val = PyUnicode_FromString(state->flag);
        if (!flag_val) {
            PyErr_Print();
            Py_DECREF(gifts_module);
            return NULL;
        }
        if (PyModule_AddObject(gifts_module, "flag", flag_val) < 0) {
            PyErr_Print();
            Py_DECREF(flag_val);
            Py_DECREF(gifts_module);
            return NULL;
        }
        state->gifts_module = gifts_module;
    }

    PyObject *sys_module = PyImport_ImportModule("sys");
    if (!sys_module) {
        PyErr_Print();
        return NULL;
    }

    PyObject *modules = PyObject_GetAttrString(sys_module, "modules");
    if (!modules || !PyDict_Check(modules)) {
        PyErr_Print();
        Py_XDECREF(modules);
        Py_DECREF(sys_module);
        return NULL;
    }

    if (privileged) {
        if (PyDict_SetItemString(modules, "gifts", state->gifts_module) < 0) {
            PyErr_Print();
            Py_DECREF(modules);
            Py_DECREF(sys_module);
            return NULL;
        }
    } else {
        if (PyDict_DelItemString(state->globals_dict, "gifts") < 0) {
            PyErr_Clear();
        }
        if (PyDict_DelItemString(modules, "gifts") < 0) {
            PyErr_Clear();
        }
    }

    Py_DECREF(modules);
    Py_DECREF(sys_module);

    return state->globals_dict;
}

static void execute_python_code(PypuPCIState *state, const uint8_t *pyc, uint32_t pyc_len)
{
    debug_log("[pypu] executing python code from MMIO (%u bytes)\n", pyc_len);
    for (uint32_t i = 0; i < pyc_len && i < 32; i++) {
        debug_log("%s%02x", (i == 0 ? "[pypu] code bytes: " : " "), pyc[i]);
    }
    debug_log("%s\n", pyc_len > 0 ? "" : "[pypu] code bytes: <none>");

    if (pyc_len < 16) {
        debug_log("[pypu] abort: missing header (%u bytes)\n", pyc_len);
        return;
    }

    PyGILState_STATE gil = PyGILState_Ensure();

    uint32_t header_magic = load_le32(pyc);
    uint32_t pyc_flags = load_le32(pyc + 4);
    uint64_t pyc_hash = load_le64(pyc + 8);
    unsigned long expected_magic = (unsigned long)PyImport_GetMagicNumber();
    debug_log("[pypu] pyc header: magic=0x%08x expected=0x%08lx flags=0x%08x hash=0x%016" PRIx64 "\n",
              header_magic, expected_magic, pyc_flags, pyc_hash);

    if (header_magic != (uint32_t)expected_magic) {
        debug_log("[pypu] abort: bad pyc magic\n");
        PyGILState_Release(gil);
        return;
    }

    bool privileged = pyc_hash == PYPU_PRIVILEGED_HASH;
    if (privileged) {
        debug_log("[pypu] pyc hash matches privileged blob (0x%016" PRIx64 ")\n",
                  PYPU_PRIVILEGED_HASH);
    }

    const uint8_t *code = pyc + 16;
    Py_ssize_t code_len = (Py_ssize_t)pyc_len - 16;
    PyObject *code_obj = PyMarshal_ReadObjectFromString((const char *)code, code_len);
    if (!code_obj) {
        PyErr_Print();
        PyGILState_Release(gil);
        return;
    }
    if (!PyCode_Check(code_obj)) {
        debug_log("[pypu] marshal output not a code object\n");
        Py_DECREF(code_obj);
        PyGILState_Release(gil);
        return;
    }

    PyObject *globals = pypu_get_globals(state, privileged);
    if (!globals) {
        PyErr_Print();
        Py_DECREF(code_obj);
        PyGILState_Release(gil);
        return;
    }

    PyObject *result = PyEval_EvalCode((PyObject *)code_obj, globals, globals);
    if (!result) {
        debug_log("[pypu] python execution failed\n");
        PyErr_Print();
        Py_DECREF(code_obj);
        PyGILState_Release(gil);
        return;
    }
    debug_log("[pypu] python execution succeeded\n");
    Py_DECREF(result);
    Py_DECREF(code_obj);
    PyGILState_Release(gil);
}

static int enable_landlock(void)
{
    uint64_t handled =
        LANDLOCK_ACCESS_FS_EXECUTE |
        LANDLOCK_ACCESS_FS_WRITE_FILE |
        LANDLOCK_ACCESS_FS_READ_FILE |
        LANDLOCK_ACCESS_FS_READ_DIR |
        LANDLOCK_ACCESS_FS_REMOVE_DIR |
        LANDLOCK_ACCESS_FS_REMOVE_FILE |
        LANDLOCK_ACCESS_FS_MAKE_CHAR |
        LANDLOCK_ACCESS_FS_MAKE_DIR |
        LANDLOCK_ACCESS_FS_MAKE_REG |
        LANDLOCK_ACCESS_FS_MAKE_SOCK |
        LANDLOCK_ACCESS_FS_MAKE_FIFO |
        LANDLOCK_ACCESS_FS_MAKE_BLOCK |
        LANDLOCK_ACCESS_FS_MAKE_SYM |
        LANDLOCK_ACCESS_FS_REFER |
        LANDLOCK_ACCESS_FS_TRUNCATE |
        LANDLOCK_ACCESS_FS_IOCTL_DEV;

    if (prctl(PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0) < 0) {
        debug_log("[pypu] PR_SET_NO_NEW_PRIVS failed: %s\n", strerror(errno));
        return -1;
    }

    struct landlock_ruleset_attr attr = {
        .handled_access_fs = handled,
    };

    int ruleset_fd = syscall(__NR_landlock_create_ruleset, &attr, sizeof(attr), 0);
    if (ruleset_fd < 0) {
        debug_log("[pypu] landlock_create_ruleset failed: %s\n", strerror(errno));
        return -1;
    }

    int lib_fd = open("/usr/lib/python3.13", O_PATH | O_DIRECTORY);
    if (lib_fd < 0) {
        debug_log("[pypu] open python stdlib failed: %s\n", strerror(errno));
        close(ruleset_fd);
        return -1;
    }

    struct landlock_path_beneath_attr lib_rule = {
        .allowed_access =
            LANDLOCK_ACCESS_FS_READ_FILE |
            LANDLOCK_ACCESS_FS_READ_DIR |
            LANDLOCK_ACCESS_FS_EXECUTE,
        .parent_fd = lib_fd,
    };

    if (syscall(__NR_landlock_add_rule, ruleset_fd, LANDLOCK_RULE_PATH_BENEATH,
                &lib_rule, 0) < 0) {
        debug_log("[pypu] landlock_add_rule for stdlib failed: %s\n", strerror(errno));
        close(lib_fd);
        close(ruleset_fd);
        return -1;
    }
    close(lib_fd);

    if (syscall(__NR_landlock_restrict_self, ruleset_fd, 0) < 0) {
        debug_log("[pypu] landlock_restrict_self failed: %s\n", strerror(errno));
        close(ruleset_fd);
        return -1;
    }

    close(ruleset_fd);
    return 0;
}

static void *python_worker(void *opaque)
{
    PypuPCIState *state = opaque;

    Py_Initialize();
    if (enable_landlock() < 0) {
        qemu_mutex_lock(&state->py_mutex);
        state->py_thread_alive = false;
        state->done_gen = state->work_gen;
        qemu_cond_signal(&state->py_cond);
        qemu_mutex_unlock(&state->py_mutex);
        return NULL;
    }

    qemu_mutex_lock(&state->py_mutex);
    while (state->py_thread_alive) {
        while (state->py_thread_alive && state->done_gen == state->work_gen) {
            qemu_cond_wait(&state->py_cond, &state->py_mutex);
        }
        if (!state->py_thread_alive) {
            break;
        }
        uint32_t pyc_len = state->code_len;
        uint8_t pyc[CODE_BUF_SIZE];
        memcpy(pyc, state->code, pyc_len);
        uint32_t task_gen = state->work_gen;
        qemu_mutex_unlock(&state->py_mutex);

        execute_python_code(state, pyc, pyc_len);

        qemu_mutex_lock(&state->py_mutex);
        state->done_gen = task_gen;
        qemu_cond_signal(&state->py_cond);
    }
    qemu_mutex_unlock(&state->py_mutex);
    return NULL;
}

static uint64_t pypu_mmio_read(void *opaque, hwaddr addr, unsigned size)
{
    PypuPCIState *state = opaque;

    if (addr == 0x00 && size == 4) {
        return 0x50595055ull; /* "PYPU" */
    }
    if (addr == 0x04 && size == 4) {
        return state->scratch;
    }
    if (addr == 0x08 && size == 4) {
        return state->greet_count;
    }
    if (addr == 0x10 && size == 4) {
        return state->code_len;
    }
    if (addr >= 0x100 && addr - 0x100 < CODE_BUF_SIZE) {
        return state->code[addr - 0x100];
    }

    return 0;
}

static uint64_t pypu_stdout_read(void *opaque, hwaddr addr, unsigned size)
{
    PypuPCIState *state = opaque;
    if (size != 1) {
        return 0;
    }
    if (addr < sizeof(state->stdout_capture)) {
        return (uint8_t)state->stdout_capture[addr];
    }
    return 0;
}

static uint64_t pypu_stderr_read(void *opaque, hwaddr addr, unsigned size)
{
    PypuPCIState *state = opaque;
    if (size != 1) {
        return 0;
    }
    if (addr < sizeof(state->stderr_capture)) {
        return (uint8_t)state->stderr_capture[addr];
    }
    return 0;
}

static void pypu_mmio_write(void *opaque, hwaddr addr, uint64_t val,
                             unsigned size)
{
    PypuPCIState *state = opaque;

    if (addr == 0x04 && size == 4) {
        state->scratch = val;
    } else if (addr == 0x0c && size == 4) {
        state->greet_count++;
        qemu_mutex_lock(&state->py_mutex);
        state->work_gen++;
        qemu_cond_signal(&state->py_cond);
        while (state->done_gen != state->work_gen && state->py_thread_alive) {
            qemu_cond_wait(&state->py_cond, &state->py_mutex);
        }
        qemu_mutex_unlock(&state->py_mutex);
    } else if (addr == 0x10 && size == 4) {
        if (val > CODE_BUF_SIZE) {
            val = CODE_BUF_SIZE;
        }
        state->code_len = val;
    } else if (addr >= 0x100 && addr < 0x100 + CODE_BUF_SIZE && size == 1) {
        state->code[addr - 0x100] = (uint8_t)val;
    }
}

static const MemoryRegionOps pypu_mmio_ops = {
    .read = pypu_mmio_read,
    .write = pypu_mmio_write,
    .endianness = DEVICE_LITTLE_ENDIAN,
    .valid = {
        .min_access_size = 1,
        .max_access_size = 4,
    },
    .impl = {
        .min_access_size = 1,
        .max_access_size = 4,
    },
};

static const MemoryRegionOps pypu_stdout_ops = {
    .read = pypu_stdout_read,
    .endianness = DEVICE_LITTLE_ENDIAN,
    .valid = {
        .min_access_size = 1,
        .max_access_size = 1,
    },
    .impl = {
        .min_access_size = 1,
        .max_access_size = 1,
    },
};

static const MemoryRegionOps pypu_stderr_ops = {
    .read = pypu_stderr_read,
    .endianness = DEVICE_LITTLE_ENDIAN,
    .valid = {
        .min_access_size = 1,
        .max_access_size = 1,
    },
    .impl = {
        .min_access_size = 1,
        .max_access_size = 1,
    },
};

static void pypu_pci_reset(DeviceState *dev)
{
    PypuPCIState *state = PYPU_PCI(dev);

    state->scratch = 0;
    state->greet_count = 0;
    state->code_len = 0;
    memset(state->code, 0, sizeof(state->code));
    pstrcpy(state->stdout_capture, sizeof(state->stdout_capture), "");
    pstrcpy(state->stderr_capture, sizeof(state->stderr_capture), "");
    pstrcpy(state->flag, sizeof(state->flag), "");
    state->work_gen = 0;
    state->done_gen = 0;
}

static void pypu_pci_realize(PCIDevice *pdev, Error **errp)
{
    PypuPCIState *state = PYPU_PCI(pdev);

    qemu_mutex_init(&state->py_mutex);
    qemu_cond_init(&state->py_cond);
    state->py_thread_alive = true;
    state->work_gen = 0;
    state->done_gen = 0;
    g_autofree char *flag_file = NULL;
    if (g_file_get_contents("/flag", &flag_file, NULL, NULL)) {
        pstrcpy(state->flag, sizeof(state->flag), flag_file);
    }
    qemu_thread_create(&state->py_thread, "pypu-py", python_worker, state,
                       QEMU_THREAD_JOINABLE);

    pci_config_set_vendor_id(pdev->config, 0x1337);
    pci_config_set_device_id(pdev->config, 0x1225);
    pci_config_set_class(pdev->config, PCI_CLASS_OTHERS);

    memory_region_init_io(&state->mmio, OBJECT(pdev), &pypu_mmio_ops, state,
                          "pypu-mmio", 0x1000);
    pci_register_bar(pdev, 0, PCI_BASE_ADDRESS_SPACE_MEMORY, &state->mmio);
    memory_region_init_io(&state->stdout_mmio, OBJECT(pdev), &pypu_stdout_ops, state,
                          "pypu-stdout", sizeof(state->stdout_capture));
    pci_register_bar(pdev, 1, PCI_BASE_ADDRESS_SPACE_MEMORY, &state->stdout_mmio);
    memory_region_init_io(&state->stderr_mmio, OBJECT(pdev), &pypu_stderr_ops, state,
                          "pypu-stderr", sizeof(state->stderr_capture));
    pci_register_bar(pdev, 2, PCI_BASE_ADDRESS_SPACE_MEMORY, &state->stderr_mmio);
}

static void pypu_pci_class_init(ObjectClass *klass, const void *data)
{
    DeviceClass *dc = DEVICE_CLASS(klass);
    PCIDeviceClass *k = PCI_DEVICE_CLASS(klass);

    dc->legacy_reset = pypu_pci_reset;
    dc->desc = "Python Processing Unit (pypu)";
    dc->hotpluggable = false;

    k->class_id = PCI_CLASS_OTHERS;
    k->realize = pypu_pci_realize;
}

static void pypu_pci_finalize(Object *obj)
{
    PypuPCIState *state = PYPU_PCI(obj);

    qemu_mutex_lock(&state->py_mutex);
    state->py_thread_alive = false;
    qemu_cond_signal(&state->py_cond);
    qemu_mutex_unlock(&state->py_mutex);
    qemu_thread_join(&state->py_thread);
    qemu_cond_destroy(&state->py_cond);
    qemu_mutex_destroy(&state->py_mutex);

    PyGILState_STATE gil = PyGILState_Ensure();
    Py_XDECREF(state->globals_dict);
    Py_XDECREF(state->gifts_module);
    state->globals_dict = NULL;
    state->gifts_module = NULL;
    PyGILState_Release(gil);
}

static const TypeInfo pypu_pci_info = {
    .name          = TYPE_PYPU_PCI,
    .parent        = TYPE_PCI_DEVICE,
    .instance_size = sizeof(PypuPCIState),
    .class_init    = pypu_pci_class_init,
    .instance_finalize = pypu_pci_finalize,
    .interfaces = (InterfaceInfo[]) {
        { INTERFACE_PCIE_DEVICE },
        { }
    },
};

static void pypu_pci_register_types(void)
{
    type_register_static(&pypu_pci_info);
}

type_init(pypu_pci_register_types);
