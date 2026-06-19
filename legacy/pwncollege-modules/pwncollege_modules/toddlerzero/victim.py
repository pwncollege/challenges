#!/opt/pwn.college/python

import requests
import psutil
import sys
import re

open_ports = { s.laddr.port for s in psutil.net_connections(kind="inet") if s.status == 'LISTEN' }
if {{challenge.port}} not in open_ports:
    print("Service doesn't seem to be running?")
    sys.exit(1)

print(f"Visiting with a yummy cookie...")
r = requests.get("http://localhost:{{challenge.port}}/hacker_manifesto.txt", cookies={"flag": open("/flag").read().strip()})
print(f"... retrieved, in case it helps you debug: {r.content}")
