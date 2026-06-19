#!/bin/bash -ex

cat >/tmp/wrong.js <<'EOF'
var didNothing = true;
EOF

! /challenge/run /tmp/wrong.js 2>&1 | grep -q 'pwn.college{'
