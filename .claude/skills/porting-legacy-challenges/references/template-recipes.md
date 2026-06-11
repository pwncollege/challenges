# Template recipes — the seeded-determinism pattern, copy-paste

Concrete shapes for the architecture in SKILL.md §2–§3. Generalized from a real port; rename
`cimg`/`c`/levels to your module. The point of every recipe: a challenge's **body** and its
**solver** derive byte-identical seeded values because both run the same config first.

## Directory layout

```
challenges/<module>/
  common/
    <module>_lib.j2        # shared helpers: defaults, draw_magic, image/byte builders, itype
    body.c.j2              # the full C source, parameterized by a pre-built `c` (context)
    body.py.j2             # python-script variant (exec-suid)
    test.py.j2             # the shared solver, parameterized by `c`
    Dockerfile.c.j2        # extends ../../common/Dockerfile.j2, compiles + SUID
  <chal>/                  # one per challenge (presentations share config content, not files)
    DESCRIPTION.md
    challenge/
      Dockerfile.j2
      cimg.c.j2            # INLINE config + include body
    tests_public/test_functionality.sh.j2
    tests_private/test_solve.py.j2   # INLINE the SAME config + include test
```

## Shared lib — helpers + the namespace-mutation idiom

`common/<module>_lib.j2` exports macros only (no top-level output). A macro takes the
caller's `namespace()` and mutates it; mutations propagate back (this is how one call
configures both body and test).

```jinja
{#- defaults(c, level): set every option to its default; a leaf then overrides. -#}
{%- macro defaults(c, level) -%}
  {%- set c.level = level -%}
  {%- set c.version = 0 -%}
  {%- set c.color = false -%}
  {%- set c.directives = {} -%}
  {#- … all options … -#}
{%- endmacro -%}

{#- draw_magic: 5 seeded draws when random, else a fixed value. ORDER must be stable. -#}
{%- macro draw_magic(c, random, randomize) -%}
  {%- set ORD = {"c":99, "I":73, "M":77, "G":71, "(":40, "n":110, "6":54} -%}{# precomputed; no ord filter #}
  {%- if randomize -%}
    {%- set hv = random.choice(["CIMG", "CNNR", "CNMG"]) -%}
    {%- set repl = {"C":"cC[(", "I":"iI1|", "M":"mM", "G":"gG6", "N":"nN%"} -%}
    {%- set c.magic = random.choice(repl[hv[0]]) ~ random.choice(repl[hv[1]]) ~ random.choice(repl[hv[2]]) ~ random.choice(repl[hv[3]]) -%}
  {%- else -%}
    {%- set c.magic = "cIMG" -%}
  {%- endif -%}
  {%- set c.magic_int = ORD[c.magic[0]] + ORD[c.magic[1]] * 256 + ORD[c.magic[2]] * 65536 + ORD[c.magic[3]] * 16777216 -%}
{%- endmacro -%}

{#- a side-effecting builder: mutate a list element via __setitem__ (no subscript-set syntax). -#}
{%- macro make_grid(c, random, w, h) -%}
  {%- set px = [] -%}
  {%- for i in range(w * h) -%}{%- set _ = px.append([0, 0, 0, 32]) -%}{%- endfor -%}
  {%- set _ = px.__setitem__(0, [255, 255, 255, 46]) -%}
  {%- set c.target = px -%}
{%- endmacro -%}

{%- macro itype(bits) -%}uint{{ bits }}_t{%- endmacro -%}
```

Macros that aren't passed `random` can't draw from it — `{% import … as lib %}` does **not**
give imported macros your context, so always pass `random` (and `c`) as arguments.

## Leaf body — inline config, then include the shared body

`<chal>/challenge/cimg.c.j2`:

```jinja
{%- import "../../common/<module>_lib.j2" as lib -%}
{%- set c = namespace() -%}
{{- lib.defaults(c, "color") -}}
{{- lib.draw_magic(c, random, false) -}}
{%- set c.version = 2 -%}
{%- set c.color = true -%}
{%- set c.width = random.randint(20, 80) -%}
{%- include "../../common/body.c.j2" -%}
```

`{% include %}` passes context, so `body.c.j2` sees this `c` (and the `random` global). The
config draws (`random.*`) happen here, before the include — the body itself must not draw.

## Shared body — consume `c` from context (don't build it)

`common/body.c.j2` (note: it does NOT `{% set c = namespace() %}` — the leaf did):

```jinja
{%- import "<module>_lib.j2" as lib -%}{# for lib.itype etc. #}
#define _GNU_SOURCE 1
#include <stdio.h>
/* … */
struct cimg_header {
    {% if c.magic_kind == "chars" %}char magic_number[4];{% else %}unsigned int magic_number;{% endif %}
    {% if c.version %}{{ lib.itype(c.version_bitwidth) }} version;{% endif %}
} __attribute__((packed));
/* … bake seeded constants … */
if (cimg.magic_number != {{ c.magic_int }}) { puts("ERROR"); exit(-1); }
{% if c.check_framebuffer %}
char desired_output[] = { {{ c.fb_bytes | join(", ") }} };  /* bytes, not a C string literal */
{% endif %}
```

## Leaf test — inline the SAME config, then include the shared solver

`<chal>/tests_private/test_solve.py.j2` (the duplicated config is required — the test rebuilds
the same values to craft a matching input):

```jinja
{%- import "../../common/<module>_lib.j2" as lib -%}
{%- set c = namespace() -%}
{{- lib.defaults(c, "color") -}}
{{- lib.draw_magic(c, random, false) -}}
{%- set c.version = 2 -%}
{%- set c.color = true -%}
{%- set c.width = random.randint(20, 80) -%}
{%- include "../../common/test.py.j2" -%}
```

`common/test.py.j2` — **directives BEFORE the shebang** (so trimming can't eat the shebang's
newline), then build input from `c`, run, and match the flag from output:

```jinja
{%- set hexparts = [] -%}
{%- for p in c.target -%}{%- set _ = hexparts.append("%02x%02x%02x%02x" | format(p[0], p[1], p[2], p[3])) -%}{%- endfor -%}
#!/usr/bin/env python3
import re, struct, subprocess
TARGET = bytes.fromhex("{{ hexparts | join('') }}")
body = bytearray({{ c.magic | tojson }}.encode("latin1"))
body += {{ c.magic_int }}.to_bytes(4, "little")  # or pack version/dims/etc. from c.*
# … craft the rest exactly as the OLD verify() did …
open("/tmp/solve.cimg", "wb").write(body)
out = subprocess.run(["/challenge/cimg", "/tmp/solve.cimg"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=30).stdout.decode("latin1")
print(out[-2000:])
m = re.search(r"pwn\.college\{[^}\n]+\}", out)   # NOT os.environ["FLAG"] — it isn't set
assert m, "no flag"
print(f"Flag: {m.group(0)}")
```

## The shebang trap (this *will* bite you)

WRONG — `{%-` after the shebang strips its newline; `python3` then runs piped stdin as code:
```jinja
#!/usr/bin/exec-suid -- /usr/bin/python3 -I
{%- import "lib.j2" as lib -%}    {#- eats the newline above → "…python3 -Iimport sys" #}
```
RIGHT — directives first, shebang last; each `{%- … -%}` emits nothing and the shebang lands
on physical line 1:
```jinja
{%- import "lib.j2" as lib -%}
{%- set c = namespace() -%}
{%- set _ = lib.defaults(c, "x") -%}
#!/usr/bin/exec-suid -- /usr/bin/python3 -I

import sys
```

## Dockerfile — extend the common chain, compile, SUID

`common/Dockerfile.c.j2`:
```jinja
{%- extends "../../common/Dockerfile.j2" -%}
{%- block additional_packages %}{{ super() }} build-essential{% endblock -%}
{%- block setup -%}
RUN <<'EOF'
set -eu
gcc -O0 -w -o /challenge/cimg /challenge/cimg.c
chmod 4755 /challenge/cimg
{% if keep_source | default(false) %}chmod 644 /challenge/cimg.c{% else %}rm -f /challenge/cimg.c{% endif %}
rm -f /challenge/Dockerfile /challenge/.setup
EOF
{%- endblock -%}
```
`<chal>/challenge/Dockerfile.j2` (a variable set in the leaf *does* reach the extended
block via include context):
```jinja
{%- set keep_source = true -%}
{%- include "../../common/Dockerfile.c.j2" -%}
```
Only the rendered `challenge/` subdir is the Docker build context — files at the
challenge-dir root (or in `common/`) are Jinja-resolved at render time but not copied in.

## Why this is deterministic (and how to confirm)

`render()` builds a fresh `random.Random(CHALLENGE_SEED)` per file, so the body's
`draw_magic`/`make_grid` and the test's identical calls consume the same RNG stream and
produce the same magic/grid. To prove a refactor preserves behavior without re-running
Docker: `pwnshop render` the new leaf, `git stash` to the old version, render again, `diff`
— byte-identical means the same variant. To prove it survives a different deployment seed:
`CHALLENGE_SEED=42 pwnshop test …`.

## A python-script variant (`exec-suid`)

Same inline-config leaf, but the body is `common/body.py.j2` with shebang
`#!/usr/bin/exec-suid -- /usr/bin/python3 -I` (directives first!), and the leaf is named
`challenge/cimg.j2` so it renders to `/challenge/cimg` (no extension) — the exec-suid
shebang both makes it SUID-runnable and triggers black formatting (first line contains
`python`). `chmod 4755` it in the Dockerfile.
```
