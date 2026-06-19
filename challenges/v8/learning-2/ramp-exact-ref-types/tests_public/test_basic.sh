#!/bin/bash -ex

cat >/tmp/solve.js <<'EOF'
function solve(api) {
    return api.cases.map((value) => api.routeExactRef(value));
}
EOF

! /challenge/run /tmp/solve.js 2>&1 | grep -q 'pwn.college{'
