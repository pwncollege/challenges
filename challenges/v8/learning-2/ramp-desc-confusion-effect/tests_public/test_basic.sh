#!/bin/bash -ex

cat >/tmp/solve.js <<'EOF'
api.value.prove();
EOF

! /challenge/run /tmp/solve.js 2>&1 | grep -q 'pwn.college{'
