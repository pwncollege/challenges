#!/bin/bash -ex

cat >/tmp/solve.js <<'EOF'
function solve(api) { return 0n; }
EOF

! /challenge/run /tmp/solve.js 2>&1 | grep -q 'pwn.college{'

cat >/tmp/solve.js <<'EOF'
function solve(api) {
    const signature = api.sigRead(0x30n);
    return api.read64(api.probeAddress);
}
EOF

! /challenge/run /tmp/solve.js 2>&1 | grep -q 'pwn.college{'
