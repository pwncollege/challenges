# pwncollege challenge monorepo

This repository will one day contain all core pwn.college challenges.

The basic idea is that challenges are just directories in here, similar to how they're specified in dojos currently.
They'll be auto-built out of these directories, probably as docker files (though some nix stuff is another possibility), and deployed seamlessly.

# Repository structure

The repository structure is:

- `./$MODULE_ID/$CHALLENGE_ID`: each challenge is a directory, and multiple challenge directories make up a module
- `./$MODULE_ID/$CHALLENGE_ID/challenge`: this directory contains challenge artifacts (code, etc) that are used for building and deployment
- `./$MODULE_ID/$CHALLENGE_ID/tests_public`: unencrypted tests used to test challenge functionality before deployment and also to test community contributions via CI
- `./$MODULE_ID/$CHALLENGE_ID/tests_private`: encrypted tests used to ensure challenge solvability before deployment

# Building and testing:

There are a few options in the challenge building process, depending on the needs of the challenge.

## the default case

Normally, when a challenge is built, its `./$MODULE_ID/$CHALLENGE_ID/challenge` is just deployed into /challenge in the default docker container (simple `ubuntu:24.04` with some preinstalled packages and `exec-suid` for SUIDing interpreted programs.
At the end of the container built process, if a `./$MODULE_ID/$CHALLENGE_ID/.setup` file exists, it will be executed in the docker build context.
When the container is launched for a user to attempt the challenge, if a `./$MODULE_ID/$CHALLENGE_ID/.init` file exists (built as `/challenge/.init` in the resulting challenge image), it will be executed before as the challenge container starts up.

## tests

Tests are copied into a temporary directory in a running challenge container and executed with the `FLAG` variable set to the value of the random flag generated to `/flag`.

## custom environments

If a challenge needs build customization beyond `.setup`, it can specify its own `./$MODULE_ID/$CHALLENGE_ID/challenge/Dockerfile`, which will be used instead of the default dockerfile.

## templating

Any file that ends in `.j2` is automatically jinja2-formatted during challenge building.
Templates are passed in a `challenge` parameter that has a few useful utility functions, mostly related to seeded RNG.
Most base templates included in this repository also support various customizations via the `settings` namespace.
Examples abount around the repository.

Anything can be templated, including `./$MODULE_ID/$CHALLENGE_ID/challenge/Dockerfile.j2` (for example, to extend the `default-dockerfile.j2` template with additional packages to install and so on).
Before extending the default template, consider if it would not be easier and more understandable to just make a full `Dockerfile`.

Permissions are preserved when rendering a template.
If you want something executable, make the template executable.

## actually building

The repository contains all you need to build these challenges.

```
# build and test
./build.py --test web_security/path-traversal-1

# if you want to see a single file (for easier debugging)
./build.py web_security/path-traversal-1/tests_public/test_normal.py.j2
```

# pwn.college DOJO integration

**FUTURE WORK.**
This repository will contain various yamls files for different dojos.
These dojos will specify modules to include.
Each module will have its own `module.yml`.

# Porting legacy templates

We are in the process of porting the pwnshop-based curriculum and the multi-repo based curriculum to this format.
The old model was: each dojo would be its own repository (e.g., intro-to-cybersecurity-dojo, program-security-dojo, systems-security-dojo, software-exploitation-dojo, etc) of `./$MODULE_ID/$CHALLENGE_ID` directories full of files to deploy into `/challenge`.
Sometimes, these files were separately generated via pwnshop from the pwncollege-challenges repository, which has `./pwncollege_modules/$SLIGHTLY_DIFFERENT_MODULE_ID/__init__.py` files specifying challenge and verification logic.
These `__init__.py` files also specify jinja2 templates, sprinkled around the pwncollege-challenges and pwnshop repositories.
The dojo repositories' `module.yml` files would sometimes specify the pwnshop details for challenges.

The process of porting is:

1. Identify the challenges to be ported by reading the `module.yml` file.
2. Determine any connections to the pwnshop templates by looking at `module.yml`.
3. Look at `pwncollege-modules/$WHATEVER_MODULE_ID/__init__.py` for the appropriate class and determine the template and challenge logic to port out, if any.
4. Port the challenge files and template and challenge logic to this repository at `./$MODULE_ID/base_templates/` and `./$MODULE_ID/$CHALLENGE_ID/challenge`.
5. If there are templates, use `build.py` to render them and ensure that the result is identical to the previously-rendered version in whatever legacy dojo repository.
6. Port out the challenge verification logic to `./$MODULE_ID/$CHALLENGE_ID/tests_public` and `./$MODULE_ID/$CHALLENGE_ID/tests_private`. The former should just be functionality tests and the latter should include anything that actually exploits the challenge, whether partially or fully.


# In the meantime, some musings:

Some gaps we still need to fill:

- different architectures. Does docker cover all usecases?
- i have some doubts that this challenges-are-jinja-templates style will scale to all challenge complexities. yan85 has some hella spaghetti code. Maybe refactors will help, or maybe we'll need to have some other workarounds.
- should we follow symlinks during challege building? We do in the legacy case. Maybe only follow them if they point outside of the `challenge` dir? That might also be a PITA, though.
