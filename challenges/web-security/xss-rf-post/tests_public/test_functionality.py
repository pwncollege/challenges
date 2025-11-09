#!/usr/bin/env python3
import subprocess
import requests
import atexit
import time
import os

FLAG = os.environ["FLAG"]

proc = subprocess.Popen(['/challenge/server'])
time.sleep(1)  # Give it time to start

# Test that server is running
response = requests.get("http://challenge.localhost/")
assert response.status_code == 200
assert "pwnpost" in response.text

print("Public tests passed!")