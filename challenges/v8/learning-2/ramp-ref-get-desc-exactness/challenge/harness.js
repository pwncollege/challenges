const exactToken = 0x66000000 | ((Math.random() * 0xffff) >>> 0);
const genericToken = 0x33000000 | ((Math.random() * 0xffff) >>> 0);
const exactValue = Object.freeze({ label: "exact reference" });
const genericValue = Object.freeze({ label: "generic reference" });
const exactDescriptor = Object.freeze({ exact: true, token: exactToken });
const genericDescriptor = Object.freeze({ exact: false, token: genericToken });
const descriptors = new WeakMap([
    [exactValue, exactDescriptor],
    [genericValue, genericDescriptor],
]);
function ref_get_desc(v) {
    if (!descriptors.has(v)) throw new Error("unknown reference value");
    return descriptors.get(v);
}
const api = Object.freeze({ exactValue, genericValue, ref_get_desc });

__PWN_SOLVE_SOURCE__;

if (typeof solve !== "function") throw new Error("define solve(api)");
const result = solve(api);
if (Array.isArray(result) && result[0] === exactToken && result[1] === genericToken) {
    print("__PWN_SUCCESS_MARKER__");
}
