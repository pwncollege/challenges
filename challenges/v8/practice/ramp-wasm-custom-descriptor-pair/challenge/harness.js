const I32 = 0x7f;
const REF = 0x64;
const EXACT = 0x62;
const FUNC = 0x60;
const STRUCT = 0x5f;
const SUBTYPE = 0x50;
const REC = 0x4e;
const DESCRIPTOR = 0x4d;
const DESCRIBES = 0x4c;
const GC = 0xfb;

const OP = {
    drop: 0x1a,
    local_get: 0x20,
    i32_const: 0x41,
    end: 0x0b,
};

const GCOP = {
    struct_new_default: 0x01,
};

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

function i32v(value) {
    value |= 0;
    const out = [];
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

function ref(typeIndex) {
    return [REF, ...i32v(typeIndex)];
}

function exactRef(typeIndex) {
    return [REF, EXACT, ...i32v(typeIndex)];
}

function valtype(type) {
    return Array.isArray(type) ? type : [type];
}

function funcType(params, results) {
    const out = [FUNC, ...u32v(params.length)];
    for (const param of params) out.push(...valtype(param));
    out.push(...u32v(results.length));
    for (const result of results) out.push(...valtype(result));
    return out;
}

function funcBody(code) {
    const bytes = [0x00, ...code, OP.end];
    return [...u32v(bytes.length), ...bytes];
}

function i32Const(value) {
    return [OP.i32_const, ...i32v(value)];
}

function makeCustomDescriptorModule(expectedToken) {
    const describedType = 0;
    const descriptorType = 1;
    const makeDescriptorType = 2;
    const makeValueType = 3;
    const validateType = 4;

    const types = [
        ...u32v(4),
        REC, 0x02,
            SUBTYPE, 0x00, DESCRIPTOR, ...u32v(descriptorType), STRUCT, 0x00,
            SUBTYPE, 0x00, DESCRIBES, ...u32v(describedType), STRUCT, 0x00,
        ...funcType([], [exactRef(descriptorType)]),
        ...funcType([exactRef(descriptorType)], [ref(describedType)]),
        ...funcType([exactRef(descriptorType), ref(describedType)], [I32]),
    ];

    const functions = [
        ...u32v(3),
        ...u32v(makeDescriptorType),
        ...u32v(makeValueType),
        ...u32v(validateType),
    ];
    const exports = [
        ...u32v(3),
        ...str("makeDescriptor"), 0x00, ...u32v(0),
        ...str("makeValue"), 0x00, ...u32v(1),
        ...str("validate"), 0x00, ...u32v(2),
    ];
    const codes = [
        ...u32v(3),
        ...funcBody([GC, GCOP.struct_new_default, ...u32v(descriptorType)]),
        ...funcBody([OP.local_get, 0, GC, GCOP.struct_new_default, ...u32v(describedType)]),
        ...funcBody([OP.local_get, 1, OP.drop, OP.local_get, 0, OP.drop, ...i32Const(expectedToken)]),
    ];

    return new Uint8Array([
        0x00, 0x61, 0x73, 0x6d,
        0x01, 0x00, 0x00, 0x00,
        ...section(1, types),
        ...section(3, functions),
        ...section(7, exports),
        ...section(10, codes),
    ]);
}

const expectedToken = (((Math.random() * 0x3fffffff) >>> 0) | 0x1000) | 0;
const wasm = new WebAssembly.Instance(new WebAssembly.Module(makeCustomDescriptorModule(expectedToken))).exports;
const api = Object.freeze({
    makeDescriptor: wasm.makeDescriptor,
    makeValue: wasm.makeValue,
});

__PWN_SOLVE_SOURCE__;

if (typeof solve !== "function") {
    throw new Error("define solve(api)");
}

const result = solve(api);
if (!result || typeof result !== "object") {
    throw new Error("solve(api) must return { descriptor, value }.");
}
if (result.descriptor === result.value) {
    throw new Error("Return the descriptor object and the described value object separately.");
}

let token;
try {
    token = wasm.validate(result.descriptor, result.value);
} catch (error) {
    throw new Error("Return the descriptor from makeDescriptor() and the value from makeValue(descriptor).");
}

if (token !== expectedToken) {
    throw new Error("The returned objects did not validate as the descriptor/described pair.");
}

print("__PWN_SUCCESS_MARKER__");
