const exactToken = 0x12000000 | ((Math.random() * 0xffff) >>> 0);
const subtypeToken = 0x34000000 | ((Math.random() * 0xffff) >>> 0);
const values = Object.freeze([
    Object.freeze({ boundaryExact: true, label: "exact boundary value" }),
    Object.freeze({ boundaryExact: false, label: "subtype-compatible boundary value" }),
]);

function requireKnownValue(value) {
    if (!values.includes(value)) {
        throw new Error("unknown boundary value");
    }
}

function routeExactBoundary(value) {
    requireKnownValue(value);
    if (!value.boundaryExact) {
        throw new Error("routeExactBoundary only accepts the exact boundary value");
    }
    return exactToken;
}

function routeSubtypeBoundary(value) {
    requireKnownValue(value);
    if (value.boundaryExact) {
        throw new Error("routeSubtypeBoundary only accepts the subtype-compatible boundary value");
    }
    return subtypeToken;
}

const api = Object.freeze({ values, routeExactBoundary, routeSubtypeBoundary });

__PWN_SOLVE_SOURCE__;

if (typeof solve !== "function") throw new Error("define solve(api)");
const result = solve(api);
if (Array.isArray(result) && result[0] === exactToken && result[1] === subtypeToken) print("__PWN_SUCCESS_MARKER__");
