# Deep-Dive Verdict Summary

Generated: 2026-06-03.

This summary is scoped to post-Turboshaft candidates.
Pre-cutoff 2024 and early-2025 deep dives are archived under `../../../legacy/chain-candidate-analysis/deep-dives/`.

A `Keep` verdict means the chain is worth exploit/challenge work next.
It does not mean a new challenge has already been implemented.

## Existing Challenge-Proven Keeps

| Chain | Verdict | Report |
| --- | --- | --- |
| `CVE-2025-5419 + b/422645418` | Keep | [2025-5419-422645418.md](2025-5419-422645418.md) |
| `CVE-2025-5959 + b/422645418` | Hold | [2025-5959-422645418.md](2025-5959-422645418.md) |

## New Keep Variants

| Chain | Best target / notes | Report |
| --- | --- | --- |
| `CVE-2025-13226 / 13227 / 13228 / 13229 / 13230 + b/452605803 / b/446113730` | Built custom-descriptor variants now cover subtype validation, branch analysis, `ref.get_desc` exactness, imported `ref.func` exactness, and JS-to-Wasm exactness, with both dispatch-table escape halves accepted where the overlap is real. | [2025-customdesc-452605803.md](2025-customdesc-452605803.md) |
| `CVE-2026-7899 + WasmFX tags table` | Built and accepted as `chain-cve-2026-7899-514157844`. | [2026-wasmfx-tags.md](2026-wasmfx-tags.md) |
| `CVE-2026-9973 + WasmFX tags table / continuation variant` | Built and accepted as `chain-cve-2026-9973-514157844` and `chain-cve-2026-9973-505751230`. Attempted `chain-cve-2026-9973-502229895` was dropped because the real target already has dynamic continuation signature checks. | [2026-wasmfx-tags.md](2026-wasmfx-tags.md) |

These are the best new candidates for challenge implementation.
The WasmFX tag variants listed here are now challenge-backed with full helper-free private exploits; the remaining entries still require the same standard before being accepted as finished challenges.

`CVE-2026-7899 + b/503422307` was removed from the keep list after the remake attempt: the first-stage caged RW worked, but the dispatch-table second stage did not become a deterministic helper-free flag exploit.
The accepted `CVE-2026-7899 + WasmFX tags table` challenge uses that first stage with a different, verified second stage.

## Holds

| Chain family | Best variant / blocker | Report |
| --- | --- | --- |
| `CVE-2026-7337 + JSPI lifetime bugs` | Real overlap; first-stage targeted caged RW into JSPI is unproven. | [2026-7337-jspi.md](2026-7337-jspi.md) |
| Early-H2 2025 JSPI/WasmSuspendingObject | Best is `CVE-2025-9864 + b/432289371`; `CVE-2025-11219` variants are weaker. | [2025-9864-or-11219-jspi.md](2025-9864-or-11219-jspi.md) |
| `CVE-2026-7337 + b/498095290` | Dispatch-table sink is plausible; first-stage targeted corruption is unproven. | [2026-7337-498095290.md](2026-7337-498095290.md) |

## Drops For Default Challenge Construction

| Chain | Reason | Report |
| --- | --- | --- |
| Late-June 2025 TypedArray switcheroo | b/435630461 is real, but neither CVE-2025-6554 nor b/428112179 provides the required helper-free TypedArray map/external-pointer corruption. | [2025-6554-or-428112179-435630461.md](2025-6554-or-428112179-435630461.md) |
| `CVE-2025-10585 + b/446113730` | Drop for default x64; hold only as ARM64-specific research. | [2025-10585-446113730.md](2025-10585-446113730.md) |
| Wasm load-elim + 2026 bytecode-verifier gaps | Depends on sandbox-testing/internal bytecode helpers/fuzzer or unit-test bytecode paths. | [2026-wasm-loadelim-bytecode-verifier.md](2026-wasm-loadelim-bytecode-verifier.md) |

## Next Work

1. Build any remaining new Keep variants only after confirming the same standard already used by the accepted WasmFX/custom-descriptor chains.
2. For each implementation, require unmodified vulnerable V8, no helper or sandbox-testing interface, and a private test that performs the full exploit to the flag.
3. Re-run existing Keep challenges inside the proper Nix dev shell with `pwnshop test`.
