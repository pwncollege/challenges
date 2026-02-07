#!/usr/bin/env python3
import sys, struct, os

# usage: scrub_btf_lines.py file.o   (scrubs in place)
if len(sys.argv) != 2:
    sys.exit("usage: scrub_btf_lines.py file.o")

path = sys.argv[1]
data = bytearray(open(path, "rb").read())
if data[:4] != b"\x7fELF":
    sys.exit("not an ELF file")

# --- ELF64 header bits ---
e_shoff     = struct.unpack_from("<Q", data, 0x28)[0]
e_shentsize = struct.unpack_from("<H", data, 0x3A)[0]
e_shnum     = struct.unpack_from("<H", data, 0x3C)[0]
e_shstrndx  = struct.unpack_from("<H", data, 0x3E)[0]

# --- .shstrtab (section name string table) ---
shstr_hdr_off = e_shoff + e_shentsize * e_shstrndx
_, _, _, _, shstr_off, shstr_size, _, _, _, _ = struct.unpack_from(
    "<IIQQQQIIQQ", data, shstr_hdr_off
)
shstr = data[shstr_off : shstr_off + shstr_size]

btf_off = btfext_off = None

# --- find .BTF and .BTF.ext sections ---
for i in range(e_shnum):
    off = e_shoff + i * e_shentsize
    sh_name, _, _, _, sh_offset, _, _, _, _, _ = struct.unpack_from(
        "<IIQQQQIIQQ", data, off
    )
    if sh_name >= shstr_size:
        continue
    end = shstr.find(b"\0", sh_name)
    if end == -1:
        continue
    name = shstr[sh_name:end].decode("ascii", "ignore")
    if name == ".BTF":
        btf_off = sh_offset
    elif name == ".BTF.ext":
        btfext_off = sh_offset

# must have both .BTF and .BTF.ext
if btf_off is None or btfext_off is None:
    sys.exit("missing .BTF or .BTF.ext")

# --- .BTF header: locate string table ---
magic, ver, flags, hdr_len, type_off, type_len, str_off, str_len = struct.unpack_from(
    "<HBBIIIII", data, btf_off
)
if magic != 0xEB9F:
    sys.exit("bad BTF magic")

str_base = btf_off + hdr_len + str_off

# --- .BTF.ext header: locate line_info subsection ---
emagic, ever, eflags, ehdr_len, fioff, filen, lioff, lilen, core_off, core_len = struct.unpack_from(
    "<HBBIIIIIII", data, btfext_off
)
if emagic != 0xEB9F or lilen <= 4:
    # no line info → nothing to scrub
    sys.exit("missing line info in .BTF.ext")

li_base = btfext_off + ehdr_len + lioff
li_end  = li_base + lilen

# first u32 in line_info subsection is *rec_size* only
rec_size = struct.unpack_from("<I", data, li_base)[0]
pos = li_base + 4

to_scrub = set()

# line_info layout:
#   __u32 rec_size;
#   struct btf_ext_info_sec {
#       __u32 sec_name_off;
#       __u32 num_info;
#       struct bpf_line_info records[num_info]; // each rec_size bytes
#   } sec[...];
while pos < li_end:
    if pos + 8 > li_end:
        break
    sec_name_off, num_info = struct.unpack_from("<II", data, pos)
    pos += 8
    # don't scrub sec_name_off; libbpf uses it to match sections
    for _ in range(num_info):
        if pos + rec_size > li_end:
            pos = li_end
            break
        insn_off, file_off, line_off, line_col = struct.unpack_from(
            "<IIII", data, pos
        )
        to_scrub.add(file_off)
        to_scrub.add(line_off)
        pos += rec_size

# --- zero referenced strings in .BTF string table ---
limit = str_base + str_len
for off in to_scrub:
    if not (0 < off < str_len):
        continue
    start = str_base + off
    end = start
    while end < limit and data[end] != 0:
        end += 1
    if end > start:
        data[start:end] = b"\0" * (end - start)

open(path, "wb").write(data)
