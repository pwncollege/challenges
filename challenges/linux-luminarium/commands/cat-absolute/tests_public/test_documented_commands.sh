#!/bin/sh
set -eu

/challenge/run | grep -Fq "/flag"
