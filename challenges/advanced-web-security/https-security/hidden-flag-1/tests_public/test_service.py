#!/usr/bin/env python3

import ssl
import urllib.request

pem = ssl.get_server_certificate(("challenge.localhost", 443), timeout=5)
context = ssl.create_default_context(cadata=pem)
with urllib.request.urlopen("https://challenge.localhost/", context=context, timeout=5) as response:
    assert response.read() == b"Look closer!!!!\n"
