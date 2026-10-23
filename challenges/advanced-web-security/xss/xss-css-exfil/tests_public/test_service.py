#!/usr/bin/env python3

import subprocess
import time

import requests


server = subprocess.Popen(["/challenge/server"])
try:
    for _ in range(100):
        try:
            requests.get("http://challenge.localhost/", timeout=1).raise_for_status()
            break
        except requests.RequestException:
            time.sleep(0.1)
    else:
        raise AssertionError("server did not become ready in time")

    css = "#account { color: rgb(1, 2, 3); }"
    requests.post(
        "http://challenge.localhost/payload",
        data={"payload": css},
    ).raise_for_status()

    response = requests.get("http://challenge.localhost/")
    response.raise_for_status()
    assert css in response.text
    assert "data-token=" not in response.text
    policy = response.headers["Content-Security-Policy"]
    assert "default-src 'none'" in policy
    assert "style-src 'unsafe-inline'" in policy
    assert "img-src http://hacker.localhost:1337" in policy

    response = requests.get("http://challenge.localhost/redeem", params={"token": "wrong"})
    assert response.status_code == 403
finally:
    server.terminate()
    server.wait()
