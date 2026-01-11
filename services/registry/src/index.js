export default {
  async fetch(request, env) {
    const { pathname } = new URL(request.url);

    if (pathname === "/v2/") {
      return new Response(null, { status: 200 });
    }

    if (request.method !== "GET" && request.method !== "HEAD") {
      return new Response(null, { status: 405, headers: { Allow: "GET, HEAD" } });
    }

    const match = pathname.match(/^\/v2\/(.+)\/(manifests|blobs)\/([^/]+)$/);
    if (!match) {
      return new Response("Not found", { status: 404 });
    }

    const [, name, kind, ref] = match;

    switch (kind) {
      case "manifests": {
        let manifestRef = ref;
        if (!manifestRef.includes(":")) {
          const tagObject = await env.REGISTRY_BUCKET.get(`manifests/${name}/${ref}`);
          if (!tagObject) {
            return new Response("Not found", { status: 404 });
          }
          manifestRef = (await tagObject.text()).trim();
        }

        const object = await env.REGISTRY_BUCKET.get(`blobs/${manifestRef.replace(":", "/")}`);
        if (!object) {
          return new Response("Not found", { status: 404 });
        }

        const body = await object.text();
        const { mediaType } = JSON.parse(body);

        const headers = new Headers();
        object.writeHttpMetadata(headers);
        headers.set("Content-Type", mediaType);
        headers.set("Content-Length", String(object.size));
        headers.set("Docker-Content-Digest", manifestRef);

        return new Response(body, { status: 200, headers });
      }

      case "blobs": {
        if (!ref.includes(":")) {
          return new Response("Not found", { status: 404 });
        }

        return Response.redirect(
          new URL(`blobs/${ref.replace(":", "/")}`, `https://${env.R2_DOMAIN}`).toString(),
          307
        );
      }

      default:
        return new Response("Not found", { status: 404 });
    }
  },
};
