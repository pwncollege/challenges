#!/bin/bash -ex

cat >/tmp/solve.js <<'EOF'
function solve(api) { return { d8Base: 0n, stackRet: 0n }; }
EOF

! /challenge/run /tmp/solve.js 2>&1 | grep -q 'pwn.college{'

cat >/tmp/solve.js <<'EOF'
function solve(api) {
    const partitionBase = api.stateRead(0x10n) & ~0xffffffffn;
    return {
        d8Base: api.read64(partitionBase + api.d8AnchorCandidates[0].offset),
        stackRet: api.read64(partitionBase + api.stackAnchorOffset),
    };
}
EOF

! /challenge/run /tmp/solve.js 2>&1 | grep -q 'pwn.college{'
