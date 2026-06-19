# 2024 Canonical Wasm Type Bugs + Dispatch/CPT Deep Dive

Generated: 2026-06-03.

Scope: `CVE-2024-12053` / `CVE-2024-12381` / `CVE-2024-12692` as first-stage
Wasm canonical-type confusions, paired with either the December 2024
`WasmDispatchTable` rewrite (`b/350628675`, `b/42204123`) or the
`WasmCodePointerTable` signature-check hardening (`b/350292240`).

Sources:

- Local index: `CVE_ISSUE_CAPABILITY_INDEX.md`
- Local index: `NON_CVE_RELEVANT_ISSUES.md`
- Local candidate summary: `chain-candidate-analysis/2024-h2.md`
- Local V8 checkout: `/home/yans/code/v8`

## Verdict

| Variant | Exact mainline overlap revision | Decision | Reason |
| --- | --- | --- | --- |
| `CVE-2024-12053` + `WasmDispatchTable` | `c000741f63186cf66ce422fb7aca04255d2d9465` (`20d9a7f^`) | HOLD | Chronological overlap exists, but the later regression test is a small wrapper-tiering/toString trigger, not a concrete cage R/W primitive. |
| `CVE-2024-12381` + `WasmDispatchTable` | `0b03a5d093800433f0fa2de88d33cb99e0a29ace` (`74caf544^`) | HOLD | Stronger first-stage evidence and exact overlap, but the dispatch CL is a broad architecture rewrite with no dedicated exploit regression. |
| `CVE-2024-12692` + `WasmDispatchTable` | `0b03a5d093800433f0fa2de88d33cb99e0a29ace` (`74caf544^`) | HOLD | Strong first-stage evidence and exact overlap; same second-stage uncertainty as above. |
| `CVE-2024-12053` + CPT | none in default mainline build | DROP | `CVE-2024-12053` was fixed before CPT was enabled by default. Only a custom `v8_enable_wasm_code_pointer_table=true` build overlaps. |
| `CVE-2024-12381` + CPT | `2fa717a2972e6a4b3897ce099ba2495bf87e1aad` (`a4d354fa^`) | KEEP | CPT is enabled by default, first-stage test demonstrates intended object-confusion shape, and the second-stage fix adds signature validation at CPT loads. |
| `CVE-2024-12692` + CPT | `0ea5a485280535ce427d547440b62acd03d5a037` (`3852cf8b^`) | KEEP | Same as above, with a mutability-confusion first stage. |

The best next candidates are therefore the CPT pairings with `CVE-2024-12381`
and `CVE-2024-12692`. The dispatch-table variants remain worth tracking, but
they need a concrete way to turn cage corruption into corruption of the exact
dispatch/import metadata affected by `74caf544`.

## Mainline Commit Evidence

### First-stage fixes

`CVE-2024-12053`, bug `379009132`:

- Main fix: `20d9a7f760c018183c836283017a321638b66810`
- Commit date: 2024-11-19 17:47:52 +0000
- Subject: `[wasm] Remove relative type indexes from canonical types`
- Evidence in commit message: relative types leaked from the type canonicalizer
  and caused type confusion in callers.
- Branch merge indexed locally: `3fdedec45691a3ab005d62c3295436507e8d277a`,
  `refs/branch-heads/13.2@{#22}`, commit date 2024-11-27.
- Parent / last vulnerable mainline revision for mainline analysis:
  `c000741f63186cf66ce422fb7aca04255d2d9465`.

`CVE-2024-12381`, bug `381696874`:

- Main fix: `a4d354fa54ba3e6a0f061c6b959be408ead5db95`
- Commit date: 2024-12-02 15:15:20 +0000
- Subject: `[wasm] Fix equality of canonical value types`
- Evidence in commit message: V8 incorrectly assumed value kind implied
  indexedness and failed to compare generic non-index reference types.
- Branch merge indexed locally: `aad03217f482b90f34ae559ca3492295f56e648e`,
  `refs/branch-heads/13.2@{#30}`, commit date 2024-12-05.
- Parent / last vulnerable mainline revision:
  `2fa717a2972e6a4b3897ce099ba2495bf87e1aad`.

`CVE-2024-12692`, bug `382291459`:

- Main fix: `3852cf8b5bceed6a76e4537fc0aa191f9ed672a3`
- Commit date: 2024-12-05 19:19:51 +0000
- Subject: `[wasm] Fix comparison of canonical struct types`
- Evidence in commit message: canonical struct comparison checked field types
  but missed field mutability.
- Branch merge indexed locally: `92ed656a375cc0fa3346f00f7e0d9faf0df04db2`,
  `refs/branch-heads/13.2@{#34}`, commit date 2024-12-10.
- Parent / last vulnerable mainline revision:
  `0ea5a485280535ce427d547440b62acd03d5a037`.

### Second-stage fixes

`WasmDispatchTable`, bugs `350628675` and `42204123`:

- Main fix: `74caf5449508c72236970e5d9e01b7212d609122`
- Commit date: 2024-12-02 11:28:13 +0000
- Subject: `[wasm][sandbox] One WasmDispatchTable per WasmTableObject`
- Parent / last vulnerable mainline revision:
  `0b03a5d093800433f0fa2de88d33cb99e0a29ace`.
- Ancestry checks: `20d9a7f` is before `74caf544`; `74caf544` is before
  `a4d354fa` and `3852cf8b`.

`WasmCodePointerTable`, bug `350292240`:

- Main fix: `58f407806ad0ea83d8174dd701ba4b84c3cca14f`
- Commit date: 2024-12-12 04:06:35 -0800
- Subject: `[sandbox][wasm] add signature checks to the code pointer table`
- Evidence in commit message: every CPT entry now stores a signature hash and
  every load validates the signature.
- CPT default enablement: `bca5a5d291ae7877bcdbd185955bd63e962ef0f1`,
  `[wasm][cfi] Enable the WasmCodePointerTable by default`, commit date
  2024-11-22 08:52:36 +0000, changed `v8_enable_wasm_code_pointer_table` from
  `false` to `v8_enable_webassembly`.
- Ancestry checks: `bca5a5d` is after `20d9a7f`; `bca5a5d` is before
  `a4d354fa`, `3852cf8b`, and `58f40780`.

## Fix Diff Findings

### `CVE-2024-12053`: relative canonical indexes

`20d9a7f` removes stored relative type indexes from canonical types. The patch
passes recursion-group bounds into canonicalization, hashing, and equality, and
computes relative indexes on demand instead of keeping a relative bit in
`ValueTypeBase`. This is a real canonicalizer type-confusion bug, but the later
regression test is not a ready-made addrof/read/write shape.

Regression evidence was added later in
`ed5cd496163651ad81699424d2b95a77cffc8c32` on 2025-01-09:
`test/mjsunit/regress/wasm/regress-379009132.js` builds a self-referential
function-reference signature, tiers a wrapper with
`--wasm-wrapper-tiering-budget=1`, calls the function, then calls
`func_ref.toString()`.

First-stage primitive classification: `HS-RW potential`, but currently
weaker than the other two variants because the local regression test does not
show a direct struct-field confusion primitive.

### `CVE-2024-12381`: canonical value-type equality

`a4d354fa` changes `CanonicalEquality::EqualValueType` so equality checks both
whether each value type has an index and, for generic non-index reference types,
compares heap representation. Before the fix, `ref null none` and
`ref null any` style shapes could canonicalize as equivalent in the wrong
contexts.

Regression evidence in `ed5cd496`:
`test/mjsunit/regress/wasm/regress-381696874.js` deliberately searches
colliding struct layouts, names intended helpers `addrof`, `caged_read`, and
`caged_write`, then expects the fixed compiler to reject a mismatched
`struct.get`. This is strong evidence of an intended object-layout confusion
first stage.

First-stage primitive classification: strong `HS-RW potential`.

### `CVE-2024-12692`: canonical struct mutability

`3852cf8b` updates `CanonicalEquality::EqualStructType` so canonical struct
equality compares both field value types and the mutability bitmap. Before the
fix, mutable and immutable fields could be treated as the same canonical struct
shape.

Regression evidence in `ed5cd496`:
`test/mjsunit/regress/wasm/regress-382291459.js` constructs colliding mutable
and const struct layouts, writes through a field using one type, reads through
another, and expects the fixed compiler to reject the mismatch.

First-stage primitive classification: strong `HS-RW potential`.

## Dispatch-Table Second Stage

`74caf544` is not a small bounds-check patch; it is a trust-boundary rewrite:

- Stores a `WasmDispatchTable` on each `WasmTableObject`.
- Removes `WasmTableObject::uses`.
- Introduces `WasmDispatchTable::protected_uses`, a protected weak array of
  `<WasmTrustedInstanceData, table_index>` pairs, so users are updated when a
  dispatch table grows.
- Adds `WasmDispatchTable::table_type` and updates signature checks to use the
  table's canonical value type.
- Changes `WasmDispatchTable` from `TrustedObject` to `ExposedTrustedObject`.
- Moves `WasmImportData::call_origin` from a normal `Smi|WasmFuncRef|Tuple2`
  field to a protected pointer storing a `WasmInternalFunction` or
  `WasmDispatchTable`, with the table slot stored in a bit field.

Reachability classification: medium. The affected state is reachable from
normal Wasm table/import setup, and a cage R/W first stage plausibly targets
the pre-fix `call_origin` / table-use metadata. The blocker is that the commit
does not add a focused regression test, and the patch reads like architectural
sandbox hardening. For challenge work, this needs a concrete pre-`74caf544`
write target and a call path that consumes the corrupted dispatch/import state.

Exact default mainline overlaps:

- `CVE-2024-12053`: overlap ends at `20d9a7f^`, exact candidate
  `c000741f63186cf66ce422fb7aca04255d2d9465`.
- `CVE-2024-12381`: overlap ends at `74caf544^`, exact candidate
  `0b03a5d093800433f0fa2de88d33cb99e0a29ace`.
- `CVE-2024-12692`: overlap ends at `74caf544^`, exact candidate
  `0b03a5d093800433f0fa2de88d33cb99e0a29ace`.

Decision: hold all dispatch variants. `CVE-2024-12381` and `CVE-2024-12692`
are the better two if dispatch gets revisited.

## CPT Second Stage

`58f40780` adds signature validation to `WasmCodePointerTable` entries:

- `WasmCodePointerTableEntry` gains `signature_hash_` under the sandbox.
- Entry creation becomes `MakeCodePointerEntry(entrypoint, signature_hash)`.
- Entry reads become `GetEntrypoint(index, signature_hash)` and check the
  stored hash.
- x64 `MacroAssembler::ResolveWasmCodePointer` changes from a direct table load
  to two 32-bit signature-hash comparisons followed by
  `AbortReason::kWasmSignatureMismatch` on failure.
- `CallDescriptor` now stores a Wasm signature hash for indirect Wasm calls.
- `GetEntrypointWithoutSignatureCheck` remains only for explicit internal
  paths such as equality/debug/native-function handling.

Reachability classification: medium-high. The missing validation is closer to
an exploitable second-stage property than the dispatch rewrite: before the fix,
the table entry was just an entrypoint, so corrupting a Wasm code-pointer
handle or call-target metadata could select a valid Wasm entrypoint with an
incompatible signature. It is still not automatically arbitrary native
execution; a useful mismatched-signature target must be found.

Exact default mainline overlaps:

- `CVE-2024-12053`: no default-build overlap. At
  `c000741f63186cf66ce422fb7aca04255d2d9465`, `BUILD.gn` still had
  `v8_enable_wasm_code_pointer_table = false`; default enablement
  `bca5a5d` landed after the `20d9a7f` CVE fix.
- `CVE-2024-12381`: exact candidate
  `2fa717a2972e6a4b3897ce099ba2495bf87e1aad`. This is `a4d354fa^`; its
  `BUILD.gn` has `v8_enable_wasm_code_pointer_table = v8_enable_webassembly`,
  and it predates `58f40780`.
- `CVE-2024-12692`: exact candidate
  `0ea5a485280535ce427d547440b62acd03d5a037`. This is `3852cf8b^`; its
  `BUILD.gn` has `v8_enable_wasm_code_pointer_table = v8_enable_webassembly`,
  and it predates `58f40780`.

Decision: keep `CVE-2024-12381` + CPT and `CVE-2024-12692` + CPT. Drop
`CVE-2024-12053` + CPT for default builds; only hold it as a custom-GN variant
if intentionally enabling the temporary CPT flag before `bca5a5d`.

## Branch Notes

The local CVE index points at `refs/branch-heads/13.2` cherry-picks for all
three CVEs:

- `3fdedec` for `CVE-2024-12053`, branch position `13.2@{#22}`
- `aad03217` for `CVE-2024-12381`, branch position `13.2@{#30}`
- `92ed656` for `CVE-2024-12692`, branch position `13.2@{#34}`

Those branch commits were cherry-picked from mainline fixes. The branch was
created from main before the CPT default enablement (`bca5a5d`) and before the
mainline dispatch rewrite (`74caf544`). Local `git branch --contains` checks
for `74caf544` and `58f40780` showed main / later `13.3` refs, not the indexed
`13.2` branch line.

Branch implication: do not use the 13.2 cherry-pick dates as default-build CPT
overlap evidence. For dispatch, 13.2 may still contain the older table/import
architecture, but there is no local second-stage branch fix boundary to use.

## Recommended Next Work

1. Prioritize `CVE-2024-12381` at
   `2fa717a2972e6a4b3897ce099ba2495bf87e1aad` and `CVE-2024-12692` at
   `0ea5a485280535ce427d547440b62acd03d5a037`.
2. Reproduce the `ed5cd496` regression shapes on those exact revisions, then
   turn the compile-time type confusion into a stable cage read/write.
3. Inventory pre-`58f40780` Wasm call sites that consume CPT handles and find a
   mismatched-signature target that gives controllable memory effects.
4. Revisit dispatch only after the CPT path fails or after finding a concrete
   pre-`74caf544` corruptible `WasmImportData::call_origin` or table-use target.
