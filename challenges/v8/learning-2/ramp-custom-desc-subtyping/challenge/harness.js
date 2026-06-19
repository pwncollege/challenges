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

function describedType(descriptorType, supertype) {
    const out = [SUBTYPE];
    if (supertype === undefined) {
        out.push(0x00);
    } else {
        out.push(0x01, ...u32v(supertype));
    }
    out.push(DESCRIPTOR, ...u32v(descriptorType), STRUCT, 0x00);
    return out;
}

function descriptorType(describedTypeIndex, supertype) {
    const out = [SUBTYPE];
    if (supertype === undefined) {
        out.push(0x00);
    } else {
        out.push(0x01, ...u32v(supertype));
    }
    out.push(DESCRIBES, ...u32v(describedTypeIndex), STRUCT, 0x00);
    return out;
}

function makeCustomDescriptorSubtypeModule(tokens) {
    const baseType = 0;
    const derivedType = 1;
    const baseDescriptorType = 2;
    const derivedDescriptorType = 3;
    const makeBaseDescriptorType = 4;
    const makeDerivedDescriptorType = 5;
    const makeBaseValueType = 6;
    const makeDerivedValueType = 7;
    const acceptAsBaseType = 8;
    const validateDerivedDescriptorType = 9;
    const validateDerivedValueType = 10;

    const types = [
        ...u32v(8),
        REC, 0x04,
            ...describedType(baseDescriptorType),
            ...describedType(derivedDescriptorType, baseType),
            ...descriptorType(baseType),
            ...descriptorType(derivedType, baseDescriptorType),
        ...funcType([], [exactRef(baseDescriptorType)]),
        ...funcType([], [exactRef(derivedDescriptorType)]),
        ...funcType([exactRef(baseDescriptorType)], [ref(baseType)]),
        ...funcType([exactRef(derivedDescriptorType)], [ref(derivedType)]),
        ...funcType([ref(baseDescriptorType), ref(baseType)], [I32]),
        ...funcType([exactRef(derivedDescriptorType)], [I32]),
        ...funcType([ref(derivedType)], [I32]),
    ];

    const functionTypes = [
        makeBaseDescriptorType,
        makeDerivedDescriptorType,
        makeBaseValueType,
        makeDerivedValueType,
        acceptAsBaseType,
        validateDerivedDescriptorType,
        validateDerivedValueType,
    ];
    const functions = [
        ...u32v(functionTypes.length),
        ...functionTypes.flatMap(u32v),
    ];
    const exports = [
        ...u32v(7),
        ...str("makeBaseDescriptor"), 0x00, ...u32v(0),
        ...str("makeDerivedDescriptor"), 0x00, ...u32v(1),
        ...str("makeBaseValue"), 0x00, ...u32v(2),
        ...str("makeDerivedValue"), 0x00, ...u32v(3),
        ...str("acceptAsBase"), 0x00, ...u32v(4),
        ...str("validateDerivedDescriptor"), 0x00, ...u32v(5),
        ...str("validateDerivedValue"), 0x00, ...u32v(6),
    ];
    const codes = [
        ...u32v(7),
        ...funcBody([GC, GCOP.struct_new_default, ...u32v(baseDescriptorType)]),
        ...funcBody([GC, GCOP.struct_new_default, ...u32v(derivedDescriptorType)]),
        ...funcBody([OP.local_get, 0, GC, GCOP.struct_new_default, ...u32v(baseType)]),
        ...funcBody([OP.local_get, 0, GC, GCOP.struct_new_default, ...u32v(derivedType)]),
        ...funcBody([
            OP.local_get, 1, OP.drop,
            OP.local_get, 0, OP.drop,
            ...i32Const(tokens.acceptAsBase),
        ]),
        ...funcBody([OP.local_get, 0, OP.drop, ...i32Const(tokens.derivedDescriptor)]),
        ...funcBody([OP.local_get, 0, OP.drop, ...i32Const(tokens.derivedValue)]),
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

const tokenBase = ((((Math.random() * 0x10000000) >>> 0) << 2) & 0x3ffffffc) | 0;
const tokens = Object.freeze({
    acceptAsBase: tokenBase | 0x1,
    derivedDescriptor: tokenBase | 0x2,
    derivedValue: tokenBase | 0x3,
});
const wasm = new WebAssembly.Instance(new WebAssembly.Module(makeCustomDescriptorSubtypeModule(tokens))).exports;
const api = Object.freeze({
    makeBaseDescriptor: wasm.makeBaseDescriptor,
    makeDerivedDescriptor: wasm.makeDerivedDescriptor,
    makeBaseValue: wasm.makeBaseValue,
    makeDerivedValue: wasm.makeDerivedValue,
    acceptAsBase: wasm.acceptAsBase,
});

__PWN_SOLVE_SOURCE__;

if (typeof solve !== "function") {
    throw new Error("define solve(api)");
}

const result = solve(api);
if (!result || typeof result !== "object") {
    throw new Error("solve(api) must return { descriptor, value, accepted }.");
}
if (result.descriptor === result.value) {
    throw new Error("Return the derived descriptor object and the derived value object separately.");
}

let descriptorToken;
try {
    descriptorToken = wasm.validateDerivedDescriptor(result.descriptor);
} catch (error) {
    throw new Error("Return the descriptor made by makeDerivedDescriptor(), not the base descriptor.");
}

let valueToken;
try {
    valueToken = wasm.validateDerivedValue(result.value);
} catch (error) {
    throw new Error("Return the value made by makeDerivedValue(derivedDescriptor), not the base value.");
}

if (descriptorToken !== tokens.derivedDescriptor || valueToken !== tokens.derivedValue) {
    throw new Error("The returned derived descriptor/value pair did not validate.");
}
if (result.accepted !== tokens.acceptAsBase) {
    throw new Error("Pass the derived descriptor and derived value to acceptAsBase(), and return that token as accepted.");
}

print("__PWN_SUCCESS_MARKER__");
