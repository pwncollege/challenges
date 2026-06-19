# 2026 Wasm Load-Elimination + Bytecode-Verifier Gaps Deep Dive

Generated: 2026-06-03.

Overall verdict: **Drop for challenge construction; hold-low for verifier research**.

The source overlap is real for several revisions: `CVE-2026-9973 / b/509268941` remains vulnerable before `55cc1df03832e742cba83a2491fc5a13031be0f3`, and `b/513009811` remains vulnerable until `05858aaece5ecda66f5312d069d544e7ef36f2ff`. The bytecode-verifier gaps are also real sandbox-labeled hardening commits. The chain falls down on the bridge: the strongest verifier tests require `--sandbox-testing`, `%GetBytecode`, `%InstallBytecode`, or unit-test-created `BytecodeArray` objects. A normal Wasm load-elimination OOB write is not shown to create or modify executable trusted bytecode helper-free.

## Sources Checked

- Local reports: `chain-candidate-analysis/INDEX.md`, `chain-candidate-analysis/2026-h1.md`, `chain-candidate-analysis/deep-dives/2026-wasm-loadelim-503422307.md`, `chain-candidate-analysis/deep-dives/2026-wasmfx-tags.md`, `CVE_ISSUE_CAPABILITY_INDEX.md`, and `NON_CVE_RELEVANT_ISSUES.md`.
- Local V8 checkout: `/home/yans/code/v8`, read-only. It has unrelated local edits in `include/v8-internal.h` and `src/sandbox/sandboxed-pointer-inl.h`; I did not modify or revert them.
- Evidence commands used were `git show`, `git log`, `git rev-parse`, `git merge-base --is-ancestor`, and source greps only.

## Variant Verdicts

| Variant | Verdict | Best target revision | Reason |
| --- | --- | --- | --- |
| `CVE-2026-9973 + b/507520268` | **Drop / hold-low** | `dbafd06731e4924b0f58eead66b0601c24c20235` (`bb07280e51d1be1a1cd3cef95151b2c4fccfdd75^`) | Exact source overlap exists and `WasmAllocateFeedbackVector` is still allowed by the verifier, but the only local regression uses `%GetBytecode`, `%InstallBytecode`, `--sandbox-testing`, and `--verify-bytecode-full`; the commit says the outcome was crashes/fuzzer cleanliness. |
| `CVE-2026-9973 + later Wasm intrinsic gaps` | **Hold-low** | `c2eab5ee184d928140d72cfd4156c570913fa6ae` (`55cc1df03832e742cba83a2491fc5a13031be0f3^`) | Best first-stage primitive evidence: the regression shows optimized WasmGC `array.set` can lose a bounds check. This revision is before `de8ca504`, `5873eb8`, and `b6e9fb8`, but after the `WasmAllocateFeedbackVector` fix. Still no helper-free bytecode publication path. |
| `b/513009811 + exception-handler verifier gaps` | **Hold-low** | `cf0711105ccf6e70fde62418c2214361138d4340` (`5873eb8fd9c86d9a977000a3255c46b1996df433^`) | The first-stage fix is still absent and the exception-handler reland is not present. However, `b/513009811` only proves a `Load`/`LoadTrustedPointer` aliasing bug, not a caged RW primitive, and the verifier sink is unit-test-only unless bytecode can be published. |
| `b/513009811 + broad Wasm-intrinsic verifier ban` | **Hold-low** | `d82d5bd8ad543679c22c8115b44fabacc8a662da` (`b6e9fb898e854239e7e1be3c48231a2180327aed^`) | First stage is still vulnerable and broad Wasm intrinsics are not yet denied by the verifier. Exception-handler checks and the two specific intrinsic blocklists have already landed. The same helper-free gap remains. |
| Any variant requiring `--sandbox-testing`, `Sandbox.MemoryView`, `%InstallBytecode`, or unit-test bytecode construction | **Drop for pwn.college challenge** | n/a | These are useful for V8 sandbox-verifier research but violate the helper-free challenge bar. |

## Fix Timeline And Overlap

First-stage fixes:

- `55cc1df03832e742cba83a2491fc5a13031be0f3`, committed 2026-05-12 13:49:05 -0700, `[wasm][turboshaft] Fix Phi handling in Load Elimination some more`, `Fixed: 509268941`.
- Parent: `c2eab5ee184d928140d72cfd4156c570913fa6ae`, committed 2026-05-12 13:10:01 -0700.
- `05858aaece5ecda66f5312d069d544e7ef36f2ff`, committed 2026-05-21 08:01:19 -0700, `[wasm] Fix AssertNotNull lowering vs. load elimination`, `Bug: 513009811`.
- Parent: `ee8516cec0729a54d7a6b530730a93862c4f7805`, committed 2026-05-21 07:27:35 -0700.

Bytecode-verifier fixes:

- `bb07280e51d1be1a1cd3cef95151b2c4fccfdd75`, committed 2026-05-11 02:08:10 -0700, `[sandbox] Disallow WasmAllocateFeedbackVector in bytecode verifier`, `Fixed: 507520268`.
- `de8ca504d7508cfe82a8cc2b1db8538f67d3de74`, committed 2026-05-17 20:02:05 -0700, `[sandbox] Add kWasmStringNewWtf8 to bytecode verifier blocklist`, `Bug: 513035609`.
- `a1dd77a620ff51a38b57e5e3687eda290c01e676`, committed 2026-05-18 07:41:06 -0700, `[sandbox] Fix exception handler validation in the bytecode verifier`, `Fixed: 513355978, 513103027`.
- `47c2ef1086188c8078ab66f60b72b0c84f7f934d`, committed 2026-05-18 08:01:41 -0700, reverted the exception-handler fix.
- `5873eb8fd9c86d9a977000a3255c46b1996df433`, committed 2026-05-19 01:06:07 -0700, relanded the exception-handler fix.
- `b6e9fb898e854239e7e1be3c48231a2180327aed`, committed 2026-05-21 02:45:12 -0700, `[sandbox] Disallow Wasm intrinsics in bytecode verifier`, `Bug: 513009810, 513035609, 512533945, 514896898`.

Ancestor checks from local history:

- `bb07280e` is an ancestor of `c2eab5ee`, so `55cc^` no longer contains `b/507520268`.
- `de8ca504`, `5873eb8`, and `b6e9fb8` are not ancestors of `c2eab5ee`, so `55cc^` still contains those later verifier gaps.
- `55cc1df` is an ancestor of `d82d5bd`, so `CVE-2026-9973` is already fixed in the later `b/513009811` target windows.
- `5873eb8` is an ancestor of `d82d5bd`, so the broad-intrinsic target has exception-handler validation already fixed.
- `b6e9fb8` is an ancestor of `ee8516c`, so `05858^` is too late for the listed verifier gaps.

## First-Stage Evidence

### CVE-2026-9973 / b/509268941

The fix adds dependent-Phi handling to `src/compiler/turboshaft/wasm-load-elimination-reducer.h`. Before the fix, loop Phi replacements could depend on one another without being cleared in parallel during loop revisit. The patch adds `MaybeReplacePhi`, `phi_replacements_backups_`, and backup/clear/recompute logic in `BeginBlock<for_loop_revisit>`.

The strongest regression is `test/mjsunit/regress/wasm/regress-509268941.js`:

- Creates a length-10 WasmGC array and a length-1 WasmGC array.
- Stores `0x1337` to `cur[3]` inside a loop.
- Updates `cur` through `holder.field`, then changes `holder.field` to the small array.
- The test comment states optimized code incorrectly elided the bounds check in later iterations.
- Correct behavior is `kTrapArrayOutOfBounds`, including after `%WasmTierUpFunction`.

Assessment: this is the only first stage in this candidate with direct OOB-write-shaped evidence. It is still only a narrow WasmGC OOB store, not a demonstrated arbitrary caged RW or bytecode-object write.

### b/513009811

The fix message is explicit: `AssertNotNull` used a trapping `Load` at the same offset as a `LoadTrustedPointer` for `WasmInternalFunction::trusted_internal_`. Load elimination treated the normal load and trusted-pointer load as aliases even though their representations differ.

Patch evidence:

- `05858aa...` changes `WasmLoweringReducer::REDUCE(AssertNotNull)` to load representation-specific fields for structs, arrays, waitqueues, and function refs instead of always loading an `Int32` at `kTaggedSize`.
- It adds debug checks in `LateLoadEliminationAnalyzer::ProcessLoad` and `ProcessTrustedLoad` so `LoadOp` does not alias with `LoadTrustedPointerOp`.
- Follow-up `8a885ed63641d4b0bfb4d8d9aaddc21104614b35` introduces a dedicated `MemoryRepresentation` for `LoadTrustedPointer`, referencing `474402851, 513009811`.

The regression `test/mjsunit/regress/wasm/regress-513009811.js` uses `--future`, `ref.as_non_null`, and `call_ref`, then checks that a function call returns `11`.

Assessment: security-relevant under the heap sandbox because it involves trusted-pointer load aliasing, but the local test does not show OOB write, caged RW, or targeted bytecode corruption.

## Verifier Second-Stage Mechanics

### Wasm Runtime Function / Intrinsic Blocklist

`bb07280e` adds only:

```text
case Runtime::kWasmAllocateFeedbackVector:
  return false;
```

Its regression `test/mjsunit/sandbox/regress/regress-507520268.js` is helper-dependent:

- Flags: `--allow-natives-syntax --sandbox-testing --verify-bytecode-full`.
- Calls `%GetBytecode(f)`.
- Replaces `ba.bytecode` with a `CallRuntime 613` sequence, where `613` is `Runtime::kWasmAllocateFeedbackVector`.
- Sets `ba.frame_size = 24`.
- Calls `%InstallBytecode(f, ba)`.
- Calls `f()` and expects the process to be killed.

The commit message says `WasmAllocateFeedbackVector` is an internal Wasm runtime function, normal JS bytecode has no legitimate reason to call it, and manipulated bytecode can expose internal Wasm allocation logic to untrusted inputs, "leading to crashes." It also says the blocklist is for fuzzer cleanliness.

`de8ca504` adds `Runtime::kWasmStringNewWtf8` to the same blocklist. `b6e9fb8` replaces the ad hoc list with `FOR_EACH_INTRINSIC_WASM` and `FOR_EACH_INTRINSIC_WASM_TEST`, returning `Runtime::IsEnabledForFuzzing(id)` for those IDs. The broad ban is guarded by:

```text
if (!v8_flags.fuzzing) return true;
```

That makes the broad intrinsic blocklist primarily a fuzzing/full-verifier cleanliness rule, not a normal-production bytecode execution rule.

### Exception Handler Validation

`5873eb8` relands the `a1dd77a` fix in `BytecodeVerifier::VerifyLight`:

- It now checks that `handler >= end`, so exception handlers must be after their try-ranges.
- It now checks handler data: either invalid-register sentinel or `0 <= data < bytecode->register_count()`.

The added unit tests build `BytecodeArray` objects directly with crafted `HandlerTable` data:

- `HandlerTableEntryWithHandlerBeforeEnd` sets a handler inside/before the try range and expects verifier death.
- `HandlerTableEntryWithInvalidData` sets handler data to register `1000` and expects verifier death.

This is the best-looking second-stage class because invalid handler data affects interpreter exception state rather than only runtime function selection. However, the evidence is still verifier/unit-test evidence. There is no local proof that a Wasm OOB write can manufacture a published trusted `BytecodeArray` with malicious handler metadata.

## Can Manipulated Bytecode Execute?

Yes, but the demonstrated route is not helper-free.

`Runtime_InstallBytecode` does the following:

1. Reads a JS object containing `bytecode`, `constant_pool`, `handler_table`, `frame_size`, `parameter_count`, `max_arguments`, and `incoming_new_target_or_generator_register`.
2. Allocates a new trusted `BytecodeArray`.
3. Calls `BytecodeVerifier::Verify(isolate, new_bytecode, &zone)`.
4. Replaces the target `SharedFunctionInfo` bytecode.
5. Discards compiled code and updates the function to `InterpreterEntryTrampoline`.

`BytecodeArray::MarkVerified` publishes the trusted object in the trusted pointer table and installs it into its in-sandbox wrapper. The normal bytecode writer also calls `BytecodeVerifier::Verify` before returning a `BytecodeArray`.

The blocker is access. `%GetBytecode` and `%InstallBytecode` are specifically described in `Runtime::IsEnabledForFuzzing` as sandbox-fuzzing/testing APIs. The comment says `%InstallBytecode` allows installing manipulated bytecode checked for sandbox safety, not general correctness. Those APIs are exposed under `--sandbox-testing` or `--sandbox-fuzzing`, not normal challenge execution.

A raw first-stage caged RW could in theory mutate an already-published bytecode wrapper or related metadata after verification. That is a different path: it bypasses the verifier rather than exploiting these verifier gaps. The current local evidence does not show a Wasm load-elimination primitive that can write trusted `BytecodeArray` contents or protected trusted-pointer fields.

## Helper-Free Viability

Current status: **not viable for a pwn.college challenge without a new primitive**.

Positive evidence:

- `CVE-2026-9973` has a normal Wasm regression with an optimized OOB-store shape.
- `b/513009811` is a real trusted-pointer representation aliasing bug class.
- The verifier hardening commits are sandbox-labeled and local source confirms the missing checks.
- Manipulated bytecode can execute after verifier-mediated publication.

Blocking evidence:

- The bytecode-verifier regressions use `--sandbox-testing`, `%GetBytecode`, `%InstallBytecode`, or unit-test direct object creation.
- `verify_bytecode_full` is mainly for fuzzing/testing; `fuzzing`, `sandbox_fuzzing`, and `sandbox_testing` imply it.
- `b6e9fb8` explicitly only applies the broad Wasm intrinsic blocklist when `v8_flags.fuzzing` is true.
- The verifier commits describe crashes/fuzzer cleanliness, not a confirmed escape.
- The first stages do not show the ability to create, publish, or modify trusted bytecode helper-free.
- If a first-stage caged RW mutates already-published bytecode directly, the listed verifier fixes are not the meaningful second-stage boundary.

## Best Target Revisions

Use these only for further research, not challenge scaffolding:

- `dbafd06731e4924b0f58eead66b0601c24c20235`: parent of `bb07280e`; includes `CVE-2026-9973` and leaves `WasmAllocateFeedbackVector` allowed. Best for reproducing `b/507520268`.
- `c2eab5ee184d928140d72cfd4156c570913fa6ae`: parent of `55cc1df`; best first-stage evidence for `CVE-2026-9973`, and still before `de8ca504`, `5873eb8`, and `b6e9fb8`.
- `cf0711105ccf6e70fde62418c2214361138d4340`: parent of the exception-handler reland; `b/513009811` is still vulnerable and exception-handler validation is absent due to the revert.
- `d82d5bd8ad543679c22c8115b44fabacc8a662da`: parent of `b6e9fb8`; `b/513009811` is still vulnerable and the broad Wasm-intrinsic verifier change is absent, while the exception-handler checks are already present.

Do not use `ee8516cec0729a54d7a6b530730a93862c4f7805` (`05858^`) for this bytecode-verifier pairing. It is a good target for studying `b/513009811` itself, but all listed verifier fixes have already landed by then.

## Final Recommendation

Drop this as a challenge candidate for now. Keep only a low-priority research note:

- **Hold-low** `CVE-2026-9973 + later verifier gaps` at `c2eab5ee...` if the next task is to understand verifier hardening under `--sandbox-testing`.
- **Hold-low** `b/513009811 + exception-handler validation` at `cf071110...` if someone first extracts a real primitive from the `LoadTrustedPointer` aliasing bug.
- **Drop** all variants that require `%InstallBytecode`, `Sandbox.MemoryView`, direct unit-test bytecode construction, or fuzzing-only verifier behavior for a pwn.college exploit.

The next decisive experiment would be a helper-free proof that a Wasm load-elimination first stage can affect a trusted published `BytecodeArray` or its handler table. Without that, the verifier gap and the Wasm first stage are adjacent in time but not connected by an exploit path.
