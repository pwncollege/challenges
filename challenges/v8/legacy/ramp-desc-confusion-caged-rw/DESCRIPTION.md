After a descriptor confusion gives you access to the wrong field, the next job is shaping that access into a useful primitive.
Exploit code usually wants one stable interface that reads and writes by heap-cage byte offset.

This level still avoids Wasm and models only the post-confusion access shape.
The harness gives you a base-relative confused access object.
Return `read32(offset)` and `write32(offset, value)` functions that take cage offsets, then run `/challenge/run` with your solve file to get the flag.
