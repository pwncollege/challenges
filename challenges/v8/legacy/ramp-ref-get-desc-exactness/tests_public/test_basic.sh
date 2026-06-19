#!/bin/bash -ex

cat >/tmp/solve.js <<'EOF'
function solve(api) { const a = api.ref_get_desc(api.exactValue); return [a.token, a.token]; }
EOF

! /challenge/run /tmp/solve.js 2>&1 | grep -q 'pwn.college{'
