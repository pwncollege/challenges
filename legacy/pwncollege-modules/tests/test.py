import os
import re
import pytest

import pwnshop


# TODO: tests do not currently support kernel challenges or multi challenges
# skip_modules = ["BabyMem", "Toddler1", "Toddler2", "BabyKernel"]

test_challenges = [
    challenge
    for challenge_name, challenge in pwnshop.all_challenges.items()
    if "Level" in challenge_name
    and re.fullmatch(os.getenv("TEST_CHALLENGE", ".*"), challenge_name)
]


@pytest.mark.parametrize("challenge", test_challenges)
def test_generate_source(challenge):
    challenge_instance = challenge(seed=0x42)
    assert challenge_instance.generate_source()


@pytest.mark.parametrize("challenge", test_challenges)
def test_build_binary(challenge):
    challenge_instance = challenge(seed=0x42)
    assert challenge_instance.build_binary()


@pytest.mark.parametrize("challenge", test_challenges)
def test_verify(challenge):
    challenge_instance = challenge(seed=0x42)
    challenge_instance.verify()
