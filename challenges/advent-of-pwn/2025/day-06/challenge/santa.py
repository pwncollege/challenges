#!/usr/local/bin/python -u
import hashlib
import json
import os
import random
import re
import time
import uuid
from pathlib import Path

import requests
from cryptography.hazmat.primitives import serialization

NORTH_POOLE = os.environ["NORTH_POOLE"]
SANTA_KEY = serialization.load_ssh_private_key(
    Path("/challenge/keys/santa/key").read_bytes(), password=None
)

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
SECRET_GIFT = os.urandom(16).hex()
FLAG_GIFT = Path("/flag").read_text()
LETTER_HEADER = "Dear Santa,\n\nFor christmas this year I would like "

REQUIRED_CONFIRMATION_DEPTH = 5

RECENT_GIFTS_EXPIRY_SECONDS = 90
RECENT_GIFTS = {}


print("[santa] starting...")
while True:
    try:
        print("[santa] looking for new letters...")
        now = time.time()
        RECENT_GIFTS = {gift: ts for gift, ts in RECENT_GIFTS.items() if now - ts <= RECENT_GIFTS_EXPIRY_SECONDS}

        head_resp = requests.get(f"{NORTH_POOLE}/block")
        head_resp.raise_for_status()
        head_json = head_resp.json()
        head_block = head_json["block"]
        head_hash = head_json["hash"]

        chain = [head_block]
        current_hash = head_block["prev_hash"]
        while current_hash:
            current_resp = requests.get(f"{NORTH_POOLE}/block", params={"hash": current_hash})
            if current_resp.status_code != 200:
                break
            current_json = current_resp.json()
            block = current_json["block"]
            chain.append(block)
            current_hash = block["prev_hash"]
        chain.reverse()

        balances_resp = requests.get(f"{NORTH_POOLE}/balances", params={"hash": head_hash})
        balances_resp.raise_for_status()
        balances_json = balances_resp.json()
        nice_balances = balances_json.get("balances", {})

        letters = {}

        # Collect letters Santa can trust (recent blocks are not yet sufficiently confirmed)
        for block in chain[:-REQUIRED_CONFIRMATION_DEPTH]:
            for tx in block["txs"]:
                if tx["type"] == "letter" and tx["dst"] == "santa" and tx["letter"].startswith(LETTER_HEADER):
                    child = tx["src"]
                    letters.setdefault(child, {})
                    letters[child][tx["nonce"]] = tx

        # Remove letters Santa already responded to with gifts
        for block in chain:
            for tx in block["txs"]:
                if tx["type"] == "gift" and tx["src"] == "santa":
                    assert tx["nonce"].endswith("-gift")
                    child = tx["dst"]
                    if child in letters:
                        letters[child].pop(tx["nonce"][:-5], None)
        for child, child_letters in letters.items():
            for nonce in list(child_letters.keys()):
                if nonce in RECENT_GIFTS:
                    child_letters.pop(nonce)

        # Santa only gives gifts to children on the nice list
        for child in list(letters.keys()):
            if nice_balances.get(child, 0) <= 0:
                letters.pop(child, None)

        letter = next((tx for child_letters in letters.values() for tx in child_letters.values()), None)
        if not letter:
            time.sleep(10)
            continue

        child = letter["src"]
        gift_value = None

        if SECRET_GIFT in letter["letter"]:
            gift_value = FLAG_GIFT

        if not gift_value and (match := re.search(r"secret index #([0-9]+)", letter["letter"])):
            index = int(match.group(1))
            if 0 <= index < len(SECRET_GIFT):
                gift_value = SECRET_GIFT[index]

        if not gift_value:
            for gift in GIFTS:
                if gift.lower() in letter["letter"].lower():
                    gift_value = gift
                    break

        if not gift_value:
            gift_value = random.choice(GIFTS)

        gift_tx = {
            "dst": child,
            "src": "santa",
            "type": "gift",
            "gift": gift_value,
            "nonce": f"{letter['nonce']}-gift",
        }
        msg = json.dumps(gift_tx, sort_keys=True, separators=(",", ":"))
        digest = hashlib.sha256(msg.encode()).digest()
        gift_tx["sig"] = SANTA_KEY.sign(digest).hex()

        RECENT_GIFTS[letter["nonce"]] = time.time()
        resp = requests.post(f"{NORTH_POOLE}/tx", json=gift_tx)
        if resp.status_code == 200:
            print(f"[santa] queued gift {gift_tx['nonce']} for {child}")
        else:
            print(f"[santa] rejected gift {gift_tx['nonce']} for {child}: {resp.text}")

    except Exception as e:
        print("[santa] error:", e)

    time.sleep(1)
