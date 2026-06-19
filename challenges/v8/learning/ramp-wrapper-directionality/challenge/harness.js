function u32v(value) {
    const out = [];
    do {
        let byte = value & 0x7f;
        value >>>= 7;
        if (value) byte |= 0x80;
        out.push(byte);
    } while (value);
    return out;
}

function str(value) {
    return [value.length, ...Array.from(value, (c) => c.charCodeAt(0))];
}

function section(id, body) {
    return [id, ...u32v(body.length), ...body];
}

function funcBody(code) {
    return [...u32v(code.length + 2), 0x00, ...code, 0x0b];
}

function makeExternrefImportCaller() {
    return new Uint8Array([
        0x00, 0x61, 0x73, 0x6d,
        0x01, 0x00, 0x00, 0x00,
        ...section(1, [0x01, 0x60, 0x01, 0x6f, 0x01, 0x6f]),
        ...section(2, [0x01, ...str("env"), ...str("mark"), 0x00, 0x00]),
        ...section(3, [0x01, 0x00]),
        ...section(7, [0x01, ...str("call"), 0x00, 0x01]),
        ...section(10, [0x01, ...funcBody([0x20, 0x00, 0x10, 0x00])]),
    ]);
}

const tokenObject = Object.freeze({ token: ((Math.random() * 0xffffffff) >>> 0) || 1 });
const wasmToJsResult = Object.freeze({ direction: "wasm-to-js", token: tokenObject.token });
const wasmToJs = new WebAssembly.Instance(new WebAssembly.Module(makeExternrefImportCaller()), {
    env: {
        mark(value) {
            return value === tokenObject ? wasmToJsResult : null;
        },
    },
});
const api = Object.freeze({ tokenObject, wasmToJs });

__PWN_SOLVE_SOURCE__;

if (typeof solve !== "function") throw new Error("define solve(api)");
const result = solve(api);
if (Array.isArray(result)) {
    throw new Error("This ramp only asks for the Wasm-to-JS import-call result, not both wrapper directions.");
}
if (result === tokenObject) {
    throw new Error("Returning the token object does not prove the Wasm-to-JS import path ran.");
}
if (result !== wasmToJsResult) {
    throw new Error("Call api.wasmToJs.exports.call(api.tokenObject) and return the JavaScript import's result object.");
}
print("__PWN_SUCCESS_MARKER__");
