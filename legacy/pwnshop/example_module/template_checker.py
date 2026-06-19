#!/opt/pwn.college/python

import subprocess
import os

runner_path = os.path.dirname(__file__) + "/{{challenge.shellcode_runner}}"
result = subprocess.run([runner_path], stdin=0, stdout=subprocess.PIPE, check=False).stdout.strip().split()[-1]
if result == b"{{challenge.password}}":
    print(open("/flag").read())
else:
    print(f"Nope: {result} is incorrect")
