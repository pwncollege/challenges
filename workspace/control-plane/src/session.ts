import type { Bindings } from "./common.ts";
import { unixSeconds } from "./common.ts";
import { importPrivateKey, importPublicKey, signCanonical, verifyCanonical } from "./signing.ts";

const SESSION_COOKIE = "pwn_workspace_session";
const SESSION_TTL_SECONDS = 7 * 24 * 60 * 60;

type SessionPayload = {
  user_uuid: string;
  expires_at: number;
};

export async function createSessionCookie(env: Bindings, userUUID: string) {
  const payload = JSON.stringify({
    user_uuid: userUUID,
    expires_at: unixSeconds() + SESSION_TTL_SECONDS,
  } satisfies SessionPayload);
  const privateKey = await importPrivateKey(env.PWN_WORKSPACE_PRIVATE_KEY_B64);
  const signature = await signCanonical(privateKey, payload);
  const secure = env.PWN_WORKSPACE_ENVIRONMENT === "production" ? "; Secure" : "";
  return [
    `${SESSION_COOKIE}=${encodeURIComponent(payload)}.${encodeURIComponent(signature)}`,
    "Path=/",
    "HttpOnly",
    "SameSite=Lax",
    `Max-Age=${SESSION_TTL_SECONDS}`,
    secure,
  ].filter(Boolean).join("; ");
}

export async function sessionUserUUID(env: Bindings, cookieHeader: string | undefined) {
  const value = cookieHeader?.split(";").map((cookie) => cookie.trim()).find((cookie) => cookie.startsWith(`${SESSION_COOKIE}=`));
  if (!value) return null;

  let payloadText: string;
  let signature: string;
  try {
    [payloadText, signature] = value.slice(SESSION_COOKIE.length + 1).split(".").map(decodeURIComponent);
  } catch {
    return null;
  }
  if (!payloadText || !signature) return null;

  const publicKey = await importPublicKey(env.PWN_WORKSPACE_PUBLIC_KEY_B64);
  if (!(await verifyCanonical(publicKey, payloadText, signature).catch(() => false))) return null;

  let payload: Partial<SessionPayload>;
  try {
    payload = JSON.parse(payloadText) as Partial<SessionPayload>;
  } catch {
    return null;
  }
  if (typeof payload.user_uuid !== "string") return null;
  if (typeof payload.expires_at !== "number") return null;
  if (!Number.isSafeInteger(payload.expires_at) || payload.expires_at < unixSeconds()) return null;
  return payload.user_uuid;
}
