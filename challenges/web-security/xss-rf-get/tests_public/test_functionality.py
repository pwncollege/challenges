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


# Test that server is running
response = requests.get("http://challenge.localhost/")
assert response.status_code == 200
assert "pwnpost" in response.text

print("Public tests passed!")