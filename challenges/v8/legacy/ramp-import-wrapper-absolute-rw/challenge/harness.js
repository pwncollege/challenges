const token = ((Math.random() * 0xffffffff) >>> 0) || 1;
const scratch = 0x777700000000n + BigInt((Math.random() * 0x1000) >>> 0);
const processMemory = new Map();
function wrapperWrite(addr, value) { processMemory.set(addr.toString(), value >>> 0); }
function wrapperRead(addr) { return processMemory.get(addr.toString()) || 0; }
const api = Object.freeze({ scratch, token, wrapperRead, wrapperWrite });

__PWN_SOLVE_SOURCE__;

if (typeof solve !== "function") throw new Error("define solve(api)");
const abs = solve(api);
abs.write32(scratch, token);
if (abs.read32(scratch) === token) print("__PWN_SUCCESS_MARKER__");
