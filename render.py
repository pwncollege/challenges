import pathlib
import random
import sys
import os

from jinja2 import Environment, FileSystemLoader
class MockChallenge:
    random = random.Random(1338)

template = sys.argv[1]

env = Environment(loader=FileSystemLoader(list(pathlib.Path(template).parents)))
template = env.get_template(os.path.basename(template))
print(template.render(challenge=MockChallenge))
