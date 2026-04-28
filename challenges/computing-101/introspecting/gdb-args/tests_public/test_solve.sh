#!/bin/bash

# Prefer the system gdb directly so the /challenge/bin/gdb wrapper (which
# rejects multi-arg invocations) does not interfere with testing
GDB=/usr/bin/gdb
[[ -x "$GDB" ]] || GDB=$(command -v gdb)
if [[ -z "$GDB" ]]; then
  echo "FAIL: gdb not found"
  exit 1
fi

OBJDUMP=/usr/bin/objdump
[[ -x "$OBJDUMP" ]] || OBJDUMP=$(command -v objdump)
if [[ -z "$OBJDUMP" ]]; then
  echo "FAIL: objdump not found"
  exit 1
fi

# Running outside gdb should still trap on int3
OUTSIDE_OUTPUT=$(/challenge/debug-me hello world 2>&1)
OUTSIDE_STATUS=$?

set -e

if [[ "$OUTSIDE_STATUS" -eq 0 ]]; then
  echo "FAIL: Direct launch unexpectedly succeeded"
  exit 1
fi

if [[ "$OUTSIDE_STATUS" -ne 133 ]] && ! echo "$OUTSIDE_OUTPUT" | grep -Eiq "trace/breakpoint trap|breakpoint trap|SIGTRAP"; then
  echo "FAIL: Direct launch did not appear to trap as expected"
  exit 1
fi

# First run without set args: should not hit SIGTRAP/int3
NO_ARGS_OUTPUT=$("$GDB" -q -nx -batch \
  -x /challenge/.gdb \
  -ex "starti" \
  -ex "continue" \
  /challenge/debug-me 2>/dev/null || true)

if echo "$NO_ARGS_OUTPUT" | grep -q "SIGTRAP"; then
  echo "FAIL: Program hit breakpoint without arguments"
  exit 1
fi


# Now solve the intended way: set args, continue to int3, read rdi
WITH_ARGS_OUTPUT=$("$GDB" -q -nx -batch \
  -x /challenge/.gdb \
  -ex "set args test1 test2" \
  -ex "starti" \
  -ex "continue" \
  -ex "print/d \$rdi" \
  /challenge/debug-me 2>&1 || true)

CALCULATED=$(echo "$WITH_ARGS_OUTPUT" | sed -n 's/^\$[0-9][0-9]* = //p' | tail -n 1)

if [[ -z "$CALCULATED" ]]; then
  echo "FAIL: Could not read rdi after breakpoint"
  exit 1
fi

if ! /challenge/submit-number "$CALCULATED" >/dev/null 2>&1; then
  echo "FAIL: Retrieved value was not accepted by submit-number"
  echo "--- gdb output ---"
  echo "$WITH_ARGS_OUTPUT"
  echo "--- end gdb output ---"
  ls -la /challenge/
  exit 1
fi

# Skipped for NUM=0 since the binary's exit-path `mov rdi, 0x0` would false-positive.
if [[ "$CALCULATED" -ne 0 ]]; then
  NUM_HEX=$(printf '0x%x' "$CALCULATED")
  if "$OBJDUMP" -d -M intel /challenge/debug-me 2>/dev/null | grep -qE "mov[[:space:]]+rdi.*(${NUM_HEX}|${CALCULATED})"; then
    echo "FAIL: NUM is statically visible via objdump on /challenge/debug-me"
    exit 1
  fi
fi

# The SUID helper must refuse callers whose parent is not gdb
if /challenge/.read-secret >/dev/null 2>&1; then
  echo "FAIL: /challenge/.read-secret leaked NUM to a non-gdb caller"
  exit 1
fi

echo "PASS"
exit 0
