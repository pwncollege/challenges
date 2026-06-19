const token = ((Math.random() * 0xffffffff) >>> 0) || 1;
const scratchAddress = 0x70001000n + BigInt(((Math.random() * 0x1000) >>> 0) & ~3);
const processMemory = new Map([[scratchAddress.toString(), 0]]);

const retargetableView = {
    backingStore: 0x41414000n,
    setUint32(offset, value, littleEndian) {
        if (littleEndian !== true) {
            throw new Error("Use little-endian DataView-style writes.");
        }
        const address = this.backingStore + BigInt(offset >>> 0);
        processMemory.set(address.toString(), value >>> 0);
    },
    getUint32(offset, littleEndian) {
        if (littleEndian !== true) {
            throw new Error("Use little-endian DataView-style reads.");
        }
        const address = this.backingStore + BigInt(offset >>> 0);
        return processMemory.get(address.toString()) || 0;
    },
};

function retargetBackingStore(view, address) {
    if (view !== retargetableView) {
        throw new Error("This ramp only exposes one retargetable view.");
    }
    if (address !== scratchAddress) {
        throw new Error("Retarget the backing store to the provided scratchAddress.");
    }
    view.backingStore = address;
}

const api = Object.freeze({
    retargetableView,
    scratchAddress,
    token,
    retargetBackingStore,
});

__PWN_SOLVE_SOURCE__;

if (typeof solve !== "function") {
    throw new Error("define solve(api)");
}

solve(api);
if ((processMemory.get(scratchAddress.toString()) >>> 0) === token) {
    print("__PWN_SUCCESS_MARKER__");
} else {
    throw new Error("The scratch process address does not contain the token.");
}
