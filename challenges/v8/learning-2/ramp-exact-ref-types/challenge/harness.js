const exactToken = 0x70000000 | ((Math.random() * 0xffffff) >>> 0);
const subtypeToken = 0x51000000 | ((Math.random() * 0xffffff) >>> 0);
const cases = Object.freeze([
    Object.freeze({ isExact: true, label: "same dynamic type" }),
    Object.freeze({ isExact: false, label: "subtype-compatible" }),
]);

function requireKnownCase(value) {
    if (!cases.includes(value)) {
        throw new Error("unknown reference case");
    }
}

function routeExactRef(value) {
    requireKnownCase(value);
    if (!value.isExact) {
        throw new Error("routeExactRef only accepts the exact reference case");
    }
    return exactToken;
}

function routeSubtypeRef(value) {
    requireKnownCase(value);
    if (value.isExact) {
        throw new Error("routeSubtypeRef only accepts the subtype-compatible reference case");
    }
    return subtypeToken;
}

const api = Object.freeze({ cases, routeExactRef, routeSubtypeRef });

__PWN_SOLVE_SOURCE__;

if (typeof solve !== "function") throw new Error("define solve(api)");
const result = solve(api);
if (Array.isArray(result) && result[0] === exactToken && result[1] === subtypeToken) {
    print("__PWN_SUCCESS_MARKER__");
}
