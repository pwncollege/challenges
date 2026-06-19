#!/bin/bash -ex

cat >/tmp/declared.js <<'EOF'
const proofObject = allocateProofObject();
leakWithDescriptor(proofObject, declaredDescriptor);
EOF

if /challenge/run /tmp/declared.js 2>&1 | grep -q 'pwn.college{'; then
    echo "declared-descriptor leak unexpectedly received the flag" >&2
    exit 1
fi
