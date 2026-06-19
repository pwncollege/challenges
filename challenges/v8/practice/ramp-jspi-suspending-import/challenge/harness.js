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

function makeSuspendingImportCaller() {
    return new Uint8Array([
        0x00, 0x61, 0x73, 0x6d,
        0x01, 0x00, 0x00, 0x00,
        ...section(1, [0x01, 0x60, 0x01, 0x7f, 0x01, 0x6f]),
        ...section(2, [0x01, ...str("env"), ...str("suspend"), 0x00, 0x00]),
        ...section(3, [0x01, 0x00]),
        ...section(7, [0x01, ...str("call"), 0x00, 0x01]),
        ...section(10, [0x01, ...funcBody([0x41, ...u32v(callbackNonce), 0x10, 0x00])]),
    ]);
}

const tokenObject = Object.freeze({ jspiToken: ((Math.random() * 0xffffffff) >>> 0) || 1 });
const callbackNonce = ((Math.random() * 0x7fffffff) >>> 0) || 1;
const module = new WebAssembly.Module(makeSuspendingImportCaller());
let callbackCalls = 0;

function tokenCallback(value) {
    callbackCalls++;
    return Promise.resolve(value === callbackNonce ? tokenObject : null);
}

function createInstance(suspendingImport) {
    if (!(suspendingImport instanceof WebAssembly.Suspending)) {
        throw new Error("wrap api.tokenCallback with WebAssembly.Suspending before importing it");
    }
    return new WebAssembly.Instance(module, { env: { suspend: suspendingImport } });
}

const api = Object.freeze({ tokenCallback, createInstance });

__PWN_SOLVE_SOURCE__;

if (typeof solve !== "function") throw new Error("define solve(api)");

Promise.resolve()
    .then(() => solve(api))
    .then((result) => {
        if (result === tokenObject && callbackCalls === 1) {
            print("__PWN_SUCCESS_MARKER__");
        }
    });
