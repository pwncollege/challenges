#!/usr/bin/env python3

import json
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

    preferences = {"theme": {"color": "blue"}}
    requests.post(
        "http://challenge.localhost/payload",
        data={"payload": json.dumps(preferences)},
    ).raise_for_status()
    response = requests.get("http://challenge.localhost/preferences")
    response.raise_for_status()
    assert response.json() == preferences
    assert requests.get("http://challenge.localhost/admin/secret").status_code == 403
finally:
    server.terminate()
    server.wait()
