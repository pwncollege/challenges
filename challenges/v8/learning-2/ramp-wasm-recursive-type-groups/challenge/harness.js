const I32 = 0x7f;
const FUNC = 0x60;
const STRUCT = 0x5f;
const REF_NULL = 0x63;
const SUBTYPE = 0x50;
const REC = 0x4e;
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

function checkBytes(bytes, offset, expected, name) {
    for (let j = 0; j < expected.length; j++) {
        if (bytes[offset + j] !== expected[j]) {
            fail(`${name} does not match the provided subtype definition.`);
        }
    }
}

function checkRecursiveGroup(group) {
    if (group[0] === SUBTYPE) {
        fail("These types refer to each other, so they need an api.REC group wrapper instead of standalone subtype entries.");
    }

    requireByte(group, 0, REC, "Start the recursive type group with api.REC.");
    requireByte(group, 1, 0x02, "The recursive group should contain exactly the two provided subtype definitions.");

    let i = 2;
    checkBytes(group, i, leftSubtype, "left subtype");
    i += leftSubtype.length;
    checkBytes(group, i, rightSubtype, "right subtype");
    i += rightSubtype.length;

    if (i !== group.length) {
        fail("The recursive group has extra trailing bytes.");
    }
}

const expectedAnswer = 0x2d;
const leftSubtype = Object.freeze([SUBTYPE, 0x00, STRUCT, 0x01, REF_NULL, 0x01, MUTABLE]);
const rightSubtype = Object.freeze([SUBTYPE, 0x00, STRUCT, 0x01, REF_NULL, 0x00, MUTABLE]);
const api = Object.freeze({
    REC,
    leftSubtype,
    rightSubtype,
});

__PWN_SOLVE_SOURCE__;

if (typeof buildRecursiveGroup !== "function") {
    fail("define buildRecursiveGroup(api)");
}

const recursiveGroup = normalizeBytes(buildRecursiveGroup(api), "recursive group");
checkRecursiveGroup(recursiveGroup);
const typeSectionBody = [0x02, ...recursiveGroup, FUNC, 0x00, 0x01, I32];

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
