#!/bin/bash -x

cd "$(dirname "${BASH_SOURCE[0]}")"/..

rm -rf example_deploy/*/*/*
pwnshop -C example_module apply example_deploy/pwnshop.yml --mp --quiet || exit 1
read -d '' -a SOURCES < <(find example_deploy -iname "*.c")
read -d '' -a BINS < <(find example_deploy -iname shell)
read -d '' -a LIBS < <(find example_deploy -iwholename "*/lib/*")
[ "${#SOURCES[@]}" -eq 1 ] || exit 1
[ "${#BINS[@]}" -eq 6 ] || exit 1
[ "${#LIBS[@]}" -eq 3 ] || exit 1

[ -f example_deploy/checked-shell/_0/runner ] || exit 1
[ -f example_deploy/checked-shell/_0/checker ] || exit 1
[ -f example_deploy/checked-shell/_1/runner ] || exit 1
[ -f example_deploy/checked-shell/_1/checker ] || exit 1

rm -rf example_deploy/*/*/*
pwnshop -C example_module apply example_deploy/pwnshop.yml || exit 1
read -d '' -a SOURCES < <(find example_deploy -iname "*.c")
read -d '' -a BINS < <(find example_deploy -iname shell)
read -d '' -a LIBS < <(find example_deploy -iwholename "*/lib/*")
[ "${#SOURCES[@]}" -eq 1 ] || exit 1
[ "${#BINS[@]}" -eq 6 ] || exit 1
[ "${#LIBS[@]}" -eq 3 ] || exit 1

echo SUCCESS
