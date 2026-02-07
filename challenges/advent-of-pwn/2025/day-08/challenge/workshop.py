#!/usr/local/bin/python
import hashlib
import os
import pwd
import secrets
import shutil
import subprocess
from pathlib import Path

from flask import Flask, jsonify, render_template_string, request

app = Flask(__name__)

TEMPLATES_DIR = Path("/challenge/templates")
WORKSHOP_DIR = Path("/run/workshop")
TINKERING_DIR = WORKSHOP_DIR / "tinkering"
ASSEMBLED_DIR = WORKSHOP_DIR / "assembled"

SECRET = secrets.token_hex(16)


def drop_privs():
    pw = pwd.getpwnam("nobody")
    if os.getuid() != 0:
        return
    os.setgroups([])
    os.setgid(pw.pw_gid)
    os.setuid(pw.pw_uid)


def toy_hash(toy_id: str) -> str:
    return hashlib.sha256(f"{SECRET}:{toy_id}".encode()).hexdigest()


@app.route("/create", methods=["POST"])
def create():
    payload = request.get_json(force=True, silent=True) or {}
    template = payload.get("template")
    if not template:
        return jsonify({"error": "missing template"}), 400
    bp = TEMPLATES_DIR / template
    if not bp.exists():
        templates = sorted([path.name for path in TEMPLATES_DIR.glob("*")])
        return jsonify({"error": "unknown template", "templates": templates}), 404

    toy_id = secrets.token_hex(8)
    src = TINKERING_DIR / toy_hash(toy_id)
    shutil.copyfile(bp, src)
    return jsonify({"toy_id": toy_id})


@app.route("/tinker/<toy_id>", methods=["POST"])
def tinker(toy_id: str):
    payload = request.get_json(force=True, silent=True) or {}
    op = payload.get("op")
    src = TINKERING_DIR / toy_hash(toy_id)
    if not src.exists():
        return jsonify({"status": "error", "error": "toy not found"}), 404

    text = src.read_text()

    if op == "replace":
        idx = int(payload.get("index", 0))
        length = int(payload.get("length", 0))
        content = payload.get("content", "")
        new_text = text[:idx] + content + text[idx + length :]
        src.write_text(new_text)
        return jsonify({"status": "tinkered"})

    if op == "render":
        ctx = payload.get("context", {})
        rendered = render_template_string(text, **ctx)
        src.write_text(rendered)
        return jsonify({"status": "tinkered"})

    return jsonify({"status": "error", "error": "bad op"}), 400


@app.route("/assemble/<toy_id>", methods=["POST"])
def assemble(toy_id: str):
    payload = request.get_json(force=True, silent=True) or {}
    src = TINKERING_DIR / toy_hash(toy_id)
    if not src.exists():
        return jsonify({"status": "error", "error": "toy not found"}), 404

    dest = ASSEMBLED_DIR / toy_hash(toy_id)
    cmd = ["gcc", "-x", "c", "-O2", "-pipe", "-o", str(dest), str(src)]
    proc = subprocess.run(cmd, capture_output=True, text=True, preexec_fn=drop_privs)
    if proc.returncode != 0:
        return jsonify({"status": "error", "error": "failed to build"}), 400
    return jsonify({"status": "assembled"})


@app.route("/play/<toy_id>", methods=["POST"])
def play(toy_id: str):
    bin_path = ASSEMBLED_DIR / toy_hash(toy_id)
    if not bin_path.exists():
        src = TINKERING_DIR / toy_hash(toy_id)
        if src.exists():
            return jsonify({"status": "error", "error": "toy not built"}), 400
        return jsonify({"status": "error", "error": "toy not found"}), 404
    payload = request.get_json(force=True, silent=True) or {}
    stdin_data = payload.get("stdin", "")
    proc = subprocess.run([str(bin_path)], input=stdin_data, capture_output=True, text=True, preexec_fn=drop_privs)
    return jsonify({"stdout": proc.stdout, "stderr": proc.stderr, "returncode": proc.returncode})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80)
