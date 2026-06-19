const token = ((Math.random() * 0xffffffff) >>> 0) || 1;
const handles = Object.freeze({ safe: 0x1010, win: 0x5150 });
const donor = Object.freeze({ role: "donor" });
const recipient = Object.freeze({ role: "recipient" });
const trustedHandles = new WeakMap([
    [donor, handles.win],
    [recipient, handles.safe],
]);

function requireBoundaryObject(obj) {
    if (!trustedHandles.has(obj)) {
        throw new Error("unknown boundary object");
    }
}

function requireTrustedHandleField(field) {
    if (field !== "trustedHandle") {
        throw new Error("this ramp only exposes the trustedHandle field");
    }
}

function readField(obj, field) {
    requireBoundaryObject(obj);
    requireTrustedHandleField(field);
    return trustedHandles.get(obj);
}

function writeField(obj, field, value) {
    requireBoundaryObject(obj);
    requireTrustedHandleField(field);
    trustedHandles.set(obj, value >>> 0);
}

function callRecipient() { return trustedHandles.get(recipient) === handles.win ? token : 0; }
const api = Object.freeze({ donor, recipient, readField, writeField, callRecipient });

__PWN_SOLVE_SOURCE__;

if (typeof solve !== "function") throw new Error("define solve(api)");
solve(api);
if (callRecipient() === token) print("__PWN_SUCCESS_MARKER__");
