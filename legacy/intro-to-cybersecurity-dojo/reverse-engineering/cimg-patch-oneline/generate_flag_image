#!/opt/pwn.college/python

import subprocess
import random
import struct
import os

raw_flag_lines = subprocess.check_output(["/usr/bin/figlet", "-fascii9"], input=open("/flag", "rb").read()).split(b"\n")
max_line_length = max(len(line) for line in raw_flag_lines)
flag_lines = [ line.ljust(max_line_length) for line in raw_flag_lines ]

flag_pixels = [ ]
for y,line in enumerate(flag_lines):
	for x,c in enumerate(line):
		flag_pixels += [ (x, y, c) ]
random.shuffle(flag_pixels)

directives = [ ]
for p in flag_pixels:
	directives += [ struct.pack("<HBBBBBBBB", 2, p[0], p[1], 1, 1, 0x8c, 0x1d, 0x40, p[2]) ]

img = b"cIMG" + struct.pack("<HBBI", 3, max_line_length, 1, len(directives)) + b"".join(directives)
with open("/challenge/flag.cimg", "wb") as o:
	o.write(img)
