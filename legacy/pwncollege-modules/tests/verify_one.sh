#!/bin/bash -e

PWNSHOP=${PWNSHOP:-"docker run --rm -t -v /var/run/docker.sock:/var/run/docker.sock -v /tmp:/tmp modules pwnshop"}

[ "$1" == "BabyRaceComplexTOCTOUstat" ] && ARGS="-w"
[ "$1" == "BabyRaceComplexTOCTOUlstat" ] && ARGS="-w"

$PWNSHOP verify --flag pwn.college{test} --timeout 120 $ARGS "$@"
