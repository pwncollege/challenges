#!/opt/pwn.college/python

import Crypto
import struct
import sys
import os

from Crypto.Cipher import AES
from Crypto.Util.Padding import pad

key = open("/challenge/.key", "rb").read()
cipher = AES.new(key=key, mode={{challenge.aes_mode}})

message = sys.stdin.buffer.read1()
assert len(message) <= {{challenge.maximum_length}}, "Your message is too long!"
plaintext = b"VERIFIED" + struct.pack(b"<Q", len(message)) + message
ciphertext = cipher.encrypt(pad(plaintext, cipher.block_size))

sys.stdout.buffer.write(ciphertext)
