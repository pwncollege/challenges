const callSite = { path: "", argv0: "" };
function writeCString(field, value) { callSite[field] = String(value); }
function invoke() { return callSite.path === "/challenge/catflag" && callSite.argv0 === "/challenge/catflag"; }
const api = Object.freeze({ writeCString, invoke });

__PWN_SOLVE_SOURCE__;

if (typeof solve !== "function") throw new Error("define solve(api)");
solve(api);
if (invoke()) print("__PWN_SUCCESS_MARKER__");
