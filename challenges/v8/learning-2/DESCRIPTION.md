This module teaches a modern V8 heap-sandbox exploit chain by starting from the capabilities the final exploit needs, then replacing each provided capability with the mechanism that creates it.

The target triangle is:

```text
CVE-2025-13226 + b/452605803
  -> CVE-2025-13226 + b/446113730
  -> CVE-2025-13228 + b/446113730
```

The first arc builds a full chain from a Wasm custom-descriptor first stage into a dispatch-table sandbox escape.
The second arc swaps the escape while keeping the first stage.
The third arc swaps the first stage while keeping the escape.

The path is standalone.
It does not assume that you completed the older V8 learning module.
