#!/usr/bin/env python3

import requests


response = requests.get("http://challenge.localhost", timeout=10)
print(response.text)
assert "pwn.college{" in response.text
