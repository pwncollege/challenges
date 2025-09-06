#!/usr/bin/env python3
import subprocess
import requests
import atexit
import time
import os

FLAG = os.environ["FLAG"]

proc = subprocess.Popen(['/challenge/server'])
atexit.register(lambda: (proc.terminate(), proc.wait()))
time.sleep(1)

# Create a session to maintain cookies
s = requests.Session()

response = s.get("http://challenge.localhost/")
assert response.status_code == 200
assert "Welcome to pwnpost" in response.text
assert "Login" in response.text

response = s.post("http://challenge.localhost/login", data={
    "username": "guest",
    "password": "password"
})
assert response.status_code == 200
assert response.history[0].status_code == 302

response = s.get("http://challenge.localhost/")
assert response.status_code == 200
assert "Post:" in response.text or "textarea name=content" in response.text
assert "Publish All Drafts" in response.text or "publish" in response.text.lower()

response = s.post("http://challenge.localhost/draft", data={
    "content": "Test draft post",
    "publish": ""
})
assert response.status_code == 200
assert response.history[0].status_code == 302

response = s.get("http://challenge.localhost/")
assert response.status_code == 200
assert "Author: guest" in response.text
assert "YOUR POST:" in response.text
assert "Test draft post" in response.text

response = s.post("http://challenge.localhost/publish")
assert response.status_code == 200
assert response.history[0].status_code == 302

response = s.get("http://challenge.localhost/")
assert response.status_code == 200
assert "Test draft post" in response.text

response = s.get("http://challenge.localhost/ephemeral")
assert response.status_code == 200
assert "ephemeral message" in response.text
assert "The message: (none)" in response.text

response = s.get("http://challenge.localhost/ephemeral?msg=Hello")
assert response.status_code == 200
assert "The message: Hello" in response.text

response = requests.post("http://challenge.localhost/login", data={
    "username": "admin",
    "password": "wrong"
})
assert response.status_code == 403
assert "Invalid username or password" in response.text

print("Public tests passed!")