#!/usr/bin/env python3
import subprocess
import requests
import atexit
import time
import os

FLAG = os.environ["FLAG"]

proc = subprocess.Popen(['/challenge/server'])
for _ in range(100):
    try:
        requests.get("http://challenge.localhost/")
        break
    except requests.RequestException:
        time.sleep(0.1)
else:
    raise AssertionError("server did not become ready in time")


# Test normal posting
response = requests.post("http://challenge.localhost/", data={"content": "Test post"})
assert response.status_code == 200
assert response.history[0].status_code == 302

# Test that post appears
response = requests.get("http://challenge.localhost/")
assert response.status_code == 200
assert "Test post" in response.text

print("Public tests passed!")