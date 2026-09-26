import fs from "node:fs/promises";
import { build } from "esbuild";
import { convertV4MiniflareOptions, Miniflare } from "miniflare";

export async function loadModule(entryPoint) {
  const result = await build({
    entryPoints: [entryPoint],
    bundle: true,
    format: "esm",
    platform: "node",
    write: false,
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
  const mf = new Miniflare(convertV4MiniflareOptions({
    modules: true,
    script: 'export default { fetch() { return new Response("test"); } };',
    compatibilityDate: "2026-05-08",
    d1Databases: ["DB"],
    r2Buckets: ["VOLUMES"],
    d1Persist: false,
    r2Persist: false,
    ...options,
  }));
  t.after(() => mf.dispose());
  const DB = await mf.getD1Database("DB");
  const VOLUMES = await mf.getR2Bucket("VOLUMES");
  await loadSQL(DB, "migrations/0001_schema.sql");
  await loadSQL(DB, "seed.sql");
  return { DB, VOLUMES, mf };
}
