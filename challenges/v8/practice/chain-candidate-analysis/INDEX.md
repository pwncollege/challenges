# V8 Chain Candidate Index

Generated: 2026-06-03.

This index is scoped to post-Turboshaft V8 chain candidates.
The cutoff is March 25, 2025, matching V8's public Turboshaft transition writeup.

Pre-cutoff 2024 and early-2025 research notes live under `../../legacy/chain-candidate-analysis/`.

Source reports:

- [2025 H1, post-cutoff](2025-h1.md)
- [2025 H2](2025-h2.md)
- [2026 H1](2026-h1.md)

Related inventories:

- [`../CVE_ISSUE_CAPABILITY_INDEX.md`](../CVE_ISSUE_CAPABILITY_INDEX.md)
- [`../NON_CVE_RELEVANT_ISSUES.md`](../NON_CVE_RELEVANT_ISSUES.md)

## Legend

| Evidence | Meaning |
| --- | --- |
| Existing-test backed | The repo already contains local challenge material and a private exploit for this pairing or for the same second-stage path. This does not mean the exploit was re-run during this documentation pass. |
| High | Strong component match and explicit sandbox-boundary fix language. Needs helper-free exploit synthesis before becoming a challenge. |
| Medium | Plausible overlap and capability path, but the primitive or second-stage trigger is not yet proven. |
| Low | Useful background lead, but likely redundant, embedder-specific, platform-specific, or too speculative for immediate challenge work. |

## Best Candidates

| Candidate | Window | Evidence | Capability path | Fix-window notes | Report |
| --- | --- | --- | --- | --- | --- |
| `CVE-2025-5419 + b/422645418` | 2025 H1 | Existing-test backed | Turboshaft stale load/store-store aliasing gives caged RW; corrupt JSPI `WasmSuspenderObject` state to reuse native-stack / suspender state. | First stage fixed by `7bc0a67ebfbf44e7adab47fc2bbbe308660e27f4` on 2025-05-27; second-stage short fix `25e22b601c7ddb0a3491cdfb5c604e9e589278d2` on 2025-06-05; hardening `9dcbe0576a48866e9f2c1a242fe6f875c55a6373` on 2025-06-12. | [2025 H1](2025-h1.md#candidate-1-cve-2025-5419--b422645418) |
| `CVE-2025-5959 + b/422645418` | 2025 H1 | Static-backed, runtime failing, narrow window | Wasm canonical equality type confusion gives caged RW; same JSPI suspender/native-stack second stage as above. A direct run reaches the JSPI forged-stack handoff, then segfaults before the flag. | Second-stage short fix landed at 2025-06-05 04:34 -0700; first-stage fix landed at 2025-06-05 07:09 -0700. Existing local revision predates both. | [2025 H1](2025-h1.md#candidate-2-cve-2025-5959--b422645418) |
| `CVE-2025-12428 or CVE-2025-13226..13230 + b/452605803 / b/446113730` | 2025 H2 | High | Wasm custom-descriptor/subtyping bugs supply caged corruption; accepted second stages swap `dispatch_table_for_imports` while still exposed or abuse stale old dispatch-table growth to reclaim code-pointer-table state. | `CVE-2025-12428` fixed 2025-10-06; `CVE-2025-13226..13230` fixed 2025-09-23; `b/446113730` fixes landed 2025-09-23; `b/452605803` fix landed 2025-10-30, was reverted, then relanded as `58bdae122c0f44e427ee2ec7dda636620e7aade2` on 2025-10-31. | [2025 H2](2025-h2.md#candidate-1-cve-2025-12428--b452605803) |
| `CVE-2026-7337 + b/501147587 / b/485784597` | 2026 H1 | High | Maglev Smi-check elision gives object corruption; JSPI suspender EPT/native-stack lifetime bugs give a sandbox-boundary target. | First-stage introducing CL identified as `6469250a124acef52bceabae77ed887f5c8f29ac` on 2025-09-26; first-stage fixes landed 2026-04-14; JSPI stack-return fix landed 2026-02-25; JSPI unwind fix landed 2026-04-15. | [2026 H1](2026-h1.md#candidate-1-cve-2026-7337--jspi-suspender-eptnative-stack-reuse) |
| `CVE-2026-7899 / CVE-2026-9973 + b/503422307` | 2026 H1 | High | Wasm Turboshaft load-elimination bugs may give caged Wasm object corruption; WasmDispatchTable UAF may expose stale trusted dispatch-table state. | Dispatch-table UAF fixed by `9c0c3018761681a8ea2e4c1bf26d6a04ec46f3b8` on 2026-04-22; `CVE-2026-7899` fixed 2026-04-23; `CVE-2026-9973` fixed 2026-05-11. | [2026 H1](2026-h1.md#candidate-2-wasm-turboshaft-load-elimination-bug--wasmdispatchtable-uaf) |
| `CVE-2026-9973 / b/513009811 / CVE-2026-9896 + b/505751230 / b/514157844` | 2026 H1 | Medium-high | Wasm or Maglev in-cage RW paired with WasmFX tags table remaining in sandbox; corrupted tags may produce forged out-of-sandbox references or stack-buffer corruption. | First-stage fixes span 2026-05-05 through 2026-05-21; tags table moved to trusted space by `e8baffef1a07eb566572447b26442ad44df52a50` on 2026-06-02. | [2026 H1](2026-h1.md#candidate-3-wasm-or-maglev-first-stage--wasmfx-tags-table-in-sandbox) |

## Secondary Candidates

| Candidate | Evidence | Why keep it | Main caveat |
| --- | --- | --- | --- |
| `CVE-2025-6554` or b/428112179 + b/40070746 / b/435630461 | Medium-low | Late-June TypedArray guard-region window plus ElementsKind switcheroo could yield native OOB access. | Window is very short; May 2025 TypedArray-length changes may already close part of the route. |
| `CVE-2025-10585 + b/446113730` | Medium for ARM64, low for x64 | Strong second-stage language around invalid Wasm code pointers and old dispatch tables. | First stage is ARM64-specific and regression uses sandbox-testing. |
| `CVE-2025-9864` or `CVE-2025-11219 + b/432289371 / b/427946951` | Medium-low | Early-H2 JSPI / WasmSuspendingObject issues explicitly describe sandbox escapes. | Short windows and first-stage primitive quality is unknown. |
| `CVE-2026-7337 + b/498095290` | Medium | Maglev object corruption plus Wasm dispatch-table parameter hardening. | The second stage may be hardening rather than a proven reachable escape. |
| Wasm load-elimination first stages + 2026 bytecode-verifier gaps | Medium-low | Wasm bytecode verifier fixes are sandbox-labeled and close to Wasm first stages. | Need to show manipulated bytecode can execute and produces more than a crash. |

## Deprioritized Or Special-Case Leads

- Inspector, embedder API, or command-line API issues are unsuitable for normal
  d8 challenges unless the challenge intentionally exposes that embedder
  surface.
- ARM64, Loong64, MIPS64, or other platform-specific rows are not portable to
  the default x64 challenge environment.
- Sandbox-hardening-only rows are useful diff-mining seeds, but should not be
  called real chain candidates until a helper-free JavaScript/Wasm trigger is
  demonstrated.

## Next Triage Queue

1. Reconfirm the post-cutoff existing-test-backed chains are still helper-free
   after the latest local edits: `chain-cve-2025-5419-422645418` and
   `chain-cve-2025-5959-422645418`.
2. Keep `CVE-2025-12428` as the remaining H2 2025 hold; the
   `CVE-2025-13226..13230` variants are now challenge-backed for both accepted
   dispatch-table second stages.
3. Triage 2026 first: `CVE-2026-7337 + JSPI`, then any new replacement for the
   dropped `CVE-2026-7899 + b/503422307` second-stage trigger, while keeping
   `CVE-2026-9973 + WasmFX tags table` as the accepted 2026 chain.
4. For every new chain, require three checks before keeping it as a challenge:
   vulnerable unmodified V8 revision, no helper or sandbox-testing interface,
   and a private test that performs the full exploit path to the flag.
