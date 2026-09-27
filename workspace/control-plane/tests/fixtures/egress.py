"""Check permitted egress and that DNS/direct-address policy is enforced."""

import socket
import urllib.error
import urllib.request


assert socket.gethostbyname("example.com") == "192.0.2.1"
client = urllib.request.build_opener(urllib.request.ProxyHandler({}))
for scheme in ("http", "https"):
    with client.open(f"{scheme}://example.com", timeout=15) as response:
        assert response.status == 200
        assert b"Example Domain" in response.read()

try:
    socket.gethostbyname("blocked.invalid")
except socket.gaierror:
    pass
else:
    raise AssertionError("unlisted DNS name resolved")

# Reach the policy proxy directly with a disallowed HTTP Host.
try:
    request = urllib.request.Request(
        "http://192.0.2.1", headers={"Host": "blocked.invalid"}
    )
    client.open(request, timeout=5)
except urllib.error.HTTPError as error:
    assert error.code == 403
else:
    raise AssertionError("unlisted HTTP Host was allowed")

# An address outside the proxy must be blocked by the CNI packet policy.
try:
    socket.create_connection(("1.1.1.1", 443), timeout=2).close()
except OSError:
    pass
else:
    raise AssertionError("direct Internet connection was allowed")
print("egress: allowed HTTP/HTTPS; blocked DNS, HTTP Host, and direct Internet")
