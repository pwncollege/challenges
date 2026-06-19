const leftToken = ((Math.random() * 0xffffffff) >>> 0) ^ 0x13572468;
const rightToken = ((Math.random() * 0xffffffff) >>> 0) ^ 0x24681357;
const api = Object.freeze({ leftToken, rightToken });

__PWN_SOLVE_SOURCE__;

if (typeof solve !== "function") throw new Error("define solve(api)");
const pair = solve(api);
if (pair && pair.left && pair.right &&
    pair.left.peer === pair.right && pair.right.peer === pair.left &&
    pair.left.token === leftToken && pair.right.token === rightToken) {
    print("__PWN_SUCCESS_MARKER__");
}
