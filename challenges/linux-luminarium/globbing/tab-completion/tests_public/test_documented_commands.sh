#!/bin/sh
set -eu

listing="$(ls -1 /challenge)"
printf '%s\n' "$listing" | grep -qx "Dockerfile"
printf '%s\n' "$listing" | grep -q '^pwncollege'
if printf '%s\n' "$listing" | grep -qx "DESCRIPTION.md"; then
	echo "Unexpected description file in /challenge" >&2
	exit 1
fi

if cat /challenge/pwncollege >/dev/null 2>&1; then
	echo "The incomplete filename unexpectedly resolved" >&2
	exit 1
fi

completion="$(bash -c 'compgen -f -- /challenge/pwn')"
[ "$(printf '%s\n' "$completion" | wc -l)" -eq 1 ]
cat "$completion" >/dev/null
