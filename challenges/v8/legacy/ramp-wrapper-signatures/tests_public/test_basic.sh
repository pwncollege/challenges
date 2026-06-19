#!/bin/bash -ex

cat >/tmp/solve.js <<'EOF'
function solve(api) { return api.instance.exports.callNarrow(); }
EOF

! /challenge/run /tmp/solve.js 2>&1 | grep -q 'pwn.college{'
