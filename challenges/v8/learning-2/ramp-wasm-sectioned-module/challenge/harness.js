function u32v(value) {
    const out = [];
    value >>>= 0;
    do {
        let byte = value & 0x7f;
        value >>>= 7;
        if (value) byte |= 0x80;
        out.push(byte);
    } while (value);
    return out;
}

const answerValue = 0x2d;
globalThis.expectedAnswer = answerValue;
globalThis.section = Object.freeze(function section(id, body) {
    return [id, ...u32v(body.length), ...body];
});
globalThis.sectionBodies = Object.freeze({
    type: Object.freeze([0x01, 0x60, 0x00, 0x01, 0x7f]),
    function: Object.freeze([0x01, 0x00]),
    export: Object.freeze([0x01, 0x06, 0x61, 0x6e, 0x73, 0x77, 0x65, 0x72, 0x00, 0x00]),
    code: Object.freeze([0x01, 0x04, 0x00, 0x41, answerValue, 0x0b]),
});

__PWN_SOLVE_SOURCE__;

if (typeof build !== "function") {
    throw new Error("solve.js must define build()");
}

const bytes = build();
const instance = new WebAssembly.Instance(new WebAssembly.Module(new Uint8Array(bytes)));
if (instance.exports.answer() === answerValue) {
    print("__PWN_SUCCESS_MARKER__");
}
