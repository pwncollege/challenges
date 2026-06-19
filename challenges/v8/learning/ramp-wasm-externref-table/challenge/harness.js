const tokenObject = Object.freeze({ tag: "externref-table-token", value: ((Math.random() * 0xffffffff) >>> 0) });
const referenceTable = new WebAssembly.Table({ element: "externref", initial: 1 });
const api = Object.freeze({ tokenObject, referenceTable, slot: 0 });

__PWN_SOLVE_SOURCE__;

if (typeof solve !== "function") throw new Error("define solve(api)");
solve(api);
if (referenceTable.get(0) === tokenObject) print("__PWN_SUCCESS_MARKER__");
