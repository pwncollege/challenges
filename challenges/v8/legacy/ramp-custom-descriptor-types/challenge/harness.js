const descriptorToken = ((Math.random() * 0xffffffff) >>> 0) || 0x1337;
const described = Object.freeze({ kind: "described-type" });
const descriptor = Object.freeze({ kind: "descriptor" });
const describedTypes = new WeakMap([[descriptor, described]]);
const descriptorTokens = new WeakMap([[descriptor, descriptorToken]]);
let lookedUpDescribed = false;
let lookedUpToken = false;

function requireDescriptor(value) {
    if (!describedTypes.has(value)) {
        throw new Error("unknown descriptor");
    }
}

function getDescribedType(value) {
    requireDescriptor(value);
    lookedUpDescribed = true;
    return describedTypes.get(value);
}

function getDescriptorToken(value) {
    requireDescriptor(value);
    lookedUpToken = true;
    return descriptorTokens.get(value);
}

const api = Object.freeze({ descriptor, getDescribedType, getDescriptorToken });

__PWN_SOLVE_SOURCE__;

if (typeof solve !== "function") throw new Error("define solve(api)");
const result = solve(api);
if (lookedUpDescribed && lookedUpToken &&
    result && result.descriptor === descriptor && result.described === described && result.token === descriptorToken) {
    print("__PWN_SUCCESS_MARKER__");
}
