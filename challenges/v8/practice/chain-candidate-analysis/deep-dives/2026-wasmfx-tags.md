# CVE-2026 WasmFX Tags-Table Chain Deep Dive

Generated: 2026-06-03.

Scope: `CVE-2026-7899 / b/505481948`, `CVE-2026-9973 / b/509268941`, `b/513009811`, and `CVE-2026-9896 / b/508811474` as first-stage candidates paired with the WasmFX tags-table hardening tracked under `b/505751230` and `b/514157844`.

Inputs used:

- Local reports: `CVE_ISSUE_CAPABILITY_INDEX.md`, `NON_CVE_RELEVANT_ISSUES.md`, `chain-candidate-analysis/INDEX.md`, and `chain-candidate-analysis/2026-h1.md`.
- Local V8 history at `/home/yans/code/v8`. The V8 worktree has unrelated local edits, so all evidence below is from `git show`, `git log`, and `git grep`; no checkout/reset was performed.

## Verdict Summary

| Variant | Verdict | Best target revision | Why |
| --- | --- | --- | --- |
| `CVE-2026-7899 + WasmFX tags table` | **BUILT / ACCEPTED** | `488364a9dd4665b8ad1616abc404d251f39bd263` (`9c0c3018761681a8ea2e4c1bf26d6a04ec46f3b8^`) | Full helper-free chain now exists: CVE-2026-7899 expands a neighboring Wasm array into caged RW; corrupted imported `WebAssembly.Tag` identity seeds a mismatched WasmFX tag table and yields native RW. |
| `CVE-2026-9973 + WasmFX tags table / continuation variant` | **BUILT / ACCEPTED** | `c2eab5ee184d928140d72cfd4156c570913fa6ae` (`55cc1df03832e742cba83a2491fc5a13031be0f3^`) | Full helper-free chains now exist: CVE-2026-9973 expands a neighboring Wasm array into caged RW; the accepted second stages cover imported-tag identity confusion and continuation signature-hash collision. The direct continuation-signature-confusion pairing with `b/502229895` was attempted and dropped because this target already has dynamic continuation signature checks. |
| `b/513009811 + WasmFX tags table` | **HOLD** | `ee8516cec0729a54d7a6b530730a93862c4f7805` (`05858aaece5ecda66f5312d069d544e7ef36f2ff^`) | Strong compiler bug class involving `LoadTrustedPointer` aliasing, but current regression only proves wrong representation/load-elimination behavior, not a reusable caged RW primitive. Better second-stage revision than CVE-2026-9973 because later WasmFX signature fixes have landed. |
| `CVE-2026-9896 + WasmFX tags table` | **DROP for this chain** | `fd04a1e0b6c915a634984641271c793cdaf80bc5` (`00f6ecd8a7cca6911789a11b7a7b01aaf41f925b^`) | The bug is a Maglev concurrent-GC race causing `DeoptimizationLiteralArray` OOB writes. It is real OOB-write evidence, but timing-sensitive, not Wasm-local, and not obviously steerable into the tags-table path helper-free. |

Overall recommendation: keep the family through the implemented
`chain-cve-2026-7899-514157844`, `chain-cve-2026-9973-514157844`,
and `chain-cve-2026-9973-505751230` challenges. Drop
`chain-cve-2026-9973-502229895`: the `CVE-2026-9973` target is after
`1947e8a7337`, so WasmFX continuation dynamic signature checks reject the
direct `b/502229895` confusion with `RuntimeError: function signature mismatch`.
Treat `b/513009811` as a backup research path only. Drop `CVE-2026-9896` from
the WasmFX-tags chain unless a separate deterministic caged arbitrary-write
exploit appears.

## Overlap

Second-stage hardening landed at:

- `e8baffef1a07eb566572447b26442ad44df52a50` on 2026-06-02, `[wasm] Move tags table to trusted space`, bugs `505751230,514157844`.
- Parent: `a2cad09e04ec515383f984a0efc449c223b2a3b4`, 2026-06-03T06:58:21-07:00 in local history.

First-stage fixes:

- `00f6ecd8a7cca6911789a11b7a7b01aaf41f925b`, 2026-05-05, `[maglev] Fix deopt literals IdentityMap race during GC`, fixed `508811474`.
- `bb38f8914db99bd3bed6758132b104a9af00ca04`, 2026-04-23, `[wasm][turboshaft] Fix Phi handling in Wasm Load Elimination`, fixed `505481948`.
- `55cc1df03832e742cba83a2491fc5a13031be0f3`, 2026-05-11, `[wasm][turboshaft] Fix Phi handling in Load Elimination some more`, fixed `509268941`.
- `05858aaece5ecda66f5312d069d544e7ef36f2ff`, 2026-05-21, `[wasm] Fix AssertNotNull lowering vs. load elimination`, fixed `513009811`. Follow-up `8a885ed63641d4b0bfb4d8d9aaddc21104614b35` on 2026-05-27 also references `513009811` and introduces a dedicated `MemoryRepresentation` for `LoadTrustedPointer`.

The vulnerable overlap exists for all three first stages because the tags table was not moved to trusted space until after all three first-stage fixes. The useful overlap ends at the first-stage fix for each variant.

## WasmFX Availability

WasmFX is implemented and available on x64 in the relevant revisions, but it is disabled by default:

- `src/wasm/wasm-feature-flags.h` lists `wasmfx` as an experimental Wasm feature, `V(wasmfx, "core stack switching", false)`.
- Tests that exercise this path use `--experimental-wasm-wasmfx`.
- The pwn.college common runner currently invokes `/challenge/d8` without this flag, so a challenge would need a custom `run.j2`.
- The module common `args.gn` currently has `v8_enable_sandbox = false`; a real heap-sandbox chain challenge must override this and build with the sandbox enabled.

This does not block a challenge, but it means the candidate is not drop-in compatible with the current common challenge template.

## Second-Stage Tags-Table Path

The `e8baffef` commit message is explicit:

- Legacy Wasm exception values use a `FixedArray`, so tag-table tampering stays sandbox-contained.
- WasmFX parameters use a stack buffer, and pointers are stored uncompressed.
- An incorrect tag can forge out-of-sandbox references or cause stack-buffer overflows.
- `WasmExceptionTag` objects themselves remain untrusted; their identity/address is the sensitive value stored in the tags table.

Before `e8baffef`, `WasmTrustedInstanceData` had:

- `DECL_OPTIONAL_ACCESSORS(tags_table, Tagged<FixedArray>)`
- `kTagsTableOffset` listed as a normal tagged field.
- `module-instantiate.cc` allocated it with `NewFixedArray(tags_count, AllocationType::kOld)`.
- Imported/local tags were written directly into `trusted_data_->tags_table()->set(...)`.

After `e8baffef`, this becomes:

- `DECL_PROTECTED_POINTER_ACCESSORS(tags_table, TrustedFixedArray)`
- `kProtectedTagsTableOffset` listed as a protected field.
- Allocation uses a trusted fixed array path.

So the path is real: a caged RW primitive can target a sandbox `FixedArray` that controls tag identity used by WasmFX stack-buffer parameter packing/unpacking.

Construction result:

- The accepted challenge avoids a direct heap scan for `tags_table`. It corrupts
  an exported `WebAssembly.Tag` wrapper's sandbox `tag` field before importing
  it into a fresh WasmFX module; import validation uses the wrapper's canonical
  type index, while the vulnerable instance tag table is seeded from the
  corrupted `WasmExceptionTag` identity.
- The useful mismatch is `(ref box, i64)` versus `(i64, ref box)`. A `suspend`
  using static tag A is caught by the handler compiled for static tag B, so
  WasmFX stack-buffer packing/unpacking leaks an uncompressed pointer and treats
  an attacker-controlled integer as a reference.
- The final challenge uses no `--sandbox-testing`, no `Sandbox.MemoryView`, no
  native syntax, and no V8 helper patch.

## First-Stage Evidence

### CVE-2026-7899 / b/505481948

Fix: `bb38f8914db99bd3bed6758132b104a9af00ca04`.

Patch summary: Wasm load elimination kept stale Phi replacements when later
inputs proved non-identical. The regression `test/mjsunit/regress/wasm/regress-505481948.js`
uses WasmGC arrays and a holder struct. Optimized code can treat a loop Phi as
the earlier big array after the holder field changes to a small array, then
write index `3` through the wrong bounds state. Correct behavior is a
`kTrapArrayOutOfBounds` trap.

Assessment:

- The bug produces an optimized Wasm OOB-store shape and was remade into stable
  helper-free caged RW at `488364a9dd4665b8ad1616abc404d251f39bd263`.
- That target is also before the WasmFX tags-table trusted-space migration, so
  it overlaps the same accepted tag-identity second stage.
- This does not rescue `CVE-2026-7899 + b/503422307`; that dispatch-table-UAF
  trigger remains unproven. It establishes a different accepted second stage.

Verdict: **BUILT / ACCEPTED** as `chain-cve-2026-7899-514157844`.

### CVE-2026-9973 / b/509268941

Fix: `55cc1df03832e742cba83a2491fc5a13031be0f3`.

Patch summary: Wasm load elimination failed to clear dependent Phi replacements up front. The regression `test/mjsunit/regress/wasm/regress-509268941.js` constructs a WasmGC length-10 array, a length-1 array, and a struct holder. Optimized code can incorrectly elide the bounds check for `cur[3] = 0x1337` after `cur` changes to the small array. The fixed behavior is an `array out of bounds` trap before and after tier-up.

Assessment:

- This is the strongest first-stage variant because the regression directly encodes an out-of-bounds Wasm store.
- It is Wasm-local, so heap shaping around Wasm objects and the tags-table allocation is plausible.
- The target `55cc^` is before the May 13 WasmFX signature-index reland, so it may include additional WasmFX signature-hash weakness. Do not rely on that for the core tags-table chain; document it as target-revision noise.
- Construction update: the accepted challenge turns the OOB store into caged RW
  by expanding an adjacent Wasm array length, then uses an imported-tag
  corruption path to seed the vulnerable WasmFX tag table with the wrong
  `WasmExceptionTag` identity.
- Additional construction update: the same helper-free CVE-2026-9973 caged RW
  now also drives the `b/505751230` continuation signature-hash collision
  second stage. The direct `b/502229895` continuation-signature-confusion
  variant was attempted on the unmodified `55cc1df^` target and dropped because
  `1947e8a7337` dynamic continuation signature checks have already landed; the
  real engine throws `RuntimeError: function signature mismatch` at resume time.

Verdict: **BUILT / ACCEPTED** as `chain-cve-2026-9973-514157844`,
and `chain-cve-2026-9973-505751230`.

### b/513009811

Fix: `05858aaece5ecda66f5312d069d544e7ef36f2ff`; follow-up `8a885ed63641d4b0bfb4d8d9aaddc21104614b35`.

Patch summary: `AssertNotNull` used a trapping load at the same offset as a `LoadTrustedPointer` of `WasmInternalFunction::trusted_internal_`. Load elimination could alias a normal load with a trusted-pointer load even though they have different representations. The fix loads known object fields with representation-specific offsets and adds checks that normal loads do not alias `LoadTrustedPointerOp`.

Regression: `test/mjsunit/regress/wasm/regress-513009811.js` uses `--future`, a nullable function reference, `ref.as_non_null`, and `call_ref`. It verifies correct return behavior. It does not demonstrate an OOB write or controllable caged RW by itself.

Assessment:

- The bug class is security-relevant under the heap sandbox because confusing a trusted-pointer load with a normal load is exactly the kind of representation mismatch that can cross trust boundaries.
- The exploit primitive is not yet proven. It may produce wrong calls/trusted pointer confusion rather than convenient caged RW.
- Targeting `05858^` is cleaner for WasmFX than `55cc^`: the May 13 WasmFX signature-index fixes have landed and the tags table is still in sandbox.

Verdict: **HOLD** until a first-stage primitive is reproduced.

### CVE-2026-9896 / b/508811474

Fix: `00f6ecd8a7cca6911789a11b7a7b01aaf41f925b`.

Patch summary: Maglev used an `IdentityMap` for deopt literals and assigned IDs based on map size. Concurrent GC could shortcut/merge strings, rehash/shrink the map, corrupt IDs, and cause OOB writes in `DeoptimizationLiteralArray`. The regression is randomized and timing-sensitive, with `--expose-gc --allow-natives-syntax`.

Assessment:

- The first-stage bug has explicit OOB-write language and a regression test.
- It is a poor fit for this chain: not Wasm-local, not deterministic, and the corrupted array is internal compiler/deopt metadata rather than a direct caged RW surface.
- Pairing it with WasmFX tags would require first solving a separate reliable Maglev exploitation problem.

Verdict: **DROP for this WasmFX-tags chain**.

## Helper-Free Viability

The accepted helper-free second-stage path is:

1. Build a factory module exporting two tags whose parameter layouts differ in
   pointer/non-pointer order and size.
2. Corrupt the second exported `WebAssembly.Tag` wrapper's sandbox `tag` field
   to point at the first tag's `WasmExceptionTag`.
3. Instantiate a second module importing both tags. The imported module's
   vulnerable tag table receives mismatched tag identity while retaining the
   second tag's static signature for validation/code generation.
4. Trigger `suspend`/handler dispatch to leak an uncompressed pointer and forge
   an out-of-sandbox reference, then use that primitive for native RW and a ROP
   call to `/challenge/catflag`.

Known helper use to avoid:

- `--sandbox-testing`
- `--expose-memory-corruption-api`
- `Sandbox.MemoryView`
- direct C++ runtime helpers beyond standard d8 flags needed to expose WasmFX and optimization controls.

Accepted challenge flags:

- `--experimental-wasm-wasmfx`
- optimization/tiering stabilizers: `--nowasm-loop-unrolling`,
  `--nowasm-loop-peeling`, `--no-liftoff`, `--no-wasm-lazy-compilation`,
  `--wasm-tiering-budget=1`, `--wasm-wrapper-tiering-budget=1`,
  `--wasm-sync-tier-up`, and `--no-concurrent-recompilation`.

## Best Revision

Best accepted target for `CVE-2026-7899`: `488364a9dd4665b8ad1616abc404d251f39bd263`, the parent of `9c0c3018761681a8ea2e4c1bf26d6a04ec46f3b8`.

Rationale:

- CVE-2026-7899 is still vulnerable.
- The regression demonstrates a real optimized Wasm OOB store.
- WasmFX exists and is gated only by `--experimental-wasm-wasmfx`.
- The tags table is still a sandbox `FixedArray`.
- The target also predates the unrelated dispatch-table-UAF fix, but the
  accepted challenge does not rely on that unproven second stage.

Best accepted target for `CVE-2026-9973`: `c2eab5ee184d928140d72cfd4156c570913fa6ae`, the parent of `55cc1df03832e742cba83a2491fc5a13031be0f3`.

Rationale:

- CVE-2026-9973 is still vulnerable.
- The regression demonstrates a real optimized Wasm OOB store.
- WasmFX exists and is gated only by `--experimental-wasm-wasmfx`.
- The tags table is still a sandbox `FixedArray`.
- The second-stage trusted-space migration has not landed.

Alternative target for `b/513009811`: `ee8516cec0729a54d7a6b530730a93862c4f7805`, the parent of `05858aaece5ecda66f5312d069d544e7ef36f2ff`. Use this only if the `AssertNotNull` / `LoadTrustedPointer` bug can be turned into a real primitive; it has a cleaner WasmFX state because the May 13 signature-index fixes are already present.

Do not use `e8baffef^` as the target for this chain: it maximizes the second-stage vulnerable window, but all three first-stage fixes have already landed.

## Challenge Result

The challenges `chain-cve-2026-7899-514157844/`,
`chain-cve-2026-9973-514157844/`, and
`chain-cve-2026-9973-505751230/` were built with empty V8 patches and passed:

```bash
nix develop -c pwnshop test chain-cve-2026-7899-514157844 --jobs 1 --timeout 300
nix develop -c pwnshop test chain-cve-2026-9973-514157844 --jobs 1 --timeout 300
nix develop -c pwnshop test challenges/v8-exploitation/chain-cve-2026-9973-505751230
```

Result:

```text
All tests passed (1 challenges, 2 testcases)
```

`chain-cve-2026-9973-502229895/` was attempted and removed from the module
because the authentic unmodified target rejects the continuation confusion:

```text
RuntimeError: function signature mismatch
```
