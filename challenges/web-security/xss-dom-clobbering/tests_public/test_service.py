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

    payload = "<strong>review me</strong>"
    requests.post(
        "http://challenge.localhost/payload", data={"payload": payload}
    ).raise_for_status()
    response = requests.get("http://challenge.localhost/")
    response.raise_for_status()
    assert payload not in response.text

    response = requests.post(
        "http://challenge.localhost/login",
        data={"username": "admin", "password": "incorrect"},
    )
    assert response.status_code == 403
finally:
    server.terminate()
    server.wait()
