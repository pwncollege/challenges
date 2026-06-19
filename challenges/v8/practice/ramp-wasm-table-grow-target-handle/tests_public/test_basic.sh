#!/bin/bash -ex

cat >/tmp/solve.js <<'EOF'
function solve() {}
EOF

! /challenge/run /tmp/solve.js 2>&1 | grep -q 'pwn.college{'

cat >/tmp/solve.js <<'EOF'
const table1Offset = Sandbox.getAddressOf(calibrationTable1);
const table2Offset = Sandbox.getAddressOf(calibrationTable2);
const growTableOffset = Sandbox.getAddressOf(growTable);
const table1View = new DataView(new Sandbox.MemoryView(table1Offset + dispatchHandleFieldOffset, 4));
const table2View = new DataView(new Sandbox.MemoryView(table2Offset + dispatchHandleFieldOffset, 4));
const growView = new DataView(new Sandbox.MemoryView(growTableOffset + dispatchHandleFieldOffset, 4));
const handle1 = table1View.getUint32(0, true);
table2View.getUint32(0, true);
growView.setUint32(0, handle1, true);
growStagedTable();
EOF

! /challenge/run /tmp/solve.js 2>&1 | grep -q 'pwn.college{'

cat >/tmp/solve.js <<'EOF'
const table1Offset = Sandbox.getAddressOf(calibrationTable1);
const table2Offset = Sandbox.getAddressOf(calibrationTable2);
const growTableOffset = Sandbox.getAddressOf(growTable);
const table1View = new DataView(new Sandbox.MemoryView(table1Offset + dispatchHandleFieldOffset, 4));
const table2View = new DataView(new Sandbox.MemoryView(table2Offset + dispatchHandleFieldOffset, 4));
const growView = new DataView(new Sandbox.MemoryView(growTableOffset + dispatchHandleFieldOffset, 4));
const handle1 = table1View.getUint32(0, true);
const handle2 = table2View.getUint32(0, true);
const stride = (handle2 - handle1) | 0;
const targetHandle = (handle1 - stride * targetOffset) >>> 0;
growView.setUint32(0, targetHandle);
growStagedTable();
EOF

! /challenge/run /tmp/solve.js 2>&1 | grep -q 'pwn.college{'
