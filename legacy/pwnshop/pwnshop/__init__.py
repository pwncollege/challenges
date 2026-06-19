ALL_CHALLENGES = { }
ALL_MODULES = { }
MODULE_LEVELS = { }

from .challenge import Challenge, PythonChallenge, KernelChallenge, WindowsChallenge, ChallengeGroup
from .register import register_challenge, register_challenges
from .util import did_segfault, did_timeout, did_abort, did_sigsys, retry
from .environments import DockerEnvironment, BareEnvironment
