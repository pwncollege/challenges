const descriptor = Object.freeze({ token: ((Math.random() * 0xffffffff) >>> 0) || 1 });
const value = Object.freeze({ kind: "described-value" });
const descriptors = new WeakMap([[value, descriptor]]);
let usedRefGetDesc = false;
function ref_get_desc(v) {
    if (!descriptors.has(v)) throw new Error("unknown reference value");
    usedRefGetDesc = true;
    return descriptors.get(v);
}
const api = Object.freeze({ value, ref_get_desc });

__PWN_SOLVE_SOURCE__;

if (typeof solve !== "function") throw new Error("define solve(api)");
if (solve(api) === descriptor.token && usedRefGetDesc) print("__PWN_SUCCESS_MARKER__");
