#!/usr/bin/env python3

import socket
import subprocess
import time

import requests


server = subprocess.Popen(["/challenge/server"])
for _ in range(200):
    try:
        with socket.create_connection(("challenge.localhost", 80), timeout=0.25):
            break
    except OSError:
        assert server.poll() is None, "server exited before becoming ready"
        time.sleep(0.1)
else:
    raise AssertionError("server did not become ready in time")

session = requests.Session()
session.trust_env = False
base_url = "http://challenge.localhost"

response = session.get(base_url, timeout=3)
assert response.status_code == 200
assert response.text == "Profile for learner\n"
assert "pwn.college{" not in response.text

saved = session.post(base_url + "/preferences", json={"theme": {"accent": "blue"}}, timeout=3)
assert saved.status_code == 200
assert saved.json() == {"saved": True}

direct = session.post(
    base_url + "/preferences",
    json={"template": "{{ secret() }}"},
    timeout=3,
)
assert direct.status_code == 200
response = session.get(base_url, timeout=3)
assert response.text == "Profile for learner\n"
assert "pwn.college{" not in response.text
