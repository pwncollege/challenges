#!/bin/bash -ex
cat >/tmp/test.js <<'JSEOF'
function warmup() {
  return 1;
}

%PrepareFunctionForOptimization(warmup);

if (typeof WinOOBRead !== "function") {
  throw new Error("WinOOBRead is missing");
}

if (typeof gc !== "undefined") {
  throw new Error("gc() should not be exposed");
}
JSEOF

/challenge/run /tmp/test.js
