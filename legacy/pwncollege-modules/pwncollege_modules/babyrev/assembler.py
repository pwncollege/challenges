#
# ISA definitions
#

INSTRUCTION_ORDER = [ 'imm', 'stk', 'add', 'stm', 'ldm', 'jmp', 'cmp', 'sys' ]
SYSCALL_ORDER = [ 'open', 'read_memory', 'read_code', 'write', 'sleep', 'exit' ]
FLAG_ORDER = [ 'l', 'g', 'e', 'n', 'z' ]
REG_ORDER = [ 'a', 'b', 'c', 'd', 's', 'i', 'f' ]
ENCODING_ORDER = [ 'op', 'arg1', 'arg2' ]
WORD_WIDTH = 1
STACK_DIRECTION = 1







EMULATOR_PATH="./babyvm"

#
# Assembler
#

import itertools
import random
import struct
import time
import pwn
import os

WORD_FMT = [ None, "B", "H", None, "I" ][WORD_WIDTH]
def generate_encoding():
	global INSTRUCTION_ENCODING
	global SYSCALL_ENCODING
	global FLAG_ENCODING
	global REG_ENCODING
	global ENCODING
	INSTRUCTION_ENCODING = { i: struct.pack(WORD_FMT, 1 << INSTRUCTION_ORDER.index(i)) for i in INSTRUCTION_ORDER }
	SYSCALL_ENCODING = { i: struct.pack(WORD_FMT, 1 << SYSCALL_ORDER.index(i)) for i in SYSCALL_ORDER }
	FLAG_ENCODING = { i: struct.pack(WORD_FMT, 1 << FLAG_ORDER.index(i)) for i in FLAG_ORDER }
	REG_ENCODING = { i: struct.pack(WORD_FMT, 1 << REG_ORDER.index(i)) for i in REG_ORDER }

	ENCODING = { }
	ENCODING.update(INSTRUCTION_ENCODING)
	ENCODING.update(SYSCALL_ENCODING)
	ENCODING.update(FLAG_ENCODING)
	ENCODING.update(REG_ENCODING)

	# the constants in twos compliment, lazy
	for _i in range(256):
		ENCODING[str(_i)] = struct.pack(WORD_FMT, _i & (256**WORD_WIDTH-1))
		ENCODING[hex(_i)] = struct.pack(WORD_FMT, _i & (256**WORD_WIDTH-1))
		ENCODING[str(-_i)] = struct.pack(WORD_FMT, -_i & (256**WORD_WIDTH-1))

INSTRUCTION_ENCODING = { }
SYSCALL_ENCODING = { }
FLAG_ENCODING = { }
REG_ENCODING = { }
ENCODING = { }
generate_encoding()

def encode_instruction(s):
	op, arg1, arg2 = [ w.strip(',') for w in s.split() ]
	inst = list(ENCODING_ORDER)
	inst[inst.index('op')] = op
	inst[inst.index('arg1')] = arg1
	inst[inst.index('arg2')] = arg2

	e = [ (ENCODING[w] if w in ENCODING else ENCODING.setdefault(w, struct.pack(WORD_FMT, int(w, 0) & (256**WORD_WIDTH-1)))) for w in inst ]
	return b''.join(e)

#
# Higher level
#

global_counter = itertools.count()

def regsaver(f):
	def saver(*args, save="abc", **kwargs):
		for r in save:
			yield f"stk 0 {r}"
		yield from f(*args, **kwargs)
		for r in save[::-1]:
			yield f"stk {r} 0"
	return saver

def push_bytes(string):
	word_strs = [ string[i*WORD_WIDTH:(i+1)*WORD_WIDTH].ljust(WORD_WIDTH, b'\0') for i in range(0, len(string), WORD_WIDTH) ]
	word_nums = [ struct.unpack(WORD_FMT, w)[0] for w in word_strs ]
	for w in word_nums[::STACK_DIRECTION]:
		yield f"imm d {w}"
		yield "stk 0 d"

@regsaver
def store_constant(where, string):
	word_strs = [ string[i*WORD_WIDTH:(i+1)*WORD_WIDTH].ljust(WORD_WIDTH, b'\0') for i in range(0, len(string), WORD_WIDTH) ]
	word_nums = [ struct.unpack(WORD_FMT, w)[0] for w in word_strs ]
	for i,w in enumerate(word_nums[::STACK_DIRECTION]):
		yield f"imm d {w}"
		yield f"imm c {where+i}"
		yield "stm c d"

def mov(dst, src, offset=0):
	if dst == src:
		return

	if src not in REG_ORDER:
		yield f"imm {dst} {(src+offset) if offset else src}"
	else:
		yield f"imm {dst} {offset}"
		yield f"add {dst} {src}"

@regsaver
def print_stored(src, size, ret_reg='d'):
	assert size != 'b', "print_string will clobber a size passed in through register 'b'"

	yield from mov('b', src)
	yield from mov('c', size)
	yield "imm a 1"
	yield f"sys write {ret_reg}"

@regsaver
def print_constant(message, ret_reg='d'):
	if STACK_DIRECTION == 1:
		yield from mov('b', 's', offset=1)
	yield from push_bytes(message)
	if STACK_DIRECTION == -1:
		yield from mov('b', 's', offset=1)
	yield from print_stored('b', len(message), ret_reg=ret_reg, save="") #pylint:disable=unexpected-keyword-arg

@regsaver
def read_bytes(dst, size, fd=0, ret_reg='d'):
	assert size != 'b', "read_bytes will clobber a size passed in through register 'b'"

	yield from mov('b', dst)
	yield from mov('c', size)
	yield from mov("a", fd)
	yield f"sys read_memory {ret_reg}"

@regsaver
def open_file(dst, ret_reg='d', flags=0):
	yield from mov('a', dst)
	yield from mov('b', flags)
	yield f"sys open {ret_reg}"

def vm_exit(exit_code):
	yield f"imm a {exit_code}"
	yield "sys exit 0"

def jmp(dst, conditions=""):
	condition = 0
	for c in conditions:
		condition |= struct.unpack(WORD_FMT, ENCODING[c])[0]

	yield from mov('d', dst)
	yield f"jmp {condition} d"

def call(dst):
	if dst in REG_ORDER:
		assert dst != 'd', "we clobber d during calls..."
		yield "imm d 2"
		yield "add d i"
		yield "stk 0 d"
		yield "jmp 0 {dst}"
	else:
		yield "imm d 2"
		yield "add d i"
		yield "stk 0 d"
		yield f"imm i {dst}"

def finalize(program):
	#print("#### PROGRAM:")
	#print("\n".join(program))

	# get labels
	labels = { }
	for n,s in enumerate(program):
		if s.startswith("LABEL"):
			labels[s] = n - len(labels)
	program = [ s for s in program if not s.startswith("LABEL") ]

	assembled = b""
	for i in program:
		for label,address in labels.items():
			i = i.replace(label, str(address))

		assert "LABEL" not in i, "Unresolved label in instruction: "+i
		assembled += encode_instruction(i)

	assert len(assembled) < (256**WORD_WIDTH)*3
	return assembled

#
# Functions
#

def memcmp():
	# args in: a, b, c
	# return in: d

	yield "LABEL:memcmp-entry"
	yield "add a c"
	yield "add b c"
	yield "LABEL:memcmp-head"
	yield "imm d -1"
	yield "add a d"
	yield "add b d"
	yield "stk 0 a"
	yield "stk 0 b"
	yield "ldm a a"
	yield "ldm b b"
	yield "cmp a b"
	yield "stk b 0"
	yield "stk a 0"
	yield "imm d LABEL:memcmp-end"
	yield "jmp n d"
	yield "imm d -1"
	yield "add c d"
	yield "imm d 0"
	yield "cmp c d"
	yield "imm d LABEL:memcmp-head"
	yield "jmp n d"
	yield "LABEL:memcmp-end"
	yield "stk d c"
	yield "stk i, 0"

#
# Whole programs
#

#
# Testing
#

def simple_test(inputs, expected_output, expected_result):
	with open("/tmp/program", "wb") as p:
		p.write(inputs[0])
	vm = pwn.process(EMULATOR_PATH)
	vm.readrepeat(timeout=0.1)
	for i in inputs:
		vm.write(i)
		time.sleep(0.1)
	vm.readline()
	vm.shutdown('out')
	if expected_output:
		o = vm.read()
		assert o == expected_output
	vm.wait()
	assert vm.proc.returncode == expected_result

def level1(key, key_location, padding_size=0, r=random):
	#pylint:disable=unexpected-keyword-arg

	mcloc = random.randrange(1)

	# the input
	part1 = [
		list(print_constant(b"ENTER KEY: ")) + list(read_bytes(0x40, len(key))),
	]
	for i,k in enumerate(key):
		part1 += [ list(store_constant(key_location+i, bytes([k]), save="")) ]
	r.shuffle(part1)

	program = [ ]
	for p in part1:
		program += p

	program += [ "imm i LABEL:check" ]
	if mcloc == 0:
		program += list(memcmp())

	# the check"

	# the lose and win

	part2 = [
		[ "LABEL:lose" ] + list(print_constant(b"INCORRECT!\n", save="")) + list(vm_exit(1)),
		[ "LABEL:win" ] +
		list(print_constant(b"CORRECT! Here is your flag:\n", save="")) +
		list(store_constant(0x80, b"/flag\0", save="")) +
		list(open_file(0x80, save="")) +
		list(read_bytes(0x80, 0xff, fd='d', save="")) +
		list(print_stored(0x80, 'd', save="")) +
		list(vm_exit(0)),
		[ "LABEL:check" ] +
		list(mov('a', 0x40)) +
		list(mov('b', key_location+padding_size)) +
		list(mov('c', len(key)-padding_size)) +
		list(call("LABEL:memcmp-entry")) +
		[ "imm c 0" ] +
		[ "cmp d c" ] +
		list(jmp("LABEL:win", "e")) +
		list(jmp("LABEL:lose", "lg"))
	]
	if mcloc == 1:
		part2 += [ list(memcmp()) ]
	r.shuffle(part2)
	for p in part2:
		program += p

	return finalize(program)

def program_getflag():
	program = [ ]
	program += list(store_constant(0x80, b"/flag"))
	program += list(open_file(0x80, save="")) #pylint:disable=unexpected-keyword-arg
	program += list(read_bytes(0x80, 0xff, fd='d', save="")) #pylint:disable=unexpected-keyword-arg
	program += list(print_stored(0x80, 'd', save="")) #pylint:disable=unexpected-keyword-arg
	program += list(vm_exit(42))
	return finalize(program)

def generalized(key, key_location, padding_size=0, key_differences=(), idx_correct=None, idx_incorrect=None, idx_flagpath=None, idx_enter=None, len_correct=None, len_incorrect=None, len_enter=None, store_key=True, r=random, input_location=0x30):
	#pylint:disable=unexpected-keyword-arg

	# the input
	part_input = (
		[ "LABEL:input" ] +
		list(print_stored(idx_enter, len_enter, save="") if idx_enter else print_constant(b"KEY: ")) +
		list(read_bytes(input_location, len(key))) +
		[ "imm i LABEL:mangle" ]
	)
	part_memcmp = list(memcmp())
	part_lose = (
		[ "LABEL:lose" ] +
		list(print_stored(idx_incorrect, len_incorrect, save="") if idx_incorrect else print_constant(b"INCORRECT!\n", save="")) +
		list(vm_exit(1))
	)
	part_win = (
		[ "LABEL:win" ] +
		list(print_stored(idx_correct, len_correct, save="") if idx_correct else print_constant(b"CORRECT! Your flag:\n", save="")) +
		list([] if idx_flagpath else store_constant(0x80, b"/flag\0", save="")) +
		list(open_file(idx_flagpath or 0x80, save="")) +
		list(read_bytes('s', 0xff, fd='d', save="")) +
		list(print_stored('s', 'd', save="")) +
		list(vm_exit(0))
	)
	part_check = (
		[ "LABEL:check" ] +
		list(mov('a', input_location)) +
		list(mov('b', key_location+padding_size)) +
		list(mov('c', len(key)-padding_size)) +
		list(call("LABEL:memcmp-entry")) +
		[ "imm c 0" ] +
		[ "cmp d c" ] +
		list(jmp("LABEL:win", "e")) +
		list(jmp("LABEL:lose", "lg"))
	)

	part_mangle = [ "LABEL:mangle", "stk 0 a", "stk 0 b", "stk 0 c" ]
	for i,kd in enumerate(key_differences):
		byteaddr = input_location + i
		part_mangle += [ f"imm a {byteaddr}", f"imm c {kd}", "ldm b a", "add b c", "stm a b" ]
	part_mangle += [ "stk c 0", "stk b 0", "stk a 0", "imm i, LABEL:check" ]

	part_store = [ "LABEL:init" ]
	if store_key:
		for i,k in enumerate(key):
			part_store += list(store_constant(key_location+i, bytes([k]), save=""))
		part_store += [ "imm i, LABEL:input" ]

	er1 = r.choice("abcd")
	er2 = r.choice(list(set("abcd") - {er1}))
	label = "init" if store_key else "input"
	part_entry = r.choice([
		[ f"imm i LABEL:{label}" ],
		[ f"imm {er1} LABEL:{label}", f"stk i {er1}" ],
		[ f"imm {er1} {key_location-1}", f"imm {er2} LABEL:{label}", f"stm {er1} {er2}", f"ldm i, {er1}" ]
	])
	parts = [ part_input, part_memcmp, part_lose, part_win, part_check, part_mangle, part_store ]
	r.shuffle(parts)

	program = part_entry
	for p in parts:
		assert type(p[0]) is str
		program += p
	return finalize(program)


if __name__ == '__main__':
	#pylint:disable=unexpected-keyword-arg
	with open("vm_defines.h", "w") as _o:
		_o.write(randomize(random))
	assert os.system(f"gcc -o {EMULATOR_PATH} babyvm.c -DDEBUG=0 -DNOTEMPLATE=1") == 0
	# just exit
	_program = list(vm_exit(42))
	simple_test([finalize(_program)], b"", 42)

	# print hello world
	with open("vm_defines.h", "w") as _o:
		_o.write(randomize(random))
	assert os.system(f"gcc -o {EMULATOR_PATH} babyvm.c -DDEBUG=0 -DNOTEMPLATE=1") == 0
	_program = [ ]
	_program += list(print_constant(b"HELLO WORLD!\n"))
	_program += list(vm_exit(42))
	simple_test([finalize(_program)], b"HELLO WORLD!\n", 42)

	# print hello world (not with stack)
	with open("vm_defines.h", "w") as _o:
		_o.write(randomize(random))
	assert os.system(f"gcc -o {EMULATOR_PATH} babyvm.c -DDEBUG=0 -DNOTEMPLATE=1") == 0
	_program = [ ]
	_program += list(store_constant(128, b"HELLO WORLD!\n"))
	_program += list(print_stored(128, 13))
	_program += list(vm_exit(42))
	simple_test([finalize(_program)], b"HELLO WORLD!\n", 42)

	# echo
	with open("vm_defines.h", "w") as _o:
		_o.write(randomize(random))
	assert os.system(f"gcc -o {EMULATOR_PATH} babyvm.c -DDEBUG=0 -DNOTEMPLATE=1") == 0
	_program = [ ]
	_program += list(read_bytes(0x80, 5))
	_program += list(print_stored(0x80, 'd'))
	_program += list(vm_exit(42))
	simple_test([finalize(_program), "asdf"], b"asdf", 42)
	simple_test([finalize(_program), "HELLO WORLD!"], b"HELLO", 42)

	# loop
	with open("vm_defines.h", "w") as _o:
		_o.write(randomize(random))
	assert os.system(f"gcc -o {EMULATOR_PATH} babyvm.c -DDEBUG=0 -DNOTEMPLATE=1") == 0
	_program = [ ]
	_program += [ "LABEL:start" ]
	_program += list(read_bytes(0x80, 0xff, save="")) #pylint:disable=unexpected-keyword-arg
	_program += [ "stk 0 d" ]
	_program += [ "imm c 0", "cmp d c" ] + list(jmp("LABEL:exit", 'e'))
	_program += [ "stk d 0" ]
	_program += list(print_stored(0x80, 'd', save="")) #pylint:disable=unexpected-keyword-arg
	_program += list(jmp("LABEL:start"))
	_program += [ "LABEL:exit" ]
	_program += list(vm_exit(42))
	simple_test([finalize(_program), "asdf", "fdsa"], b"asdffdsa", 42)
	simple_test([finalize(_program), "HELLO WORLD!"], b"HELLO WORLD!", 42)
	simple_test([finalize(_program), "HELLO WORLD!", " HO\nW IS IT GO\0ING?"], b"HELLO WORLD! HO\nW IS IT GO\0ING?", 42)

	# readflag
	with open("vm_defines.h", "w") as _o:
		_o.write(randomize(random))
	assert os.system(f"gcc -o {EMULATOR_PATH} babyvm.c -DDEBUG=0 -DNOTEMPLATE=1") == 0
	_program = [ ]
	_program += list(store_constant(0x80, b"/flag"))
	_program += list(open_file(0x80, save="")) #pylint:disable=unexpected-keyword-arg
	_program += list(read_bytes(0x80, 0xff, fd='d', save="")) #pylint:disable=unexpected-keyword-arg
	_program += list(print_stored(0x80, 'd', save="")) #pylint:disable=unexpected-keyword-arg
	_program += list(vm_exit(42))
	simple_test([finalize(_program)], open("/flag", "rb").read(), 42)

	# readflag
	_program = [ ]
	_program += list(store_constant(0x80, b"/flag"))
	_program += list(open_file(0x80, save="")) #pylint:disable=unexpected-keyword-arg
	_program += list(read_bytes(0x80, 0xff, fd='d', save="")) #pylint:disable=unexpected-keyword-arg
	_program += list(print_stored(0x80, 'd', save="")) #pylint:disable=unexpected-keyword-arg
	_program += list(vm_exit(42))
	simple_test([finalize(_program)], open("/flag", "rb").read(), 42)

	# test memcmp
	_key = b"0"+os.urandom(7)
	_program = [ ]
	_program += list(store_constant(0x80, _key))
	_program += list(store_constant(0x40, _key))
	_program += list(mov('a', 0x80))
	_program += list(mov('b', 0x40))
	_program += list(mov('c', 8))
	_program += list(call("LABEL:memcmp-entry"))
	_program += [ "stk 0 d" ]
	_program += list(print_stored('s', '1', save="")) #pylint:disable=unexpected-keyword-arg
	_program += list(vm_exit(42))
	_program += list(memcmp())
	simple_test([finalize(_program)], b"\x00", 42)

	# test memcmp failure
	_key = b"0"+os.urandom(7)
	_program = [ ]
	_program += list(store_constant(0x80, _key))
	_program += list(store_constant(0x40, b"1"+_key[1:]))
	_program += list(mov('a', 0x80))
	_program += list(mov('b', 0x40))
	_program += list(mov('c', 8))
	_program += list(call("LABEL:memcmp-entry"))
	_program += [ "stk 0 d" ]
	_program += list(print_stored('s', '1', save=""))
	_program += list(vm_exit(42))
	_program += list(memcmp())
	simple_test([finalize(_program)], b"\x01", 42)


	# test level1
	_key = os.urandom(8)
	_key_location = random.randrange(0x80, 0xf0)
	_program = level1(_key, _key_location)
	simple_test([_program, _key], b"ENTER KEY: CORRECT! Here is your flag:\n"+open("/flag", "rb").read(), 0)
	_wrong = bytearray(_key)
	_wrong[0] += 1
	simple_test([_program, bytes(_wrong)], b"ENTER KEY: INCORRECT!\n", 1)
	simple_test([level1(_key, _key_location, padding_size=1), bytes(_wrong)[1:]], b"ENTER KEY: CORRECT! Here is your flag:\n"+open("/flag", "rb").read(), 0)
	simple_test([level1(_key, _key_location, padding_size=2), bytes(_wrong)[2:]], b"ENTER KEY: CORRECT! Here is your flag:\n"+open("/flag", "rb").read(), 0)

	print("YES!!!")
