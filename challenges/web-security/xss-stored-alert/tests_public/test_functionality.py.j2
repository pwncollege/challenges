#!/usr/bin/env python3
import subprocess
import requests
import atexit
import time
import os

{% from 'common/random_names.j2' import generate_names %}
{% set challenge = namespace() %}
{{ generate_names(challenge, random) }}

FLAG = os.environ["FLAG"]

proc = subprocess.Popen(['/challenge/server'])
time.sleep(1)  # Give it time to start

# Test normal posting
response = requests.post(f"http://challenge.localhost/{{challenge.endpoint_challenge}}", data={"{{challenge.parameter_content}}": "Test post"})
assert response.status_code == 200
assert response.history[0].status_code == 302

# Test that post appears
response = requests.get(f"http://challenge.localhost/{{challenge.endpoint_challenge}}")
assert response.status_code == 200
assert "Test post" in response.text

print("Public tests passed!")