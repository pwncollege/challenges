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
    const ARRAY_LEN = 0x0f;

    const arrayType = 0;
    const types = [
        ...u32v(3),
        ARRAY, I32, MUTABLE,
        FUNC, ...u32v(1), I32, ...u32v(1), 0x64, ...u32v(arrayType),
        FUNC, ...u32v(1), 0x64, ...u32v(arrayType), ...u32v(1), I32,
    ];

    const functions = [1, 2];
    const exports = [
        ["newArray", 0],
        ["arrayLen", 1],
    ];
    const bodies = [
        [LOCAL_GET, 0, GC, ARRAY_NEW_DEFAULT, ...u32v(arrayType)],
        [LOCAL_GET, 0, GC, ARRAY_LEN],
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
let smallArray;
let largeArray;
const calls = {
    madeSmallArray: false,
    madeLargeArray: false,
    lengthReads: 0,
};

const exports = Object.freeze({
    newArray(length) {
        const array = wasm.newArray(length);
        if (length === smallLength) {
            smallArray = array;
            calls.madeSmallArray = true;
        } else if (length === largeLength) {
            largeArray = array;
            calls.madeLargeArray = true;
        }
        return array;
    },
    arrayLen(array) {
        if (array === smallArray || array === largeArray) calls.lengthReads++;
        return wasm.arrayLen(array);
    },
});

const api = Object.freeze({
    exports,
    smallLength,
    largeLength,
});

__PWN_SOLVE_SOURCE__;

if (typeof solve !== "function") {
    throw new Error("define solve(api)");
}

const result = solve(api);
if (!result || typeof result !== "object") {
    throw new Error("solve(api) must return the array observations.");
}
if (!calls.madeSmallArray || !calls.madeLargeArray) {
    throw new Error("Create both the small and large Wasm arrays.");
}
if (calls.lengthReads < 2) {
    throw new Error("Read the length of both arrays.");
}

if (result.smallLength !== smallLength) {
    throw new Error("Observe the small array length.");
}
if (result.largeLength !== largeLength) {
    throw new Error("Observe the large array length.");
}

print("__PWN_SUCCESS_MARKER__");
