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

function makeImportCaller() {
    return new Uint8Array([
        0x00, 0x61, 0x73, 0x6d,
        0x01, 0x00, 0x00, 0x00,
        ...section(1, [0x01, 0x60, 0x00, 0x01, 0x7f]),
        ...section(2, [0x01, ...str("env"), ...str("getToken"), 0x00, 0x00]),
        ...section(3, [0x01, 0x00]),
        ...section(7, [0x01, ...str("call"), 0x00, 0x01]),
        ...section(10, [0x01, ...funcBody([0x10, 0x00])]),
    ]);
}

const token = ((Math.random() * 0x3fffffff) >>> 0) || 1;
const imports = Object.freeze({ getToken: () => token });
const instance = new WebAssembly.Instance(new WebAssembly.Module(makeImportCaller()), { env: imports });
const api = Object.freeze({ imports, instance });

__PWN_SOLVE_SOURCE__;

if (typeof solve !== "function") throw new Error("define solve(api)");
if (solve(api) === token) print("__PWN_SUCCESS_MARKER__");
