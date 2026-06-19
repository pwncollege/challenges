#!/bin/bash -ex

cat >/tmp/solve.js <<'EOF'
function solve() {}
EOF

! /challenge/run /tmp/solve.js 2>&1 | grep -q 'pwn.college{'

cat >/tmp/solve.js <<'EOF'
const donorOffset = Sandbox.getAddressOf(donorTable);
const recipientOffset = Sandbox.getAddressOf(recipientTable);
const donorView = new DataView(new Sandbox.MemoryView(donorOffset + dispatchHandleFieldOffset, 4));
const recipientView = new DataView(new Sandbox.MemoryView(recipientOffset + dispatchHandleFieldOffset, 4));
const donorHandle = donorView.getUint32(0, true);
recipientView.setUint32(0, donorHandle);
EOF

! /challenge/run /tmp/solve.js 2>&1 | grep -q 'pwn.college{'
