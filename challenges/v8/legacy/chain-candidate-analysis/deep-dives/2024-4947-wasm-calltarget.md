# CVE-2024-4947 + Wasm Trusted Call-Target / Dispatch Path

Generated: 2026-06-03.

Verdict: **Drop for the exact local CVE-2024-7024-labelled Wasm raw-memory
chain; Hold only for a separate pre-June 2024 Wasm signature/dispatch
confusion hunt.**

The substitution idea is attractive but does not line up with the local
6100/7024 chain. The checked-in CVE-2024-4947 challenge revision is the direct
parent of the 4947 fix, but it is already after the two b/334120897 fixes that
make the local 6100/7024 second stage work: `WasmFunctionData` has already moved
to trusted space, and the i32 high-word raw-memory primitive has already been
hardened. The local 4947 challenge also does not prove a heap-sandbox caged-R/W
primitive: it builds with `v8_enable_sandbox = false` and runs with
`--allow-natives-syntax --expose-gc`.

## Sources Checked

- Local index:
  - `CVE_ISSUE_CAPABILITY_INDEX.md`
  - `chain-candidate-analysis/INDEX.md`
  - `chain-candidate-analysis/2024-h1.md`
- Local challenge material:
  - `cve-2024-4947/challenge/REVISION`
  - `cve-2024-4947/challenge/args.gn`
  - `cve-2024-4947/challenge/run.j2`
  - `cve-2024-4947/challenge/patch`
  - `chain-cve-2024-6100-7024/tests_private/test_exploit.sh`
  - `chain-candidate-analysis/deep-dives/2024-6100-7024-labelled.md`
- Local V8 checkout: `/home/yans/code/v8`

The private `cve-2024-4947/tests_private/WRITEUP.md` and
`test_exploit.sh` are git-crypt encrypted in this checkout, so I could not use
their exploit internals.

## Exact 4947 Mapping

CVE-2024-4947 maps locally to b/340221135 and V8 commit:

- `b3c01ac1e60afc9addad9942f7a9a6c5e8a4a6da`
- `2024-05-13 19:03:05 +0000`
- `[compiler] Don't build AccessInfo for storing to module exports`
- `Cr-Commit-Position: refs/heads/main@{#93872}`

The local 4947 challenge revision is:

- `473318dfdb09464902c7633cad03b16431145800`
- `2024-05-13 18:02:00 +0000`
- `Cr-Commit-Position: refs/heads/main@{#93871}`
- `git describe --contains`: `12.7.9~1`

`git rev-parse b3c01ac1...^` equals `473318df...`, so this is the exact parent
of the 4947 fix.

The fix does two relevant things:

- In `src/compiler/access-info.cc`, `AccessorAccessInfoHelper` now returns
  `PropertyAccessInfo::Invalid` for any store to a module namespace object.
- In `src/maglev/maglev-graph-builder.cc`, property-store lowering now
  switches over `PropertyAccessInfo::kind()` and makes `kModuleExport`
  unreachable for stores, instead of falling through to `TryBuildStoreField`.

Before the fix, Maglev could build store AccessInfo for module exports even
though module namespace stores are specified as errors or no-ops. That is good
evidence for a Maglev type confusion / object corruption first stage, but the
local material does not show that this stage is a reusable arbitrary caged R/W
primitive under `v8_enable_sandbox = true`.

## Overlap With The Local Wasm Chain

The local 6100/7024-labelled chain uses V8 revision:

- `1778ccde8eb86a01b4c16c34490a597235203b2d`
- `2024-04-13 19:24:32 +0000`

The exact local Wasm second stage depends on b/334120897-era behavior:

- `cf9373a0d6760146534b096cee60675a3ea09ad7`
  - `2024-04-29 13:53:03 +0000`
  - `[wasm][sandbox] Make WasmFunctionData trusted`
  - commit text says moving `WasmFunctionData` to trusted space addresses ways
    Wasm functions can escape from a compromised V8 sandbox.
- `5942a14103720910a8c6a0aebc67f4314dd8fdd9`
  - `2024-05-02 13:15:29 +0000`
  - `[wasm][sandbox] Fix sandbox escapes via i32 high word`
  - commit text says in-sandbox corruption could cause i64 values to be passed
    to functions expecting i32.

Ancestry from `/home/yans/code/v8`:

- `473318df...` is before the CVE-2024-4947 fix `b3c01ac1...`.
- `473318df...` is **not** before `cf9373a...`; that fix is already included.
- `473318df...` is **not** before `5942a141...`; that fix is already included.
- `473318df...` is before later b/336507783 / b/42204510 hardening:
  `47ac44d...`, `e25efe6...`, `f603d576...`, `2b620f7...`, and `388e59d...`.

So there is no exact overlap between the proven 4947 parent revision and the
local 6100/7024 raw-memory path. A hypothetical older revision before
`cf9373a...` or `5942a141...` would need proof that CVE-2024-4947 is already
present there; this checkout only establishes `unknown-intro..b3c01ac1^`.

## Wasm Metadata Reachability

At the local 6100/7024 revision (`1778ccde...`), `WasmFunctionData` is an
ordinary `HeapObject` with a `func_ref` field. The chain writes that field from
caged JS/Wasm corruption:

- It reads `SharedFunctionInfo::function_data`.
- It overwrites `WasmFunctionData::func_ref` for `oob_read` and `oob_write`.
- It abuses the i64-to-i32 high-word bug to turn Wasm memory accesses into raw
  virtual-address read/write.
- It then uses raw write to patch `WasmInternalFunction::call_target`.

At the CVE-2024-4947 parent revision (`473318df...`), that exact target is gone:

- `WasmFunctionData` is `ExposedTrustedObject`, not a normal `HeapObject`.
- `SharedFunctionInfo` uses `trusted_function_data` under the sandbox.
- `WasmFunctionData` has a protected `internal` pointer pairing it with
  `WasmInternalFunction`.
- `WasmFuncRef` remains a caged `HeapObject`, but its important field is an
  indirect trusted-pointer handle to `WasmInternalFunction`.

A caged write may still be able to corrupt a `WasmFuncRef` handle or other
ordinary heap references, but that is much weaker than the local chain's
`WasmFunctionData::func_ref` rewrite. It can at best swap already-existing
trusted objects if the handle values are known. It does not directly write the
trusted `WasmInternalFunction::call_target`, does not create arbitrary trusted
objects, and does not read the trusted pointer table without a raw-memory
primitive.

## Second-Stage Mapping And Dispatch Notes

The local report now maps the CVE-2024-7024-labelled chain primarily to
b/334120897, with related b/336507783 / b/42204510 hardening around Wasm
function refs, signature checks, dispatch tables, and `WasmApiFunctionRef`.

For CVE-2024-4947 at `473318df...`:

- The b/334120897 raw-memory path is already closed by `cf9373a...` and
  `5942a141...`.
- Later signature/call-ref hardening is still absent:
  - `47ac44d...`, 2024-06-05, verifies signatures for `call_ref`.
  - `e25efe6...`, 2024-06-11, verifies signatures in JS-to-Wasm wrappers.
  - `f603d576...`, 2024-06-12, checks signatures when updating tables.
  - `2b620f7...`, 2024-06-27, checks signatures when importing tables.
  - `388e59d...`, 2024-07-01, un-exposes `WasmApiFunctionRef`.

That leaves a possible research lead: use a 4947-derived caged write to corrupt
ordinary Wasm references or table entries and trigger a pre-signature-check
call mismatch. But that would be a different chain from the checked-in
6100/7024 exploit. It would need a concrete trigger that crosses the sandbox
boundary without first obtaining raw memory. I did not find local evidence for
that trigger.

## Caged R/W And Helper-Free Viability

Current status: **not proven**.

The local 4947 challenge is not a good proof of heap-sandbox first-stage quality:

- `cve-2024-4947/challenge/args.gn` sets `v8_enable_sandbox = false`.
- `cve-2024-4947/challenge/run.j2` invokes d8 with
  `--allow-natives-syntax --expose-gc`.
- The private writeup and exploit are encrypted in this checkout, so I could not
  verify whether they avoid native syntax, debug helpers, or unsandboxed
  assumptions.

By contrast, the local 6100/7024 chain has a visible helper-free first stage:
standard Wasm modules build caged `read64Caged`, `write64Caged`, and `addrof`.
There is no equivalent visible 4947 primitive here.

For this candidate to become viable, the first stage would need to demonstrate,
under `v8_enable_sandbox = true` and without `--allow-natives-syntax`, all of:

- stable object address discovery or equivalent caged pointer recovery;
- caged read/write strong enough to mutate selected Wasm ordinary-heap objects;
- ability to locate exported Wasm functions, `WasmFuncRef` objects, or table
  entries without debug helpers;
- a second-stage path that still works after `WasmFunctionData` is trusted and
  i32 high-word clearing is present.

## Best Target Revision

For reproducing CVE-2024-4947 itself, the best pinned revision is:

- `473318dfdb09464902c7633cad03b16431145800` (`b3c01ac1^`, `12.7.9~1`)

For the exact local 6100/7024 Wasm raw-memory path, there is no good 4947 target
revision currently proven. The required Wasm window is before:

- `cf9373a0d6760146534b096cee60675a3ea09ad7` for caged
  `WasmFunctionData` corruption; and/or
- `5942a14103720910a8c6a0aebc67f4314dd8fdd9` for the i32 high-word raw-memory
  effect.

But the local 4947 mapping only proves the bug at `473318df...`, after both
fixes. Testing an older revision such as `cf9373a^` would be range research, not
a confirmed CVE-2024-4947 chain target.

For the separate pre-signature-check idea, the best target remains
`473318df...`: it is the exact 4947 vulnerable parent and still predates the
June/July b/336507783 and b/42204510 signature / `WasmApiFunctionRef`
hardening. That path should be tracked separately from the local
CVE-2024-7024-labelled raw-memory chain.

## Final Recommendation

Drop this as a direct replacement for CVE-2024-6100 in the local
CVE-2024-7024-labelled Wasm call-target chain.

Hold a narrower follow-up only if someone first produces a sandbox-enabled,
helper-free CVE-2024-4947 caged R/W primitive. The next investigation should
then target `473318df...` and look for a pre-June signature/dispatch mismatch,
not for the already-closed `WasmFunctionData` / i32-high-word raw-memory path.
