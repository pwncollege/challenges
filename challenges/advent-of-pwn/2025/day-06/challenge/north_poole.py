#!/usr/local/bin/python -u
import hashlib
import json
import time
import uuid
from pathlib import Path

from flask import Flask, jsonify, request
from cryptography.hazmat.primitives import serialization

app = Flask(__name__)

DIFFICULTY = 16
TX_EXPIRY_SECONDS = 60

def hash_block(block: dict) -> str:
    block_str = json.dumps(block, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(block_str.encode()).hexdigest()


genesis = {
    "index": 0,
    "prev_hash": "0" * 64,
    "nonce": "",
    "txs": [],
    "nice": None,
}

BLOCKS = {hash_block(genesis): genesis}
TXPOOL = []
IDENTITIES = {
    child_dir.name: serialization.load_ssh_public_key((child_dir / "key.pub").read_bytes())
    for child_dir in Path("/challenge/keys").iterdir()
}


def get_best_chain_block():
    best_hash = None
    best_index = -1
    for blk_hash, blk in BLOCKS.items():
        if blk["index"] > best_index:
            best_index = blk["index"]
            best_hash = blk_hash
    return best_hash


def validate_tx(tx):
    tx_type = tx.get("type")
    if tx_type not in {"letter", "gift", "transfer"}:
        raise ValueError("invalid tx type")

    for field in ("src", "dst", "type", tx_type, "nonce", "sig"):
        if field not in tx:
            raise ValueError(f"missing field {field}")

    identity = IDENTITIES.get(tx["src"])
    if not identity:
        raise ValueError("unknown src")

    if tx["dst"] not in IDENTITIES:
        raise ValueError("unknown dst")

    try:
        sig = bytes.fromhex(tx.get("sig", ""))
    except ValueError:
        raise ValueError("invalid sig encoding")

    payload = {
        "src": tx["src"],
        "dst": tx["dst"],
        "type": tx["type"],
        tx_type: tx[tx_type],
        "nonce": tx["nonce"],
    }
    msg = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(msg.encode()).digest()

    try:
        identity.verify(sig, digest)
    except Exception:
        raise ValueError("invalid signature")

    if tx_type == "transfer":
        amount = tx.get("transfer")
        if not isinstance(amount, (int, float)) or amount <= 0:
            raise ValueError("invalid transfer amount")


def get_nice_balances(block):
    balances = {name: 1 for name in IDENTITIES}

    chain = [block]
    current_hash = block["prev_hash"]
    while current_hash in BLOCKS:
        blk = BLOCKS[current_hash]
        chain.append(blk)
        current_hash = blk["prev_hash"]
    chain.reverse()

    for blk in chain:
        nice_person = blk.get("nice")
        if nice_person:
            balances[nice_person] = balances.get(nice_person, 0) + 1

        for tx in blk["txs"]:
            tx_type = tx.get("type")
            src = tx.get("src")
            dst = tx.get("dst")
            if tx_type == "gift" and src == "santa":
                balances[src] = balances.get(src, 0) + 1
                balances[dst] = balances.get(dst, 0) - 1
            elif tx_type == "transfer":
                amount = tx.get("transfer", 0)
                balances[src] = balances.get(src, 0) - amount
                balances[dst] = balances.get(dst, 0) + amount

    return balances


@app.route("/block", methods=["GET", "POST"])
def block_endpoint():
    """Get a block (default: best-chain head) or submit a mined block."""
    if request.method == "GET":
        blk_hash = request.args.get("hash") or get_best_chain_block()
        blk = BLOCKS.get(blk_hash)
        if not blk:
            return jsonify({"error": "unknown block id"}), 404
        return jsonify({"hash": blk_hash, "block": blk})

    if request.method == "POST":
        block = request.get_json(force=True)
        required_block_fields = ("index", "prev_hash", "nonce", "txs", "nice")
        for field in required_block_fields:
            if field not in block:
                return jsonify({"error": f"missing field {field} in block"}), 400

        block_hash = hash_block(block)
        prev_hash = block.get("prev_hash")

        prefix_bits = len(block_hash) * 4 - len(block_hash.lstrip("0")) * 4
        if prefix_bits < DIFFICULTY:
            return jsonify({"error": "invalid proof of work"}), 400

        if prev_hash not in BLOCKS:
            return jsonify({"error": "unknown parent"}), 400

        expected_index = BLOCKS[prev_hash]["index"] + 1
        if block.get("index") != expected_index:
            return jsonify({"error": "invalid index"}), 400

        nice_person = block.get("nice")
        try:
            for tx in block["txs"]:
                validate_tx(tx)
                if tx.get("src") == nice_person:
                    return jsonify({"error": "nice person cannot be tx src"}), 400
        except ValueError as e:
            return jsonify({"error": f"{e} in block tx"}), 400

        balances = get_nice_balances(block)
        if any(balance < 0 for balance in balances.values()):
            return jsonify({"error": "negative balance"}), 400

        mined_nonces = [tx["nonce"] for tx in block["txs"]]
        if len(mined_nonces) != len(set(mined_nonces)):
            return jsonify({"error": "duplicate tx nonce in block"}), 400
        while prev_hash in BLOCKS:
            blk = BLOCKS[prev_hash]
            for tx in blk["txs"]:
                if tx.get("nonce") in mined_nonces:
                    return jsonify({"error": "duplicate tx nonce in chain"}), 400
            prev_hash = blk["prev_hash"]

        # Enforce a cap: no identity may appear as "nice" more than 10 times in the chain.
        nice_counts = {}
        current_hash = block_hash
        blk = block
        while True:
            nice_person = blk.get("nice")
            if nice_person:
                nice_counts[nice_person] = nice_counts.get(nice_person, 0) + 1
                if nice_counts[nice_person] > 10:
                    return jsonify({"error": "abuse of nice list detected"}), 400
            current_hash = blk["prev_hash"]
            if current_hash not in BLOCKS:
                break
            blk = BLOCKS[current_hash]

        BLOCKS[block_hash] = block
        return jsonify({"status": "accepted"})


@app.route("/tx", methods=["POST"])
def submit_tx():
    """Submit a transaction into the global tx pool."""
    tx = request.get_json(force=True)
    try:
        validate_tx(tx)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    TXPOOL.append((time.time(), tx))
    return jsonify({"status": "queued"})


@app.route("/txpool", methods=["GET"])
def get_txpool():
    """Get the relevant tx pool (default: best-chain head)."""
    blk_hash = request.args.get("hash") or get_best_chain_block()

    mined_nonces = set()
    current_hash = blk_hash
    while current_hash in BLOCKS:
        blk = BLOCKS[current_hash]
        for tx in blk["txs"]:
            mined_nonces.add(tx.get("nonce"))
        current_hash = blk["prev_hash"]

    now = time.time()
    TXPOOL[:] = [
        (ts, tx) for ts, tx in TXPOOL
        if now - ts <= TX_EXPIRY_SECONDS
    ]
    fresh = [tx for _, tx in TXPOOL if tx.get("nonce") not in mined_nonces]

    return jsonify({"hash": blk_hash, "txs": fresh})


@app.route("/balances", methods=["GET"])
def get_balances():
    """Get nice/transfer balances for the chain ending at the given (or best) hash."""
    blk_hash = request.args.get("hash") or get_best_chain_block()
    blk = BLOCKS.get(blk_hash)
    if not blk:
        return jsonify({"error": "unknown block id"}), 404
    balances = get_nice_balances(blk)
    return jsonify({"hash": blk_hash, "balances": balances})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80)
