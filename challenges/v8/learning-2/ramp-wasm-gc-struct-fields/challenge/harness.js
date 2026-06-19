const I32 = 0x7f;
const FUNC = 0x60;
const STRUCT = 0x5f;
const MUTABLE = 0x01;
const IMMUTABLE = 0x00;

const OP = {
    i32_const: 0x41,
    end: 0x0b,
};

function fail(message) {
    throw new Error(message);
}

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

function str(value) {
    return [value.length, ...Array.from(value, (c) => c.charCodeAt(0))];
}

function section(id, body) {
    return [id, ...u32v(body.length), ...body];
}

function funcBody(code) {
    const bytes = [0x00, ...code, OP.end];
    return [...u32v(bytes.length), ...bytes];
}

function normalizeBytes(value, name) {
    const bytes = Array.from(value || []);
    if (bytes.length === 0) fail(`${name} must be a non-empty byte array.`);
    for (const byte of bytes) {
        if (!Number.isInteger(byte) || byte < 0 || byte > 0xff) {
            fail(`${name} must contain byte values.`);
        }
    }
    return bytes;
}

function requireByte(bytes, index, expected, message) {
    if (bytes[index] !== expected) {
        fail(message);
    }
}

function checkStructType(bytes) {
    let i = 0;
    requireByte(bytes, i++, STRUCT, "A Wasm GC struct type starts with api.STRUCT.");
    requireByte(bytes, i++, 0x02, "Encode exactly two struct fields.");
    requireByte(bytes, i++, I32, "The first field's storage type should be i32.");
    requireByte(bytes, i++, MUTABLE, "The first field should be mutable.");
    requireByte(bytes, i++, I32, "The second field's storage type should be i32.");
    requireByte(bytes, i++, IMMUTABLE, "The second field should be immutable.");

    if (i !== bytes.length) {
        fail("The struct type has extra trailing bytes.");
    }
}

const expectedAnswer = 0x2d;
const api = Object.freeze({
    I32,
    STRUCT,
    MUTABLE,
    IMMUTABLE,
});

__PWN_SOLVE_SOURCE__;

if (typeof buildStructType !== "function") {
    fail("define buildStructType(api)");
}

const structType = normalizeBytes(buildStructType(api), "struct type");
checkStructType(structType);
const typeSectionBody = [0x02, ...structType, FUNC, 0x00, 0x01, I32];

const bytes = [
    0x00, 0x61, 0x73, 0x6d,
    0x01, 0x00, 0x00, 0x00,
    ...section(1, typeSectionBody),
    ...section(3, [0x01, 0x01]),
    ...section(7, [0x01, ...str("answer"), 0x00, 0x00]),
    ...section(10, [0x01, ...funcBody([OP.i32_const, expectedAnswer])]),
];

const instance = new WebAssembly.Instance(new WebAssembly.Module(new Uint8Array(bytes)));
if (instance.exports.answer() !== expectedAnswer) {
    fail("The generated module did not run the expected answer() function.");
}

print("__PWN_SUCCESS_MARKER__");
