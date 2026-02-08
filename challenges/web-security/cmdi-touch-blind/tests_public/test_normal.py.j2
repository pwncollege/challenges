#!/usr/bin/env python3

import subprocess
import requests
import atexit
import time
import os

{% from 'common/random_names.j2' import generate_names %}
{% set challenge = namespace() %}
{{ generate_names(challenge, random) }}

FLAG = os.environ.get("FLAG", "pwn.college{test}")

proc = subprocess.Popen(['/challenge/server'])
time.sleep(1)  # Give it time to start

# Test that the touch service works normally
response = requests.get(f"http://challenge.localhost/{{challenge.endpoint_challenge}}",
                        params={"{{challenge.parameter_filepath}}": "/tmp/test_file"})
assert response.status_code == 200
assert "Welcome to the touch service" in response.text
assert "Ran touch /tmp/test_file!" in response.text