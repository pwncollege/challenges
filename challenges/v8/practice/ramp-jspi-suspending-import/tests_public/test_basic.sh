#!/bin/bash -ex

cat >/tmp/solve.js <<'EOF'
function solve(api) { return null; }
EOF

! /challenge/run /tmp/solve.js 2>&1 | grep -q 'pwn.college{'

cat >/tmp/solve.js <<'EOF'
async function solve(api) { return await api.tokenCallback(); }
EOF

! /challenge/run /tmp/solve.js 2>&1 | grep -q 'pwn.college{'
