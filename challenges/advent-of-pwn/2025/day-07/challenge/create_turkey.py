#!/usr/bin/env python3

import sys
import base64
import re

if len(sys.argv) != 2:
    print(f"Usage: {sys.argv[0]} <duck_content_filename>")
    sys.exit(1)

duck_file = sys.argv[1]

# Read the duck content
with open(duck_file, 'r') as f:
    duck_content = f.read()

# Escape for use in bash echo with double quotes
duck_content = duck_content.replace('\\', '\\\\').replace('"', '\\"').replace('$', '\\$').replace('`', '\\`')

# Read turkey-payload and replace DUCK_CONTENT
with open('turkey-payload', 'r') as f:
    script_content = f.read()

script_content = script_content.replace('DUCK_CONTENT', duck_content)

# Encode in reverse order of unpacking:
# Step 1: XOR each byte with 0x42
xored = bytes(b ^ 0x42 for b in script_content.encode())
# Step 2: Reverse byte order
reversed_bytes = xored[::-1]
# Step 3: Base64 encode
payload = base64.b64encode(reversed_bytes).decode()

# Replace the payload line in turkey.py
with open('turkey.py', 'r') as f:
    py_content = f.read()

py_content = re.sub(r"PAYLOAD = '.*?'", f"PAYLOAD = '{payload}'", py_content)

with open('turkey.py', 'w') as f:
    f.write(py_content)

print("Payload created and inserted into turkey.py")
