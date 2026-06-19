#!/bin/bash -ex

cat >/tmp/solve.js <<'EOF'
function solve(api) {
    const access = api.confusedAccess;
    return {
        read32(offset) { return access.read32FromBase(offset); },
        write32(offset, value) { return access.write32FromBase(offset, value); },
    };
}
EOF

! /challenge/run /tmp/solve.js 2>&1 | grep -q 'pwn.college{'
