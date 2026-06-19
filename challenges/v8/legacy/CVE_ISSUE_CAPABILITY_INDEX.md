# V8 CVE And Issue Capability Index, 2024-2026

Status: initial inventory seed, generated 2026-06-03.

This document tracks V8/WebAssembly CVEs and related Chromium/V8 issues that are relevant to
heap-sandbox-era challenge construction. It is not a claim that every CVE below is challenge-ready.
Rows marked only by a Chrome release window need patch-level triage before challenge work.

## Capability Labels

| Label | Meaning |
| --- | --- |
| `HS-R` | In-heap-sandbox read or leak. Useful as a first-stage leak, not enough for a flag by itself. |
| `HS-RW` | In-heap-sandbox read/write or object corruption. Usually enough for d8 control under the cage, not enough to escape modern V8 heap sandbox alone. |
| `HS-EXEC` | Control of JS/Wasm/JIT execution inside the heap sandbox. Still needs an escape primitive for raw native effects. |
| `SBX-ESC` | V8 heap sandbox escape or out-of-cage native/trusted-memory corruption. Potentially enough to reach native code execution in d8. |
| `REN-ESC` | Browser renderer/process sandbox escape. None of the pure V8 rows below imply this without a separate browser bug. |
| `API/EMBEDDER` | V8 API/embedding surface; likely not reachable from ordinary challenge JavaScript without a custom embedder path. |
| `UNK` | Public row is too generic; capability needs fix diff and regression-test triage. |

Affected commit range convention:

- `unknown-intro..FIX^` means the public issue maps to a V8 fix commit, but the introducing commit
  is not yet identified.
- `release-window only` means the official Chrome Releases row is known, but I have not mapped the
  public bug ID to a unique V8 git fix commit yet.
- Challenge-grade candidates need an exact vulnerable revision, exact fixing commit, and a real
  exploit path. This table is the starting list, not the end of that process.

Primary sources used:

- Official Chrome Releases posts and Atom feed: https://chromereleases.googleblog.com/
- Local V8 git history at `/home/yans/code/v8`; public commits are linkable under
  `https://chromium.googlesource.com/v8/v8.git/+/COMMIT`.

## Non-CVE Issue Appendix

See `NON_CVE_RELEVANT_ISSUES.md` for the generated non-CVE issue inventory. That appendix covers
635 public non-CVE issue IDs from V8 commits dated 2024-01-01 through 2026-06-03 after excluding
issue IDs already mapped to CVE rows here. It is filtered for sandbox boundary work,
trusted/external-pointer hardening, bytecode-verifier or dispatch-table hardening,
JSPI/native-stack handling, OOB/bounds/overflow/UAF/race/type-confusion-style fixes, and comparable
exploit-chain relevance.

## Chain-Relevant Exact Mappings

| ID | Bug / issue | Affected commit range | Capability | Notes |
| --- | --- | --- | --- | --- |
| CVE-2024-0517 | b/1515930 | `unknown-intro..78dd4b31847ab1f5b06ef3d8742a9f3835fb6919^`; fixed by `78dd4b31847ab1f5b06ef3d8742a9f3835fb6919` | `HS-RW`, `HS-EXEC` potential | Maglev allocation-folding OOB write. Heap-sandbox first stage, not a sandbox escape alone. |
| CVE-2024-0518 | b/1507412 | `unknown-intro..46cb67e3b296e50d7fda5a58233d18b9f3dab0d5^`; fixed by `46cb67e3b296e50d7fda5a58233d18b9f3dab0d5` | `HS-RW` potential | V8 type confusion. |
| CVE-2024-0519 | b/1517354 | `unknown-intro..e0f2a195d87c9a06685121e0e783efd92d030df3^`; fixed by `e0f2a195d87c9a06685121e0e783efd92d030df3` | `HS-R` / `HS-RW` potential | OOB memory access. |
| CVE-2024-2887 | b/330575496 | `unknown-intro..c7d8916419a85c7f90d51592ed140eb1599212ec^`; fixed by `c7d8916419a85c7f90d51592ed140eb1599212ec` | `SBX-ESC` | GSAB / `ArrayBuffer.prototype.transfer` path. Existing helper-free challenge uses revision `f0b4342fe7f3849aeb19a1dc77f4c8ad5fd68688` and obtains full virtual address read/write. |
| CVE-2024-4947 | b/340221135 | `unknown-intro..b3c01ac1e60afc9addad9942f7a9a6c5e8a4a6da^`; fixed by `b3c01ac1e60afc9addad9942f7a9a6c5e8a4a6da` | `HS-RW`, `HS-EXEC` potential | Maglev module namespace AccessInfo type confusion. Existing challenge revision: `473318dfdb09464902c7633cad03b16431145800`. |
| CVE-2024-6100 | likely b/344608204 | `unknown-intro..422cdc5eddcadb53b8eafb099722fb211a35739e^`; fixed by `422cdc5eddcadb53b8eafb099722fb211a35739e` | `HS-RW` | Wasm canonicalized-type confusion; sufficient as a cage R/W first stage, insufficient for flag alone under modern heap sandbox. Existing chain revision: `1778ccde8eb86a01b4c16c34490a597235203b2d`. |
| CVE-2024-7024 | currently used challenge label | exact public mapping still needs confirmation | `SBX-ESC` | Existing chain treats this as trusted Wasm call-target corruption after CVE-2024-6100. Keep as chain-relevant but verify the public CVE/bug mapping before adding new variants. |
| Chromium issue 344963941 | b/344963941 | `unknown-intro..8859e5e21f4b5e587d9b75839c27befbdf1b9ddd^`; fixed by `8859e5e21f4b5e587d9b75839c27befbdf1b9ddd` | `SBX-ESC` | Irregexp native-stack / interpreter hardening issue. Used as second stage with CVE-2024-6100. |
| CVE-2025-5419 | b/420636529 | `unknown-intro..7bc0a67ebfbf44e7adab47fc2bbbe308660e27f4^`; fixed by `7bc0a67ebfbf44e7adab47fc2bbbe308660e27f4` | `HS-RW` | Stale JIT load / alias-analysis bug. Existing chain revision: `5c198837c21b9b6cde113c4cb35d00e6b368f9a5`. Not an escape alone. |
| CVE-2025-5959 | b/422313191 | `unknown-intro..a970eed8995bb1b2cd083c3c79cdefc79e84f8b7^`; fixed by `a970eed8995bb1b2cd083c3c79cdefc79e84f8b7` | `HS-RW` | Wasm canonical equality type confusion. Existing chain revision: `d7d46a7beb311a718780e77277f17d2edc9359df`. Not an escape alone. |
| Chromium issue 422645418 | b/422645418 | `unknown-intro..25e22b601c7ddb0a3491cdfb5c604e9e589278d2^`, then hardened by `9dcbe0576a48866e9f2c1a242fe6f875c55a6373` | `SBX-ESC` | JSPI suspender/native-stack corruption escape used as second stage for CVE-2025-5419 and CVE-2025-5959 chains. |
| Chromium issue 435630461 | b/435630461 | practical no-large-guard window starts after `b40a364440cbe4353a5eb01f567448872f5a1c6d`, guard restored by `ba28598bb8ccb3fbefd2ffa0baaeaddb8b66be89`, TypedArray checks relanded by `fb9c018080153be9e7517c59913a314842cb0f4b` | `SBX-ESC` potential | TypedArray switcheroo/native OOB-write family. Practical exploitability is version-window sensitive. |
| CVE-2025-6554 | b/427663123 | `unknown-intro..069790710f28b00ff8d7b4c665eef6b4eb8768f6^`; fixed by `069790710f28b00ff8d7b4c665eef6b4eb8768f6` and merge commits | `HS-RW` potential | Optional-chain hole-check elision. Candidate first stage only unless paired with an escape. |
| CVE-2025-10585 | b/445380761 | `unknown-intro..ec6c184783824fa8f974013aae28a45c36c0112f^`; fixed by `ec6c184783824fa8f974013aae28a45c36c0112f` | `HS-RW` / `HS-EXEC` potential | ARM64 compiler issue; not currently a good portable d8 challenge candidate without an ARM64 exploit path. |
| Chromium issue 446113730 | b/446113730 | fixed by `1d13848287a6e226862b1e1a90b6ae747c8a2ba2` with follow-ups | `SBX-ESC` potential | Regression used `--sandbox-testing`; challenge suitability requires a helper-free trigger. |
| Chromium issue 452605803 | b/452605803 | fixed by `58bdae122c0f44e427ee2ec7dda636620e7aade2` | `SBX-ESC` potential | Wasm dispatch-table/imports hardening. Needs standalone exploitability triage. |

## Full CVE Inventory

### 2024

| CVE | Bug | Public class | Fixed/disclosed | Potential capability | Range status |
| --- | --- | --- | --- | --- | --- |
| CVE-2024-0517 | b/1515930 | Out of bounds write in V8 | 2024-01-16 | `HS-RW`, `HS-EXEC` potential | exact mapping above |
| CVE-2024-0518 | b/1507412 | Type confusion in V8 | 2024-01-16 | `HS-RW` potential | exact mapping above |
| CVE-2024-0519 | b/1517354 | Out of bounds memory access in V8 | 2024-01-16 | `HS-R` / `HS-RW` potential | exact mapping above |
| CVE-2024-2884 | public bug not captured | Out of bounds read in V8 | 2024-01-30 | `HS-R` | release-window only |
| CVE-2024-3169 | public bug not captured | Use after free in V8 | 2024-01-30 | `HS-RW` potential | release-window only |
| CVE-2024-1938 | b/324596281 | Type confusion in V8 | 2024-02-27 | `HS-RW` potential | mapped candidate fix: `2109613ad4622028778a38fb418956fab8b478b6` |
| CVE-2024-1939 | b/323694592 | Type confusion in V8 | 2024-02-27 | `HS-RW` potential | mapped candidate fix: `eacf7f40e7dd2ca11b6e2f63dd8e8bd681ca91c4` / `fbd00f2178c1a437fd1362dab39c0144ea6b1b08` |
| CVE-2024-2173 | b/325893559 | Out of bounds memory access in V8 | 2024-03-05 | `HS-R` / `HS-RW` potential | mapped candidate fix: `7330f46163e8a2c10a3d40ecbf554656f0ac55e8` |
| CVE-2024-2174 | b/325866363 | Inappropriate implementation in V8 | 2024-03-05 | `UNK` | mapped candidate fix: `955d1972ef0a32cf44fc27cd32d055a7ddc30fcf` |
| CVE-2024-2887 | b/330575496 | Type confusion in WebAssembly | 2024-03-26 | `SBX-ESC` | exact mapping above |
| CVE-2024-3156 | public bug not captured | Inappropriate implementation in V8 | 2024-04-02 | `UNK` | release-window only |
| CVE-2024-3159 | public bug not captured | Out of bounds memory access in V8 | 2024-04-02 | `HS-R` / `HS-RW` potential | release-window only |
| CVE-2024-2625 | public bug not captured | Object lifecycle issue in V8 | 2024-04-16 | `HS-RW` potential | release-window only |
| CVE-2024-3832 | b/331358160 | Object corruption in V8 | 2024-04-16 | `HS-RW` potential | mapped candidate fix: `38e23f3a5d07022def739030d877ea224dd7952d` |
| CVE-2024-3833 | b/331383939 | Object corruption in WebAssembly | 2024-04-16 | `HS-RW` potential | mapped candidate fix: `292c5a8536ae0a70ac59d8ea8b3bdcceac44e8a5` |
| CVE-2024-3914 | b/330759272 | Use after free in V8 | 2024-04-16 | `HS-RW` potential | release-window only |
| CVE-2024-4059 | b/333182464 | Out of bounds read in V8 API | 2024-04-24 | `API/EMBEDDER`, `HS-R` | mapped candidate fix: `b505dbee47b2d718fad79aec7dd3ee440db28b37` |
| CVE-2024-4761 | b/339458194 | Out of bounds write in V8 | 2024-05-13 | `HS-RW` potential | mapped candidate fix: `81c2d9b9b7db1be972d1a67fc10fb86f960349ab` |
| CVE-2024-4947 | b/340221135 | Type confusion in V8 | 2024-05-15 | `HS-RW`, `HS-EXEC` potential | exact mapping above |
| CVE-2024-4949 | b/326607001 | Use after free in V8 | 2024-05-15 | `HS-RW` potential | mapped candidate fix: `73f62bd5882f878d4aea8b5b7249084eecd97525` |
| CVE-2024-5158 | b/338908243 | Type confusion in V8 | 2024-05-21 | `HS-RW` potential | mapped candidate fix: `b77915f9eac137650051b149afaae1c6adb62fcb` |
| CVE-2024-5274 | b/341663589 | Type confusion in V8 | 2024-05-23 | `HS-RW` potential | mapped candidate fix: `4565b6a2a184062f6b7555e4ebb329698a8570cd` |
| CVE-2024-5830 | public bug not captured | Type confusion in V8 | 2024-06-11 | `HS-RW` potential | release-window only |
| CVE-2024-5833 | public bug not captured | Type confusion in V8 | 2024-06-11 | `HS-RW` potential | release-window only |
| CVE-2024-5837 | public bug not captured | Type confusion in V8 | 2024-06-11 | `HS-RW` potential | release-window only |
| CVE-2024-5838 | public bug not captured | Type confusion in V8 | 2024-06-11 | `HS-RW` potential | release-window only |
| CVE-2024-5841 | public bug not captured | Use after free in V8 | 2024-06-11 | `HS-RW` potential | release-window only |
| CVE-2024-6100 | likely b/344608204 | Type confusion in V8 | 2024-06-18 | `HS-RW` | exact mapping above |
| CVE-2024-6101 | public bug not captured | Inappropriate implementation in WebAssembly | 2024-06-18 | `UNK` / possible `HS-RW` | release-window only |
| CVE-2024-6772 | b/346597059 | Inappropriate implementation in V8 | 2024-07-16 | `UNK` | mapped candidate fix/regression: `ab3bfaa628a5a1c5fb77bec8b7fecf6139d5ce74` |
| CVE-2024-6773 | b/347724915 | Type confusion in V8 | 2024-07-16 | `HS-RW` potential | mapped candidate fix: `96493c74c092f53c876d2e2944ff73edeea4f1bb` |
| CVE-2024-6779 | b/351327767 | Out of bounds memory access in V8 | 2024-07-16 | `HS-R` / `HS-RW` potential | mapped candidate fix: `01630b99b9f303a224de7fee4deb065e8aff1fab` |
| CVE-2024-7535 | b/352690885 | Inappropriate implementation in V8 | 2024-08-06 | `UNK` | mapped candidate fix: `7acd351777d9135f4e631c04b6f28a10e57952b9` |
| CVE-2024-7550 | b/355256380 | Type confusion in V8 | 2024-08-06 | `HS-RW` potential | mapped candidate fix: `9338284ec75623edf02c437aec339c1638345816` |
| CVE-2024-7965 | b/356196918 | Inappropriate implementation in V8 | 2024-08-21 | `UNK` | mapped candidate fix: `79c429b44b69b92033c7c132b4ceeadc9205c3b8` |
| CVE-2024-7971 | b/360700873 | Type confusion in V8 | 2024-08-21 | `HS-RW` potential | mapped candidate fix: `9d79b3bac9189a5b9782a78c360f2f8813959cd4` |
| CVE-2024-7972 | b/345960102 | Inappropriate implementation in V8 | 2024-08-21 | `UNK` | mapped candidate fix: `1b85c84da74a325826f4e940d1affee9d94c8beb` |
| CVE-2024-7974 | b/339141099 | Insufficient data validation in V8 API | 2024-08-21 | `API/EMBEDDER` | mapped candidate fix: `e1a61acd40f102934058d3a92c59aea49d2e9ab4` |
| CVE-2024-7969 | b/351865302 | Type confusion in V8 | 2024-08-28 | `HS-RW` potential | mapped candidate fix: `10b4403117735b40c77c6941644b512b48a71570` |
| CVE-2024-8194 | b/360533914 | Type confusion in V8 | 2024-08-28 | `HS-RW` potential | mapped candidate fix: `79f3f1276efa17a6172a0923dd13436ad8337a86` |
| CVE-2024-7970 | b/358485426 | Out of bounds write in V8 | 2024-09-02 | `HS-RW` potential | mapped candidate fix: `e75055b000b8c2455c60bfddda92ac4e57fcb0ab` |
| CVE-2024-8638 | b/362539773 | Type confusion in V8 | 2024-09-10 | `HS-RW` potential | mapped candidate fix: `309f157dd68a9af1490d5d820cc928f095ac9b93` |
| CVE-2024-8904 | b/365376497 | Type confusion in V8 | 2024-09-17 | `HS-RW` potential | mapped candidate fix: `000866bcb5d2f8868dbcb1b7b4a0d92dec9a006f` |
| CVE-2024-8905 | b/359949835 | Inappropriate implementation in V8 | 2024-09-17 | `UNK` | mapped candidate fix: `aa2cbd9e4ed70238694e07f1c525941aa1e04429` |
| CVE-2024-9121 | b/363538434 | Inappropriate implementation in V8 | 2024-10-01 | `UNK` | mapped candidate fix: `8068f489ec2c7e9de15e179c8c25b45224f7f96f` |
| CVE-2024-9122 | b/365802567 | Type confusion in V8 | 2024-10-01 | `HS-RW` potential | mapped candidate fix: `73d20a70839498fe1e6ca77e21d322732cddba0d` |
| CVE-2024-9370 | b/368311899 | Inappropriate implementation in V8 | 2024-10-01 | `UNK` | mapped candidate fix: `ed8e1cf4b4a6d0f1c9acc990f22a562db9491703` |
| CVE-2024-9602 | public bug not captured | Type confusion in V8 | 2024-10-08 | `HS-RW` potential | release-window only |
| CVE-2024-9603 | public bug not captured | Type confusion in V8 | 2024-10-08 | `HS-RW` potential | release-window only |
| CVE-2024-10230 | b/371565065 | Type confusion in V8 | 2024-10-22 | `HS-RW` potential | mapped candidate fix: `5fcbf3954eb9f7f8221f068b5324e5b6f04b5839` |
| CVE-2024-10231 | b/372269618 | Type confusion in V8 | 2024-10-22 | `HS-RW` potential | mapped candidate fix: `d9893f4856af26e78ba5021063ee2b1c61a3023b` |
| CVE-2024-11395 | b/377384894 | Type confusion in V8 | 2024-11-19 | `HS-RW` potential | mapped candidate fix: `ef6ed156f1b78006de28ef262b55468d511d6984` |
| CVE-2024-12053 | b/379009132 | Type confusion in V8 | 2024-12-03 | `HS-RW` potential | mapped candidate fix: `3fdedec45691a3ab005d62c3295436507e8d277a` |
| CVE-2024-12381 | b/381696874 | Type confusion in V8 | 2024-12-10 | `HS-RW` potential | mapped candidate fix: `aad03217f482b90f34ae559ca3492295f56e648e` |
| CVE-2024-12692 | b/382291459 | Type confusion in V8 | 2024-12-18 | `HS-RW` potential | mapped candidate fix: `92ed656a375cc0fa3346f00f7e0d9faf0df04db2` |
| CVE-2024-12693 | b/382190919 | Out of bounds memory access in V8 | 2024-12-18 | `HS-R` / `HS-RW` potential | mapped candidate fix: `aad648bd2af9815d0c48eeb78cbf3d8e6471d094` |
| CVE-2024-12695 | b/383647255 | Out of bounds write in V8 | 2024-12-18 | `HS-RW` potential | mapped candidate fix: `cb0d9e1d7b8889192e417363d0d7280a2ea114fa` |

### 2025

| CVE | Bug | Public class | Fixed/disclosed | Potential capability | Range status |
| --- | --- | --- | --- | --- | --- |
| CVE-2025-0291 | b/383356864 | Type confusion in V8 | 2025-01-07 | `HS-RW` potential | mapped candidate fix: `e606275980b9b0192d26115a77bd5bf37e49a07f` |
| CVE-2025-0434 | b/374627491 | Out of bounds memory access in V8 | 2025-01-17 | `HS-R` / `HS-RW` potential | mapped candidate fix: `5c3b50c26c50e68dbedf8ff991249e75e46ef06e` |
| CVE-2025-0611 | b/386143468 | Object corruption in V8 | 2025-01-22 | `HS-RW` potential | mapped candidate fix: `97e828af5cbcf50c3ff0064a4a5c22e18c18b4b5` |
| CVE-2025-0612 | b/385155406 | Out of bounds memory access in V8 | 2025-01-22 | `HS-R` / `HS-RW` potential | mapped candidate fix: `d35770876597b8c25de3c483b9368686f3a9fda8` |
| CVE-2025-0445 | b/392521083 | Use after free in V8 | 2025-02-04 | `HS-RW` potential | mapped candidate fix: `8834c16acfcc226202633132ff2a1ad2779b4ed8` |
| CVE-2025-0995 | b/391907159 | Use after free in V8 | 2025-02-12 | `HS-RW` potential | mapped candidate fix: `19ad509f7b61ef75bfb7a0b93f6246db1c78826d` |
| CVE-2025-0998 | b/386857213 | Out of bounds memory access in V8 | 2025-02-12 | `HS-R` / `HS-RW` potential | mapped candidate fix: `fd9d1daf420a26763daa013f7ba8bd5aa0c47bed` |
| CVE-2025-0999 | b/394350433 | Heap buffer overflow in V8 | 2025-02-18 | `HS-RW` potential | mapped candidate fix: `f6961c4066a99a774c97eb3a3939aa5489464eae` |
| CVE-2025-9479 | b/390743124 | Out of bounds read in V8 | 2025-02-25 | `HS-R` | mapped candidate fix: `95520eaf46efe69d64a41541a9f8c3a09d4d0ac5` |
| CVE-2025-1914 | b/397731718 | Out of bounds read in V8 | 2025-03-04 | `HS-R` | mapped candidate fix: `00b8fba79ed2d14ec8e7fb1e2bcc38f3d59afaef` |
| CVE-2025-1920 | b/398065918 | Type confusion in V8 | 2025-03-10 | `HS-RW` potential | mapped candidate fix: `7c3ccfc4429cb9fefe586a5359a12ebcbb101dd7` |
| CVE-2025-2135 | b/400052777 | Type confusion in V8 | 2025-03-10 | `HS-RW` potential | mapped candidate fix: `8b490a9690b859346a68a3d2a7008b4e1852c3ea` |
| CVE-2025-2137 | b/398999390 | Out of bounds read in V8 | 2025-03-10 | `HS-R` | mapped candidate fix: `812f91c5821259311a8d321b23654e7f74284a52` |
| CVE-2025-5280 | b/417169470 | Out of bounds write in V8 | 2025-05-27 | `HS-RW` potential | mapped candidate fix: `96d88f5f25963997c603e2fe0ec7c971e1af5245` |
| CVE-2025-5419 | b/420636529 | Out of bounds read and write in V8 | 2025-06-02 | `HS-RW` | exact mapping above |
| CVE-2025-5959 | b/422313191 | Type confusion in V8 | 2025-06-10 | `HS-RW` | exact mapping above |
| CVE-2025-6191 | b/420697404 | Integer overflow in V8 | 2025-06-17 | `HS-RW` potential | mapped candidate fix: `59579e02020412e150a032960411cfcd4a5157bf` |
| CVE-2025-6554 | b/427663123 | Type confusion in V8 | 2025-06-30 | `HS-RW` potential | exact mapping above |
| CVE-2025-7656 | public bug not captured | Integer overflow in V8 | 2025-07-15 | `HS-RW` potential | release-window only |
| CVE-2025-8010 | public bug not captured | Type confusion in V8 | 2025-07-22 | `HS-RW` potential | release-window only |
| CVE-2025-8011 | public bug not captured | Type confusion in V8 | 2025-07-22 | `HS-RW` potential | release-window only |
| CVE-2025-8880 | b/433533359 | Race in V8 | 2025-08-12 | `UNK` / possible `HS-RW` | mapped candidate fix: `1eda9300e26ec1aad95f98b6cb8e0d3ca6fb1e92` |
| CVE-2025-9132 | public bug not captured | Out of bounds write in V8 | 2025-08-19 | `HS-RW` potential | release-window only |
| CVE-2025-9864 | b/434513380 | Use after free in V8 | 2025-09-18 | `HS-RW` potential | mapped candidate fix: `bb0f74799bc9fb01df2bc0be98cacd6c36d32676` |
| CVE-2025-10585 | b/445380761 | Type confusion in V8 | 2025-09-18 | `HS-RW`, `HS-EXEC` potential | exact mapping above |
| CVE-2025-10890 | public bug not captured | Side-channel information leakage in V8 | 2025-09-23 | `HS-R` | release-window only |
| CVE-2025-10891 | public bug not captured | Integer overflow in V8 | 2025-09-23 | `HS-RW` potential | release-window only |
| CVE-2025-10892 | public bug not captured | Integer overflow in V8 | 2025-09-23 | `HS-RW` potential | release-window only |
| CVE-2025-11215 | b/439758498 | Off by one error in V8 | 2025-09-30 | `HS-R` / `HS-RW` potential | mapped candidate fix: `5666bca708c0a2f888b78e34281b00ed20356cb2` |
| CVE-2025-11219 | b/439772737 | Use after free in V8 | 2025-09-30 | `HS-RW` potential | mapped candidate fix: `4293cb47afcbb1575f51e1cbd63c7cf8f21f85ff` |
| CVE-2025-12036 | b/452296415 | Inappropriate implementation in V8 | 2025-10-28 | `UNK` | mapped candidate fix: `e4c04d524dcad9bb504db4b557dde746b655c42a` |
| CVE-2025-12428 | b/447613211 | Type confusion in V8 | 2025-10-28 | `HS-RW` potential | mapped candidate fix: `55496daf90227fb93311c535922f4b2142eeb72c` |
| CVE-2025-12429 | b/450618029 | Inappropriate implementation in V8 | 2025-10-28 | `UNK` | mapped candidate fix: `1f5fbf68240881514b88112d13c146facdb60244` |
| CVE-2025-12432 | b/439522866 | Race in V8 | 2025-10-28 | `UNK` / possible `HS-RW` | mapped candidate fix: `3bbb4dcb340460be8ff9afe51290cfe94d7188ff` |
| CVE-2025-12433 | b/449760249 | Inappropriate implementation in V8 | 2025-10-28 | `UNK` | mapped candidate fix: `b371b4f8ba073fb5c054273e8909bee5de574b35` |
| CVE-2025-12441 | b/444049512 | Out of bounds read in V8 | 2025-10-28 | `HS-R` | mapped candidate fix: `89ab7b1efb333b85f5669b10659b8b4abf14bb9b` |
| CVE-2025-12727 | b/454485895 | Inappropriate implementation in V8 | 2025-11-11 | `UNK` | mapped candidate fix: `b19529cce414aa9dd38d70d52a97228a9b432c7a` |
| CVE-2025-13042 | public bug not captured | Inappropriate implementation in V8 | 2025-11-11 | `UNK` | release-window only |
| CVE-2025-13223 | b/460017370 | Type confusion in V8 | 2025-11-17 | `HS-RW` potential | mapped candidate fix: `ece65a06fbaf4926078af001a817f1bb867d83c6` |
| CVE-2025-13224 | b/450328966 | Type confusion in V8 | 2025-11-17 | `HS-RW` potential | mapped candidate fix: `78d7b6b12c97b7a4f4a96230f61af54aa64b6fd6` |
| CVE-2025-13226 | b/446113732 | Type confusion in V8 | 2025-10-28 | `HS-RW` potential | mapped candidate fix: `48c3551179299151b044b2c161566465497c0407` |
| CVE-2025-13227 | b/446122633 | Type confusion in V8 | 2025-10-28 | `HS-RW` potential | mapped candidate fix: `48c3551179299151b044b2c161566465497c0407` |
| CVE-2025-13228 | b/446124893 | Type confusion in V8 | 2025-10-28 | `HS-RW` potential | mapped candidate fix: `48c3551179299151b044b2c161566465497c0407` |
| CVE-2025-13229 | b/446113731 | Type confusion in V8 | 2025-10-28 | `HS-RW` potential | mapped candidate fix: `48c3551179299151b044b2c161566465497c0407` |
| CVE-2025-13230 | b/446124892 | Type confusion in V8 | 2025-10-28 | `HS-RW` potential | mapped candidate fix: `48c3551179299151b044b2c161566465497c0407` |
| CVE-2025-13630 | b/456547591 | Type confusion in V8 | 2025-12-02 | `HS-RW` potential | mapped candidate fix: `00348ef5c3c11842465ca11e7e39706dbe91ed86` |
| CVE-2025-13721 | b/355120682 | Race in V8 | 2025-12-02 | `UNK` / possible `HS-RW` | mapped candidate fix: `b8b01791845cb77d5482f299310e9bfdcd012842` |
| CVE-2025-14766 | b/466786677 | Out of bounds read and write in V8 | 2025-12-16 | `HS-RW` potential | mapped candidate fix: `0865590a3443271c6e47b44bfeecac33ec08a25d` |

### 2026 Through 2026-06-03

| CVE | Bug | Public class | Fixed/disclosed | Potential capability | Range status |
| --- | --- | --- | --- | --- | --- |
| CVE-2026-0899 | b/458914193 | Out of bounds memory access in V8 | 2026-01-27 | `HS-R` / `HS-RW` potential | mapped candidate fix: `978f2b8a73fdc1c6d17fa5966dee81393e2f1533` |
| CVE-2026-0900 | b/465730465 | Inappropriate implementation in V8 | 2026-01-27 | `UNK` | mapped candidate fix: `5a96a3530f02f495eb17e5effa877aade940e8a2` |
| CVE-2026-0902 | b/469143679 | Inappropriate implementation in V8 | 2026-01-27 | `UNK` | mapped candidate fix: `2ebb924f4a51ec8022c1413775fc2e41736cc1a6` |
| CVE-2026-1220 | public bug not captured | Race in V8 | 2026-01-20 | `UNK` / possible `HS-RW` | release-window only |
| CVE-2026-1862 | b/479726070 | Type confusion in V8 | 2026-02-03 | `HS-RW` potential | mapped candidate fix: `64f39da03f085c62991c32e0d500642814b4c862` |
| CVE-2026-2649 | b/481074858 | Integer overflow in V8 | 2026-02-18 | `HS-RW` potential | mapped candidate fix: `05656ecfc7af9746c168fa77872870d620c6e0ee` |
| CVE-2026-3542 | b/485152421 | Inappropriate implementation in WebAssembly | 2026-03-03 | `UNK` / possible `HS-RW` | mapped candidate fix: `e6e9212e61783850e78548ed9ceef0e472d4e0c6` |
| CVE-2026-3543 | b/485267831 | Inappropriate implementation in V8 | 2026-03-03 | `UNK` | mapped candidate fix: `5251912fda3917d373b24190c36739b5af26c01d` |
| CVE-2026-3926 | b/478659010 | Out of bounds read in V8 | 2026-03-10 | `HS-R` | mapped candidate fix: `134c3696cd53593d7a668bf3cc88a06a1750c67d` |
| CVE-2026-3910 | b/491410818 | Inappropriate implementation in V8; in the wild | 2026-03-12 | `UNK`; likely first-stage until diff triage | mapped candidate fix: `c7c4c691bfb8e2bfe6849523ba31e41920d8f6da` |
| CVE-2026-4447 | b/486657483 | Inappropriate implementation in V8 | 2026-03-18 | `UNK` | mapped candidate fix: `bf136adcbb927aeec4548865c600d5498932e979` |
| CVE-2026-4450 | b/487746373 | Out of bounds write in V8 | 2026-03-18 | `HS-RW` potential | mapped candidate fix: `b67b37e7b00c929a401049ca7d97bdf9dfe51400` |
| CVE-2026-4457 | b/488803413 | Type confusion in V8 | 2026-03-18 | `HS-RW` potential | mapped candidate fix: `ed2551437b5a4c05e8dee8fda2f2d070ed4eccfd` |
| CVE-2026-4461 | b/490558172 | Inappropriate implementation in V8 | 2026-03-18 | `UNK` | mapped candidate fix: `871dc8735e630b258632ae87633a60a962df4cef` |
| CVE-2026-5279 | b/490642836 | Object corruption in V8 | 2026-03-31 | `HS-RW` potential | mapped candidate fix: `47d2f3621bf1f33933fde72cd8c01ec69b37c579` |
| CVE-2026-5861 | b/486927780 | Use after free in V8 | 2026-04-07 | `HS-RW` potential | mapped candidate fix: `912a425b2c81a03dbef9cb8f41d1e11c3fd4fb6d` |
| CVE-2026-5862 | b/470566252 | Inappropriate implementation in V8 | 2026-04-07 | `UNK` | mapped candidate fix: `a0570afad500d7882b2e4c5981ccb6cf00704df5` |
| CVE-2026-5863 | b/484527367 | Inappropriate implementation in V8 | 2026-04-07 | `UNK` | mapped candidate fix: `b54c7841e2cdb2c3a8c7c315daa41ca99ecd7329` |
| CVE-2026-5865 | b/491884710 | Type confusion in V8 | 2026-04-07 | `HS-RW` potential | mapped candidate fix: `fac60cc3fdf84591594354fb3629a2fcb376ff23` |
| CVE-2026-5871 | b/495679730 | Type confusion in V8 | 2026-04-07 | `HS-RW` potential | mapped candidate fix: `021c5b193bd4fa56587f398904bdfd3ede134801` |
| CVE-2026-5873 | b/496301615 | Out of bounds read and write in V8 | 2026-04-07 | `HS-RW` potential | mapped candidate fix: `f297f82fea9600676ba07a94e25764c6ffbd2ad5` |
| CVE-2026-5893 | b/487768771 | Race in V8 | 2026-04-07 | `UNK` / possible `HS-RW` | mapped candidate fix: `02cd73dfc58dbe73054382c85f9f126af9ce597e` |
| CVE-2026-5904 | b/483851888 | Use after free in V8 | 2026-04-07 | `HS-RW` potential | mapped candidate fix: `dffe5526c94d41a7662ceafd60bf38db447156b0` |
| CVE-2026-5892 | b/487568011 | Race in V8 | 2026-04-22 | `UNK` / possible `HS-RW` | release-window only |
| CVE-2026-6363 | b/495751197 | Type confusion in V8 | 2026-04-22 | `HS-RW` potential | mapped candidate fix: `a068030f517914f1f3f444fcb76c24f64c3e8f24` |
| CVE-2026-7337 | b/500880819 | Type confusion in V8 | 2026-04-28 | `HS-RW` potential | mapped candidate fix: `cc9a97f192319ed218c191fa20cbecd1bf51cb71` |
| CVE-2026-7899 | b/505481948 | Out of bounds read and write in V8 | 2026-05-05 | `HS-RW` potential | mapped candidate fix: `bb38f8914db99bd3bed6758132b104a9af00ca04` |
| CVE-2026-7902 | b/502030575 | Out of bounds memory access in V8 | 2026-05-05 | `HS-R` / `HS-RW` potential | mapped candidate fix: `7c165d90f0800b78c92fd0c13690e7b40683026a` |
| CVE-2026-7936 | b/490485402 | Object lifecycle issue in V8 | 2026-05-05 | `HS-RW` potential | mapped candidate fix: `5149ba38c669234a86ef4589ffbc4dea0ec245d2` |
| CVE-2026-7940 | b/493631402 | Use after free in V8 | 2026-05-05 | `HS-RW` potential | mapped candidate fix: `3942e1b16e4404c138df60655be1e27812e4d65c` |
| CVE-2026-7999 | b/493099941 | Inappropriate implementation in V8 | 2026-05-05 | `UNK` | mapped candidate fix: `45ec8457e14cbdc9a23b118f0ad48f7ac6d9bcff` |
| CVE-2026-8540 | b/496627235 | Type confusion in V8 | 2026-05-12 | `HS-RW` potential | mapped candidate fix: `e6c5b6cb3a656b95eb8849d2c274f92bfd29ef32` |
| CVE-2026-8570 | b/490353576 | Type confusion in V8 | 2026-05-12 | `HS-RW` potential | mapped candidate fix: `54fec2bb063997d5f545c90b8b342b5d620c994f` |
| CVE-2026-9896 | b/508811474 | Out of bounds write in V8 | 2026-05-27 | `HS-RW` potential | mapped candidate fix: `00f6ecd8a7cca6911789a11b7a7b01aaf41f925b` |
| CVE-2026-9938 | b/502300817 | Inappropriate implementation in V8 | 2026-05-27 | `UNK` | mapped candidate fix: `2e4d9a0eae234ba045faaf7bf58580aa1b8dd3a4` |
| CVE-2026-9968 | b/506499280 | Integer overflow in V8 | 2026-05-27 | `HS-RW` potential | mapped candidate fix: `89ba284081b3c2f96b612d2f78b79e370b0479f4` |
| CVE-2026-9973 | b/509268941 | Out of bounds write in V8 | 2026-05-27 | `HS-RW` potential | mapped candidate fix: `55cc1df03832e742cba83a2491fc5a13031be0f3` |
| CVE-2026-10022 | b/513289241 | Type confusion in V8 | 2026-05-27 | `HS-RW` potential | mapped candidate fix: `5d91cd2961f8eb284edf3972b38501997fd60025` |

## Immediate Triage Targets

1. Prioritize exact-diff triage for `SBX-ESC` rows and issues first: CVE-2024-2887, CVE-2024-7024 mapping, b/344963941, b/422645418, b/435630461, b/446113730, and b/452605803.
2. Then prioritize recent first-stage bugs that overlap known escape windows: CVE-2025-5419, CVE-2025-5959, CVE-2025-6554, CVE-2025-10585, and 2026 Wasm/Maglev `HS-RW` rows.
3. Treat `release-window only` rows as incomplete until the exact V8 fix commit and regression trigger are found.
