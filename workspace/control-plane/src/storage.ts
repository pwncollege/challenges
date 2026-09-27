import { Effect } from "effect";
import { AwsClient } from "aws4fetch";
import { Environment } from "./common.ts";
import { fromPromise } from "./workspaces/errors.ts";

export const snapshotUrl = Effect.fn("snapshotUrl")(function*(
  method: "GET" | "PUT", volumeUUID: string, snapshotUUID: string,
) {
  const env = yield* Environment;
  return yield* fromPromise(async () => {
    const client = new AwsClient({
      service: "s3", region: "auto",
      accessKeyId: env.PWN_WORKSPACE_R2_ACCESS_KEY_ID,
      secretAccessKey: env.PWN_WORKSPACE_R2_SECRET_ACCESS_KEY,
    });
    const path = ["snapshots", volumeUUID, snapshotUUID].map(encodeURIComponent).join("/");
    const url = new URL(`${env.PWN_WORKSPACE_R2_BUCKET_URL.replace(/\/$/, "")}/${path}`);
    url.searchParams.set("X-Amz-Expires", "900");
    return (await client.sign(url, { method, aws: { signQuery: true } })).url;
  });
});
