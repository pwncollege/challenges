# pwnshop

Pwnshop is a templated challenge generation engine, built on jinja, to generate source code for challenges, compile it, verify it, and all that fun stuff.
We use pwnshop to generate most of pwn.college's challenges!

This repository has the core of pwnshop, along with one example challenge.

## Installing

```
pip install pwnshop
```

## Challenge Generation

Let's generate some things!


```sh
# by default, pwnshop looks in the current directory for an __init__.py that defines challenges.
# you can override by passing a path to the -C argument
cd path/to/example_module

# render example challenge source code in testing mode
pwnshop render ShellExample

# render example challenge source code in teaching mode
pwnshop render ShellExample --walkthrough

# test the example challenge binary and solution
pwnshop verify ShellExample --walkthrough

# build the example challenge binary
pwnshop build ShellExample --walkthrough -O example_shell
```

## Writing challenges

Check out `example_module` for an example challenge.

1. Write some templates.
2. Write some Python.
