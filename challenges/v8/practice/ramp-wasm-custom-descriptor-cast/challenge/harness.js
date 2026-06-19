const I32 = 0x7f;
const ANYREF = 0x6e;
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
    block: 0x02,
    return_: 0x0f,
    drop: 0x1a,
    local_get: 0x20,
    i32_const: 0x41,
    end: 0x0b,
};

const GCOP = {
    struct_new_default: 0x01,
    br_on_cast_desc_eq_fail: 0x26,
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

function describedType(descriptorType) {
    return [SUBTYPE, 0x00, DESCRIPTOR, ...u32v(descriptorType), STRUCT, 0x00];
}

function descriptorType(describedTypeIndex) {
    return [SUBTYPE, 0x00, DESCRIBES, ...u32v(describedTypeIndex), STRUCT, 0x00];
}

function brOnCastDescEqFail(typeIndex) {
    const sourceIsNullable = 1;
    const targetIsNullable = 0;
    const flags = (targetIsNullable << 1) | sourceIsNullable;
    return [
        GC, GCOP.br_on_cast_desc_eq_fail,
        flags,
        ...u32v(0),
        ANYREF,
        ...i32v(typeIndex),
    ];
}

function classifyByDescriptor(typeIndex, matchToken, mismatchToken) {
    return funcBody([
        OP.block, ANYREF,
            OP.local_get, 0,
            OP.local_get, 1,
            ...brOnCastDescEqFail(typeIndex),
            ...i32Const(matchToken),
            OP.return_,
        OP.end,
        OP.drop,
        ...i32Const(mismatchToken),
    ]);
}

function makeCustomDescriptorCastModule(tokens) {
    const leftType = 0;
    const rightType = 1;
    const leftDescriptorType = 2;
    const rightDescriptorType = 3;
    const makeLeftDescriptorType = 4;
    const makeRightDescriptorType = 5;
    const makeLeftValueType = 6;
    const makeRightValueType = 7;
    const classifyLeftType = 8;
    const classifyRightType = 9;
    const validateLeftValueType = 10;
    const validateRightValueType = 11;

    const types = [
        ...u32v(9),
        REC, 0x04,
            ...describedType(leftDescriptorType),
            ...describedType(rightDescriptorType),
            ...descriptorType(leftType),
            ...descriptorType(rightType),
        ...funcType([], [exactRef(leftDescriptorType)]),
        ...funcType([], [exactRef(rightDescriptorType)]),
        ...funcType([exactRef(leftDescriptorType)], [ref(leftType)]),
        ...funcType([exactRef(rightDescriptorType)], [ref(rightType)]),
        ...funcType([ANYREF, exactRef(leftDescriptorType)], [I32]),
        ...funcType([ANYREF, exactRef(rightDescriptorType)], [I32]),
        ...funcType([ref(leftType)], [I32]),
        ...funcType([ref(rightType)], [I32]),
    ];

    const functionTypes = [
        makeLeftDescriptorType,
        makeRightDescriptorType,
        makeLeftValueType,
        makeRightValueType,
        classifyLeftType,
        classifyRightType,
        validateLeftValueType,
        validateRightValueType,
    ];
    const functions = [
        ...u32v(functionTypes.length),
        ...functionTypes.flatMap(u32v),
    ];
    const exports = [
        ...u32v(8),
        ...str("makeLeftDescriptor"), 0x00, ...u32v(0),
        ...str("makeRightDescriptor"), 0x00, ...u32v(1),
        ...str("makeLeftValue"), 0x00, ...u32v(2),
        ...str("makeRightValue"), 0x00, ...u32v(3),
        ...str("classifyLeft"), 0x00, ...u32v(4),
        ...str("classifyRight"), 0x00, ...u32v(5),
        ...str("validateLeftValue"), 0x00, ...u32v(6),
        ...str("validateRightValue"), 0x00, ...u32v(7),
    ];
    const codes = [
        ...u32v(8),
        ...funcBody([GC, GCOP.struct_new_default, ...u32v(leftDescriptorType)]),
        ...funcBody([GC, GCOP.struct_new_default, ...u32v(rightDescriptorType)]),
        ...funcBody([OP.local_get, 0, GC, GCOP.struct_new_default, ...u32v(leftType)]),
        ...funcBody([OP.local_get, 0, GC, GCOP.struct_new_default, ...u32v(rightType)]),
        ...classifyByDescriptor(leftType, tokens.leftMatch, tokens.leftMismatch),
        ...classifyByDescriptor(rightType, tokens.rightMatch, tokens.rightMismatch),
        ...funcBody([OP.local_get, 0, OP.drop, ...i32Const(tokens.leftValue)]),
        ...funcBody([OP.local_get, 0, OP.drop, ...i32Const(tokens.rightValue)]),
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

const tokenBase = ((((Math.random() * 0x08000000) >>> 0) << 3) & 0x3ffffff8) | 0;
const tokens = Object.freeze({
    leftMatch: tokenBase | 0x1,
    leftMismatch: tokenBase | 0x2,
    rightMatch: tokenBase | 0x3,
    rightMismatch: tokenBase | 0x4,
    leftValue: tokenBase | 0x5,
    rightValue: tokenBase | 0x6,
});
const wasm = new WebAssembly.Instance(new WebAssembly.Module(makeCustomDescriptorCastModule(tokens))).exports;
const api = Object.freeze({
    makeLeftDescriptor: wasm.makeLeftDescriptor,
    makeRightDescriptor: wasm.makeRightDescriptor,
    makeLeftValue: wasm.makeLeftValue,
    makeRightValue: wasm.makeRightValue,
    classifyLeft: wasm.classifyLeft,
    classifyRight: wasm.classifyRight,
});

__PWN_SOLVE_SOURCE__;

if (typeof solve !== "function") {
    throw new Error("define solve(api)");
}

const result = solve(api);
if (!result || typeof result !== "object") {
    throw new Error("solve(api) must return { leftValue, rightValue, leftWithLeft, rightWithLeft, rightWithRight, leftWithRight }.");
}
if (result.leftValue === result.rightValue) {
    throw new Error("Return one value made with the left descriptor and another made with the right descriptor.");
}

let leftValueToken;
try {
    leftValueToken = wasm.validateLeftValue(result.leftValue);
} catch (error) {
    throw new Error("Return the value made by makeLeftValue(leftDescriptor) as leftValue.");
}

let rightValueToken;
try {
    rightValueToken = wasm.validateRightValue(result.rightValue);
} catch (error) {
    throw new Error("Return the value made by makeRightValue(rightDescriptor) as rightValue.");
}

if (leftValueToken !== tokens.leftValue || rightValueToken !== tokens.rightValue) {
    throw new Error("The returned leftValue/rightValue objects did not validate.");
}
if (result.leftWithLeft !== tokens.leftMatch) {
    throw new Error("classifyLeft(leftValue, leftDescriptor) should take the descriptor-match path.");
}
if (result.rightWithLeft !== tokens.leftMismatch) {
    throw new Error("classifyLeft(rightValue, leftDescriptor) should take the descriptor-mismatch path.");
}
if (result.rightWithRight !== tokens.rightMatch) {
    throw new Error("classifyRight(rightValue, rightDescriptor) should take the descriptor-match path.");
}
if (result.leftWithRight !== tokens.rightMismatch) {
    throw new Error("classifyRight(leftValue, rightDescriptor) should take the descriptor-mismatch path.");
}

print("__PWN_SUCCESS_MARKER__");
