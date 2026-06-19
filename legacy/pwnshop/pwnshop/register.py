import inspect

from . import ALL_CHALLENGES, MODULE_LEVELS, ALL_MODULES

def register_challenge(challenge):
	module = inspect.getmodule(challenge)
	module_name = module.__name__.split(".")[-1]
	challenge_name = challenge.__name__

	if challenge_name in ALL_CHALLENGES:
		print("WARNING: replacing previously-registered challenge %s with new challenge %s" % (ALL_CHALLENGES[challenge_name], challenge))

	ALL_CHALLENGES[challenge_name] = challenge
	MODULE_LEVELS.setdefault(module_name, []).append(challenge)
	ALL_MODULES[module_name] = module

def register_challenges(challenges):
	for c in challenges:
		register_challenge(c)
