const token = ((Math.random() * 0xffffffff) >>> 0) || 1;
const safeTarget = Object.freeze({ name: "safe", result: 0 });
const winTarget = Object.freeze({ name: "win", result: token });
const wasmExportedFunctionData = { callTarget: safeTarget };
const sharedFunctionInfo = Object.freeze({ wasmExportedFunctionData });
const exportedFunction = Object.freeze({ sharedFunctionInfo });

function readField(object, field) {
    if (object === exportedFunction && field === "sharedFunctionInfo") {
        return sharedFunctionInfo;
    }
    if (object === sharedFunctionInfo && field === "wasmExportedFunctionData") {
        return wasmExportedFunctionData;
    }
    if (object === wasmExportedFunctionData && field === "callTarget") {
        return wasmExportedFunctionData.callTarget;
    }
    throw new Error(`Unsupported metadata read ${field}.`);
}

function writeField(object, field, value) {
    if (object !== wasmExportedFunctionData || field !== "callTarget") {
        throw new Error("Only the WasmExportedFunctionData callTarget is writable in this ramp.");
    }
    if (value !== safeTarget && value !== winTarget) {
        throw new Error("callTarget must be one of the provided target objects.");
    }
    wasmExportedFunctionData.callTarget = value;
}

function callExportedFunction() {
    return wasmExportedFunctionData.callTarget.result;
}

const api = Object.freeze({
    exportedFunction,
    winTarget,
    readField,
    writeField,
    callExportedFunction,
});

__PWN_SOLVE_SOURCE__;

if (typeof solve !== "function") {
    throw new Error("define solve(api)");
}

solve(api);
if (api.callExportedFunction() === token) {
    print("__PWN_SUCCESS_MARKER__");
} else {
    throw new Error("The exported function still resolves to the safe call target.");
}
