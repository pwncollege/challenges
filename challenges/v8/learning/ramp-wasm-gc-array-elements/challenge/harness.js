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

function makeArrayModule() {
    const I32 = 0x7f;
    const FUNC = 0x60;
    const ARRAY = 0x5e;
    const MUTABLE = 0x01;
    const EXTERNAL_FUNCTION = 0x00;
    const GC = 0xfb;
    const LOCAL_GET = 0x20;
    const ARRAY_NEW_DEFAULT = 0x07;
    const ARRAY_GET = 0x0b;
    const ARRAY_SET = 0x0e;
    const ARRAY_LEN = 0x0f;

    const arrayType = 0;
    const types = [
        ...u32v(5),
        ARRAY, I32, MUTABLE,
        FUNC, ...u32v(1), I32, ...u32v(1), 0x64, ...u32v(arrayType),
        FUNC, ...u32v(1), 0x64, ...u32v(arrayType), ...u32v(1), I32,
        FUNC, ...u32v(2), 0x64, ...u32v(arrayType), I32, ...u32v(1), I32,
        FUNC, ...u32v(3), 0x64, ...u32v(arrayType), I32, I32, ...u32v(0),
    ];

    const functions = [1, 2, 3, 4];
    const exports = [
        ["newArray", 0],
        ["arrayLen", 1],
        ["arrayGet", 2],
        ["arraySet", 3],
    ];
    const bodies = [
        [LOCAL_GET, 0, GC, ARRAY_NEW_DEFAULT, ...u32v(arrayType)],
        [LOCAL_GET, 0, GC, ARRAY_LEN],
        [LOCAL_GET, 0, LOCAL_GET, 1, GC, ARRAY_GET, ...u32v(arrayType)],
        [LOCAL_GET, 0, LOCAL_GET, 1, LOCAL_GET, 2, GC, ARRAY_SET, ...u32v(arrayType)],
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

const wasm = new WebAssembly.Instance(new WebAssembly.Module(makeArrayModule())).exports;
const smallLength = 2;
const largeLength = 9;
const probeIndex = 1;
const smallValue = (((Math.random() * 0x7fffffff) >>> 0) | 0x1000) | 0;
const largeValue = (((Math.random() * 0x7fffffff) >>> 0) | 0x2000) | 0;
const smallArray = wasm.newArray(smallLength);
const largeArray = wasm.newArray(largeLength);
const calls = {
    storedSmallValue: false,
    storedLargeValue: false,
    valueReads: 0,
};

const exports = Object.freeze({
    arrayGet(array, index) {
        if ((array === smallArray || array === largeArray) && index === probeIndex) calls.valueReads++;
        return wasm.arrayGet(array, index);
    },
    arraySet(array, index, value) {
        if (array === smallArray && index === probeIndex && value === smallValue) {
            calls.storedSmallValue = true;
        }
        if (array === largeArray && index === probeIndex && value === largeValue) {
            calls.storedLargeValue = true;
        }
        return wasm.arraySet(array, index, value);
    },
});

const api = Object.freeze({
    exports,
    smallArray,
    largeArray,
    probeIndex,
    smallValue,
    largeValue,
});

__PWN_SOLVE_SOURCE__;

if (typeof solve !== "function") {
    throw new Error("define solve(api)");
}

const result = solve(api);
if (!result || typeof result !== "object") {
    throw new Error("solve(api) must return the array element observations.");
}
if (!calls.storedSmallValue || !calls.storedLargeValue) {
    throw new Error("Store the provided probe values into their matching arrays.");
}
if (calls.valueReads < 2) {
    throw new Error("Read the probe value from both arrays.");
}

if (result.smallValue !== smallValue) {
    throw new Error("Return the observed small-array value as smallValue.");
}
if (result.largeValue !== largeValue) {
    throw new Error("Return the observed large-array value as largeValue.");
}

print("__PWN_SUCCESS_MARKER__");
