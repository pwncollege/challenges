const token = ((Math.random() * 0xffffffff) >>> 0) || 1;
const scratch = 0x1000000000n + BigInt((Math.random() * 0x1000) >>> 0);
const memory = new Map();
function dispatchRead(addr) { return memory.get(addr.toString()) || 0; }
function dispatchWrite(addr, value) { memory.set(addr.toString(), value >>> 0); }
const api = Object.freeze({ scratch, dispatchRead, dispatchWrite, token });

__PWN_SOLVE_SOURCE__;

if (typeof solve !== "function") throw new Error("define solve(api)");
const abs = solve(api);
if (!abs || typeof abs.read32 !== "function" || typeof abs.write32 !== "function") throw new Error("return read32/write32");
abs.write32(scratch, token);
if (abs.read32(scratch) === token) print("__PWN_SUCCESS_MARKER__");
