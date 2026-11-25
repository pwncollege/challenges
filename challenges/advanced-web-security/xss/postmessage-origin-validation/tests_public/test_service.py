#!/usr/bin/env python3

import subprocess
import time

import requests


# Left running on purpose: the test container is discarded afterward, and CI runners deny signalling it.
server = subprocess.Popen(["/challenge/server"])
for _ in range(100):
    try:
        requests.get("http://challenge.localhost/", timeout=1).raise_for_status()
        break
    except requests.RequestException:
        time.sleep(0.1)
else:
    raise AssertionError("server did not become ready in time")

response = requests.get(
    "http://challenge.localhost/redeem", params={"token": "wrong"}
)
assert response.status_code == 403

response = requests.get("http://challenge.localhost:8080/")
response.raise_for_status()
assert '<iframe id=dashboard src="http://challenge.localhost/">' in response.text

response = requests.get("http://challenge.localhost:8080/missing")
assert response.status_code == 404
