import type { Bindings } from "../common.ts";
import { canonicalRequest, importPrivateKey, importPublicKey, signCanonical, verifyCanonical } from "../signing.ts";

async function signTransferURL(env: Bindings, method: "GET" | "PUT", pathAndQuery: string, expires: string) {
  const privateKey = await importPrivateKey(env.PWN_WORKSPACE_PRIVATE_KEY_B64);
  return signCanonical(privateKey, canonicalRequest(method, pathAndQuery, expires));
}

export async function verifyTransferURL(env: Bindings, requestURL: string, method: "GET" | "PUT") {
  const url = new URL(requestURL);
  const expires = url.searchParams.get("expires") ?? "";
  const signature = url.searchParams.get("signature") ?? "";
  const expiresAt = Number(expires);
  if (!Number.isSafeInteger(expiresAt) || expiresAt < Math.floor(Date.now() / 1000)) {
    return false;
  }

  url.searchParams.delete("signature");
  const canonical = canonicalRequest(method, `${url.pathname}${url.search}`, expires);
  const publicKey = await importPublicKey(env.PWN_WORKSPACE_PUBLIC_KEY_B64);
  return verifyCanonical(publicKey, canonical, signature).catch(() => false);
}

export async function transferUrl(
  env: Bindings,
  method: "GET" | "PUT",
  volumeUUID: string,
  snapshotUUID: string,
) {
  const url = new URL(`/api/volumes/${volumeUUID}/snapshots/${snapshotUUID}`, env.PWN_WORKSPACE_ORIGIN);
  const expires = String(Math.floor(Date.now() / 1000) + 15 * 60);
  url.searchParams.set("expires", expires);
  url.searchParams.set("signature", await signTransferURL(env, method, `${url.pathname}${url.search}`, expires));
  return url.toString();
}
