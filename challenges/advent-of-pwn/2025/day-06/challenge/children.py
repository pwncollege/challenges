#!/usr/local/bin/python -u
import hashlib
import json
import os
import random
import sys
import time
import uuid
from pathlib import Path

import requests
from cryptography.hazmat.primitives import serialization

NORTH_POOLE = os.environ["NORTH_POOLE"]
LETTER_HEADER = "Dear Santa,\n\nFor christmas this year I would like "

GIFTS = [
    "bicycle",
    "train set",
    "drone",
    "robot kit",
    "skateboard",
    "telescope",
    "lego castle",
    "paint set",
    "guitar",
    "soccer ball",
    "puzzle box",
    "chemistry kit",
    "story book",
    "piano keyboard",
    "rollerblades",
    "coding tablet",
    "chess set",
    "binoculars",
    "science lab",
    "magic set",
    "remote car",
    "ukulele",
    "basketball",
    "hockey stick",
    "football",
    "dollhouse",
    "action figures",
    "model airplane",
    "rc helicopter",
    "night sky map",
    "art easel",
    "scooter",
]

children = sys.argv[1:]
if not children:
    print("Usage: children.py <name> [<name> ...]")
    sys.exit(1)

keys = {}
for name in children:
    key_path = Path("/challenge/keys") / name / "key"
    keys[name] = serialization.load_ssh_private_key(key_path.read_bytes(), password=None)

while True:
    try:
        child = random.choice(children)
        gift = random.choice(GIFTS)
        letter = f"{LETTER_HEADER}{gift}"

        letter = {
            "src": child,
            "dst": "santa",
            "type": "letter",
            "letter": letter,
            "nonce": str(uuid.uuid4()),
        }

        msg = json.dumps(letter, sort_keys=True, separators=(",", ":"))
        digest = hashlib.sha256(msg.encode()).digest()
        letter["sig"] = keys[child].sign(digest).hex()

        resp = requests.post(f"{NORTH_POOLE}/tx", json=letter)
        if resp.status_code == 200:
            print(f"[{child}] asked for '{gift}' ({letter['nonce']})")
        else:
            print(f"[{child}] request rejected: {resp.text}")
    except Exception as e:
        print(f"[{child}] error:", e)

    time.sleep(random.randint(10, 120))
