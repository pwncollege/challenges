#!/bin/bash -ex
cat > /tmp/test.js <<'JSEOF'
if (typeof Sandbox !== "object") throw new Error("Sandbox missing");
if (typeof Sandbox.getAddressOf !== "function") throw new Error("getAddressOf missing");
if (typeof Sandbox.getSizeOf !== "function") throw new Error("getSizeOf missing");
if (typeof WinCageRW !== "function") throw new Error("WinCageRW missing");

if (typeof WinTyperMismatch !== "undefined") throw new Error("WinTyperMismatch should be absent");
if ("MemoryView" in Sandbox) throw new Error("MemoryView should be absent");
if ("byteLength" in Sandbox) throw new Error("byteLength should be absent");
if (typeof Sandbox.getLibcBase === "function") throw new Error("getLibcBase should be absent");
if (typeof Sandbox.getD8Base === "function") throw new Error("getD8Base should be absent");
if (typeof Sandbox.getWasmMemoryStartOffsetLo === "function") throw new Error("getWasmMemoryStartOffsetLo should be absent");
if (typeof Sandbox.getWasmMemoryStartOffsetHi === "function") throw new Error("getWasmMemoryStartOffsetHi should be absent");

console.log("ok");
JSEOF
/challenge/run /tmp/test.js 2>&1 | grep -q ok
