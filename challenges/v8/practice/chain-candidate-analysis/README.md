# Chain Candidate Analysis

Generated for post-Turboshaft V8 heap-sandbox-era chain hunting.

Inputs:

- `../CVE_ISSUE_CAPABILITY_INDEX.md`
- `../NON_CVE_RELEVANT_ISSUES.md`
- Local V8 git history at `/home/yans/code/v8`

Method:

1. Split candidate analysis by date window.
2. Pair plausible first-stage bugs (`HS-R`, `HS-RW`, `HS-EXEC`) with contemporaneous sandbox-boundary bugs (`SBX-ESC` or strong sandbox-hardening signal).
3. Keep only candidates with a plausible overlap before the relevant fixes.
4. Mark uncertainty explicitly.
5. Treat a candidate as challenge-ready only after a helper-free trigger and exploit path are verified against an unmodified vulnerable V8 revision.

Expected reports:

- `2025-h1.md`
- `2025-h2.md`
- `2026-h1.md`
- `INDEX.md`

Pre-cutoff 2024 and early-2025 reports are archived under `../../legacy/chain-candidate-analysis/`.
