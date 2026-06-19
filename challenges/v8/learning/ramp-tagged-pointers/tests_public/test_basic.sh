#!/bin/bash -ex

cat >/tmp/noop.js <<'EOF'
var didNothing = true;
EOF

! /challenge/run /tmp/noop.js 2>&1 | grep -q 'pwn.college{'
