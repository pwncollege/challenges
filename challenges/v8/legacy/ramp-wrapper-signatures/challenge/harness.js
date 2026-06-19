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

function i64v(value) {
    const out = [];
    value = BigInt(value);
    for (;;) {
        let byte = Number(value & 0x7fn);
        value >>= 7n;
        const done = (value === 0n && (byte & 0x40) === 0) || (value === -1n && (byte & 0x40) !== 0);
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

function makeSignatureModule(value) {
    return new Uint8Array([
        0x00, 0x61, 0x73, 0x6d,
        0x01, 0x00, 0x00, 0x00,
        ...section(1, [
            0x03,
            0x60, 0x01, 0x7e, 0x01, 0x7e,
            0x60, 0x01, 0x7f, 0x01, 0x7f,
            0x60, 0x00, 0x01, 0x7e,
        ]),
        ...section(2, [
            0x02,
            ...str("env"), ...str("wide"), 0x00, 0x00,
            ...str("env"), ...str("narrow"), 0x00, 0x01,
        ]),
        ...section(3, [0x02, 0x02, 0x02]),
        ...section(7, [
            0x02,
            ...str("callWide"), 0x00, 0x02,
            ...str("callNarrow"), 0x00, 0x03,
        ]),
        ...section(10, [
            0x02,
            ...funcBody([0x42, ...i64v(value), 0x10, 0x00]),
            ...funcBody([0x42, ...i64v(value), 0xa7, 0x10, 0x01, 0xad]),
        ]),
    ]);
}

const token = 0x100000000n + BigInt((Math.random() * 0xffffff) >>> 0);
const imports = Object.freeze({ narrow: (x) => x, wide: (x) => x });
const instance = new WebAssembly.Instance(new WebAssembly.Module(makeSignatureModule(token)), { env: imports });
const api = Object.freeze({ token, instance });

__PWN_SOLVE_SOURCE__;

if (typeof solve !== "function") throw new Error("define solve(api)");
if (solve(api) === token) print("__PWN_SUCCESS_MARKER__");
