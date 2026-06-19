#!/bin/bash -ex

cat >/tmp/solve.js <<'EOF'
function solve(api) { return null; }
EOF

! /challenge/run /tmp/solve.js 2>&1 | grep -q 'pwn.college{'

cat >/tmp/solve.js <<'EOF'
function solve(api) {
    const descriptor = api.makeBaseDescriptor();
    const value = api.makeBaseValue(descriptor);
    const accepted = api.acceptAsBase(descriptor, value);
    return { descriptor, value, accepted };
}
EOF

! /challenge/run /tmp/solve.js 2>&1 | grep -q 'pwn.college{'
