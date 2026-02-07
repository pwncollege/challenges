#include <linux/bpf.h>
#include <linux/ptrace.h>
#include <linux/types.h>
#include <stdbool.h>
#include <stddef.h>
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>

struct {
    __uint(type, BPF_MAP_TYPE_ARRAY);
    __uint(max_entries, 1);
    __type(key, __u32);
    __type(value, __u32);
} progress SEC(".maps");

struct {
    __uint(type, BPF_MAP_TYPE_ARRAY);
    __uint(max_entries, 1);
    __type(key, __u32);
    __type(value, __u32);
} success SEC(".maps");

static __always_inline bool name_equals(const char *haystack, const __u8 *lit, int nlen)
{
    char buf[16];
    int len = bpf_probe_read_user_str(buf, sizeof(buf), haystack);

    if (len != nlen + 1)
        return false;

    for (int j = 0; j < nlen; j++) {
        if (((__u8)buf[j]) != lit[j])
            return false;
    }

    return true;
}

static __always_inline int handle_path(const char *filename)
{
    __u32 key0 = 0;
    __u32 *statep;
    __u32 state;

    statep = bpf_map_lookup_elem(&progress, &key0);
    state = statep ? *statep : 0;

    if (name_equals(filename, (const __u8[]){'d','a','s','h','e','r'}, 6)) {
        state = 1;
    } else if (state == 1 && name_equals(filename, (const __u8[]){'d','a','n','c','e','r'}, 6)) {
        state = 2;
    } else if (state == 2 && name_equals(filename, (const __u8[]){'p','r','a','n','c','e','r'}, 7)) {
        state = 3;
    } else if (state == 3 && name_equals(filename, (const __u8[]){'v','i','x','e','n'}, 5)) {
        state = 4;
    } else if (state == 4 && name_equals(filename, (const __u8[]){'c','o','m','e','t'}, 5)) {
        state = 5;
    } else if (state == 5 && name_equals(filename, (const __u8[]){'c','u','p','i','d'}, 5)) {
        state = 6;
    } else if (state == 6 && name_equals(filename, (const __u8[]){'d','o','n','n','e','r'}, 6)) {
        state = 7;
    } else if (state == 7 && name_equals(filename, (const __u8[]){'b','l','i','t','z','e','n'}, 7)) {
        state = 8;
    } else {
        state = 0;
    }

    if (state == 8) {
        __u32 v = 1;
        bpf_map_update_elem(&success, &key0, &v, BPF_ANY);
    }

    bpf_map_update_elem(&progress, &key0, &state, BPF_ANY);
    return 0;
}

static __always_inline bool is_sleigh(const char *name)
{
    return name_equals(name, (const __u8[]){'s','l','e','i','g','h'}, 6);
}

SEC("kprobe/__x64_sys_linkat")
int handle_do_linkat(struct pt_regs *ctx)
{
    char tmp[16];
    int len;
    struct pt_regs *regs = (struct pt_regs *)PT_REGS_PARM1(ctx);
    const char *oldname = NULL;
    const char *newname = NULL;

    if (!regs)
        return 0;

    bpf_probe_read_kernel(&oldname, sizeof(oldname),
                          (const void *)((const char *)regs + offsetof(struct pt_regs, rsi)));
    bpf_probe_read_kernel(&newname, sizeof(newname),
                          (const void *)((const char *)regs + offsetof(struct pt_regs, r10)));

    if (!oldname || !newname)
        return 0;

    len = bpf_probe_read_user_str(tmp, sizeof(tmp), oldname);
    if (len <= 0)
        return 0;

    if (!is_sleigh(oldname))
        return 0;

    len = bpf_probe_read_user_str(tmp, sizeof(tmp), newname);
    if (len <= 0)
        return 0;

    return handle_path(newname);
}

char LICENSE[] SEC("license") = "Dual BSD/GPL";
