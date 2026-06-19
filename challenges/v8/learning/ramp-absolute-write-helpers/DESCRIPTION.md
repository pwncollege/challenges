After the 32-bit fixture access is wrapped into qword writes, the exploit also needs byte writes.
Those writes will later lay out byte strings, argument arrays, and return-chain data.
Byte payloads must be packed into little-endian qword values before they are stored.
A final partial qword should be padded with zero bytes.
This level keeps address discovery out of scope and teaches only byte packing on top of qword writes.

In this level, the harness provides only `api.write64(address, value)`.
Return a `writeBytes(address, bytes)` helper that writes byte arrays through qword stores, then run `/challenge/run` with your solve file to get the flag.
