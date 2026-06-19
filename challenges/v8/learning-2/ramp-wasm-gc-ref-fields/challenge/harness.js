const I32 = 0x7f;
const FUNC = 0x60;
const STRUCT = 0x5f;
const REF_NULL = 0x63;
const MUTABLE = 0x01;

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

function checkHolderStructType(bytes) {
    let i = 0;
    requireByte(bytes, i++, STRUCT, "The holder type should be a Wasm GC struct.");
    requireByte(bytes, i++, 0x01, "The holder struct should have one field.");
    requireByte(bytes, i++, REF_NULL, "The holder field should be encoded as a nullable reference.");
    requireByte(bytes, i++, targetTypeIndex, "The nullable reference should point at api.targetTypeIndex.");
    requireByte(bytes, i++, MUTABLE, "The holder reference field should be mutable.");

    if (i !== bytes.length) {
        fail("The holder struct type has extra trailing bytes.");
    }
}

const expectedAnswer = 0x2d;
const targetTypeIndex = 0x00;
const targetStructType = Object.freeze([STRUCT, 0x01, I32, MUTABLE]);
const api = Object.freeze({
    STRUCT,
    REF_NULL,
    MUTABLE,
    targetTypeIndex,
});

__PWN_SOLVE_SOURCE__;

if (typeof buildHolderStructType !== "function") {
    fail("define buildHolderStructType(api)");
}

const holderStructType = normalizeBytes(buildHolderStructType(api), "holder struct type");
checkHolderStructType(holderStructType);
const typeSectionBody = [
    0x03,
    ...targetStructType,
    ...holderStructType,
    FUNC, 0x00, 0x01, I32,
];

const bytes = [
    0x00, 0x61, 0x73, 0x6d,
    0x01, 0x00, 0x00, 0x00,
    ...section(1, typeSectionBody),
    ...section(3, [0x01, 0x02]),
    ...section(7, [0x01, ...str("answer"), 0x00, 0x00]),
    ...section(10, [0x01, ...funcBody([OP.i32_const, expectedAnswer])]),
];

const instance = new WebAssembly.Instance(new WebAssembly.Module(new Uint8Array(bytes)));
if (instance.exports.answer() !== expectedAnswer) {
    fail("The generated module did not run the expected answer() function.");
}

print("__PWN_SUCCESS_MARKER__");
