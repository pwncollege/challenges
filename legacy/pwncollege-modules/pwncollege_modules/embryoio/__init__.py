import itertools
import pwnshop
import signal
import pwn
import sys
import os

PWNSHOP_AUTOREGISTER = False

from pwnshop import Challenge

_PASSWORD = [ "--password", "{self.random_word(8)}" ]
_CHALLENGE_EASY = [ "--num_challenges", "1", "--challenge_ops", "+*", "--challenge_depth", "1" ]
_CHALLENGE_MEDIUM = [ "--num_challenges", "5", "--challenge_ops", "+*%", "--challenge_depth", "3" ]
_CHALLENGE_HARD = [ "--num_challenges", "50", "--challenge_ops", "+*&^%|", "--challenge_depth", "5" ]
_CHALLENGE_INSANE = [ "--num_challenges", "500", "--challenge_ops", "+*&^%|", "--challenge_depth", "10" ]
_SIGNAL_EASY = [ "--num_signals", "1" ]
_SIGNAL_MEDIUM = [ "--num_signals", "5" ]
_SIGNAL_HARD = [ "--num_signals", "50" ]
_SIGNAL_INSANE = [ "--num_signals", "500" ]

ALL_CHALS = [ ]

# cycles for parents: bash (interactive), shellscript, python, ipython (interactive), binary
A_SEQUENCE = [
    [ ], # literally just run this thing
    [ ] + _PASSWORD, # a password on stdin
    [ "--check_arg", "1:{self.random_word(10)}" ], # password on argv[1]
    [ "--check_env", "{self.random_word(6)}:{self.random_word(10)}" ], # password on env
    [ "--check_stdin_path", "/tmp/{self.random_word(6)}" ] + _PASSWORD, # password via file
    [ "--check_stdout_path", "/tmp/{self.random_word(6)}" ], # flag via stdout
    [ "--empty_env" ], # empty environment
]
A_PARENTS = [ "bash", "shellscript", "ipython", "python", "binary" ]
for p,s in itertools.product(A_PARENTS, A_SEQUENCE):
    ALL_CHALS.append([ "--parent", p ] + s)

# some fun redirection stuff. same parents as above
B_SEQUENCE = [
    [ "--check_stdout_pipe", "cat" ], # stdout to cat
    [ "--check_stdout_pipe", "grep" ], # stdout to grep
    [ "--check_stdout_pipe", "sed" ], # stdout to sed
    [ "--check_stdout_pipe", "rev" ], # stdout to rev
    [ "--check_stdin_pipe", "cat" ] + _PASSWORD, # stdin for cat
    [ "--check_stdin_pipe", "rev" ] + _PASSWORD, # stdin for rev
]
B_PARENTS = [ "bash", "shellscript", "ipython", "python", "binary" ]
for p,s in itertools.product(B_PARENTS, B_SEQUENCE):
    ALL_CHALS.append([ "--parent", p ] + s)

# some one-off fun stuff (no mods here)
C_SEQUENCE = [
    [ "--parent", "find" ], # launch from find
    [ "--parent", "find", "--check_arg", "1:{self.random_word(10)}" ], # lanch from find AND pass in a file as a password
]
ALL_CHALS += C_SEQUENCE

# cycles for parents: shellscript, python, binary
D_SEQUENCE = [
    [ "--check_arg", "{self.random.randrange(12,345)}:{self.random_word(10)}" ], # password on random argv
    [ "--empty_argv" ], # empty argv through a wrapper or whatnot
    [ "--check_env", "{self.random.randrange(12,345)}:{self.random_word(10)}", "--empty_env" ], # password via env, but also empty env other than that
    [ "--check_env", "{self.random.randrange(12,345)}:{self.random_word(10)}", "--empty_env", "--check_arg", "{self.random.randrange(12,345)}:{self.random_word(10)}" ], # env and arg
    [ "--cwd", "/tmp/{self.random_word(6)}", "--check_stdin_path", "{self.random_word(6)}" ], # cwd, with a relative input file
    [ "--cwd", "/tmp/{self.random_word(6)}", "--parent_different_cwd" ] # different CWD than parent
]
D_PARENTS = [ "shellscript", "python", "binary" ]
for p,s in itertools.product(D_PARENTS, D_SEQUENCE):
    ALL_CHALS.append([ "--parent", p ] + s)

# cycles for parents: shellscript, python, binary
E_SEQUENCE = [
    [ ] + _CHALLENGE_EASY, # challenges
    [ ] + _CHALLENGE_MEDIUM, # challenges
    [ "--check_arg", "0:/tmp/{self.random_word(6)}" ], # symlink
    [ "--check_arg", "0:{self.random_word(6)}" ], # symlink + path
    [ "--check_stdin_fifo" ] + _PASSWORD, # stdin to fifo
    [ "--check_stdout_fifo" ], # stdout to fifo
    [ "--check_stdin_fifo", "--check_stdout_fifo" ] + _PASSWORD, # stdin and stdout are fifos
    [ "--check_stdin_fifo", "--check_stdout_fifo" ] + _CHALLENGE_EASY, # stdin and stdout are fifos
    [ "--input_dup", "{self.random.randrange(12,345)}" ] + _PASSWORD, # random input FD
    [ "--input_dup", "2" ] + _PASSWORD, # stderr
    [ "--input_dup", "1" ] + _PASSWORD, # stdout
    [ ] + _SIGNAL_EASY, # signal
    [ ] + _SIGNAL_MEDIUM, # signal
]
E_PARENTS = [ "shellscript", "python", "binary" ]
for p,s in itertools.product(E_PARENTS, E_SEQUENCE):
    ALL_CHALS.append([ "--parent", p ] + s)

# cycles for parents: bash (interactive), shellscript, python, ipython (interactive), binary
F_SEQUENCE = [
    [ ] + _CHALLENGE_HARD, # challenges
    [ ] + _CHALLENGE_INSANE, # challenges
    [ ] + _SIGNAL_HARD, # signal
    [ ] + _SIGNAL_INSANE, # signal
    [ "--check_stdin_pipe", "cat", "--check_stdout_pipe", "cat" ] + _CHALLENGE_HARD, # cat for stdin and stdout, plus challenges!
]
F_PARENTS = [ "shellscript", "python", "binary" ]
for p,s in itertools.product(F_PARENTS, F_SEQUENCE):
    ALL_CHALS.append([ "--parent", p ] + s)

# cycles for clients: shellscript, python, binary, netcat, socat
G_SEQUENCE = [
    [ "--listen_dup", "{self.random.randrange(1000,2000)}" ] + _CHALLENGE_MEDIUM,
]
G_PARENTS = [ "shellscript", "python", "binary" ]
for p,s in itertools.product(G_PARENTS, G_SEQUENCE):
    ALL_CHALS.append([ "--client", p ] + s)

#print(f"EMBRYOIO HAS {len(ALL_CHALS)} CHALLENGES.", file=sys.stderr)
#for n,c in enumerate(ALL_CHALS, start=1):
#   print(n, " ".join(c), file=sys.stderr)

#
# Generate the chals
#

class EmbryoIOBase(Challenge):
    TEMPLATE_PATH = "embryoio/embryoio.c"
    checker_path = "/challenge/chio.py"

def make_classes(arg_lists, start=1):
    for n,args in enumerate(arg_lists, start=start):
        def e_init(self, *args, **kwargs):
            EmbryoIOBase.__init__(self, *args, **kwargs)
            self.checker_args = [ a if "{" not in a else eval('f"'+a+'"', globals(), {"self": self}) for a in self.unformatted_args ] #pylint:disable=eval-used
            with open("/tmp/args", 'a') as f:
                f.write(' '.join(self.checker_args) + '\n')
        yield type(f"EmbryoIOLevel{n}", (EmbryoIOBase,), { "__init__": e_init, "unformatted_args": args })

LEVELS = [ ]
for c in make_classes(ALL_CHALS, 1):
    globals()[c.__name__] = c
    LEVELS.append(c)
NUM_TESTING=0
DOJO_MODULE="interaction"

CHOOSE_LEVELS = { 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 40, 42, 44, 47, 54, 56, 58, 60, 61, 65, 66, 68, 69, 71, 72, 73, 74, 75, 77, 79, 80, 81, 83, 85, 86, 87, 88, 89, 94, 97, 99, 100, 102, 103, 104, 105, 106, 107, 110, 112, 113, 115, 116, 117, 118, 120, 123, 126, 128, 131, 133, 136, 138, 140, 141, 142 }
#pwnshop.register_challenges(LEVELS)
