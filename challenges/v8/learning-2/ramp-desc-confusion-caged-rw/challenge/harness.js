const expectedToken = ((Math.random() * 0xffffffff) >>> 0) || 1;
const proofOffset = (0x4000 + ((Math.random() * 0x1000) >>> 0)) & ~3;
const baseOffset = proofOffset - 0x2c;
const memory = new Map([[proofOffset, 0]]);
let usedRelativeRead = false;
let usedRelativeWrite = false;

function normalizeInteger(value, name) {
    const number = Number(value);
    if (!Number.isInteger(number)) {
        throw new Error(`${name} must be an integer`);
    }
    return number;
}

function resolveTarget(delta) {
    const normalizedDelta = normalizeInteger(delta, "confused access delta");
    const target = baseOffset + normalizedDelta;
    if (target === baseOffset + proofOffset) {
        throw new Error("The confused access takes a delta from baseOffset. Subtract baseOffset from the cage offset.");
    }
    if (!memory.has(target)) {
        throw new Error(`The delta 0x${normalizedDelta.toString(16)} does not target a known proof field.`);
    }
    return target;
}

const confusedAccess = Object.freeze({
    baseOffset,
    read32FromBase(delta) {
        usedRelativeRead = true;
        return memory.get(resolveTarget(delta)) >>> 0;
    },
    write32FromBase(delta, value) {
        usedRelativeWrite = true;
        memory.set(resolveTarget(delta), normalizeInteger(value, "write value") >>> 0);
    },
});

const api = Object.freeze({ confusedAccess, proofOffset, expectedToken });

__PWN_SOLVE_SOURCE__;

if (typeof solve !== "function") throw new Error("define solve(api)");
const rw = solve(api);
if (!rw || typeof rw.read32 !== "function" || typeof rw.write32 !== "function") {
    throw new Error("solve(api) must return { read32(offset), write32(offset, value) }");
}
rw.write32(proofOffset, expectedToken);
const proofValue = rw.read32(proofOffset);
if (usedRelativeRead && usedRelativeWrite && proofValue === expectedToken) {
    print("__PWN_SUCCESS_MARKER__");
}
