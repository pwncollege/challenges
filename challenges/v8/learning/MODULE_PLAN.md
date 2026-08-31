# V8 Learning Module Plan

This is the active plan for `challenges/v8/learning`.
It is the curriculum contract for a standalone modern V8 learning track.
Do not assume learners have completed `v8/learning-2`; `learning` and `learning-2`
are alternative tracks under consideration.

The module teaches a post-Turboshaft two-stage heap-sandbox escape shape:

```text
CVE-2026-7899 + issue 514157844
  -> CVE-2026-9973 + issue 514157844
  -> CVE-2026-9973 + issue 505751230
```

`CVE-2026-7899` and `CVE-2026-9973` are different Wasm/Turboshaft first stages.
Issue 514157844 and issue 505751230 are different WasmFX sandbox escapes.

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
  used by shared foundations and process-memory ramps that do not need a
  specific 2026 vulnerable revision.
- `488364a9dd4665b8ad1616abc404d251f39bd263`: April 22, 2026,
  used by `chain-cve-2026-7899-514157844` and the real CVE-2026-7899
  trigger, marker, `addrof`, reference-RW, and proof-object-write ramps.
- `c2eab5ee184d928140d72cfd4156c570913fa6ae`: May 12, 2026,
  used by `chain-cve-2026-9973-514157844`,
  `chain-cve-2026-9973-505751230`, the real CVE-2026-9973 trigger,
  marker, `addrof`, reference-RW, and proof-object-write ramps, the WasmFX
  escape ramps, and the live `d8` process-memory integration ramp.

## Pedagogy

This module now follows the same capability-first philosophy as `learning-2`,
but with the CVEs and WasmFX concepts from `learning`.
The ramp works backward from what the final exploit needs:

1. First show the native process-memory finish from a provided absolute
   `read32`/`write32` primitive.
2. Then teach the heap-cage primitive contract and guarded Sandbox access that
   the V8-specific corruption ramps use.
3. Then show the issue 514157844 imported-tag escape from guarded access to the
   WasmFX objects it corrupts.
4. Then teach the Wasm encoding, reference, GC-array, and optimized-tiering
   bedrock needed to understand the real first stages.
5. Then replace the modeled first-stage effects with the real CVE-2026-7899
   caged primitive and use it in the first capstone.
6. Then swap the first stage to CVE-2026-9973 while preserving the already-taught
   imported-tag escape.
7. Finally, keep the CVE-2026-9973 first stage and swap the escape to issue
   505751230.

This ordering gives learners working exploit capabilities early, then removes
helper layers only after the missing concepts have their own ramp.
Do not introduce a capability before the harness gives enough support for the
task to be one positive, gradable concept.

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
- Full capstone native tails keep ASLR enabled.
  They may use revision-specific metadata, gadget, and scratch offsets only
  after rebasing them from runtime leaks and validating the resulting addresses.

## Curriculum

### Process-Memory Finish From a Provided Primitive

1. `ramp-native32-qword-helpers`
   Concept: native 32-bit read/write primitives must be combined into 64-bit
   qword helpers.
   Task: build little-endian `read64` and `write64` on top of provided absolute
   `read32` and `write32`.
2. `ramp-absolute-read-helpers`
   Concept: a 64-bit absolute read primitive needs smaller unsigned read wrappers.
   Task: build unaligned `read8`, `read16`, and `read32` on top of `read64`.
3. `ramp-absolute-write-helpers`
   Concept: byte arrays must be packed before a 64-bit absolute write stores them.
   Task: build `writeBytes` that packs bytes into little-endian qwords and
   zero-pads the final partial qword.
4. `ramp-elf-program-headers`
   Concept: ELF program headers identify executable, writable, and dynamic regions.
   Task: parse the provided loaded-ELF process image's program-header table and
   return segment starts and sizes.
5. `ramp-elf-dynamic-tables`
   Concept: ELF dynamic-table records identify import-resolution tables.
   Task: walk tag/value entries to find the string, symbol, and PLT relocation
   tables.
6. `ramp-elf-plt-imports`
   Concept: PLT relocation records connect imported names to GOT slots and targets.
   Task: resolve the `syscall` and `exit` GOT slots and targets from the provided
   process image.
7. `ramp-executable-gadget-scan`
   Concept: simple 64-bit x86 ROP gadgets can be found by byte-pattern scanning.
   Task: scan the provided executable segment for the capstone `ret` and
   multi-pop argument-loader patterns.
8. `ramp-catflag-path-layout`
   Concept: `execve` receives its path as a null-terminated C string.
   Task: write `/challenge/catflag` into an absolute-write-shaped scratch region
   and return its address.
9. `ramp-catflag-argv-layout`
   Concept: `execve` receives `argv` as a null-terminated pointer array.
   Task: write `argv[0] = path` and `argv[1] = NULL`.
10. `ramp-syscall-chain-layout`
    Concept: the final control transfer is a qword return chain.
    Task: write the ret-aligned multi-pop chain for
    `syscall(59, path, argv, NULL)` followed by `exit(0)`.
11. `ramp-process-memory-chain`
    Concept: the final native stage can be discovered dynamically in the real
    running `d8` image.
    Task: start from live `d8` image and stack leaks plus absolute
    `read32`/`write32`, derive the ELF base and return-chain slot, parse the real
    program headers and dynamic table, resolve imports, rebase and validate the
    revision-specific gadgets, lay out `/challenge/catflag` and `argv`, and write
    the final return chain.

### Heap-Cage Primitive Contract

12. `ramp-v8-cage-boundary`
    Concept: a caged V8 heap write is weaker than a process-memory write.
    Task: derive a proof-field cage offset in a normal JS object and mutate it
    with guarded `Sandbox.MemoryView`.
13. `ramp-tagged-pointers`
    Concept: a leaked heap-object reference carries the low heap-object tag bit.
    Task: convert a tagged reference into an object start before writing the
    proof field.
14. `ramp-type-confusion-effect`
    Concept: type confusion can retarget an object-reference field.
    Task: retarget a frozen reference cell from a decoy object to the proof
    object, then call the normal proof method.
15. `ramp-caged-rw-interface`
    Concept: different first stages should normalize to one cage-offset contract.
    Task: adapt differently shaped caged primitives behind `read32` and
    `write32`.

### Issue 514157844 Imported-Tag Escape From Guarded Access

16. `ramp-wasmfx-tag-identity-field`
    Concept: a `WebAssembly.Tag` wrapper contains an internal identity field.
    Task: locate that field in real tag wrappers and copy one tag identity into
    another wrapper with guarded `Sandbox.MemoryView`.
17. `ramp-wasmfx-imported-tag-handler`
    Concept: imported WasmFX handlers match on tag identity.
    Task: instantiate a real WasmFX module whose handler catches a suspension
    because two tag identities were made equal.
18. `ramp-wasmfx-tag-native-leak`
    Concept: imported-tag confusion can reinterpret a Wasm reference as an
    integer pointer.
    Task: store the tagged proof-box pointer leaked by the native path.
19. `ramp-wasmfx-tag-native-read`
    Concept: imported-tag confusion can read through a leaked proof-box pointer.
    Task: convert the leaked pointer with the named helper and read the proof
    field.
20. `ramp-wasmfx-tag-native-write`
    Concept: imported-tag confusion can write through a leaked proof-box pointer.
    Task: convert the leaked pointer with the named helper and mutate the proof
    field.

### Wasm Encoding and Reference Foundations

21. `ramp-wasm-sectioned-module`
    Concept: a Wasm binary is a header plus typed sections.
    Task: wrap provided section bodies into a validating module that exports
    `answer()`.
22. `ramp-wasm-leb128-fields`
    Concept: Wasm integer fields use unsigned LEB128 encoding.
    Task: encode the numeric fields needed by a generated module.
23. `ramp-wasm-gc-struct-fields`
    Concept: a Wasm GC struct type encodes a field count plus per-field storage
    type and mutability.
    Task: encode one real struct type with mutable and immutable `i32` fields.
24. `ramp-wasm-gc-ref-fields`
    Concept: a Wasm GC reference field encodes `ref null` plus a heap type index.
    Task: encode one mutable nullable reference field to an earlier struct type.
25. `ramp-wasm-recursive-type-groups`
    Concept: related Wasm heap types can be defined in one recursive type group.
    Task: wrap two provided mutually referencing subtype definitions in one real
    recursive group entry.
26. `ramp-js-to-wasm-wrapper`
    Concept: a JS-to-Wasm wrapper can preserve an `externref` object.
    Task: pass a token object through a real Wasm externref export unchanged.
27. `ramp-js-values-as-wasm-refs`
    Concept: JavaScript objects can live in Wasm reference-typed state.
    Task: store a token object in a real mutable Wasm `externref` global.
28. `ramp-wasm-externref-table`
    Concept: Wasm reference table slots preserve JavaScript object identity.
    Task: store and recover a token object through a real `externref` table.
29. `ramp-wrapper-directionality`
    Concept: a Wasm-to-JS import call crosses the opposite boundary direction.
    Task: call a Wasm export that passes an `externref` into a JavaScript import
    and returns the import result.

### Wasm/Turboshaft First-Stage Bedrock

30. `ramp-wasm-optimized-tiering`
    Concept: the relevant Wasm bugs appear on the optimized Wasm path.
    Task: use V8's real Wasm tier-up intrinsic through a guarded helper and call
    the optimized export.
31. `ramp-wasm-gc-arrays`
    Concept: Wasm GC arrays have observable runtime length.
    Task: allocate real Wasm GC arrays and return their lengths.
32. `ramp-wasm-gc-array-elements`
    Concept: Wasm GC arrays have mutable typed element storage.
    Task: store provided probe values into already-created arrays and read them
    back through Wasm array operations.
33. `ramp-wasm-gc-array-shapes`
    Concept: a holder struct can retarget which array reference its methods follow.
    Task: create a holder for one array, retarget it to another, and return the
    holder observations.
34. `ramp-wasm-load-elim-effect`
    Concept: load elimination can reuse stale object identity across an update.
    Task: create real Wasm arrays and a holder, then use guarded
    `Sandbox.MemoryView` to retarget the holder's array-reference field so a
    holder write lands on the stale array.
35. `ramp-wasm-array-oob-to-caged-rw`
    Concept: an expanded neighboring Wasm array can become caged heap read/write.
    Task: use guarded `Sandbox.MemoryView` to expand a real Wasm array's length
    word, then normalize real OOB `array.get`/`array.set` operations into
    cage-offset `read32` and `write32`.

### CVE-2026-7899 First Stage

36. `ramp-cve-2026-7899-trigger`
    Concept: real CVE-2026-7899 can expand the victim Wasm array on the optimized
    Wasm path.
    Task: build and trigger the vulnerable module, then return exports whose
    `victim_read`/`victim_write` reach beyond the original array bounds.
37. `ramp-cve-2026-7899-marker`
    Concept: the expanded victim array can find the bridge holder by scanning for
    a marker field.
    Task: scan for the marker and derive the adjacent externref and
    typed-reference field indexes.
38. `ramp-cve-2026-7899-addrof`
    Concept: the bridge externref field leaks tagged V8 heap references for
    ordinary JavaScript objects.
    Task: return an `addrof(obj)` helper backed by `set_obj` and the expanded
    victim array's object-field index.
39. `ramp-cve-2026-7899-ref-rw`
    Concept: the bridge typed-reference field can retarget Wasm struct accessors
    to raw cage byte offsets.
    Task: create a typed Wasm probe struct, derive its field address, and return
    `read32Raw`/`write32Raw` helpers.
40. `ramp-cve-2026-7899-caged-rw`
    Concept: the CVE-2026-7899 pieces compose into the taught proof-object write
    contract.
    Task: mutate the same object-local proof target without `Sandbox` helpers.
41. `chain-cve-2026-7899-514157844`
    Concept: first complete 2026 Wasm load-elimination plus WasmFX chain.
    Task: trigger CVE-2026-7899, build caged read/write, use issue 514157844,
    reach native `read32`/`write32`, and run `/challenge/catflag`.

### CVE-2026-9973 First-Stage Swap

42. `ramp-cve-2026-9973-trigger`
    Concept: CVE-2026-9973's optimized loop trigger expands the exposed victim array.
    Task: build the real vulnerable Wasm module, trigger it, and return exports
    whose victim array supports out-of-bounds `victim_read`/`victim_write`.
43. `ramp-cve-2026-9973-marker`
    Concept: the expanded victim array can locate the bridge holder by scanning
    for a marker field.
    Task: scan for the marker and derive the adjacent externref and typed-ref
    field indexes.
44. `ramp-cve-2026-9973-addrof`
    Concept: the bridge externref field leaks tagged V8 heap references for
    normal JavaScript objects.
    Task: return an `addrof(obj)` helper backed by `set_obj` and the expanded
    victim array's object-field index.
45. `ramp-cve-2026-9973-ref-rw`
    Concept: the bridge typed-reference field can retarget Wasm struct accessors
    to raw cage byte offsets.
    Task: create a typed Wasm probe struct, derive its field address, and return
    `read32Raw`/`write32Raw` helpers.
46. `ramp-cve-2026-9973-caged-rw`
    Concept: the CVE-2026-9973 pieces compose into the same proof-object write
    contract as the prior first stage.
    Task: mutate the same object-local proof target without `Sandbox` helpers.
47. `chain-cve-2026-9973-514157844`
    Concept: swap the first stage while preserving the imported-tag escape.
    Task: replace CVE-2026-7899 with CVE-2026-9973 and reuse issue 514157844.

### Issue 505751230 Continuation Escape Swap

48. `ramp-wasmfx-cont-collision`
    Concept: a continuation box's reference field selects which continuation
    `resume` executes.
    Task: replace a static box's continuation reference with a colliding actual
    continuation reference, then resume the static box.
49. `ramp-wasmfx-cont-native-leak`
    Concept: a continuation mismatch can return a tagged Wasm reference as an
    integer pointer.
    Task: retarget the leak continuation pair and store the tagged proof-box
    pointer.
50. `ramp-wasmfx-cont-native-read`
    Concept: a forged reference can aim a continuation read pair at a process
    address.
    Task: use the leak helper, retarget the real read continuation pair, convert
    the proof-field address, and read the proof field.
51. `ramp-wasmfx-cont-native-write`
    Concept: a forged reference can aim a continuation write pair at a process
    address.
    Task: use the leak helper, retarget the real write continuation pair, convert
    the proof-field address, and mutate the proof field.
52. `chain-cve-2026-9973-505751230`
    Concept: swap the escape while preserving the CVE-2026-9973 first stage.
    Task: replace issue 514157844 with issue 505751230 and run
    `/challenge/catflag`.

## Gap Audit

- The native finish is self-contained and appears before any V8-specific first stage.
- Heap-cage mechanics and guarded Sandbox access appear before learners must
  inspect or mutate V8 object fields.
- Issue 514157844 is introduced through guarded access to its corrupted WasmFX
  state, so learners see the process-memory effect before replacing the guarded
  write with a real first-stage primitive.
- Wasm binary encoding and reference mechanics appear before learners synthesize
  the real CVE trigger modules.
- Modeled optimized-Wasm array effects appear before the real CVE-2026-7899
  trigger.
- The native return-chain layout ramp names the multi-pop gadget consumption
  order before learners must write the chain.
- CVE-2026-9973 is introduced as a narrow first-stage swap after the 7899 chain
  is complete.
- Issue 505751230 is introduced as a narrow escape swap after the imported-tag
  chain is complete.
- The three capstones use live ASLR-derived anchors instead of fixed-address
  native tails.

## Verification

Current structural expectations:

- `learning/module.yml` contains 52 active challenge entries.
- Every active challenge directory exists under `learning/`.
- No extra active challenge directories exist under `learning/`.
- Active challenge IDs fit the dojo parser's 32-character limit.
- Public tests are smoke checks, not solve writeups.
- Private tests execute the reference solve and check the real flag.
- `tools/dojo/parse-dojo-yml challenges/v8/dojo.yml` accepts the module.
- Focused post-review check:
  `nix develop --command pwnshop test challenges/v8/learning-2/ramp-js-to-wasm-wrapper challenges/v8/learning/ramp-syscall-chain-layout`
  passed for 2 challenges / 4 testcases.
- Combined post-review full-suite check:
  `nix develop --command pwnshop test challenges/v8/learning challenges/v8/learning-2 --jobs 1 --timeout 300`
  passed for 96 challenges / 194 testcases.

Current full-suite command:

```bash
nix develop -c pwnshop test \
  $(awk '/^  - id: /{print "challenges/v8/learning/" $3}' challenges/v8/learning/module.yml) \
  --jobs 1 --timeout 300
```

The combined post-review full-suite result above covers this module and
`learning-2`.
