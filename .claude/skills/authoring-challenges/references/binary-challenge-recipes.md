# Binary challenge recipes (compiled-SUID archetype)

One of the four archetypes (see `SKILL.md` §7). Use this when the learner manipulates a
**compiled SUID binary** to a success condition that hands over `/flag` — deterministic
addresses, ASLR off, optional gdb-under-ptrace. (For graded asm/ELF use
`interpreted-checker-challenges.md`; for services use `service-and-web-challenges.md`.
Legacy modules pull prebuilt binaries from external dojos and don't use these recipes.)

Patterns below are taken **verbatim from working levels** in
`challenges/computing-101/the-stack-revisited/`. Read the real files alongside this:
`mem-stack-align/challenge/{program.c,.setup}` and
`gdb-stack-align/challenge/{program.c,bin/gdb,.setup}`.

## Deterministic addresses for a SUID binary (two-phase: personality + memfd re-exec)

ASLR must be off so the stack layout is reproducible. The catch: `personality()`
persists across `execve`, **but** re-execing a SUID binary triggers secureexec and
clears `ADDR_NO_RANDOMIZE`. The fix is a two-phase design: the SUID phase opens `/flag`
(into an inherited FD), sets the personality, **drops privileges**, and re-execs a
**non-SUID memfd copy** of itself. The flag sticks the second time, addresses are
deterministic, and the inherited FD still reads `/flag`.

```c
#define _GNU_SOURCE
#include <err.h>
#include <fcntl.h>
#include <stdio.h>
#include <sys/personality.h>
#include <sys/stat.h>
#include <sys/syscall.h>
#include <unistd.h>

extern char **environ;
#define FLAG_FD 100

static int re_exec_phase(void) {            // FD 100 only exists after setup_phase
    struct stat st;
    return fstat(FLAG_FD, &st) == 0;
}

static void inherit_fd(const char *path, int target, int flags) {
    int fd = open(path, flags);
    if (fd < 0) err(1, "open %s", path);
    if (dup2(fd, target) < 0) err(1, "dup2 %s", path);
    close(fd);
}

static int memfd_clone(const char *path) {   // a memfd carries no SUID bit
    int src = open(path, O_RDONLY);
    if (src < 0) err(1, "open %s", path);
    int dst = syscall(SYS_memfd_create, "clone", 0);
    if (dst < 0) err(1, "memfd_create");
    char buf[8192]; ssize_t n;
    while ((n = read(src, buf, sizeof buf)) > 0)
        if (write(dst, buf, n) != n) err(1, "write");
    close(src);
    return dst;
}

static void setup_phase(char **argv) {
    inherit_fd("/flag", FLAG_FD, O_RDONLY);                 // open while still root
    if (personality(personality(0xFFFFFFFF) | ADDR_NO_RANDOMIZE) < 0) err(1, "personality");
    if (setresuid(getuid(), getuid(), getuid()) < 0) err(1, "setresuid");  // drop privs
    int exe = memfd_clone("/proc/self/exe");
    char path[64]; snprintf(path, sizeof path, "/proc/self/fd/%d", exe);
    execve(path, argv, environ);                            // re-exec the non-SUID copy
    err(1, "execve");
}

static int challenge_phase(int argc, char **argv) {
    // ... ASLR is off here; real challenge logic. On success: ...
    char buf[256];
    ssize_t n = read(FLAG_FD, buf, sizeof buf);             // print the REAL flag
    if (n > 0) write(1, buf, n);
    return 0;
}

int main(int argc, char **argv) {
    if (re_exec_phase()) return challenge_phase(argc, argv);
    setup_phase(argv);
    return 1; /* unreachable */
}
```

- **Do NOT** disable ASLR via `/proc/sys/kernel/randomize_va_space` — `/proc/sys` is
  read-only in the runtime, so it's a silent no-op.
- **Do NOT** add `privileged: true` / a `challenge.yml` for `personality`. The dev
  shell's dockerd ships a patched seccomp profile (`runtime/seccomp.nix`) that already
  allows `personality(ADDR_NO_RANDOMIZE)`. Check `runtime/seccomp.nix` before reaching
  for any extra capability or privilege.
- The flag comes from the **inherited FD opened pre-drop** — no memfd copy of `/flag` is
  needed (an inherited FD keeps its read rights across `execve`).

## Building + installing the SUID binary (`.setup`)

`.setup` runs at **build** time (`.init` runs at container **start**).

```sh
#!/bin/bash
set -e
gcc -static -O2 -o /challenge/program /challenge/program.c
chmod 4755 /challenge/program     # 4755 = SUID + rwxr-xr-x (the repo convention)
rm /challenge/program.c           # don't ship source
```

## Driving a SUID binary under gdb (the `/challenge/bin/gdb` exec-suid wrapper)

A SUID binary loses its elevation under ptrace unless the **debugger itself runs as
root**. Ship a hardened wrapper at `/challenge/bin/gdb`, SUID via its `exec-suid`
shebang, that runs gdb as root but locks down what it will do. This is the established
pattern across the `introspecting/gdb-*` and `gdb-stack-align` levels.

```bash
#!/usr/bin/exec-suid --real -- /bin/bash -p
# Run gdb as root so the kernel preserves SUID elevation on the inferior under ptrace.
# Two defense layers: (1) forward only an allowlist of flags and refuse any inferior
# other than /challenge/program; (2) /challenge/.gdb (loaded via -x before any user
# input) redefines shell/pipe/python/source/dump/save/add-symbol-file as no-ops.
set -e
args=(); program=""
while (( $# )); do
  case "$1" in
    -batch|-q|--quiet|--silent) args+=("$1"); shift ;;
    -ex|--eval-command) [ -n "${2+x}" ] || { echo "$1 needs an argument" >&2; exit 1; }
                        args+=("$1" "$2"); shift 2 ;;
    -*) echo "rejected gdb flag: $1" >&2; exit 1 ;;
    *)  [ -z "$program" ] || { echo "only one program argument allowed" >&2; exit 1; }
        program="$1"; shift ;;
  esac
done
[ -n "$program" ] || { echo "usage: gdb /challenge/program" >&2; exit 1; }
[ "$(realpath -- "$program")" = "/challenge/program" ] || { echo "this wrapper only debugs /challenge/program" >&2; exit 1; }
unset LD_PRELOAD LD_LIBRARY_PATH LD_AUDIT GDBHISTFILE PYTHONPATH PYTHONHOME
exec /usr/bin/gdb -nx -x /challenge/.gdb "${args[@]}" "$program"
```

Install in `.setup`: `chmod 4755 /challenge/bin/gdb` (the SUID bit on the *script* is
what tells `exec-suid` to elevate) and `chmod 644 /challenge/.gdb`. Point the learner at
it in the DESCRIPTION (e.g. "run `gdb /challenge/program`").

## Enforcing "solve it both inside AND outside gdb" (pre-drop sentinels)

When a level must be solved both ways (see `gdb-stack-align`), detect the debugger and
record each path with a **root-owned, mode-600 sentinel file opened before the privilege
drop**. The learner can't forge them: they're root-owned, and the only writable handle
is the pre-drop `dup2` inheritance. Release the flag only when both exist.

```c
#define MY_SENT_FD 101
#define OTHER_SENT_FD 102
static int is_traced(void) {                 // TracerPid != 0 ⇒ a debugger is attached
    int fd = open("/proc/self/status", O_RDONLY); if (fd < 0) return 0;
    char buf[4096]; ssize_t n = read(fd, buf, sizeof buf - 1); close(fd);
    if (n <= 0) return 0; buf[n] = 0;
    char *p = strstr(buf, "TracerPid:");
    return p && atoi(p + sizeof("TracerPid:") - 1) != 0;
}
// in setup_phase(), before dropping privs:
int traced = is_traced();
inherit_fd(traced ? GDB_SENTINEL : SHELL_SENTINEL, MY_SENT_FD,    O_WRONLY | O_APPEND);
inherit_fd(traced ? SHELL_SENTINEL : GDB_SENTINEL, OTHER_SENT_FD, O_RDONLY);
// in challenge_phase() on a correct solve: write "1" to MY_SENT_FD, fsync, then read
// OTHER_SENT_FD; print the flag only if the other context already wrote its sentinel.
```

The binary must still **run** in both contexts — `is_traced()` only selects which
sentinel to set; it never refuses to run untraced.

## Tests

- `tests_private/test_solve.sh` runs the **actual published solving procedure** and
  checks the real flag comes back. Because ASLR is off the solve is deterministic — e.g.
  `mem-stack-align` reads `argv[0]` from a clean baseline run and computes the exact env
  padding to hit the target alignment (no brute force needed):
  ```sh
  #!/bin/bash
  set -e
  BASELINE=$(env -i /challenge/program 2>&1 || true)
  ARGV0=$(printf '%s' "$BASELINE" | grep -oP '0x[0-9a-fA-F]+' | head -1)
  LOW=$(( ARGV0 & 0xFFFF )); DELTA=$(( (LOW - 0x5390) & 0xFFFF ))
  PAD_LEN=$(( DELTA - 5 )); [ "$PAD_LEN" -lt 0 ] && PAD_LEN=$(( PAD_LEN + 0x10000 ))
  PAD=$(printf 'x%.0s' $(seq 1 $PAD_LEN) 2>/dev/null)
  exec env -i "FOO=$PAD" /challenge/program     # prints the flag on success
  ```
- `tests_private/**` is git-crypt-encrypted (`.gitattributes`:
  `**/tests_private/** filter=git-crypt-computing-101`). Borrow the key from a sibling
  checkout under `~/pwncollege/challenges*/.git/git-crypt/keys/` instead of prompting for
  a GPG passphrase.
- Test files must be executable. **Always run via `nix develop --command pwnshop test ...`.**

## module.yml — ordering and hiding

Challenge order is the order of `- type: challenge` entries in the module's `module.yml`
(plus interleaved `lecture`/`markdown` resources). To hide a not-yet-released challenge,
add a future `visibility.start` to its entry and validate with `tools/dojo/parse-dojo-yml`:

```yaml
- type: challenge
  id: my-challenge
  name: "Human-Readable Name"
  visibility:
    start: "2099-01-01T00:00:00+00:00"   # ISO-8601 with tz offset; must parse via fromisoformat
```

`visibility` is valid on dojo, module, and challenge entries (precedent:
`advent-of-pwn/2025/module.yml`, `v8-exploitation/module.yml`). When editing one entry
among many similar ones, keep the edit target tight so you don't touch an adjacent,
pre-existing challenge.
