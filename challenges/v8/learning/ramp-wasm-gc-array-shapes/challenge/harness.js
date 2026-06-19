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
    return [...u32v(code.length + 2), 0x00, ...code, 0x0b];
}

function refType(typeIndex) {
    return [0x64, ...u32v(typeIndex)];
}

function makeArrayHolderModule() {
    const I32 = 0x7f;
    const FUNC = 0x60;
    const ARRAY = 0x5e;
    const STRUCT = 0x5f;
    const MUTABLE = 0x01;
    const EXTERNAL_FUNCTION = 0x00;
    const GC = 0xfb;
    const LOCAL_GET = 0x20;
    const ARRAY_NEW_DEFAULT = 0x07;
    const ARRAY_GET = 0x0b;
    const ARRAY_SET = 0x0e;
    const ARRAY_LEN = 0x0f;
    const STRUCT_NEW = 0x00;
    const STRUCT_GET = 0x02;
    const STRUCT_SET = 0x05;

    const arrayType = 0;
    const holderType = 1;
    const types = [
        ...u32v(10),
        ARRAY, I32, MUTABLE,
        STRUCT, ...u32v(2), ...refType(arrayType), MUTABLE, I32, MUTABLE,
        FUNC, ...u32v(1), I32, ...u32v(1), ...refType(arrayType),
        FUNC, ...u32v(1), ...refType(arrayType), ...u32v(1), I32,
        FUNC, ...u32v(2), ...refType(arrayType), I32, ...u32v(1), I32,
        FUNC, ...u32v(3), ...refType(arrayType), I32, I32, ...u32v(0),
        FUNC, ...u32v(2), ...refType(arrayType), I32, ...u32v(1), ...refType(holderType),
        FUNC, ...u32v(1), ...refType(holderType), ...u32v(1), I32,
        FUNC, ...u32v(2), ...refType(holderType), I32, ...u32v(1), I32,
        FUNC, ...u32v(2), ...refType(holderType), ...refType(arrayType), ...u32v(0),
    ];

    const functions = [2, 3, 4, 5, 6, 7, 8, 7, 9];
    const exports = [
        ["newArray", 0],
        ["arrayLen", 1],
        ["arrayGet", 2],
        ["arraySet", 3],
        ["makeHolder", 4],
        ["holderLen", 5],
        ["holderGet", 6],
        ["holderMarker", 7],
        ["holderSetArray", 8],
    ];
    const bodies = [
        [LOCAL_GET, 0, GC, ARRAY_NEW_DEFAULT, ...u32v(arrayType)],
        [LOCAL_GET, 0, GC, ARRAY_LEN],
        [LOCAL_GET, 0, LOCAL_GET, 1, GC, ARRAY_GET, ...u32v(arrayType)],
        [LOCAL_GET, 0, LOCAL_GET, 1, LOCAL_GET, 2, GC, ARRAY_SET, ...u32v(arrayType)],
        [LOCAL_GET, 0, LOCAL_GET, 1, GC, STRUCT_NEW, ...u32v(holderType)],
        [LOCAL_GET, 0, GC, STRUCT_GET, ...u32v(holderType), 0, GC, ARRAY_LEN],
        [LOCAL_GET, 0, GC, STRUCT_GET, ...u32v(holderType), 0, LOCAL_GET, 1, GC, ARRAY_GET, ...u32v(arrayType)],
        [LOCAL_GET, 0, GC, STRUCT_GET, ...u32v(holderType), 1],
        [LOCAL_GET, 0, LOCAL_GET, 1, GC, STRUCT_SET, ...u32v(holderType), 0],
    ];

    return new Uint8Array([
        0x00, 0x61, 0x73, 0x6d,
        0x01, 0x00, 0x00, 0x00,
        ...section(1, types),
        ...section(3, [...u32v(functions.length), ...functions.flatMap(u32v)]),
        ...section(7, [
            ...u32v(exports.length),
            ...exports.flatMap(([name, index]) => [...str(name), EXTERNAL_FUNCTION, ...u32v(index)]),
        ]),
        ...section(10, [...u32v(bodies.length), ...bodies.flatMap(funcBody)]),
    ]);
}

const wasm = new WebAssembly.Instance(new WebAssembly.Module(makeArrayHolderModule())).exports;
const smallLength = 2;
const largeLength = 9;
const probeIndex = 1;
const smallValue = (((Math.random() * 0x7fffffff) >>> 0) | 0x1000) | 0;
const largeValue = (((Math.random() * 0x7fffffff) >>> 0) | 0x2000) | 0;
const holderMarker = (((Math.random() * 0x7fffffff) >>> 0) | 0x4000) | 0;
const smallArray = wasm.newArray(smallLength);
const largeArray = wasm.newArray(largeLength);
wasm.arraySet(smallArray, probeIndex, smallValue);
wasm.arraySet(largeArray, probeIndex, largeValue);
let holderObject;
const calls = {
    madeHolder: false,
    retargetedHolder: false,
    holderLengthReads: 0,
    holderValueReads: 0,
    markerReads: 0,
};

const exports = Object.freeze({
    makeHolder(array, marker) {
        const holder = wasm.makeHolder(array, marker);
        if (array === smallArray && marker === holderMarker) {
            holderObject = holder;
            calls.madeHolder = true;
        }
        return holder;
    },
    holderLen(holder) {
        if (holder === holderObject) calls.holderLengthReads++;
        return wasm.holderLen(holder);
    },
    holderGet(holder, index) {
        if (holder === holderObject && index === probeIndex) calls.holderValueReads++;
        return wasm.holderGet(holder, index);
    },
    holderMarker(holder) {
        if (holder === holderObject) calls.markerReads++;
        return wasm.holderMarker(holder);
    },
    holderSetArray(holder, array) {
        if (holder === holderObject && array === largeArray) {
            calls.retargetedHolder = true;
        }
        return wasm.holderSetArray(holder, array);
    },
});

const api = Object.freeze({
    exports,
    smallArray,
    largeArray,
    probeIndex,
    holderMarker,
});

__PWN_SOLVE_SOURCE__;

if (typeof solve !== "function") {
    throw new Error("define solve(api)");
}

const result = solve(api);
if (!result || typeof result !== "object") {
    throw new Error("solve(api) must return the holder observations.");
}
if (!calls.madeHolder) {
    throw new Error("Create the holder while it points at the small array.");
}
if (!calls.retargetedHolder) {
    throw new Error("Retarget the holder to the large array with holderSetArray.");
}
if (calls.holderLengthReads < 2 || calls.holderValueReads < 2) {
    throw new Error("Observe the holder before and after retargeting it.");
}
if (calls.markerReads === 0) {
    throw new Error("Read the holder marker from the original holder object.");
}

if (result.beforeLength !== smallLength) {
    throw new Error("Return beforeLength while the holder still points at the small array.");
}
if (result.beforeValue !== smallValue) {
    throw new Error("Return beforeValue from the holder before retargeting.");
}
if (result.afterLength !== largeLength) {
    throw new Error("Return afterLength after retargeting the holder to the large array.");
}
if (result.afterValue !== largeValue) {
    throw new Error("Return afterValue from the holder after retargeting.");
}
if (result.marker !== holderMarker) {
    throw new Error("Return marker from the same holder object; only its array reference field should change.");
}

print("__PWN_SUCCESS_MARKER__");
