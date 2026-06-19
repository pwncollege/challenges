#!/bin/bash -ex

cat >/tmp/smoke.js <<'EOF'
const m = new WebAssembly.Module(new Uint8Array([
  0x00, 0x61, 0x73, 0x6d, 0x01, 0x00, 0x00, 0x00,
  0x01, 0x04, 0x01, 0x60, 0x00, 0x00
]));
if (!(m instanceof WebAssembly.Module)) throw new Error("bad module");
print("wasm-ok");
EOF

output=$(/challenge/run /tmp/smoke.js 2>&1)
echo "$output"
grep -q 'wasm-ok' <<< "$output"
