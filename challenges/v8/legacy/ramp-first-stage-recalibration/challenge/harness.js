const token = ((Math.random() * 0xffffffff) >>> 0) || 1;
const bLeak = 0x680;
const deltaToXDispatch = 0x38;
const xPreflight = { dispatchFieldOffset: bLeak + deltaToXDispatch, value: 0 };
function write32(offset, value) { if (offset === xPreflight.dispatchFieldOffset) xPreflight.value = value >>> 0; }
function callXPreflight() { return xPreflight.value === token ? token : 0; }
const api = Object.freeze({ bLeak, deltaToXDispatch, token, write32, callXPreflight });

__PWN_SOLVE_SOURCE__;

if (typeof solve !== "function") throw new Error("define solve(api)");
solve(api);
if (callXPreflight() === token) print("__PWN_SUCCESS_MARKER__");
