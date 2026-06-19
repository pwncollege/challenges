#!/bin/bash -ex

cat >/tmp/wrong.js <<'EOF'
allocateProofObject();
const referenceCell = allocateReferenceCell();
referenceCell.prove();
EOF

! /challenge/run /tmp/wrong.js 2>&1 | grep -q 'pwn.college{'
