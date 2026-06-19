# V8 Learning Module Plan

This is the active plan for `challenges/v8/learning`.
It is the curriculum contract for the modern V8 learning track, not a scratchpad for
inactive exploit families.

The module teaches a post-Turboshaft two-stage heap-sandbox escape shape.
The active order ramps directly into the first full chain, then introduces each
remaining capstone swap immediately before the capstone that uses it:

- `AX`: `chain-cve-2026-7899-514157844`
- `BX`: `chain-cve-2026-9973-514157844`
- `BY`: `chain-cve-2026-9973-505751230`

`A` and `B` are different Wasm/Turboshaft first stages.
`X` and `Y` are different WasmFX sandbox escapes.

## Scope

Active learning content lives in `learning/` and in `learning/module.yml`.
Pre-cutoff and superseded material belongs in `../legacy/`.
Post-cutoff experiments, alternate chains, and unresolved research notes belong in
`../practice/`.
This file should not track inactive ramp designs in detail.
Inactive material can come back only after it has a mechanically distinct, tested
capstone role and a one-concept ramp path.

## Modernity Cutoff

Use the March 25, 2025 V8 Turboshaft transition as the cutoff.
The [V8 Turboshaft transition post](https://v8.dev/blog/leaving-the-sea-of-nodes)
states that WebAssembly had moved to Turboshaft throughout its pipeline by then.

TurboFan still appears in V8 terminology.
That is not enough to disqualify a challenge by itself.
The active capstones here rely on post-cutoff Wasm/Turboshaft behavior, not the
old Sea-of-Nodes Wasm backend.

Active V8 revisions:

- `04a92d6a85419c705384a2fa9effd886fc30009b`: September 23, 2025,
  used by the shared foundation, Wasm encoding/reference, and process-memory
  ramps that do not need a specific 2026 vulnerable revision.
- `488364a9dd4665b8ad1616abc404d251f39bd263`: April 22, 2026,
  used by `chain-cve-2026-7899-514157844` and the real CVE-2026-7899
  trigger, marker, `addrof`, reference-RW, and proof-object-write ramps.
- `c2eab5ee184d928140d72cfd4156c570913fa6ae`: May 12, 2026,
  used by `chain-cve-2026-9973-514157844`,
  `chain-cve-2026-9973-505751230`, the real CVE-2026-9973 trigger,
  marker, `addrof`, reference-RW, and proof-object-write ramps, the WasmFX
  escape ramps, and the live `d8` process-memory integration ramp.

## Design Rules

- One challenge teaches one positive, gradable concept.
- If a capstone needs two new ideas, add another ramp.
- Negative results stay in planning prose, not in challenge mechanics.
- Foundational heap ramps use V8's official `Sandbox` API behind narrow guards.
- Guarded helpers expose only the API calls needed by the current concept.
- Guarded helpers should catch common mistakes with direct feedback.
- Heap-layout ramps make learners derive offsets from real objects at runtime.
- Later ramps may expose already-taught offsets or conversions as named helpers.
- Modeled ramps can model an API shape or composition contract, not an invented bug.
- Full capstones must trigger the real vulnerable V8 revision.
- Full capstones must not use ramp-only guarded `Sandbox` helpers.
- Sandbox-escape capstones finish by running `/challenge/catflag`.
- The final process-memory ramp practices dynamic native discovery against the
  real running `d8` image with ASLR enabled, from live image and stack leaks
  plus absolute `read32`/`write32`.
- Full capstone native tails keep ASLR enabled. They may use revision-specific
  metadata, gadget, and scratch offsets only after rebasing them from runtime
  leaks and validating the resulting addresses.

## Active Capstone Spine

The current capstone triangle is:

- `AX`: CVE-2026-7899 gives helper-free caged read/write, then issue 514157844
  uses imported-tag identity corruption to escape.
- `BX`: CVE-2026-9973 replaces the first stage, then issue 514157844 uses the
  same imported-tag identity escape.
- `BY`: CVE-2026-9973 stays fixed, then issue 505751230 replaces the escape with
  a continuation signature-hash collision.

The active teaching order is:

1. Foundation ramps from nothing to the modeled Wasm array OOB and caged
   read/write shape.
2. Real CVE-2026-7899 first-stage ramps, split into trigger, bridge discovery,
   `addrof`, reference retargeting, and proof-object write levels.
3. Issue 514157844 imported-tag ramps plus process-memory finishing ramps.
4. `AX`, the first full chain capstone.
5. The CVE-2026-9973 first-stage swap ramp, split into trigger, bridge discovery,
   `addrof`, reference retargeting, and proof-object write levels.
6. `BX`, the second full chain capstone.
7. The remaining issue 505751230 continuation escape swap ramps.
8. `BY`, the final full chain capstone.

## Active Ramp Contract

### Heap Sandbox Foundations

- `ramp-v8-cage-boundary`
  Concept: a caged V8 heap write is weaker than a process-memory write.
  Challenge: derive a proof-field cage offset in a normal JS object and mutate it
  with guarded `Sandbox.MemoryView`.
- `ramp-tagged-pointers`
  Concept: a leaked heap-object reference carries the low heap-object tag bit.
  Challenge: convert a tagged reference into an object start before writing the
  proof field.
- `ramp-type-confusion-effect`
  Concept: type confusion can retarget an object-reference field.
  Challenge: retarget a frozen reference cell from a decoy object to the proof
  object, then call the normal proof method.
- `ramp-caged-rw-interface`
  Concept: different first stages should normalize to one cage-offset contract.
  Challenge: adapt differently shaped caged primitives behind `read32` and
  `write32`.

### Wasm Encoding and Reference Foundations

- `ramp-wasm-sectioned-module`
  Concept: a Wasm binary is a header plus typed sections.
  Challenge: wrap provided section bodies into a validating module that exports
  `answer()`.
- `ramp-wasm-leb128-fields`
  Concept: Wasm integer fields use unsigned LEB128 encoding.
  Challenge: encode the numeric fields needed by a generated module.
- `ramp-wasm-gc-struct-fields`
  Concept: a Wasm GC struct type encodes a field count plus per-field storage
  type and mutability.
  Challenge: encode one real struct type with mutable and immutable `i32`
  fields.
- `ramp-wasm-gc-ref-fields`
  Concept: a Wasm GC reference field encodes `ref null` plus a heap type index.
  Challenge: encode one mutable nullable reference field to an earlier struct
  type.
- `ramp-wasm-recursive-type-groups`
  Concept: related Wasm heap types can be defined in one recursive type group.
  Challenge: wrap two provided mutually referencing subtype definitions in one
  real recursive group entry.
- `ramp-js-to-wasm-wrapper`
  Concept: a JS-to-Wasm wrapper can preserve an `externref` object.
  Challenge: pass a token object through a real Wasm externref export unchanged.
- `ramp-js-values-as-wasm-refs`
  Concept: JavaScript objects can live in Wasm reference-typed state.
  Challenge: store a token object in a real mutable Wasm `externref` global.
- `ramp-wasm-externref-table`
  Concept: Wasm reference table slots preserve JavaScript object identity.
  Challenge: store and recover a token object through a real `externref` table.
- `ramp-wrapper-directionality`
  Concept: a Wasm-to-JS import call crosses the opposite boundary direction.
  Challenge: call a Wasm export that passes an `externref` into a JavaScript
  import and returns the import result.

### CVE-2026-7899 First-Stage Ramps

- `ramp-wasm-optimized-tiering`
  Concept: the relevant Wasm bugs appear on the optimized Wasm path.
  Challenge: use V8's real Wasm tier-up intrinsic through a guarded helper and
  call the optimized export.
- `ramp-wasm-gc-arrays`
  Concept: Wasm GC arrays have observable runtime length.
  Challenge: allocate real Wasm GC arrays and return their lengths.
- `ramp-wasm-gc-array-elements`
  Concept: Wasm GC arrays have mutable typed element storage.
  Challenge: store provided probe values into already-created arrays and read
  them back through Wasm array operations.
- `ramp-wasm-gc-array-shapes`
  Concept: a holder struct can retarget which array reference its methods follow.
  Challenge: create a holder for one array, retarget it to another, and return
  the holder observations.
- `ramp-wasm-load-elim-effect`
  Concept: load elimination can reuse stale object identity across an update.
  Challenge: create real Wasm arrays and a holder, then use guarded
  `Sandbox.MemoryView` to retarget the holder's array-reference field so a
  holder write lands on the stale array.
- `ramp-wasm-array-oob-to-caged-rw`
  Concept: an expanded neighboring Wasm array can become caged heap read/write.
  Challenge: use guarded `Sandbox.MemoryView` to expand a real Wasm array's
  length word, then normalize real OOB `array.get`/`array.set` operations into
  cage-offset `read32` and `write32`.
- `ramp-cve-2026-7899-trigger`
  Concept: real CVE-2026-7899 can expand the victim Wasm array on the optimized
  Wasm path.
  Challenge: build and trigger the vulnerable module, then return exports whose
  `victim_read`/`victim_write` reach beyond the original array bounds.
- `ramp-cve-2026-7899-marker`
  Concept: the expanded victim array can find the bridge holder by scanning for
  a marker field.
  Challenge: scan for the marker and derive the adjacent externref and
  typed-reference field indexes.
- `ramp-cve-2026-7899-addrof`
  Concept: the bridge externref field leaks tagged V8 heap references for
  ordinary JavaScript objects.
  Challenge: return an `addrof(obj)` helper backed by `set_obj` and the expanded
  victim array's object-field index.
- `ramp-cve-2026-7899-ref-rw`
  Concept: the bridge typed-reference field can retarget Wasm struct accessors
  to raw cage byte offsets.
  Challenge: create a typed Wasm probe struct, derive its field address, and
  return `read32Raw`/`write32Raw` helpers.
- `ramp-cve-2026-7899-caged-rw`
  Concept: the CVE-2026-7899 pieces compose into the taught proof-object write
  contract.
  Challenge: mutate the same object-local proof target without `Sandbox`
  helpers.

### Issue 514157844 Imported-Tag Escape Ramps

- `ramp-wasmfx-tag-identity-field`
  Concept: a `WebAssembly.Tag` wrapper contains an internal identity field.
  Challenge: locate that field in real tag wrappers and copy one tag identity
  into another wrapper.
- `ramp-wasmfx-imported-tag-handler`
  Concept: imported WasmFX handlers match on tag identity.
  Challenge: instantiate a real WasmFX module whose handler catches a suspend
  because two tag identities were made equal.
- `ramp-wasmfx-tag-native-leak`
  Concept: imported-tag confusion can reinterpret a Wasm reference as an integer
  pointer.
  Challenge: store the tagged proof-box pointer leaked by the native path.
- `ramp-wasmfx-tag-native-read`
  Concept: imported-tag confusion can read through a leaked proof-box pointer.
  Challenge: convert the leaked pointer with the named helper and read the proof
  field.
- `ramp-wasmfx-tag-native-write`
  Concept: imported-tag confusion can write through a leaked proof-box pointer.
  Challenge: convert the leaked pointer with the named helper and mutate the
  proof field.

### Process-Memory Escape Ramps

- `ramp-native32-qword-helpers`
  Concept: native 32-bit read/write primitives must be combined into 64-bit
  qword helpers.
  Challenge: build little-endian `read64` and `write64` on top of provided
  absolute `read32` and `write32`.
- `ramp-absolute-read-helpers`
  Concept: a 64-bit absolute read primitive needs smaller unsigned read wrappers.
  Challenge: build unaligned `read8`, `read16`, and `read32` on top of `read64`.
- `ramp-absolute-write-helpers`
  Concept: byte arrays must be packed before a 64-bit absolute write stores them.
  Challenge: build `writeBytes` that packs bytes into little-endian qwords and
  zero-pads the final partial qword.
- `ramp-elf-program-headers`
  Concept: ELF program headers identify executable, writable, and dynamic regions.
  Challenge: parse the provided loaded-ELF process image's program-header table
  and return segment starts and sizes.
- `ramp-elf-dynamic-tables`
  Concept: ELF dynamic-table records identify import-resolution tables.
  Challenge: walk tag/value entries to find the string, symbol, and PLT
  relocation tables.
- `ramp-elf-plt-imports`
  Concept: PLT relocation records connect imported names to GOT slots and targets.
  Challenge: resolve the `syscall` and `exit` GOT slots and targets from the
  provided process image.
- `ramp-executable-gadget-scan`
  Concept: simple 64-bit x86 ROP gadgets can be found by byte-pattern scanning.
  Challenge: scan the provided executable segment for the capstone `ret` and
  multi-pop argument-loader patterns.
- `ramp-catflag-path-layout`
  Concept: `execve` receives its path as a null-terminated C string.
  Challenge: write `/challenge/catflag` into an absolute-write-shaped scratch
  region and return its address.
- `ramp-catflag-argv-layout`
  Concept: `execve` receives `argv` as a null-terminated pointer array.
  Challenge: write `argv[0] = path` and `argv[1] = NULL`.
- `ramp-syscall-chain-layout`
  Concept: the final control transfer is a qword return chain.
  Challenge: write the ret-aligned multi-pop chain for
  `syscall(59, path, argv, NULL)` followed by `exit(0)`.
- `ramp-process-memory-chain`
  Concept: the final native stage can be discovered dynamically in the real
  running `d8` image.
  Challenge: start from live `d8` image and stack leaks plus absolute
  `read32`/`write32`, derive the ELF base and return-chain slot, parse the real
  program headers and dynamic table, resolve imports, rebase and validate the
  revision-specific multi-pop and leading `ret` gadgets, lay out
  `/challenge/catflag` and `argv` in writable process memory, and write the final
  ret-aligned multi-pop return chain.

### First Chain Capstone

- `chain-cve-2026-7899-514157844`
  Concept: first complete 2026 Wasm load-elimination plus WasmFX chain.
  Challenge: trigger CVE-2026-7899, build caged read/write, use issue 514157844,
  reach native `read32`/`write32`, and run `/challenge/catflag`.

### CVE-2026-9973 First-Stage Swap

- `ramp-cve-2026-9973-trigger`
  Concept: CVE-2026-9973's optimized loop trigger expands the exposed victim array.
  Challenge: build the real vulnerable Wasm module, trigger it, and return exports
  whose victim array supports out-of-bounds `victim_read`/`victim_write`.
- `ramp-cve-2026-9973-marker`
  Concept: the expanded victim array can locate the bridge holder by scanning for
  a marker field.
  Challenge: scan for the marker and derive the adjacent externref and typed-ref
  field indexes.
- `ramp-cve-2026-9973-addrof`
  Concept: the bridge externref field leaks tagged V8 heap references for normal
  JavaScript objects.
  Challenge: return an `addrof(obj)` helper backed by `set_obj` and the expanded
  victim array's object-field index.
- `ramp-cve-2026-9973-ref-rw`
  Concept: the bridge typed-reference field can retarget Wasm struct accessors to
  raw cage byte offsets.
  Challenge: create a typed Wasm probe struct, derive its field address, and return
  `read32Raw`/`write32Raw` helpers.
- `ramp-cve-2026-9973-caged-rw`
  Concept: the CVE-2026-9973 pieces compose into the same proof-object write
  contract as the prior first stage.
  Challenge: mutate the same object-local proof target without `Sandbox` helpers.

### Second Chain Capstone

- `chain-cve-2026-9973-514157844`
  Concept: swap the first stage while preserving the imported-tag escape.
  Challenge: replace CVE-2026-7899 with CVE-2026-9973 and reuse issue 514157844.

### Issue 505751230 Continuation Escape Swap

- `ramp-wasmfx-cont-collision`
  Concept: a continuation box's reference field selects which continuation
  `resume` executes.
  Challenge: replace a static box's continuation reference with a colliding
  actual continuation reference, then resume the static box.
- `ramp-wasmfx-cont-native-leak`
  Concept: a continuation mismatch can return a tagged Wasm reference as an
  integer pointer.
  Challenge: retarget the leak continuation pair and store the tagged proof-box
  pointer.
- `ramp-wasmfx-cont-native-read`
  Concept: a forged reference can aim a continuation read pair at a process
  address.
  Challenge: use the already-taught leak helper, retarget the real read
  continuation pair, convert the proof-field address, and read the proof field.
- `ramp-wasmfx-cont-native-write`
  Concept: a forged reference can aim a continuation write pair at a process
  address.
  Challenge: use the already-taught leak helper, retarget the real write
  continuation pair, convert the proof-field address, and mutate the proof field.

### Final Chain Capstone

- `chain-cve-2026-9973-505751230`
  Concept: swap the escape while preserving the CVE-2026-9973 first stage.
  Challenge: replace issue 514157844 with issue 505751230 and run
  `/challenge/catflag`.

## Verification

Current structural expectations:

- `learning/module.yml` contains 52 active challenge entries.
- Every active challenge directory exists under `learning/`.
- No extra active challenge directories exist under `learning/`.
- Active challenge IDs fit the dojo parser's 32-character limit.
- Public tests are smoke checks, not solve writeups.
- Private tests execute the reference solve and check the real flag.
- `tools/dojo/parse-dojo-yml challenges/v8/dojo.yml` accepts the module.

Current full-suite command:

```bash
nix develop -c pwnshop test \
  $(awk '/^  - id: /{print "challenges/v8/learning/" $3}' challenges/v8/learning/module.yml) \
  --jobs 1 --timeout 300
```

Most recent recorded full-suite result in this file predates the current
52-challenge split and should not be cited as a current full-module pass:

```text
All tests passed (48 challenges, 97 testcases)
```

Focused result after adding the per-concept CVE-2026-9973 ramp from real trigger
to proof-object write:

```text
All tests passed (5 challenges, 10 testcases)
```

Focused result after adding the process-memory integration ramp that composes
the prior native read/write, ELF parsing, gadget-scan, path/argv, and
return-chain layout levels:

```text
All tests passed (11 challenges, 22 testcases)
```

Focused result after removing retry loops from the three capstone private tests
so each reference exploit must produce the flag on its first run.
This focused command was run twice consecutively:

```text
All tests passed (3 challenges, 6 testcases)
```

Focused result after replacing pure process-memory helper ramps with the
deterministic loaded-ELF process image:

```text
All tests passed (7 challenges, 14 testcases)
```

Focused result after aligning process-memory harness names and descriptions with
the deterministic process-image fixture boundary:

```text
All tests passed (7 challenges, 14 testcases)
```

Focused result after making the capstone fixed-offset native stage deterministic
through the shared runner:

```text
All tests passed (3 challenges, 6 testcases)
```

Focused result after renaming the real-CVE proof target from absolute
`proofFieldOffset` to object-local `proofFieldDelta`:

```text
All tests passed (2 challenges, 4 testcases)
```

Focused result after clarifying the program-header return shape and capstone
sandbox-boundary notes:

```text
All tests passed (1 challenges, 2 testcases)
```

Focused result after removing unnecessary `--sandbox-testing` from the pure
layout drills (`ramp-catflag-path-layout`, `ramp-catflag-argv-layout`, and
`ramp-syscall-chain-layout`):

```text
All tests passed (3 challenges, 6 testcases)
```

Focused result after tightening `ramp-wasm-leb128-fields` so every encoded value
is checked as an unsigned Wasm field supplied by the harness, including direct
feedback for fixed-width little-endian encodings, then rerunning the full
Wasm/reference foundation group:

```text
All tests passed (9 challenges, 18 testcases)
```

Focused result after tightening `ramp-wasmfx-cont-collision` so the
stored resume token must match the retargeted `resume` wrapper return value:

```text
All tests passed (1 challenges, 2 testcases)
```

Focused result after tightening first-stage validator state flow in
`ramp-wasm-optimized-tiering` and `ramp-wasm-load-elim-effect`:

```text
All tests passed (2 challenges, 4 testcases)
```

Focused result after clarifying the modeled first-stage effect boundary, the
tagged-reference handoff, and the matching harness feedback in the real CVE
caged-write ramps:

```text
All tests passed (4 challenges, 8 testcases)
```

Focused result after tightening WasmFX helper value flow in
`ramp-wasmfx-imported-tag-handler`, `ramp-wasmfx-tag-native-read`,
`ramp-wasmfx-tag-native-write`,
`ramp-wasmfx-cont-native-read`, and
`ramp-wasmfx-cont-native-write`:

```text
All tests passed (5 challenges, 10 testcases)
```

Focused result after tightening the WasmFX escape ramp boundary so the
continuation-collision level proves retargeted execution without exposing the
leak as that level's required learner variable, and after clarifying the
helperized field-address/reference conversions:

```text
All tests passed (9 challenges, 18 testcases)
```

Focused result after making the Wasm/Turboshaft first-stage observation levels
name their required return fields in both DESCRIPTION text and validator
feedback, then rerunning the full first-stage group:

```text
All tests passed (8 challenges, 16 testcases)
```

Focused result after naming the exact return fields in the ELF and gadget-scan
process-memory ramp descriptions, then rerunning the full process-memory group:

```text
All tests passed (10 challenges, 20 testcases)
```

Focused result after making the recursive-type-group DESCRIPTION explicitly name
the provided `api.REC` wrapper constant, then rerunning the full Wasm/reference
foundation group:

```text
All tests passed (9 challenges, 18 testcases)
```

Focused result after clarifying the available guarded Sandbox APIs in the tagged
pointer and type-confusion foundation descriptions, then rerunning the full heap
foundation group:

```text
All tests passed (4 challenges, 9 testcases)
```

Focused result after aligning the process-memory gadget and return-chain ramps
with the multi-pop argument-loader shape used by the capstones:

```text
All tests passed (3 challenges, 6 testcases)
```

Focused result after clarifying the capstone native-finish bridge and rerunning
the three active capstones:

```text
All tests passed (3 challenges, 6 testcases)
```

Focused result after replacing the synthetic final process-memory composition
with the live `d8` dynamic native-finish ramp:

```text
All tests passed (11 challenges, 22 testcases)
```

Focused result after clarifying exact API handoffs in the CVE marker/`addrof`
ramps, the WasmFX tag-identity wording, and the live process-memory integration
ramp:

```text
All tests passed (6 challenges, 12 testcases)
```

Focused result after clarifying the WasmFX-to-native read/write bridge, the
global helper handoff in the modeled Wasm array OOB ramp, and the live
process-memory contract:

```text
All tests passed (12 challenges, 24 testcases)
```

Focused result after adding the first-use WAT-to-JS tooling bridge in the real
CVE trigger ramps, distinguishing address/size access from `MemoryView` access
in the modeled Wasm array OOB ramp, and carrying the leading `ret` gadget
requirement through the native-chain layout descriptions:

```text
All tests passed (5 challenges, 10 testcases)
```

Focused result after clarifying unaligned sub-qword reads and carrying the
ret-aligned native-finish handoff into the active capstone descriptions:

```text
All tests passed (4 challenges, 8 testcases)
```

Full learning-suite result after the blue-belt curriculum bridge review and
fixes:

```text
All tests passed (52 challenges, 105 testcases)
```

Full learning-suite result after removing the final process-memory page-scan
affordance and the final capstone retry loop:

```text
All tests passed (52 challenges, 105 testcases)
```

Full learning-suite result after making the CVE-2026-9973 caged-write reference
solve self-contained:

```text
All tests passed (52 challenges, 105 testcases)
```
