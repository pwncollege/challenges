#!/bin/bash -ex

cat > /tmp/test.js <<'JSEOF'
(async function() {
  const helpers = ["gc", "RegisterWeak", "WasCollected", "WinAsyncGC", "setTimeout"];
  for (const name of helpers) {
    if (typeof globalThis[name] !== "function") {
      throw new Error(`${name} is missing`);
    }
  }

  const keepAlive = { marker: 1 };
  RegisterWeak(keepAlive);
  if (WasCollected() !== false) {
    throw new Error("WasCollected should be reset after RegisterWeak");
  }

  let rejected = false;
  try {
    WinAsyncGC();
  } catch (err) {
    rejected = String(err).includes("collection not observed");
  }

  if (!rejected) {
    throw new Error("WinAsyncGC should reject before collection");
  }

  gc();
  await new Promise((resolve) => setTimeout(resolve, 0));

  if (typeof WasCollected() !== "boolean") {
    throw new Error("WasCollected() did not return a boolean");
  }
})();
JSEOF

/challenge/run /tmp/test.js
