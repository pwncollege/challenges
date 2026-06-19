const token = ((Math.random() * 0xffffffff) >>> 0) || 1;
const cpt = { safe: () => 0, win: () => token };
const wrapper = Object.freeze({ kind: "imported-wrapper" });
let cptEntry = "safe";

function patchCpt(entry) {
    if (!Object.prototype.hasOwnProperty.call(cpt, entry)) {
        throw new Error("unknown code pointer table entry");
    }
    cptEntry = entry;
}

function callWrapper() { return cpt[cptEntry](); }
const api = Object.freeze({ wrapper, patchCpt, callWrapper });

__PWN_SOLVE_SOURCE__;

if (typeof solve !== "function") throw new Error("define solve(api)");
solve(api);
if (callWrapper() === token) print("__PWN_SUCCESS_MARKER__");
