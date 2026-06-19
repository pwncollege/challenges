# March 2025 First Stages + JSPI Stack / Jump-Buffer Issues

Verdict: **Hold the March chain-validation variant; drop the CVE-2025-2135 retired-stack variant unless the first-stage intro is proven before 2025-02-27.**

The strongest concrete pairing is `CVE-2025-2135 / b/400052777` with `b/384553540`, targeted at a revision immediately before the CVE fix:

- Best target revision: `8f51e033902da9b786358e6e82f0dc57b46464dc`, the parent of `8b490a9690b859346a68a3d2a7008b4e1852c3ea`.
- Why this revision: it is before `[turbofan] Fix TransitionElementsKindOrCheckMap` on 2025-03-04, but before `[wasm][jspi] Validate the in-sandbox chain of stacks` on 2025-03-06.
- What remains open there: the JSPI continuation-chain validation bug. The earlier retired-stack EPT fixes from 2025-02-27 and 2025-02-28 are already present, so this is not the best revision for the stale retired-stack/jump-buffer UAF variant.

There is no local combined challenge or exploit for this pair. The report below is therefore static commit and source-shape verification, not exploit validation.

## Component Evidence

### First Stage: CVE-2025-2135 / b/400052777

Fix commit:

- `8b490a9690b859346a68a3d2a7008b4e1852c3ea`
- Commit date: `2025-03-04T06:09:01-08:00`
- Subject: `[turbofan] Fix TransitionElementsKindOrCheckMap`
- Files: `src/compiler/node-properties.cc`, `test/mjsunit/compiler/regress-400052777.js`
- Message: "Take into account that TransitionElementsKindOrCheckMap might change the map of an aliasing object."

The one-line compiler fix is directly relevant to an object-confusion first stage. Before the fix, `NodeProperties::InferMapsUnsafe` treated maps as reliable after `TransitionElementsKindOrCheckMap` unless the receiver was the exact value input. The patch marks maps unreliable even when the transitioned object is not syntactically the same node:

```cpp
// `receiver` and `object` might alias, so
// TransitionElementsKindOrCheckMaps might change receiver's map.
result = kUnreliableMaps;
```

The regression test is helper-free JavaScript in the sense that it does not use `Sandbox.MemoryView`; it only uses optimization intrinsics:

- Flags: `--allow-natives-syntax --turbofan --no-always-turbofan`
- Shape: force two `TransitionElementsKindOrCheckMap` operations, then call the optimized function with `v2 == v3`.
- Relevant comments in the test:
  - `PACKED_SMI -> HOLEY_DOUBLE_ELEMENTS`
  - `HOLEY_DOUBLE_ELEMENTS -> HOLEY_ELEMENTS`
  - `If v2 == v3, v3 doesn't have HOLEY_DOUBLE_ELEMENTS anymore.`

This is credible type-confusion evidence, but it is not yet a caged read/write proof. The local material does not show:

- a stable fake-object/addrof primitive,
- controlled `FixedArray`/`FixedDoubleArray` confusion,
- a caged arbitrary read/write primitive,
- or a port to the challenge runner without `%` intrinsics.

So the first stage is **plausible HS-RW**, not proven HS-RW.

### Adjacent Late-Feb First Stage: CVE-2025-1920 / b/398065918

Fix commit:

- `7c3ccfc4429cb9fefe586a5359a12ebcbb101dd7`
- Commit date: `2025-02-27T08:53:02-08:00`
- Subject: `Reland^2 "[maglev] Clear the current allocation block only on effects"`
- Files: `src/maglev/maglev-graph-builder.cc`, `src/maglev/maglev-graph-builder.h`, `src/maglev/maglev-ir.h`

This fix lands after the first JSPI retired-stack EPT fix (`cafb8dd`, 06:36) and before the jmpbuf EPT fix (`a1c874`, 2025-02-28). That gives a real date-ordering overlap for the jmpbuf-EPT subvariant, for example at `8991ae8c46eb90e5b6280e14febaf46437bd895b` (`2025-02-27T08:42:06-08:00`): after `cafb8dd`, before `7c3ccfc`, before `a1c874`.

However, there is less direct primitive evidence than for CVE-2025-2135. The local index classifies it as type confusion / HS-RW potential, but the fix does not ship a small JS regression comparable to `regress-400052777.js`. Treat this as a **hold-low adjacent first stage**, not a stronger replacement.

## JSPI Second-Stage Evidence

### b/384549659: Retired Stack / Jmpbuf EPT Lifetime

Fix 1:

- `cafb8dd063b325c536d4ad1ac59263e5ac151c18`
- Commit date: `2025-02-27T06:36:01-08:00`
- Subject: `[wasm][jspi] Clear wasm stack EPT entry on exit`
- Message says a corrupted in-sandbox continuation could keep a reference to the retired stack EPT entry, and nulling converts stack UAF into null dereference.

Before this commit, `RetireWasmStack` accepted a raw `wasm::StackMemory*` and returned it to the stack pool without clearing the `WasmContinuationObject.stack` external pointer. The fix changes retirement to accept the continuation object and, under `V8_ENABLE_SANDBOX`, calls:

```cpp
continuation->set_stack(this, kNullAddress);
```

Fix 2:

- `a1c8741cd8d80ad53fd16e39544e2e07bab1ea2b`
- Commit date: `2025-02-28T08:30:49-08:00`
- Subject: `[wasm][jspi] Clear jmpbuf EPT entry when stack retires`
- Message says the jump buffer is an inner pointer to the stack and should be cleared for the same reason.

This adds:

```cpp
continuation->set_jmpbuf(this, kNullAddress);
```

Stronger hardening:

- `42c35cc770b53fd62b148ec395589b351298304e`
- Commit date: `2025-03-10T09:27:28-07:00`
- Subject: `[wasm][jspi] Remove jump buffer external pointer`
- Message says the direct jmpbuf external pointer "can be corrupted and increases the sandbox attack surface."

At `8b490^`, `WasmContinuationObject` still has:

```tq
parent: WasmContinuationObject|Undefined;
stack: ExternalPointer;
jmpbuf: ExternalPointer;  // Direct access to the stack's jump buffer.
```

That object layout is a concrete second-stage target. The catch is timing: by the best CVE-2025-2135 revision (`8b490^`), both EPT nulling fixes have landed. A CVE-2025-2135 + b/384549659 chain would require proving that b/400052777 was already exploitable before `cafb8dd` / `a1c874`, not merely before its Mar 4 fix. I did not find local evidence for that introduction date.

### b/384553540: In-Sandbox Continuation-Chain Validation

Fix commit:

- `9942165c0721b0653e861643a04d1314a33b6b5a`
- Commit date: `2025-03-06T03:59:43-08:00`
- Subject: `[wasm][jspi] Validate the in-sandbox chain of stacks`
- Files include `src/builtins/x64/builtins-x64.cc`, `src/execution/isolate.cc`, `src/wasm/stacks.h`, and `src/wasm/wasm-external-refs.cc`.

The commit message is explicit: validate the in-sandbox chain of `WasmContinuationObject`s by also building a C++-heap linked list of `JumpBuffer` objects, then compare pointers on return/suspend.

The fix adds, under sandbox builds:

```cpp
JumpBuffer* caller;
```

to `wasm::JumpBuffer`, and validates stack switches in `Isolate::SwitchStacks`:

```cpp
if (stack->jmpbuf()->state == wasm::JumpBuffer::Suspended) {
  stack->jmpbuf()->caller = old_stack->jmpbuf();
} else {
  DCHECK_EQ(stack->jmpbuf()->state, wasm::JumpBuffer::Inactive);
  SBXCHECK_EQ(old_stack->jmpbuf()->caller, stack->jmpbuf());
}
```

Before this fix, the x64 JSPI builtins loaded jump buffers from attacker-corruptible `WasmContinuationObject` fields, updated `RootIndex::kActiveContinuation`, and called `SyncStackLimit()` without validating that the in-sandbox `parent` chain matched an out-of-sandbox stack relationship.

At `8b490^`, examples from the pre-fix x64 path:

- `SaveState` loads `WasmContinuationObject::kJmpbufOffset` and fills the jump buffer.
- `ReloadParentContinuation` loads `WasmContinuationObject::kParentOffset`, stores it to `ActiveContinuation`, then loads that parent's jmpbuf.
- `Generate_WasmSuspend` loads `suspender.continuation`, then follows `suspender_continuation.parent` to choose the caller stack.
- `Generate_WasmResumeHelper` sets `target_continuation.parent = active_continuation`, stores `target_continuation` as active, and switches to its jmpbuf.

That is the closest March analogue to the later proven b/422645418 JSPI suspender chain: corrupt an in-sandbox JSPI object graph, then let stack-switch assembly trust it enough to move through a native `JumpBuffer`.

## Overlap Windows

### CVE-2025-2135 + b/384553540

This overlap is exact at the fix-window level:

- First-stage fix: `8b490a9690b859346a68a3d2a7008b4e1852c3ea`, `2025-03-04T06:09:01-08:00`.
- JSPI chain-validation fix: `9942165c0721b0653e861643a04d1314a33b6b5a`, `2025-03-06T03:59:43-08:00`.
- Best revision: `8f51e033902da9b786358e6e82f0dc57b46464dc` (`8b490^`).

This target keeps b/400052777 open and b/384553540 open. It does not keep the b/384549659 retired-stack EPT bugs open.

### CVE-2025-2135 + b/384549659

This should be treated as **not verified**.

The retired-stack fixes landed before the CVE-2025-2135 fix:

- Stack EPT nulling: `cafb8dd`, `2025-02-27T06:36:01-08:00`.
- Jmpbuf EPT nulling: `a1c874`, `2025-02-28T08:30:49-08:00`.
- CVE-2025-2135 fix: `8b490a`, `2025-03-04T06:09:01-08:00`.

The CVE might have existed before Feb 27, but this pass did not establish that. Without an introduction commit or a successful run of `regress-400052777.js` on `cafb8dd^`, the exact overlap is speculative.

### CVE-2025-1920 + b/384549659

This is a plausible adjacent late-Feb hold:

- `cafb8dd^` (`6c119915cf0f554f73af12ed3338b275d054d93b`) is before stack EPT nulling and before the final CVE-2025-1920 fix.
- `8991ae8c46eb90e5b6280e14febaf46437bd895b` is after stack EPT nulling, before the CVE-2025-1920 fix, and before jmpbuf EPT nulling, so it is the cleaner jmpbuf-only overlap.
- The primitive quality is not proven locally.

## Mechanics And Viability

Expected chain shape:

1. Use a first-stage compiler bug to get targeted writes inside the V8 heap sandbox.
2. Create real JSPI objects through public WebAssembly JSPI APIs.
3. Locate and corrupt `WasmContinuationObject.parent`, `WasmContinuationObject.stack`, or `WasmContinuationObject.jmpbuf`.
4. Trigger JSPI suspend/resume/return/exception unwinding so the builtins follow the corrupted in-sandbox continuation chain.
5. Convert the bad chain into native stack-switch confusion or stale stack/jump-buffer reuse.

For the March 4 target, the credible target is step 4 via missing parent-chain validation. The retired-stack UAF route is already partially neutralized by nulling `stack` and `jmpbuf` EPT entries.

Helper-free status:

- JSPI itself is public WebAssembly API, not a d8 helper.
- At this revision, JSPI is disabled by default and needs `--experimental-wasm-jspi`. The feature table lists `V(jspi, "javascript promise integration", false)` under staged features.
- Existing JSPI chain challenges in this repo run d8 with `--experimental-wasm-jspi` and normal compiler-tuning flags. That flag is acceptable challenge surface, but it must be documented.
- No `--sandbox-testing` or `Sandbox.MemoryView` should be needed for the JSPI surface. The missing piece is replacing direct field corruption with a real first-stage heap primitive.

## Variant Decisions

| Variant | Decision | Reason |
| --- | --- | --- |
| `CVE-2025-2135 + b/384553540` | **Hold** | Exact fix-window overlap exists; JSPI fix explicitly validates corrupted in-sandbox continuation chains; first-stage caged RW is not proven. |
| `CVE-2025-2135 + b/384549659` | **Drop for now** | The useful retired-stack fixes predate the CVE fix by several days; no local proof that b/400052777 is present and exploitable before `cafb8dd` / `a1c874`. |
| `CVE-2025-1920 + b/384549659` | **Hold-low** | Date ordering gives a jmpbuf-only overlap around 2025-02-27, but primitive evidence is weaker than CVE-2025-2135. |
| Other late-Feb HS-RW rows + b/384549659 | **Drop/queue only** | Inventory has nearby HS-RW-potential rows, but this pass found no stronger first-stage primitive evidence or exact chain material. |
| Post-`42c35cc` jmpbuf variants | **Drop** | The direct `WasmContinuationObject.jmpbuf` external pointer is removed; this eliminates the cleanest b/384549659 corruption target. |

## Next Work

To promote the hold to keep:

1. Run or port `test/mjsunit/compiler/regress-400052777.js` on `8f51e033` and confirm the pre-fix behavior is reachable in the challenge build shape.
2. Turn the elements-kind/map confusion into a caged read/write primitive, or prove it cannot be stabilized.
3. Build a JSPI harness at `8f51e033` that creates nested continuations/suspenders and confirms controlled corruption of `WasmContinuationObject.parent` changes the stack-switch path before `9942165c`.
4. Add a negative check on `9942165c` showing the same corrupted parent chain trips `SBXCHECK_EQ(old_stack->jmpbuf()->caller, stack->jmpbuf())`.

Until then, this is a conceptually strong but unproven chain candidate.
