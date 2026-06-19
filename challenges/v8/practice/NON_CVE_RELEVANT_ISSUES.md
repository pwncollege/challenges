# V8 Non-CVE Relevant Issues, Post-Turboshaft

Scope: post-Turboshaft non-CVE issues referenced by active V8 practice and learning candidates.
The full historical inventory is archived at `../legacy/NON_CVE_RELEVANT_ISSUES.md`.

Cutoff: March 25, 2025.

| Issue | Capability | Active status |
| --- | --- | --- |
| b/422645418 | JSPI `WasmSuspenderObject` / native-stack corruption path. | Used by CVE-2025-5419 and held CVE-2025-5959 chain candidates. |
| b/410295354 | Wasm dispatch-table update type hardening. | Secondary H1 2025 candidate only. |
| b/413385716 | Per-isolate JS dispatch-table loading for cached wrappers. | Secondary H1 2025 candidate only. |
| b/40070746 / b/435630461 | TypedArray guard-region / ElementsKind switcheroo family. | Held or dropped for post-cutoff first stages until helper-free metadata corruption exists. |
| b/452605803 | `dispatch_table_for_imports` exposure / dispatch-table corruption escape path. | Challenge-backed with CVE-2025-13226 through CVE-2025-13230. |
| b/446113730 | Stale Wasm dispatch-table growth / code-pointer-table state escape path. | Challenge-backed with CVE-2025-13226 through CVE-2025-13230. |
| b/498095290 | Wasm dispatch-table parameter hardening. | Held with CVE-2026-7337; first-stage targeted corruption is unproven. |
| b/503422307 | WasmDispatchTable UAF / stale trusted dispatch-table state candidate. | Dropped for active challenge construction after remake attempt did not produce a deterministic helper-free flag exploit. |
| b/505751230 | WasmFX continuation signature-hash collision path. | Challenge-backed with CVE-2026-9973; active 2026 candidate. |
| b/514157844 | WasmFX tag identity / tags-table sandbox-boundary path. | Challenge-backed with CVE-2026-7899 and CVE-2026-9973. |
