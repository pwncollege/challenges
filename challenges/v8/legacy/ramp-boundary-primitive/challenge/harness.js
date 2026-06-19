const token = ((Math.random() * 0xffffffff) >>> 0) || 1;
const object = { slot: 0 };
const cPrimitive = Object.freeze({ loadField(name) { return object[name] || 0; }, storeField(name, value) { object[name] = value >>> 0; } });
function yPreflight(read32, write32) { write32("slot", token); return read32("slot") === token ? token : 0; }
const api = Object.freeze({ cPrimitive, yPreflight });

__PWN_SOLVE_SOURCE__;

if (typeof solve !== "function") throw new Error("define solve(api)");
if (solve(api) === token) print("__PWN_SUCCESS_MARKER__");
