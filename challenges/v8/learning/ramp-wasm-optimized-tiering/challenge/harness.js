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

function makeStepModule(delta) {
    return new Uint8Array([
        0x00, 0x61, 0x73, 0x6d,
        0x01, 0x00, 0x00, 0x00,
        ...section(1, [0x01, 0x60, 0x01, 0x7f, 0x01, 0x7f]),
        ...section(3, [0x01, 0x00]),
        ...section(7, [0x01, ...str("step"), 0x00, 0x00]),
        ...section(10, [0x01, ...funcBody([0x20, 0x00, 0x41, delta, 0x6a])]),
    ]);
}

const delta = 1 + ((Math.random() * 0x3f) >>> 0);
const input = 0x13370000 | (((Math.random() * 0xffff) >>> 0) & 0xffff);
const expected = (input + delta) | 0;
const instance = new WebAssembly.Instance(new WebAssembly.Module(makeStepModule(delta)));
const originalStep = instance.exports.step;
let optimizedFunction = null;
let stepCalls = 0;
let optimizedStepCalls = 0;

function step(value) {
    stepCalls++;
    if (optimizedFunction === step) optimizedStepCalls++;
    return originalStep(value);
}

function forceOptimizedWasm(fn) {
    if (fn !== step) {
        throw new Error("forceOptimizedWasm must target the provided Wasm export.");
    }
    const target = originalStep;
    eval("%WasmTierUpFunction(target);");
    optimizedFunction = fn;
}

const api = Object.freeze({
    exports: Object.freeze({ step }),
    input,
    forceOptimizedWasm,
});

__PWN_SOLVE_SOURCE__;

if (typeof solve !== "function") {
    throw new Error("define solve(api)");
}

const result = solve(api);
if (optimizedFunction !== step) {
    throw new Error("Call forceOptimizedWasm(api.exports.step) before returning.");
}
if (stepCalls === 0) {
    throw new Error("Call api.exports.step(api.input) after forcing the optimized tier.");
}
if (optimizedStepCalls === 0) {
    throw new Error("Call api.exports.step(api.input) after forcing the optimized tier.");
}
if (result !== expected) {
    throw new Error("Return the result of the optimized Wasm function call.");
}
print("__PWN_SUCCESS_MARKER__");
