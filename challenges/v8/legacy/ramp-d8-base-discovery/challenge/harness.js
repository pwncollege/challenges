const base = 0x555550000000n + (BigInt((Math.random() * 0x4000) >>> 0) << 12n);
const leakedPointer = base + 0x23450n;
const pageSize = 0x1000n;
function read32(addr) { return addr === base ? 0x464c457f : 0; }
const api = Object.freeze({ leakedPointer, pageSize, read32 });

__PWN_SOLVE_SOURCE__;

if (typeof solve !== "function") throw new Error("define solve(api)");
if (solve(api) === base) print("__PWN_SUCCESS_MARKER__");
