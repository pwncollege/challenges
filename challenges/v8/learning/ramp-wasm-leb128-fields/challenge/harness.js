function section(id, sizeBytes, body) {
    return [id, ...sizeBytes, ...body];
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

function fixedLittleEndian32(value) {
    return [
        value & 0xff,
        (value >>> 8) & 0xff,
        (value >>> 16) & 0xff,
        (value >>> 24) & 0xff,
    ];
}

const exportName = "answer" + "x".repeat(123);
const exportNameBytes = Array.from(exportName, (c) => c.charCodeAt(0));
const expectedAnswer = 0x2d;

globalThis.fields = Object.freeze({
    typeSectionSize: 5,
    functionSectionSize: 2,
    functionTypeIndex: 0,
    exportSectionSize: 134,
    exportNameLength: exportName.length,
    exportFunctionIndex: 0,
    codeBodySize: 4,
    codeSectionSize: 6,
});

__PWN_SOLVE_SOURCE__;

if (typeof fill !== "function") {
    throw new Error("solve.js must define fill()");
}

const enc = fill();
function encodedField(name) {
    const bytes = Array.from(enc?.[name] || []);
    if (bytes.length === 0) {
        throw new Error(`${name} must be an unsigned LEB128 byte array.`);
    }
    for (const byte of bytes) {
        if (!Number.isInteger(byte) || byte < 0 || byte > 0xff) {
            throw new Error(`${name} must contain byte values.`);
        }
    }

    const expected = u32v(fields[name]);
    if (bytes.length === 4 && bytes.every((byte, i) => byte === fixedLittleEndian32(fields[name])[i])) {
        throw new Error(`${name} is fixed-width little-endian. Encode the integer as unsigned LEB128.`);
    }
    if (bytes.length !== expected.length || bytes.some((byte, i) => byte !== expected[i])) {
        throw new Error(`${name} is not the unsigned LEB128 encoding of fields.${name}.`);
    }
    return bytes;
}

const codeBody = [0x00, 0x41, expectedAnswer, 0x0b];
const bytes = [
    0x00, 0x61, 0x73, 0x6d,
    0x01, 0x00, 0x00, 0x00,
    ...section(1, encodedField("typeSectionSize"), [0x01, 0x60, 0x00, 0x01, 0x7f]),
    ...section(3, encodedField("functionSectionSize"), [0x01, ...encodedField("functionTypeIndex")]),
    ...section(7, encodedField("exportSectionSize"), [
        0x01,
        ...encodedField("exportNameLength"), ...exportNameBytes,
        0x00, ...encodedField("exportFunctionIndex"),
    ]),
    ...section(10, encodedField("codeSectionSize"), [0x01, ...encodedField("codeBodySize"), ...codeBody]),
];

const instance = new WebAssembly.Instance(new WebAssembly.Module(new Uint8Array(bytes)));
if (instance.exports[exportName]() === expectedAnswer) {
    print("__PWN_SUCCESS_MARKER__");
}
