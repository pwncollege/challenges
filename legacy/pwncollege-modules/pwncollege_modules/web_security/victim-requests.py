#!/opt/pwn.college/python

import requests
import psutil
import sys
import re

open_ports = { s.laddr.port for s in psutil.net_connections(kind="inet") if s.status == 'LISTEN' }
if 80 not in open_ports:
    print("Service doesn't seem to be running?")
    sys.exit(1)
challenge_url = "http://challenge.localhost:80/"
flag = open("/flag").read().strip()

print(f"Visiting {challenge_url}...")
try:
    num_inputs = len(re.findall(r"<input[^<]*>", requests.get(challenge_url, timeout=1).text))
    if num_inputs <= 2:
        print("You did not inject an <input> textbox...")
    else:
        print("You got it! Here is your flag:")
        print(flag)
except requests.exceptions.ConnectionError:
    print("Connection error... Is the service running?")
