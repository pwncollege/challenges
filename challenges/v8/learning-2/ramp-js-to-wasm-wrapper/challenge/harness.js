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

function makeExternrefEcho() {
    return new Uint8Array([
        0x00, 0x61, 0x73, 0x6d,
        0x01, 0x00, 0x00, 0x00,
        ...section(1, [0x01, 0x60, 0x01, 0x6f, 0x01, 0x6f]),
        ...section(3, [0x01, 0x00]),
        ...section(7, [0x01, ...str("echo"), 0x00, 0x00]),
        ...section(10, [0x01, ...funcBody([0x20, 0x00])]),
    ]);
}

const tokenObject = Object.freeze({ boundaryToken: ((Math.random() * 0xffffffff) >>> 0) || 1 });
const instance = new WebAssembly.Instance(new WebAssembly.Module(makeExternrefEcho()));
const originalEcho = instance.exports.echo;
let echoCalls = 0;
const api = Object.freeze({
    tokenObject,
    instance: Object.freeze({
        exports: Object.freeze({
            echo(value) {
                echoCalls++;
                return originalEcho(value);
            },
        }),
    }),
});

__PWN_SOLVE_SOURCE__;

if (typeof solve !== "function") throw new Error("define solve(api)");
const result = solve(api);
if (echoCalls === 0) {
    throw new Error("Call api.instance.exports.echo(api.tokenObject).");
}
if (result === tokenObject) print("__PWN_SUCCESS_MARKER__");
