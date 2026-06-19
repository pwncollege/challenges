# Early-H1 2025 First Stages + b/385775375 TypedArray Sort Deep Dive

Verdict: **Hold**, with one reusable **keep** component and several **drop** first-stage pairings.

The b/385775375 second stage is real and well evidenced: the fixing CL explicitly says it fixes a sandbox escape related to sorting TypedArrays, and the regression corrupts a TypedArray map byte before repeatedly calling `TypedArray.prototype.sort()`. The weak part is the first stage. The named Jan-Feb 2025 CVEs all have timeline overlap with the TypedArray-sort bug, but the public regressions I found do not demonstrate helper-free, targeted corruption of `Map::bit_field2` or an equivalent TypedArray/map state. Treat this family as a valid second-stage idea that needs a stronger first-stage PoC before becoming a challenge candidate.

## Sources Checked

- Local index rows: `CVE_ISSUE_CAPABILITY_INDEX.md`, `NON_CVE_RELEVANT_ISSUES.md`, `chain-candidate-analysis/2025-h1.md`, and `chain-candidate-analysis/INDEX.md`.
- Local V8 checkout: `/home/yans/code/v8`, read-only. It currently has unrelated local edits in `include/v8-internal.h` and `src/sandbox/sandboxed-pointer-inl.h`; I did not modify or revert them.
- Candidate output only: this file.

## Second Stage: b/385775375

Fix commit:

- `66bd3ee476b8be86faf209d13620b2f73024aa61`
- `2025-02-20 06:56:17 -0800`
- Subject: `[sandbox] Fix a sandbox escape related to sorting TypedArrays`
- Bug: `385775375`
- Files: `src/runtime/runtime-typedarray.cc`, `test/mjsunit/sandbox/regress-385775375.js`

The regression test is direct sandbox-escape evidence. It runs with `--sandbox-testing`, creates a large `Int32Array` over a `SharedArrayBuffer`, reads the array map through `Sandbox.MemoryView`, computes `bit_field2_addr = ar_map + 10`, and starts a worker that repeatedly flips that byte between its original value and `value ^ 0xff`. The main thread then calls `ar.sort()` 10,000 times.

That byte is not arbitrary. In V8, `Map::kBitField2Offset` stores `bit_field2`; `Map::Bits2::ElementsKindBits` live there. Relevant local source evidence:

- `src/objects/map.tq` has `bit_field2: MapBitFields2`.
- `src/objects/map.h` documents `[bit_field2]`.
- `src/objects/map-inl.h` reads/writes `Map::kBitField2Offset` and decodes `ElementsKindBits`.
- `src/objects/elements-kind.h` defines `kElementsKindBits = 6`.

The vulnerable pre-fix `Runtime_TypedArraySortFast` shape at `66bd3ee^` was:

- It read `size_t length = array->GetLength()` before copying.
- For shared buffers, it copied `array->GetByteLength()` bytes into a temporary `ByteArray` or C++ `std::vector<uint8_t>`.
- Under `DisallowGarbageCollection`, it switched on `array->type()`, which is map/elements-kind derived.
- It sorted `data .. data + length` as the corrupted `ctype`.
- On exit, it copied `array->GetByteLength()` bytes back.

The fix made the byte length a stable input and checked consistency with the type selected later:

- It hoisted `const size_t byte_length = array->GetByteLength()`.
- It used that byte length for temporary allocation and both copies.
- It moved `length = array->GetLength()` later.
- It added `SBXCHECK(length * sizeof(ctype) == byte_length)` inside each typed-array sort case.

So the second stage needs a first stage that can corrupt a live TypedArray map/type byte, or otherwise create the same mismatch between the stored byte length/length and the element type used by `sort()`. The public test's `Sandbox.MemoryView` write is a stand-in for that primitive, not part of a helper-free chain.

## Exact Overlap

The useful mainline overlap condition is simple: choose a revision before the first-stage fix and before `66bd3ee`. Every named CVE source fix below landed before `66bd3ee`, so the immediate parent of each source fix is a concrete overlap revision where b/385775375 is still unfixed.

| Candidate | Local index fix | Main/source fix | Source fix date | Concrete overlap revision | Overlap verdict |
| --- | --- | --- | --- | --- | --- |
| CVE-2025-0291 / b/383356864 | `e606275980b9` branch merge | `c84e01e92bfd` | 2024-12-13 06:13:41 -0800 | `c84e01e^ = a04649d147e6` | exact but weak |
| CVE-2025-0434 / b/374627491 | `5c3b50c26c50` | same | 2024-11-19 15:58:42 +0000 | `5c3b50c^ = bf31a08e262a` | exact but weak |
| CVE-2025-0611 / b/386143468 | `97e828af5cbc` branch merge | `b44bd24761f1` | 2025-01-09 01:46:37 -0800 | `b44bd24^ = 1be46f0e2e71` | exact but weak |
| CVE-2025-0612 / b/385155406 | `d35770876597` | same | 2025-01-07 05:22:59 -0800 | `d357708^ = 933009a52a9b` | exact but weak |
| CVE-2025-0445 / b/392521083 | `8834c16acfcc` branch merge | `ce071a295e54` | 2025-01-29 01:08:42 -0800 | `ce071a2^ = c0e150bb6f4d` | exact, hold-low |
| CVE-2025-0995 / b/391907159 | `19ad509f7b61` branch merge | `33ca4f51e5db` | 2025-01-31 01:32:22 -0800 | `33ca4f5^ = 6a906deec874` | exact, drop for this chain |
| CVE-2025-0998 / b/386857213 | `fd9d1daf420a` branch merge | `0242cac4b203` | 2025-02-05 12:54:30 -0800 | `0242cac^ = 97685852228e` | exact, drop |
| CVE-2025-0999 / b/394350433 | `f6961c4066a9` branch merge | `84a0e230dabc` | 2025-02-10 06:35:30 -0800 | `84a0e23^ = 1b27e4674f11` | exact, hold |

For each listed parent revision, `git merge-base --is-ancestor 66bd3ee <parent>` returned false. That confirms the TypedArray-sort fix is not already in the selected overlap revision. The first-stage introduction points remain unknown in the local index, so these are fix-parent overlap proofs, not full vulnerable-range proofs.

Branch nuance: the local CVE index often records branch-head merge fixes. For a mainline V8 challenge, the source fix is the better boundary. For a Chrome branch recreation, the branch merges remain useful dates, but I found no local branch backport of `66bd3ee` by grepping the V8 history for `385775375`.

## Named First-Stage CVEs

### CVE-2025-0445 / b/392521083

Source fix: `ce071a295e54b32bf7f03373da943678231cb1ee`, `2025-01-29 01:08:42 -0800`, `[runtime] Fix write barrier check in FastCloneJSObject`.

Evidence:

- The CL says it adds a missing check for a page being marked.
- It replaces a young-generation-only write-barrier skip with `TrySkipWriteBarrier`.
- It adds `Runtime_IsNoWriteBarrierNeeded` as a debug/fuzzing validation helper.
- The local CVE index labels it `Use after free in V8` and `HS-RW potential`.

Assessment: **Hold-low**. A write-barrier bug can plausibly become stale-object/UAF corruption, and the overlap with b/385775375 is exact. However, the public fix does not include a helper-free JS regression that writes an attacker-chosen byte to a chosen heap object, much less `TypedArray.map.bit_field2`. Keep it only if a separate first-stage exploit exists that turns the missed barrier into targeted in-cage write.

### CVE-2025-0995 / b/391907159

Source fix: `33ca4f51e5dbba9817eba16fd3249e66a880cf33`, `2025-01-31 01:32:22 -0800`, `[wasm] Replace {dead_code_} set with {is_dying_} bit`.

Evidence:

- The CL changes Wasm code GC lifetime tracking.
- It removes the global `dead_code_` set, adds an atomic `WasmCode::dying_`, and rejects dying wrappers from the import-wrapper cache.
- It adds `SBXCHECK(!compiled_wrapper || !compiled_wrapper->is_dying())` in `WasmDispatchTable::SetForWrapper`.
- The local CVE index labels it `Use after free in V8` and `HS-RW potential`.

Assessment: **Drop for this TypedArray-sort chain**. This may be interesting as a Wasm-code lifetime issue, possibly even a different sandbox-boundary investigation, but the public diff points at stale `WasmCode`/wrapper references, not arbitrary JS heap object writes. I found no public JS regression that can corrupt a TypedArray map byte. Pairing it with b/385775375 would require building a complete in-cage write primitive from private knowledge, so it is not a good concrete chain variant from the available evidence.

### CVE-2025-0998 / b/386857213

Source fix: `0242cac4b20305b03b74c2e9588003378eebeb77`, `2025-02-05 12:54:30 -0800`, `Fix out of bound string access`.

Evidence:

- The fix adds a length check in `GetOffsetTimeZone` after parsing a colon.
- The regression is only `assertThrows(() => new Intl.DateTimeFormat("en", {timeZone: "+09:"}), RangeError);`.
- The local CVE index labels it `Out of bounds memory access in V8` and `HS-R` / `HS-RW potential`.

Assessment: **Drop**. The public regression demonstrates an OOB read-shaped parser bug, not object corruption or a write primitive. It does not look capable of helper-free TypedArray/map corruption without additional non-public exploit work.

### CVE-2025-0999 / b/394350433

Source fix: `84a0e230dabc2c874a129c2280d6be4f45636225`, `2025-02-10 06:35:30 -0800`, `Reland "Lower the maximum JS parameter count"`.

Evidence:

- The original fix says the maximum JS parameter count was lowered to leave room for extra implicit call-node arguments, especially in wasm-to-JS wrappers where there is no bailout mechanism.
- The actual code changes `Code::kMaxArguments` from `(1 << 16) - 1` to `(1 << 16) - 10`.
- Several max-argument regressions are adjusted downward.
- The local CVE index labels it `Heap buffer overflow in V8` and `HS-RW potential`.

Assessment: **Hold**. This is the best of the named CVE pairings on public metadata because it is a heap-buffer-overflow class bug in compiler/call plumbing, and the overlap with b/385775375 is exact. Still, the public regression does not produce a ready `addrof`/write primitive or a targeted map-byte write. Hold it for deeper exploit reconstruction; do not promote it as a chain until the first-stage primitive is demonstrated without `Sandbox.MemoryView`.

## Similar Jan-Feb HS-RW Rows

The local index has adjacent Jan-Feb candidates beyond the four named CVEs. I checked the public commit evidence where it looked relevant.

| Row | Fix evidence | Public primitive evidence | Chain action |
| --- | --- | --- | --- |
| CVE-2025-0291 / b/383356864 | `c84e01e92bfd`, WasmGC type analyzer single-block loop fix | No public JS PoC in the CL; Wasm type-analysis correctness issue | Drop for this chain unless a Wasm GC exploit is found |
| CVE-2025-0434 / b/374627491 | `5c3b50c26c50`, interpreter hole-elision scope for switch jump tables | Regression is a TDZ/ReferenceError constructor case, no write primitive | Drop |
| CVE-2025-0611 / b/386143468 | `b44bd24761f1`, Maglev regalloc non-loop resumable-loop handling | No public JS regression in the CL; compiler state/register allocation bug | Hold only as generic compiler first-stage backlog |
| CVE-2025-0612 / b/385155406 | `d35770876597`, max-args check for bound-function inlining | Fix prevents oversized artificial frame/input count; no map corruption PoC | Hold-low |
| non-CVE b/391921972 | `bd10ccc8f3ef`, Liftoff memory bounds check debug-mode tagged-slot clobber | Debugging-mode Wasm stack-slot taggedness issue | Drop for release d8 chain |
| non-CVE b/381917890 | `bc9081f99d1c`, simulator stack-limit reset after overflow | Simulator-specific JSPI/Wasm regression | Drop for x64 release challenge |
| non-CVE b/395053819 | `f99c2e013acc`, string array-index hash overflow | Regression stores large numeric property names and checks values | Drop |
| non-CVE b/384959125 / b/396485545 | `2a7a04843046`, feedback for overflowed Smi adds | Regression gets optimized `NaN`; fixed 2025-02-20 02:15, about 4h41m before b/385 fix | Hold-low for compiler triage, not this chain |

The 2025-02-20 feedback row is the tightest non-CVE timing overlap: the parent of `2a7a0484` is before the b/385 fix by a few hours. But the public regression is type-feedback correctness, not a demonstrated in-cage write primitive.

## Helper-Free TypedArray/Map Corruption Requirement

The b/385 regression is not helper-free. It depends on:

- `--sandbox-testing`
- `new Sandbox.MemoryView(...)`
- `Sandbox.getAddressOf(ar)`
- A background `Worker` that flips the map byte directly

A real challenge chain must replace those with a first-stage primitive that can locate the target TypedArray/map and corrupt the same state. The minimum credible first-stage evidence would be one of:

- full in-cage arbitrary read/write, with `addrof` and a byte/word write to `Map::kBitField2Offset`;
- reliable object/map confusion that assigns a TypedArray an attacker-chosen map or elements kind;
- a direct TypedArray metadata corruption that makes `GetLength()` or `array->type()` inconsistent with `GetByteLength()`.

I did not find that evidence in the public regressions for CVE-2025-0445, CVE-2025-0995, CVE-2025-0998, CVE-2025-0999, or the adjacent Jan-Feb HS-RW rows. The local index's `HS-RW potential` label is useful for triage, but it is not enough to prove this specific second-stage handoff.

## Keep / Hold / Drop Variants

**Keep: b/385775375 as a second-stage primitive skeleton.** The TypedArray-sort bug is a real sandbox escape primitive once an attacker can corrupt `Map::bit_field2` or equivalent TypedArray type metadata. Preserve it as a reusable second-stage target.

**Hold: CVE-2025-0999 + b/385775375.** Best named pairing by bug class. Exact overlap exists at `84a0e230^ = 1b27e4674f11`, and the CVE class is heap buffer overflow. Needs first-stage exploit reconstruction.

**Hold-low: CVE-2025-0445 + b/385775375.** Exact overlap exists at `ce071a29^ = c0e150bb6f4d`; write-barrier/UAF class could become object corruption. Needs a public or locally reconstructed primitive.

**Hold-low: CVE-2025-0611, CVE-2025-0612, and non-CVE b/384959125/b/396485545.** These are plausible compiler/runtime first-stage backlog rows with exact timeline overlap, but no current evidence that they can target TypedArray map/type state.

**Drop for this chain: CVE-2025-0995.** Wasm code lifetime UAF evidence is not aligned with TypedArray map corruption. It may belong in a separate Wasm dispatch/code-pointer investigation.

**Drop: CVE-2025-0998.** Public evidence is an Intl string OOB read and exception regression, not a write primitive.

**Drop: CVE-2025-0291, CVE-2025-0434, non-CVE b/391921972, b/381917890, and b/395053819 for this chain.** The public evidence is too far from helper-free TypedArray/map corruption or is debug/simulator/string-correctness scoped.

## Recommendation

Do not build this as a challenge yet. The correct next step is first-stage reconstruction, not more timeline work. Start with CVE-2025-0999 and CVE-2025-0445 because they have the best public bug classes for producing in-cage corruption. Promote only if one can corrupt `Map::kBitField2Offset` or otherwise cause the same `length`/`byte_length`/`array->type()` inconsistency without `--sandbox-testing`.
