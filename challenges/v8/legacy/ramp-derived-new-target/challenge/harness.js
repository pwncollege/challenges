const token = Object.freeze({ value: ((Math.random() * 0xffffffff) >>> 0) || 1 });

function ReplacementConstructor() {}
Object.defineProperty(ReplacementConstructor.prototype, "replacementToken", {
    value: token,
    writable: false,
    configurable: false,
});

class ParentConstructor {
    constructor() {
        this.parentSawNewTarget = new.target;
        this.parentSawPrototype = Object.getPrototypeOf(this);
    }
}

class DerivedConstructor extends ParentConstructor {
    constructor() {
        const derivedSawNewTarget = new.target;
        super();
        this.derivedSawNewTarget = derivedSawNewTarget;
    }
}

const api = Object.freeze({
    DerivedConstructor,
    ReplacementConstructor,
});

__PWN_SOLVE_SOURCE__;

if (typeof solve !== "function") {
    throw new Error("define solve(api)");
}

const result = solve(api);
if (!result || typeof result !== "object") {
    throw new Error("solve(api) must return the constructed object.");
}
if (Object.getPrototypeOf(result) !== ReplacementConstructor.prototype) {
    throw new Error("The returned object was not allocated with ReplacementConstructor.prototype.");
}
if (result.parentSawNewTarget !== ReplacementConstructor) {
    throw new Error("ParentConstructor did not observe ReplacementConstructor as new.target.");
}
if (result.derivedSawNewTarget !== ReplacementConstructor) {
    throw new Error("DerivedConstructor did not observe ReplacementConstructor as new.target.");
}
if (result.replacementToken !== token) {
    throw new Error("The returned object does not carry the replacement prototype token.");
}
print("__PWN_SUCCESS_MARKER__");
