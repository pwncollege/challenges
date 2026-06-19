const token = (((Math.random() * 0xffffffff) >>> 0) || 1).toString(16).padStart(8, "0");
const subject = `prefix:${token}:suffix`;
const tokenStart = subject.indexOf(token);
const tokenEnd = tokenStart + token.length;

function makeRegExp(source, flags) {
    return new RegExp(source, flags);
}

const api = Object.freeze({
    subject,
    token,
    makeRegExp,
});

__PWN_SOLVE_SOURCE__;

if (typeof solve !== "function") {
    throw new Error("define solve(api)");
}

const result = solve(api);
if (!result || typeof result !== "object") {
    throw new Error("solve(api) must return an object with value, start, and end.");
}
if (result.value !== token) {
    throw new Error("The capture value does not match the token.");
}
if (result.start !== tokenStart || result.end !== tokenEnd) {
    throw new Error("The capture start/end offsets do not match the token position.");
}
print("__PWN_SUCCESS_MARKER__");
