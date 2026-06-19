#!/bin/bash -ex

cat >/tmp/solve.js <<'EOF'
function solve(api) { return null; }
EOF

! /challenge/run /tmp/solve.js 2>&1 | grep -q 'pwn.college{'

cat >/tmp/solve.js <<'EOF'
function solve(api) {
    const leftDescriptor = api.makeLeftDescriptor();
    const leftValue = api.makeLeftValue(leftDescriptor);

    return {
        leftValue,
        rightValue: leftValue,
        leftWithLeft: api.classifyLeft(leftValue, leftDescriptor),
        rightWithLeft: api.classifyLeft(leftValue, leftDescriptor),
        rightWithRight: 0,
        leftWithRight: 0,
    };
}
EOF

! /challenge/run /tmp/solve.js 2>&1 | grep -q 'pwn.college{'
