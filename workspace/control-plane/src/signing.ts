export function bytesFromBase64(value: string): Uint8Array {
  if (typeof atob === "function") {
    return Uint8Array.from(atob(value), (c) => c.charCodeAt(0));
  }
  return new Uint8Array(Buffer.from(value, "base64"));
}

function bufferSource(bytes: Uint8Array): ArrayBuffer {
  return bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength) as ArrayBuffer;
}

export function base64FromBytes(value: ArrayBuffer): string {
  const bytes = new Uint8Array(value);
  let binary = "";
  for (const byte of bytes) binary += String.fromCharCode(byte);
  if (typeof btoa === "function") return btoa(binary);
  return Buffer.from(bytes).toString("base64");
}

export async function sha256Hex(body: string | ArrayBuffer | Uint8Array): Promise<string> {
  let bytes: Uint8Array;
  if (typeof body === "string") {
    bytes = new TextEncoder().encode(body);
  } else if (body instanceof Uint8Array) {
    bytes = body;
  } else {
    bytes = new Uint8Array(body);
  }
  const digest = await crypto.subtle.digest("SHA-256", bufferSource(bytes));
  return [...new Uint8Array(digest)].map((b) => b.toString(16).padStart(2, "0")).join("");
}

export function canonicalRequest(method: string, pathAndQuery: string, timestamp: string, bodyHash = ""): string {
  return `${method.toUpperCase()}\n${pathAndQuery}\n${timestamp}\n${bodyHash}`;
}

export async function importPrivateKey(pkcs8Base64: string): Promise<CryptoKey> {
  return crypto.subtle.importKey(
    "pkcs8",
    bufferSource(bytesFromBase64(pkcs8Base64)),
    { name: "Ed25519" },
    false,
    ["sign"],
  );
}

export async function importPublicKey(spkiBase64: string): Promise<CryptoKey> {
  return crypto.subtle.importKey(
    "spki",
    bufferSource(bytesFromBase64(spkiBase64)),
    { name: "Ed25519" },
    false,
    ["verify"],
  );
}

export async function signCanonical(privateKey: CryptoKey, canonical: string): Promise<string> {
  const signature = await crypto.subtle.sign("Ed25519", privateKey, new TextEncoder().encode(canonical));
  return base64FromBytes(signature);
}

export async function verifyCanonical(publicKey: CryptoKey, canonical: string, signatureBase64: string): Promise<boolean> {
  return crypto.subtle.verify(
    "Ed25519",
    publicKey,
    bufferSource(bytesFromBase64(signatureBase64)),
    new TextEncoder().encode(canonical),
  );
}
