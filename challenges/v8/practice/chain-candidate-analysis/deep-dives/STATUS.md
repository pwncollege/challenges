# Deep-Dive Status

Generated: 2026-06-03.

This status file is scoped to post-Turboshaft candidates.
Pre-cutoff 2024 and early-2025 deep dives are archived under `../../../legacy/chain-candidate-analysis/deep-dives/`.

Completed:

| Output | Verdict | Notes |
| --- | --- | --- |
| `2025-5419-422645418.md` | Keep | Runtime verification now passes in `nix develop` with `pwnshop test challenges/v8/practice/chain-cve-2025-5419-422645418 --jobs 1 --timeout 300`. |
| `2025-5959-422645418.md` | Hold | Static verification still says the CVE-2025-5959 first stage and b/422645418 JSPI path are real, but runtime verification fails before the flag; direct run reaches the final forged-stack handoff and then segfaults. |
| `2025-customdesc-452605803.md` | Mixed | Keep `CVE-2025-13226 / 13227 / 13228 / 13229 / 13230 + b/452605803` and `+ b/446113730`; hold `CVE-2025-12428`. |
| `2026-7337-jspi.md` | Drop/Hold | Revisit found no helper-free evidence that CVE-2026-7337 upgrades to targeted caged RW/JSPI corruption. |
| `2026-wasm-loadelim-503422307.md` | Drop/Mixed | Drop `CVE-2026-7899 + b/503422307` after remake attempt; the 7899 first stage is salvaged separately via WasmFX; hold only if a deterministic dispatch-table trigger is later found. |
| `2026-wasmfx-tags.md` | Mixed | Keep `CVE-2026-7899 + WasmFX tags table` and `CVE-2026-9973 + WasmFX tags table`; hold `b/513009811 + WasmFX`; drop `CVE-2026-9896 + WasmFX`. |
| `2025-6554-or-428112179-435630461.md` | Drop | b/435630461 is well evidenced, but neither first stage drives helper-free TypedArray map/external-pointer corruption. |
| `2025-10585-446113730.md` | Drop/Hold | Drop for default x64 challenge generation; hold only as ARM64-specific research. |
| `2025-9864-or-11219-jspi.md` | Hold | Best variant is `CVE-2025-9864 + b/432289371`; `b/427946951` is conditional/low and `CVE-2025-11219` variants are weaker. |
| `2026-7337-498095290.md` | Drop/Hold | Exact overlap and dispatch-table mechanics documented, but CVE-2026-7337 targeted-corruption upgrade remains unproven. |
| `2026-wasm-loadelim-bytecode-verifier.md` | Drop/Hold-low | Drop for challenge construction; verifier path depends on sandbox-testing, internal bytecode helpers, fuzzing/full-verifier behavior, or unit-test bytecode. |

Active:

| Output | Candidate | Agent |
| --- | --- | --- |
None.

Queued:

None.
