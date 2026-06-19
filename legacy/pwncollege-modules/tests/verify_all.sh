#!/bin/bash

cd "$(dirname "${BASH_SOURCE[0]}")"/..
PWNSHOP=${PWNSHOP:-"docker run --rm -t modules pwnshop"}

LOGDIR=/tmp/logs-$$
mkdir -p $LOGDIR/chals
$PWNSHOP list |
	tr -d '\r' |
	sed -e "s/.* //" |
	parallel --group --timeout 180 "timeout -k10 150 tests/verify_one.sh {} | tee $LOGDIR/chals/{}" |
	tee \
	>(grep ^VERIFYING | awk '{print $2}' > $LOGDIR/attempted) \
	>(grep ^FAILED | awk '{print $2}' > $LOGDIR/failed) \
	>(grep ^MISSING | awk '{print $2}' > $LOGDIR/missing) \
	>(grep ^SUCCEEDED | awk '{print $2}' > $LOGDIR/succeeded) \
	$LOGDIR/log

# somehow tee takes a while to finish? what?
sleep 10

echo
echo
echo
echo
echo "ATTEMPTED: $(wc -l $LOGDIR/attempted)"
echo "SUCCEEDED: $(wc -l $LOGDIR/succeeded)"
echo "MISSING: $(wc -l $LOGDIR/missing)"
echo "FAILED: $(wc -l $LOGDIR/failed)"

echo ""
echo "FAILURES:"
sort $LOGDIR/failed
