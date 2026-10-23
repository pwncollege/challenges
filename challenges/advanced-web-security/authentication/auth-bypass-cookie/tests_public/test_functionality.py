#!/usr/bin/env python3
import subprocess
import requests
import atexit
import time
import re

proc = subprocess.Popen(['/challenge/server'])
for _ in range(100):
    try:
        requests.get("http://challenge.localhost/")
        break
    except requests.RequestException:
        time.sleep(0.1)
else:
    raise AssertionError("server did not become ready in time")


response = requests.get("http://challenge.localhost/")
assert response.status_code == 200
assert "Welcome to the login service" in response.text

response = requests.post("http://challenge.localhost/", data={
    "username": "guest",
    "password": "password"
}, allow_redirects=False)
assert response.status_code == 302
assert "session_user=guest" in response.headers.get('Set-Cookie', '')

response = requests.get("http://challenge.localhost/", cookies={"session_user": "guest"})
assert response.status_code == 200
assert "Hello, guest!" in response.text
assert not re.search(r"pwn\.college\{[^}\n]+\}", response.text)

response = requests.post("http://challenge.localhost/", data={
    "username": "admin",
    "password": "wrong"
})
assert response.status_code == 403
assert "Invalid username or password" in response.text

print("Public tests passed!")
