# V8 CVE And Issue Capability Index, Post-Turboshaft

Scope: post-Turboshaft candidates used by the active V8 practice and learning tracks.
The full historical pre-cutoff inventory is archived at `../legacy/CVE_ISSUE_CAPABILITY_INDEX.md`.

Cutoff: March 25, 2025.
V8's public Turboshaft transition writeup says WebAssembly uses Turboshaft throughout its pipeline by that point, and the JavaScript backend has moved to Turboshaft except for remaining frontend/builtin work.

## Challenge-Backed Rows

| ID | Bug | Capability | Active status |
| --- | --- | --- | --- |
| CVE-2025-5419 | b/420636529 | `HS-RW` via Turboshaft stale load / store-store alias-analysis issue. | Active practice candidate with b/422645418. |
| CVE-2025-5959 | b/422313191 | `HS-RW` via Wasm canonical equality type confusion. | Held practice candidate with b/422645418; source evidence is real but the local chain currently fails before the flag. |
| CVE-2025-13226 | b/446113732 | `HS-RW` via custom-descriptor subtype-validation confusion. | Challenge-backed with b/452605803 and b/446113730. |
| CVE-2025-13227 | b/446122633 | `HS-RW` via custom-descriptor type confusion. | Challenge-backed with b/452605803 and b/446113730. |
| CVE-2025-13228 | b/446124893 | `HS-RW` via over-exact `ref.get_desc`. | Challenge-backed with b/452605803 and b/446113730. |
| CVE-2025-13229 | b/446113731 | `HS-RW` via imported `ref.func` exactness confusion. | Challenge-backed with b/452605803 and b/446113730. |
| CVE-2025-13230 | b/446124892 | `HS-RW` via JS-to-Wasm exactness confusion. | Challenge-backed with b/452605803 and b/446113730. |
| CVE-2026-7899 | tracked in local 2026 reports | `HS-RW` via Wasm Turboshaft load-elimination bug. | Active practice candidate with WasmFX tags table. |
| CVE-2026-9973 | tracked in local 2026 reports | `HS-RW` via Wasm Turboshaft load-elimination bug. | Active practice candidate with WasmFX tags table / continuation variants. |

## Held Or Secondary Rows

| ID | Bug | Capability | Reason held |
| --- | --- | --- | --- |
| CVE-2025-12428 | b/447613211 | Custom-descriptor-adjacent prototype/IC state confusion. | Clean overlap with b/452605803, but no demonstrated caged read/write primitive yet. |
| CVE-2025-5280 | b/417169470 | Turboshaft late-load-elimination alias issue. | Potential dispatch-table overlap, but no chain proof yet. |
| CVE-2025-6554 | b/427663123 | Optional-chain hole-check elision. | Does not currently drive helper-free TypedArray map/external-pointer corruption for b/435630461. |
| CVE-2025-9864 | b/434513380 | Maglev object corruption candidate. | JSPI second-stage overlap exists, but targeted caged corruption into JSPI state is unproven. |
| CVE-2025-10585 | b/445380761 | ARM64 compiler issue. | Not portable to the default x64 challenge environment. |
| CVE-2025-11219 | b/439772737 | `WebAssembly.validate()` UAF candidate. | No local evidence of controlled caged writes. |
| CVE-2026-7337 | tracked in local 2026 reports | Maglev Smi-check elision. | JSPI/dispatch-table sinks are plausible, but targeted first-stage corruption is unproven. |
