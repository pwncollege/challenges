#!/bin/sh
set -eu

for path in /challenge/naughty-or-nice/*; do
    [ -f "$path" ] || continue
    digest=$(basename "$path")
    input="/list/$digest"

    if [ ! -f "$input" ]; then
        echo "$digest: missing"
        exit 1
    fi

    if output=$("$path" < "$input" 2>&1); then
        cat "$input"
    else
        echo "$digest: $output"
        exit 1
    fi
done
