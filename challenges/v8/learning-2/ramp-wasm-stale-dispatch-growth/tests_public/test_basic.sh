#!/bin/bash -ex

cat >/tmp/solve.js <<'EOF'
function solve(api) { return null; }
EOF

! /challenge/run /tmp/solve.js 2>&1 | grep -q 'pwn.college{'

cat >/tmp/solve.js <<'EOF'
function solve(api) {
    return api.readStaleSignature();
}
EOF

! /challenge/run /tmp/solve.js 2>&1 | grep -q 'pwn.college{'

cat >/tmp/solve.js <<'EOF'
function solve(api) {
    api.triggerDispatchGrowth();
    return 42n;
}
EOF

! /challenge/run /tmp/solve.js 2>&1 | grep -q 'pwn.college{'
