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

function i32v(value) {
    const out = [];
    value |= 0;
    for (;;) {
        let byte = value & 0x7f;
        value >>= 7;
        const done = (value === 0 && (byte & 0x40) === 0) || (value === -1 && (byte & 0x40) !== 0);
        if (!done) byte |= 0x80;
        out.push(byte);
        if (done) return out;
    }
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

function makeTableModule(winValue) {
    return new Uint8Array([
        0x00, 0x61, 0x73, 0x6d,
        0x01, 0x00, 0x00, 0x00,
        ...section(1, [0x01, 0x60, 0x00, 0x01, 0x7f]),
        ...section(2, [0x01, ...str("env"), ...str("table"), 0x01, 0x70, 0x00, 0x02]),
        ...section(3, [0x03, 0x00, 0x00, 0x00]),
        ...section(7, [
            0x03,
            ...str("safe"), 0x00, 0x00,
            ...str("win"), 0x00, 0x01,
            ...str("call"), 0x00, 0x02,
        ]),
        ...section(10, [
            0x03,
            ...funcBody([0x41, 0x00]),
            ...funcBody([0x41, ...i32v(winValue)]),
            ...funcBody([0x41, 0x00, 0x11, 0x00, 0x00]),
        ]),
    ]);
}

const token = ((Math.random() * 0x3fffffff) >>> 0) || 1;
const table = new WebAssembly.Table({ element: "anyfunc", initial: 2 });
const instance = new WebAssembly.Instance(new WebAssembly.Module(makeTableModule(token)), { env: { table } });
table.set(0, instance.exports.safe);
table.set(1, instance.exports.safe);

const api = Object.freeze({
    table,
    dispatchSlot: 0,
    winFunction: instance.exports.win,
    indirectCall: instance.exports.call,
});

__PWN_SOLVE_SOURCE__;

if (typeof solve !== "function") throw new Error("define solve(api)");
solve(api);
if (instance.exports.call() === token) print("__PWN_SUCCESS_MARKER__");
