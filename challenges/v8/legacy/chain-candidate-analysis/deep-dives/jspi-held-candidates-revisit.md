# JSPI Held Candidates Revisit

Decision: **do not promote any reviewed family to a challenge**.

Challenge bar checked for all variants: unmodified vulnerable V8, sandbox
enabled, no `--sandbox-testing`, no `Sandbox.MemoryView` / `Sandbox.getAddressOf`,
no helper APIs, no synthetic corruption, and a private test that runs the full
exploit chain to the flag.

## Scope

Revisited:

- `2025-9864-or-11219-jspi.md`
- `2025-march-jspi-stack.md`
- `2024-h2-jspi-native-stack.md`

Cross-checks used:

- Existing working JSPI escape chains:
  `chain-cve-2025-5419-422645418` and
  `chain-cve-2025-5959-422645418`.
- Local V8 history/regressions for `b/371565065`, `b/400052777`,
  `b/434513380`, `b/439772737`, `b/432289371`, `b/384553540`,
  `b/384549659`, `b/356419168`, `b/356176643`, and `b/427946951`.

## 2025-9864 / 2025-11219 + early-H2 JSPI

Best-looking sink remains `b/432289371`, because the upstream regression shows
the exact corruption target: replace `WasmSuspendingObject.callable` at `+0xc`
with a Wasm export pointer and instantiate an importing module to create a
suspending-import / Wasm-function import inconsistency.

Missing primitive:

- The `b/432289371` regression still relies on `--sandbox-testing`,
  `Sandbox.MemoryView`, and `Sandbox.getAddressOf` to perform the field write.
- `CVE-2025-9864 / b/434513380` only gives local evidence of a Maglev
  Float64/Smi representation confusion via `Math.sqrt(0)` and
  `%OptimizeMaglevOnNextCall`; it does not provide `addrof`, fake object,
  caged read/write, or a targeted compressed-pointer write to
  `WasmSuspendingObject.callable`.
- `CVE-2025-11219 / b/439772737` is a real stale `ArrayBuffer` wire-byte vector
  in `WebAssembly.validate()`, but the observed primitive is stale read/validate
  of freed backing-store bytes. The local material does not show a heap layout
  that turns it into a precise in-cage write.
- `b/427946951` is a weaker sink for this repo because the direct
  `StackMemory` sandbox-extension issue is tied to hardware sandbox support,
  while the challenge args used by existing chains only set
  `v8_enable_sandbox = true`.

Result: **hold/no-go**. The concrete missing step is a helper-free first stage
that can locate a `WasmSuspendingObject` and write its compressed `callable`
field to a chosen Wasm export.

## March 2025 JSPI stack candidates

The best exact overlap remains `CVE-2025-2135 / b/400052777` plus
`b/384553540` at `8f51e033902da9b786358e6e82f0dc57b46464dc`.

Missing primitive / trigger:

- `b/400052777` is a real Turbofan map-reliability bug around aliasing
  `TransitionElementsKindOrCheckMap`, but the regression only demonstrates the
  bad optimized state. It does not establish a stable fake-object, `addrof`, or
  caged read/write primitive.
- The usable `b/384553540` sink requires corrupting the in-sandbox JSPI
  continuation chain, such as `WasmContinuationObject.parent`, `stack`, or
  `jmpbuf`, and then triggering suspend/resume/return so stack-switch builtins
  trust the corrupted graph.
- The older retired-stack route (`b/384549659`) is not a clean pairing with
  `CVE-2025-2135`: the `stack` and `jmpbuf` EPT nulling fixes landed before the
  clean first-stage target. Promoting that variant would require proving the
  first-stage bug was already exploitable before those February fixes and still
  gives a precise continuation/jump-buffer corruption primitive.

Result: **hold/no-go**. The concrete missing step is a real heap-sandbox write
primitive from the array transition bug, plus a demonstrated corrupted
continuation-chain trigger without sandbox helpers.

## 2024 H2 JSPI native-stack candidates

The strongest variant remains `CVE-2024-10230 / b/371565065` plus the October
2024 JSPI stack-state hardening (`b/356419168`, `b/356176643`, `b/42202153`) at
`792f2c275b4df075f33659d06ba2940a0a3e3e6a`.

Missing primitive / trigger:

- `b/371565065` has meaningful Wasm GC wrapper-tiering type-confusion evidence,
  but the regression is still a witness, not an exploit. It uses
  `--wasm-wrapper-tiering-budget=1` and `%CountUnoptimizedWasmToJSWrapper`, and
  the local material does not turn the confused struct layout into a caged
  read/write primitive.
- The JSPI sink requires corrupting a continuation or jump-buffer relationship
  so pre-fix stack switching resumes or returns through the wrong native stack.
  That requires precise field writes to `WasmContinuationObject` /
  `WasmSuspenderObject` state or aliased `JumpBuffer` data.
- Other H2 candidates in the report remain lower quality as first stages:
  they either lack local primitive evidence, are JSPI correctness bugs
  themselves, or do not show an object-metadata corruption path.

Result: **hold/no-go**. The concrete missing step is converting the Wasm GC
wrapper confusion into helper-free address discovery and targeted caged writes,
then proving a corrupted JSPI stack switch reaches control flow needed for the
flag chain.

## Files Touched

- Added this report only:
  `chain-candidate-analysis/deep-dives/jspi-held-candidates-revisit.md`

No challenge directory was created, `module.yml` was not edited, and no
`pwnshop test` was run because there is no authentic full exploit candidate to
test.
