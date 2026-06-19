# Modern V8 Ramp Designs

This note tracks the replacement `learning-2` ramp and the shorter modern
alternatives considered from `challenges/v8/practice`.

Constraint: `learning-2` replaces `learning`, so it cannot assume any skill that
only appears in `learning/`.

## Actual Standalone Triangle Ramp

Target chain spine:

```text
CVE-2025-13226 + b/452605803
  -> CVE-2025-13226 + b/446113730
  -> CVE-2025-13228 + b/446113730
```

Current draft location:

- `challenges/v8/learning-2/MODULE_PLAN.md`
- `challenges/v8/learning-2/module.yml`

Honest target length: 43 levels.
Current draft: 43 validated levels.

The count is high because the replacement ramp must teach four foundations
inside `learning-2` before the real CVEs:

1. Native process-memory finish from an already-provided absolute primitive.
2. Dispatch-table escape concepts backward from the produced native primitive.
3. V8 cage, tagged-pointer, and normalized caged-read/write interfaces.
4. Wasm binary, Wasm GC, exact refs, externrefs, tables, wrappers, and custom
   descriptors.

The sequence is:

| Range | Section | Purpose |
| --- | --- | --- |
| 1-11 | Native finish | Build the dynamic `/challenge/catflag` ret-chain from process read/write. |
| 12-15 | Dispatch escape effect | Teach imported-wrapper signature state, ASLR anchors, and table dispatch handles. |
| 16-18 | Caged primitive bedrock | Teach cage offsets, tagged refs, and normalized caged RW. |
| 19-30 | Wasm/custom-descriptor bedrock | Teach the Wasm machinery needed before the descriptor CVEs. |
| 31-35 | CVE-2025-13226 first stage | Move from modeled descriptor confusion to the real caged primitive. |
| 36 | First capstone | Full `13226 + 452605803` chain with ASLR-derived native anchors. |
| 37-38 | Second-stage swap | Add stale dispatch growth, then full `13226 + 446113730` chain. |
| 39-43 | First-stage swap | Add `ref.get_desc` exactness, then full `13228 + 446113730` chain. |

The key design choice is backwards ordering for the escape and native finish.
Learners see what a capability is for before they are asked to produce it from a
real bug.

## Validation Status

Validated in `nix develop`:

- All 43 challenges passed as `pwnshop test challenges/v8/learning-2`.
- The imported-wrapper proof was specifically fixed to use a live
  dispatch-state probe under ASLR instead of a fixed `d8` address.
- The capstone solves derive live process-image and stack/control-flow targets
  through the intended exploit path; they do not disable ASLR and do not use
  fixed `d8` or stack addresses.

## Shorter Modern Options

This audit excludes `CVE-2025-5419 + b/422645418`.

### Full `XA -> XB -> YB` Triangles

| Option | Honest ramp | Assessment |
| --- | ---: | --- |
| `13226+452 -> 13226+446 -> 13228+446` | 43 | Best teaching order. Starts with the cleanest descriptor subtype-validation bug, then swaps to a close `ref.get_desc` exactness first stage. |
| `13227+452 -> 13227+446 -> 13230+446` | 43-45 | Not shorter in practice. Starts with a less clean custom-descriptor confusion and ends with JS-to-Wasm exactness, which still needs the same Wasm/custom-descriptor foundation. |
| `13230+452 -> 13230+446 -> 13228+446` | 43-45 | Shorter exploit source, not a shorter ramp. JS-to-Wasm exactness is a worse first lesson because the wrapper boundary has to be taught before the descriptor model is settled. |
| Other `13226..13230` descriptor triangles | 43-47 | The shared costs dominate: Wasm/custom descriptors, dispatch-table escape, and native finish. First-stage choice only moves one or two levels. |
| `2026-7899/9973 + 514157844/505751230` triangles | 50+ | Newer, but longer. Adds optimized Wasm load-elimination plus WasmFX continuations/tags before the same sandbox-escape and native-finish burden. |

Conclusion for full triangles: the descriptor-dispatch triangle remains the best
short ramp. The shortest honest variant is still roughly the 43-level
`13226 -> 13228` design.

### Shorter If We Relax The Shape

| Option | Honest ramp | What we lose |
| --- | ---: | --- |
| Single descriptor chain, e.g. `13226+446` or `13230+452` | 34-38 | No stage-swap lesson. This is the only meaningfully shorter route. |
| Two-chain first-stage swap, e.g. `13226+446 -> 13228+446` | 39-41 | No second-stage replacement lesson. |
| Two-chain second-stage swap, e.g. `13226+452 -> 13226+446` | 39-41 | No first-stage replacement lesson. |
| Descriptor chain with fixed native tail | 34-37 | Abandons the dynamic native-finish standard from the current learning design. |

Pragmatic recommendation: if the user-facing goal is "quick first modern V8
chain", use a single descriptor chain after repairing the shared escape. If the
goal is "stage replacement", keep the full triangle and accept that it is not a
short ramp.

## Dropped Or Held Leads

| Option | Status | Reason |
| --- | --- | --- |
| `CVE-2025-5959 + b/422645418` | Hold | Very large Wasm canonical-type first stage plus the JSPI stack-switching escape family. It is not a shorter replacement ramp. |
| `2026-7899/9973 + 514157844/505751230` | Hold for later | Good modern material, but the existing learning-style path is longer because WasmFX adds a separate conceptual stack. |
| `CVE-2025-13230` as the first lesson | Drop for now | The exploit is compact, but the ramp starts at the JS-to-Wasm wrapper boundary, which is less teachable than `13226` subtype-validation confusion. |
| `CVE-2025-13227` as the first lesson | Drop for now | It is modern and usable, but does not shorten the foundation and is less direct than `13226`. |
