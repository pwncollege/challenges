# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is the pwn.college challenge monorepo containing cybersecurity CTF challenges. Challenges are organized as directories under modules (e.g., `web_security`, etc.) and are built as Docker containers for deployment.

## Key Commands

### Building and Testing Challenges

```bash
# Build and test a challenge
~/.virtualenvs/pwnc/bin/python3 ./build.py --test MODULE_ID/CHALLENGE_ID

# Example: Build and test path-traversal-1
~/.virtualenvs/pwnc/bin/python3 ./build.py --test web_security/path-traversal-1

# Render a single template file for debugging
~/.virtualenvs/pwnc/bin/python3 ./build.py MODULE_ID/CHALLENGE_ID/path/to/file.j2

# Build challenge without testing
~/.virtualenvs/pwnc/bin/python3 ./build.py MODULE_ID/CHALLENGE_ID --output-dir /tmp/output
```

### Python Environment

Always use the virtual environment Python interpreter:
```bash
~/.virtualenvs/pwnc/bin/python3
```

## Architecture

### Directory Structure
- `MODULE_ID/CHALLENGE_ID/challenge/`: Challenge source code and artifacts
- `MODULE_ID/CHALLENGE_ID/tests_public/`: Unencrypted functionality tests
- `MODULE_ID/CHALLENGE_ID/tests_private/`: Encrypted exploitation tests
- `MODULE_ID/base_templates/`: Shared Jinja2 templates for the module

### Templating System
- Files ending in `.j2` are Jinja2 templates rendered during build
- Templates receive a `challenge` object with seeded RNG functions
- Template permissions are preserved when rendering
- Python templates are auto-formatted with Black
- C templates are auto-formatted with astyle

### Docker Build Process
1. If no `Dockerfile` exists, uses `default-dockerfile.j2`
2. Copies `challenge/` directory to `/challenge` in container
3. Executes `.setup` script if present during build
4. Executes `.init` script if present at container startup

### Testing Framework
- Tests run in temporary containers with a random flag at `/flag`
- Test files must be named `test_*.py` or `test_*.py.j2`
- Tests receive `FLAG` environment variable
- Public tests verify functionality
- Private tests contain exploitation logic

## Challenge Development Workflow

1. Create challenge directory: `MODULE_ID/CHALLENGE_ID/`
2. Add challenge code to `challenge/` subdirectory
3. Create templates using `.j2` extension if needed
4. Write public tests for functionality verification
5. Write private tests for exploitation verification
6. Test with: `~/.virtualenvs/pwnc/bin/python3 ./build.py --test MODULE_ID/CHALLENGE_ID`

## Important Notes

- Docker is required for building and testing challenges
- The `exec-suid` utility is automatically included for SUIDing interpreted programs
- Templates can extend `default-dockerfile.j2` or provide custom Dockerfiles
- Challenge verification should be split between public (functionality) and private (exploitation) tests