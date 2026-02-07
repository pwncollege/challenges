#!/bin/sh

set -eu

mkdir -p /dev /proc /sys
mount -t devtmpfs devtmpfs /dev
mount -t proc proc /proc
mount -t sysfs sys /sys

exec /bin/sh
