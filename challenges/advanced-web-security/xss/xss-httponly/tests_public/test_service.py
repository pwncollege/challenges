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

    response = requests.get("http://challenge.localhost/admin/secret")
    assert response.status_code == 403

    payload = "<strong>administrator review</strong>"
    response = requests.post("http://challenge.localhost/payload", data={"payload": payload})
    response.raise_for_status()

    response = requests.post(
        "http://challenge.localhost/login",
        data={"username": "admin", "password": "incorrect"},
        allow_redirects=False,
    )
    assert response.status_code == 403
    assert "Set-Cookie" not in response.headers
finally:
    server.terminate()
    server.wait()
