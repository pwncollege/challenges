# V8 Learning 2 Module Plan

This module replaces the forward-only `v8/learning` ramp with a standalone
capability-first curriculum for the target triangle:

```text
CVE-2025-13226 + b/452605803
  -> CVE-2025-13226 + b/446113730
  -> CVE-2025-13228 + b/446113730
```

Design rule: do not assume anything taught in `v8/learning`.
Existing `learning`, `practice`, and modern `legacy` directories may be reused as
implementation sources, but this module must introduce the prerequisite concepts in
its own order.

## Status

This is a replacement-module draft, not a registered dojo module yet.

Current structural target:

- `learning-2/module.yml` contains 44 active challenge entries.
- The added `ramp-js-to-wasm-wrapper` bridge closes the wrapper-directionality
  prerequisite without assuming `v8/learning`.
- The imported-wrapper proof was specifically fixed to use a live
  dispatch-state probe under ASLR instead of a fixed `d8` address.
- The three capstone solves derive live process-image and stack/control-flow
  targets through the intended exploit path; they do not disable ASLR and do not
  use fixed `d8` or stack addresses.

## Pedagogy

The ramp works backward from capability to cause:

1. First show the final process-memory finish using a provided native primitive.
2. Then teach heap-cage offsets, tagged references, and the stable caged primitive contract.
3. Then show the dispatch-table escape effect, its live ASLR anchors, and the caged table fields that create it.
4. Then teach the Wasm and custom-descriptor bedrock needed for the first stages.
5. Then replace modeled descriptor access with the real CVE-2025-13226 caged primitive.
6. Then swap the second stage to b/446113730.
7. Then swap the first stage to CVE-2025-13228.

This ordering keeps the learner oriented around what each capability is for.
Whenever a callback would hide a concept that is necessary to reason about the next
level, the missing concept gets its own ramp before the callback is removed.

## Curriculum

### Process-Memory Finish From A Provided Primitive

1. `ramp-native32-qword-helpers`
   Concept: absolute 32-bit native primitives compose into little-endian qword helpers.
   Task: return `read64` and `write64` on top of provided `read32` / `write32`.
2. `ramp-absolute-read-helpers`
   Concept: qword reads need byte, word, and dword extraction.
   Task: implement unaligned `read8`, `read16`, and `read32`.
3. `ramp-absolute-write-helpers`
   Concept: byte-oriented writes need qword packing.
   Task: implement `writeBytes`.
4. `ramp-elf-program-headers`
   Concept: ELF program headers locate executable, writable, and dynamic regions.
   Task: parse the provided loaded ELF fixture.
5. `ramp-elf-dynamic-tables`
   Concept: dynamic-table records locate symbol, string, and relocation tables.
   Task: walk the fixture dynamic table.
6. `ramp-elf-plt-imports`
   Concept: PLT relocations resolve imported function targets.
   Task: resolve `syscall` and `exit`.
7. `ramp-executable-gadget-scan`
   Concept: the finish needs simple x86-64 return-chain gadgets.
   Task: scan executable memory for the expected gadgets.
8. `ramp-catflag-path-layout`
   Concept: `execve` needs a null-terminated C path string.
   Task: write `/challenge/catflag`.
9. `ramp-catflag-argv-layout`
   Concept: `execve` needs a null-terminated `argv` pointer array.
   Task: lay out `argv[0] = path`, `argv[1] = NULL`.
10. `ramp-syscall-chain-layout`
    Concept: the final transfer is a qword return chain.
    Task: lay out `syscall(59, path, argv, NULL)` and `exit(0)`.
11. `ramp-process-memory-chain`
    Concept: the finish must rebase live `d8` and stack leaks under ASLR.
    Task: compose the ELF parser, import resolver, gadget scan, path/argv layout, and return chain.

### Caged Primitive Bedrock

12. `ramp-v8-cage-boundary`
    Concept: heap-cage read/write is not process read/write.
    Task: mutate a proof field with guarded `Sandbox.MemoryView`.
13. `ramp-tagged-pointers`
    Concept: compressed heap-object references carry V8 tag bits.
    Task: untag a leaked reference and reach the same proof field.
14. `ramp-caged-rw-interface`
    Concept: first stages need one stable `read32(offset)` / `write32(offset, value)` interface.
    Task: normalize two provided caged primitive shapes.

### Dispatch Escape Backward From Its Effect

15. `ramp-import-wrapper-sig-state`
    Concept: b/452605803 needs copied imported-wrapper signature state before absolute reads work.
    Task: copy callback-exposed signature state and prove the absolute read.
16. `ramp-dispatch-state-aslr-anchors`
    Concept: the dispatch-state region contains live native anchors for the `d8` image and stack under ASLR.
    Task: derive the dispatch-state region, recover the live `d8` ELF base, and compute the return slot.
17. `ramp-wasm-table-dispatch-handle`
    Concept: `WebAssembly.Table` carries a caged `trusted_dispatch_table` handle.
    Task: copy one table handle into another table with guarded Sandbox access.
18. `ramp-table-grow-target-handle`
    Concept: the grow-stage target handle is derived from a dispatch-table stride.
    Task: compute the target handle and stage it in the grow table.

### Wasm And Custom-Descriptor Bedrock

19. `ramp-wasm-sectioned-module`
    Concept: Wasm modules are sectioned binaries.
    Task: assemble a validating module from provided sections.
20. `ramp-wasm-leb128-fields`
    Concept: Wasm integer fields use LEB128.
    Task: encode numeric fields used by generated modules.
21. `ramp-wasm-gc-struct-fields`
    Concept: Wasm GC structs encode mutable field storage.
    Task: encode a mutable `i32` struct field list.
22. `ramp-wasm-gc-ref-fields`
    Concept: Wasm GC reference fields point at heap type indexes.
    Task: encode a nullable reference field to an earlier type.
23. `ramp-wasm-recursive-type-groups`
    Concept: mutually dependent heap types live in recursive groups.
    Task: wrap related subtype definitions in one group.
24. `ramp-exact-ref-types`
    Concept: exact refs constrain the dynamic heap type, not only the supertype.
    Task: route exact and subtype-compatible references correctly.
25. `ramp-js-to-wasm-wrapper`
    Concept: a JS-to-Wasm wrapper can preserve an `externref` object.
    Task: pass a token object through a real Wasm externref export unchanged.
26. `ramp-js-values-as-wasm-refs`
    Concept: JS objects can sit in Wasm reference-typed state.
    Task: store and recover a token through `externref`.
27. `ramp-wasm-externref-table`
    Concept: Wasm tables preserve JS object identity.
    Task: store and recover an object through a table slot.
28. `ramp-wrapper-directionality`
    Concept: JS-to-Wasm and Wasm-to-JS wrappers are different boundary paths.
    Task: pass an `externref` through the import path.
29. `ramp-wasm-custom-descriptor-pair`
    Concept: a descriptor object describes a specific Wasm heap type.
    Task: create a descriptor and its described value.
30. `ramp-custom-desc-subtyping`
    Concept: descriptor and described type hierarchies must agree.
    Task: create a derived pair that passes base checks.
31. `ramp-wasm-custom-descriptor-cast`
    Concept: descriptor-checked casts use the descriptor operand.
    Task: classify values through two descriptor-checked paths.

### CVE-2025-13226 First Stage

32. `ramp-desc-confusion-effect`
    Concept: descriptor confusion changes how a value is interpreted.
    Task: retarget a modeled descriptor with guarded Sandbox access.
33. `ramp-desc-confusion-leak`
    Concept: wrong descriptor interpretation can expose a tagged heap reference.
    Task: turn a modeled descriptor leak into a proof-field write.
34. `ramp-desc-confusion-caged-rw`
    Concept: wrong-field access should become cage-offset read/write.
    Task: return normalized `read32` and `write32`.
35. `ramp-cve-2025-13226-leak`
    Concept: CVE-2025-13226 creates the wrong-layout view with a real custom-descriptor module.
    Task: trigger the bug and return the leaked tagged reference.
36. `ramp-cve-2025-13226-caged-rw`
    Concept: the 13226 wrong-layout view can be shaped into cage-offset read/write.
    Task: trigger the bug, calibrate the field, and return normalized caged helpers.
37. `chain-cve-2025-13226-452605803`
    Concept: full CVE-2025-13226 to b/452605803 chain under ASLR.
    Task: use the first-stage caged read/write, corrupt dispatch-table state, derive live native anchors, and run `/challenge/catflag`.

### Second-Stage Swap

38. `ramp-wasm-stale-dispatch-growth`
    Concept: b/446113730 leaves stale imported-wrapper dispatch state reachable after growth.
    Task: trigger growth and read the stale signature value.
39. `chain-cve-2025-13226-446113730`
    Concept: second-stage swap while keeping the CVE-2025-13226 first stage.
    Task: replace b/452605803 with b/446113730, derive live native anchors, and run `/challenge/catflag`.

### First-Stage Swap

40. `ramp-ref-get-desc`
    Concept: `ref.get_desc` exposes the descriptor associated with a Wasm reference.
    Task: extract the descriptor token.
41. `ramp-ref-get-desc-exactness`
    Concept: descriptor extraction must preserve exactness.
    Task: keep exact and generic descriptor paths separate.
42. `ramp-cve-2025-13228-ref-get-desc`
    Concept: CVE-2025-13228 misapplies exactness after descriptor extraction.
    Task: trigger the real `ref.get_desc` exactness confusion and leak the tagged reference.
43. `ramp-cve-2025-13228-caged-rw`
    Concept: the 13228 trigger reuses the same wrong-layout primitive shape.
    Task: return normalized caged helpers from the 13228 first stage.
44. `chain-cve-2025-13228-446113730`
    Concept: first-stage swap while preserving the b/446113730 escape.
    Task: replace CVE-2025-13226 with CVE-2025-13228, derive live native anchors, and run `/challenge/catflag`.

## Gap Audit

- The native finish is self-contained and appears before any V8-specific first stage.
- Sandbox/cage mechanics appear before learners must write caged dispatch-table fields.
- b/452605803 is introduced through its signature-state effect, then through the ASLR anchors exposed by that state, then through the table fields needed to create that effect.
- Wasm binary encoding and GC reference mechanics appear before custom-descriptor modules.
- A JS-to-Wasm wrapper bridge appears before the Wasm-to-JS directionality ramp.
- The native return-chain layout ramp names the multi-pop gadget consumption
  order before learners must write the chain.
- Modeled descriptor confusion appears before the real CVE-2025-13226 trigger.
- b/446113730 is introduced as a narrow second-stage swap after the learner already understands dispatch-table staging.
- CVE-2025-13228 is introduced as a narrow first-stage swap after descriptor extraction and exactness are already covered.
- The three capstones use live ASLR-derived anchors instead of copied
  fixed-address practice tails.
- Focused post-review check:
  `nix develop --command pwnshop test challenges/v8/learning-2/ramp-js-to-wasm-wrapper challenges/v8/learning/ramp-syscall-chain-layout`
  passed for 2 challenges / 4 testcases.
- Combined post-review full-suite check:
  `nix develop --command pwnshop test challenges/v8/learning challenges/v8/learning-2 --jobs 1 --timeout 300`
  passed for 96 challenges / 194 testcases.
