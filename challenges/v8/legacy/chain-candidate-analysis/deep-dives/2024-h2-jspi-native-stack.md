# 2024 H2 First Stages + JSPI Native-Stack / Stack-State Deep Dive

Generated: 2026-06-03.

Verdict: **Hold**, not keep. The strongest variant is `CVE-2024-10230` plus
`b/356419168` / `b/356176643` / `b/42202153`, because the first-stage fix has
a concrete Wasm GC wrapper-tiering type-confusion regression and the second
stage is direct sandbox/native-stack hardening. I did not find local evidence
for a helper-free caged read/write primitive or a complete first-to-second-stage
exploit for any H2 2024 variant, so none should be promoted to keep yet.

## Sources Checked

- Local triage: `chain-candidate-analysis/2024-h2.md`.
- Local indexes: `CVE_ISSUE_CAPABILITY_INDEX.md` and
  `NON_CVE_RELEVANT_ISSUES.md`.
- Local V8 checkout: `/home/yans/code/v8`, read-only for this pass. It has
  unrelated local edits in `include/v8-internal.h` and
  `src/sandbox/sandboxed-pointer-inl.h`; I did not modify or revert them.

## Second-Stage Evidence

### JSPI stack-state hardening: b/356419168, b/356176643, b/42202153

Main fix sequence:

- `8cccb138760e28d4c7ad8f89b6dd774f641f01f1`, 2024-10-17 11:16:19 +0000,
  `[wasm][jspi][sandbox] Verify stack state on stack switch`.
- Reverted by `7ec975d60fa282119f15cf75adcb23ada68d08b2`, 2024-10-17
  12:03:07 +0000.
- Relanded as `a9abc1649e1e5793af028a1b73992df651ceee5f`, 2024-10-17
  15:25:09 +0000.

The commit message is explicit sandbox evidence: it checks and updates target
stack state on stack switch "to prevent stack corruptions under the sandbox
security model." The diff upgrades `SwitchStackState` from a `debug_code`-only
check to a `V8_ENABLE_SANDBOX` check, adds a separate `Suspended` state to
`wasm::JumpBuffer`, creates newly allocated JSPI target continuations in
`Suspended` rather than `Inactive`, and makes resume paths require the expected
state before loading a jump buffer.

The strongest code comment in `src/wasm/stacks.h` describes the threat model:
if the external pointer to a jump buffer is corrupted and replaced with a
different jump buffer, the state check verifies the target is not active or
retired before resuming it. That is a real heap-sandbox boundary: an in-cage
write that can redirect or alias `WasmContinuationObject::jmpbuf` should be able
to influence a native stack switch unless this state check catches it.

Reachability is through JSPI stack switching. In the relevant October snapshots,
tests still use `--experimental-wasm-jspi`, and
`src/flags/flag-definitions.h` contains implications from
`--experimental-wasm-stack-switching` / `--experimental-wasm-growable-stacks` to
`--experimental-wasm-jspi`. This is challenge-acceptable if the runner opts in
with the flag, but it is not browser-default reachability.

### Suspend/resume parameter-count hardening: b/372749557

Main fixes:

- `552c4d6ecbbc2d0513d5ea40a112de776836cadc`, 2024-10-29 12:54:06 +0000,
  `[sandbox] Fix parameter count issues in ResumeGeneratorTrampoline`.
- `1d49cdf95498fe07ca867777f1a942eac2045bbd`, 2024-10-29 15:07:34 +0000,
  `[sandbox] Load parameter count from bytecode in suspend/resume`.

These are real sandbox hardening, but less directly JSPI/native-stack than the
October 17 stack-state CL. The first commit changes `ResumeGeneratorTrampoline`
to load the formal parameter count from the JS dispatch table when leaptiering
is enabled, instead of trusting `SharedFunctionInfo`. The second makes
Sparkplug suspend/resume generator operations load the parameter count from
bytecode, again avoiding `SharedFunctionInfo::formal_parameter_count`.

This gives a plausible second stage for an in-cage write that corrupts SFI or
dispatch metadata and then triggers generator suspend/resume stack/register
copying. I would keep it as a lower-confidence alternate, not as the primary
JSPI native-stack path.

## Exact Overlap

For mainline pairings, the relevant limiting second-stage fix is the reland
`a9abc1649e1e5793af028a1b73992df651ceee5f` on 2024-10-17. The original
`8cccb138...` landed earlier the same day but was reverted, so the useful
mainline cutoff is the reland.

Local ancestry checks confirmed:

- `5fcbf3954eb9f7f8221f068b5324e5b6f04b5839` (`CVE-2024-10230` main fix) is
  an ancestor of `a9abc164...`.
- `e7ccf0af1bdddd20dc58e1790a94739dba0209a3` (`CVE-2024-10231` main fix) is
  an ancestor of `a9abc164...`.
- The indexed `d9893f485...` for `CVE-2024-10231` is a branch-head merge and is
  not an ancestor of the mainline JSPI reland, so use `e7ccf0af...` for
  mainline overlap reasoning.
- `ef6ed156f1b78006de28ef262b55468d511d6984` (`CVE-2024-11395`) is after the
  2024-10-29 `b/372749557` fixes, so it is not an exact post-fix first-stage
  overlap. Any overlap would depend on an unknown introduction date before
  2024-10-29.

Good selected vulnerable mainline revisions, if this candidate is developed:

- For `CVE-2024-10230 + b/356.../b/42202153`: use
  `5fcbf3954eb9f7f8221f068b5324e5b6f04b5839^`
  (`792f2c275b4df075f33659d06ba2940a0a3e3e6a`, 2024-10-10 12:10:02 +0000).
  It is immediately before the first-stage fix and before the JSPI reland.
- For `CVE-2024-10230 + b/372749557`: the same parent revision is also before
  the October 29 parameter-count fixes.

All earlier H2 first-stage candidates (`CVE-2024-7971`, `8194`, `8638`,
`8904`) have broad inferred overlap with the October JSPI hardening if the JSPI
bug already existed, but their fixes land far earlier and introduction dates are
not mapped locally.

## First-Stage Candidates

### CVE-2024-10230 / b/371565065: Hold, strongest

Fix:

- `5fcbf3954eb9f7f8221f068b5324e5b6f04b5839`, 2024-10-10 12:31:01 +0000,
  `[wasm] Don't tier up wrapper if signature depends on other instance`.

The fix disables wasm-to-js wrapper tier-up when the JavaScript function was
imported in a different instance and the signature contains indexed types. The
regression `test/mjsunit/regress/wasm/regress-371565065.js` is strong primitive
evidence: it builds two modules with structurally confused indexed Wasm GC
types, imports a table from one instance into another, tiers up a wrapper, then
calls through the table so a value with source struct layout is treated as a
target struct layout and written through `struct.set`.

The regression still uses `--wasm-wrapper-tiering-budget=1` and
`--allow-natives-syntax` for `%CountUnoptimizedWasmToJSWrapper`, so it is not a
drop-in helper-free exploit. But the core trigger is ordinary Wasm/table/import
behavior; the native intrinsic is an assertion/tiering check. This is the only
reviewed H2 first-stage candidate with local evidence resembling a useful typed
object confusion rather than only a crash or bounds/resource guard.

Why hold: likely enough to attempt a caged RW exploit if the confused struct can
be shaped into object/array metadata corruption. Needs real primitive work.

### CVE-2024-7971 / b/360700873: Hold low

Fixes:

- Main: `97975764885482e92e53f65352446b5c4ea68f20`, 2024-08-20 11:12:51
  +0000, `[wasm] Spill all loop inputs before entering loop`.
- Indexed branch fix: `9d79b3bac9189a5b9782a78c360f2f8813959cd4`,
  2024-08-22 09:42:21 +0000, `[M126][wasm] Spill all loop inputs before
  entering loop`.
- Follow-up regression: `4ddcbf22b7be0a30c88c1485f0b5e4863d9aefd7`,
  2024-08-27, adds `test/mjsunit/regress/wasm/regress-360700873.js`.

The follow-up test is meaningful: it uses Liftoff loop inputs containing float
and reference values, GC during an imported call, and a crafted f64 bit pattern
that comments as a cleared weak pointer. That points to miscompiled stack/register
state with GC-visible references. However, the test uses `--expose-gc` and
`--liftoff-only`, and I did not find local evidence that it becomes a stable
cage read/write primitive. Keep as a possible research branch only.

### CVE-2024-8194 / b/360533914: Drop for this chain

Fix:

- `79f3f1276efa17a6172a0923dd13436ad8337a86`, 2024-08-20 10:33:14 +0000,
  `[wasm] Lower kMaxCanonicalTypes again`.

The fix reduces `kMaxCanonicalTypes` from Smi range to `kV8MaxWasmTypes` because
`ValueType` still stores canonicalized type indices in limited heap-type bits.
This is a valid type-safety fix, but locally it reads like a bounds/resource
guard around excessive canonical types. I found no local regression or exploit
shape showing object confusion or caged RW suitable for corrupting JSPI state.

### CVE-2024-8638 / b/362539773: Drop / hold very low

Fix:

- Main: `7860c9605e30623eb81129250790aa44757f0e4b`, 2024-08-29 13:49:06
  +0000, `[wasm] Skip WasmJSFunctions in js-to-wasm wrapper tier-up`.
- Indexed branch merge: `309f157dd68a9af1490d5d820cc928f095ac9b93`,
  2024-09-04 09:37:38 +0000.

The bug is a wrapper-tiering type assumption: tier-up replacement assumed all
same-signature exports had `WasmExportedFunctionData`, but re-exported
`WebAssembly.Function` imports can have `WasmJSFunctionData`. That is memory
safety relevant, but the local diff only adds a skip/check before updating code
and wrapper data. I did not find evidence for a controlled RW primitive.

### CVE-2024-8904 / b/365376497: Drop as first stage

Fix:

- Main: `906e41b88fa5b79d2afc699f8c4da87c4eb9c7e5`, 2024-09-10 11:14:36
  +0000, `[wasm][jspi] Fix JSPI + lazy deopt`.
- Indexed branch merge: `000866bcb5d2f8868dbcb1b7b4a0d92dec9a006f`,
  2024-09-13 10:40:32 +0000.
- Later regression: `208862261fe346f83786703da16c1872ebe1e579`, 2025-02-07,
  adds `test/mjsunit/regress/wasm/regress-365376497.js`.

This is JSPI stack-iterator/deoptimizer correctness, not a good first-stage
cage-corruption source. The fix follows ancestor stack segments to patch lazy
deopt activations. The later regression uses `--experimental-wasm-jspi` and
provokes deopt around `WebAssembly.promising`, but does not demonstrate caged
RW. Do not pair it as a first stage with another JSPI hardening bug.

### CVE-2024-10231 / b/372269618: Drop

Fixes:

- Main: `e7ccf0af1bdddd20dc58e1790a94739dba0209a3`, 2024-10-11 08:33:13
  +0000, `[wasm] Fix default externref/exnref reference`.
- Indexed branch merge: `d9893f4856af26e78ba5021063ee2b1c61a3023b`,
  2024-10-16 15:08:39 +0000.

The fix changes default reference values: `nullexternref` becomes `null`
instead of `undefined`, and `exnref` / `nullexnref` become `null` instead of
`wasm_null`. This may cause type confusion at the language level, but the local
evidence does not show object metadata corruption or an RW path. It overlaps in
time but is a poor first-stage candidate for this chain.

### CVE-2024-11395 / b/377384894: Drop as first stage

Fix:

- `ef6ed156f1b78006de28ef262b55468d511d6984`, 2024-11-06 10:25:40 +0000,
  `[wasm][jspi] Fix stack-switching in unwinder`.

The diff adds `StackFrame::WASM_TO_JS_FUNCTION` to the unwinder's
stack-switching handling. It is JSPI/native-stack adjacent, but it is not a
first-stage caged RW bug. Because it lands after both October second-stage
fixes, it is better tracked as separate JSPI hardening, not as the first half of
this chain.

## Helper-Free And Flags

No reviewed H2 variant is currently proven helper-free.

- The JSPI second stage requires a runner flag in the October 2024 snapshots:
  `--experimental-wasm-jspi` or an implied flag such as
  `--experimental-wasm-stack-switching`. That is acceptable for a pwn.college d8
  challenge if explicitly configured, but it is still a feature flag.
- The promising first-stage regression for `CVE-2024-10230` uses
  `--wasm-wrapper-tiering-budget=1` and `%CountUnoptimizedWasmToJSWrapper`.
  The intrinsic is not part of the memory corruption itself, but a challenge
  exploit must force tier-up without `--allow-natives-syntax` or justify a
  non-helper tiering flag.
- The `CVE-2024-7971` regression uses `--expose-gc` and `--liftoff-only`.
- None of the reviewed H2 material uses `--sandbox-testing` as the only
  corruption mechanism, but none provides the missing first-stage caged RW
  either.

## Keep / Hold / Drop

Hold:

- `CVE-2024-10230 + b/356419168/b/356176643/b/42202153`. Best target revision:
  `5fcbf3954eb9f7f8221f068b5324e5b6f04b5839^`. This has exact mainline overlap,
  a meaningful Wasm GC wrapper-tiering type-confusion regression, and a direct
  JSPI native-stack stack-state hardening target. Missing piece: helper-free
  caged RW and a demonstrated write to `WasmContinuationObject` / jump-buffer
  state.

Hold low:

- `CVE-2024-10230 + b/372749557`. Same first-stage promise, lower-confidence
  second stage through generator parameter-count corruption rather than direct
  JSPI native-stack switching.
- `CVE-2024-7971 + b/356...` only if someone wants to research Liftoff
  reference/GC state corruption. Current evidence is not enough for a challenge
  chain.

Drop for this chain:

- `CVE-2024-8194`, `CVE-2024-8638`, `CVE-2024-8904`, `CVE-2024-10231`, and
  `CVE-2024-11395` as first stages. They either lack local primitive evidence,
  are themselves JSPI/unwinder correctness bugs, or do not show a path from
  ordinary JS/Wasm to caged read/write.

## Next Work If Resumed

Start from `5fcbf3954eb9f7f8221f068b5324e5b6f04b5839^` with
`--experimental-wasm-jspi` enabled and no `--sandbox-testing`. First prove a
small read/write primitive from the `regress-371565065.js` shape without
`--allow-natives-syntax`; then inspect October 2024 object layouts for
`WasmContinuationObject` and its external-pointer `jmpbuf` field. The success
criterion is not just a crash: it needs a controlled alias or replacement of a
valid JSPI jump buffer followed by a stack switch that behaves differently on
`5fcb^` and traps after `a9abc164...`.
