#!/bin/bash -xe

cd "$(dirname "${BASH_SOURCE[0]}")"/..

cd example_module
EXM=$PWD
TMP=$(mktemp -d)

pwnshop list | grep ShellExample
pwnshop render ShellExample
pwnshop -D $TMP build ShellExample
file $TMP/shellexample | grep ELF
pwnshop -D $TMP build ShellOptimized
strings $TMP/shelloptimized | grep -- "-O3"
pwnshop verify ShellExample

( pwnshop verify || true ) | tee /tmp/out
cat /tmp/out | grep "SUCCEEDED: ShellExample"
cat /tmp/out | grep "SUCCEEDED: ShellOptimized"
cat /tmp/out | grep "FAILED: ShellBadVerifier"
cat /tmp/out | grep "SUCCEEDED: Shell1604"
cat /tmp/out | grep "SUCCEEDED: Shell1604InVitu"
cat /tmp/out | grep "SUCCEEDED: PythonPass"

cd /
pwnshop -C $EXM render ShellExample

echo SUCCESS
