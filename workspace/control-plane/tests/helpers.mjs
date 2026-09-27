import fs from "node:fs/promises";
import { Cause, Effect, Exit } from "effect";
import { build } from "esbuild";
import { convertV4MiniflareOptions, Miniflare } from "miniflare";

export const snapshotBindings = {
  PWN_WORKSPACE_R2_BUCKET_URL: "https://control.test/cdn-cgi/local/r2/s3/volumes",
  PWN_WORKSPACE_R2_ACCESS_KEY_ID: "workspace-local",
  PWN_WORKSPACE_R2_SECRET_ACCESS_KEY: "workspace-local-secret",
};

export async function loadModule(entryPoint) {
  const result = await build({
    entryPoints: [entryPoint],
    bundle: true,
    format: "esm",
    platform: "node",
    write: false,
    plugins: [{
      name: "shared-effect",
      setup(build) {
        // Tests and bundled application modules must share Effect's runtime and
        // schema interpreter. Absolute URLs also work from the data-URL module.
        build.onResolve({ filter: /^effect(?:\/|$)/ }, ({ path }) => ({
          path: import.meta.resolve(path), external: true,
        }));
      },
    }],
  });
  const source = `${result.outputFiles[0].text}\n//# sourceURL=${entryPoint}\n`;
  return import(`data:text/javascript;base64,${Buffer.from(source).toString("base64")}`);
}

export async function loadSQL(db, file) {
  const sql = await fs.readFile(file, "utf8");
  for (const statement of sql.split(";")) {
    if (statement.trim()) await db.prepare(statement).run();
  }
}

export async function createBindings(t, options = {}) {
  const configuration = {
    modules: true,
    script: 'export default { fetch() { return new Response("test"); } };',
    compatibilityDate: "2026-05-08",
    d1Databases: ["DB"],
    r2Buckets: { VOLUMES: { id: "volumes", s3Credentials: {
      accessKeyId: snapshotBindings.PWN_WORKSPACE_R2_ACCESS_KEY_ID,
      secretAccessKey: snapshotBindings.PWN_WORKSPACE_R2_SECRET_ACCESS_KEY,
    } } },
    d1Persist: false,
    r2Persist: false,
    ...options,
    bindings: { ...snapshotBindings, ...options.bindings },
  };
  const mf = new Miniflare(convertV4MiniflareOptions(configuration));
  t.after(() => mf.dispose());
  const address = await mf.ready;
  configuration.port = Number(address.port);
  configuration.bindings.PWN_WORKSPACE_R2_BUCKET_URL = new URL("/cdn-cgi/local/r2/s3/volumes", address).toString();
  await mf.setOptions(convertV4MiniflareOptions(configuration));
  const DB = await mf.getD1Database("DB");
  const VOLUMES = await mf.getR2Bucket("VOLUMES");
  await loadSQL(DB, "migrations/0001_schema.sql");
  await loadSQL(DB, "seed.sql");
  return { DB, VOLUMES, mf, bindings: configuration.bindings };
}

export async function runEffect(effect) {
  const exit = await Effect.runPromiseExit(effect);
  if (Exit.isFailure(exit)) throw Cause.squash(exit.cause);
  return exit.value;
}
