#!/usr/bin/env python3
import subprocess
import requests
import atexit
import time
import os

FLAG = os.environ["FLAG"]

proc = subprocess.Popen(['/challenge/server'])
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
assert "Publish your drafts" in response.text or "publish" in response.text.lower()

response = s.post("http://challenge.localhost/draft", data={
    "content": "Test draft post",
    "publish": ""
})
assert response.status_code == 200
assert response.history[0].status_code == 302

response = s.get("http://challenge.localhost/")
assert response.status_code == 200
assert "Author: guest" in response.text
assert "Draft post" in response.text
assert "Test draft p" in response.text

response = s.post("http://challenge.localhost/publish")
assert response.status_code == 200
assert response.history[0].status_code == 302

response = s.get("http://challenge.localhost/")
assert response.status_code == 200
assert "Test draft post" in response.text
assert "Draft post" not in response.text or "Author: admin" in response.text

response = requests.post("http://challenge.localhost/login", data={
    "username": "admin",
    "password": "wrong"
})
assert response.status_code == 403
assert "Invalid username or password" in response.text

print("Public tests passed!")