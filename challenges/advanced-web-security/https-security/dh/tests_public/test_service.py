#!/usr/bin/env python3

import json
import urllib.error
import urllib.request

url = "http://challenge.localhost/"
with urllib.request.urlopen(url, timeout=5) as response:
    params = json.load(response)

assert params.keys() == {"p", "g"}
p, g = (int(params[name], 16) for name in ("p", "g"))
assert p.bit_length() == 2048
assert 2 <= g <= p - 2 and pow(g, (p - 1) // 2, p) == p - 1

for invalid in (None, 2, "", "0x10", "0", "1", format(p - 1, "x"), format(p, "x")):
    request = urllib.request.Request(
        url,
        data=json.dumps({"A": invalid}).encode(),
        headers={"Content-Type": "application/json"},
    )
    try:
        urllib.request.urlopen(request, timeout=5).close()
    except urllib.error.HTTPError as error:
        assert error.code == 400
    else:
        raise AssertionError(f"Accepted invalid public value {invalid!r}")
