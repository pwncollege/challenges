const tokenObject = Object.freeze({ token: ((Math.random() * 0xffffffff) >>> 0) || 1 });
const wasmGlobal = new WebAssembly.Global({ value: "externref", mutable: true }, null);
const api = Object.freeze({ tokenObject, wasmGlobal });

__PWN_SOLVE_SOURCE__;

if (typeof solve !== "function") throw new Error("define solve(api)");
solve(api);
if (wasmGlobal.value === tokenObject) print("__PWN_SUCCESS_MARKER__");
