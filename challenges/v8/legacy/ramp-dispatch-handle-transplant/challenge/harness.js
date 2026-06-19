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

function makeFunctions(winValue) {
    return new Uint8Array([
        0x00, 0x61, 0x73, 0x6d,
        0x01, 0x00, 0x00, 0x00,
        ...section(1, [0x01, 0x60, 0x00, 0x01, 0x7f]),
        ...section(3, [0x02, 0x00, 0x00]),
        ...section(7, [0x02, ...str("safe"), 0x00, 0x00, ...str("win"), 0x00, 0x01]),
        ...section(10, [0x02, ...funcBody([0x41, 0x00]), ...funcBody([0x41, ...i32v(winValue)])]),
    ]);
}

const token = ((Math.random() * 0x3fffffff) >>> 0) || 1;
const functions = new WebAssembly.Instance(new WebAssembly.Module(makeFunctions(token))).exports;
const donor = new WebAssembly.Table({ element: "anyfunc", initial: 1 });
const recipient = new WebAssembly.Table({ element: "anyfunc", initial: 1 });
donor.set(0, functions.win);
recipient.set(0, functions.safe);
function callRecipient() { return recipient.get(0)(); }
const api = Object.freeze({ donor, recipient, callRecipient });

__PWN_SOLVE_SOURCE__;

if (typeof solve !== "function") throw new Error("define solve(api)");
solve(api);
if (callRecipient() === token) print("__PWN_SUCCESS_MARKER__");
