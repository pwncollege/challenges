#!/usr/local/bin/python -u
import hashlib
import json
import os
import random
import time
from pathlib import Path

import requests

NORTH_POOLE = os.environ["NORTH_POOLE"]
ELF_NAME = os.environ["ELF_NAME"]

DIFFICULTY = 16
DIFFICULTY_PREFIX = "0" * (DIFFICULTY // 4)
CHILDREN = [path.name for path in Path("/challenge/keys").iterdir()]
NICE = list()  # The nice list doesn't care about your fancy set O(1) operations


def hash_block(block: dict) -> str:
    block_str = json.dumps(block, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(block_str.encode()).hexdigest()


print(f"Elf {ELF_NAME} starting to mine for the North-Poole... difficulty={DIFFICULTY}")
while True:
    try:
        print(f"[{ELF_NAME}] mining a new block...")
        tx_resp = requests.get(f"{NORTH_POOLE}/txpool")
        tx_resp.raise_for_status()
        tx_json = tx_resp.json()
        txs = tx_json["txs"]
        head_hash = tx_json["hash"]

        head_resp = requests.get(f"{NORTH_POOLE}/block", params={"hash": head_hash})
        head_resp.raise_for_status()
        head_json = head_resp.json()
        head_block = head_json["block"]

        children = [child for child in CHILDREN if child not in NICE]
        if random.random() >= 0.5 and children:
            nice = random.choice(children)
        else:
            nice = None

        block = {
            "index": head_block["index"] + 1,
            "prev_hash": hash_block(head_block),
            "nonce": 0,
            "txs": txs,
            "nice": nice,
        }

        nonce = 0
        while True:
            block["nonce"] = nonce
            block_hash = hash_block(block)
            if block_hash.startswith(DIFFICULTY_PREFIX):
                break
            nonce += 1

        resp = requests.post(f"{NORTH_POOLE}/block", json=block)
        if resp.status_code == 200:
            print(f"[{ELF_NAME}] mined block {block['index']} ({block_hash})")
            if nice in CHILDREN:
                NICE.append(nice)
        else:
            print(f"[{ELF_NAME}] block rejected: {resp.text}")
    except Exception as e:
        print(f"[{ELF_NAME}] exception while mining: {e}")

    time.sleep(random.randint(10, 120))
